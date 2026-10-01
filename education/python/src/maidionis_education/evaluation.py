"""Complete prediction accounting; metrics/passing policy supplied explicitly."""
from .contracts import canonical,digest,record
from .storage import Journal

def percentile(values,p):
    import math
    if not 0<=p<=1 or any(not math.isfinite(x) for x in values): raise ValueError('percentile input')
    if not values: return None
    values=sorted(values); pos=(len(values)-1)*p; lo=int(pos);hi=min(lo+1,len(values)-1)
    return values[lo]+(values[hi]-values[lo])*(pos-lo)

def rate(name,numerator,support,*,slice='all',exclusions=0,denominator='admitted examples'):
    if not 0<=numerator<=support or type(support) is not int: raise ValueError('rate counts')
    return dict(name=name,version='1',value=numerator/support if support else None,numerator=numerator,support=support,
                denominator=denominator,exclusions=exclusions,slice=slice,warning=None if support else 'zero_support')

class EvaluationLedger:
    def __init__(self,root,plan): self.journal=Journal(root,plan)
    def register(self,registration,plan):
        record('evaluation-registration',registration)
        if registration['policy_digest']!=plan['evaluation_policy_digest'] or registration['descriptor_digest']!=plan['descriptor_digest'] or registration['environment_digest'] is None:
            raise ValueError('preregistered evaluation policy')
        old=self.journal.replay('evaluation:registration')
        if old is None: self.journal.commit('registration','evaluation:registration',registration)
        elif old!=registration: raise ValueError('registration is immutable')
        return digest(canonical(registration))
    def admit(self,registration,reason):
        h=digest(canonical(registration))
        if self.journal.replay('evaluation:registration')!=registration: raise ValueError('register before evaluation access')
        if self.journal.replay('evaluation:access') is not None: raise ValueError('evaluation access already admitted')
        self.journal.commit('access','evaluation:access',dict(registration_digest=h,reason=reason))

def evaluate(rows,predictions,registration,registry,*,run_id,artifact_digest,reducers,passing_policy):
    record('evaluation-registration',registration)
    rh=digest(canonical(registration)); errors=[]; ids={}; seen=set(); good=[]
    if registration['descriptor_digest']!=digest(canonical(registry.descriptor)): raise ValueError('evaluation descriptor')
    if set(reducers)!={(r['id'],r['version'],r['config_digest']) for r in registration['metrics']}:
        raise ValueError('explicit reducer bindings')
    for row in rows:
        registry.sample(row)
        if row['split']!=registration['split'] or row['sample_id'] in ids: raise ValueError('expected sample framing')
        ids[row['sample_id']]=row
    if len(ids)<registration['minimum_samples']: errors.append('insufficient support')
    for p in predictions:
        try:
            record('prediction',p); sid=p['sample_id'];row=ids.get(sid)
            if row is None or sid in seen: raise ValueError('unexpected/duplicate prediction')
            seen.add(sid)
            for k,v in dict(experiment_id=registration['experiment_id'],run_id=run_id,dataset_id=row['dataset_id'],
                dataset_digest=registration['dataset_digest'],split=registration['split'],descriptor_digest=registration['descriptor_digest'],
                artifact_digest=artifact_digest,evaluated_component_digest=registration['evaluated_component_digest'],
                evaluation_registration_digest=rh,selection_scope=registration['selection_scope']).items():
                if p[k]!=v: raise ValueError('prediction identity')
            if p['target']!=row['target'] or p['error_status'] is not None or p['result']['status']!='ok': raise ValueError('error/target prediction')
            if registration['calibration']=='required' and p['calibration_status']!='calibrated': raise ValueError('required calibration')
            if registration['calibration']=='not_applicable' and p['calibration_status'] not in ('not_applicable','uncalibrated'): raise ValueError('calibration claim')
            registry.payload('target_schema',p['target'])
            # Raw schema is an explicit registered specialization extension.
            refs=registry._schemas
            raw_ref=p['raw_output_schema']; bound=refs.get((raw_ref['id'],raw_ref['version']))
            if bound is None or bound[0]!=raw_ref: raise ValueError('raw schema binding')
            from .contracts import validate
            validate(p['raw_output'],bound[1])
            request=dict(schema_version='maidionis.request.v1',request_id=sid,
                **{k:row[k] for k in ('specialization_id','specialization_version','task_id','task_version')},
                payload_schema=row['input_schema'],payload=row['input'],context_ref=None)
            registry.result(p['result'],request,artifact_digest); good.append(p)
        except (ValueError,KeyError,TypeError) as e: errors.append(str(e))
    if seen!=set(ids): errors.append('missing prediction')
    metrics=[]
    for ref in registration['metrics']:
        metrics.extend(reducers[(ref['id'],ref['version'],ref['config_digest'])](good))
    report=record('evaluation-report',dict(schema_version='maidionis.evaluation-report.v1',experiment_id=registration['experiment_id'],
        run_id=run_id,descriptor_digest=registration['descriptor_digest'],evaluated_component_digest=registration['evaluated_component_digest'],
        evaluation_registration_digest=rh,dataset_digest=registration['dataset_digest'],artifact_digest=artifact_digest,
        split=registration['split'],selection_scope=registration['selection_scope'],status='invalid_run' if errors else 'complete',
        expected_samples=len(ids),observed_samples=len(predictions),errors=errors,metrics=metrics,
        limitations=['Train diagnostic selection is not held-out generalization.'] if registration['selection_scope']=='train_diagnostic' else []))
    summary=record('evaluation-summary',dict(schema_version='maidionis.evaluation-summary.v1',report_digest=digest(canonical(report)),
        evaluation_registration_digest=rh,evaluated_component_digest=registration['evaluated_component_digest'],status=report['status'],
        passing=not errors and bool(passing_policy(report))))
    return report,summary
