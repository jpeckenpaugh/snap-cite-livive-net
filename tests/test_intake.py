"""Authored engineering records only; none qualifies the genuine corpus."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from snapcite.intake import read_json, validate_records

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw = b'prompt\noutput'
        (self.root/'raw.txt').write_bytes(raw)
        h = lambda b: hashlib.sha256(b).hexdigest()
        self.record = dict(schema_version='intake-1',fixture_id='AUTHORED-TEST-1',origin='authored-test',entity='Part',
            artifact=dict(path='raw.txt',sha256=h(raw),source_ref='authored test, not a generation',access_restrictions='test only',exporter='test author',timestamp='test timestamp',request_id='test-request',response_id='test-response',prompt=dict(start=0,end=6,sha256=h(raw[:6])),output=dict(start=7,end=13,sha256=h(raw[7:]))),
            generation=dict(model_family='authored test placeholder',exact_model_version='authored test placeholder',temperature=0.7,settings_evidence_ref='authored test placeholder'),
            observation=dict(assertion='Part exists',failure_class='none',expected_verdict='green',rationale='test only',snapshot_sha256='0'*64,snapshot_pointer='/Classes/0',inheritance_chain=['Part'],source_span_ref='raw.txt:7:13'),
            review=dict(curator='test-curator',decision='accepted',rationale='test only',independent_reviewer='test-reviewer',independent_decision='accepted',independent_rationale='test only'))
    def run_record(self, record=None):
        return validate_records([self.record if record is None else record],self.root)
    def test_authored_complete_but_excluded(self):
        report=self.run_record()
        self.assertTrue(report['records'][0]['complete'])
        self.assertEqual(report['records'][0]['admission'],'excluded-authored-test')
        self.assertEqual(report['coverage']['Part']['recorded_admitted']['green'],0)
    def test_every_required_field_missing_blocks(self):
        for section in ('artifact','generation','observation','review'):
            for field in self.record[section]:
                r=copy.deepcopy(self.record); del r[section][field]
                with self.subTest(section=section,field=field):
                    self.assertFalse(self.run_record(r)['records'][0]['complete'])
    def test_invalid_metadata(self):
        for temp in (None,True,'0.7'):
            r=copy.deepcopy(self.record); r['generation']['temperature']=temp
            self.assertFalse(self.run_record(r)['records'][0]['complete'])
    def test_tamper_and_span(self):
        for field,value in (('sha256','1'*64),('path','../raw.txt')):
            r=copy.deepcopy(self.record); r['artifact'][field]=value
            self.assertFalse(self.run_record(r)['records'][0]['complete'])
        for start,end in ((-1,5),(0,100),(4,4),(0,6)):
            r=copy.deepcopy(self.record); r['artifact']['output'].update(start=start,end=end)
            self.assertFalse(self.run_record(r)['records'][0]['complete'])
    def test_symlink_escape(self):
        (self.root/'escape').symlink_to('/etc/hosts')
        r=copy.deepcopy(self.record); r['artifact']['path']='escape'
        self.assertFalse(self.run_record(r)['records'][0]['complete'])
    def test_review_and_coverage_mechanics_only(self):
        # Relabel copies solely to exercise admission branches, not actual evidence.
        records=[]
        for i,color in enumerate(['green']*3+['yellow']*2+['red']):
            r=copy.deepcopy(self.record); r.update(fixture_id=f'AUTHORED-BRANCH-{i}',origin='genuine-recorded-output')
            r['observation']['expected_verdict']=color
            raw=f'prompt\noutput-{i}'.encode(); path=f'raw-{i}.txt'; (self.root/path).write_bytes(raw)
            r['artifact'].update(path=path,sha256=hashlib.sha256(raw).hexdigest())
            r['artifact']['output'].update(end=len(raw),sha256=hashlib.sha256(raw[7:]).hexdigest())
            records.append(r)
        report=validate_records(records,self.root)
        self.assertTrue(report['coverage']['Part']['exact_3_2_1'])
        self.assertFalse(report['coverage']['Part']['suite_qualified'])
        self.assertEqual(report['development_gate'],'blocked')
        self.assertEqual(self.run_record(records[0])['records'][0]['admission'],'recorded-admitted')
        records[0]['review']['decision']='pending'
        self.assertEqual(self.run_record(records[0])['records'][0]['admission'],'pending-review')
        records[0]['review']['decision']='rejected'
        self.assertEqual(self.run_record(records[0])['records'][0]['admission'],'recorded-rejected')
        records[0]['review']['decision']='accepted'
        records[0]['review']['independent_reviewer']='test-curator'
        self.assertEqual(self.run_record(records[0])['records'][0]['admission'],'blocked-reviewer-not-independent')
    def test_duplicate_ids_and_entities(self):
        report=validate_records([self.record,self.record],self.root)
        self.assertTrue(all(not r['complete'] for r in report['records']))
    def test_malformed_shapes(self):
        for r in ([],None,42,{'fixture_id':[]}):
            self.assertFalse(validate_records([r],self.root)['records'][0]['complete'])
    def test_duplicate_observation_and_entity_separation(self):
        a=copy.deepcopy(self.record); a['origin']='genuine-recorded-output'
        b=copy.deepcopy(a); b['fixture_id']='AUTHORED-DUPLICATE'
        report=validate_records([a,b],self.root)
        self.assertEqual(report['records'][1]['admission'],'blocked-incomplete')
        b['entity']='Instance'
        report=validate_records([a,b],self.root)
        self.assertEqual(report['coverage']['Part']['recorded_admitted']['green'],1)
        self.assertEqual(report['coverage']['Instance']['recorded_admitted']['green'],1)
        self.assertFalse(report['coverage']['Instance']['exact_3_2_1'])
    def test_cli_exit_codes(self):
        p=self.root/'record.json'
        def run():
            return subprocess.run([sys.executable,'-m','snapcite.intake','--artifact-root',str(self.root),str(p)],capture_output=True,text=True)
        p.write_text(json.dumps(self.record))
        result=run(); self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)['development_gate'],'blocked')
        p.write_text('{}'); self.assertEqual(run().returncode,1)
        p.write_text('{'); self.assertEqual(run().returncode,2)
    def test_strict_json(self):
        p=self.root/'input.json'
        for raw in ('{"a":1,"a":2}','{"temperature":NaN}','{"temperature":1e999}'):
            p.write_text(raw)
            with self.assertRaises(ValueError): read_json(p)
    def test_template_incomplete(self):
        template=read_json(Path(__file__).resolve().parents[1]/'examples/intake-record-template.json')
        self.assertFalse(self.run_record(template)['records'][0]['complete'])

if __name__=='__main__': unittest.main()
