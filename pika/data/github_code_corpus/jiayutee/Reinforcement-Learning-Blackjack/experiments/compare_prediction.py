"""Reproduce the fixed September 26 teaching experiment from the project root."""
import json
from pathlib import Path
from foundations.monte_carlo import estimate_values as mc, source_metadata
from foundations.td import estimate_values as td

seeds = [7, 19, 42, 101, 2026]
states = [(16, 10, False), (20, 10, False), (13, 2, True)]
rows = []
for seed in seeds:
    reports = [('MC', mc(10000, seed, 17)),
               ('TD alpha=0.1', td(10000, seed, 17, 0.1)),
               ('TD alpha=0.05', td(10000, seed, 17, 0.05))]
    baseline = reports[0][1]
    for name, report in reports:
        for key in ('wins', 'losses', 'pushes', 'mean_return'):
            assert report[key] == baseline[key], (seed, name, key)
        selected = [s for s in report['states'] if tuple(s['observation']) in states]
        rows.append({'seed': seed, 'estimator': name,
                     'mean_return': report['mean_return'], 'states': selected})
record = {'source': source_metadata(), 'episodes_per_run': 10000,
          'threshold': 17, 'gamma': 1, 'seeds': seeds,
          'rules': baseline['rules'], 'runs': rows,
          'limitations': 'Descriptive comparison only: no ground-truth values or accuracy ranking. Same fixed policy and seed produce identical games across estimators; these are not 15 independent samples. TD uses constant alpha; MC uses first-visit sample means. Visit meanings differ in general.'}
assert record['source']['foundations_source_dirty'] is False
Path('experiments/2026-09-26-prediction-comparison.json').write_text(json.dumps(record, indent=2)+'\n')
for row in rows:
    print(row['seed'], row['estimator'], row['mean_return'], [(s['observation'], round(s['value'],6), s['visits']) for s in row['states']])
