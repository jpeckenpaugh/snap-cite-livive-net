import copy
import tempfile
import unittest
from pathlib import Path
from snapcite.engine import ROOT,Failure,Snapshot,canonical,digest,evaluate,load,read,sha
from snapcite.__main__ import pdf,replay

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.raw=(ROOT/'examples/development-snapshot.json').read_bytes()
        self.source=b'part.Name = "Example"\n'
        self.t={'version':'0.1-dev','status':'development-not-qualified','engine':'0.1.0','schema_sha256':digest(read(ROOT/'schemas/manifest.json')),'rubric_sha256':digest(read(ROOT/'schemas/rubric.json')),'snapshot':{'sha256':sha(self.raw),'source':'authored test data','commit':'test','path':'example','redistribution':'development-authored'}}
        self.m={'version':'0.1-dev','touchstone':digest(self.t),'source':{'repository':'https://example.invalid/repo','commit':'a'*40,'path':'example.luau','sha256':sha(self.source)},'coverage':{'scope':'explicit-assertions-only','required_claims':['claim']},'assertions':[{'id':'claim','op':'member_exists','class':'Part','member':'Name','member_type':'Property','span':{'start':0,'end':len(self.source),'sha256':sha(self.source)}}]}
    def run_packet(self): return evaluate(self.m,self.t,self.raw,self.source,digest(self.t))
    def test_canonical_golden(self):
        self.assertEqual(canonical({'z':[2,1],'a':'é'}),b'{"a":"\xc3\xa9","z":[2,1]}')
        self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))
        self.assertNotEqual(digest([1,2]),digest([2,1]))
    def test_reject_ambiguous_json(self):
        for raw in [b'{"a":1,"a":2}',b'NaN',b'1.0',b'9007199254740992',b'"\\ud800"',b'{"\\u00e9":1}']:
            with self.subTest(raw=raw),self.assertRaises(Failure):load(raw)
    def test_json_encoding_contract(self):
        text='{"a":"é"}'
        self.assertEqual(load(text.encode('utf-8')),{'a':'é'})
        self.assertEqual(load(text),{'a':'é'})
        for encoding in ('utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be','utf-8-sig'):
            with self.subTest(encoding=encoding),self.assertRaises(Failure):
                load(text.encode(encoding))
        for raw in (b'"\xff"',b'"\xc0\xaf"','\ufeff'+text):
            with self.subTest(raw=raw),self.assertRaises(Failure):load(raw)

    def test_replay_rejects_non_utf8_json_and_bom(self):
        import shutil
        original=ROOT/'staging/citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815'
        trust='1776068965d523ed851dc5feed880a350694853982b15f480fbe422e69396ea8'
        with tempfile.TemporaryDirectory() as d:
            bundle=Path(d)/'bundle';shutil.copytree(original,bundle)
            self.assertEqual(replay(bundle,trust)['overall'],'green')
            for path in sorted(bundle.rglob('*.json')):
                raw=path.read_bytes();text=raw.decode('utf-8')
                for encoding in ('utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be','utf-8-sig'):
                    with self.subTest(path=str(path.relative_to(bundle)),encoding=encoding):
                        path.write_bytes(text.encode(encoding))
                        try:
                            with self.assertRaises(Failure):replay(bundle,trust)
                        finally:path.write_bytes(raw)
            self.assertEqual(replay(bundle,trust)['overall'],'green')

    def test_inherited_evidence_and_determinism(self):
        p=self.run_packet(); self.assertEqual(p,self.run_packet())
        f=p['findings'][0]; self.assertEqual(f['declaring_entity'],'Instance')
        self.assertEqual(f['evidence'][-1]['pointer'],'/Classes/0/Members/0')
        self.assertEqual(f['snippet'],self.source.decode()); self.assertEqual(p['ci_gate'],'blocked-development')
    def test_exact_case_absence_protocol(self):
        # Protocol branch check, not an entity corpus fixture or agent failure.
        self.m['assertions'][0]['member']='name'
        p=self.run_packet(); self.assertEqual(p['overall'],'red')
        self.assertIn('Name',p['findings'][0]['evidence'][-1]['searched_members']['Instance'])
    def test_missing_required_coverage(self):
        self.m['coverage']['required_claims'].append('missing')
        self.assertEqual(self.run_packet()['overall'],'unevaluated')
    def test_unsupported_cannot_green(self):
        self.m['assertions'][0]['op']='SQL'
        self.assertEqual(self.run_packet()['overall'],'unevaluated')
    def test_tamper_snapshot_source_span(self):
        for target in ['snapshot','source','span','schema','rubric','manifest']:
            with self.subTest(target=target):
                self.setUp()
                if target=='snapshot':self.raw+=b' '
                elif target=='source':self.source+=b' '
                elif target=='span':self.m['assertions'][0]['span']['end']-=1
                elif target=='schema':self.t['schema_sha256']='0'*64;self.m['touchstone']=digest(self.t)
                elif target=='rubric':self.t['rubric_sha256']='0'*64;self.m['touchstone']=digest(self.t)
                else:self.m['touchstone']='0'*64
                with self.assertRaises(Failure):self.run_packet()
    def test_trust_anchor_required(self):
        with self.assertRaises(Failure):evaluate(self.m,self.t,self.raw,self.source,'0'*64)
    def test_strict_schema(self):
        self.m['extra']='ignored?'
        with self.assertRaises(Failure):self.run_packet()
    def test_bad_fields_for_supported_operation(self):
        self.m['assertions'][0]['item']='extra'
        with self.assertRaises(Failure):self.run_packet()
    def test_path_traversal(self):
        self.m['source']['path']='../secret'
        with self.assertRaises(Failure):self.run_packet()
    def test_duplicate_claims(self):
        self.m['assertions']*=2
        with self.assertRaises(Failure):self.run_packet()
    def test_cycles_missing_parent_duplicate_names(self):
        for mutation in ['cycle','missing','duplicate','malformed']:
            x=load(self.raw)
            if mutation=='cycle':x['Classes'][0]['Superclass']='Part'
            if mutation=='missing':x['Classes'][0]['Superclass']='Missing'
            if mutation=='duplicate':x['Classes'].append(x['Classes'][0])
            if mutation=='malformed':del x['Classes'][0]['Members']
            with self.subTest(mutation=mutation),self.assertRaises(Failure):Snapshot(canonical(x))
    def test_deprecated_protocol_branch(self):
        # Only schema/rubric behavior; never asserted as mined failure provenance.
        x=load(self.raw);x['Classes'][0]['Members'][0]['Tags']=['Deprecated']
        self.raw=canonical(x);self.t['snapshot']['sha256']=sha(self.raw);self.m['touchstone']=digest(self.t)
        self.assertEqual(self.run_packet()['overall'],'yellow')
    def test_enum_and_class_operations(self):
        x=load(self.raw);x['Enums']=[{'Name':'Material','Items':[{'Name':'Plastic','Value':1}]}]
        s=Snapshot(canonical(x))
        self.assertEqual(s.query({'id':'c','op':'class_exists','class':'Part','span':{}})['status'],'green')
        self.assertEqual(s.query({'id':'e','op':'enum_item_exists','enum':'Material','item':'Plastic','span':{}})['status'],'green')
    def test_cli_source_commit_binding_and_exit_codes(self):
        import subprocess,sys,os
        with tempfile.TemporaryDirectory() as d:
            b=Path(d);repo=b/'repo';repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
            git('init');(repo/'example.luau').write_bytes(self.source);git('add','example.luau')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','source')
            self.m['source']['commit']=git('rev-parse','HEAD')
            for n,v in [('manifest',self.m),('touchstone',self.t)]: (b/(n+'.json')).write_bytes(canonical(v))
            (b/'snapshot.json').write_bytes(self.raw)
            cmd=[sys.executable,'-m','snapcite','build','--manifest',str(b/'manifest.json'),'--touchstone',str(b/'touchstone.json'),'--snapshot',str(b/'snapshot.json'),'--repo',str(repo),'--out',str(b/'out'),'--trust',digest(self.t),'--pdf']
            run=subprocess.run(cmd,capture_output=True)
            self.assertEqual(run.returncode,1,run.stderr)
            bundle=b/'out'/digest(self.m)
            check=[sys.executable,'-m','snapcite','replay',str(bundle),'--trust',digest(self.t)]
            self.assertEqual(subprocess.run(check,capture_output=True).returncode,1)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2) # immutable output
            (bundle/'source.bin').write_bytes(b'changed')
            self.assertEqual(subprocess.run(check,capture_output=True).returncode,2)
    def test_offline_bundle_replay_and_tamper(self):
        from snapcite.engine import report
        import shutil
        with tempfile.TemporaryDirectory() as d:
            b=Path(d);p=self.run_packet()
            for n,v in [('manifest',self.m),('touchstone',self.t),('packet',p)]:
                (b/(n+'.json')).write_bytes(canonical(v))
            (b/'source.bin').write_bytes(self.source);(b/'snapshot.json').write_bytes(self.raw)
            (b/'schemas').mkdir()
            for n in ('manifest.json','touchstone.json'):shutil.copyfile(ROOT/'schemas'/n,b/'schemas'/n)
            shutil.copyfile(ROOT/'schemas/rubric.json',b/'rubric.json')
            (b/'report.txt').write_text(report(p),encoding='utf-8');pdf(report(p),b/'report.pdf')
            self.assertEqual(replay(b,digest(self.t)),p)
            (b/'report.pdf').write_bytes(b'tampered')
            with self.assertRaises(Failure):replay(b,digest(self.t))
            (b/'report.pdf').unlink()
            p['overall']='yellow';(b/'packet.json').write_bytes(canonical(p))
            with self.assertRaises(Failure):replay(b,digest(self.t))
    def test_pdf_repeatability(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.pdf';b=Path(d)/'b.pdf'
            pdf('Evidence é\n'+str(self.run_packet()),a);pdf('Evidence é\n'+str(self.run_packet()),b)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertTrue(a.read_bytes().startswith(b'%PDF'))

if __name__=='__main__':unittest.main()
