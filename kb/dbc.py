"""WDBC (3.3.5 client DBC) reader. Standard library only.

Fail-closed by design: every structural assumption about a file is checked,
and a mismatch raises DbcError rather than returning partial data. The
gtOCTClassCombatRatingScalar incident (S243) is the reason: that table is
(index, float) pairs while its siblings are bare float columns, and a reader
that assumed one shape for all six would have silently mis-read it.

Format reference: WDBC header is 20 bytes -
    magic 'WDBC', record_count, field_count, record_size, string_block_size
followed by record_count * record_size bytes of records, then the string
block. All integers little-endian uint32.
"""

import struct

WDBC_MAGIC = b"WDBC"
HEADER_SIZE = 20


class DbcError(Exception):
    """Raised for any structural problem with a DBC file."""


class DbcFile(object):
    """A parsed WDBC file: header fields plus the raw record block."""

    def __init__(self, path, record_count, field_count, record_size, body):
        self.path = path
        self.record_count = record_count
        self.field_count = field_count
        self.record_size = record_size
        self.body = body


def read_wdbc(path):
    """Read and structurally validate a WDBC file. Returns a DbcFile."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < HEADER_SIZE:
        raise DbcError("%s: file shorter than WDBC header" % path)
    magic, nrec, nfield, recsize, strsize = struct.unpack_from(
        "<4sIIII", data, 0)
    if magic != WDBC_MAGIC:
        raise DbcError("%s: bad magic %r, expected WDBC" % (path, magic))
    expected = HEADER_SIZE + nrec * recsize + strsize
    if len(data) != expected:
        raise DbcError(
            "%s: size mismatch: header says %d bytes "
            "(20 + %d*%d + %d), file is %d"
            % (path, expected, nrec, recsize, strsize, len(data)))
    body = data[HEADER_SIZE:HEADER_SIZE + nrec * recsize]
    return DbcFile(path, nrec, nfield, recsize, body)


def read_float_column(path, expect_records=None):
    """Read a single-float-per-record gt table. Returns a list of floats.

    Refuses (fail closed) any file whose record shape is not exactly one
    4-byte field, and optionally any file whose record count is not the
    expected one.
    """
    dbc = read_wdbc(path)
    if dbc.field_count != 1 or dbc.record_size != 4:
        raise DbcError(
            "%s: expected 1 float field per record, found "
            "field_count=%d record_size=%d"
            % (path, dbc.field_count, dbc.record_size))
    if expect_records is not None and dbc.record_count != expect_records:
        raise DbcError(
            "%s: expected %d records, found %d"
            % (path, expect_records, dbc.record_count))
    return list(struct.unpack("<%df" % dbc.record_count, dbc.body))


def read_index_float_pairs(path, expect_records=None):
    """Read an (int index, float value) table such as
    gtOCTClassCombatRatingScalar. Returns a list of (index, value) tuples.
    """
    dbc = read_wdbc(path)
    if dbc.field_count != 2 or dbc.record_size != 8:
        raise DbcError(
            "%s: expected (index, float) records, found "
            "field_count=%d record_size=%d"
            % (path, dbc.field_count, dbc.record_size))
    if expect_records is not None and dbc.record_count != expect_records:
        raise DbcError(
            "%s: expected %d records, found %d"
            % (path, expect_records, dbc.record_count))
    out = []
    for i in range(dbc.record_count):
        idx, val = struct.unpack_from("<if", dbc.body, i * 8)
        out.append((idx, val))
    return out
