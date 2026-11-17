from typing import Any, Awaitable, Callable

END = "__end__"
MAX_STEPS = 20

NodeFunction = Callable[[dict[str, Any]], Awaitable[str]]


class StateGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, NodeFunction] = {}
        self._entry: str = ""

    def add_node(self, name: str, function: NodeFunction) -> None:
        self._nodes[name] = function

    def set_entry_point(self, name: str) -> None:
        self._entry = name

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        current = self._entry
        steps = 0
        while current != END:
            steps += 1
            if steps > MAX_STEPS or current not in self._nodes:
                raise RuntimeError(f"graph stopped at node '{current}' after {steps} steps")
            current = await self._nodes[current](state)
        return state
