import base64
from pathlib import Path

from nonebot import get_bot, on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters import Message

from nonebot.adapters.qzone import PublishEvent, LoginEvent, LogoutEvent
from nonebot.adapters.qzone import MessageSegment


SAMPLE_IMAGE_PATH = str((Path(__file__).parent.parent / "sample.png").resolve())


def to_uri(path: str):
    with open(path, "rb") as img:
        binary = img.read()
    code = base64.b64encode(binary).decode("utf-8")
    return f"data:image/png;base64,{code}"


publish = on_command("publish", to_me())
login = on_command("login", to_me())
logout = on_command("logout", to_me())


@publish.handle()
async def handle_publish(message: Message = CommandArg()):
    bot = get_bot("qzone")
    print(type(message), message)
    msg = MessageSegment.text(str(message))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    await bot.send(PublishEvent(), msg)
    await publish.send(f"{msg} Published")


@login.handle()
async def handle_login(message: Message = CommandArg()):
    bot = get_bot("qzone")
    await bot.send(LoginEvent(), message)


@logout.handle()
async def handle_logout(message: Message = CommandArg()):
    bot = get_bot("qzone")
    await bot.send(LogoutEvent(), message)
