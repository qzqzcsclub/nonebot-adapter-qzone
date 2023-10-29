from pathlib import Path

import nonebot
import nonebot.adapters

nonebot.adapters.__path__.append(  # type: ignore
    str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
)


from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.qzone import Adapter as QzoneAdapter


nonebot.init(driver="~fastapi+~httpx")
nonebot.load_plugin("plugins.post")

app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(QzoneAdapter)
driver.register_adapter(ConsoleAdapter)

if __name__ == "__main__":
    nonebot.logger.warning(
        "Always use `nb run` to start the bot instead of manually running!"
    )
    nonebot.run(app="__mp_main__:app")
