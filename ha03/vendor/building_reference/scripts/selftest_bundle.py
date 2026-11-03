"""Offline byte-preservation tests; synthetic PNGs, no network or visual claims."""
import unittest,tempfile,json,base64,io,re,zipfile
from pathlib import Path
from PIL import Image
from bundle_reference_images import collect,render
class BundleTests(unittest.TestCase):
    def run_bundle(self,bad=False):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);f=p/'source.png';Image.new('RGB',(16,12),'green').save(f);raw=f.read_bytes()
            images=[{'image_id':'img-fixture','local_path':str(f),'selection_status':'selected','verification_status':'not_reviewed','covered_components':['component-fixture']}]
            if bad:
                (p/'bad.png').write_text('bad');images.append({'image_id':'img-bad','local_path':str(p/'bad.png'),'selection_status':'candidate'})
            m={'title':'合成离线测试','images':images};records,data=collect(m,p/'manifest.json',p/'assets',1)
            html,gaps=render('<html><img src="'+str(f)+'"></html>',m,records,data,'test',p/'report.html')
            return raw,records,data,html,gaps
    def test_original_bytes_preserved(self):
        raw,records,data,html,gaps=self.run_bundle();self.assertEqual(data[0],raw);self.assertIn(base64.b64encode(raw).decode(),html);self.assertEqual(gaps,[])
    def test_no_auto_visual_upgrade(self):
        _,records,_,_,_=self.run_bundle();self.assertEqual(records[0]['verification_status'],'not_reviewed')
    def test_bad_image_not_in_archive(self):
        _,records,data,html,_=self.run_bundle(True);self.assertEqual(len(data),1);self.assertFalse(records[1]['included_in_bundle'])
        z=re.search(r'data:application/zip;base64,([^"\s]+)',html)
        self.assertIsNotNone(z)
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(z[1]))) as f:self.assertFalse(any('img-bad' in x for x in f.namelist()))
    def test_empty_bundle_no_false_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);records,data=collect({'images':[]},p/'m.json',p/'assets',1);self.assertEqual(data,{})
if __name__=='__main__':unittest.main(verbosity=2)
