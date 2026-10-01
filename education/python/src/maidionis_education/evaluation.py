"""Complete prediction accounting; metrics/passing policy supplied explicitly."""
from .contracts import canonical,digest,record
from .storage import Journal
from .datasets import EvaluationDataset

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
    def __init__(self,root,plan):
        import copy
        self._plan=copy.deepcopy(record('education-plan',plan))
        self.journal=Journal(root,self._plan)
    def register(self,registration,plan):
        record('evaluation-registration',registration)
        if plan!=self._plan: raise ValueError('evaluation plan substitution')
        if registration['policy_digest']!=self._plan['evaluation_policy_digest'] or registration['descriptor_digest']!=self._plan['descriptor_digest'] or registration['experiment_id']!=self._plan['experiment_id']:
            raise ValueError('preregistered evaluation policy')
        if registration['dataset_digest'] not in {ref['digest'] for ref in self._plan['dataset_references']}:
            raise ValueError('evaluation dataset not in plan')
        old=self.journal.replay('evaluation:registration')
        if old is None: self.journal.commit('registration','evaluation:registration',registration)
        elif old!=registration: raise ValueError('registration is immutable')
        return digest(canonical(registration))
    def admit(self,registration,reason):
        h=digest(canonical(registration))
        if self.journal.replay('evaluation:registration')!=registration: raise ValueError('register before evaluation access')
        if self.journal.replay('evaluation:access') is not None: raise ValueError('evaluation access already admitted')
        self.journal.commit('access','evaluation:access',dict(registration_digest=h,reason=reason))

def evaluate(dataset,predictions,registration,registry,*,run_id,artifact_digest,reducers,passing_policy,baselines=None):
    record('evaluation-registration',registration)
    rh=digest(canonical(registration)); errors=[]; ids={}; seen=set(); good=[]
    error_count=0
    def error(message):
        nonlocal error_count
        error_count+=1
        if len(errors)<1000: errors.append(message[:1024])
    if registration['descriptor_digest']!=digest(canonical(registry.descriptor)): raise ValueError('evaluation descriptor')
    if type(dataset) is not EvaluationDataset: raise ValueError('verified evaluation dataset required')
    if dataset.dataset_digest!=registration['dataset_digest'] or dataset.split!=registration['split'] or dataset.descriptor_digest!=registration['descriptor_digest'] or dataset.build_digest!=registry.build_digest:
        raise ValueError('evaluation dataset identity')
    rows=dataset.rows
    if set(reducers)!={(r['id'],r['version'],r['config_digest']) for r in registration['metrics']}:
        raise ValueError('explicit reducer bindings')
    baselines={} if baselines is None else baselines
    if set(baselines)!={(r['id'],r['version'],r['config_digest']) for r in registration['baselines']}:
        raise ValueError('explicit baseline bindings')
    for row in rows:
        registry.sample(row)
        if row['dataset_id']!=dataset.dataset_id or row['split']!=registration['split'] or row['sample_id'] in ids: raise ValueError('expected sample framing')
        ids[row['sample_id']]=row
    if len(ids)!=dataset.expected_samples: raise ValueError('evaluation expected sample inventory')
    if len(ids)<registration['minimum_samples']: error('insufficient support')
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
            if p['target']!=row['target'] or p['error_status'] is not None or p['result']['status'] not in ('ok','abstain'): raise ValueError('error/target prediction')
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
        except (ValueError,KeyError,TypeError) as e: error(str(e))
    if seen!=set(ids): error('missing prediction')
    if error_count>1000: errors[-1]=str(error_count-999)+' additional evaluation errors omitted'
    metrics=[]
    for ref in registration['metrics']:
        metrics.extend(reducers[(ref['id'],ref['version'],ref['config_digest'])](good))
    for ref in registration['baselines']:
        metrics.extend(baselines[(ref['id'],ref['version'],ref['config_digest'])](rows))
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
