from typing import Any, List
from typing_extensions import override

from nonebot.drivers import Driver
from nonebot.adapters import Adapter as BaseAdapter

from .bot import Bot
from .config import ADAPTER_NAME, Config
from .message import Message, Text, Image, MessageSegment
from .utils import log
from .session import Session


class Adapter(BaseAdapter):
    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)

        self.adapter_config: Config = Config(**self.config.dict())

        self.bot = Bot(self, "qzone")
        self._setup()

        self.session = Session(self.request)

    @classmethod
    @override
    def get_name(cls) -> str:
        return ADAPTER_NAME

    def _setup(self) -> None:
        self.driver.on_startup(self._startup)
        self.driver.on_shutdown(self._shutdown)

    async def _startup(self) -> None:
        await self.login()
        self.bot_connect(self.bot)

    async def _shutdown(self) -> None:
        self.bot_disconnect(self.bot)

    async def login(self) -> None:
        await self.session.login()

    async def post(self, message: Message) -> None:
        content = ""
        images: List[str] = []
        # log("DEBUG", f"Message: {message}")
        for sgm in message:
            if isinstance(sgm, Text):
                log("DEBUG", f"{sgm} {type(sgm)} {sgm.data}")
                content = sgm.data["text"]
            if isinstance(sgm, Image):
                log("DEBUG", f"{sgm} {type(sgm)} {sgm.data}")
                images.append(sgm.data["file"])

        await self.session.publish(content, images)

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        # log("DEBUG", f"Adapter _call_api: {bot} {api} {data}")
        await self.post(data["message"])
