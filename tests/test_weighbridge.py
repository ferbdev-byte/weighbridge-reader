import io
import json
from datetime import datetime

import pytest

from weighbridge import Reading, StabilityDetector, Ticket, parse
from weighbridge.cli import main, run
from weighbridge.sources import simulate


@pytest.mark.parametrize(
    "line, kg, stable, net",
    [
        ("ST,GS,+0024360kg", 24360, True, False),
        ("US,GS,+  12000kg", 12000, False, False),
        ("ST,NT,-00000.5kg", -0.5, True, True),
        ("ST,GS,+24.360 t", 24360, True, False),
        ("\x02ST,GS,+0001234kg\r\n", 1234, True, False),
    ],
)
def test_adstyle(line, kg, stable, net):
    r = parse(line)
    assert (r.kg, r.stable, r.net) == (kg, stable, net)


def test_overload():
    assert parse("OL,GS,+9999999kg").overload


def test_reversed_xk3190():
    assert parse("=0.06342").kg == 24360.0  # "0.06342" đảo lại là "24360.0"
    assert parse("=5.43210", "reversed").kg == 1234.5


def test_generic():
    assert parse("WT: 15880 kg").kg == 15880
    assert parse("weight 2,5 t").kg == 2500
    assert parse("không có số") is None
    assert parse("") is None


def test_stability_locks_once_per_truck():
    det = StabilityDetector(samples=3, tolerance_kg=5)
    seq = [0, 8000, 15000, 24340, 24360, 24362, 24361, 24360, 24359, 0, 0, 9100, 9120, 9121, 9119]
    locked = [x for x in (det.feed(Reading(kg)) for kg in seq) if x is not None]
    assert locked == [24361, 9120]


def test_stability_respects_unstable_flag():
    det = StabilityDetector(samples=3)
    for _ in range(5):
        assert det.feed(Reading(5000, stable=False)) is None
    assert det.feed(Reading(5000, True)) is None
    assert det.feed(Reading(5000, True)) is None
    assert det.feed(Reading(5000, True)) == 5000


def test_ticket_selling_and_buying_directions():
    sell = Ticket("51C-123.45", "Sắt vụn", impurity_pct=2, unit_price=8000)
    sell.record(24360, datetime(2026, 11, 23, 8))   # xe chở hàng vào
    sell.record(9120, datetime(2026, 11, 23, 9))    # xe không ra
    assert (sell.net_kg, sell.deduction_kg, sell.payable_kg) == (15240, 305, 14935)
    assert sell.amount == 14935 * 8000

    buy = Ticket("51C-999.99")
    buy.record(7040)     # xe không vào lấy hàng
    buy.record(15880)    # xe có hàng ra
    assert (buy.gross_kg, buy.tare_kg, buy.net_kg) == (15880, 7040, 8840)


def test_simulated_end_to_end():
    out = io.StringIO()
    tickets = run(simulate(), "auto", StabilityDetector(), ["51C-111.11", "51C-222.22"], out, 8000, 1)
    assert [t.plate for t in tickets] == ["51C-111.11", "51C-222.22"]
    assert abs(tickets[0].net_kg - (24360 - 9120)) <= 4
    assert abs(tickets[1].net_kg - (15880 - 7040)) <= 4
    rows = [json.loads(x) for x in out.getvalue().splitlines()]
    assert rows[0]["payable_kg"] == tickets[0].payable_kg


def test_simulated_reversed_format():
    tickets = run(simulate(fmt="reversed"), "auto", StabilityDetector(), [])
    assert len(tickets) == 2


def test_cli_simulate(tmp_path, capsys):
    out = tmp_path / "phieu.jsonl"
    assert main(["--simulate", "--plate", "51C-111.11", "-o", str(out)]) == 0
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2
    assert "51C-111.11" in capsys.readouterr().out
