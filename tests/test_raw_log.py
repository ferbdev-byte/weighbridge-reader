from weighbridge.cli import main


def test_raw_log_keeps_every_frame(tmp_path):
    raw = tmp_path / "raw.log"
    assert main(["--simulate", "--raw-log", str(raw)]) == 0
    rows = raw.read_text(encoding="utf-8").splitlines()
    assert len(rows) > 50
    stamp, frame = rows[0].split("\t")
    assert "T" in stamp and frame.startswith(("ST,", "US,"))
