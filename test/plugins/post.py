from nonebot import get_bot, on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters import Message

from nonebot.adapters.qzone import PostEvent


post = on_command("post", to_me())


@post.handle()
async def handle_post(message: Message = CommandArg()):
    bot = get_bot("qzone")
    await bot.send(PostEvent, message)
    await post.send(f"{message} Posted")
