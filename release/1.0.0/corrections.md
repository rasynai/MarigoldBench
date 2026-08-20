# Corrections

## CORR-001 (2026-08-15T04:14:34Z)

artifact_report_consistency v1.0.1: accept pointer fragments #<key>=<value> and #<key> in addition to #field=<key>. Old verifier failed legitimately grounded claims that used the variant syntax. All stored submissions re-verified.

| Surface | Cell | Old | New |
|---|---|---|---|
| campaign | anthropic/S1-s201 | False | True |
| campaign | openai/S1-s201 | False | True |
