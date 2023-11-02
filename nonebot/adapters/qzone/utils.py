import os
import subprocess
import platform
from typing import Any, Union
from pathlib import Path
from enum import Enum

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


def _ensure_dir(path: Union[Path, str]) -> None:
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def save_image(content: Any, path: Union[Path, str]) -> None:
    _ensure_dir(path)
    with open(path, "wb") as file:
        file.write(content)


def remove_file(path: Union[Path, str]) -> None:
    os.remove(path)


def open_file(path: Union[Path, str]) -> None:
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


log = logger_wrapper(ADAPTER_NAME)
