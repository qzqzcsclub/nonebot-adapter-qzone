from nonebot import get_bot, on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters import Message

from nonebot.adapters.qzone import PublishEvent, LoginEvent, LogoutEvent, QueryEvent
from nonebot.adapters.qzone import MessageSegment

from . import SAMPLE_IMAGE_PATH, to_uri


publish = on_command("publish", to_me())
login = on_command("login", to_me())
logout = on_command("logout", to_me())
query = on_command("query", to_me())


@publish.handle()
async def handle_publish(message: Message = CommandArg()):
    bot = get_bot("qzone_bot")
    print(type(message), message)
    msg = MessageSegment.text(str(message))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    msg += MessageSegment.image(to_uri(SAMPLE_IMAGE_PATH))
    tid, pic_id = await bot.send(PublishEvent(), msg)
    await publish.send(f"Published: {tid} {pic_id}")


@login.handle()
async def handle_login(message: Message = CommandArg()):
    bot = get_bot("qzone_bot")
    await bot.send(LoginEvent(), message)


@logout.handle()
async def handle_logout(message: Message = CommandArg()):
    bot = get_bot("qzone_bot")
    await bot.send(LogoutEvent(), message)


@query.handle()
async def handle_query(message: Message = CommandArg()):
    bot = get_bot("qzone_bot")
    qq_number: str = await bot.send(QueryEvent(), message)
    if qq_number:
        await query.send(f"{qq_number} logged in")
    else:
        await query.send("No account logged in")
