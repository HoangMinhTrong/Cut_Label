import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import pymupdf as fitz
import app
from label_info import parse_lines, safe_buyer, validate_info


def parse(*lines):
    return parse_lines([{'text': line, 'confidence': 1} for line in lines])


class InfoTests(unittest.TestCase):
    def test_buyer_and_tracking(self):
        info = parse('Raquel Cardozo', 'SHIP TO: Rebecca Simmons', 'Buyer @tandybear',
                     'USPS TRACKING #', '9434 6502 0810 4154 4384 43')
        self.assertEqual(info['buyer'], 'tandybear')
        self.assertEqual(info['tracking'], '9434650208104154438443')
        self.assertFalse(info['info_review'])
    def test_missing_buyer_does_not_use_recipient(self):
        self.assertTrue(parse('SHIP TO: Rebecca Simmons', '9434650208104154438443')['info_review'])
    def test_ambiguity_and_low_confidence(self):
        self.assertTrue(parse('Buyer @alice', 'Buyer @bob', '9434650208104154438443')['info_review'])
        self.assertTrue(parse_lines([{'text':'Buyer @alice','confidence':.3},
                                    {'text':'9434650208104154438443','confidence':1}])['info_review'])
    def test_filename_safety_and_invalid_tracking(self):
        self.assertNotIn('/', safe_buyer('../../test/name:*'))
        with self.assertRaises(ValueError):
            validate_info({'buyer':'alice', 'tracking':'Order 12345'})
    def test_pdf_text_without_ocr(self):
        from label_info import read_info
        with fitz.open() as doc:
            p = doc.new_page(width=288,height=432)
            p.insert_text((20,100),'Buyer @alice')
            p.insert_text((20,390),'9434 6502 0810 4154 4384 43')
            with patch('label_info.ocr_lines', side_effect=AssertionError('Must use PDF text')):
                info = read_info(p,[0,0,1,1])
            self.assertFalse(info['info_review'])
            self.assertEqual(info['info_source'],'PDF text')


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.input, self.output, self.state = [root/x for x in ('input','output','state')]
        for p in (self.input,self.output,self.state): p.mkdir()
        self.patches = [patch.object(app,'INPUT',self.input),patch.object(app,'OUTPUT',self.output),
                        patch.object(app,'STATE',self.state)]
        for p in self.patches: p.start()
        self.source = self.input/'batch.pdf'
        with fitz.open() as doc:
            for name,tracking in [('alice','9434650208104154438443'),('bob','9434650208104155262290')]:
                p=doc.new_page(width=288,height=432)
                p.insert_text((20,100),f'Buyer @{name}')
                p.insert_text((20,390),tracking)
            doc.save(self.source)
        self.job={'id':app.digest(self.source),'name':self.source.name,'pages':[
            {'buyer':'alice','tracking':'9434650208104154438443'},
            {'buyer':'bob','tracking':'9434650208104155262290'}]}
        self.boxes=[[0,0,1,1],[0,0,1,1]]
    def tearDown(self):
        for p in self.patches: p.stop()
        self.temp.cleanup()
    def test_split_named_outputs_and_idempotent(self):
        app.finish(self.job,self.boxes)
        self.assertEqual(self.job['outputs'],['alice_9434650208104154438443.pdf','bob_9434650208104155262290.pdf'])
        for name in self.job['outputs']:
            with fitz.open(self.output/name) as doc:
                self.assertEqual(len(doc),1)
                self.assertEqual(tuple(doc[0].rect),(0,0,288,432))
                self.assertIn(name.split('_')[0],doc[0].get_text())
        app.finish(self.job,self.boxes)
        self.assertEqual(len(list(self.output.glob('*.pdf'))),2)
    def test_collision_keeps_existing_file(self):
        path=self.output/'alice_9434650208104154438443.pdf'
        path.write_bytes(b'existing label')
        app.finish(self.job,self.boxes)
        self.assertEqual(path.read_bytes(),b'existing label')
        self.assertEqual(self.job['outputs'][0],'alice_9434650208104154438443_2.pdf')
    def test_invalid_second_page_leaves_no_partial_output(self):
        with self.assertRaises(ValueError):
            app.finish(self.job,[[0,0,1,1],[0,0,0,0]])
        self.assertFalse(list(self.output.glob('*.pdf')))
    def test_legacy_archived(self):
        old=self.output/'legacy_4x6.pdf'; old.write_bytes(b'old PDF')
        self.job['legacy_output']=old.name
        app.finish(self.job,self.boxes)
        self.assertFalse(old.exists())
        self.assertEqual((self.state/'previous-output'/self.job['id']/old.name).read_bytes(),b'old PDF')

if __name__=='__main__': unittest.main()
