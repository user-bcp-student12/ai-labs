from pathlib import Path


def store_upload(upload_dir: str, filename: str, content: bytes) -> Path:
    target = Path(upload_dir) / filename
    target.write_bytes(content)
    return target