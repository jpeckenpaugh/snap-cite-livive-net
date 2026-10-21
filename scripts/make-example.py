"""Build inputs from committed source; never manufactures failure-corpus records."""
import subprocess
from pathlib import Path
from snapcite.engine import ROOT,canonical,digest,sha,read
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
source=subprocess.check_output(['git','show',commit+':examples/presence.luau'])
t={'version':'0.1-dev','status':'development-not-qualified','engine':'0.1.0',
   'schema_sha256':digest(read(ROOT/'schemas/manifest.json')),'rubric_sha256':digest(read(ROOT/'schemas/rubric.json')),
   'snapshot':{'sha256':sha((ROOT/'examples/development-snapshot.json').read_bytes()),'source':'Locally authored positive development example; not upstream API evidence','commit':commit,'path':'examples/development-snapshot.json','redistribution':'development-authored'}}
start=source.index(b'part.Name'); end=source.index(b'\n',start)
m={'version':'0.1-dev','touchstone':digest(t),'source':{'repository':'https://github.com/jpeckenpaugh/snap-cite-livive-net','commit':commit,'path':'examples/presence.luau','sha256':sha(source)},'coverage':{'scope':'explicit-assertions-only','required_claims':['name_presence']},'assertions':[{'id':'name_presence','op':'member_exists','class':'Part','member':'Name','member_type':'Property','span':{'start':start,'end':end,'sha256':sha(source[start:end])}}]}
Path('build').mkdir(exist_ok=True)
for n,v in [('touchstone',t),('manifest',m)]: Path('build/'+n+'.json').write_bytes(canonical(v))
print(digest(t))
