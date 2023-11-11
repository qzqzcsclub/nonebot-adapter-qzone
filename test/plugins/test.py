import asyncio

from nonebot import get_bot, on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters import Message

from nonebot.adapters.qzone import PublishEvent
from nonebot.adapters.qzone import MessageSegment


test_delay = on_command("test-delay", to_me())


@test_delay.handle()
async def handle_test_delay(message: Message = CommandArg()):
    time = int(str(message))
    await test_delay.send(f"Delayed publishing is scheduled for {time} minutes later")
    await asyncio.sleep(time * 60)
    bot = get_bot("qzone_bot")
    msg = MessageSegment.text("test")
    tid, pic_id = await bot.send(PublishEvent(), msg)
    await test_delay.send(f"Delayed published: {tid} {pic_id}")
