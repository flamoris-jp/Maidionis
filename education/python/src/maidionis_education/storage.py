"""Linux reference durability. No overwrite, implicit recovery, or symlink import."""
from __future__ import annotations
from contextlib import contextmanager
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import stat
import tempfile
from .contracts import canonical, digest, loads, safe_path

def read(path, cap):
    path = Path(path).absolute()
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = nxt
        source = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(source)
            if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
                raise ValueError('regular file byte bound')
            raw = bytearray()
            while True:
                block = os.read(source, min(65536, cap - len(raw) + 1))
                if not block: break
                raw.extend(block)
                if len(raw) > cap: raise ValueError('file byte bound')
            after = os.fstat(source)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or len(raw) != before.st_size:
                raise ValueError('mutable source')
            return bytes(raw)
        finally: os.close(source)
    finally: os.close(fd)

def _no_links(path):
    path = Path(path).absolute()
    for p in [path, *path.parents]:
        if p.is_symlink(): raise ValueError('symlink path')

def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)

@contextmanager
def writer(path):
    path = Path(path); _no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally: os.close(fd)

def inventory(files):
    return [dict(path=safe_path(p), sha256=digest(b), bytes=len(b)) for p, b in sorted(files.items())]

def durable_write(path, raw, fault=lambda _: None):
    _no_links(path); fault('write')
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            n = os.write(fd, view)
            if n <= 0: raise OSError('short write')
            view = view[n:]
        fault('fsync'); os.fsync(fd)
    finally: os.close(fd)

def publish(path, files, fault=lambda _: None):
    """Fresh tree publication with Linux renameat2(RENAME_NOREPLACE)."""
    import shutil
    path = Path(path); _no_links(path)
    if len(files) > 1000 or sum(map(len, files.values())) > 2**30:
        raise ValueError('publication bound')
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=path.parent))
    try:
        for name, raw in sorted(files.items()):
            member = stage / safe_path(name); member.parent.mkdir(parents=True, exist_ok=True)
            durable_write(member, raw, fault)
            if read(member, len(raw)) != raw: raise ValueError('staging verification')
        for folder in sorted((p for p in stage.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            sync_directory(folder)
        fault('directory_fsync'); sync_directory(stage); fault('rename')
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.renameat2(-100, os.fsencode(stage), -100, os.fsencode(path), 1):
            code = ctypes.get_errno(); raise OSError(code, os.strerror(code))
        sync_directory(path.parent)
    finally:
        if stage.exists(): shutil.rmtree(stage)

def replace(path, raw, fault=lambda _: None):
    path = Path(path); _no_links(path)
    fd, tmp = tempfile.mkstemp(prefix='.pointer-', dir=path.parent); os.close(fd); os.unlink(tmp)
    try:
        durable_write(tmp, raw, fault); fault('pointer')
        os.replace(tmp, path); sync_directory(path.parent)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def snapshot(root, entries, total_cap=2**30, member_cap=64*2**20):
    root = Path(root); _no_links(root)
    if not isinstance(entries, list) or len(entries) > 1000: raise ValueError('inventory bound')
    out = {}; total = 0
    for e in entries:
        if set(e) != {'path', 'sha256', 'bytes'} or type(e['bytes']) is not int or e['bytes'] < 0:
            raise ValueError('inventory fields')
        p = safe_path(e['path']); total += e['bytes']
        if p == 'manifest.json' or p in out or e['bytes'] > member_cap or total > total_cap:
            raise ValueError('inventory bounds/duplicate/self reference')
        b = read(root / p, e['bytes'])
        if len(b) != e['bytes'] or digest(b) != e['sha256']: raise ValueError('inventory digest')
        out[p] = b
    seen = set()
    for p in root.rglob('*'):
        if p.is_symlink(): raise ValueError('symlink member')
        if p.is_dir(): continue
        if not p.is_file(): raise ValueError('nonregular member')
        if p.name == 'manifest.json' and p.parent == root: continue
        seen.add(p.relative_to(root).as_posix())
    if seen != set(out): raise ValueError('extra or missing inventory member')
    return out

class Journal:
    """Single-writer hash chain. Orphan response objects are inert, never replayed."""
    def __init__(self, root, plan, max_bytes=None):
        self.root = Path(root); self.plan = digest(canonical(plan))
        self.max_bytes = max_bytes or plan['max_output_bytes']
    def _events(self):
        p = self.root / 'events.jsonl'
        raw = read(p, self.max_bytes) if p.exists() else b''
        if raw and not raw.endswith(b'\n'): raise ValueError('partial journal')
        events = []; previous = '0'*64; keys = set()
        from .contracts import record
        for line in raw.splitlines():
            e = record('journal-event', loads(line))
            if canonical(e)!=line+b'\n': raise ValueError('noncanonical journal event')
            if e['sequence'] != len(events) or e['previous_digest'] != previous or e['plan_digest'] != self.plan or e['key'] in keys:
                raise ValueError('journal identity/chain')
            b = read(self.root / (e['content_digest']+'.json'), self.max_bytes)
            if digest(b) != e['content_digest']: raise ValueError('journal content')
            keys.add(e['key']); events.append(e); previous = digest(canonical(e))
        return raw, events, previous
    def replay(self, key):
        _, events, _ = self._events()
        for e in events:
            if e['key'] == key: return loads(read(self.root / (e['content_digest']+'.json'), self.max_bytes), self.max_bytes)
        return None
    def commit(self, event, key, value):
        from .contracts import record
        with writer(self.root / 'writer.lock'):
            raw, events, previous = self._events()
            if any(e['key'] == key for e in events): raise ValueError('journal key exists')
            b = canonical(value); h = digest(b)
            e = record('journal-event', dict(schema_version='maidionis.journal-event.v1', sequence=len(events), previous_digest=previous,
                       event=event, key=key, content_digest=h, plan_digest=self.plan))
            line = canonical(e)
            # Include all retained content, not just the journal index.
            retained = sum(p.stat().st_size for p in self.root.glob('*.json'))
            if retained + len(b) + len(raw) + len(line) > self.max_bytes: raise ValueError('journal storage budget')
            p = self.root / (h+'.json')
            if p.exists():
                if read(p, len(b)) != b: raise ValueError('response conflict')
            else: durable_write(p, b); sync_directory(self.root)
            replace(self.root / 'events.jsonl', raw + line)
