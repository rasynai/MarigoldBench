# NF-kB reporter potency method, section 8 extract

Response is analyzed as log2 induction relative to the same-plate
vehicle mean. Fit response = intercept + slope * log2(dose_nM)
by unweighted least squares over eligible test wells.

A test well is ineligible when its post-read volume is below 44.0 uL. Three or more such wells in a
contiguous perimeter region are assigned to edge evaporation; do not
replace their responses with a plate or dose mean.

The two-fold-induction potency is the dose at fitted response = 1.
For this troubleshooting calculation, use the validated response
repeatability SD of 0.12 log2 units.
With n eligible wells and fitted slope b, calculate
SE[log2 potency] = SD / (abs(b) * sqrt(n)).
The 95 percent interval endpoints are 2 raised to
(fitted log2 potency minus or plus 1.96 times that SE).
Report interval width as upper endpoint minus lower endpoint.

Corrected potency may be reported when every retained dose level is
represented and the position exclusion is documented. Otherwise the
potency is not reportable from the run.

Doses in this method are nominal concentrations in culture medium.
The method does not infer intracellular concentration from nominal dose.