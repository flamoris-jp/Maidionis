import copy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from maidionis_education.contracts import canonical,digest,loads,record,RegistryBuilder,schema,validate
from tinybeat import registry,DESCRIPTOR,BUILD,SCHEMAS,CONFIGS,ref,component,IDENTITY

class Contracts(unittest.TestCase):
    def test_strict_parser(self):
        for raw in [b'{"x":1,"x":2}',b'"\xff"',b'"\\ud800"',b'NaN',b'1e999',b'['*33+b'0'+b']'*33,
                    b'{"'+b'a'*257+b'":0}',b'18446744073709551616']:
            with self.assertRaises(ValueError): loads(raw)
        with self.assertRaises(ValueError): loads(b' '*65537)
    def test_native_python_shared_contracts(self):
        exe=os.environ.get('MAIDIONIS_CONTRACT_CHECK')
        if not exe: self.skipTest('native contract checker not supplied')
        request=dict(schema_version='maidionis.request.v1',request_id='r1',**IDENTITY,payload_schema=ref('input'),payload={'energy':3,'beat_position':2},context_ref=None)
        variants=[(canonical(DESCRIPTOR),'specialization',True),(canonical(request),'request',True),
                  (b'{"schema_version":"maidionis.request.v1","schema_version":"x"}','request',False),
                  (canonical(dict(request,extra=1)),'request',False),(canonical(dict(request,request_id=4)),'request',False),
                  (b'{"x":1e999}','request',False)]
        with tempfile.TemporaryDirectory() as td:
            for raw,name,expected in variants:
                p=Path(td)/'case.json';p.write_bytes(raw)
                try: record(name,loads(raw)); py=True
                except ValueError: py=False
                native=subprocess.run([exe,name,str(p)],capture_output=True)
                self.assertEqual(py,expected); self.assertEqual(native.returncode==0,expected)
    def test_registry_binding_and_neutral_request(self):
        r=registry()
        q=dict(schema_version='maidionis.request.v1',request_id='r1',**IDENTITY,payload_schema=ref('input'),payload={'energy':50,'beat_position':8},context_ref=None)
        r.request(q)
        for payload in [{'energy':True,'beat_position':2},{'energy':101,'beat_position':2},{'energy':1,'beat_position':2,'target':True}]:
            with self.assertRaises(ValueError): r.request(dict(q,payload=payload))
        d=r.descriptor;d['task_id']='changed'; self.assertEqual(r.descriptor['task_id'],DESCRIPTOR['task_id'])
        b=RegistryBuilder(BUILD)
        with self.assertRaises(ValueError): b.freeze(DESCRIPTOR)
        b.add_schema(ref('input'),SCHEMAS['input'])
        with self.assertRaises(ValueError): b.add_schema(ref('input'),SCHEMAS['input'])
        with self.assertRaises(ValueError): b.add_operation(component('architecture'),{},lambda v:None)
    def test_schema_validity(self):
        from jsonschema import Draft202012Validator
        import maidionis_contracts
        for p in Path(maidionis_contracts.__file__).parent.glob('*.schema.json'):
            Draft202012Validator.check_schema(loads(p.read_bytes(),4*1024*1024))

if __name__=='__main__': unittest.main()
