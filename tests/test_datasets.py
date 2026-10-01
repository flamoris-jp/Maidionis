import copy
from pathlib import Path
import tempfile
import unittest
from fixture_data import *
from maidionis_education.datasets import validate_dataset,split_for,_validate

class Datasets(unittest.TestCase):
    def test_deterministic_freeze_and_rename(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a';b=Path(td)/'b'
            da=frozen(a);db=frozen(b);self.assertEqual(da,db)
            m,rows=validate_dataset(a,da,registry(),hooks())
            self.assertEqual(sum(x['records'] for x in m['counts'].values()),176)
            self.assertTrue(all(m['counts'][s]['records']>0 for s in m['counts']))
            rows,proofs=fixture();old=[r['split'] for r in rows]
            for row,p in zip(rows,proofs):
                row['family_id']='alias:'+row['family_id'];p['ancestry']=['grid-v1',row['family_id']]
            _validate(rows,proofs,registry(),hooks(),42,'test.grid.v1')
            self.assertEqual(old,[r['split'] for r in rows])
    def test_reject_corrupt_anchors_proofs_seed(self):
        rows,proofs=fixture()
        mutations=[lambda r,p:r[0].update(family_fingerprint='0'*64),lambda r,p:r[0].update(split='dev' if r[0]['split']!='dev' else 'train'),
                   lambda r,p:p[0].update(outcome='unverified'),lambda r,p:r[0].update(supersedes=r[1]['sample_id']),
                   lambda r,p:p[0].update(source_digest='0'*64),lambda r,p:r[1].update(sample_id=r[0]['sample_id'])]
        for f in mutations:
            r=copy.deepcopy(rows);p=copy.deepcopy(proofs);f(r,p)
            with self.assertRaises(ValueError): _validate(r,p,registry(),hooks(),42,'test.grid.v1')
        with self.assertRaises(ValueError): _validate(rows,proofs,registry(),hooks(),43,'test.grid.v1')
    def test_publication_fault_preserves_no_partial(self):
        with tempfile.TemporaryDirectory() as td:
            for name in ('write','fsync','directory_fsync','rename'):
                root=Path(td)/name
                def fail(point):
                    if point==name: raise OSError('injected')
                with self.assertRaises(OSError): frozen(root,fail)
                self.assertFalse(root.exists())
                frozen(root)
                with self.assertRaises(OSError): frozen(root)
    def test_snapshot_extra_symlink_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'data';h=frozen(root)
            (root/'extra').write_bytes(b'x')
            with self.assertRaises(ValueError): validate_dataset(root,h,registry(),hooks())
            (root/'extra').unlink();(root/'train.jsonl').write_bytes(b'{}\n')
            with self.assertRaises(ValueError): validate_dataset(root,h,registry(),hooks())

if __name__=='__main__': unittest.main()
