import os
from pathlib import Path

from pydantic import Field, BaseModel, validator


ADAPTER_NAME = "Qzone"


class Config(BaseModel):
    bot_id: str = Field(default="qzone", alias="qzone_bot_id")
    cache_path: Path = Field(
        default=Path(__file__).parent / "cache",
        validate_default=True,
        alias="qzone_cache_path",
    )

    @validator("cache_path")
    @classmethod
    def is_dir(cls, v: Path) -> Path:
        if os.path.isfile(v):
            raise ValueError("'cache_path' must point to a directory")
        if not os.path.isdir(v):
            os.makedirs(v)
        return v

    @property
    def qrcode_path(self) -> Path:
        return self.cache_path / "qrcode.png"

    @property
    def cookie_path(self) -> Path:
        return self.cache_path / "cookies"

    class Config:
        extra = "ignore"
        allow_population_by_field_name = True
