#!/usr/bin/env python3
"""Static invariants for Fair Value scenario semantics.
Run: python tests/test_fair_value_invariants.py
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
g=(ROOT/'generate_data.py').read_text(encoding='utf-8')
a=(ROOT/'augment_models.py').read_text(encoding='utf-8')

# FCF Yield: req can reach 18%; Bear must never use a lower yield than Base.
assert "fcfps/max(.16,req),fcfps/req,fcfps/max(.08,req-.02)" in g
for req in (.09,.12,.16,.17,.18):
    fcfps=100.0
    bear=fcfps/max(.16,req);base=fcfps/req;bull=fcfps/max(.08,req-.02)
    assert bear <= base <= bull, (req,bear,base,bull)

# Both core and augmentation composite preserve scenario labels, so every method
# entering them must obey Bear <= Base <= Bull.
assert "comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use)" in g
assert "comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use)" in a
print('PASS fair-value scenario invariants')
