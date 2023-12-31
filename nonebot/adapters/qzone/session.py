import asyncio
import json
import math
import time
import re
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, List, Optional, Dict, Union, Tuple

from nonebot.drivers import URL, Request, Response, Cookies
from nonebot.utils import escape_tag

from .config import Config
from .utils import log, open_file, save_image, remove_file
from .exception import NotLoggedIn, AlreadyLoggedIn


def _cookies_to_dict(cookies: Cookies) -> dict:
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie.name] = cookie.value
    return cookie_dict


class Session:
    CookieRefreshTime: timedelta = timedelta(minutes=10)

    def __init__(
        self,
        request: Callable[[Request], Coroutine[Any, Any, Response]],
        config: Config,
    ) -> None:
        self._request = request
        self.config = config
        self.qq_number: Optional[str] = None
        self._cookies: Cookies = Cookies()
        self.cookies_last_used: Optional[datetime] = None
        self._load_cookies()
        self.maintainer = asyncio.create_task(self._maintain_cookies())

    async def request(self, method: str, url: Union[URL, str], **kwargs) -> Response:
        if "cookies" not in kwargs:
            kwargs["cookies"] = self.cookies
            self.cookies_last_used = datetime.now()
        return await self._request(Request(method, url, **kwargs))

    async def get(self, url: Union[URL, str], **kwargs) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: Union[URL, str], **kwargs) -> Response:
        return await self.request("POST", url, **kwargs)

    @property
    def cookies(self) -> Cookies:
        return self._cookies

    @cookies.setter
    def cookies(self, value: Cookies) -> None:
        self._cookies = value
        if "uin" in value:
            self._save_cookies()

    def _load_cookies(self) -> None:
        if not os.path.isfile(self.config.cookie_path):
            log("INFO", f"Cookie file {self.config.cookie_path} not found")
            return

        try:
            data = json.loads(self.config.cookie_path.read_text())
            last_used = datetime.fromtimestamp(data["last_used"])
            if datetime.now() - last_used > self.CookieRefreshTime:
                log(
                    "INFO",
                    f"Cookies in {self.config.cookie_path} are considered expired",
                )
                self._delete_cookies()
                return

            self.cookies_last_used = last_used
            self.cookies.update(data["cookies"])
            self.qq_number = self.cookies["uin"][1:]
            log(
                "INFO",
                f"Cookies loaded from {self.config.cookie_path}: {self.qq_number} logged in",
            )
        except (json.decoder.JSONDecodeError, TypeError, KeyError) as err:
            log(
                "INFO",
                f"Cookies in {self.config.cookie_path} failed to parse: <{type(err).__name__}: {err}>",
            )
            self._delete_cookies()

    def _save_cookies(self) -> None:
        assert self.cookies_last_used
        data = {
            "last_used": self.cookies_last_used.timestamp(),
            "cookies": _cookies_to_dict(self.cookies),
        }
        self.config.cookie_path.write_text(json.dumps(data))
        log("INFO", f"Cookies saved to {self.config.cookie_path}: {data}")

    def _delete_cookies(self) -> None:
        self._cookies.clear()
        os.remove(self.config.cookie_path)
        log("INFO", f"Cookies deleted: {self.cookies}")

    async def _maintain_cookies(self) -> None:
        while True:
            if self.qq_number:
                response = await self.get(
                    f"https://user.qzone.qq.com/{self.qq_number}/more",
                )
                assert response.request
                self.cookies = response.request.cookies
                log("DEBUG", f"Cookies updated: {self.cookies}")
            await asyncio.sleep(self.CookieRefreshTime.total_seconds())

    def close(self) -> None:
        self.maintainer.cancel()

    @property
    def logged_in(self) -> bool:
        return self.qq_number is not None

    @staticmethod
    def _decrypt_qrsig(qrsig) -> int:
        val = 0
        for i in qrsig:
            val += (val << 5) + ord(i)
        return 2147483647 & val

    @staticmethod
    def _get_time() -> str:
        return str(math.floor(time.time() * 1000))

    @staticmethod
    def _calc_gtk(val: str) -> int:
        hsh = 5381
        for i in val:
            hsh += (hsh << 5) + ord(i)
        return hsh & 0x7FFFFFFF

    async def _get_qrcode(self) -> None:
        qrcode = await self.get(
            "https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.405252856480647&daid=5&pt_3rd_aid=0&u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone",
        )
        save_image(qrcode.content, self.config.qrcode_path)
        open_file(self.config.qrcode_path)
        log("INFO", f"QRCode successfully saved to {self.config.qrcode_path}")
        assert qrcode.request
        self.cookies = qrcode.request.cookies

    async def _check_qrcode(self) -> Optional[str]:
        qrsig = self.cookies["qrsig"]
        ptqrtoken = str(self._decrypt_qrsig(qrsig))
        url = URL(
            "https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&js_ver=23083115&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&&o1vId=17651ac69455d734d04e49acc7987a50&pt_js_version=v1.47.0"
        ) % {
            "ptqrtoken": ptqrtoken,
            "action": "0-0-" + self._get_time(),
        }
        qrstatus = await self.get(url)
        assert isinstance(qrstatus.content, bytes)
        text = qrstatus.content.decode()
        matcher = re.search("ptuiCB\\('0','0','(https:[a-zA-Z0-9?=&/._%]+)','0'", text)
        return matcher.group(1) if matcher else None

    def _get_qzreferrer(self) -> str:
        return f"https://user.qzone.qq.com/{self.qq_number}"

    def _get_gtk(self) -> int:
        return self._calc_gtk(self.cookies["p_skey"])

    def _get_qq_number(self) -> str:
        return self.cookies["uin"][1:]

    async def _upload_image(self, uri: str) -> dict:
        log("DEBUG", f"Upload images with\n{self.cookies}")
        data = {
            "qzreferrer": self._get_qzreferrer(),
            "filename": "filename",
            "zzpanelkey": "",
            "qzonetoken": "",
            "uploadtype": 1,
            "albumtype": 7,
            "exttype": 0,
            "refer": "shuoshuo",
            "output_type": "jsonhtml",
            "charset": "utf-8",
            "output_charset": "utf-8",
            "upload_hd": 1,
            "hd_width": 2048,
            "hd_height": 10000,
            "hd_quality": 96,
            "backUrls": "http://upbak.photo.qzone.qq.com/cgi-bin/upload/cgi_upload_image,http://119.147.64.75/cgi-bin/upload/cgi_upload_image",
            "url": f"https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image?g_tk={self._get_gtk()}",
            "base64": 1,
            "skey": self.cookies["skey"],
            "zzpaneluin": self.qq_number,
            "uin": self.qq_number,
            "p_skey": self.cookies["p_skey"],
            "jsonhtml_callback": "callback",
            "p_uin": self.qq_number,
            "picfile": uri,
        }
        html = await self.post(
            f"https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image?g_tk={self._get_gtk()}",
            data=data,
        )
        assert isinstance(html.content, bytes)
        log("DEBUG", f"Upload result {html}")
        html = html.content.decode()
        log("DEBUG", escape_tag(html))
        return json.loads(html[html.find("data") + 6 : html.find("ret") - 2])

    async def login(self):
        if self.logged_in:
            raise AlreadyLoggedIn

        await self._get_qrcode()
        while True:
            await asyncio.sleep(1)
            check_sig_link = await self._check_qrcode()
            if check_sig_link:
                # log("DEBUG", matcher.group(1))
                log("DEBUG", str(self.cookies))
                response = await self.get(check_sig_link)
                assert response.request
                self.cookies = response.request.cookies
                self.qq_number = self._get_qq_number()
                break
        remove_file(self.config.qrcode_path)
        log("DEBUG", str(self.cookies))
        # log("DEBUG", self.cookies["p_skey"])
        log("INFO", f"Logged in successfully, QQ number is {self.qq_number}")

    async def logout(self):
        if not self.logged_in:
            raise NotLoggedIn
        self.qq_number = None
        self._delete_cookies()
        log("INFO", "Logged out successfully")

    async def publish(
        self, content: str = "", images: Optional[List[str]] = None
    ) -> Tuple[str, List[str]]:
        if not self.logged_in:
            raise NotLoggedIn
        assert self.qq_number
        log("DEBUG", f"Publish with\n{self.cookies}")

        data: Dict[str, Union[int, str]] = {}
        pic_id: List[str] = []
        if not images:
            data = {
                "syn_tweet_version": 1,
                "paramstr": 1,
                "pic_template": "",
                "richtype": "",
                "richval": "",
                "special_url": "",
                "subrichtype": "",
                "con": content,
                "feedversion": 1,
                "ver": 1,
                "ugc_right": 1,
                "to_sign": 0,
                "hostuin": self.qq_number,
                "code_version": 1,
                "format": "fs",
                "qzreferrer": self._get_qzreferrer(),
            }
        else:
            richval = []
            pic_bo = []
            for img in images:
                ret = await self._upload_image(img)
                richval.append(
                    ",{0},{1},{2},{3},{4},{5},,{4},{5}".format(
                        ret["albumid"],
                        ret["lloc"],
                        ret["sloc"],
                        ret["type"],
                        ret["height"],
                        ret["width"],
                    )
                )
                pic_bo.append(ret["pre"][ret["pre"].find("bo=") + 3 :])
                pic_id.append(ret["lloc"])
            data = {
                "syn_tweet_version": 1,
                "paramstr": 1,
                "pic_template": f"tpl-{len(images)}-1",
                "richtype": 1,
                "richval": "\t".join(richval),
                "special_url": "",
                "subrichtype": 1,
                "con": content,
                "feedversion": 1,
                "ver": 1,
                "ugc_right": 1,
                "to_sign": 0,
                "hostuin": self.qq_number,
                "code_version": 1,
                "format": "fs",
                "qzreferrer": self._get_qzreferrer(),
                "pic_bo": "{0}\t{0}".format(",".join(pic_bo)),
            }

        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6?g_tk={self._get_gtk()}"
        # log("DEBUG", f"DATA: {data}")
        html = await self.post(url, data=data)
        assert isinstance(html.content, bytes)
        log("DEBUG", f"Publish result: {html}")
        html = html.content.decode()
        log("DEBUG", escape_tag(html))
        ret = json.loads(html[html.find("callback(") + 9 : html.find("});") + 1])
        return ret["t1_tid"], pic_id
