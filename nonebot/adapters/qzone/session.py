import json
import math
import time
import re

from typing import Any, Callable, Coroutine, List, Optional, Dict, Union

from nonebot.drivers import URL, Request, Response, Cookies
from nonebot.utils import escape_tag

from .utils import log, open_file, save_image, remove_file
from .utils import QRCODE_SAVE_PATH


class Session:
    def __init__(
        self, request: Callable[[Request], Coroutine[Any, Any, Response]]
    ) -> None:
        self.request = request
        self.qq_number: str
        self.cookies: Cookies

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
        request = Request(
            "GET",
            "https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.405252856480647&daid=5&pt_3rd_aid=0&u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone",
        )
        qrcode = await self.request(request)
        save_image(qrcode.content, QRCODE_SAVE_PATH)
        open_file(QRCODE_SAVE_PATH)
        log("INFO", f"二维码成功保存到 {QRCODE_SAVE_PATH}")
        self.cookies = qrcode.request.cookies  # type: ignore

    async def _check_qrcode(self) -> Optional[str]:
        qrsig = self.cookies["qrsig"]
        ptqrtoken = str(self._decrypt_qrsig(qrsig))
        url = URL(
            "https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&js_ver=23083115&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&&o1vId=17651ac69455d734d04e49acc7987a50&pt_js_version=v1.47.0"
        ) % {
            "ptqrtoken": ptqrtoken,
            "action": "0-0-" + self._get_time(),
        }
        qrstatus = await self.request(Request("GET", str(url), cookies=self.cookies))
        text = qrstatus.content.decode()  # type: ignore
        matcher = re.search("ptuiCB\\('0','0','(https:[a-zA-Z0-9?=&/._%]+)','0'", text)
        return matcher.group(1) if matcher else None

    def _get_qzreferrer(self) -> str:
        return f"https://user.qzone.qq.com/{self.qq_number}"

    def _get_gtk(self) -> int:
        return self._calc_gtk(self.cookies["p_skey"])

    async def _upload_image(self, uri: str) -> dict:
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
        html = await self.request(
            Request(
                "POST",
                f"https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image?g_tk={self._get_gtk()}",
                data=data,
                cookies=self.cookies,
            )
        )
        html = html.content.decode()  # type: ignore
        return json.loads(html[html.find("data") + 6 : html.find("ret") - 2])

    async def login(self):
        await self._get_qrcode()
        while True:
            time.sleep(1)
            check_sig_link = await self._check_qrcode()
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
        log("INFO", f"登录成功，QQ 号码为 {self.qq_number}")

    async def publish(self, content: str = "", images: Optional[List[str]] = None):
        data: Dict[str, Union[int, str]] = {}
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
                "hostuin": "3193974372",
                "code_version": 1,
                "format": "fs",
                "qzreferrer": self._get_qzreferrer(),
                "pic_bo": "{0}\t{0}".format(",".join(pic_bo)),
            }

        url = f"https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6?g_tk={self._get_gtk()}"
        # log("DEBUG", f"DATA: {data}")
        response = await self.request(
            Request("POST", url, data=data, cookies=self.cookies)
        )
        log("DEBUG", escape_tag(response.content.decode()))  # type: ignore
