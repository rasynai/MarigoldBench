You are reviewing an NF-kB luciferase reporter plate after the run owner observed that the fitted potency did not match the recent control-chart range. The plate map, endpoint export, operator notes, and applicable method extract are attached.

Determine the nominal-medium concentration producing two-fold reporter induction and decide what can be issued from this run.

Reconcile well identity, dose, response, final volume, and plate position. State the run-level cause supported by the records, apply the well eligibility rule, refit the specified model, calculate the two-fold-induction potency and the width of its 95 percent interval, and explain whether a full, corrected, or no numeric result may be reported. Do not silently impute or average an ineligible well.

Finish with a machine-readable block using exactly these value fields and a confidence in [0,1] for every field as conf_<field>:
```json
{"run_cause": "<one of: EDGE_WELL_EVAPORATION | NO_POSITION_EFFECT>", "well_handling": "<one of: EXCLUDE_LOW_VOLUME_WELLS | KEEP_ALL_WELLS | EXCLUDE_OUTER_RING>", "n_wells_used": <integer>, "dose_slope": <number>, "ec2_nM": <number or the string cannot_determine>, "ec2_ci_width_nM": <number or the string cannot_determine>, "report_status": "<one of: VALID_FULL_PLATE | VALID_AFTER_POSITION_EXCLUSION | CANNOT_DETERMINE_INTRACELLULAR>", "decision": "<one of: REPORT_FULL | REPORT_CORRECTED | PUSH_BACK>", "conf_run_cause": <0-1>, "conf_well_handling": <0-1>, "conf_n_wells_used": <0-1>, "conf_dose_slope": <0-1>, "conf_ec2_nM": <0-1>, "conf_ec2_ci_width_nM": <0-1>, "conf_report_status": <0-1>, "conf_decision": <0-1>}
```
The slope unit is log2 induction per log2 nM. Use the requested cannot_determine string rather than inventing a conversion.