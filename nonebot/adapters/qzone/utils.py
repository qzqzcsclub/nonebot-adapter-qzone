from enum import Enum
import os
import subprocess
import platform
import sys
from typing import Any

from nonebot.utils import logger_wrapper

from .config import ADAPTER_NAME


class Platform(Enum):
    MACOS = "MacOS"
    WINDOWS = "Windows"
    WSL = "WSL"
    LINUX = "Linux"
    UNKNOWN = "Unknown"

    @staticmethod
    def get_platform() -> "Platform":
        match platform.system():
            case "Darwin":
                return Platform.MACOS
            case "Windows":
                return Platform.WINDOWS
            case "Linux":
                if "microsoft" in platform.release():
                    return Platform.WSL
                else:
                    return Platform.LINUX
            case _:
                return Platform.UNKNOWN


BASE_DIR: str = os.getcwd()
CACHE_DIR: str = os.path.join(BASE_DIR, "cache")
PLATFORM: Platform = Platform.get_platform()

QRCODE_SAVE_PATH = os.path.join(CACHE_DIR, "qrcode.png")


def _ensure_dir(path: str) -> None:
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def save_image(content: Any, path: str) -> None:
    _ensure_dir(path)
    with open(path, "wb") as file:
        file.write(content)


def remove_file(path: str) -> None:
    os.remove(path)


def open_file(path: str) -> None:
    match PLATFORM:
        case Platform.MACOS:
            os.system(f"open {path}")
        case Platform.WINDOWS:
            ...
        case Platform.WSL:
            subprocess.call(["wslview", path])
        case Platform.LINUX:
            subprocess.call(["xdg-open", path])
        case _:
            raise OSError("Unknown platform")


# def log(identifier: str, msg: Any) -> None:
#     print(f"[{identifier}] {msg}", file=sys.stderr)


log = logger_wrapper(ADAPTER_NAME)
