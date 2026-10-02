"""Specialization-owned verification/projection, neutral immutable family freeze."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .contracts import canonical, digest, loads, record, validate
from .storage import inventory, publish, read, snapshot, writer

SPLITS = ('train', 'dev', 'calibration_fit', 'calibration_select', 'test')

@dataclass(frozen=True, slots=True, init=False)
class EvaluationDataset:
    """A whole verified split; callers receive copies, never mutable identity state."""
    dataset_digest: str
    dataset_id: str
    descriptor_digest: str
    build_digest: str
    split: str
    expected_samples: int
    _row_bytes: tuple

    def __init__(self, *args, **kwargs):
        raise TypeError('use evaluation_data to verify a frozen dataset')

    @property
    def rows(self):
        return tuple(loads(raw,128*1024) for raw in self._row_bytes)

def evaluation_data(root, trusted_digest, registry, hooks, *, split):
    """Verify the entire frozen tree, then seal all records of the requested split."""
    if split not in SPLITS: raise ValueError('evaluation split')
    manifest, rows=validate_dataset(root,trusted_digest,registry,hooks)
    selected=tuple(canonical(row) for row in rows if row['split']==split)
    count=manifest['counts'][split]['records']
    if len(selected)!=count: raise ValueError('evaluation split accounting')
    handle=object.__new__(EvaluationDataset)
    for name,value in dict(dataset_digest=trusted_digest,dataset_id=manifest['dataset_id'],
        descriptor_digest=digest(canonical(registry.descriptor)),build_digest=registry.build_digest,
        split=split,expected_samples=count,_row_bytes=selected).items():
        object.__setattr__(handle,name,value)
    return handle

def split_for(fingerprint, seed):
    validate(fingerprint, {'type':'string', 'pattern':'^[a-f0-9]{64}$'})
    if type(seed) is not int or not 0 <= seed < 2**63: raise ValueError('split seed')
    h = digest(('maidionis-split-v1\n'+str(seed)+'\n'+fingerprint).encode())
    bucket = int(h[:16], 16) % 10000
    return SPLITS[sum(bucket >= boundary for boundary in (6000, 7500, 8500, 9000))]

@dataclass(frozen=True)
class DatasetHooks:
    identity: dict
    grouping: dict
    dedup: dict
    verification: dict
    root_projection: object
    equivalent_key: object
    verify: object
    split_algorithm: str = "maidionis-split-v1"
    assign_split: object = None
    def check(self):
        if self.split_algorithm == "maidionis-split-v1":
            if self.assign_split is not None: raise ValueError("neutral partition cannot be overridden")
        elif not callable(self.assign_split) or not self.split_algorithm: raise ValueError("explicit partition binding required")
        config = {'type':'object', 'required':['id','version','config_digest'], 'additionalProperties':False,
                  'properties':{'id':{'type':'string'}, 'version':{'type':'string'}, 'config_digest':{'type':'string','pattern':'^[a-f0-9]{64}$'}}}
        for ref in (self.identity, self.grouping, self.dedup, self.verification): validate(ref, config)
        if not all(callable(x) for x in (self.root_projection, self.equivalent_key, self.verify)):
            raise ValueError('missing explicit dataset hook')

def _root_value(v):
    if isinstance(v, dict):
        for x in v.values(): _root_value(x)
    elif isinstance(v, list):
        for x in v: _root_value(x)
    elif type(v) not in (str, int): raise ValueError('anchor root integer/string contract')

def family_for(sample, registry, hooks):
    roots = hooks.root_projection(sample['input'])
    if not isinstance(roots, list) or not roots or len(roots) > 1000: raise ValueError('roots bound')
    entries = []
    for content in roots:
        _root_value(content); entries.append(dict(digest=digest(canonical(content)), content=content))
    entries.sort(key=lambda x:x['digest'])
    if len({x['digest'] for x in entries}) != len(entries): raise ValueError('duplicate roots')
    d = registry.descriptor
    anchor = record('family-anchor', dict(schema_version='maidionis.family-anchor.v1', task_id=d['task_id'],
                      task_version=d['task_version'], grouping_profile=hooks.grouping, root_digests=[x['digest'] for x in entries]))
    return digest(canonical(anchor)), anchor, entries

def assigned_split(sample, fingerprint, hooks, seed):
    if hooks.split_algorithm == 'maidionis-split-v1': return split_for(fingerprint, seed)
    if not callable(hooks.assign_split): raise ValueError('missing compiled partition hook')
    value=hooks.assign_split(sample['input'], fingerprint, seed)
    if value not in SPLITS: raise ValueError('partition result')
    return value

def prepare_sample(sample, registry, hooks, seed):
    """Fill family identity from trusted projection; never use display ID as a seed."""
    result = dict(sample)
    fp, _, _ = family_for(sample, registry, hooks)
    result.update(family_fingerprint=fp, split=assigned_split(sample, fp, hooks, seed))
    registry.sample(result)
    return result

def _validate(samples, provenance, registry, hooks, seed, dataset_id, audit_ancestors=()):
    hooks.check(); ids = {}; proofs = {}; families = {}; equivalent = {}; root_owner = {}; aliases = {}
    for p in provenance:
        record('provenance', p)
        if p['provenance_id'] in proofs: raise ValueError('duplicate provenance')
        proofs[p['provenance_id']] = p
    audit_ids=set()
    for row in audit_ancestors:
        record('audit-ancestor',row)
        d=registry.descriptor
        for k in ('specialization_id','specialization_version','task_id','task_version','input_schema','target_schema'):
            if row[k]!=d[k]: raise ValueError('ancestor contract identity')
        registry.payload('input_schema',row['input']);registry.payload('target_schema',row['target'])
        if row['sample_id'] in ids: raise ValueError('duplicate audit ancestor')
        ids[row['sample_id']]=row;audit_ids.add(row['sample_id'])
        fp,_,_=family_for(row,registry,hooks)
        if row['family_fingerprint']!=fp or row['split']!=assigned_split(row,fp,hooks,seed): raise ValueError('ancestor family/split binding')
        p=proofs.get(row['provenance_id'])
        if p is None or p['sample_id']!=row['sample_id'] or p['source_digest']!=digest(canonical(row['input'])) or p['final_target']!=row['target'] or p['supersedes']!=row['supersedes']:
            raise ValueError('ancestor provenance binding')
        if not p['source_license'] or (p['teacher'] is None and p['reviewer'] is None and not p['non_model_source_reason']):
            raise ValueError('ancestor source evidence')
        if row['verification_status']!=p['outcome'] or row['verification_profile']!=p['verification_profile']: raise ValueError('ancestor audit status/profile')
    for row in samples:
        registry.sample(row)
        if row['sample_id'] in ids or row['dataset_id'] != dataset_id: raise ValueError('sample identity')
        ids[row['sample_id']] = row
        fp, anchor, roots = family_for(row, registry, hooks)
        if row['family_fingerprint'] != fp or row['split'] != assigned_split(row, fp, hooks, seed): raise ValueError('family/split mismatch')
        if row['family_id'] in aliases and aliases[row['family_id']] != fp: raise ValueError('family alias reuse')
        aliases[row['family_id']] = fp
        key = canonical(hooks.equivalent_key(row['input']))
        if key in equivalent and equivalent[key] != fp: raise ValueError('cross-family equivalent')
        equivalent[key] = fp
        for root in roots:
            if root['digest'] in root_owner and root_owner[root['digest']] != fp: raise ValueError('cross-family ancestry needs regrouping')
            root_owner[root['digest']] = fp
        p = proofs.get(row['provenance_id'])
        if p is None or p['sample_id'] != row['sample_id'] or p['final_target'] != row['target'] or p['source_digest'] != digest(canonical(row['input'])):
            raise ValueError('provenance binding')
        if p['verification_profile'] != hooks.verification or row['verification_profile'] != hooks.verification or p['outcome'] != 'verified' or p['disposition'] not in ('accepted','corrected'):
            raise ValueError('verification eligibility')
        if p['teacher'] is None and p['reviewer'] is None and not p['non_model_source_reason']: raise ValueError('absent source reason')
        if p['supersedes'] != row['supersedes'] or not p['source_license'] or not hooks.verify(row, p): raise ValueError('verification/lineage')
        group = families.setdefault(fp, dict(fingerprint=fp, anchor=anchor, roots=roots, aliases=[], members=[],audit_members=[]))
        group['aliases'].append(row['family_id']); group['members'].append(row['sample_id'])
    if len(proofs) != len(samples)+len(audit_ancestors): raise ValueError('extra provenance')
    used_audit=set()
    for row in [*samples,*audit_ancestors]:
        if row['supersedes'] is not None:
            prior = ids.get(row['supersedes'])
            if prior is None or prior['family_fingerprint'] != row['family_fingerprint'] or prior['split'] != row['split']:
                raise ValueError('correction ancestry')
        seen = set(); cur = row
        while cur['supersedes'] is not None:
            if cur['sample_id'] in seen: raise ValueError('lineage cycle')
            seen.add(cur['sample_id']); cur = ids[cur['supersedes']]
            if cur['sample_id'] in audit_ids:used_audit.add(cur['sample_id'])
    if used_audit!=audit_ids:raise ValueError('unreferenced audit ancestor')
    for row in audit_ancestors:
        fp=row['family_fingerprint']
        if fp not in families:raise ValueError('audit ancestor has no admitted descendant')
        if row['family_id'] in aliases and aliases[row['family_id']]!=fp:raise ValueError('ancestor alias collision')
        aliases[row['family_id']]=fp
        families[fp]['aliases'].append(row['family_id']);families[fp]['audit_members'].append(row['sample_id'])
    for f in families.values():
        f['aliases'] = sorted(set(f['aliases'])); f['members'].sort();f['audit_members'].sort()
    return sorted(families.values(), key=lambda f:f['fingerprint'])

def _counts(samples):
    counts = {}
    for split in SPLITS:
        rows = [r for r in samples if r['split'] == split]; tags = {}; support = {}
        for r in rows:
            for t in r['tags']: tags[t] = tags.get(t, 0) + 1
            p = r['verification_profile']['id']; support[p] = support.get(p, 0) + 1
        counts[split] = dict(records=len(rows), families=len({r['family_fingerprint'] for r in rows}),
                             tags=[dict(id=k,count=v) for k,v in sorted(tags.items())],
                             verification_support=[dict(id=k,count=v) for k,v in sorted(support.items())])
    return counts

def _check_components(files, registry):
    descriptor=registry.descriptor
    if files.get('descriptor.json')!=canonical(descriptor): raise ValueError('descriptor bytes')
    semantic=descriptor['semantic_spec']
    if semantic['path'] not in files or digest(files[semantic['path']])!=semantic['sha256']: raise ValueError('semantic component')
    required=[descriptor[k]['sha256'] for k in ('input_schema','target_schema','output_schema','diagnostics_schema') if descriptor[k] is not None]
    required += [descriptor[k]['config_digest'] for k in ('input_codec','output_codec','architecture','objective','numerical_compatibility')]
    required += [r['config_digest'] for r in descriptor['heads']]
    if not set(required)<={digest(b) for b in files.values()}: raise ValueError('missing bound schema/config component')

def freeze(root, samples, provenance, registry, hooks, component_files, *, dataset_id, seed, created_at, generator,
           license_summary, limitations, purpose='research_fixture', audit_ancestors=(),fault=lambda _:None):
    root = Path(root)
    if len(samples) > 1000000 or not samples: raise ValueError('dataset sample bound')
    if len(samples)+len(audit_ancestors)>1000000:raise ValueError('audit/sample bound')
    families = _validate(samples, provenance, registry, hooks, seed, dataset_id,audit_ancestors)
    files = dict(component_files)
    _check_components(files,registry)
    if any(name in files for name in ('family-index.json','provenance.jsonl','audit-ancestors.jsonl','split.config.json','manifest.json',*(s+'.jsonl' for s in SPLITS))):
        raise ValueError('reserved dataset member')
    files['family-index.json'] = canonical(families)
    files['provenance.jsonl'] = b''.join(canonical(p) for p in sorted(provenance,key=lambda p:p['provenance_id']))
    files['audit-ancestors.jsonl']=b''.join(canonical(r) for r in sorted(audit_ancestors,key=lambda r:r['sample_id']))
    for split in SPLITS:
        lines = [canonical(r) for r in sorted(samples,key=lambda r:r['sample_id']) if r['split'] == split]
        if any(len(line) > 128*1024 for line in lines): raise ValueError('record byte bound')
        files[split+'.jsonl'] = b''.join(lines)
    split_config = dict(algorithm=hooks.split_algorithm, seed=seed, grouping=hooks.grouping, hook=hooks.identity)
    files['split.config.json'] = canonical(split_config)
    manifest = record('dataset', dict(schema_version='maidionis.dataset.v1', dataset_id=dataset_id, parent=None,
        descriptor=dict(path='descriptor.json',sha256=digest(files['descriptor.json'])), created_at=created_at, generator=generator,
        split_profile=dict(id='maidionis-split' if hooks.split_algorithm=='maidionis-split-v1' else hooks.split_algorithm,version='1',seed=seed,config_digest=digest(files['split.config.json']),
            grouping_version=hooks.grouping['version'],family_registry_digest=digest(files['family-index.json'])),
        dedup_profile=hooks.dedup, verification_profile=hooks.verification, files=inventory(files), counts=_counts(samples),
        provenance_index=dict(path='provenance.jsonl',sha256=digest(files['provenance.jsonl'])), license_summary=license_summary,
        limitations=limitations, purpose=purpose))
    raw = canonical(manifest); files['manifest.json'] = raw
    with writer(root.parent / (root.name+'.freeze.lock')): publish(root, files, fault)
    return digest(raw)

def validate_dataset(root, trusted_digest, registry, hooks):
    raw = read(Path(root)/'manifest.json', 4*2**20)
    if digest(raw) != trusted_digest: raise ValueError('trusted dataset digest')
    m = record('dataset', loads(raw,4*2**20)); files = snapshot(root, m['files'])
    _check_components(files,registry)
    if m['descriptor']['path']!='descriptor.json' or m['provenance_index']['path']!='provenance.jsonl' or m['split_profile']['grouping_version']!=hooks.grouping['version']:
        raise ValueError('dataset metadata path/profile binding')
    if files.get('descriptor.json') != canonical(registry.descriptor) or digest(files['descriptor.json']) != m['descriptor']['sha256']:
        raise ValueError('descriptor binding')
    config = loads(files['split.config.json'])
    if config != dict(algorithm=hooks.split_algorithm,seed=m['split_profile']['seed'],grouping=hooks.grouping,hook=hooks.identity) or digest(files['split.config.json']) != m['split_profile']['config_digest']:
        raise ValueError('split profile binding')
    if m['dedup_profile'] != hooks.dedup or m['verification_profile'] != hooks.verification: raise ValueError('dataset hook identity')
    def jsonl(raw):
        if raw and not raw.endswith(b'\n'): raise ValueError('JSONL framing')
        return [loads(line,128*1024) for line in raw.splitlines()]
    samples = []
    for split in SPLITS:
        rows = jsonl(files[split+'.jsonl'])
        if any(r['split'] != split for r in rows): raise ValueError('split framing')
        samples.extend(rows)
    proofs = jsonl(files['provenance.jsonl'])
    ancestors=jsonl(files['audit-ancestors.jsonl'])
    families = _validate(samples, proofs, registry, hooks, m['split_profile']['seed'], m['dataset_id'],ancestors)
    if files['family-index.json'] != canonical(families) or digest(files['family-index.json']) != m['split_profile']['family_registry_digest']:
        raise ValueError('family registry binding')
    if digest(files['provenance.jsonl']) != m['provenance_index']['sha256'] or m['counts'] != _counts(samples): raise ValueError('provenance/count binding')
    return m, samples
