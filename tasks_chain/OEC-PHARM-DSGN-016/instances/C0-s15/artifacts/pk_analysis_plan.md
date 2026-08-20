# PK analysis plan extract — absorption design

The pilot may be transferred to the planned study only when route,
formulation code, and unit dose match the planned treatment.
A formulation mismatch requires a replacement pilot; absorption-rate
estimates are not transferred between tablets and suspensions.

For a transferable pilot, include rows with 0.10 <= Fa <= 0.80.
Use verified_elapsed_h rather than nominal_h. Fit
    -ln(1 - Fa) = ka * t
by ordinary least squares constrained through the origin.

The status column records workflow annotations. It does not remove a
row. Exclude a row only when exclusion_code contains EXCLUDE.

The regular early grid runs from 0.00 through 1.50 h, including both
endpoints. Its selected interval must:
  1. be no greater than one half of the fitted absorption half-life;
  2. be an integer multiple of 0.05 h;
  3. tile the 1.50 h window exactly.
Choose the largest interval satisfying all three rules.

Absolute bioavailability requires a dose-normalized systemic exposure
reference from intravenous dosing or another validated reference route.
An oral concentration-time profile alone does not identify absolute F.