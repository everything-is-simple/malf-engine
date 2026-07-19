"""Synthetic TDX .day parsing and atomic publication primitives for factory trials."""
from __future__ import annotations

import hashlib
import json
import os
import struct
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

RECORD = struct.Struct("<5If2I")


class DayFileRejected(ValueError):
    """The whole symbol file is rejected; callers must not skip a bad bar."""


@dataclass(frozen=True)
class DayBar:
    trading_date: date
    open_raw: int
    high_raw: int
    low_raw: int
    close_raw: int
    amount: float
    volume: int
    reserved: int


def _parse_date(value: int) -> date:
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except ValueError as exc:
        raise DayFileRejected("invalid_date") from exc


def parse_day_file(path: Path, *, evaluation_date: date) -> tuple[DayBar, ...]:
    before = path.stat()
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise DayFileRejected("source_changed_during_read")
    if len(payload) == 0 or len(payload) % RECORD.size:
        raise DayFileRejected("invalid_record_length")

    bars: list[DayBar] = []
    previous: date | None = None
    for raw in RECORD.iter_unpack(payload):
        trading_date = _parse_date(raw[0])
        if trading_date > evaluation_date:
            raise DayFileRejected("future_date")
        if previous is not None and trading_date <= previous:
            raise DayFileRejected("date_not_strictly_increasing")
        bar = DayBar(trading_date, raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7])
        if min(bar.open_raw, bar.high_raw, bar.low_raw, bar.close_raw) <= 0:
            raise DayFileRejected("non_positive_price")
        if bar.high_raw < max(bar.open_raw, bar.close_raw, bar.low_raw):
            raise DayFileRejected("invalid_high")
        if bar.low_raw > min(bar.open_raw, bar.close_raw, bar.high_raw):
            raise DayFileRejected("invalid_low")
        if bar.volume < 0 or bar.amount < 0:
            raise DayFileRejected("negative_volume_or_amount")
        bars.append(bar)
        previous = trading_date
    return tuple(bars)


def make_fixture(path: Path, rows: Iterable[tuple[int, int, int, int, int, float, int, int]]) -> None:
    path.write_bytes(b"".join(RECORD.pack(*row) for row in rows))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    try:
        with tmp.open("wb") as fh:
            fh.write(encoded)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
