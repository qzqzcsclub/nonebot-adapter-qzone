from typing import Optional
from typing_extensions import override

from nonebot.adapters import Event as BaseEvent

from .message import Message


class Event(BaseEvent):
    pass


class PostEvent(Event):
    content: Optional[Message] = None

    @override
    def get_event_name(self) -> str:
        return "post"

    @override
    def get_type(self) -> str:
        return "post"

    @override
    def get_event_description(self) -> str:
        return str(self.dict())