from typing_extensions import override

from nonebot.exception import AdapterException
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable

from .config import ADAPTER_NAME


class QzoneAdapterException(AdapterException):
    @override
    def __init__(self) -> None:
        super().__init__(ADAPTER_NAME)


class ApiNotAvailable(QzoneAdapterException, BaseApiNotAvailable):
    pass


class NotLoggedIn(QzoneAdapterException):
    pass


class AlreadyLoggedIn(QzoneAdapterException):
    pass
