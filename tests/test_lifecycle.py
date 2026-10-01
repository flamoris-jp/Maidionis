"""A21: real native train/resume/export/load/infer/evaluate/finalize, no teacher."""
import copy
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import unittest
from fixture_data import *
from maidionis_education.datasets import validate_dataset
from maidionis_education.artifacts import export_components,export_candidate,finalize,component_digest
from maidionis_education.evaluation import evaluate,rate,EvaluationLedger
from maidionis_education.contracts import loads
from maidionis_education.storage import inventory
from test_education import plan

DRIVER=os.environ.get('MAIDIONIS_TINYBEAT_DRIVER')
AS_CAP=2*2**30
POLICY=digest(b'Train-only two-output Bernoulli diagnostic; full accounting; no quality gate v1\n')
METRIC=config('metrics',{'outputs':['kick','snare'],'reducer':'bernoulli_accuracy_v1'})
CARD=dict(license='Apache-2.0 synthetic test fixture',intended_use='Offline train-only mechanics verification',
          limitations=['No held-out generalization or musical quality claim; no production admission.'])
def reducers():
    def reduce(rows):
        return [rate(name+'.accuracy',sum(p['target'][name]==p['result']['payload'][name] for p in rows),len(rows),
                     denominator='one prediction per admitted train input') for name in ('kick','snare')]
    return {(METRIC['id'],METRIC['version'],METRIC['config_digest']):reduce}
def host_limit():
    resource.setrlimit(resource.RLIMIT_AS,(AS_CAP,AS_CAP))
    resource.setrlimit(resource.RLIMIT_CPU,(30,30))
def run(*args, success=True):
    p=subprocess.run([DRIVER,*map(str,args)],capture_output=True,timeout=35,preexec_fn=host_limit)
    if success and p.returncode: raise AssertionError(p.stderr.decode(errors='replace'))
    if not success:
        if p.returncode==0: raise AssertionError('native rejection expected')
        if p.stdout: raise AssertionError('failed operation published partial output')
        return p
    if len(p.stdout)>4*2**20: raise AssertionError('native output limit')
    return loads(p.stdout,4*2**20)

@unittest.skipUnless(DRIVER,'native Tiny Beat driver required; run tools/verify.py for acceptance')
class Lifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.dataset=cls.root/'data'
        cls.data_digest=frozen(cls.dataset)
        cls.manifest,all_rows=validate_dataset(cls.dataset,cls.data_digest,registry(),hooks())
        cls.rows=[r for r in all_rows if r['split']=='train']
        cls.full=run('train',cls.dataset,cls.data_digest,cls.root/'full-checkpoints',cls.root/'full',0,0)
        cls.first=run('train',cls.dataset,cls.data_digest,cls.root/'resumed-checkpoints',cls.root/'first',2,0)
        cls.resumed=run('train',cls.dataset,cls.data_digest,cls.root/'resumed-checkpoints',cls.root/'resumed',0,1)
        cls.components=export_components(component_files(),cls.root/'full')
        cls.registration=dict(schema_version='maidionis.evaluation-registration.v1',id='test:evaluation:1',version='1',
            experiment_id='offline:1',policy_digest=POLICY,descriptor_digest=digest(canonical(DESCRIPTOR)),
            evaluated_component_digest=component_digest(cls.components),dataset_digest=cls.data_digest,split='train',
            selection_scope='train_diagnostic',metrics=[METRIC],baselines=[],calibration='not_applicable',minimum_samples=1,
            tolerance=1e-6,environment_digest=cls.full['environment_digest'])
        cls.registration_digest=digest(canonical(cls.registration));cls.candidate=cls.root/'candidate'
        p=plan();p['evaluation_policy_digest']=POLICY
        cls.ledger=EvaluationLedger(cls.root/'evaluation-ledger',p)
        cls.ledger.register(cls.registration,p);cls.ledger.admit(cls.registration,'Train-only synthetic mechanics')
        cls.candidate_digest=export_candidate(cls.candidate,cls.components,cls.root/'full',cls.registration,
            artifact_id='test:candidate:1',created_at=TIME,model_card=CARD)
        cls.composition=cls.root/'composition';cls.composition.mkdir()
        for p,b in component_files().items():(cls.composition/p).write_bytes(b)
        requests=[dict(schema_version='maidionis.request.v1',request_id=r['sample_id'],**IDENTITY,payload_schema=ref('input'),
                       payload=r['input'],context_ref=None) for r in cls.rows]
        (cls.composition/'inference-inputs.json').write_bytes(canonical(requests))
        cls.loaded=cls.infer(cls.candidate,cls.candidate_digest)
        cls.predictions=[]
        for r,p in zip(cls.rows,cls.loaded['predictions']):
            cls.predictions.append(dict(schema_version='maidionis.prediction.v1',experiment_id='offline:1',run_id='test:run:1',
                sample_id=r['sample_id'],dataset_id=r['dataset_id'],dataset_digest=cls.data_digest,split='train',
                descriptor_digest=cls.registration['descriptor_digest'],artifact_digest=cls.candidate_digest,
                evaluated_component_digest=cls.registration['evaluated_component_digest'],evaluation_registration_digest=cls.registration_digest,
                selection_scope='train_diagnostic',calibration_status='not_applicable',result=p['result'],target=r['target'],
                raw_output_schema=ref('raw'),raw_output=p['raw_output'],timing=dict(elapsed_ns=0,profile='test.mechanics'),error_status=None))
        cls.report,cls.summary=cls.evaluate(cls.predictions)
        cls.final=cls.root/'final'
        cls.final_digest=finalize(cls.candidate,cls.candidate_digest,cls.final,cls.report,cls.summary,
            artifact_id='test:completed:1',created_at=TIME,model_card=CARD)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    @classmethod
    def infer(cls,path,digest_value,*,persistent=2**20,peak=16*2**20,fault='none'):
        return run('infer',cls.composition,path,digest_value,64*2**20,AS_CAP,persistent,peak,fault)
    @classmethod
    def evaluate(cls,predictions):
        return evaluate(cls.rows,predictions,cls.registration,registry(),run_id='test:run:1',artifact_digest=cls.candidate_digest,
            reducers=reducers(),passing_policy=lambda report:True)
    def test_real_fresh_process_resume_and_gradient(self):
        self.assertGreater(self.full['gradient_l1'],0);self.assertTrue(self.full['parameters_changed'])
        self.assertGreater(self.resumed['gradient_l1'],0)
        for k in ('state','final_sha256','best_sha256','final_logits','best_logits'):
            self.assertEqual(self.full[k],self.resumed[k],k)
        self.assertGreater(self.resumed['state']['global_step'],self.first['state']['global_step'])
    def test_archive_inference_and_immutable_finalization(self):
        run('validate',self.composition,self.candidate,self.candidate_digest,'offline_evaluation')
        final=self.infer(self.final,self.final_digest)
        self.assertNotEqual(self.candidate_digest,self.final_digest)
        self.assertEqual(self.loaded['component_digest'],final['component_digest'])
        self.assertEqual(self.candidate_digest,digest((self.candidate/'manifest.json').read_bytes()))
        self.assertEqual(self.report['status'],'complete')
        for i,(old,new) in enumerate(zip(self.loaded['predictions'],final['predictions'])):
            for actual,expected in zip(old['raw_output'],self.full['best_logits'][i]):self.assertLessEqual(abs(actual-expected),1e-6)
            self.assertEqual(old['raw_output'],new['raw_output']);self.assertEqual(old['result']['payload'],new['result']['payload'])
            self.assertIsNone(old['result']['diagnostics'])
        receipt=self.loaded['receipt'];self.assertEqual(receipt['process_address_space_cap'],AS_CAP)
        self.assertGreater(receipt['observed_peak_rss_bytes'],receipt['tensor_bytes'])
    def test_missing_duplicate_error_wrong_raw_invalidate_complete_accounting(self):
        cases=[self.predictions[:-1],self.predictions+[self.predictions[0]]]
        p=copy.deepcopy(self.predictions);p[0]['error_status']='nonfinite';cases.append(p)
        p=copy.deepcopy(self.predictions);p[0]['raw_output_schema']['sha256']='0'*64;cases.append(p)
        for p in cases:
            report,summary=self.evaluate(p);self.assertEqual(report['status'],'invalid_run');self.assertFalse(summary['passing'])
        for metric in self.report['metrics']:
            name=metric['name'].split('.')[0]
            correct=sum(p['target'][name]==p['result']['payload'][name] for p in self.predictions)
            self.assertEqual(metric['numerator'],correct);self.assertEqual(metric['support'],len(self.rows))
    def test_loading_faults_capacity_expiry_and_pending_serving_rejected(self):
        for persistent,peak,fault in [(1,16*2**20,'none'),(2**20,1,'none'),(2**20,16*2**20,'expired'),
            (2**20,16*2**20,'after_construct'),(2**20,16*2**20,'after_load'),(2**20,16*2**20,'before_transfer'),
            (2**20,16*2**20,'expire_after_load')]:
            run('infer',self.composition,self.candidate,self.candidate_digest,64*2**20,AS_CAP,persistent,peak,fault,success=False)
        run('validate',self.composition,self.candidate,self.candidate_digest,'serving',success=False)
    def test_bundle_mutation_shape_extra_symlink_and_evidence(self):
        import shutil
        for index,kind in enumerate(('weights','shape','extra','symlink','status','unknown_profile','registration','self_inventory')):
            root=self.root/('bad:'+str(index));shutil.copytree(self.candidate,root)
            m=loads((root/'manifest.json').read_bytes(),4*2**20)
            if kind=='weights':(root/'weights.pt').write_bytes(b'corrupt')
            elif kind=='shape':m['tensor_inventory'][0]['shape'][0]+=1
            elif kind=='extra':(root/'extra').write_bytes(b'x')
            elif kind=='symlink':(root/'weights.pt').unlink();(root/'weights.pt').symlink_to(self.candidate/'weights.pt')
            elif kind=='status':m['status']='research_only'
            elif kind=='unknown_profile':m['compatibility']['profile']='unknown'
            elif kind=='registration':m['evidence']['evaluation']['evaluation_registration_digest']='0'*64
            else:m['files'].append(dict(path='manifest.json',sha256='0'*64,bytes=1))
            (root/'manifest.json').write_bytes(canonical(m));h=digest(canonical(m))
            run('validate',self.composition,root,h,'offline_evaluation',success=False)
    def test_every_checkpoint_inventory_member_corruption_rejects_resume(self):
        import shutil
        source=self.root/'resumed-checkpoints';pointer=loads((source/'latest.json').read_bytes())
        m=loads((source/pointer['checkpoint']/'manifest.json').read_bytes(),4*2**20)
        for i,e in enumerate(m['files']):
            root=self.root/('corrupt-checkpoint-'+str(i));shutil.copytree(source,root)
            member=root/pointer['checkpoint']/e['path'];member.write_bytes(member.read_bytes()+b'x')
            run('train',self.dataset,self.data_digest,root,self.root/('bad-output-'+str(i)),0,1,success=False)
        bad=self.root/'bad-pointer';shutil.copytree(source,bad)
        (bad/'latest.json').write_bytes(canonical(dict(checkpoint='../outside',manifest_digest='0'*64)))
        run('train',self.dataset,self.data_digest,bad,self.root/'bad-pointer-out',0,1,success=False)
    def test_preregistration_and_finalization_cannot_substitute_components(self):
        p=plan();p['evaluation_policy_digest']=POLICY
        changed=dict(self.registration,policy_digest='0'*64)
        with self.assertRaises(ValueError):self.ledger.register(changed,p)
        with self.assertRaises(ValueError):self.ledger.admit(self.registration,'repeat')
        report=dict(self.report,evaluated_component_digest='0'*64)
        with self.assertRaises(ValueError):finalize(self.candidate,self.candidate_digest,self.root/'bad-final',report,self.summary,
            artifact_id='bad',created_at=TIME,model_card=CARD)

if __name__=='__main__':unittest.main()
