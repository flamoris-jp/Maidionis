"""Maintainer-only schema generator. Generated schemas are checked in and shared.

Uses a deliberately small JSON Schema subset implemented in both languages.
No unchecked extension or arbitrary remote $ref is accepted.
"""
import json
from pathlib import Path

def obj(**fields):
    return dict(type="object", properties=fields, required=list(fields), additionalProperties=False)
def arr(item, maximum=1000, minimum=0, unique=False):
    return dict(type="array", items=item, minItems=minimum, maxItems=maximum, uniqueItems=unique)
def string(maximum=128, pattern=None):
    s=dict(type="string", minLength=1, maxLength=maximum)
    if pattern: s["pattern"]=pattern
    return s
def integer(lo=0, hi=2**63-1): return dict(type="integer", minimum=lo, maximum=hi)
def number(lo=-1e30, hi=1e30): return dict(type="number", minimum=lo, maximum=hi)
def enum(*values): return {"enum":list(values)}
def nullable(s): return {"anyOf":[{"type":"null"},s]}
ID=string(pattern=r"^[A-Za-z0-9._:-]{1,128}$")
HASH=string(64,r"^[a-f0-9]{64}$")
PATH=string(1024,r"^[A-Za-z0-9_-][A-Za-z0-9._/-]*$")
TIME=string(32,r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$")
REF=obj(id=ID,version=ID,sha256=HASH)
CONFIG=obj(id=ID,version=ID,config_digest=HASH)
FILE=obj(path=PATH,sha256=HASH,bytes=integer(0,2**30))
FILEREF=obj(path=PATH,sha256=HASH)
IDENTITY=dict(specialization_id=ID,specialization_version=ID,task_id=ID,task_version=ID)
SPLIT=enum("train","dev","calibration_fit","calibration_select","test")
CONTEXT=nullable(obj(source_id=ID,snapshot_id=ID,projection_version=ID,digest=HASH))
VALUE={"anyOf":[{"type":"object"},{"type":"array"},{"type":"string"},{"type":"number"},{"type":"boolean"},{"type":"null"}]}
# VALUE fields are subsequently validated against an explicitly registered schema.
def record(name, **fields): return obj(schema_version={"const":"maidionis."+name+".v1"},**fields)
schemas={}
schemas["specialization"]=record("specialization",**IDENTITY,input_schema=REF,target_schema=REF,output_schema=REF,
 semantic_spec=FILEREF,input_codec=CONFIG,output_codec=CONFIG,architecture=CONFIG,heads=arr(CONFIG,16,1),
 objective=CONFIG,diagnostics_schema=nullable(REF),numerical_compatibility=CONFIG)
schemas["request"]=record("request",request_id=ID,**IDENTITY,payload_schema=REF,payload=VALUE,context_ref=CONTEXT)
schemas["result"]=record("result",request_id=nullable(ID),**{k:nullable(v) for k,v in IDENTITY.items()},
 artifact_digest=nullable(HASH),context_ref=CONTEXT,payload_schema=nullable(REF),status=enum("ok","abstain","error"),
 payload=VALUE,diagnostics=VALUE,error=nullable(obj(code=enum("invalid_request","unsupported_schema","unsupported_specialization",
 "incompatible_contract","input_too_large","artifact_invalid","profile_unsupported","resource_exhausted","nonfinite_output",
 "cancelled","deadline_exceeded","internal_error"),message=string(1024))))
schemas["sample"]=record("sample",sample_id=ID,family_id=ID,family_fingerprint=HASH,dataset_id=ID,**IDENTITY,
 split=SPLIT,input_schema=REF,input=VALUE,target_schema=REF,target=VALUE,provenance_id=ID,
 verification_profile=CONFIG,verification_status=enum("verified"),tags=arr(ID,32,0,True),supersedes=nullable(ID))
schemas["family-anchor"]=record("family-anchor",task_id=ID,task_version=ID,grouping_profile=CONFIG,root_digests=arr(HASH,1000,1,True))
COUNT=obj(records=integer(0,1000000),families=integer(0,1000000),tags=arr(obj(id=ID,count=integer(0,1000000))),
 verification_support=arr(obj(id=ID,count=integer(0,1000000))))
schemas["dataset"]=record("dataset",dataset_id=ID,parent=nullable(obj(id=ID,digest=HASH)),descriptor=FILEREF,created_at=TIME,
 generator=obj(code_digest=HASH,config_digest=HASH),split_profile=obj(id=ID,version=ID,seed=integer(),config_digest=HASH,
 grouping_version=ID,family_registry_digest=HASH),dedup_profile=CONFIG,verification_profile=CONFIG,files=arr(FILE),
 counts=obj(**{k:COUNT for k in SPLIT["enum"]}),provenance_index=FILEREF,license_summary=string(4096),
 limitations=arr(string(4096),32),purpose=enum("research_fixture","registered_evaluation"))
schemas["prediction"]=record("prediction",experiment_id=ID,run_id=ID,sample_id=ID,dataset_id=ID,dataset_digest=HASH,
 split=SPLIT,descriptor_digest=HASH,artifact_digest=HASH,evaluated_component_digest=HASH,evaluation_registration_digest=HASH,
 selection_scope=enum("dev","train_diagnostic"),calibration_status=enum("calibrated","uncalibrated","not_applicable"),
 result=schemas["result"],target=VALUE,raw_output_schema=REF,raw_output=VALUE,
 timing=obj(elapsed_ns=integer(),profile=ID),error_status=nullable(ID))
schemas["evaluation-registration"]=record("evaluation-registration",id=ID,version=ID,experiment_id=ID,
 policy_digest=HASH,descriptor_digest=HASH,evaluated_component_digest=HASH,dataset_digest=HASH,split=SPLIT,
 selection_scope=enum("dev","train_diagnostic"),metrics=arr(CONFIG,32,1),baselines=arr(CONFIG,32),
 calibration=enum("required","not_applicable"),minimum_samples=integer(1,1000000),
 tolerance=number(0,1),environment_digest=HASH)
EVAL_PENDING=obj(state=enum("pending"),evaluation_registration_digest=HASH,evaluated_component_digest=HASH)
EVAL_COMPLETED=obj(state=enum("completed"),evaluation_registration_digest=HASH,evaluated_component_digest=HASH,
 report_digest=HASH,summary_digest=HASH)
CALIBRATION={"anyOf":[obj(state=enum("not_applicable")),obj(state=enum("completed"),record_digest=HASH)]}
TENSOR=obj(name=ID,dtype=enum("float32"),shape=arr(integer(1,30000000),8,1),role=enum("parameter","buffer"))
schemas["artifact"]=record("artifact",format_version={"const":1},artifact_id=ID,created_at=TIME,
 descriptor_digest=HASH,training_run_id=ID,status=enum("research_candidate","research_only","release_candidate"),files=arr(FILE),
 compatibility=obj(profile=ID,build_digest=HASH,libtorch=ID,compiler_abi=ID,platform=ID,dtype=enum("float32")),
 tensor_inventory=arr(TENSOR),limits=obj(max_batch=integer(1,64),max_input_bytes=integer(1,65536),parameters=integer(1,30000000)),
 evidence=obj(training_digest=HASH,calibration=CALIBRATION,evaluation={"anyOf":[EVAL_PENDING,EVAL_COMPLETED]}))
schemas["checkpoint"]=record("checkpoint",checkpoint_id=ID,created_at=TIME,descriptor_digest=HASH,config_digest=HASH,
 dataset_digest=HASH,environment_digest=HASH,codec_digest=HASH,files=arr(FILE),state_digest=HASH,history_digest=HASH)
schemas["training-state"]=record("training-state",completed_epoch=integer(),next_epoch=integer(),global_step=integer(),
 planned_total_steps=integer(1),scheduler=obj(id=ID,version=ID,phase=integer(),base_lr=number(1e-12,1)),
 parameter_groups=arr(obj(name=ID,decay=number(0,1)),100000,1),best_objective=number(0),best_epoch=integer(),
 best_weights_digest=HASH,patience_counter=integer(),stopped={"type":"boolean"},selection_scope=enum("dev","train_diagnostic"),
 epoch_order_version=ID,rng_inventory=arr(PATH,8,1),history=arr(obj(epoch=integer(),step=integer(),loss=number(0),
 objective=number(0),lr=number(0,1),improved={"type":"boolean"}),10000,1))
schemas["provenance"]=record("provenance",provenance_id=ID,sample_id=ID,ancestry=arr(ID,1000,1,True),
 source_digest=HASH,source_license=string(4096),generator=CONFIG,teacher=nullable(CONFIG),reviewer=nullable(CONFIG),
 non_model_source_reason=nullable(string(4096)),prompt_digest=nullable(HASH),sampling_digest=nullable(HASH),
 raw_response_digest=nullable(HASH),proposed_target=VALUE,reviewed_target=VALUE,final_target=VALUE,
 verification_profile=CONFIG,outcome=enum("verified","rejected","unverified"),disposition=enum("accepted","rejected","corrected"),
 human_audit_ref=nullable(HASH),created_at=TIME,supersedes=nullable(ID))
schemas["education-plan"]=record("education-plan",experiment_id=ID,descriptor_digest=HASH,hook_identity=CONFIG,
 native_build_digest=HASH,curriculum_digest=HASH,prompt_digest=HASH,providers=arr(CONFIG,16),verification_profile=CONFIG,
 dataset_references=arr(obj(id=ID,digest=HASH),100),training_config_digest=HASH,selection_config_digest=HASH,
 calibration_config_digest=nullable(HASH),evaluation_policy_digest=HASH,max_cycles=integer(1,1000),
 max_attempts=integer(1,1000000),max_examples=integer(1,1000000),max_elapsed_seconds=integer(1,86400),
 max_output_bytes=integer(1,2**30))
schemas["journal-event"]=record("journal-event",sequence=integer(),previous_digest=HASH,event=ID,key=ID,
 content_digest=HASH,plan_digest=HASH)
METRIC=obj(name=ID,version=ID,value=nullable(number()),numerator=number(0),support=integer(),
 denominator=string(256),exclusions=integer(),slice=ID,warning=nullable(ID))
schemas['evaluation-report']=record('evaluation-report',experiment_id=ID,run_id=ID,descriptor_digest=HASH,
 evaluated_component_digest=HASH,evaluation_registration_digest=HASH,dataset_digest=HASH,artifact_digest=HASH,
 split=SPLIT,selection_scope=enum('dev','train_diagnostic'),status=enum('complete','invalid_run'),
 expected_samples=integer(),observed_samples=integer(),errors=arr(string(1024),1000),metrics=arr(METRIC,1000),
 limitations=arr(string(4096),32))
schemas['evaluation-summary']=record('evaluation-summary',report_digest=HASH,evaluation_registration_digest=HASH,
 evaluated_component_digest=HASH,status=enum('complete','invalid_run'),passing={'type':'boolean'})
schemas['family-index']=arr(obj(fingerprint=HASH,anchor=schemas['family-anchor'],
 roots=arr(obj(digest=HASH,content=VALUE),1000,1),aliases=arr(ID,1000000,1,True),members=arr(ID,1000000,1,True)),1000000)
schemas['model-config']=obj(kind=enum('dense','pooled','encoder'),input_width=integer(1,256),hidden_width=integer(1,1024),
 output_width=integer(1,256),dropout_milli=integer(0,999),vocabulary=integer(0,8192),layers=integer(1,4),heads=integer(1,4),
 ffn_width=integer(1,1024),max_length=integer(1,256),controls=arr(integer(1,8191),16,0,True))
schemas['model-card']=obj(status=enum('research_candidate','research_only','release_candidate'),component_digest=HASH,
 license=string(4096),intended_use=string(4096),limitations=arr(string(4096),32,1))
schemas['training-metadata']=obj(training_run_id=ID,config=obj(seed=integer(),epochs=integer(1,10000),batch_size=integer(1,64),
 patience=integer(1,10000),learning_rate=number(1e-12,1),weight_decay=number(0,1),max_grad_norm=number(1e-12,1000),
 selection_scope=enum('dev','train_diagnostic'),scheduler=enum('linear_decay.v1'),optimizer=enum('adamw.v1'),
 betas=arr(number(0,1),2,2),epsilon=number(1e-12,1),epoch_order=enum('sha256_sort.v1'),device=enum('cpu'),dtype=enum('float32'),threads={"const":1}),
 state=schemas['training-state'],checkpoint_digest=HASH,dataset_digest=HASH,environment_digest=HASH,
 descriptor_digest=HASH,build_digest=HASH,model_config=schemas['model-config'],weights_digest=HASH)
for name, schema in schemas.items():
    schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"maidionis."+name+".v1",**schema}
    (Path(__file__).parent/(name+".schema.json")).write_text(json.dumps(schema,sort_keys=True,indent=2)+"\n")
