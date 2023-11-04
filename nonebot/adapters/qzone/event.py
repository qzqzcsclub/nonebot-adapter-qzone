from typing import Optional
from typing_extensions import override

from nonebot.adapters import Event as BaseEvent
from nonebot.utils import escape_tag

from .message import Message


class Event(BaseEvent):
    @override
    def get_type(self) -> str:
        return ""

    @override
    def get_event_name(self) -> str:
        return ""

    @override
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @override
    def get_user_id(self) -> str:
        raise ValueError("Event has no user!")

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no session!")

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @override
    def is_tome(self) -> bool:
        return False


class PublishEvent(Event):
    @override
    def get_event_name(self) -> str:
        return "publish"

    @override
    def get_type(self) -> str:
        return "publish"


class LoginEvent(Event):
    @override
    def get_event_name(self) -> str:
        return "login"

    @override
    def get_type(self) -> str:
        return "login"


class LogoutEvent(Event):
    @override
    def get_event_name(self) -> str:
        return "logout"

    @override
    def get_type(self) -> str:
        return "logout"


class QueryEvent(Event):
    @override
    def get_event_name(self) -> str:
        return "query"

    @override
    def get_type(self) -> str:
        return "query"
