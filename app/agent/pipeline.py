from app.agent import nodes
from app.agent.graph import StateGraph


def build_agent() -> StateGraph:
    graph = StateGraph()
    graph.add_node("ingest", nodes.ingest)
    graph.add_node("extract", nodes.extract)
    graph.add_node("dispatch", nodes.dispatch)
    graph.add_node("identity", nodes.identity)
    graph.add_node("faq", nodes.faq)
    graph.add_node("qualify", nodes.qualify)
    graph.add_node("offer_slots", nodes.offer_slots)
    graph.add_node("choose_slot", nodes.choose_slot)
    graph.add_node("post_booking", nodes.post_booking)
    graph.add_node("finish", nodes.finish)
    graph.set_entry_point("ingest")
    return graph


agent = build_agent()
