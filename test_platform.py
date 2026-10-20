import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import platform_support
import label_info


class PlatformTests(unittest.TestCase):
    def test_windows_reserved_filename(self):
        self.assertEqual(label_info.safe_buyer('CON.example'), '_CON.example')
        self.assertEqual(label_info.safe_buyer('Alice'), 'Alice')

    def test_windows_folder(self):
        folder = Path(tempfile.gettempdir())/'label folder'
        with patch('platform_support.sys.platform', 'win32'), patch('platform_support.os.startfile', create=True) as start, patch('platform_support.subprocess.Popen') as popen:
            platform_support.open_folder(folder)
            start.assert_called_once_with(str(folder.resolve()))
            popen.assert_not_called()

    def test_mac_folder(self):
        folder = Path(tempfile.gettempdir())/'label folder'
        with patch('platform_support.sys.platform', 'darwin'), patch('platform_support.subprocess.Popen') as popen:
            platform_support.open_folder(folder)
            popen.assert_called_once_with(['open', str(folder.resolve())])

    def test_windows_ocr_skips_apple(self):
        with patch('label_info.sys.platform', 'win32'), patch('label_info.vision_lines') as apple, patch('label_info.rapid_lines', return_value=[]) as rapid:
            self.assertEqual(label_info.recognize_image('label.png'), [])
            rapid.assert_called_once_with('label.png')
            apple.assert_not_called()

    def test_mac_falls_back_without_swift(self):
        with patch('label_info.sys.platform', 'darwin'), patch('label_info.vision_lines', side_effect=FileNotFoundError), patch('label_info.rapid_lines', return_value=[]) as rapid:
            self.assertEqual(label_info.recognize_image('label.png'), [])
            rapid.assert_called_once()

    def test_ocr_failure_allows_manual_review(self):
        import pymupdf as fitz
        with fitz.open() as doc:
            page = doc.new_page()
            with patch('label_info.ocr_lines', side_effect=RuntimeError('test runtime failure')):
                info = label_info.read_info(page, [0, 0, 1, 1])
            self.assertTrue(info['info_review'])
            self.assertEqual(info['info_source'], 'Nhập tay')

    @unittest.skipUnless(os.environ.get('CUT_LABEL_OCR_TEST') == '1', 'Enable real OCR with CUT_LABEL_OCR_TEST=1')
    def test_real_portable_ocr(self):
        import pymupdf as fitz
        with tempfile.TemporaryDirectory() as td, fitz.open() as doc:
            page = doc.new_page(width=400, height=400)
            page.insert_text((25, 100), 'Buyer @samplebuyer', fontsize=18)
            page.insert_text((25, 300), '9434 6502 0810 4154 4384 43', fontsize=16)
            image = Path(td)/'label.png'
            page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(image)
            info = label_info.parse_lines(label_info.rapid_lines(image))
            self.assertEqual(info['buyer'], 'samplebuyer')
            self.assertEqual(info['tracking'], '9434650208104154438443')
            self.assertFalse(info['info_review'])


if __name__ == '__main__':
    unittest.main()
