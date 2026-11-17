from typing import Optional

from app.agent.language import contains_keyword, normalize

TOPIC_KEYWORDS = {
    "golden_visa": [
        "golden visa", "residency", "residence permit", "visa", "iqama",
        "الاقامة الذهبية", "الفيزا الذهبية", "الاقامة", "اقامة", "فيزا",
    ],
    "fees": [
        "fee", "fees", "dld", "rett", "transfer", "registration", "commission", "tax", "taxes", "closing cost",
        "رسوم", "ضريبة", "عمولة", "تسجيل", "نقل الملكية", "تكاليف",
    ],
    "ownership": [
        "foreigner", "foreigners", "non-resident", "non resident", "can i buy", "can i own", "freehold", "ownership", "allowed to buy",
        "تملك", "اجنبي", "اجانب", "الاجانب", "غير مقيم", "يحق لي", "اقدر اشتري",
    ],
}

ENTRIES = {
    ("DUBAI", "fees"): {
        "en": "In Dubai the main buying cost is the Dubai Land Department transfer fee of 4% of the property price, plus a small admin fee and the registration trustee fee. Agency commission is usually 2%. Our consultant will give you the exact total for your budget on the call.",
        "ar": "في دبي، أهم رسوم الشراء هي رسوم دائرة الأراضي والأملاك 4% من سعر العقار، مع رسوم إدارية بسيطة ورسوم مكتب التسجيل. وعمولة الوسيط غالباً 2%. المستشار يعطيك التكلفة الدقيقة حسب ميزانيتك في المكالمة.",
    },
    ("SAUDI", "fees"): {
        "en": "In Saudi Arabia, property transactions are subject to a 5% Real Estate Transaction Tax (RETT) on the sale price. Our consultant will confirm any exemptions and the latest rules for your case.",
        "ar": "في السعودية، تُفرض ضريبة التصرفات العقارية بنسبة 5% على سعر البيع. المستشار يأكد لك الاستثناءات وآخر الأنظمة على حالتك.",
    },
    ("DUBAI", "golden_visa"): {
        "en": "Dubai offers a 10-year Golden Visa to property investors who own property worth AED 2 million or more. Our consultant can check whether your target property qualifies.",
        "ar": "دبي تعطي الإقامة الذهبية لمدة 10 سنوات للمستثمرين اللي يملكون عقار قيمته مليونين درهم أو أكثر. المستشار يتأكد لك إذا العقار اللي تبيه يؤهلك.",
    },
    ("QATAR", "golden_visa"): {
        "en": "In Qatar, buying property in the designated zones can qualify you for residency, with higher value thresholds opening permanent residency benefits. The conditions are updated from time to time, so our consultant will confirm the current values.",
        "ar": "في قطر، شراء عقار في المناطق المخصصة للتملك الأجنبي يؤهلك للإقامة، وفيه شروط أعلى للإقامة الدائمة. الشروط تتحدث من وقت لوقت، والمستشار يأكد لك القيم الحالية.",
    },
    ("DUBAI", "ownership"): {
        "en": "Foreign buyers can purchase freehold property in Dubai's designated freehold areas and hold full ownership rights. Our consultant can point you to the right communities for your budget.",
        "ar": "الأجنبي يقدر يشتري عقار تملك حر في مناطق التملك الحر المخصصة في دبي ويكون له حقوق الملكية كاملة. المستشار يرشح لك أنسب المناطق حسب ميزانيتك.",
    },
    ("SAUDI", "ownership"): {
        "en": "Saudi Arabia is opening property ownership to non-Saudis under a newer framework that applies in designated zones. Eligibility depends on the city and zone, so our consultant will confirm what applies to you.",
        "ar": "السعودية فتحت التملك لغير السعوديين بنظام جديد يطبق في مناطق محددة. الأهلية تختلف حسب المدينة والمنطقة، والمستشار يأكد لك اللي ينطبق عليك.",
    },
    ("QATAR", "ownership"): {
        "en": "Foreigners can own property in Qatar in designated freehold and usufruct zones such as The Pearl and Lusail. Our consultant will walk you through the options.",
        "ar": "الأجنبي يقدر يتملك في قطر داخل مناطق التملك الحر والانتفاع المخصصة مثل اللؤلؤة ولوسيل. المستشار يشرح لك الخيارات المتاحة.",
    },
    ("KUWAIT", "ownership"): {
        "en": "Property ownership in Kuwait is largely restricted to Kuwaiti nationals, with limited provisions for GCC citizens. Non-GCC foreigners generally can't buy directly, so our consultant will explain the legal routes available.",
        "ar": "التملك العقاري في الكويت محصور غالباً بالمواطنين الكويتيين مع أحكام محدودة لمواطني دول الخليج. غير الخليجي عادة ما يقدر يشتري مباشرة، والمستشار يوضح لك الطرق القانونية المتاحة.",
    },
}

_TOPICS = {topic: [normalize(word) for word in words] for topic, words in TOPIC_KEYWORDS.items()}


def detect_topic(text: str) -> Optional[str]:
    normalized = normalize(text)
    for topic, words in _TOPICS.items():
        if any(contains_keyword(normalized, word) for word in words):
            return topic
    return None


def answer(country: str, topic: str, language: str) -> Optional[str]:
    entry = ENTRIES.get((country, topic))
    if entry is None:
        return None
    return entry["ar"] if language == "ar" else entry["en"]
