# Cut Label — PDF 4×6 inch

App local cho macOS. Theo dõi folder `input`, cắt label và lưu PDF vào `output`.

## Sử dụng

1. Nhấp đúp **Start Cut Label.command**. App mở tại http://127.0.0.1:8765.
2. Copy batch PDF, PNG, JPG hoặc TIFF vào **input**. Chờ file copy xong và khoảng 3–5 giây.
3. Lấy PDF trong **output**, hoặc bấm tên file trên app. Tên file: **Buyername_sốtracking.pdf**, ví dụ `tandybear_9434650208104154438443.pdf`.
4. Tệp có trạng thái **Cần kiểm tra**: bấm **Kiểm tra & xuất**, kiểm tra vùng cắt và nhập/sửa Buyer name, tracking từng trang, xác nhận xuất. Có thể sửa lại cả tệp đã xuất bằng **Sửa tên / vùng cắt**.
5. Khi in chọn giấy **4×6 inch / 101.6×152.4 mm**, **100% / Actual size**, tắt Fit to page.

Giữ cửa sổ Terminal chạy; đóng Terminal hoặc Ctrl+C sẽ dừng theo dõi. App không tự chạy khi đăng nhập máy. Không cần kết nối internet sau khi cài thư viện.

## Quy tắc xử lý

- Mỗi trang nguồn chứa một label. PDF nhiều trang được tách thành từng PDF riêng để tên Buyer/tracking khớp chính xác với label.
- Buyer name lấy từ dòng **Buyer @...**, bỏ dấu `@`, không lấy tên người gửi hoặc tên trong địa chỉ giao hàng. Ký tự không phù hợp tên file được đổi thành `_`.
- Ưu tiên đọc chữ trực tiếp từ PDF. PDF dạng ảnh / JPG / PNG dùng Apple Vision OCR tại máy, không gửi label ra dịch vụ bên ngoài. Cần macOS và Xcode Command Line Tools (`xcrun swiftc`); helper tự biên dịch ở lần OCR đầu tiên. Nếu OCR không chạy hoặc đọc thiếu/không chắc, app yêu cầu nhập tay.
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

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Có thể dùng `--port 8766` hoặc `--no-browser`. Mỗi lần chỉ mở một instance app trên cùng folder.

Kiểm tra tự động:

```sh
.venv/bin/python -m unittest -v test_cropper.py test_label_info.py
```

Tham khảo cơ chế giữ PDF vector: https://pymupdf.readthedocs.io/en/latest/page.html#Page.show_pdf_page
