"""Offline intake checks. Recorded reviewer claims are not authenticated approval."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import sys
from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).resolve().parents[1] / 'schemas/intake-record.json'

def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON number: ' + value)
    value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                       parse_constant=constant)
    # Also reject overflow such as 1e999, which parse_constant does not catch.
    def check(v):
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError('nonfinite number')
        if isinstance(v, str): v.encode('utf-8')
        if isinstance(v, dict):
            for k, x in v.items(): check(k); check(x)
        if isinstance(v, list):
            for x in v: check(x)
    check(value)
    return value

def inspect(record, root):
    errors = [('/' + '/'.join(map(str, e.absolute_path)) + ': ' + e.message)
              for e in Draft202012Validator(read_json(SCHEMA)).iter_errors(record)]
    if not errors:
        a = record['artifact']
        path = PurePosixPath(a['path'])
        try:
            if path.is_absolute() or '..' in path.parts or '\\' in a['path']:
                raise ValueError('artifact path must stay within artifact root')
            root = Path(root).resolve()
            target = root.joinpath(*path.parts)
            if not target.resolve().is_relative_to(root):
                raise ValueError('artifact resolves outside artifact root')
            raw = target.read_bytes()
            if hashlib.sha256(raw).hexdigest() != a['sha256']:
                errors.append('/artifact/sha256: raw artifact hash mismatch')
            for name in ('prompt', 'output'):
                span = a[name]
                start, end = span['start'], span['end']
                if not 0 <= start < end <= len(raw):
                    errors.append('/artifact/' + name + ': invalid byte span')
                elif hashlib.sha256(raw[start:end]).hexdigest() != span['sha256']:
                    errors.append('/artifact/' + name + ': span hash mismatch')
            if max(a['prompt']['start'], a['output']['start']) < min(a['prompt']['end'], a['output']['end']):
                errors.append('/artifact: prompt/output spans overlap')
        except (OSError, ValueError) as exc:
            errors.append('/artifact: ' + str(exc))
    complete = not errors
    admission = 'blocked-incomplete'
    if complete:
        r = record['review']
        if record['origin'] == 'authored-test': admission = 'excluded-authored-test'
        elif r['decision'] == 'rejected' or r['independent_decision'] == 'rejected': admission = 'recorded-rejected'
        elif r['curator'] == r['independent_reviewer']: admission = 'blocked-reviewer-not-independent'
        elif r['decision'] == r['independent_decision'] == 'accepted': admission = 'recorded-admitted'
        else: admission = 'pending-review'
    return {'fixture_id':record.get('fixture_id') if isinstance(record,dict) else None,
            'complete':complete,'admission':admission,'errors':sorted(errors)}

def validate_records(records, root):
    results = [inspect(r, root) for r in records]
    ids = [r.get('fixture_id') for r in records if isinstance(r,dict)]
    duplicates = {i for i in ids if isinstance(i,str) and ids.count(i)>1}
    for result in results:
        if isinstance(result['fixture_id'],str) and result['fixture_id'] in duplicates:
            result.update(complete=False, admission='blocked-incomplete')
            result['errors'].append('/fixture_id: duplicate fixture ID')
    seen = set()
    for record, result in zip(records, results):
        if result['complete']:
            a = record['artifact']
            identity = (record['entity'], a['sha256'], a['output']['start'], a['output']['end'])
            if identity in seen:
                result.update(complete=False, admission='blocked-incomplete')
                result['errors'].append('/artifact/output: duplicate entity observation')
            seen.add(identity)
    coverage = {}
    for record, result in zip(records, results):
        if isinstance(record,dict) and isinstance(record.get('entity'),str):
            counts = coverage.setdefault(record['entity'],dict(green=0,yellow=0,red=0))
            if result['admission'] == 'recorded-admitted':
                counts[record['observation']['expected_verdict']] += 1
    return {'schema_version':'intake-report-1','development_gate':'blocked',
            'approval_authentication':'not-performed', 'records':results,
            'coverage':{entity:{'recorded_admitted':counts,'exact_3_2_1':counts==dict(green=3,yellow=2,red=1),
                                'suite_qualified':False} for entity,counts in sorted(coverage.items())}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records',nargs='+',help='record JSON files; no evidence is executed')
    parser.add_argument('--artifact-root',required=True)
    args = parser.parse_args()
    try:
        result = validate_records([read_json(p) for p in args.records],args.artifact_root)
        print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True))
        return 0 if all(r['complete'] for r in result['records']) else 1
    except (OSError,ValueError,TypeError) as exc:
        print('Intake execution failure: '+str(exc),file=sys.stderr)
        return 2

if __name__ == '__main__': sys.exit(main())
