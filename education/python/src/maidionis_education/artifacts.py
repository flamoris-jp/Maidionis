"""Immutable offline packaging/finalization; never production approval."""
from pathlib import Path
from .contracts import canonical,digest,loads,record
from .storage import inventory,publish,read,snapshot,writer

EXCLUDED={'manifest.json','training.json','model-card.json','evaluation-registration.json','evaluation-report.json','evaluation-summary.json'}
def component_digest(files):
    return digest(canonical(inventory({p:b for p,b in files.items() if p not in EXCLUDED})))

def export_components(component_files,trained_root):
    p=Path(trained_root); files=dict(component_files)
    files['model.config.json']=read(p/'model.config.json',65536)
    files['weights.pt']=read(p/'best.pt',256*2**20)
    return files

def export_candidate(root,components,trained_root,registration,*,artifact_id,created_at,model_card):
    trained_root=Path(trained_root);files=dict(components)
    training=loads(read(trained_root/'training.json',4*2**20),4*2**20);record('training-metadata',training)
    summary=loads(read(trained_root/'summary.json',4*2**20),4*2**20)
    comp=component_digest(files);record('evaluation-registration',registration)
    if registration['evaluated_component_digest']!=comp or registration['descriptor_digest']!=digest(files['descriptor.json']) or registration['dataset_digest']!=training['dataset_digest']:
        raise ValueError('export registration binding')
    if training['weights_digest']!=digest(files['weights.pt']) or training['state']['best_weights_digest']!=training['weights_digest']:
        raise ValueError('selected-best export')
    files['training.json']=canonical(training);files['evaluation-registration.json']=canonical(registration)
    card=dict(model_card,status='research_candidate',component_digest=comp);record('model-card',card);files['model-card.json']=canonical(card)
    env=summary['environment']
    m=record('artifact',dict(schema_version='maidionis.artifact.v1',format_version=1,artifact_id=artifact_id,created_at=created_at,
        descriptor_digest=digest(files['descriptor.json']),training_run_id=training['training_run_id'],status='research_candidate',files=inventory(files),
        compatibility=dict(profile='linux.cpu.fp32.serial.v1',build_digest=training['build_digest'],libtorch=env['libtorch'],
            compiler_abi=str(env['abi']),platform=env['platform'],dtype='float32'),tensor_inventory=summary['tensor_inventory'],
        limits=dict(max_batch=64,max_input_bytes=65536,parameters=summary['parameter_count']),
        evidence=dict(training_digest=digest(files['training.json']),calibration=dict(state='not_applicable'),
            evaluation=dict(state='pending',evaluation_registration_digest=digest(files['evaluation-registration.json']),evaluated_component_digest=comp))))
    raw=canonical(m);files['manifest.json']=raw
    root=Path(root)
    with writer(root.parent/(root.name+'.publish.lock')):publish(root,files)
    return digest(raw)

def finalize(candidate,expected_digest,destination,report,summary,*,artifact_id,created_at,model_card):
    candidate=Path(candidate);raw=read(candidate/'manifest.json',4*2**20)
    if digest(raw)!=expected_digest: raise ValueError('candidate manifest digest')
    m=record('artifact',loads(raw,4*2**20));files=snapshot(candidate,m['files'],512*2**20,256*2**20)
    if m['status']!='research_candidate' or m['evidence']['evaluation']['state']!='pending': raise ValueError('pending candidate required')
    record('evaluation-report',report);record('evaluation-summary',summary)
    old=m['evidence']['evaluation'];rh=digest(files['evaluation-registration.json']);comp=component_digest(files)
    if comp!=old['evaluated_component_digest'] or rh!=old['evaluation_registration_digest']: raise ValueError('candidate components changed')
    if report['artifact_digest']!=expected_digest or summary['report_digest']!=digest(canonical(report)) or report['status']!=summary['status']:
        raise ValueError('finalization report binding')
    for evidence in (report,summary):
        if evidence['evaluated_component_digest']!=comp or evidence['evaluation_registration_digest']!=rh: raise ValueError('finalization identity')
    registration=record('evaluation-registration',loads(files['evaluation-registration.json']))
    for k in ('descriptor_digest','dataset_digest','split','selection_scope','experiment_id'):
        if report[k]!=registration[k]: raise ValueError('report registration binding')
    if summary['passing'] and report['status']!='complete': raise ValueError('invalid passing evidence')
    # No automatic release/promotion operation exists in this API.
    files['evaluation-report.json']=canonical(report);files['evaluation-summary.json']=canonical(summary)
    card=dict(model_card,status='research_only',component_digest=comp);record('model-card',card);files['model-card.json']=canonical(card)
    m=dict(m,artifact_id=artifact_id,created_at=created_at,status='research_only',files=inventory(files),
        evidence=dict(m['evidence'],evaluation=dict(state='completed',evaluation_registration_digest=rh,evaluated_component_digest=comp,
            report_digest=digest(files['evaluation-report.json']),summary_digest=digest(files['evaluation-summary.json']))))
    record('artifact',m)
    if component_digest(files)!=comp: raise ValueError('finalization mutated evaluated components')
    raw=canonical(m);files['manifest.json']=raw;destination=Path(destination)
    with writer(destination.parent/(destination.name+'.publish.lock')):publish(destination,files)
    return digest(raw)
