from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import time
import multiprocessing
from tinybeat import *
from fixture_data import VERIFY,HOOK,oracle
from maidionis_education.education import Controller,EducationHooks,TransportLimits,TransportError,HTTPProvider

def plan():
    return dict(schema_version='maidionis.education-plan.v1',experiment_id='offline:1',descriptor_digest=digest(canonical(DESCRIPTOR)),
        hook_identity=HOOK,native_build_digest=BUILD,curriculum_digest=BUILD,prompt_digest=BUILD,providers=[HOOK,HOOK],
        verification_profile=VERIFY,dataset_references=[],training_config_digest=BUILD,selection_config_digest=BUILD,
        calibration_config_digest=None,evaluation_policy_digest=BUILD,max_cycles=2,max_attempts=8,max_examples=2,
        max_elapsed_seconds=60,max_output_bytes=2**20)
def education_hooks():
    return EducationHooks(HOOK,BUILD,VERIFY,digest(canonical(DESCRIPTOR)),BUILD,BUILD,lambda x:dict(input=x),lambda x:registry().payload('target_schema',x),
        lambda x,a,b:dict(status='verified' if a==b==oracle(x) else 'unverified',target=a))
class Fake:
    identity=HOOK
    def __init__(self,replies): self.replies=list(replies);self.calls=[]
    def __call__(self,payload,deadline,cancelled):
        self.calls.append(payload)
        v=self.replies.pop(0)
        if isinstance(v,Exception): raise v
        return v
class Education(unittest.TestCase):
    def test_concurrent_controller_rejected_before_provider_calls_and_budget_changes(self):
        with tempfile.TemporaryDirectory() as td:
            x=dict(energy=100,beat_position=15);raw=canonical(oracle(x));p=plan();p['max_examples']=1
            teacher=Fake([raw]);reviewer=Fake([raw])
            second=Controller(p,education_hooks(),td,teacher,reviewer)
            outer=self
            class Overlap(Fake):
                def __call__(self,*args):
                    with outer.assertRaises(BlockingIOError):second.cycle(1,[x])
                    outer.assertFalse(teacher.calls+reviewer.calls)
                    return super().__call__(*args)
            first=Controller(p,education_hooks(),td,Overlap([raw]),Fake([raw]))
            self.assertEqual(first.cycle(0,[x])[0]['status'],'verified')
            events=first.journal._events()[1]
            self.assertEqual(sum(e['event']=='adjudication' for e in events),1)
            self.assertEqual(sum(e['event']=='attempt' for e in events),2)
            with self.assertRaises(ValueError):second.cycle(1,[x])
            self.assertFalse(teacher.calls+reviewer.calls)
            self.assertEqual(second.cycle(0,[x])[0]['status'],'verified')
        # Exceptions release the controller lease for explicit recovery.
        with tempfile.TemporaryDirectory() as td:
            failed=Controller(plan(),education_hooks(),td,Fake([]),Fake([]),cancelled=lambda:True)
            with self.assertRaises(TransportError):failed.cycle(0,[x])
            recovered=Controller(plan(),education_hooks(),td,Fake([raw]),Fake([raw]))
            self.assertEqual(recovered.cycle(0,[x])[0]['status'],'verified')
    def test_isolated_transport_deadline_oversize_truncation_and_cleanup(self):
        provider=HTTPProvider('https://offline.invalid',remote_opt_in=True,limits=TransportLimits(seconds=.1))
        before={p.pid for p in multiprocessing.active_children()}
        def block(*args): time.sleep(10);return b'{}'
        start=time.monotonic()
        with patch.object(HTTPProvider,'_exchange',block):
            with self.assertRaises(TransportError):provider({},time.monotonic()+.1,lambda:False)
        self.assertLess(time.monotonic()-start,1)
        self.assertEqual(before,{p.pid for p in multiprocessing.active_children()})
        for response in (b'x'*(129*1024),TransportError('truncated',True),TransportError('redirect',False),TransportError('HTTP status 401',False)):
            def exchange(*args):
                if isinstance(response,Exception):raise response
                return response
            with patch.object(HTTPProvider,'_exchange',exchange):
                with self.assertRaises(TransportError):provider({},time.monotonic()+1,lambda:False)
        with patch.object(HTTPProvider,'_exchange',lambda *args:b'{"ok":true}'):
            self.assertEqual(provider({},time.monotonic()+1,lambda:False),b'{"ok":true}')
        with self.assertRaises(TransportError):provider({},time.monotonic()+1,lambda:True)
    def test_blind_review_replay_and_no_agreement_auto_verification(self):
        with tempfile.TemporaryDirectory() as td:
            x=dict(energy=100,beat_position=15);bad=dict(kick=False,snare=False)
            a=Fake([canonical(bad)]);b=Fake([canonical(bad)])
            c=Controller(plan(),education_hooks(),td,a,b)
            self.assertEqual(c.cycle(0,[x])[0]['status'],'unverified')
            self.assertEqual(b.calls,[dict(input=x)])
            a2=Fake([]);b2=Fake([])
            self.assertEqual(Controller(plan(),education_hooks(),td,a2,b2).cycle(0,[x])[0]['status'],'unverified')
            self.assertFalse(a2.calls+b2.calls)
    def test_retries_schema_and_hooks_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            x=dict(energy=100,beat_position=15);raw=canonical(oracle(x))
            a=Fake([TransportError('timeout',True),raw]);b=Fake([raw])
            self.assertEqual(Controller(plan(),education_hooks(),td,a,b).cycle(0,[x])[0]['status'],'verified')
            self.assertEqual(len(a.calls),2)
        with tempfile.TemporaryDirectory() as td:
            a=Fake([b'{"kick":true,"kick":false}']);b=Fake([])
            with self.assertRaises(TransportError): Controller(plan(),education_hooks(),td,a,b).cycle(0,[x])
            self.assertEqual(len(a.calls),1)
        p=plan();p['native_build_digest']='0'*64
        with self.assertRaises(ValueError): Controller(p,education_hooks(),'unused',Fake([]),Fake([]))
        for field in ('descriptor_digest','curriculum_digest','prompt_digest'):
            p=plan();p[field]='0'*64
            with self.assertRaises(ValueError):Controller(p,education_hooks(),'unused',Fake([]),Fake([]))
    def test_bounds_cancel_corrupt_and_uncertain_journal(self):
        x=dict(energy=100,beat_position=15)
        with tempfile.TemporaryDirectory() as td:
            a=Fake([b' '*129000]);c=Controller(plan(),education_hooks(),td,a,Fake([]))
            with self.assertRaises(TransportError): c.cycle(0,[x])
            (Path(td)/'events.jsonl').write_bytes(b'{')
            with self.assertRaises(ValueError): c.journal.replay('x')
        with tempfile.TemporaryDirectory() as td:
            a=Fake([]);c=Controller(plan(),education_hooks(),td,a,Fake([]),cancelled=lambda:True)
            with self.assertRaises(TransportError): c.cycle(0,[x])
            self.assertFalse(a.calls)
        for origin in ('http://example.com','https://user:pass@example.com','https://example.com/?key=x'):
            with self.assertRaises(ValueError): HTTPProvider(origin,remote_opt_in=True)
        with self.assertRaises(ValueError): HTTPProvider('https://example.com')

if __name__=='__main__': unittest.main()
