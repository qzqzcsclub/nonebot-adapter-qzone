from typing import Any, List, Optional
from typing_extensions import override

from nonebot.drivers import Driver
from nonebot.adapters import Adapter as BaseAdapter

from .bot import Bot
from .config import ADAPTER_NAME, Config
from .message import Message, Text, Image, MessageSegment
from .utils import log
from .session import Session
from .extension import ApiNotAvailable


class Adapter(BaseAdapter):
    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)

        self.adapter_config: Config = Config(**self.config.dict())
        log("DEBUG", self.adapter_config.bot_id)
        log("DEBUG", str(self.adapter_config.cache_path))

        self.bot = Bot(self, self.adapter_config.bot_id)
        self._setup()

        self.session = Session(self.request, self.adapter_config)

    @classmethod
    @override
    def get_name(cls) -> str:
        return ADAPTER_NAME

    def _setup(self) -> None:
        self.driver.on_startup(self._startup)
        self.driver.on_shutdown(self._shutdown)

    async def _startup(self) -> None:
        self.bot_connect(self.bot)

    async def _shutdown(self) -> None:
        self.bot_disconnect(self.bot)

    async def login(self) -> None:
        await self.session.login()

    async def logout(self) -> None:
        await self.session.logout()

    async def publish(self, message: Message) -> None:
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

    async def query(self) -> Optional[str]:
        return self.session.qq_number

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        # log("DEBUG", f"Adapter _call_api: {bot} {api} {data}")

        if api == "publish":
            return await self.publish(data["message"])
        if api == "login":
            return await self.login()
        if api == "logout":
            return await self.logout()
        if api == "query":
            return await self.query()

        raise ApiNotAvailable
