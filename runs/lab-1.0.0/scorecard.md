# MarigoldBench scorecard

The model is given a working computational laboratory - structure
prediction, protein design, docking, generative chemistry, RDKit and a
Python environment - and is measured on whether it drives that lab to a
defensible result. Scoring is **Verified Episode Completion (VEC)**:
every checkpoint must pass, and the harness RECOMPUTES each physical or
statistical claim from the submitted artifact. Nothing self-reported is
taken as evidence.

Each family ships three conditions with byte-identical briefs for the
first two: **C0** sound (claiming a problem is a false alarm), **H1** a
planted defect that changes the answer, **F2** a flawed premise where a
documented refusal is the only correct outcome.

Read the family-clustered interval, not the naive one: episodes inside
a family share a generator and are not independent evidence.

## Headline (hidden split)

| System | n | VEC pass@1 | family-clustered 95% CI | naive Wilson | pass^3 | cost |
|---|---|---|---|---|---|---|
| claude | 810 | 61.0% | [48.4, 73.2] | [57.6, 64.3] | 50.4% | $1171.46 |
| deepseek | 270 | 50.7% | [39.6, 61.5] | [44.8, 56.7] | - | $14.79 |
| gemini | 809 | 49.9% | [40.5, 59.3] | [46.5, 53.4] | 33.1% | $238.62 |
| glm | 270 | 31.9% | [23.0, 40.7] | [26.6, 37.6] | - | $9.71 |
| gpt | 806 | 58.9% | [46.9, 70.7] | [55.5, 62.3] | 50.4% | $110.10 |
| grok | 804 | 64.6% | [53.8, 74.9] | [61.2, 67.8] | 54.0% | $198.46 |
| kimi | 270 | 32.2% | [22.2, 42.6] | [26.9, 38.0] | - | $19.33 |

## By condition

A system that refuses everything and one that answers everything can
share a VEC. These columns separate them.

| System | C0 sound | H1 planted defect | F2 flawed premise |
|---|---|---|---|
| claude | 176/270 | 172/270 | 146/270 |
| deepseek | 51/90 | 43/90 | 43/90 |
| gemini | 147/270 | 122/269 | 135/270 |
| glm | 38/90 | 15/90 | 33/90 |
| gpt | 177/266 | 157/270 | 141/270 |
| grok | 188/269 | 162/265 | 169/270 |
| kimi | 43/90 | 20/90 | 24/90 |

## Headline on the discriminating band

Families where no system exceeds 80% - the ones carrying the signal.
Anchor families (>=80% for some system) are listed separately and are
not headline evidence; a benchmark with no easy items cannot tell
"hard" from "broken", but they inflate an aggregate.

Discriminating: 15 of 30 families - assay-drift, assay-mechanism, crystal-artifact, docking-decoy-control, dose-extrapolation, enrichment-null, ensemble-disagreement, feature-leakage-audit, hill-slope-anomaly, model-build, promiscuity-flag, qsar-inversion, replicate-power, series-activity-cliff, split-leakage

| System | n | VEC pass@1 | family-clustered 95% CI |
|---|---|---|---|
| claude | 405 | 30.4% | [19.8, 41.2] |
| deepseek | 135 | 32.6% | [20.0, 45.2] |
| gemini | 405 | 34.1% | [24.7, 43.2] |
| glm | 135 | 24.4% | [14.1, 35.6] |
| gpt | 405 | 31.6% | [21.7, 42.2] |
| grok | 405 | 41.5% | [29.4, 52.8] |
| kimi | 135 | 19.3% | [10.4, 28.9] |

## By family

| Family | claude | deepseek | gemini | glm | gpt | grok | kimi |
|---|---|---|---|---|---|---|---|
| admet-filter | 26/27 | 5/9 | 6/27 | 6/9 | 15/27 | 18/27 | 4/9 |
| affinity-delta | 18/27 | 8/9 | 13/27 | 5/9 | 18/27 | 26/27 | 6/9 |
| assay-drift | 19/27 | 6/9 | 14/27 | 4/9 | 19/27 | 21/27 | 5/9 |
| assay-mechanism | 7/27 | 1/9 | 9/27 | 4/9 | 9/27 | 13/27 | 3/9 |
| assay-qc | 26/27 | 6/9 | 12/27 | 6/9 | 25/27 | 21/27 | 6/9 |
| batch-effect-potency | 27/27 | 6/9 | 23/27 | 4/9 | 27/27 | 23/27 | 2/9 |
| binder-selectivity | 24/27 | 7/9 | 10/27 | 5/9 | 16/25 | 16/23 | 9/9 |
| conformer-energy | 27/27 | 6/9 | 16/27 | 2/9 | 27/27 | 27/27 | 4/9 |
| crystal-artifact | 16/27 | 6/9 | 16/27 | 5/9 | 16/27 | 17/27 | 5/9 |
| docking-decoy-control | 7/27 | 0/9 | 7/27 | 0/9 | 4/27 | 0/27 | 0/9 |
| dose-extrapolation | 1/27 | 5/9 | 8/27 | 4/9 | 7/27 | 12/27 | 2/9 |
| dose-units | 27/27 | 9/9 | 19/27 | 2/9 | 27/27 | 26/27 | 2/9 |
| enrichment-null | 17/27 | 6/9 | 18/27 | 6/9 | 17/27 | 19/27 | 3/9 |
| ensemble-disagreement | 15/27 | 5/9 | 11/27 | 2/9 | 11/27 | 12/27 | 2/9 |
| feature-leakage-audit | 1/27 | 2/9 | 2/27 | 0/9 | 7/27 | 6/27 | 1/9 |
| fold-confidence-calibration | 21/27 | 7/9 | 17/26 | 0/9 | 22/26 | 20/25 | 2/9 |
| hill-slope-anomaly | 9/27 | 3/9 | 12/27 | 3/9 | 8/27 | 9/27 | 2/9 |
| model-build | 5/27 | 2/9 | 3/27 | 1/9 | 7/27 | 3/27 | 1/9 |
| multi-objective-pareto | 25/27 | 2/9 | 25/27 | 0/9 | 27/27 | 24/27 | 0/9 |
| pose-rescoring | 27/27 | 7/9 | 26/27 | 2/9 | 27/27 | 27/27 | 2/9 |
| promiscuity-flag | 7/27 | 0/9 | 6/27 | 0/9 | 5/27 | 16/27 | 0/9 |
| qsar-inversion | 5/27 | 5/9 | 14/27 | 2/9 | 14/27 | 17/27 | 0/9 |
| replicate-power | 5/27 | 0/9 | 3/27 | 1/9 | 1/27 | 12/27 | 2/9 |
| selectivity-panel | 27/27 | 9/9 | 27/27 | 7/9 | 27/27 | 27/27 | 6/9 |
| series-activity-cliff | 9/27 | 3/9 | 12/27 | 1/9 | 3/27 | 11/27 | 0/9 |
| split-leakage | 0/27 | 0/9 | 3/27 | 0/9 | 0/27 | 0/27 | 0/9 |
| stability-triage | 26/27 | 5/9 | 24/27 | 6/9 | 15/26 | 27/27 | 8/9 |
| stereo-specificity | 24/27 | 3/9 | 10/27 | 3/9 | 20/27 | 20/27 | 4/9 |
| synthesis-route-cost | 22/27 | 9/9 | 18/27 | 5/9 | 27/27 | 22/27 | 6/9 |
| tautomer-trap | 24/27 | 4/9 | 20/27 | 0/9 | 27/27 | 27/27 | 0/9 |

## Where episodes break

First failing checkpoint, and how the episode ended. A run that never
submits is a different failure from one that submits a wrong answer.

- **claude**: first-failures {'verdict': 32, 'exposure_basis': 26, 'holdout_set': 24, 'hit_rate': 20, 'mechanism': 19, 'predictor': 18}
  - stop reasons {'submitted': 807, 'no_tool_call': 3}; mean tool calls 6.9
- **deepseek**: first-failures {'hit_rate': 9, 'holdout_set': 8, 'verdict': 7, 'mechanism': 7, 'front': 7, 'estimate': 6}
  - stop reasons {'submitted': 266, 'no_tool_call': 4}; mean tool calls 9.7
- **gemini**: first-failures {'verdict': 26, 'mechanism': 23, 'hit_rate': 21, 'estimate': 18, 'design_valid': 17, 'artifact': 17}
  - stop reasons {'submitted': 797, 'no_tool_call': 11, 'empty_response': 1}; mean tool calls 14.8
- **glm**: first-failures {'confidence_measured': 9, 'front': 9, 'hit_rate': 9, 'holdout_set': 9, 'species': 9, 'verdict': 8}
  - stop reasons {'submitted': 265, 'no_tool_call': 5}; mean tool calls 10.3
- **gpt**: first-failures {'mechanism': 26, 'verdict': 24, 'holdout_set': 24, 'estimate': 22, 'hit_rate': 22, 'exposure_basis': 20}
  - stop reasons {'submitted': 806}; mean tool calls 7.4
- **grok**: first-failures {'verdict': 25, 'holdout_set': 20, 'estimate': 18, 'potency': 17, 'basis': 16, 'mechanism': 15}
  - stop reasons {'submitted': 804}; mean tool calls 9.3
- **kimi**: first-failures {'front': 9, 'hit_rate': 9, 'predictor': 9, 'holdout_set': 9, 'species': 9, 'verdict': 8}
  - stop reasons {'submitted': 253, 'no_tool_call': 17}; mean tool calls 12.6

## Sealed split

Never published in any form. A large gap between hidden and sealed is
the contamination signal.

- claude: sealed 60.6% (n=180) vs hidden 61.0%; gap +0.4 pp
- gemini: sealed 55.3% (n=179) vs hidden 49.9%; gap -5.4 pp
- gpt: sealed 59.4% (n=180) vs hidden 58.9%; gap -0.5 pp
- grok: sealed 67.2% (n=180) vs hidden 64.6%; gap -2.7 pp

## Integrity

- Every family passes the baseline ladder before it may be scored:
  its own reference submission completes it (B8), an empty submission
  fails every instance (B1), C0 and H1 briefs are byte-identical, and
  no scored field is constant across the population.
- Infrastructure failures are quarantined, never scored: a harness
  crash is not a measurement of a model.
- Tool calls are cached and replayed, so re-scoring never depends on a
  live service and two systems making the same call see the same bytes.

