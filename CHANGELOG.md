# Changelog

Theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/) và [SemVer](https://semver.org/lang/vi/).

## [0.2.0] - 2026-11-23

### Thêm

- Tuỳ chọn `--raw-log` lưu nguyên văn mọi bản tin đầu cân kèm thời điểm, để đối chiếu khi có tranh chấp số cân.
- Đánh dấu `py.typed` (PEP 561): dự án khác dùng thư viện sẽ nhận được thông tin kiểu.

### Cải thiện

- CI kiểm tra kiểu tĩnh bằng mypy ở chế độ strict.
- CI đo độ phủ test (branch coverage), fail nếu dưới 80%.
- GitHub Actions nâng lên bản mới (checkout v7, setup-python v7).

## [0.1.0] - 2026-11-23

### Thêm

- Bản phát hành đầu tiên. Giải mã bản tin đầu cân (A&D, XK3190-A9, dạng chung), nhận biết ổn định, phiếu cân hai chiều, trừ tạp chất, giả lập.
