import math
import os
import re
import time
from typing import Optional

import requests
from yarl import URL

from .utils import log
from .utils import open_file, remove_file, save_image, CACHE_DIR


class Handler:
    class InnerHandler:
        QRCODE_SAVE_PATH = os.path.join(CACHE_DIR, "qrcode.png")

        def __init__(self):
            self.session = requests.Session()
            self.qq_number: str

        def _get_gtk(self, val: str) -> int:
            hsh = 5381
            for i in val:
                hsh += (hsh << 5) + ord(i)
            return hsh & 0x7FFFFFFF

        def _decrypt_qrsig(self, qrsig) -> int:
            val = 0
            for i in qrsig:
                val += (val << 5) + ord(i)
            return 2147483647 & val

        def _get_time(self) -> str:
            return str(math.floor(time.time() * 1000))

        def _get_qrcode(self) -> None:
            qrcode = self.session.get(
                "https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.405252856480647&daid=5&pt_3rd_aid=0&u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone"
            )
            save_image(qrcode.content, self.QRCODE_SAVE_PATH)
            open_file(self.QRCODE_SAVE_PATH)

        def _check_qrcode(self) -> Optional[str]:
            qrsig = self.session.cookies["qrsig"]
            ptqrtoken = str(self._decrypt_qrsig(qrsig))
            url = URL(
                "https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qzone.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&js_ver=23083115&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&&o1vId=17651ac69455d734d04e49acc7987a50&pt_js_version=v1.47.0"
            ) % {
                "ptqrtoken": ptqrtoken,
                "action": "0-0-" + self._get_time(),
            }
            qrstatus = self.session.get(str(url))
            log("DEBUG", qrstatus.text)
            matcher = re.search(
                "ptuiCB\\('0','0','(https:[a-zA-Z0-9?=&/._%]+)','0'", qrstatus.text
            )
            return matcher.group(1) if matcher else None

        def login(self) -> None:
            self._get_qrcode()
            while True:
                time.sleep(1)
                check_sig_link = self._check_qrcode()
                if check_sig_link:
                    matcher = re.search("&uin=([0-9]+)&", check_sig_link)
                    if not matcher:
                        continue
                    self.qq_number = matcher.group(1)
                    self.session.get(check_sig_link)
                    break
            remove_file(self.QRCODE_SAVE_PATH)
            log("DEBUG", self.session.cookies["p_skey"])
            log("DEBUG", f"连接成功，qq 号码为 {self.qq_number}")

        def post(self, msg: str) -> None:
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
            ) % {"g_tk": self._get_gtk(self.session.cookies["p_skey"])}
            req = self.session.post(str(url), data=data)
            log("DEBUG", req.text)

    def __init__(self, *args, **kwargs):
        self.inner = self.InnerHandler(*args, **kwargs)

    def login(self) -> None:
        try:
            self.inner.login()
        except:
            pass

    def post(self, msg: str) -> None:
        try:
            self.inner.post(msg)
        except:
            pass


if __name__ == "__main__":
    log("DEBUG", "Starting")
    handler = Handler()
    handler.login()
    handler.post("test msg!")
