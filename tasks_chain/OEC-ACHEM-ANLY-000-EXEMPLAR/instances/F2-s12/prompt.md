You are the bioanalytical reviewer releasing a single clinical PK sample. The calibration standards, the preparation log for the batch, the method note extract, and the unknown's peak area are attached.

Report the WHOLE BLOOD concentration of the unknown and state whether the result can be released as a numeric value.

Work through the calibration yourself: decide which standards are eligible, fit the curve as the method requires, quantify the unknown, and apply the method's reporting rules. Show the numbers you rely on and state any assumption you had to make.

Finish your response with a machine-readable block of exactly this shape, using these field names:
```json
{"n_standards_used": <integer>, "regression_weighting": "<one of: weighted_1_over_x2 | unweighted_ols>", "calibration_slope": <number, area per nM>, "unknown_conc_nM": <number or the string cannot_determine>, "quantifiable": "<one of: ABOVE_LLOQ | BELOW_LLOQ | CANNOT_DETERMINE>", "decision": "<one of: RELEASE | DO_NOT_RELEASE | PUSH_BACK>", "conf_n_standards_used": <0-1>, "conf_regression_weighting": <0-1>, "conf_calibration_slope": <0-1>, "conf_unknown_conc_nM": <0-1>, "conf_quantifiable": <0-1>}
```
Give a calibrated confidence in [0,1] for each field: these are read as probabilities that your value is correct.