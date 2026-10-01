"""Bounded strict JSON and the shared, closed schema subset (no remote refs)."""
from __future__ import annotations
import hashlib
import json
import math
import re
from importlib.resources import files

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(value) -> bytes:
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
    loads(raw, max_bytes=4*1024*1024)
    return raw

def loads(raw: bytes | str, max_bytes=65536):
    if isinstance(raw,str): raw=raw.encode('utf-8',errors='strict')
    if not isinstance(raw,bytes) or len(raw)>max_bytes: raise ValueError('JSON byte limit')
    text=raw.decode('utf-8',errors='strict')
    # Preflight nesting before the standard DOM decoder allocates containers.
    depth=0; quoted=False; escaped=False
    for c in text:
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c in '[{':
            depth+=1
            if depth>32: raise ValueError('JSON depth limit')
        elif c in ']}': depth-=1
    count=0
    def pairs(items):
        nonlocal count
        out={}
        for key,value in items:
            count+=1
            if count>65536 or len(key.encode('utf-8'))>256 or key in out: raise ValueError('invalid JSON key')
            out[key]=value
        return out
    def bad(_): raise ValueError('nonfinite JSON')
    value=json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
    def walk(v):
        nonlocal count
        count+=1
        if count>65536: raise ValueError('JSON value limit')
        if isinstance(v,str): v.encode('utf-8',errors='strict')
        elif isinstance(v,float) and not math.isfinite(v): raise ValueError('nonfinite JSON')
        elif isinstance(v,int) and not -(2**63)<=v<2**64: raise ValueError('integer overflow')
        elif isinstance(v,dict):
            for x in v.values(): walk(x)
        elif isinstance(v,list):
            for x in v: walk(x)
    walk(value)
    return value

def schema(name):
    return loads(files('maidionis_contracts').joinpath(name+'.schema.json').read_bytes(),4*1024*1024)

def validate(v,s):
    allowed={'$schema','$id','type','properties','required','additionalProperties','items','minItems','maxItems',
             'uniqueItems','minLength','maxLength','pattern','minimum','maximum','enum','const','anyOf'}
    if set(s)-allowed: raise ValueError('unsupported schema keyword')
    if 'anyOf' in s:
        for alternative in s['anyOf']:
            try: validate(v,alternative); return v
            except ValueError: pass
        raise ValueError('schema alternatives mismatch')
    types={'object':isinstance(v,dict),'array':isinstance(v,list),'string':isinstance(v,str),
           'integer':type(v) is int,'number':type(v) in (int,float),'boolean':type(v) is bool,'null':v is None}
    if 'type' in s and not types.get(s['type'],False): raise ValueError('schema type mismatch')
    # Avoid Python's bool/int equality coercion.
    if 'const' in s and (type(v) is not type(s['const']) or v!=s['const']): raise ValueError('schema const mismatch')
    if 'enum' in s and not any(type(v) is type(x) and v==x for x in s['enum']): raise ValueError('schema enum mismatch')
    if isinstance(v,dict):
        properties=s.get('properties',{})
        if set(s.get('required',()))-set(v): raise ValueError('missing schema field')
        if s.get('additionalProperties') is False and set(v)-set(properties): raise ValueError('unknown schema field')
        for k,x in v.items():
            if k in properties: validate(x,properties[k])
    elif isinstance(v,list):
        if not s.get('minItems',0)<=len(v)<=s.get('maxItems',65536): raise ValueError('array length')
        if s.get('uniqueItems') and len({canonical(x) for x in v})!=len(v): raise ValueError('duplicate item')
        if 'items' in s:
            for x in v: validate(x,s['items'])
    elif isinstance(v,str):
        if not s.get('minLength',0)<=len(v)<=s.get('maxLength',4*1024*1024): raise ValueError('string length')
        if 'pattern' in s and re.search(s['pattern'],v,re.ASCII) is None: raise ValueError('string pattern')
    elif type(v) in (int,float):
        if not math.isfinite(v) or not s.get('minimum',-math.inf)<=v<=s.get('maximum',math.inf): raise ValueError('number bound')
    return v

def record(name,value): return validate(value,schema(name))

def safe_path(path):
    if not isinstance(path,str) or len(path.encode())>1024 or path.startswith('/') or '\\' in path or '\x00' in path:
        raise ValueError('invalid relative path')
    if any(x in ('','.', '..') for x in path.split('/')): raise ValueError('invalid relative path')
    return path

class RegistryBuilder:
    def __init__(self,build_digest):
        validate(build_digest,{'type':'string','pattern':'^[a-f0-9]{64}$'})
        self.build_digest=build_digest; self._schemas={}; self._operations={}; self._frozen=False
    def add_schema(self,ref,definition):
        if self._frozen: raise ValueError('registry frozen')
        key=(ref['id'],ref['version'])
        if key in self._schemas or digest(canonical(definition))!=ref['sha256']: raise ValueError('schema binding')
        self._schemas[key]=(ref.copy(),definition)
    def add_operation(self,ref,config,operation):
        if self._frozen or not callable(operation): raise ValueError('operation registration')
        key=(ref['id'],ref['version'])
        if key in self._operations or digest(canonical(config))!=ref['config_digest']: raise ValueError('operation binding')
        self._operations[key]=(ref.copy(),operation)
    def freeze(self,descriptor):
        import copy
        record('specialization',descriptor)
        for k in ('input_schema','target_schema','output_schema','diagnostics_schema'):
            ref=descriptor[k]
            if ref is not None and self._schemas.get((ref['id'],ref['version']),(None,))[0]!=ref: raise ValueError('missing schema binding')
        for ref in [descriptor[k] for k in ('input_codec','output_codec','architecture','objective','numerical_compatibility')]+descriptor['heads']:
            if self._operations.get((ref['id'],ref['version']),(None,))[0]!=ref: raise ValueError('missing operation binding')
        self._frozen=True
        return Registry(copy.deepcopy(descriptor),copy.deepcopy(self._schemas),dict(self._operations),self.build_digest)

class Registry:
    def __init__(self,descriptor,schemas,operations,build_digest):
        self._descriptor=descriptor; self._schemas=schemas; self._operations=operations; self.build_digest=build_digest
    @property
    def descriptor(self):
        import copy
        return copy.deepcopy(self._descriptor)
    def payload(self,field,value):
        ref=self._descriptor[field]
        if ref is None:
            if value is not None: raise ValueError('unexpected diagnostics')
        else: validate(value,self._schemas[(ref['id'],ref['version'])][1])
    def request(self,v):
        record('request',v)
        for k in ('specialization_id','specialization_version','task_id','task_version'):
            if v[k]!=self._descriptor[k]: raise ValueError('request identity')
        if v['payload_schema']!=self._descriptor['input_schema']: raise ValueError('request schema')
        self.payload('input_schema',v['payload']); return v
    def sample(self,v):
        record('sample',v)
        for k in ('specialization_id','specialization_version','task_id','task_version','input_schema','target_schema'):
            if v[k]!=self._descriptor[k]: raise ValueError('sample identity')
        self.payload('input_schema',v['input']); self.payload('target_schema',v['target']); return v
    def result(self,v,request,artifact_digest):
        record('result',v)
        for k in ('request_id','context_ref','specialization_id','specialization_version','task_id','task_version'):
            if v[k]!=request[k]: raise ValueError('result identity')
        if v['artifact_digest']!=artifact_digest or v['payload_schema']!=self._descriptor['output_schema']: raise ValueError('result binding')
        if v['status']=='ok':
            if v['error'] is not None: raise ValueError('ok error')
            self.payload('output_schema',v['payload']); self.payload('diagnostics_schema',v['diagnostics'])
        elif v['status']=='abstain':
            if v['payload'] is not None or v['error'] is not None: raise ValueError('abstention payload')
            self.payload('diagnostics_schema',v['diagnostics'])
        elif v['payload'] is not None or v['diagnostics'] is not None or v['error'] is None: raise ValueError('error payload')
        return v
