You are the bioanalytical reviewer releasing a single clinical PK sample. The analysis request form, the calibration standards, the preparation log for the batch, the laboratory stock register, the method note extract, and the unknown's peak area are attached.

Report the concentration of the unknown for the matrix and reporting basis specified on the analysis request form, and state whether the result can be released as a numeric value.

Another reviewer must be able to reproduce your result from this response alone, so show the numbers you rely on and note any assumption you had to make.

Finish your response with one machine-readable ```json block containing your value for each of these fields:
- n_standards_used: integer
- regression_weighting: the calibration treatment you used - name exactly one treatment and nothing else in this field
- calibration_slope: number, area counts per nM
- unknown_conc_nM: number ON THE MATRIX AND REPORTING BASIS THE REQUEST FORM SPECIFIES, or the string cannot_determine if no defensible number exists on that basis
- reporting_range_top_nM: the highest calibration level, in nM, of the curve you actually used
- decision: one of RELEASE (issue the numeric result), DO_NOT_RELEASE (the analysis stands but no numeric result may be issued), PUSH_BACK (the request as written cannot be fulfilled and must return to the requester)
Also include conf_<field> for every field above, each a number in [0,1] read as the probability that your value is correct.