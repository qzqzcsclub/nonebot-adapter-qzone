from typing import Type, Iterable
from typing_extensions import override

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment


class MessageSegment(BaseMessageSegment["Message"]):
    @classmethod
    @override
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @override
    def __str__(self) -> str:
        return str(self.data)

    @override
    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(content: str) -> "Text":
        return Text(content)

    @staticmethod
    def image(uri: str) -> "Image":
        return Image(uri)


class Text(MessageSegment):
    @override
    def __init__(self, content: str):
        super().__init__("text", {"text": content})

    @override
    def __str__(self) -> str:
        return f"<text: {self.data['text']}>"


class Image(MessageSegment):
    @override
    def __init__(self, uri: str):
        super().__init__("image", {"file": uri})

    @override
    def __str__(self) -> str:
        return f"<image: {self.data['file']}>"


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield Text(msg)
