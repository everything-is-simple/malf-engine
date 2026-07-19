from datetime import date
from pathlib import Path

import pytest

from boundary import DayFileRejected, atomic_write_json, make_fixture, parse_day_file, sha256_file

VALID = [
    (20260716, 1123, 1140, 1110, 1132, 1000.5, 200, 0),
    (20260717, 1132, 1150, 1120, 1145, 1200.5, 220, 0),
]


def test_valid_32_byte_records_and_raw_integer_prices(tmp_path: Path):
    source = tmp_path / "synthetic.day"
    make_fixture(source, VALID)
    bars = parse_day_file(source, evaluation_date=date(2026, 7, 19))
    assert source.stat().st_size == 64
    assert bars[0].open_raw == 1123
    assert bars[1].close_raw == 1145


@pytest.mark.parametrize(
    "rows, reason",
    [
        ([VALID[0], VALID[0]], "date_not_strictly_increasing"),
        ([VALID[1], VALID[0]], "date_not_strictly_increasing"),
        ([(20260720, 1123, 1140, 1110, 1132, 10.0, 1, 0)], "future_date"),
        ([(20260716, 1123, 1120, 1110, 1132, 10.0, 1, 0)], "invalid_high"),
        ([(20260716, 1123, 1140, 1130, 1120, 10.0, 1, 0)], "invalid_low"),
    ],
)
def test_any_bad_bar_rejects_whole_symbol(tmp_path: Path, rows, reason):
    source = tmp_path / "synthetic.day"
    make_fixture(source, rows)
    with pytest.raises(DayFileRejected, match=reason):
        parse_day_file(source, evaluation_date=date(2026, 7, 19))


def test_truncated_record_rejected(tmp_path: Path):
    source = tmp_path / "synthetic.day"
    make_fixture(source, VALID)
    source.write_bytes(source.read_bytes()[:-1])
    with pytest.raises(DayFileRejected, match="invalid_record_length"):
        parse_day_file(source, evaluation_date=date(2026, 7, 19))


def test_hash_and_atomic_pointer(tmp_path: Path):
    pointer = tmp_path / "current.json"
    atomic_write_json(pointer, {"snapshot_id": "s-001"})
    first = sha256_file(pointer)
    atomic_write_json(pointer, {"snapshot_id": "s-002"})
    assert sha256_file(pointer) != first
    assert not list(tmp_path.glob("*.tmp"))
