import tempfile
from pathlib import Path
import unittest
import pymupdf as fitz
from cropper import inspect, export


class CropTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def make(self, name='source.pdf', count=1, rotation=0, blank=False):
        path = self.root/name
        with fitz.open() as doc:
            for i in range(count):
                p = doc.new_page(width=420, height=600)
                if not blank:
                    p.draw_rect(fitz.Rect(60,60,348,492), width=.8)
                    p.insert_text((75,100), f'LABEL {i+1}')
                    for x in range(80,320,4):
                        p.draw_rect(fitz.Rect(x,350,x+2,405), fill=(0,0,0))
                p.set_rotation(rotation)
            doc.save(path)
        return path
    def test_exact_size_vectors_and_multipage(self):
        src = self.make(count=3)
        pages = inspect(src)
        self.assertTrue(all(not p['review'] for p in pages))
        out = self.root/'out.pdf'
        export(src,out,[p['box'] for p in pages])
        with fitz.open(out) as doc:
            self.assertEqual(len(doc),3)
            for p in doc:
                self.assertEqual(tuple(p.rect), (0,0,288,432))
                self.assertIn('LABEL',p.get_text())
                self.assertGreater(len(p.get_drawings()),20)
    def test_rotated(self):
        src = self.make(rotation=90)
        pages = inspect(src)
        self.assertFalse(pages[0]['review'])
        export(src,self.root/'out.pdf',[p['box'] for p in pages])
        with fitz.open(self.root/'out.pdf') as doc:
            self.assertIn('LABEL',doc[0].get_text())
    def test_blank_review(self):
        self.assertTrue(inspect(self.make(blank=True))[0]['review'])
    def test_image(self):
        src = self.make()
        with fitz.open(src) as doc:
            doc[0].get_pixmap().save(self.root/'label.png')
        pages = inspect(self.root/'label.png')
        self.assertFalse(pages[0]['review'])
        export(self.root/'label.png',self.root/'out.pdf',[p['box'] for p in pages])
    def test_bad_box_no_output(self):
        src = self.make()
        out = self.root/'out.pdf'
        with self.assertRaises(ValueError):
            export(src,out,[[0,0,float('nan'),1]])
        self.assertFalse(out.exists())
    def test_two_labels_review(self):
        src=self.root/'two.pdf'
        with fitz.open() as doc:
            p=doc.new_page(width=700,height=600)
            p.draw_rect(fitz.Rect(20,60,308,492))
            p.draw_rect(fitz.Rect(370,60,658,492))
            doc.save(src)
        self.assertTrue(inspect(src)[0]['review'])

if __name__=='__main__':
    unittest.main()
