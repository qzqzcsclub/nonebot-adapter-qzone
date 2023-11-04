from typing import Any, Union, Optional
from typing_extensions import override

from nonebot.adapters import Bot as BaseBot
from nonebot.message import handle_event

from .event import Event, PublishEvent, LoginEvent, LogoutEvent, QueryEvent
from .message import Message, MessageSegment
from .utils import log
from .extension import ApiNotAvailable


class Bot(BaseBot):
    @override
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> Any:
        log("DEBUG", f"Received {event}")

        if isinstance(event, PublishEvent):
            assert message
            return await self.publish(message)
        if isinstance(event, LoginEvent):
            return await self.login()
        if isinstance(event, LogoutEvent):
            return await self.logout()
        if isinstance(event, QueryEvent):
            return await self.query()

        raise ApiNotAvailable

    async def handle_event(self, event: Event) -> None:
        await handle_event(self, event)

    @override
    async def call_api(self, api: str, **data: Any) -> Any:
        return await super().call_api(api, **data)

    async def publish(self, message: Union[str, Message, MessageSegment]) -> Any:
        return await self.call_api("publish", message=Message(message))

    async def login(self) -> Any:
        return await self.call_api("login")

    async def logout(self) -> Any:
        return await self.call_api("logout")

    async def query(self) -> Any:
        return await self.call_api("query")
