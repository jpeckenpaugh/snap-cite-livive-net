import argparse
import importlib.metadata
import shutil
import subprocess
import sys
import textwrap
import tempfile
from pathlib import Path
from .engine import ROOT, Failure, canonical, digest, evaluate, load, read, report, sha, safe_path

def pdf(text,path):
    if importlib.metadata.version('reportlab')!='4.4.4': raise Failure('ReportLab 4.4.4 required')
    from reportlab.pdfgen import canvas
    c=canvas.Canvas(str(path),pagesize=(612,792),invariant=1,pageCompression=1)
    c.setTitle('Snap Cite development evidence')
    y=756
    for line in text.splitlines():
        # Escaped Unicode preserves every code point with built-in PDF fonts.
        line=line.encode('ascii','backslashreplace').decode('ascii')
        for part in textwrap.wrap(line,width=95,replace_whitespace=False,drop_whitespace=False) or ['']:
            if y<36: c.showPage(); y=756
            c.setFont('Courier',8); c.drawString(24,y,part); y-=10
    c.save()

def replay(bundle,trust):
    b=Path(bundle); m=read(b/'manifest.json'); t=read(b/'touchstone.json')
    for name in ('manifest.json','touchstone.json','rubric.json'):
        if name=='rubric.json' and read(b/name)!=read(ROOT/'schemas'/name): raise Failure('bundled rubric mismatch')
    for name in ('manifest.json','touchstone.json'):
        if read(b/'schemas'/name)!=read(ROOT/'schemas'/name): raise Failure('bundled schema mismatch')
    p=evaluate(m,t,(b/'snapshot.json').read_bytes(),(b/'source.bin').read_bytes(),trust)
    if read(b/'packet.json')!=p: raise Failure('packet mismatch')
    if (b/'report.txt').read_text(encoding='utf-8')!=report(p): raise Failure('report mismatch')
    if (b/'report.pdf').exists():
        with tempfile.TemporaryDirectory() as d:
            generated=Path(d)/'report.pdf'; pdf(report(p),generated)
            if generated.read_bytes()!=(b/'report.pdf').read_bytes(): raise Failure('PDF mismatch (renderer/platform or tampering)')
    return p

def main():
    ap=argparse.ArgumentParser(description='Snap Cite development slice; never freeze-qualified')
    sub=ap.add_subparsers(dest='cmd',required=True)
    build=sub.add_parser('build'); build.add_argument('--manifest',required=True); build.add_argument('--touchstone',required=True); build.add_argument('--snapshot',required=True); build.add_argument('--repo',required=True); build.add_argument('--out',required=True); build.add_argument('--trust',required=True); build.add_argument('--pdf',action='store_true')
    rp=sub.add_parser('replay'); rp.add_argument('bundle'); rp.add_argument('--trust',required=True)
    args=ap.parse_args()
    try:
        if args.cmd=='replay': p=replay(args.bundle,args.trust)
        else:
            m=read(args.manifest); t=read(args.touchstone)
            # Validate before interpolating any source data into a git argument.
            from .engine import validate
            validate(m,read(ROOT/'schemas/manifest.json')); safe_path(m['source']['path'])
            commit=m['source']['commit']
            source=subprocess.run(['git','-C',args.repo,'show',commit+':'+m['source']['path']],check=True,capture_output=True).stdout
            snap=Path(args.snapshot).read_bytes(); p=evaluate(m,t,snap,source,args.trust)
            out=Path(args.out)/p['citation']
            if out.exists(): raise Failure('bundle exists; immutable output refused')
            # Validate before creating output; remove incomplete new directory on failure.
            out.mkdir(parents=True)
            try:
                for n,v in [('manifest',m),('touchstone',t),('packet',p)]: (out/(n+'.json')).write_bytes(canonical(v))
                (out/'snapshot.json').write_bytes(snap); (out/'source.bin').write_bytes(source)
                (out/'schemas').mkdir()
                for n in ('manifest.json','touchstone.json'): shutil.copyfile(ROOT/'schemas'/n,out/'schemas'/n)
                shutil.copyfile(ROOT/'schemas/rubric.json',out/'rubric.json')
                (out/'report.txt').write_text(report(p),encoding='utf-8')
                if args.pdf: pdf(report(p),out/'report.pdf')
                replay(out,args.trust)
            except Exception:
                shutil.rmtree(out); raise
            print('Bundle: '+str(out))
        print('Verdict: '+p['overall']+'; development CI gate blocked')
        return 1
    except (Failure,OSError,subprocess.CalledProcessError,ValueError,KeyError,TypeError) as e:
        print('Execution failure (no verdict): '+str(e),file=sys.stderr); return 2
if __name__=='__main__': sys.exit(main())
