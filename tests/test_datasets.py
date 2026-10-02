import copy
from pathlib import Path
import tempfile
import unittest
from fixture_data import *
from maidionis_education.datasets import validate_dataset,split_for,_validate
from maidionis_education.storage import inventory
from maidionis_education.contracts import loads

class Datasets(unittest.TestCase):
    def test_explicit_partition_hooks_are_bound_and_fail_closed(self):
        from dataclasses import replace
        from maidionis_education.datasets import assigned_split
        r=registry();h=hooks();rows,_=fixture()
        with self.assertRaises(ValueError):replace(h,assign_split=lambda *args:'train').check()
        with self.assertRaises(ValueError):replace(h,split_algorithm='test.legacy.v1').check()
        bad=replace(h,split_algorithm='test.legacy.v1',assign_split=lambda *args:'unknown')
        with self.assertRaises(ValueError):assigned_split(rows[0],rows[0]['family_fingerprint'],bad,42)
        explicit=replace(h,split_algorithm='test.legacy.v1',assign_split=lambda *args:'train')
        explicit.check()
        self.assertEqual(assigned_split(rows[0],rows[0]['family_fingerprint'],explicit,42),'train')
        # Serialized split-profile text alone cannot install executable policy.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'data';frozen(root)
            with self.assertRaises(ValueError):validate_dataset(root,digest((root/'manifest.json').read_bytes()),r,explicit)

    def test_import_rejects_rehashed_missing_or_substituted_components_and_paths(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source';frozen(source)
            semantic=DESCRIPTOR['semantic_spec']['path']
            for i,kind in enumerate(('semantic','input.schema.json','architecture.config.json','descriptor-path','provenance-path','grouping-version')):
                root=Path(td)/str(i);shutil.copytree(source,root)
                m=loads((root/'manifest.json').read_bytes(),4*2**20)
                if kind=='semantic':(root/semantic).unlink()
                elif kind in ('input.schema.json','architecture.config.json'):(root/kind).write_bytes(b'{}\n')
                elif kind=='descriptor-path':m['descriptor']['path']='missing.json'
                elif kind=='provenance-path':m['provenance_index']['path']='missing.json'
                else:m['split_profile']['grouping_version']='other'
                files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}
                m['files']=inventory(files);raw=canonical(m);(root/'manifest.json').write_bytes(raw)
                with self.assertRaises(ValueError):validate_dataset(root,digest(raw),registry(),hooks())
    def test_correction_retains_unverified_original_only_in_audit(self):
        rows,proofs=fixture();original=copy.deepcopy(rows[0]);oldproof=copy.deepcopy(proofs[0])
        original['schema_version']='maidionis.audit-ancestor.v1';original['verification_status']='unverified'
        original['target']['kick']=not original['target']['kick']
        oldproof.update(final_target=original['target'],proposed_target=original['target'],reviewed_target=original['target'],
                        outcome='unverified',disposition='rejected')
        rows[0].update(sample_id='correction:0',provenance_id='corrected-proof:0',supersedes=original['sample_id'])
        proofs[0].update(sample_id=rows[0]['sample_id'],provenance_id=rows[0]['provenance_id'],supersedes=original['sample_id'],disposition='corrected')
        proofs.append(oldproof)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'corrected'
            h=freeze(root,rows,proofs,registry(),hooks(),component_files(),dataset_id='test.grid.v1',seed=42,created_at=TIME,
                generator=dict(code_digest=GEN['config_digest'],config_digest=HOOK['config_digest']),license_summary='Apache-2.0 synthetic',
                limitations=['Synthetic mechanics'],audit_ancestors=[original])
            m,admitted=validate_dataset(root,h,registry(),hooks())
            self.assertEqual(len(admitted),176);self.assertNotIn(original['sample_id'],{r['sample_id'] for r in admitted})
            corrected=next(r for r in admitted if r['sample_id']=='correction:0')
            self.assertEqual(corrected['family_fingerprint'],original['family_fingerprint'])
            self.assertIn(canonical(original),(root/'audit-ancestors.jsonl').read_bytes())
            original['family_fingerprint']='0'*64
            with self.assertRaises(ValueError):_validate(rows,proofs,registry(),hooks(),42,'test.grid.v1',[original])
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
