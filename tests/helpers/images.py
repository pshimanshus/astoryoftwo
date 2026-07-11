from pathlib import Path


def encoded_image_bytes(
    *,
    width: int,
    height: int,
    value: int = 240,
    extension: str = ".png",
) -> bytes:
    import cv2
    import numpy as np

    ok, encoded = cv2.imencode(
        extension,
        np.full((height, width, 3), value, dtype=np.uint8),
    )
    assert ok
    return encoded.tobytes()


def write_png(path: Path, width: int = 1080, height: int = 1440, value: int = 240) -> None:
    path.write_bytes(encoded_image_bytes(width=width, height=height, value=value, extension=".png"))


def write_jpeg(path: Path, width: int = 64, height: int = 64, value: int = 240) -> None:
    path.write_bytes(encoded_image_bytes(width=width, height=height, value=value, extension=".jpg"))
