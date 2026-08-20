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
| claude | 810 | 57.9% | [45.2, 70.1] | [54.5, 61.3] | 45.9% | $1171.46 |
| deepseek | 270 | 51.1% | [40.0, 61.5] | [45.2, 57.0] | - | $14.79 |
| gemini | 810 | 48.9% | [39.1, 58.5] | [45.5, 52.3] | 32.6% | $240.45 |
| glm | 270 | 31.9% | [23.0, 40.7] | [26.6, 37.6] | - | $9.71 |
| gpt | 810 | 58.3% | [46.2, 70.1] | [54.8, 61.6] | 49.6% | $112.75 |
| grok | 810 | 63.2% | [51.7, 74.2] | [59.8, 66.5] | 52.2% | $208.63 |
| kimi | 270 | 29.6% | [20.0, 40.0] | [24.5, 35.3] | - | $19.33 |

## By condition

A system that refuses everything and one that answers everything can
share a VEC. These columns separate them.

| System | C0 sound | H1 planted defect | F2 flawed premise |
|---|---|---|---|
| claude | 167/270 | 163/270 | 139/270 |
| deepseek | 53/90 | 42/90 | 43/90 |
| gemini | 142/270 | 119/270 | 135/270 |
| glm | 37/90 | 16/90 | 33/90 |
| gpt | 180/270 | 151/270 | 141/270 |
| grok | 185/270 | 158/270 | 169/270 |
| kimi | 39/90 | 19/90 | 22/90 |

## Headline on the discriminating band

Families where no system exceeds 80% - the ones carrying the signal.
Anchor families (>=80% for some system) are listed separately and are
not headline evidence; a benchmark with no easy items cannot tell
"hard" from "broken", but they inflate an aggregate.

Discriminating: 15 of 30 families - assay-drift, assay-mechanism, crystal-artifact, docking-decoy-control, dose-extrapolation, enrichment-null, ensemble-disagreement, feature-leakage-audit, hill-slope-anomaly, model-build, promiscuity-flag, qsar-inversion, replicate-power, series-activity-cliff, split-leakage

| System | n | VEC pass@1 | family-clustered 95% CI |
|---|---|---|---|
| claude | 405 | 27.4% | [16.5, 38.8] |
| deepseek | 135 | 33.3% | [20.0, 46.7] |
| gemini | 405 | 32.1% | [22.0, 42.5] |
| glm | 135 | 24.4% | [14.8, 34.8] |
| gpt | 405 | 30.1% | [20.2, 41.0] |
| grok | 405 | 38.5% | [25.2, 50.9] |
| kimi | 135 | 15.6% | [6.7, 25.9] |

## By family

| Family | claude | deepseek | gemini | glm | gpt | grok | kimi |
|---|---|---|---|---|---|---|---|
| admet-filter | 24/27 | 5/9 | 6/27 | 6/9 | 15/27 | 18/27 | 4/9 |
| affinity-delta | 17/27 | 8/9 | 13/27 | 5/9 | 18/27 | 26/27 | 6/9 |
| assay-drift | 18/27 | 6/9 | 14/27 | 4/9 | 19/27 | 21/27 | 5/9 |
| assay-mechanism | 0/27 | 1/9 | 3/27 | 3/9 | 5/27 | 2/27 | 0/9 |
| assay-qc | 26/27 | 6/9 | 12/27 | 6/9 | 25/27 | 21/27 | 6/9 |
| batch-effect-potency | 22/27 | 6/9 | 23/27 | 4/9 | 27/27 | 23/27 | 2/9 |
| binder-selectivity | 23/27 | 7/9 | 10/27 | 5/9 | 17/27 | 19/27 | 9/9 |
| conformer-energy | 25/27 | 6/9 | 16/27 | 2/9 | 27/27 | 27/27 | 4/9 |
| crystal-artifact | 15/27 | 6/9 | 16/27 | 5/9 | 16/27 | 17/27 | 5/9 |
| docking-decoy-control | 7/27 | 0/9 | 7/27 | 0/9 | 4/27 | 0/27 | 0/9 |
| dose-extrapolation | 1/27 | 5/9 | 8/27 | 4/9 | 7/27 | 12/27 | 0/9 |
| dose-units | 25/27 | 9/9 | 19/27 | 2/9 | 27/27 | 26/27 | 2/9 |
| enrichment-null | 17/27 | 6/9 | 18/27 | 6/9 | 17/27 | 19/27 | 3/9 |
| ensemble-disagreement | 15/27 | 5/9 | 11/27 | 2/9 | 11/27 | 12/27 | 2/9 |
| feature-leakage-audit | 0/27 | 1/9 | 0/27 | 1/9 | 5/27 | 5/27 | 0/9 |
| fold-confidence-calibration | 21/27 | 7/9 | 17/27 | 0/9 | 23/27 | 22/27 | 2/9 |
| hill-slope-anomaly | 8/27 | 3/9 | 12/27 | 3/9 | 8/27 | 9/27 | 2/9 |
| model-build | 4/27 | 4/9 | 3/27 | 1/9 | 7/27 | 3/27 | 2/9 |
| multi-objective-pareto | 25/27 | 2/9 | 25/27 | 0/9 | 27/27 | 24/27 | 0/9 |
| pose-rescoring | 27/27 | 7/9 | 26/27 | 2/9 | 27/27 | 27/27 | 2/9 |
| promiscuity-flag | 7/27 | 0/9 | 6/27 | 0/9 | 5/27 | 16/27 | 0/9 |
| qsar-inversion | 5/27 | 5/9 | 14/27 | 2/9 | 14/27 | 17/27 | 0/9 |
| replicate-power | 5/27 | 0/9 | 3/27 | 1/9 | 1/27 | 12/27 | 2/9 |
| selectivity-panel | 27/27 | 9/9 | 27/27 | 7/9 | 27/27 | 27/27 | 6/9 |
| series-activity-cliff | 9/27 | 3/9 | 12/27 | 1/9 | 3/27 | 11/27 | 0/9 |
| split-leakage | 0/27 | 0/9 | 3/27 | 0/9 | 0/27 | 0/27 | 0/9 |
| stability-triage | 26/27 | 5/9 | 24/27 | 6/9 | 16/27 | 27/27 | 7/9 |
| stereo-specificity | 24/27 | 3/9 | 10/27 | 3/9 | 20/27 | 20/27 | 4/9 |
| synthesis-route-cost | 22/27 | 9/9 | 18/27 | 5/9 | 27/27 | 22/27 | 5/9 |
| tautomer-trap | 24/27 | 4/9 | 20/27 | 0/9 | 27/27 | 27/27 | 0/9 |

## Where episodes break

First failing checkpoint, and how the episode ended. A run that never
submits is a different failure from one that submits a wrong answer.

- **claude**: first-failures {'verdict': 32, 'exposure_basis': 26, 'mechanism': 25, 'holdout_set': 24, 'hit_rate': 20, 'predictor': 18}
  - stop reasons {'submitted': 807, 'no_tool_call': 3}; mean tool calls 6.9
- **deepseek**: first-failures {'hit_rate': 9, 'holdout_set': 8, 'verdict': 7, 'mechanism': 7, 'front': 7, 'estimate': 6}
  - stop reasons {'submitted': 266, 'no_tool_call': 4}; mean tool calls 9.7
- **gemini**: first-failures {'mechanism': 30, 'verdict': 26, 'hit_rate': 21, 'estimate': 18, 'design_valid': 17, 'holdout_set': 17}
  - stop reasons {'submitted': 798, 'no_tool_call': 11, 'empty_response': 1}; mean tool calls 14.9
- **glm**: first-failures {'confidence_measured': 9, 'front': 9, 'hit_rate': 9, 'holdout_set': 9, 'species': 9, 'verdict': 8}
  - stop reasons {'submitted': 265, 'no_tool_call': 5}; mean tool calls 10.3
- **gpt**: first-failures {'mechanism': 32, 'verdict': 24, 'holdout_set': 24, 'estimate': 22, 'hit_rate': 22, 'exposure_basis': 20}
  - stop reasons {'submitted': 810}; mean tool calls 7.5
- **grok**: first-failures {'mechanism': 26, 'verdict': 25, 'holdout_set': 20, 'estimate': 18, 'potency': 17, 'basis': 16}
  - stop reasons {'submitted': 810}; mean tool calls 9.5
- **kimi**: first-failures {'exposure_basis': 9, 'front': 9, 'hit_rate': 9, 'predictor': 9, 'holdout_set': 9, 'species': 9}
  - stop reasons {'submitted': 253, 'no_tool_call': 17}; mean tool calls 12.6

## Sealed split

Never published in any form. A large gap between hidden and sealed is
the contamination signal.

- claude: sealed 57.2% (n=180) vs hidden 57.9%; gap +0.7 pp
- gemini: sealed 54.4% (n=180) vs hidden 48.9%; gap -5.6 pp
- gpt: sealed 58.3% (n=180) vs hidden 58.3%; gap -0.1 pp
- grok: sealed 65.0% (n=180) vs hidden 63.2%; gap -1.8 pp

## Integrity

- Every family passes the baseline ladder before it may be scored:
  its own reference submission completes it (B8), an empty submission
  fails every instance (B1), C0 and H1 briefs are byte-identical, and
  no scored field is constant across the population.
- Infrastructure failures are quarantined, never scored: a harness
  crash is not a measurement of a model.
- Tool calls are cached and replayed, so re-scoring never depends on a
  live service and two systems making the same call see the same bytes.

