"""Finite offline education with explicit hooks and replayable bounded transport."""
from __future__ import annotations
from dataclasses import dataclass
import http.client
import ssl
import time
import multiprocessing
from urllib.parse import urlsplit
from .contracts import canonical, digest, loads, record
from .storage import Journal,writer

class TransportError(ValueError):
    def __init__(self, message, retryable=False):
        super().__init__(message); self.retryable=retryable

@dataclass(frozen=True)
class TransportLimits:
    input_bytes: int = 65536
    response_bytes: int = 128*1024
    seconds: float = 5
    attempts: int = 3
    def check(self):
        if not (type(self.input_bytes) is int and 0 < self.input_bytes <= 65536 and type(self.response_bytes) is int and
                0 < self.response_bytes <= 128*1024 and 0 < self.seconds <= 60 and type(self.attempts) is int and 1 <= self.attempts <= 3):
            raise ValueError('transport bounds')

class HTTPProvider:
    """Opt-in HTTPS; socket deadlines and bounded chunk reads before allocation."""
    def __init__(self, origin, *, remote_opt_in=False, limits=TransportLimits(), identity=None):
        import copy
        u=urlsplit(origin); limits.check()
        if not remote_opt_in or u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('trusted HTTPS origin and explicit remote opt-in required')
        self.origin=u; self.limits=limits
        self.identity=copy.deepcopy(identity)
    def __call__(self, request, deadline, cancelled):
        # A socket timeout alone cannot bound DNS/TLS/header/body phases together.
        # The host kills and waits for this disposable Linux worker on deadline.
        if cancelled(): raise TransportError('cancelled')
        deadline=min(deadline,time.monotonic()+self.limits.seconds)
        if time.monotonic()>=deadline: raise TransportError('deadline exceeded',True)
        if len(canonical(request))>self.limits.input_bytes: raise TransportError('input byte cap')
        ctx=multiprocessing.get_context('fork');receiver,sender=ctx.Pipe(duplex=False)
        process=ctx.Process(target=_http_worker,args=(self,request,deadline,sender));process.start();sender.close()
        try:
            while True:
                if cancelled(): raise TransportError('cancelled')
                left=deadline-time.monotonic()
                if left<=0: raise TransportError('deadline exceeded',True)
                if receiver.poll(min(left,.05)):
                    try: result=receiver.recv_bytes(self.limits.response_bytes+1024)
                    except (EOFError,OSError) as e: raise TransportError('truncated worker response',True) from e
                    if time.monotonic()>deadline: raise TransportError('deadline exceeded',True)
                    if result[:1]==b'S':
                        if len(result)-1>self.limits.response_bytes: raise TransportError('response byte cap')
                        return result[1:]
                    failure=loads(result[1:])
                    raise TransportError(failure['message'],failure['retryable'])
                if not process.is_alive(): raise TransportError('transport worker failed',True)
        finally:
            receiver.close()
            if process.is_alive(): process.terminate()
            process.join(.1)
            if process.is_alive(): process.kill();process.join()
            process.close()
    def _exchange(self, request, deadline, cancelled):
        raw=canonical(request)
        if len(raw)>self.limits.input_bytes: raise TransportError('input byte cap')
        conn=http.client.HTTPSConnection(self.origin.hostname,self.origin.port,context=ssl.create_default_context())
        def remaining():
            if cancelled(): raise TransportError('cancelled')
            left=min(deadline-time.monotonic(),self.limits.seconds)
            if left<=0: raise TransportError('deadline exceeded',True)
            return left
        try:
            conn.timeout=remaining()
            conn.request('POST',self.origin.path or '/',body=raw,headers={'Content-Type':'application/json'})
            if conn.sock: conn.sock.settimeout(remaining())
            response=conn.getresponse()
            if 300 <= response.status < 400: raise TransportError('redirect rejected')
            if response.status!=200: raise TransportError('HTTP status '+str(response.status),response.status==429 or response.status>=500)
            length=response.getheader('Content-Length')
            if length is not None and (not length.isdecimal() or int(length)>self.limits.response_bytes): raise TransportError('response byte cap')
            out=bytearray()
            while True:
                if conn.sock: conn.sock.settimeout(remaining())
                chunk=response.read1(min(8192,self.limits.response_bytes-len(out)+1))
                remaining()
                if not chunk: break
                out.extend(chunk)
                if len(out)>self.limits.response_bytes: raise TransportError('response byte cap')
            if length is not None and len(out)!=int(length): raise TransportError('truncated response',True)
            return bytes(out)
        except (TimeoutError,OSError,http.client.HTTPException) as e:
            raise TransportError('transport failure',True) from e
        finally: conn.close()

def _http_worker(provider,request,deadline,sender):
    try:
        raw=provider._exchange(request,deadline,lambda:False)
        if not isinstance(raw,bytes) or len(raw)>provider.limits.response_bytes: raise TransportError('response byte cap')
        sender.send_bytes(b'S'+raw)
    except TransportError as e:
        sender.send_bytes(b'E'+canonical(dict(message=str(e),retryable=e.retryable)))
    except Exception:
        sender.send_bytes(b'E'+canonical(dict(message='transport worker failed',retryable=False)))
    finally: sender.close()

@dataclass(frozen=True)
class EducationHooks:
    identity: dict
    native_build_digest: str
    verification_profile: dict
    descriptor_digest: str
    curriculum_digest: str
    prompt_digest: str
    render: object
    validate_target: object
    adjudicate: object
    def check(self,plan):
        if self.identity!=plan['hook_identity'] or self.native_build_digest!=plan['native_build_digest'] or self.verification_profile!=plan['verification_profile']:
            raise ValueError('education hook identity')
        if self.descriptor_digest!=plan['descriptor_digest'] or self.curriculum_digest!=plan['curriculum_digest'] or self.prompt_digest!=plan['prompt_digest']:
            raise ValueError('education task/curriculum/prompt binding')
        if not all(callable(x) for x in (self.render,self.validate_target,self.adjudicate)): raise ValueError('missing explicit education hook')

class Controller:
    def __init__(self,plan,hooks,journal_root,teacher,reviewer,*,limits=TransportLimits(),cancelled=lambda:False):
        import copy
        plan=copy.deepcopy(plan); hooks=copy.deepcopy(hooks)
        self.plan=record('education-plan',plan); hooks.check(plan); limits.check()
        if not callable(teacher) or not callable(reviewer): raise ValueError('providers required')
        if len(plan['providers'])!=2 or getattr(teacher,'identity',None)!=plan['providers'][0] or getattr(reviewer,'identity',None)!=plan['providers'][1]:
            raise ValueError('provider identity')
        self.hooks=hooks; self.journal=Journal(journal_root,plan); self.teacher=teacher; self.reviewer=reviewer
        self.limits=limits; self.cancelled=cancelled; self.started=time.monotonic()
        clock=self.journal.replay('run:clock')
        if clock is None:
            clock=dict(started_ns=time.time_ns()); self.journal.commit('clock','run:clock',clock)
        elapsed=(time.time_ns()-clock['started_ns'])/1e9
        if elapsed<0: raise ValueError('journal clock moved backwards')
        self.deadline=self.started+max(0,plan['max_elapsed_seconds']-elapsed)
    def _check(self):
        if self.cancelled(): raise TransportError('cancelled')
        if time.monotonic()>=self.deadline: raise TransportError('education deadline')
    def _call(self,stage,key,payload,provider):
        replay=self.journal.replay(key)
        request_digest=digest(canonical(payload))
        if replay is not None:
            if replay['request_digest']!=request_digest: raise ValueError('replay request substitution')
            return replay['response']
        for attempt in range(self.limits.attempts):
            self._check()
            _,events,_=self.journal._events()
            if sum(e['event']=='attempt' for e in events)>=self.plan['max_attempts']: raise ValueError('attempt budget')
            # Journal intent before remote work. A crash leaves uncertainty explicit.
            attempt_key=key+':attempt:'+str(attempt)
            if self.journal.replay(attempt_key) is not None:
                failure=self.journal.replay(attempt_key+':failure')
                if failure is not None and failure['retryable']: continue
                raise ValueError('uncertain/failed remote attempt; explicit recovery required')
            self.journal.commit('attempt',attempt_key,dict(request_digest=request_digest,stage=stage))
            deadline=min(self.deadline,time.monotonic()+self.limits.seconds)
            try:
                if len(canonical(payload))>self.limits.input_bytes: raise TransportError('input byte cap')
                raw=provider(payload,deadline,self.cancelled)
                self._check()
                if time.monotonic()>deadline: raise TransportError('transport elapsed deadline',True)
                response=loads(raw,self.limits.response_bytes)
                self.hooks.validate_target(response)
            except TransportError as e:
                self.journal.commit('failure',attempt_key+':failure',dict(reason=str(e),retryable=e.retryable))
                if not e.retryable or attempt+1==self.limits.attempts: raise
                continue
            except (ValueError,UnicodeError) as e:
                self.journal.commit('failure',attempt_key+':failure',dict(reason='schema rejected',retryable=False))
                raise TransportError('schema rejected') from e
            self.journal.commit(stage,key,dict(request_digest=request_digest,response=response))
            return response
    def cycle(self,cycle,inputs):
        # Hold the experiment lease across budget checks and provider calls,
        # not only individual journal writes. Concurrent controllers fail closed.
        with writer(self.journal.root/'controller.lock'):
            return self._cycle(cycle,inputs)
    def _cycle(self,cycle,inputs):
        if type(cycle) is not int or not 0<=cycle<self.plan['max_cycles']: raise ValueError('cycle bound')
        if not isinstance(inputs,list): raise ValueError('input list required')
        _,events,_=self.journal._events()
        completed=sum(e['event']=='adjudication' for e in events)
        new=sum(self.journal.replay(f'cycle:{cycle}:row:{i}:verified') is None for i in range(len(inputs)))
        if completed+new>self.plan['max_examples']: raise ValueError('example budget')
        out=[]
        for i,input_value in enumerate(inputs):
            self._check(); key=f'cycle:{cycle}:row:{i}'
            prompt=self.hooks.render(input_value)
            proposed=self._call('teacher',key+':teacher',prompt,self.teacher)
            # The blind request is rendered from input only, never proposed output.
            reviewed=self._call('reviewer',key+':reviewer',prompt,self.reviewer)
            result=self.hooks.adjudicate(input_value,proposed,reviewed)
            if not isinstance(result,dict) or result.get('status') not in ('verified','rejected','unverified'):
                raise ValueError('adjudication outcome')
            prior=self.journal.replay(key+':verified')
            if prior is None: self.journal.commit('adjudication',key+':verified',result)
            elif prior!=result: raise ValueError('adjudication replay changed')
            out.append(result)
        return out
