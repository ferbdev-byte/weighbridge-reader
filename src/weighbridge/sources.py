"""Nguồn dữ liệu: cổng COM thật (pyserial) hoặc bộ giả lập để chạy thử không cần đầu cân."""

from __future__ import annotations

import random
from collections.abc import Iterator


def serial_lines(port: str, baud: int = 9600, timeout: float = 1.0) -> Iterator[str]:
    try:
        import serial  # pyserial
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Cần pyserial: pip install weighbridge-reader[serial]") from exc
    with serial.Serial(port, baud, timeout=timeout) as s:
        buf = b""
        while True:
            chunk = s.read(64)
            if not chunk:
                continue
            buf += chunk
            # đầu cân kết thúc bản tin bằng CR, LF hoặc ETX (0x03)
            while True:
                idx = min((i for i in (buf.find(b"\r"), buf.find(b"\n"), buf.find(b"\x03")) if i >= 0), default=-1)
                if idx < 0:
                    break
                line, buf = buf[:idx], buf[idx + 1 :]
                if line.strip():
                    yield line.decode("ascii", errors="replace")


def simulate(trucks: list[tuple[int, int]] | None = None, seed: int = 1, fmt: str = "adstyle") -> Iterator[str]:
    """Giả lập: mỗi xe lên cân (số dao động rồi đứng yên), rời cân, rồi xe không quay lại cân bì."""
    rng = random.Random(seed)
    trucks = trucks or [(24_360, 9_120), (15_880, 7_040)]

    def emit(kg: float, stable: bool) -> str:
        if fmt == "reversed":
            return "=" + f"{kg:07.1f}"[::-1]
        return f"{'ST' if stable else 'US'},GS,+{kg:08.1f}kg"

    for gross, tare in trucks:
        for target in (gross, tare):
            for _ in range(4):
                yield emit(0, True)
            for step in range(8):  # xe đang lên, số nhảy
                yield emit(target * (step + 1) / 8 + rng.uniform(-150, 150), False)
            for _ in range(8):
                yield emit(target + rng.choice((-2, 0, 0, 2)), True)
    for _ in range(4):
        yield emit(0, True)
