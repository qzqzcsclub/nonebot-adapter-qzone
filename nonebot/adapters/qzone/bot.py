from typing import Any, Union
from typing_extensions import override

from nonebot.adapters import Bot as BaseBot
from nonebot.message import handle_event

from .event import Event
from .message import Message, MessageSegment
from .utils import log


class Bot(BaseBot):
    @override
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> Any:
        log("DEBUG", f"Received {event} {message}")
        return await self.post(message)

    async def handle_event(self, event: Event) -> None:
        await handle_event(self, event)

    @override
    async def call_api(self, api: str, **data: Any) -> Any:
        return await super().call_api(api, **data)

    async def post(self, message: Union[str, Message, MessageSegment]) -> Any:
        return await self.call_api("post", content=message)
