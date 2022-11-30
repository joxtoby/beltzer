import requests

from typing import Callable, Optional


class RemoteFilePointer:
    """Similar to a regular python file handle, but for remote files."""

    def __init__(self, url: str, downloader: Callable):
        self.url: str = url
        self.download: Callable = downloader
        self._byte_position: int = 0

    def tell(self) -> int:
        return self._byte_position

    def read(self, num_bytes: int) -> bytes:
        _bytes = self.download(self.url, self._byte_position, self._byte_position + num_bytes - 1)
        self._byte_position += num_bytes
        return _bytes

    def seek(self, offset: int, whence: Optional[int] = 0) -> None:
        if whence == 0:
            self._byte_position = offset
        elif whence == 1:
            self._byte_position += offset
        elif whence == 2:
            raise NotImplementedError


def http_download(url: str, start_byte: Optional[int] = 0, end_byte: Optional[int] = None) -> bytes:
    """A simple function to download a range of bytes from a url."""
    session = requests.Session()
    _range = byte_range(start_byte, end_byte)
    headers = {"Range": _range}
    response = session.get(url, headers=headers, stream=True)
    data = b""
    for chunk in response.iter_content(1024 * 1024):
        data += chunk
    return data


def byte_range(start_byte: int, end_byte: int) -> str:
    if end_byte is not None:
        return f"bytes={start_byte}-{end_byte}"
    return f"bytes={start_byte}-"

