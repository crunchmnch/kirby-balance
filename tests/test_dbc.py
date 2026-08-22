import os
import struct
import tempfile
import unittest

from kb import dbc


def wdbc_bytes(nrec, nfield, recsize, body, strblock=b"\x00"):
    return (b"WDBC" + struct.pack("<IIII", nrec, nfield, recsize,
                                  len(strblock)) + body + strblock)


class DbcReaderTests(unittest.TestCase):
    def write(self, data):
        fd, path = tempfile.mkstemp(suffix=".dbc")
        os.write(fd, data)
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return path

    def test_reads_float_column(self):
        body = struct.pack("<3f", 1.5, 2.5, 3.5)
        path = self.write(wdbc_bytes(3, 1, 4, body))
        self.assertEqual(dbc.read_float_column(path), [1.5, 2.5, 3.5])

    def test_refuses_bad_magic(self):
        path = self.write(b"XDBC" + b"\x00" * 16)
        with self.assertRaises(dbc.DbcError):
            dbc.read_wdbc(path)

    def test_refuses_truncated_file(self):
        body = struct.pack("<3f", 1.0, 2.0, 3.0)
        data = wdbc_bytes(3, 1, 4, body)
        path = self.write(data[:-5])
        with self.assertRaises(dbc.DbcError):
            dbc.read_wdbc(path)

    def test_refuses_wrong_record_shape(self):
        # The gtOCTClassCombatRatingScalar trap: (index, float) pairs must
        # not be readable as a float column.
        body = struct.pack("<if", 1, 1.0)
        path = self.write(wdbc_bytes(1, 2, 8, body))
        with self.assertRaises(dbc.DbcError):
            dbc.read_float_column(path)
        self.assertEqual(
            dbc.read_index_float_pairs(path), [(1, 1.0)])

    def test_refuses_unexpected_record_count(self):
        body = struct.pack("<2f", 1.0, 2.0)
        path = self.write(wdbc_bytes(2, 1, 4, body))
        with self.assertRaises(dbc.DbcError):
            dbc.read_float_column(path, expect_records=1100)
