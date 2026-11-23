"""Bộ giải mã các kiểu dữ liệu mà đầu cân thường gửi qua RS232.

Hỗ trợ:
- `adstyle`  : kiểu "ST,GS,+0012340kg" (A&D và nhiều đầu cân khác). ST = ổn định, US = chưa ổn định,
               OL = quá tải; GS = tổng, NT = tịnh.
- `reversed` : kiểu đảo chuỗi "=0.04321" của đầu cân XK3190-A9 (chế độ tf=0) — chữ số bị gửi ngược.
- `generic`  : tìm số đầu tiên trong dòng, kèm đơn vị kg/t/g nếu có.
`parse(line, "auto")` thử lần lượt các kiểu trên.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

UNITS = {"kg": 1.0, "t": 1000.0, "g": 0.001, "lb": 0.45359237}


@dataclass(frozen=True)
class Reading:
    kg: float
    stable: bool | None = None   # None = đầu cân không báo
    overload: bool = False
    net: bool = False
    raw: str = ""


_AD = re.compile(r"^(ST|US|OL),(GS|NT|TR),([+-]?)\s*([0-9.]+)\s*([a-z]*)$", re.IGNORECASE)
_REV = re.compile(r"^=([0-9.]{5,9})$")
_GEN = re.compile(r"([+-]?\s*\d+(?:[.,]\d+)?)\s*(kg|t|g|lb)?\b", re.IGNORECASE)


def _to_kg(value: float, unit: str) -> float:
    return round(value * UNITS.get(unit.lower() or "kg", 1.0), 3)


def parse_adstyle(line: str) -> Reading | None:
    m = _AD.match(line.strip())
    if not m:
        return None
    status, kind, sign, num, unit = m.groups()
    if status.upper() == "OL":
        return Reading(0.0, False, True, kind.upper() == "NT", line)
    v = float(num) * (-1 if sign == "-" else 1)
    return Reading(_to_kg(v, unit), status.upper() == "ST", False, kind.upper() == "NT", line)


def parse_reversed(line: str) -> Reading | None:
    m = _REV.match(line.strip())
    if not m:
        return None
    digits = m.group(1)[::-1]
    try:
        return Reading(round(float(digits), 3), None, False, False, line)
    except ValueError:
        return None


def parse_generic(line: str) -> Reading | None:
    m = _GEN.search(line)
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace(",", ".")
    return Reading(_to_kg(float(num), m.group(2) or "kg"), None, False, False, line)


PARSERS = {"adstyle": parse_adstyle, "reversed": parse_reversed, "generic": parse_generic}


def parse(line: str, fmt: str = "auto") -> Reading | None:
    line = line.strip("\x02\x03\r\n\t ")
    if not line:
        return None
    if fmt != "auto":
        return PARSERS[fmt](line)
    for name in ("adstyle", "reversed", "generic"):
        r = PARSERS[name](line)
        if r is not None:
            return r
    return None
