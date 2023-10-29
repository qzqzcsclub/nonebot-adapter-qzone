import asyncio
from http.cookiejar import Cookie
import math
import time
import re

from typing import Any, List, Optional
from typing_extensions import override

from nonebot.utils import DataclassEncoder, escape_tag
from nonebot.drivers import URL, Driver, Request, Cookies

from nonebot.adapters import Adapter as BaseAdapter

from .bot import Bot
from .event import PostEvent
from .config import ADAPTER_NAME, Config
from .message import Message, MessageSegment
from .utils import log, open_file, save_image, remove_file
from .utils import QRCODE_SAVE_PATH


class Adapter(BaseAdapter):
    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)

        self.adapter_config: Config = Config(**self.config.dict())

        self.bot = Bot(self, "qzone")
        self.tasks: List[asyncio.Task] = []
        self._setup()

        self.cookies: Cookies = Cookies()
        self.qq_number: str = ""

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
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(
            *(asyncio.wait_for(task, timeout=10) for task in self.tasks),
            return_exceptions=True,
        )

    async def login(self) -> None:
        def _decrypt_qrsig(qrsig) -> int:
            val = 0
            for i in qrsig:
                val += (val << 5) + ord(i)
            return 2147483647 & val

        def _get_time() -> str:
            return str(math.floor(time.time() * 1000))

        async def _get_qrcode() -> None:
            request = Request(
                "GET",
                "https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.405252856480647&daid=5&pt_3rd_aid=0&u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone",
            )
            qrcode = await self.request(request)
            save_image(qrcode.content, QRCODE_SAVE_PATH)
            open_file(QRCODE_SAVE_PATH)
            log("DEBUG", f"QRCode Saved to {QRCODE_SAVE_PATH}!")
            self.cookies = qrcode.request.cookies  # type: ignore

        async def _check_qrcode() -> Optional[str]:
            qrsig = self.cookies["qrsig"]
            ptqrtoken = str(_decrypt_qrsig(qrsig))
            url = URL(
                "https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&js_ver=23083115&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&&o1vId=17651ac69455d734d04e49acc7987a50&pt_js_version=v1.47.0"
            ) % {
                "ptqrtoken": ptqrtoken,
                "action": "0-0-" + _get_time(),
            }
            qrstatus = await self.request(
                Request("GET", str(url), cookies=self.cookies)
            )
            text = qrstatus.content.decode()  # type: ignore
            matcher = re.search(
                "ptuiCB\\('0','0','(https:[a-zA-Z0-9?=&/._%]+)','0'", text
            )
            return matcher.group(1) if matcher else None

        await _get_qrcode()
        while True:
            time.sleep(1)
            check_sig_link = await _check_qrcode()
            if check_sig_link:
                matcher = re.search("&uin=([0-9]+)&", check_sig_link)
                if not matcher:
                    continue
                self.qq_number = matcher.group(1)
                # log("DEBUG", matcher.group(1))
                # log("DEBUG", self.cookies)
                response = await self.request(
                    Request("GET", check_sig_link, cookies=self.cookies)
                )
                self.cookies = response.request.cookies  # type: ignore
                break
        remove_file(QRCODE_SAVE_PATH)
        # log("DEBUG", self.cookies)
        # log("DEBUG", self.cookies["p_skey"])
        log("INFO", f"登录成功，qq 号码为 {self.qq_number}")

    async def post(self, msg: str) -> None:
        def _get_gtk(val: str) -> int:
            hsh = 5381
            for i in val:
                hsh += (hsh << 5) + ord(i)
            return hsh & 0x7FFFFFFF

        data = {
            "syn_tweet_verson": 1,
            "paramstr": 1,
            "who": 1,
            "con": msg,
            "feedversion": 1,
            "ver": 1,
            "ugc_right": 1,
            "to_sign": 0,
            "hostuin": self.qq_number,
            "code_version": 1,
            "format": "fs",
            "qzreferrer": "https://user.qzone.qq.com/" + self.qq_number,
            "pic_template": "",
            "richtype": "",
            "richval": "",
            "special_url": "",
            "subrichtype": "",
        }
        url = URL(
            "https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6"
        ) % {"g_tk": _get_gtk(self.cookies["p_skey"])}
        response = await self.request(
            Request("POST", str(url), data=data, cookies=self.cookies)
        )
        # req = self.session.post(str(url), data=data)
        # log("DEBUG", req.text)
        # log("DEBUG", response.content.decode())  # type: ignore

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        log("DEBUG", f"Adapter _call_api: {bot} {api} {data}")
        await self.post(str(data["content"]))
