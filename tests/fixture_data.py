from tinybeat import *
from maidionis_education.datasets import DatasetHooks,prepare_sample,freeze

TIME='2026-10-01T00:00:00Z'
def config(name, value): return dict(id='test.tiny-beat.'+name,version='1',config_digest=digest(canonical(value)))
GROUP=config('group',{'projection':'energy-position-v1'})
VERIFY=config('oracle',{'oracle':'kick>=50,snare>=8'})
GEN=config('generator',{'grid':'energy-0..100-step-10,position-0..15'})
HOOK=config('dataset-hooks',{'implementation':'test-v1','build_digest':BUILD})
def oracle(x): return dict(kick=x['energy']>=50,snare=x['beat_position']>=8)
def hooks():
    return DatasetHooks(HOOK,GROUP,config('dedup',{'projection':'exact-input'}),VERIFY,
        lambda x:[dict(scenario=dict(energy=x['energy'],position=x['beat_position']),template='grid-v1')],
        lambda x:x,lambda row,p:row['target']==oracle(row['input']) and p['ancestry']==['grid-v1',row['family_id']])
def fixture():
    samples=[]; proofs=[]; r=registry(); h=hooks()
    # Preregistered grid and seed. No search for split support.
    for energy in range(0,101,10):
        for position in range(16):
            i=len(samples); x=dict(energy=energy,beat_position=position); sid='row:'+str(i)
            row=dict(schema_version='maidionis.sample.v1',sample_id=sid,family_id='scenario:'+str(i),
                dataset_id='test.grid.v1',**IDENTITY,input_schema=ref('input'),input=x,target_schema=ref('target'),target=oracle(x),
                provenance_id='proof:'+str(i),verification_profile=VERIFY,verification_status='verified',tags=['grid'],supersedes=None)
            row=prepare_sample(row,r,h,42);samples.append(row)
            proofs.append(dict(schema_version='maidionis.provenance.v1',provenance_id=row['provenance_id'],sample_id=sid,
                ancestry=['grid-v1',row['family_id']],source_digest=digest(canonical(x)),source_license='Apache-2.0',generator=GEN,
                teacher=None,reviewer=None,non_model_source_reason='Deterministic synthetic oracle',prompt_digest=None,sampling_digest=None,
                raw_response_digest=None,proposed_target=row['target'],reviewed_target=row['target'],final_target=row['target'],
                verification_profile=VERIFY,outcome='verified',disposition='accepted',human_audit_ref=None,created_at=TIME,supersedes=None))
    return samples,proofs
def frozen(root, fault=lambda _:None):
    rows,proofs=fixture()
    return freeze(root,rows,proofs,registry(),hooks(),component_files(),dataset_id='test.grid.v1',seed=42,created_at=TIME,
                  generator=dict(code_digest=BUILD,config_digest=GEN['config_digest']),license_summary='Synthetic Apache-2.0 test fixture',
                  limitations=['Train-only synthetic mechanics; no generalization or musical quality claim.'],fault=fault)
