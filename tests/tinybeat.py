"""Test-only composition: synthetic mechanics, never a Drum product."""
from maidionis_education.contracts import canonical,digest,RegistryBuilder
from pathlib import Path
IDENTITY=dict(specialization_id='test.tiny-beat',specialization_version='1',task_id='test.tiny-beat',task_version='1')
def code_build_digest(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[1]
    paths=['CMakeLists.txt','tests/tinybeat.py','tests/fixture_data.py','tests/tinybeat_composition.cpp','tests/tinybeat_composition.h']
    for pattern in ('include/maidionis/*.h','src/**/*.cpp','contracts/*.schema.json','education/python/src/maidionis_education/*.py'):
        paths.extend(p.relative_to(root).as_posix() for p in root.glob(pattern))
    raw=b'maidionis-code-build-v1\n'+b''.join((p+'\n'+digest((root/p).read_bytes())+'\n').encode() for p in sorted(paths))
    return digest(raw)
BUILD=code_build_digest()
def object_schema(fields): return dict(type='object',properties=fields,required=list(fields),additionalProperties=False)
INPUT=object_schema(dict(energy=dict(type='integer',minimum=0,maximum=100),beat_position=dict(type='integer',minimum=0,maximum=15)))
OUTPUT=object_schema(dict(kick=dict(type='boolean'),snare=dict(type='boolean')))
RAW=dict(type='array',minItems=2,maxItems=2,items=dict(type='number',minimum=-1e6,maximum=1e6))
SCHEMAS={'input':INPUT,'target':OUTPUT,'output':OUTPUT,'raw':RAW}
CONFIGS={
 'input_codec':{'features':2,'energy_divisor':100,'position_divisor':15},
 'output_codec':{'threshold_milli':500,'tie':'positive'},
 'architecture':{'input_width':2,'hidden_width':8,'output_width':2,'dropout_milli':100},
 'head':{'outputs':2},'objective':{'reduction':'mean','kind':'bernoulli'},
 'numerical_compatibility':{'profile':'linux.cpu.fp32.serial.v1','libtorch':'2.5.1','archive':1}}
def ref(name): return dict(id='test.tiny-beat.'+name,version='1',sha256=digest(canonical(SCHEMAS[name])))
def component(name): return dict(id='test.tiny-beat.'+name,version='1',config_digest=digest(canonical(CONFIGS[name])))
SPEC=b'Tiny Beat synthetic oracle v1: kick when energy >= 50; snare when position >= 8. Mechanics only.\n'
DESCRIPTOR=dict(schema_version='maidionis.specialization.v1',**IDENTITY,
 input_schema=ref('input'),target_schema=ref('target'),output_schema=ref('output'),diagnostics_schema=None,
 semantic_spec=dict(path='semantic.txt',sha256=digest(SPEC)),heads=[component('head')],
 **{k:component(k) for k in CONFIGS if k!='head'})
def registry():
    b=RegistryBuilder(BUILD)
    for k,s in SCHEMAS.items(): b.add_schema(ref(k),s)
    for k,c in CONFIGS.items(): b.add_operation(component(k),c,lambda v:None)
    return b.freeze(DESCRIPTOR)
def component_files():
    return {'descriptor.json':canonical(DESCRIPTOR),'semantic.txt':SPEC,
            **{k+'.schema.json':canonical(v) for k,v in SCHEMAS.items()},
            **{k+'.config.json':canonical(v) for k,v in CONFIGS.items()}}
