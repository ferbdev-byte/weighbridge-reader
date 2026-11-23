"""Dòng lệnh: đọc cân thật hoặc giả lập, in khối lượng chốt và ghi phiếu ra JSON Lines."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from . import __version__
from .parsers import parse
from .sources import serial_lines, simulate
from .stability import StabilityDetector
from .ticket import Ticket


def _n(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def run(lines, fmt: str, detector: StabilityDetector, plates: list[str], out=None, price: int = 0,
        impurity: float = 0.0) -> list[Ticket]:
    tickets: list[Ticket] = []
    queue = list(plates)
    current: Ticket | None = None
    for line in lines:
        r = parse(line, fmt)
        if r is None:
            continue
        kg = detector.feed(r)
        if kg is None:
            continue
        if current is None:
            plate = queue.pop(0) if queue else f"XE-{len(tickets) + 1:03d}"
            current = Ticket(plate, unit_price=price, impurity_pct=impurity)
        lan = current.record(kg)
        print(f"[{datetime.now():%H:%M:%S}] {current.plate}: cân {'lần 1' if lan == 'lan_1' else 'lần 2'} = {_n(kg)} kg")
        if current.complete:
            line = f"    → hàng {_n(current.net_kg)} kg, trừ {_n(current.deduction_kg)} kg, tính {_n(current.payable_kg)} kg"
            if current.amount:
                line += f" = {_n(current.amount)} đ"
            print(line)
            if out:
                out.write(json.dumps(current.to_dict(), ensure_ascii=False) + "\n")
                out.flush()
            tickets.append(current)
            current = None
    return tickets


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="weighbridge", description="Đọc số cân từ đầu cân điện tử.")
    p.add_argument("--version", action="version", version=f"weighbridge {__version__}")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="cổng COM, vd. COM3")
    src.add_argument("--simulate", action="store_true", help="chạy giả lập, không cần đầu cân")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--format", default="auto", choices=["auto", "adstyle", "reversed", "generic"])
    p.add_argument("--samples", type=int, default=5, help="số lần đọc liên tiếp để coi là ổn định")
    p.add_argument("--tolerance", type=float, default=10.0, help="sai lệch cho phép (kg)")
    p.add_argument("--plate", action="append", default=[], help="biển số xe theo thứ tự lên cân")
    p.add_argument("--price", type=int, default=0, help="đơn giá đồng/kg")
    p.add_argument("--impurity", type=float, default=0.0, help="% trừ tạp chất")
    p.add_argument("-o", "--out", help="ghi phiếu cân ra file JSON Lines")
    args = p.parse_args(argv)

    lines = simulate() if args.simulate else serial_lines(args.port, args.baud)
    det = StabilityDetector(args.samples, args.tolerance)
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    try:
        run(lines, args.format, det, args.plate, out, args.price, args.impurity)
    except KeyboardInterrupt:
        pass
    finally:
        if out:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
