"""Nhận biết cân đã đứng yên.

Đầu cân rẻ thường không báo cờ ổn định; xe vừa lên bàn cân thì số nhảy liên tục.
Coi là ổn định khi có đủ `samples` lần đọc liên tiếp nằm trong khoảng `tolerance_kg`,
và (nếu đầu cân có báo) tất cả đều mang cờ ổn định.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .parsers import Reading


@dataclass
class StabilityDetector:
    samples: int = 5
    tolerance_kg: float = 10.0
    min_kg: float = 50.0          # dưới mức này coi như bàn cân trống
    _window: deque[Reading] = field(default_factory=deque)
    _locked: float | None = None

    def feed(self, r: Reading) -> int | None:
        """Đưa một lần đọc vào. Trả về khối lượng chốt (kg) đúng một lần cho mỗi lần cân, còn lại None."""
        if r.overload or r.kg < self.min_kg:
            self._window.clear()
            self._locked = None    # bàn cân trống → sẵn sàng cho lượt cân sau
            return None
        self._window.append(r)
        while len(self._window) > self.samples:
            self._window.popleft()
        if len(self._window) < self.samples:
            return None
        values = [x.kg for x in self._window]
        flagged_unstable = any(x.stable is False for x in self._window)
        if flagged_unstable or max(values) - min(values) > self.tolerance_kg:
            return None
        value = round(sum(values) / len(values))
        if self._locked is not None and abs(value - self._locked) <= self.tolerance_kg:
            return None            # vẫn là chiếc xe đã chốt
        self._locked = value
        return value
