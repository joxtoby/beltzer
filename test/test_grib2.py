import random
import struct
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, Mock

from beltzer import grib2


class TestSection0(TestCase):
    def setUp(self):
        self.section_bytes = b"GRIB\x00\x00\x00\x02\x00\x00\x00\x00\x00\x0fUY"

    def test_parse_raises_assertion_error_if_not_grib(self):
        invalid_bytes = b"ABCD\x00\x00\x00\x02\x00\x00\x00\x00\x00\x0fUY"
        with self.assertRaises(AssertionError):
            grib2.Section0.parse(invalid_bytes)

    def test_parse_filetype(self):
        section = grib2.Section0.parse(self.section_bytes)
        self.assertEqual(section.filetype, "GRIB")

    def test_parse_reserved(self):
        section = grib2.Section0.parse(self.section_bytes)
        self.assertEqual(section.reserved_bytes, [b'\x00', b'\x00'])

    @patch("beltzer.grib2.table_lookup")
    def test_parse_discipline(self, mock_lookup):
        discipline = random.randint(0, 9)
        section = grib2.Section0.parse(
            b"GRIB\x00\x00" + discipline.to_bytes(1, "big") + b"\x02\x00\x00\x00\x00\x00\x0fUY"
        )
        self.assertEqual(section.discipline_code, discipline)
        mock_lookup.assert_called_with("0.0", discipline)

    def test_edition_raises_assertion_error_if_not_2(self):
        invalid_bytes = b"GRIB\x00\x00\x00\x01\x00\x00\x00\x00\x00\x0fUY"
        with self.assertRaises(AssertionError):
            grib2.Section0.parse(invalid_bytes)

    def test_edition(self):
        section = grib2.Section0.parse(self.section_bytes)
        self.assertEqual(section.edition, 2)

    def test_message_length(self):
        message_length = 123456789
        section = grib2.Section0.parse(b"GRIB\x00\x00\x00\x02" + message_length.to_bytes(8, "big"))
        self.assertEqual(section.total_message_length, message_length)


class TestSection1(TestCase):
    def setUp(self):
        self.section_number = 1
        self.originating_center_id = random.randint(0, 255)
        self.originating_subcenter_id = random.randint(0, 255)
        self.grib_master_tables_version = random.randint(1, 4)
        self.grib_local_tables_version = random.randint(0, 255)
        self.reference_time_significance = random.randint(0, 255)
        self.year = random.randint(1995, 2022)
        self.month = random.randint(1, 12)
        self.day = random.randint(1, 28)
        self.hour = random.randint(0, 23)
        self.minute = random.randint(0, 59)
        self.second = random.randint(0, 59)
        self.production_status = random.randint(0, 255)
        self.type_of_data = random.randint(0, 255)
        _bytes = (
            self.section_number.to_bytes(1, 'big') +
            self.originating_center_id.to_bytes(2, 'big') +
            self.originating_subcenter_id.to_bytes(2, 'big') +
            self.grib_master_tables_version.to_bytes(1, 'big') +
            self.grib_local_tables_version.to_bytes(1, 'big') +
            self.reference_time_significance.to_bytes(1, 'big') +
            self.year.to_bytes(2, 'big') +
            self.month.to_bytes(1, 'big') +
            self.day.to_bytes(1, 'big') +
            self.hour.to_bytes(1, 'big') +
            self.minute.to_bytes(1, 'big') +
            self.second.to_bytes(1, 'big') +
            self.production_status.to_bytes(1, 'big') +
            self.type_of_data.to_bytes(1, 'big')
        )
        self.section_length_no_reserved = len(_bytes) + 4
        self.bytes_no_reserved = self.section_length_no_reserved.to_bytes(4, 'big') + _bytes
        self.reserved_bytes = b'\x00\x01\x02'
        self.section_length_with_reserved = len(_bytes) + 4 + len(self.reserved_bytes)
        self.bytes_with_reserved = self.section_length_with_reserved.to_bytes(4, 'big') + _bytes + self.reserved_bytes
        self.no_reserved_section = grib2.Section1.parse(self.bytes_no_reserved)
        self.with_reserved_section = grib2.Section1.parse(self.bytes_with_reserved)

    def test_section_length(self):
        self.assertEqual(self.no_reserved_section.section_length, self.section_length_no_reserved)
        self.assertEqual(self.with_reserved_section.section_length, self.section_length_with_reserved)

    def test_section_number(self):
        self.assertEqual(self.no_reserved_section.section_number, self.section_number)
        self.assertEqual(self.with_reserved_section.section_number, self.section_number)

    def test_parse_raises_assertion_error_if_section_number_not_1(self):
        _bytes = self.bytes_no_reserved[:4] + b'\x02' + self.bytes_no_reserved[5:]
        with self.assertRaises(AssertionError):
            grib2.Section1.parse(_bytes)

    def test_originating_center_id(self):
        self.assertEqual(self.no_reserved_section.originating_center_id, self.originating_center_id)
        self.assertEqual(self.with_reserved_section.originating_center_id, self.originating_center_id)

    def test_originating_subcenter_id(self):
        self.assertEqual(self.no_reserved_section.originating_subcenter_id, self.originating_subcenter_id)
        self.assertEqual(self.with_reserved_section.originating_subcenter_id, self.originating_subcenter_id)

    def test_grib_master_tables_version(self):
        self.assertEqual(self.no_reserved_section.grib_master_tables_version, self.grib_master_tables_version)
        self.assertEqual(self.with_reserved_section.grib_master_tables_version, self.grib_master_tables_version)

    def test_grib_local_tables_version(self):
        self.assertEqual(self.no_reserved_section.grib_local_tables_version, self.grib_local_tables_version)
        self.assertEqual(self.with_reserved_section.grib_local_tables_version, self.grib_local_tables_version)

    def test_reference_time_significance(self):
        self.assertEqual(self.no_reserved_section.reference_time_significance, self.reference_time_significance)
        self.assertEqual(self.with_reserved_section.reference_time_significance, self.reference_time_significance)

    def test_year(self):
        self.assertEqual(self.no_reserved_section.year, self.year)
        self.assertEqual(self.with_reserved_section.year, self.year)

    def test_month(self):
        self.assertEqual(self.no_reserved_section.month, self.month)
        self.assertEqual(self.with_reserved_section.month, self.month)

    def test_day(self):
        self.assertEqual(self.no_reserved_section.day, self.day)
        self.assertEqual(self.with_reserved_section.day, self.day)

    def test_hour(self):
        self.assertEqual(self.no_reserved_section.hour, self.hour)
        self.assertEqual(self.with_reserved_section.hour, self.hour)

    def test_minute(self):
        self.assertEqual(self.no_reserved_section.minute, self.minute)
        self.assertEqual(self.with_reserved_section.minute, self.minute)

    def test_second(self):
        self.assertEqual(self.no_reserved_section.second, self.second)
        self.assertEqual(self.with_reserved_section.second, self.second)

    def test_production_status(self):
        self.assertEqual(self.no_reserved_section.production_status, self.production_status)
        self.assertEqual(self.with_reserved_section.production_status, self.production_status)

    def test_type_of_data(self):
        self.assertEqual(self.no_reserved_section.type_of_data, self.type_of_data)
        self.assertEqual(self.with_reserved_section.type_of_data, self.type_of_data)

    def test_reserved_bytes(self):
        self.assertIsNone(self.no_reserved_section.reserved)
        self.assertEqual(self.with_reserved_section.reserved, self.reserved_bytes)

    def test_reference_time(self):
        self.assertEqual(self.no_reserved_section.reference_time, datetime(self.year, self.month, self.day, self.hour, self.minute, self.second))

class TestSection4(TestCase):
    @patch('beltzer.grib2.templates.load')
    def test_parse_with_no_optional_vals(self, mock_load):
        section_number = 4
        num_coordinate_vals_after_template = 0
        product_definition_template_num = random.randint(0, 1000)
        template_data = b'fake template data'
        optional_coordinate_vals = None
        _bytes = (
            section_number.to_bytes(1, 'big') +
            num_coordinate_vals_after_template.to_bytes(2, 'big') +
            product_definition_template_num.to_bytes(2, 'big') +
            template_data
        )
        section_length = len(_bytes) + 4
        _bytes = section_length.to_bytes(4, 'big') + _bytes
        section = grib2.Section4.parse(_bytes)
        self.assertEqual(section.section_number, 4)
        self.assertEqual(section.num_coordinate_vals_after_template, num_coordinate_vals_after_template)
        self.assertIsNone(section.optional_coordinate_vals)
        mock_load.assert_called_with(f'4.{product_definition_template_num}', template_data)

    @patch('beltzer.grib2.templates.load')
    def test_parse_with_optional_vals(self, mock_load):
        template_data = b'fake template data'
        mock_load.return_value=Mock(length=len(template_data))
        section_number = 4
        num_coordinate_vals_after_template = 2
        product_definition_template_num = random.randint(0, 1000)
        optional_coordinate_vals = b''.join([struct.pack('f', 1.234), struct.pack('f', 5.678)])
        _bytes = (
            section_number.to_bytes(1, 'big') +
            num_coordinate_vals_after_template.to_bytes(2, 'big') +
            product_definition_template_num.to_bytes(2, 'big') +
            template_data +
            optional_coordinate_vals
        )
        section_length = len(_bytes) + 4
        _bytes = section_length.to_bytes(4, 'big') + _bytes
        section = grib2.Section4.parse(_bytes)
        self.assertEqual(section.section_number, 4)
        self.assertEqual(section.num_coordinate_vals_after_template, num_coordinate_vals_after_template)
        mock_load.assert_called_with(f'4.{product_definition_template_num}', template_data + optional_coordinate_vals)
        self.assertEqual(section.optional_coordinate_vals, optional_coordinate_vals)

