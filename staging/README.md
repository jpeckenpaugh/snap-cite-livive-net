# Development staging artifacts

These static files demonstrate offline replay and inline evidence in a PDF.
They are not frozen API authority and cannot qualify a merge or release.
A hash-addressed bundle is never replaced. The example snapshot is locally
authored positive engineering data; it is not the proposed upstream snapshot.

A citation directory contains manifest, touchstone, schemas, rubric, snapshot,
source bytes, evidence packet, readable report and PDF. Download the whole directory
or the repository, then run the replay command shown in the report with a reviewer
trusted touchstone hash. URL availability is operational, not part of API evidence.

Development citation: [21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815](citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815/report.txt).
[PDF](citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815/report.pdf) · [manifest](citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815/manifest.json) ·
[touchstone](citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815/touchstone.json).

Review anchor for this staging example: `1776068965d523ed851dc5feed880a350694853982b15f480fbe422e69396ea8`.

```sh
python -m snapcite replay staging/citations/21c499e5932ab745d3dcdd671ed49eb3fc3b4b1e7113ff06be5bb823605bc815 --trust 1776068965d523ed851dc5feed880a350694853982b15f480fbe422e69396ea8
```

Expected exit: 1 (green presence result; development CI gate blocked).
