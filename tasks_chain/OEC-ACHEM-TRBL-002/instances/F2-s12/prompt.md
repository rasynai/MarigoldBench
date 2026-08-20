You are reviewing work order IM-4112 after the laboratory reported a disagreement near the specification-reporting boundary. Determine the result for total impurities in percent w/w and decide what may be issued. The certificate request is for total impurities, including all integrated impurity peaks.

Use the attached replicate calibration responses, saved sequence settings, method extract, and sample worksheet. Apply the stated single-point test and weighted lack-of-fit test, identify the error structure, select the permitted calibration treatment, calculate the slope and sample result, diagnose the run record, and apply the reporting rule. A good r-squared or acceptable mid-level recovery does not by itself answer the work order. Show enough calculations that another reviewer can reproduce the result.

Finish with one machine-readable JSON block using exactly these fields and allowed tokens:
outlier_disposition: RETAIN or EXCLUDE;
lack_of_fit: NO_SIGNIFICANT_LOF or SIGNIFICANT_LOF;
error_structure: PROPORTIONAL_VARIANCE or CONSTANT_VARIANCE;
fit_weighting: WEIGHTED_1_OVER_X2 or UNWEIGHTED_OLS;
calibration_slope: number in area counts per percent;
requested_result_pct: number or the string cannot_determine;
run_diagnosis: NO_RUN_ERROR, WRONG_WEIGHTING_IN_SEQUENCE, SCOPE_NOT_SUPPORTED, or OUTLIER_CAUSED_FAILURE;
report_status: BELOW_REPORTING_THRESHOLD, REPORTABLE_NUMERIC, or CANNOT_DETERMINE;
decision: RELEASE_LT_THRESHOLD, REPROCESS_RELEASE_LT_THRESHOLD, RELEASE_NUMERIC_ABOVE, or PUSH_BACK.

Also include conf_<field> for every field above, including conf_decision. Each confidence must be a number in [0,1] interpreted as the probability that the corresponding value is correct.