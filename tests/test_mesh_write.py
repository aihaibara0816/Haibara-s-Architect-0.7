import unittest,tempfile,sys,os
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'support'))
from detail_lab.mesh import write_array_atomic

class MeshWriteTests(unittest.TestCase):
 def test_short_writes_are_completed(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'mesh.bin';a=np.arange(300,dtype='<f4').reshape(10,3,10);original=os.write
   with patch('detail_lab.mesh.os.write',side_effect=lambda fd,b:original(fd,b[:7])):write_array_atomic(a,p)
   self.assertEqual(p.read_bytes(),a.tobytes());self.assertEqual(list(Path(td).glob('*.tmp')),[])
 def test_failed_write_does_not_replace_valid_cache(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'mesh.bin';p.write_bytes(b'old-valid-cache')
   with patch('detail_lab.mesh.os.write',side_effect=OSError('simulated interrupted write')):
    with self.assertRaises(OSError):write_array_atomic(np.arange(30,dtype='<f4'),p)
   self.assertEqual(p.read_bytes(),b'old-valid-cache');self.assertEqual(list(Path(td).glob('*.tmp')),[])
