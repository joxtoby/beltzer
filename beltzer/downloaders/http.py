import requests
from typing import Optional


def downloader(url: str, start_byte: Optional[int] = 0, end_byte: Optional[int] = None) -> bytes:
    """A simple function to download a range of bytes from a url."""
    session = requests.Session()
    if end_byte is not None:
        headers = {"Range": f"bytes={start_byte}-{end_byte}"}
    else:
        headers = {"Range": f"bytes={start_byte}-"}
    response = session.get(url, headers=headers, stream=True)
    data = b""
    for chunk in response.iter_content(1024 * 1024):
        data += chunk
    with open("test.grb", "wb") as f:
        f.write(data)
    return data
