import base64
from pathlib import Path

from nonebot import get_bot, on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters import Message

from nonebot.adapters.qzone import PostEvent
from nonebot.adapters.qzone import MessageSegment


SAMPLE_IMAGE_PATH = str((Path(__file__).parent.parent / "sample.png").resolve())


def to_uri(path: str):
    with open(path, "rb") as img:
        binary = img.read()
    code = base64.b64encode(binary).decode("utf-8")
    return f"data:image/png;base64,{code}"


post = on_command("post", to_me())


@post.handle()
async def handle_post(message: Message = CommandArg()):
    bot = get_bot("qzone")
    print(type(message), message)
    msg = MessageSegment.text(str(message))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    await bot.send(PostEvent, msg)
    await post.send(f"{msg} Posted")
