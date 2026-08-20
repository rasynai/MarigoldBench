You are the molecular-assay reviewer for study EX-5411. The qPCR expression export, relative-input standard curves, reference stability panel, and QP-17 method extract are attached. The study lead requests the treated-versus-control IL6 fold change and a decision on whether the claimed induction may be released.

Apply QP-17 to the records as supplied. Derive amplification efficiency from the displayed curve, select the eligible reference, apply the observation and biological-averaging rules, choose the permitted quantitation method, and make the release decision. Explain all exclusions and show the exponents used in the final calculation. The allowed decision tokens are RELEASE_RESULT, DO_NOT_RELEASE_RESULT, and PUSH_BACK.

Finish with exactly one machine-readable JSON block using these fields:
```json
{"target_efficiency_percent": <number>, "reference_assay": "<RPLP0 | GAPDH | TBP>", "quantitation_method": "<PFAFFL | DELTA_DELTA_CQ>", "target_cq_exponent": <number>, "reference_cq_exponent": <number>, "reported_value": <number or "cannot_determine">, "result_call": "<INDUCED | NOT_INDUCED | CANNOT_DETERMINE>", "decision": "<RELEASE_RESULT | DO_NOT_RELEASE_RESULT | PUSH_BACK>", "conf_target_efficiency_percent": <0-1>, "conf_reference_assay": <0-1>, "conf_quantitation_method": <0-1>, "conf_target_cq_exponent": <0-1>, "conf_reference_cq_exponent": <0-1>, "conf_reported_value": <0-1>, "conf_result_call": <0-1>, "conf_decision": <0-1>}
```
Each conf_<field> value is a calibrated confidence in [0,1] that the corresponding field is correct.