import os
import logging
import struct
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Callable, Optional, Union

from beltzer import grib2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

__version__ = "0.1.0"

@dataclass
class IndexEntry:
    message_number: int
    first_byte: int
    last_byte: int
    reference_time: datetime
    parameter: str
    level: str
    lead_seconds: int

    def to_ncep_row(self) -> str:
        """
        Return an index file row using NCEP-style formatting
        ex: 1:0:d=2022050206:PRMSL:mean sea level:26 hour fcst:
        """
        return ":".join(
            [
                str(self.message_number),
                str(self.first_byte),
                f"d={self.reference_time}",
                self.parameter,
                self.level,
                f"{int(self.lead_seconds / 3600)} hour fcst:",
            ]
        )


class Index:
    def __init__(self):
        self.entries = []

    def get_entry(
        self, message_number: Optional[int] = None, parameter: Optional[str] = None, level: Optional[str] = None
    ) -> IndexEntry:
        for entry in self.entries:
            if entry.message_number is not None and entry.message_number == message_number:
                return entry
            if entry.parameter == parameter and entry.level == level:
                return entry

    def to_ncep_idx(self, idx_filename: str) -> None:
        with open(idx_filename, "w") as _out:
            for entry in self.entries:
                _out.write(entry.to_ncep_row() + "\n")

    @classmethod
    def from_ncep_idx(cls, idx: str) -> "Index":
        index = cls()
        with open(idx) as _in:
            rows = _in.split("\n")
            for i in range(len(rows)):
                message_number, first_byte, ref_time, parameter, level, lead, _ = rows[i].split(":")
                next_first_byte = rows[i + 1].split(":")[1]
                index.entries.append(
                    IndexEntry(
                        message_number=int(message_number),
                        first_byte=int(first_byte),
                        last_byte=int(next_first_byte - 1),
                        reference_time=ref_time,
                        parameter=parameter,
                        level=level,
                        lead_seconds=lead,
                    )
                )
        return index

    @classmethod
    def from_grib2(cls, grib2: grib2.Grib2) -> "Index":
        index = cls()
        for message in grib2.messages:
            index.entries.append(
                IndexEntry(
                    message_number=message.message_number,
                    first_byte=message.first_byte,
                    last_byte=message.first_byte + message.total_length - 1,
                    reference_time=message.reference_time,
                    parameter=message.parameter,
                    level=message.level,
                    lead_seconds=message.lead_seconds,
                )
            )
        return index


def find_remote_message(
    grib_url: str, index: Index, message_number: int, downloader: Callable, byte_offset: Optional[int] = 0
) -> grib2.Message:
    logger.info(f"message number: {message_number}")
    entry = index.get_entry(message_number=message_number)
    first_byte = entry.first_byte + byte_offset
    last_byte = entry.last_byte + byte_offset
    logger.info(f"first_byte: {first_byte}, last_byte: {last_byte}")

    # Request a range of bytes that's twice the size of the original byte range to help ensure we get a full GRIB msg
    byte_length = last_byte - first_byte
    request_first_byte = first_byte - int(byte_length / 2)
    request_last_byte = last_byte + int(byte_length / 2)
    _bytes = downloader(grib_url, request_first_byte, request_last_byte)

    # Parse the bytes into a Message
    remote_message = grib2.extract_first_message(_bytes)
    logger.info(remote_message.parameter, remote_message.level)
    if remote_message.parameter == entry.parameter and remote_message.level == entry.level:
        # This is the message we wanted
        return remote_message
    else:
        # Get the equivalent of the remote message from the local index
        equiv_entry = index.get_entry(parameter=remote_message.parameter, level=remote_message.level)
        logger.info(f"equiv entry message number: {equiv_entry.message_number}")
        # Use the difference in byte position from the equiv_entry and the original request to determine the next
        # best guess and try again.
        offset_bytes = int((int(first_byte) - int(equiv_entry.first_byte)))
        logger.info(f"first byte: {first_byte}, equiv first byte: {equiv_entry.first_byte}")
        # if message_number > equiv_entry.message_number:
        #    offset_bytes *= 1
        logger.info(f"offset bytes: {offset_bytes}")
        return find_remote_message(grib_url, index, message_number, downloader, offset_bytes)


def load_remote_message(
    index: Index,
    grib_url: str,
    downloader: Callable,
    message: Optional[grib2.Message] = None,
    message_number: Optional[int] = None,
) -> grib2.Message:
    if message is None:
        message = [m for m in index.messages if m.message_number == message_number]
    _bytes = downloader(grib_url, message.first_byte, message.first_byte + message.total_length - 1)
    return grib2.extract_first_message(_bytes)
