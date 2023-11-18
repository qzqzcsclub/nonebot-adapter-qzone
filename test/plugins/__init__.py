import base64
from pathlib import Path

SAMPLE_IMAGE_PATH = Path(__file__).parent.parent / "sample.png"


def to_uri(path: Path):
    with open(path, "rb") as file:
        binary = file.read()
    code = base64.b64encode(binary).decode("utf-8")
    return f"data:image/{path.suffix[1:]};base64,{code}"
