# Cut Label — PDF 4×6 inch

App local cho **Windows 10/11 (64-bit)** và **macOS**. Theo dõi folder `input`, cắt label và lưu PDF vào `output`.

## Dùng ngay, không cần cài đặt (khuyến nghị)

Sau khi pull, mở `Start Cut Label.bat` (Windows) hoặc `Start Cut Label.command`
(macOS). Launcher tự tải Release v1.0.0 đúng nền tảng vào `.runtime`, không
cần cài Python. Lần đầu cần Internet; các lần sau dùng bản đã tải.
Dữ liệu vẫn nằm trong `input`, `output`, `.state` tại thư mục repo.
Người quản lý repo phải publish tag v1.0.0 qua workflow build trước khi sử dụng.
Launcher chạy binary của Release v1.0.0; thay đổi source chưa phát hành sẽ
không xuất hiện trong binary. Khi phát hành bản mới, cập nhật version trong
`launch.sh` và `launch.ps1` tương ứng.

Mở trang **Releases** của repository và tải đúng gói:

- Windows 10/11 64-bit: `Cut-Label-Windows-x64.zip`, giải nén rồi mở `Cut Label.exe`.
- Mac dùng chip Apple (M1/M2/M3/M4): `Cut-Label-macOS-Apple-Silicon.tar.gz`, giải nén rồi mở `Cut Label.command`.
- Mac dùng chip Intel: `Cut-Label-macOS-Intel.tar.gz`, giải nén rồi mở `Cut Label.command`.

Gói portable đã chứa Python, thư viện và model OCR; không cần cài Python, Xcode,
Tesseract hay GPU và không cần Internet khi chạy. Luôn giải nén toàn bộ gói trước
khi mở, không kéo riêng file chạy ra ngoài thư mục.

macOS có thể chặn ứng dụng tải từ Internet vì bản cộng đồng chưa được Apple
notarize. Lần đầu, Control-click `Cut Label.command`, chọn **Open**, rồi xác nhận
**Open**. Các lần sau có thể mở bình thường.

## Chạy từ mã nguồn (dành cho phát triển)

- Cài **Python 3.12 64-bit** từ https://www.python.org/downloads/ (app hỗ trợ Python 3.9–3.12). Trên Windows, chọn **Add python.exe to PATH** khi cài. Windows ARM chưa được kiểm thử; nên dùng bản x64.
- Tải/clone toàn bộ repo, giải nén vào một thư mục có quyền ghi. Không chạy trực tiếp bên trong file ZIP. Không copy `.venv` từ máy khác/hệ điều hành khác.
- Chạy `python3 bootstrap.py` trên macOS hoặc `py -3.12 bootstrap.py` trên Windows. Lần đầu cần Internet để tạo `.venv` và cài thư viện.
- Khi cập nhật source: đóng Terminal app cũ rồi chạy lại `bootstrap.py`.

## Sử dụng

1. Trên **Windows**, nhấp đúp **Start Cut Label.bat**. Trên **macOS**, nhấp đúp **Start Cut Label.command**. App mở tại http://127.0.0.1:8765.
2. Copy batch PDF, PNG, JPG hoặc TIFF vào **input**. Chờ file copy xong và khoảng 3–5 giây.
3. Lấy PDF trong **output**, hoặc bấm tên file trên app. Tên file: **Buyername_sốtracking.pdf**, ví dụ `tandybear_9434650208104154438443.pdf`.
4. Tệp có trạng thái **Cần kiểm tra**: bấm **Kiểm tra & xuất**, kiểm tra vùng cắt và nhập/sửa Buyer name, tracking từng trang, xác nhận xuất. Có thể sửa lại cả tệp đã xuất bằng **Sửa tên / vùng cắt**.
5. Khi in chọn giấy **4×6 inch / 101.6×152.4 mm**, **100% / Actual size**, tắt Fit to page.

Giữ cửa sổ Terminal chạy; đóng Terminal hoặc Ctrl+C sẽ dừng theo dõi. App không tự chạy khi đăng nhập máy. Không cần kết nối internet sau khi cài thư viện.

## Quy tắc xử lý

- Mỗi trang nguồn chứa một label. PDF nhiều trang được tách thành từng PDF riêng để tên Buyer/tracking khớp chính xác với label.
- Buyer name lấy từ dòng **Buyer @...**, bỏ dấu `@`, không lấy tên người gửi hoặc tên trong địa chỉ giao hàng. Ký tự không phù hợp tên file được đổi thành `_`.
- Ưu tiên đọc chữ trực tiếp từ PDF. PDF dạng ảnh / JPG / PNG dùng OCR tại máy, không gửi label ra dịch vụ bên ngoài. Windows dùng RapidOCR + ONNX Runtime CPU (model đi kèm gói cài đặt). macOS ưu tiên Apple Vision khi có Xcode Command Line Tools, tự chuyển sang RapidOCR nếu Vision không khả dụng/không đọc đủ trường. Không bắt buộc cài Xcode, Tesseract hoặc GPU. Nếu OCR không chạy hoặc đọc thiếu/không chắc, app yêu cầu nhập tay.
- Tracking được bỏ dấu cách, hiện hỗ trợ USPS 20/22 số bắt đầu bằng 9 và UPS bắt đầu bằng 1Z. OCR có thể nhầm ký tự; nên kiểm tra tên file batch đầu. Nếu có nhiều giá trị Buyer/tracking, app yêu cầu kiểm tra.
- Ưu tiên khung kín gần tỷ lệ 2:3; nếu không có khung kín, lấy biên nội dung tối màu.
- Không cần có viền đỏ trong file thật. Hãy dùng PDF/ảnh label gốc, không dùng ảnh chụp màn hình có giao diện trình duyệt.
- Khung có tỷ lệ lệch quá 2.5%, vùng quá nhỏ, trang trống hoặc nhiều khung rời nhau cần kiểm tra. Nhận diện tự động là heuristic, không đảm bảo đúng với mọi mẫu; kiểm tra batch đầu của mỗi mẫu mới.
- Đầu ra luôn 288×432 PDF points = 4×6 inch, không thêm lề. Vùng cắt được co/giãn kín trang. Với khung không đúng tỷ lệ 2:3, không thể đồng thời giữ nguyên tỷ lệ, không mất nội dung và không thêm lề; app yêu cầu xác nhận khi chênh lệch lớn.
- PDF giữ chữ/vector bằng cách nhúng vùng trang nguồn, không raster hóa. Ảnh giữ chất lượng theo ảnh đầu vào. Không phục hồi được mã vạch bị nhòe từ nguồn.
- Giữ nguyên file input; nhận diện trùng theo tên và nội dung. Tên đầu ra trùng với file khác sẽ thêm `_2`, `_3`, ... để tránh ghi đè. Lịch sử nằm trong `.state/jobs.json`.
- Khi nâng cấp tính năng đặt tên, app xử lý lại label cũ trong input. Các PDF đầu ra tên cũ được chuyển vào `.state/previous-output` sau khi xuất thành công, không xóa mất bản cũ.
- Chỉ theo dõi file trực tiếp trong input, không quét thư mục con. Bỏ qua symlink. PDF khóa mật khẩu cần mở khóa trước.
- File đang copy được chờ đến khi kích thước/thời gian sửa không đổi 3 giây. Với file copy qua mạng có thể ngắt quãng lâu, copy bằng đuôi `.part` rồi đổi tên thành `.pdf` khi xong; có nút thử lại khi gặp lỗi đọc.

## Chạy từ Terminal

macOS:

```sh
python3 bootstrap.py
```

Windows (PowerShell hoặc CMD):

```powershell
py -3.12 bootstrap.py
```

`bootstrap.py` tự tạo môi trường và cài đúng thư viện cho người phát triển. Nếu muốn chạy trực tiếp sau khi cài: macOS dùng `.venv/bin/python app.py`; Windows dùng `.venv\Scripts\python.exe app.py`.

Có thể dùng `--port 8766` hoặc `--no-browser`. Mỗi lần chỉ mở một instance app trên cùng folder.

Kiểm tra tự động:

```sh
.venv/bin/python -m unittest discover -v
```

Tham khảo cơ chế giữ PDF vector: https://pymupdf.readthedocs.io/en/latest/page.html#Page.show_pdf_page

Trên Windows: `.venv\Scripts\python.exe -m unittest discover -v`. Workflow `.github/workflows/test.yml` chạy kiểm tra trên Windows và macOS, gồm OCR thật với label giả lập.
