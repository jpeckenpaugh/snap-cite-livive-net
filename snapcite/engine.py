"""Deterministic bounded protocol; no source scanning or network access."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
VERSION = '0.1.0'
class Failure(ValueError):
    """Execution failure: no API verdict may be published."""

def sha(data):
    return hashlib.sha256(data).hexdigest()

def _pairs(pairs):
    out = {}
    for k,v in pairs:
        if k in out: raise Failure('duplicate JSON key: '+k)
        out[k] = v
    return out

def canonical(value):
    def check(x):
        if x is None or isinstance(x,bool): return
        if isinstance(x,int) and abs(x)<=2**53-1: return
        if isinstance(x,str):
            if any(0xD800<=ord(c)<=0xDFFF for c in x): raise Failure('surrogate string')
            return
        if isinstance(x,list):
            for v in x: check(v)
            return
        if isinstance(x,dict):
            for k,v in x.items():
                if not isinstance(k,str) or not k.isascii(): raise Failure('object keys must be ASCII')
                check(k); check(v)
            return
        raise Failure('unsupported canonical value')
    check(value)
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')

def load(data):
    try:
        value=json.loads(data,object_pairs_hook=_pairs)
        canonical(value)
        return value
    except (ValueError,UnicodeError,TypeError,RecursionError) as e: raise Failure(str(e)) from e

def read(path): return load(Path(path).read_bytes())
def digest(value): return sha(canonical(value))
def validate(value, schema):
    errors=sorted(Draft202012Validator(schema).iter_errors(value),key=lambda e:str(list(e.path)))
    if errors: raise Failure('schema: '+errors[0].message)

def safe_path(path):
    p=PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts or '\\' in path or path != str(p) or path.startswith('-'):
        raise Failure('unsafe source path')
    return path

class Snapshot:
    def __init__(self, data):
        self.data=load(data)
        try:
            self.classes=self.index(self.data['Classes'],'class')
            self.enums=self.index(self.data['Enums'],'enum')
            self.members={}; self.items={}
            for n,(i,c) in self.classes.items():
                if not isinstance(c['Superclass'],str): raise Failure('bad superclass')
                self.members[n]=self.index(c['Members'],'member')
                for _,m in self.members[n].values():
                    if m.get('MemberType') not in ('Property','Function','Event','Callback'): raise Failure('bad member type')
            for n,(_,e) in self.enums.items(): self.items[n]=self.index(e['Items'],'item')
            for n in self.classes: self.chain(n)
        except (KeyError,TypeError) as e: raise Failure('malformed snapshot') from e
    @staticmethod
    def index(records, kind):
        if not isinstance(records,list): raise Failure('bad '+kind+' list')
        out={}
        for i,r in enumerate(records):
            if not isinstance(r,dict) or not isinstance(r.get('Name'),str) or not r['Name']: raise Failure('bad '+kind+' name')
            if r['Name'] in out: raise Failure('duplicate '+kind+' name')
            if 'Tags' in r and (not isinstance(r['Tags'],list) or any(not isinstance(t,str) for t in r['Tags'])): raise Failure('bad tags')
            out[r['Name']]=(i,r)
        return out
    def chain(self,n):
        out=[]
        while n != '<<<ROOT>>>':
            if n in out: raise Failure('inheritance cycle')
            if n not in self.classes: raise Failure('missing superclass '+n)
            out.append(n); n=self.classes[n][1]['Superclass']
        return out
    def query(self,a):
        op=a['op']; evidence=[]; searched=[]; found=None; deprecated=False
        def add(pointer,record):
            nonlocal deprecated
            evidence.append({'pointer':pointer,'record':record})
            deprecated |= 'Deprecated' in record.get('Tags',[])
        if op in ('class_exists','member_exists'):
            allowed={'id','op','span','class'} | ({'member','member_type'} if op=='member_exists' else set())
            if set(a)!=allowed: raise Failure('wrong fields for '+op)
            n=a['class']; searched=sorted(self.classes) if n not in self.classes else self.chain(n)
            if n in self.classes:
                ci,c=self.classes[n]
                if op=='class_exists': add(f'/Classes/{ci}',c); found=n
                else:
                    for declaring in self.chain(n):
                        ci,c=self.classes[declaring]; add(f'/Classes/{ci}',{k:v for k,v in c.items() if k!='Members'})
                        if a['member'] in self.members[declaring]:
                            mi,m=self.members[declaring][a['member']]; add(f'/Classes/{ci}/Members/{mi}',m)
                            if m['MemberType']==a['member_type']: found=declaring
                            break
                    if found is None:
                        evidence.append({'searched_members':{c:sorted(self.members[c]) for c in self.chain(n)}})
        elif op=='enum_item_exists':
            if set(a)!={'id','op','span','enum','item'}: raise Failure('wrong fields for '+op)
            n=a['enum']; searched=sorted(self.enums)
            if n in self.enums:
                ei,e=self.enums[n]; add(f'/Enums/{ei}',{k:v for k,v in e.items() if k!='Items'})
                searched=sorted(self.items[n])
                if a['item'] in self.items[n]:
                    ii,item=self.items[n][a['item']]; add(f'/Enums/{ei}/Items/{ii}',item); found=n
        else: return {'id':a['id'],'status':'unevaluated','reason':'unsupported operation','evidence':[]}
        return {'id':a['id'],'status':'yellow' if found and deprecated else 'green' if found else 'red',
                'reason':'deprecated entity on lookup path' if found and deprecated else 'exact-case presence' if found else 'exact-case entity absent',
                'declaring_entity':found,'searched':searched,'evidence':evidence}

def evaluate(manifest,touchstone,snapshot_bytes,source_bytes,expected_touchstone):
    ms=read(ROOT/'schemas/manifest.json'); ts=read(ROOT/'schemas/touchstone.json'); rubric=read(ROOT/'schemas/rubric.json')
    validate(touchstone,ts); validate(manifest,ms)
    if digest(touchstone)!=expected_touchstone or manifest['touchstone']!=expected_touchstone: raise Failure('touchstone trust anchor mismatch')
    if touchstone['schema_sha256']!=digest(ms) or touchstone['rubric_sha256']!=digest(rubric): raise Failure('schema/rubric pin mismatch')
    if sha(snapshot_bytes)!=touchstone['snapshot']['sha256']: raise Failure('snapshot hash mismatch')
    safe_path(manifest['source']['path'])
    if sha(source_bytes)!=manifest['source']['sha256']: raise Failure('source file hash mismatch')
    try: source_bytes.decode('utf-8')
    except UnicodeError as e: raise Failure('source must be UTF-8') from e
    ids=[a['id'] for a in manifest['assertions']]
    if len(ids)!=len(set(ids)): raise Failure('duplicate assertion ID')
    snapshot=Snapshot(snapshot_bytes); findings=[]
    for a in manifest['assertions']:
        span=a['span']; start,end=span['start'],span['end']
        if start>=end or end>len(source_bytes) or sha(source_bytes[start:end])!=span['sha256']: raise Failure('source span mismatch')
        try: source_bytes[start:end].decode('utf-8')
        except UnicodeError as e: raise Failure('span splits UTF-8') from e
        finding=snapshot.query(a)
        finding['source_span']=span
        finding['snippet']=source_bytes[start:end].decode('utf-8')
        findings.append(finding)
    required=set(manifest['coverage']['required_claims'])
    gaps=sorted(required-set(ids)); extras=sorted(set(ids)-required)
    incomplete=bool(gaps or extras or any(f['status']=='unevaluated' for f in findings))
    states={f['status'] for f in findings}
    overall='red' if 'red' in states else 'unevaluated' if incomplete else 'yellow' if 'yellow' in states else 'green'
    return {'version':'0.1-dev','engine':VERSION,'qualification':'development-not-qualified',
            'citation':digest(manifest),'touchstone':expected_touchstone,'snapshot_sha256':sha(snapshot_bytes),
            'scope':'Exact-case presence only; explicit assertions; no runtime, access, typing or whole-program proof.',
            'source':manifest['source'],'coverage':{'missing':gaps,'undeclared':extras,'complete':not incomplete},
            'overall':overall,'ci_gate':'blocked-development','findings':findings,
            'limitations':['Snapshot not human-selected','No qualified 3/2/1 corpus or touchstone self-suite','Yellow policy unapproved','Independent review and pilot pending']}

def report(packet):
    return ('SNAP CITE — DEVELOPMENT / NOT FREEZE QUALIFIED\n'
            + 'Citation: '+packet['citation']+'\nTouchstone: '+packet['touchstone']
            +'\nVerdict: '+packet['overall']+'; CI gate: '+packet['ci_gate']
            +'\n'+packet['scope']+'\nOffline replay: python -m snapcite replay BUNDLE --trust '+packet['touchstone']
            +'\nResolver reference (availability not implied): https://sc.livive.net/staging/citations/'+packet['citation']+'/manifest.json'
            +'\n\nComplete inline evidence packet:\n'+json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
