import math
import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import tempfile
import unittest
from fixture_data import *
from test_education import plan
from maidionis_education.evaluation import percentile,rate,evaluate,EvaluationLedger
from maidionis_education.datasets import evaluation_data,EvaluationDataset
class StatisticalAccounting(unittest.TestCase):
    def test_zero_support_and_imbalance_keep_actual_denominators(self):
        empty=rate('empty',0,0);self.assertIsNone(empty['value']);self.assertEqual(empty['warning'],'zero_support')
        imbalanced=rate('majority',9,10);self.assertEqual(imbalanced['value'],.9);self.assertEqual(imbalanced['support'],10)
        with self.assertRaises(ValueError):rate('bad',2,1)
    def test_registered_percentile_and_nonfinite_rejection(self):
        self.assertIsNone(percentile([],.5));self.assertEqual(percentile([30,0,20,10],.25),7.5)
        for x in ([math.nan],[math.inf]):
            with self.assertRaises(ValueError):percentile(x,.5)
class EvaluationBindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        cls.data_digest=frozen(cls.root/'data')
        cls.handle=evaluation_data(cls.root/'data',cls.data_digest,registry(),hooks(),split='train')
        cls.metric=config('accounting',{'version':'all-results-v1'})
        cls.key=(cls.metric['id'],cls.metric['version'],cls.metric['config_digest'])
        cls.registration=dict(schema_version='maidionis.evaluation-registration.v1',id='test:evaluation:bindings',version='1',
            experiment_id='offline:1',policy_digest=BUILD,descriptor_digest=digest(canonical(DESCRIPTOR)),
            evaluated_component_digest=BUILD,dataset_digest=cls.data_digest,split='train',selection_scope='train_diagnostic',
            metrics=[cls.metric],baselines=[],calibration='not_applicable',minimum_samples=1,tolerance=1e-6,environment_digest=BUILD)
        cls.predictions=[]
        for row in cls.handle.rows:
            result=dict(schema_version='maidionis.result.v1',request_id=row['sample_id'],**IDENTITY,artifact_digest=BUILD,
                context_ref=None,payload_schema=ref('output'),status='ok',payload=row['target'],diagnostics=None,error=None)
            cls.predictions.append(dict(schema_version='maidionis.prediction.v1',experiment_id='offline:1',run_id='test:run:bindings',
                sample_id=row['sample_id'],dataset_id=row['dataset_id'],dataset_digest=cls.data_digest,split='train',
                descriptor_digest=cls.registration['descriptor_digest'],artifact_digest=BUILD,evaluated_component_digest=BUILD,
                evaluation_registration_digest=digest(canonical(cls.registration)),selection_scope='train_diagnostic',
                calibration_status='not_applicable',result=result,target=row['target'],raw_output_schema=ref('raw'),raw_output=[0,0],
                timing=dict(elapsed_ns=0,profile='test.mechanics'),error_status=None))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def assess(self,predictions=None,*,dataset=None,registration=None,reducer=None,passing=None):
        if reducer is None:reducer=lambda ps:[rate('observed',len(ps),len(self.handle.rows))]
        return evaluate(self.handle if dataset is None else dataset,self.predictions if predictions is None else predictions,
            self.registration if registration is None else registration,registry(),run_id='test:run:bindings',artifact_digest=BUILD,
            reducers={self.key:reducer},passing_policy=(lambda report:True) if passing is None else passing)
    def test_whole_split_bound_and_missing_predictions_not_complete(self):
        report,summary=self.assess()
        self.assertEqual(report['status'],'complete');self.assertTrue(summary['passing'])
        self.assertEqual(report['expected_samples'],self.handle.expected_samples)
        report,summary=self.assess(self.predictions[:1])
        self.assertEqual(report['expected_samples'],self.handle.expected_samples)
        self.assertEqual(report['status'],'invalid_run');self.assertFalse(summary['passing'])
        for rows in (self.handle.rows,self.handle.rows[:1]):
            with self.assertRaises(ValueError):self.assess(dataset=rows)
        with self.assertRaises(ValueError):self.assess(registration=dict(self.registration,dataset_digest='0'*64))
        other=evaluation_data(self.root/'data',self.data_digest,registry(),hooks(),split='dev')
        with self.assertRaises(ValueError):self.assess(dataset=other)
        for mutate in (lambda p:p.update(dataset_id='another.dataset'),lambda p:p.update(dataset_digest='0'*64)):
            predictions=copy.deepcopy(self.predictions);mutate(predictions[0])
            report,summary=self.assess(predictions)
            self.assertEqual(report['status'],'invalid_run');self.assertFalse(summary['passing'])
    def test_verified_handle_cannot_be_constructed_or_mutated(self):
        with self.assertRaises(TypeError):EvaluationDataset()
        with self.assertRaises(FrozenInstanceError):self.handle.dataset_digest='0'*64
        rows=self.handle.rows;rows[0]['dataset_id']='another.dataset';rows[0]['input']['energy']=100
        self.assertNotEqual(rows[0],self.handle.rows[0])
        self.assertEqual(self.assess()[0]['status'],'complete')
        (self.root/'data'/'train.jsonl').write_bytes(b'{}\n')
        try:
            self.assertEqual(self.assess()[0]['status'],'complete')
            with self.assertRaises(ValueError):evaluation_data(self.root/'data',self.data_digest,registry(),hooks(),split='train')
        finally:(self.root/'data'/'train.jsonl').write_bytes(b''.join(canonical(r) for r in self.handle.rows))
    def test_plan_dataset_and_experiment_binding(self):
        with tempfile.TemporaryDirectory() as td:
            p=plan();p['dataset_references']=[dict(id=self.handle.dataset_id,digest=self.data_digest)]
            ledger=EvaluationLedger(td,p)
            for changed in (dict(self.registration,dataset_digest='0'*64),dict(self.registration,experiment_id='other')):
                with self.assertRaises(ValueError):ledger.register(changed,p)
            changed_plan=copy.deepcopy(p);changed_plan['dataset_references']=[dict(id='other',digest='0'*64)]
            with self.assertRaises(ValueError):ledger.register(dict(self.registration,dataset_digest='0'*64),changed_plan)
            ledger.register(self.registration,p);ledger.admit(self.registration,'Offline mechanics')
    def test_abstention_is_complete_and_reducer_policy_owns_eligibility(self):
        predictions=copy.deepcopy(self.predictions);predictions[0]['result'].update(status='abstain',payload=None)
        def reducer(ps):
            answered=[p for p in ps if p['result']['status']=='ok']
            return [rate('coverage',len(answered),len(ps)),rate('answered_accuracy',
                sum(p['result']['payload']==p['target'] for p in answered),len(answered),exclusions=len(ps)-len(answered))]
        report,summary=self.assess(predictions,reducer=reducer)
        self.assertEqual(report['status'],'complete');self.assertTrue(summary['passing'])
        self.assertEqual(report['metrics'][0]['support'],self.handle.expected_samples)
        self.assertEqual(report['metrics'][1]['exclusions'],1)
        report,summary=self.assess(predictions,reducer=reducer,passing=lambda report:report['metrics'][0]['value']==1)
        self.assertEqual(report['status'],'complete');self.assertFalse(summary['passing'])
        for p in predictions:p['result'].update(status='abstain',payload=None)
        report,summary=self.assess(predictions,reducer=reducer)
        self.assertEqual(report['status'],'complete');self.assertIsNone(report['metrics'][1]['value'])
        predictions[0]['result']['payload']=dict(kick=True,snare=True)
        report,summary=self.assess(predictions,reducer=reducer)
        self.assertEqual(report['status'],'invalid_run');self.assertFalse(summary['passing'])
        predictions=copy.deepcopy(self.predictions)
        predictions[0]['result'].update(status='error',payload=None,error=dict(code='internal_error',message='Test error'))
        report,summary=self.assess(predictions,reducer=reducer)
        self.assertEqual(report['status'],'invalid_run');self.assertFalse(summary['passing'])

if __name__=='__main__':unittest.main()
