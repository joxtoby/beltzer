import struct
from io import BytesIO
from typing import Callable, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from beltzer import templates
from beltzer.downloaders import RemoteFilePointer
from beltzer.tables import table_lookup


@dataclass
class Section0:
    """
    Indicator Section
    https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_sect0.shtml
    """

    filetype: str
    reserved_bytes: bytes
    discipline_code: int
    discipline_meaning: str
    edition: int
    total_message_length: int

    section_length: int = 16

    @classmethod
    def parse(cls, data: bytes):

        # Octet 1-4 - 'GRIB'
        filetype_bytes = struct.iter_unpack(">c", data[:4])
        filetype = b"".join([b[0] for b in filetype_bytes]).decode("utf-8")
        assert filetype == "GRIB"

        # Octet 5-6 - Reserved
        reserved_bytes = [b[0] for b in (struct.iter_unpack(">c", data[4:6]))]

        # Octet 7 - Discipline
        discipline_code = data[6]
        discipline_meaning = table_lookup("0.0", discipline_code)[0]

        # Octet 8 - Edition number (2 for GRIB2)
        edition = data[7]
        assert edition == 2

        # Octet 9-16 - Total length of GRIB message in octets
        total_message_length = struct.unpack(">q", data[8 : cls.section_length])[0]
        return cls(
            filetype=filetype,
            reserved_bytes=reserved_bytes,
            discipline_code=discipline_code,
            discipline_meaning=discipline_meaning,
            edition=edition,
            total_message_length=total_message_length,
        )


@dataclass
class Section1:
    """
    Indicator Section
    https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_sect1.shtml
    """

    section_length: int
    section_number: int
    originating_center_id: int
    originating_subcenter_id: int
    grib_master_tables_version: int
    grib_local_tables_version: int
    reference_time_significance: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    production_status: int
    type_of_data: int
    reserved: bytes

    @classmethod
    def parse(cls, data: bytes):
        section_length = struct.unpack(">l", data[:4])[0]
        section_number = data[4]
        assert section_number == 1

        return cls(
            section_length=section_length,
            section_number=section_number,
            originating_center_id=struct.unpack(">h", data[5:7])[0],
            originating_subcenter_id=struct.unpack(">h", data[7:9])[0],
            grib_master_tables_version=data[9],
            grib_local_tables_version=data[10],
            reference_time_significance=data[11],
            year=struct.unpack(">h", data[12:14])[0],
            month=data[14],
            day=data[15],
            hour=data[16],
            minute=data[17],
            second=data[18],
            production_status=data[19],
            type_of_data=data[20],
            reserved=data[21:section_length] if section_length > 21 else None,
        )

    @property
    def reference_time(self) -> datetime:
        return datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)


@dataclass
class Section4:
    """
    Product Definition Section
    https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_sect4.shtml
    """

    section_length: int
    section_number: int
    num_coordinate_vals_after_template: int
    product_definition_template_num: int
    product_definition_template: templates.BaseTemplate
    optional_coordinate_vals: Optional[bytes] = None
    _parameter: Optional[str] = field(init=False, repr=False, default=None)

    @classmethod
    def parse(cls, data: bytes):
        section_length = struct.unpack(">l", data[:4])[0]
        section_number = data[4]
        num_coord_vals_after_template = struct.unpack(">h", data[5:7])[0]
        product_definition_template_num = struct.unpack(">h", data[7:9])[0]
        template = templates.load(f"4.{product_definition_template_num}", data[9:])
        optional_coordinate_vals = data[9 + template.length :] if num_coord_vals_after_template > 0 else None
        return cls(
            section_length=section_length,
            section_number=section_number,
            num_coordinate_vals_after_template=num_coord_vals_after_template,
            product_definition_template_num=product_definition_template_num,
            product_definition_template=template,
            optional_coordinate_vals=optional_coordinate_vals,
        )

    @property
    def parameter(self) -> str:
        if self._parameter is None:
            try:
                result = table_lookup(
                    f"4.2.0.{self.product_definition_template.parameter_category}",
                    self.product_definition_template.parameter_number,
                )
                description, unit, abbrev = result
                self._parameter = abbrev
                self._description = description
            except (FileNotFoundError, ValueError):
                self._parameter = (
                    f"cat {self.product_definition_template.parameter_category}, "
                    f"param {self.product_definition_template.parameter_number}"
                )
        return self._parameter

    @property
    def description(self) -> str:
        if self._description is None:
            _ = self.parameter
        return self._description


class Message:
    section0: Section0
    section1: Section1
    section4: Section4
    raw_bytes: bytes
    first_byte: int
    message_number: int

    def __init__(self, message_number: int):
        self.message_number = message_number

    @property
    def total_length(self) -> int:
        return self.section0.total_message_length

    @property
    def reference_time(self) -> datetime:
        return self.section1.reference_time

    @property
    def parameter(self) -> str:
        return self.section4.parameter

    @property
    def description(self) -> str:
        return self.section4.description

    @property
    def level(self) -> str:
        return self.section4.product_definition_template.level

    @property
    def lead_seconds(self) -> int:
        pdt = self.section4.product_definition_template
        return timedelta(**{pdt.forecast_time_unit + "s": pdt.forecast_time}).total_seconds()

    @classmethod
    def from_bytes(cls, _bytes: bytes, msg_num: Optional[int] = 1) -> "Message":
        fp = BytesIO(_bytes)
        return cls.from_fileobj(fp, msg_num)

    @classmethod
    def from_fileobj(cls, fp: BytesIO, msg_num: Optional[int] = 1) -> "Message":
        msg = cls(msg_num)
        msg.first_byte = fp.tell()
        section0_data = fp.read(16)
        if not section0_data:
            return None
        msg.section0 = Section0.parse(section0_data)
        msg.raw_bytes = section0_data

        while True:
            # For sections 1-7, the first 5 bytes in th section contain the
            # section number and byte length of the section.
            data = fp.read(5)
            section_length = struct.unpack(">l", data[:4])[0]
            section_number = data[4]

            # Read the rest of the section bytes
            data += fp.read(section_length - 5)
            msg.raw_bytes += data

            if section_number == 1:
                msg.section1 = Section1.parse(data)
            elif section_number == 4:
                msg.section4 = Section4.parse(data)
            elif section_number == 7:
                msg.raw_bytes += fp.read(4)
                return msg


    @classmethod
    def from_remote_file(cls, rfp: RemoteFilePointer, msg_num: Optional[int] = 1) -> "Message":
        msg = cls(msg_num)
        msg.first_byte = rfp.tell()
        section0_data = rfp.read(16)
        if not section0_data:
            return None
        msg.section0 = Section0.parse(section0_data)

        while True:
            data = rfp.read(5)
            section_length = struct.unpack(">l", data[:4])[0]
            section_number = data[4]

            if section_number == 1:
                data += rfp.read(section_length - 5)
                msg.section1 = Section1.parse(data)
            elif section_number == 4:
                data += rfp.read(section_length - 5)
                msg.section4 = Section4.parse(data)
            elif section_number == 7:
                rfp.seek(section_length - 5, 1)
                rfp.seek(4, 1) # for the tail "7777" indicator
                return msg
            else:
                rfp.seek(section_length - 5, 1)


class Grib2:

    messages: List[Message] = []

    def get_message(self, parameter: Optional[str] = None, level: Optional[str] = None) -> Optional[Message]:
        for message in self.messages:
            if message.parameter == parameter and message.level == level:
                return message
        return None

    @classmethod
    def open_grib(cls, grib: Union[str, bytes, BytesIO]) -> "Grib2":

        if isinstance(grib, str):
            _in = open(grib, "rb")
        elif isinstance(grib, bytes):
            _in = BytesIO(grib)
        else:
            _in = grib

        msg_num = 1
        grib2 = cls()
        while True:
            message = Message.from_fileobj(_in, msg_num=msg_num)
            if message:
                grib2.messages.append(message)
                msg_num += 1
            else:
                return grib2

    @classmethod
    def open_remote(cls, url: str, downloader: Callable) -> "Grib2":
        msg_num = 1
        grib2 = cls()
        rfp = RemoteFilePointer(url, downloader)
        while True:
            message = Message.from_remote_file(rfp, msg_num)
            if message:
                grib2.messages.append(message)
                msg_num += 1
            else:
                return grib2


def extract_first_message(_bytes: bytes) -> Optional[Message]:
    """Returns the first full GRIB2 message from the given byte string, or None if no message is found."""
    for i in range(len(_bytes)):
        if _bytes[i : i + 4] == b"GRIB":
            return Message.from_bytes(_bytes[i:])
    return None
