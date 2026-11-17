import asyncio
import os
import tempfile
import unittest

_TEMP_DIR = tempfile.mkdtemp(prefix="agent-tests-")
os.environ["AGENT_DB_PATH"] = os.path.join(_TEMP_DIR, "test.db")

from app import store
from app.agent import extractor
from app.agent.language import detect_language
from app.api import whatsapp
from app.dedupe import TTLDeduplicator
from app.service import ConversationService
from app.tools import calendar as calendar_tool
from app.tools import knowledge


def run(coroutine):
    return asyncio.run(coroutine)


async def converse(service, phone, messages):
    replies = []
    state = None
    for message in messages:
        state = await service.handle_message(phone, message)
        replies.append(state["reply"])
    return state, replies


class LanguageTests(unittest.TestCase):
    def test_detects_english_and_arabic(self):
        self.assertEqual(detect_language("I need an apartment"), "en")
        self.assertEqual(detect_language("مطلوب شقة في دبي"), "ar")
        self.assertEqual(detect_language("12345", "ar"), "ar")


class ExtractorTests(unittest.TestCase):
    def test_country_intent_timeline(self):
        self.assertEqual(extractor.detect_country("Looking in Riyadh"), "SAUDI")
        self.assertEqual(extractor.detect_country("أبي شقة في الدوحة"), "QATAR")
        self.assertEqual(extractor.detect_intent("I want a golden visa"), "GOLDEN_VISA")
        self.assertEqual(extractor.detect_intent("للاستثمار"), "INVESTMENT")
        self.assertEqual(extractor.detect_intent("للسكن"), "PERSONAL_USE")
        self.assertEqual(extractor.detect_timeline("within 3 months"), "3_MONTHS")
        self.assertEqual(extractor.detect_timeline("in 8 months"), "OFF_PLAN")
        self.assertEqual(extractor.detect_timeline("immediately"), "IMMEDIATE")

    def test_budget_parsing(self):
        usd, code, assumed = extractor.parse_budget("around 2 million AED")
        self.assertEqual(code, "AED")
        self.assertFalse(assumed)
        self.assertAlmostEqual(usd, 544600.0, places=0)
        usd, code, assumed = extractor.parse_budget("500k", "DUBAI")
        self.assertEqual(code, "AED")
        self.assertTrue(assumed)
        usd, code, _ = extractor.parse_budget("$750,000")
        self.assertEqual((usd, code), (750000.0, "USD"))
        usd, code, _ = extractor.parse_budget("ميزانيتي ٢ مليون درهم")
        self.assertEqual(code, "AED")
        self.assertIsNone(extractor.parse_budget("within 3 months"))
        self.assertIsNone(extractor.parse_budget("2 bedroom flat"))
        self.assertIsNone(extractor.parse_budget("call 0501234567"))

    def test_slot_choice(self):
        isos = [
            "2030-01-07T11:00:00+04:00",
            "2030-01-08T14:00:00+04:00",
            "2030-01-09T16:00:00+04:00",
        ]
        self.assertEqual(extractor.parse_slot_choice("2", isos), 1)
        self.assertEqual(extractor.parse_slot_choice("option 3", isos), 2)
        self.assertEqual(extractor.parse_slot_choice("4 pm works", isos), 2)
        self.assertEqual(extractor.parse_slot_choice("Tuesday", isos), 1)
        self.assertEqual(extractor.parse_slot_choice("Monday please", isos), 0)
        self.assertEqual(extractor.parse_slot_choice("the first one", isos), 0)
        self.assertIsNone(extractor.parse_slot_choice("hmm not sure", isos))


class KnowledgeTests(unittest.TestCase):
    def test_answers_and_fallback(self):
        self.assertIn("4%", knowledge.answer("DUBAI", "fees", "en"))
        self.assertIn("5%", knowledge.answer("SAUDI", "fees", "ar"))
        self.assertIsNone(knowledge.answer("KUWAIT", "fees", "en"))
        self.assertEqual(knowledge.detect_topic("what are the DLD fees"), "fees")


class DedupeTests(unittest.TestCase):
    def test_claim_once(self):
        deduplicator = TTLDeduplicator(60)
        self.assertTrue(deduplicator.claim("wamid.1"))
        self.assertFalse(deduplicator.claim("wamid.1"))
        self.assertTrue(deduplicator.claim("wamid.2"))


class WebhookTests(unittest.TestCase):
    def test_extract_messages(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {"id": "wamid.A", "from": "971500000000", "type": "text", "text": {"body": "hello"}},
                                    {"id": "wamid.B", "from": "971500000000", "type": "image"},
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        self.assertEqual(
            whatsapp.extract_messages(payload),
            [{"id": "wamid.A", "phone": "971500000000", "text": "hello"}],
        )


class CalendarTests(unittest.TestCase):
    def test_slots_and_double_booking(self):
        async def scenario():
            options = await calendar_tool.get_slot_options("owner-1")
            self.assertEqual(len(options), 3)
            labels = await calendar_tool.get_available_slots("owner-1")
            self.assertEqual(len(labels), 3)
            self.assertTrue(all("GST" in label for label in labels))
            first = options[0]["iso"]
            reference = await calendar_tool.create_calendar_event("test-a", "Sara", first)
            self.assertIsNotNone(reference)
            self.assertIsNone(await calendar_tool.create_calendar_event("test-b", "Omar", first))
            remaining = await calendar_tool.get_slot_options("owner-1")
            self.assertNotIn(first, [option["iso"] for option in remaining])

        run(scenario())


class ConversationTests(unittest.TestCase):
    def test_english_flow_to_booking(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service,
                "en-flow",
                [
                    "Hi, I'm looking for an apartment in Dubai",
                    "Investment",
                    "Around 2 million AED",
                    "Within 3 months",
                    "Ahmed Khan",
                    "2",
                ],
            )
            self.assertIn("investment", replies[0].lower())
            self.assertIn("budget", replies[1].lower())
            self.assertIn("when", replies[2].lower())
            self.assertIn("name", replies[3].lower())
            self.assertIn("1.", replies[4])
            self.assertEqual(state["booking_status"], "BOOKED")
            self.assertEqual(state["lead_name"], "Ahmed Khan")
            self.assertEqual(state["target_country"], "DUBAI")
            self.assertEqual(state["intent"], "INVESTMENT")
            self.assertEqual(state["timeline"], "3_MONTHS")
            self.assertTrue(state["is_qualified"])
            self.assertIn(state["booking_reference"], replies[5])
            self.assertTrue(any(b["phone"] == "en-flow" for b in store.list_bookings()))

        run(scenario())

    def test_arabic_flow_to_booking(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service,
                "ar-flow",
                [
                    "السلام عليكم، أبي شقة في دبي",
                    "استثمار",
                    "ميزانيتي ٢ مليون درهم",
                    "الحين",
                    "محمد العلي",
                    "الأول",
                ],
            )
            self.assertEqual(state["language"], "ar")
            self.assertTrue(all(any("؀" <= ch <= "ۿ" for ch in reply) for reply in replies))
            self.assertEqual(state["booking_status"], "BOOKED")
            self.assertEqual(state["timeline"], "IMMEDIATE")
            self.assertEqual(state["lead_name"], "محمد العلي")

        run(scenario())

    def test_faq_then_resume(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service, "faq-flow", ["What are the DLD fees in Dubai?"]
            )
            self.assertIn("4%", replies[0])
            self.assertIn("investment", replies[0].lower())
            self.assertEqual(state["target_country"], "DUBAI")

        run(scenario())

    def test_faq_asks_country_then_answers(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service, "faq-country", ["Can foreigners buy property?", "Saudi"]
            )
            self.assertIn("which country", replies[0].lower())
            self.assertIn("non-saudis", replies[1].lower())

        run(scenario())

    def test_unknown_faq_uses_safe_fallback(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service, "faq-fallback", ["What are the registration fees in Kuwait?"]
            )
            self.assertIn("not fully sure", replies[0])

        run(scenario())

    def test_identity_question_is_answered_honestly(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(service, "identity", ["Are you a bot?"])
            self.assertIn("virtual assistant", replies[0])

        run(scenario())

    def test_other_times_then_book(self):
        async def scenario():
            service = ConversationService()
            state, replies = await converse(
                service,
                "other-times",
                [
                    "Looking in Qatar for my family, 1.5 million QAR, immediately",
                    "Layla",
                    "none of these work",
                ],
            )
            self.assertEqual(state["slot_round"], 1)
            self.assertEqual(state["booking_status"], "SLOTS_OFFERED")
            self.assertIn("other times", replies[2].lower())
            state = await service.handle_message("other-times", "3")
            self.assertEqual(state["booking_status"], "BOOKED")

        run(scenario())


if __name__ == "__main__":
    unittest.main()
