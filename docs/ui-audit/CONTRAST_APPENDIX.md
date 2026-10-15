# Complete source contrast appendix

WCAG sRGB relative luminance, source token values, alpha compositing; 101 points per gradient segment; saturate matrix on flat canvas backdrop for glass; no pixel sampling

Every row is source-computed. Candidate pairings may never occur in the DOM. Source declarations and limitations are retained in contrast-data.json. Token candidates include fallback variables discovered inside color declarations; canvas-mid is also used as the tooltip foreground (components.css:379), despite its name.

| Theme | Accent | Foreground candidate | Surface | Min ratio | Max ratio | Worst background | Best background | AA normal | Pairing scope |
|---|---|---|---|---:|---:|---|---|---|---|
| light | all | canvas-mid | canvas | 1.000 | 1.126 | #E6E5EE | #D3DAE5 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass | 1.096 | 1.146 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong | 1.148 | 1.181 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid | 1.210 | 1.223 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/hover | 1.085 | 1.220 | #DDDCE6 | #CBD2DD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/press | 1.159 | 1.300 | #D6D6DF | #C5CBD7 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/track | 1.137 | 1.276 | #D8D7E1 | #C6CDD9 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/field | 1.059 | 1.120 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/field-hover | 1.133 | 1.171 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/field-focus | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/chip | 1.133 | 1.171 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/nav-selected | 1.218 | 1.228 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/secondary-button | 1.202 | 1.218 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/secondary-hover | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/secondary-active | 1.137 | 1.137 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/file-button | 1.202 | 1.218 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/segment-selected | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/kbd | 1.127 | 1.249 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-critical | 1.265 | 1.416 | #DBC9D1 | #CBBFC9 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-high | 1.188 | 1.326 | #E4CFD1 | #D4C6C9 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-medium | 1.083 | 1.203 | #E7DBD3 | #D7D2CC | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-low | 1.137 | 1.264 | #CEDBDC | #BED1D4 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-compliant | 1.152 | 1.281 | #CCDADB | #BCD0D3 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-partial | 1.083 | 1.203 | #E7DBD3 | #D7D2CC | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-noncompliant | 1.213 | 1.355 | #E1CDD3 | #D0C3CB | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/tint-insufficient | 1.093 | 1.214 | #DBDCE6 | #CBD2DE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | canvas/mark | 1.185 | 1.296 | #E9D0B5 | #DCC9AF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/hover | 1.008 | 1.053 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/press | 1.015 | 1.060 | #E4E4EA | #DCE0E7 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/track | 1.000 | 1.040 | #E5E5EC | #DEE2E9 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/field | 1.171 | 1.197 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/field-hover | 1.202 | 1.218 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/field-focus | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/chip | 1.202 | 1.218 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/nav-selected | 1.237 | 1.241 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/secondary-button | 1.230 | 1.237 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/secondary-hover | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/secondary-active | 1.137 | 1.137 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/file-button | 1.230 | 1.237 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/segment-selected | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/kbd | 1.127 | 1.249 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-critical | 1.113 | 1.162 | #E8D6DA | #E1D3D8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-high | 1.048 | 1.093 | #F1DCDB | #EAD9D8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-medium | 1.002 | 1.042 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-low | 1.005 | 1.046 | #DBE8E6 | #D4E5E3 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-compliant | 1.018 | 1.059 | #D9E7E5 | #D2E3E2 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-partial | 1.002 | 1.042 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-noncompliant | 1.070 | 1.115 | #EEDADD | #E6D7DA | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/tint-insufficient | 1.000 | 1.033 | #E2E6EE | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass/mark | 1.070 | 1.107 | #F4DBBD | #EDD8BB | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/hover | 1.056 | 1.086 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/press | 1.000 | 1.015 | #E4E6EB | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/track | 1.006 | 1.035 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/field | 1.198 | 1.215 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/field-hover | 1.219 | 1.229 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/field-focus | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/chip | 1.219 | 1.229 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/nav-selected | 1.241 | 1.244 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/secondary-button | 1.237 | 1.241 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/secondary-hover | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/secondary-active | 1.137 | 1.137 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/file-button | 1.237 | 1.241 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/segment-selected | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/kbd | 1.127 | 1.249 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-critical | 1.081 | 1.111 | #EBD9DC | #E7D7DA | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-high | 1.019 | 1.046 | #F4DFDC | #EFDDDB | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-medium | 1.044 | 1.071 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-low | 1.000 | 1.023 | #DAE9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-compliant | 1.000 | 1.015 | #DEE8E4 | #D7E8E5 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-partial | 1.044 | 1.071 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-noncompliant | 1.040 | 1.068 | #F1DDDE | #ECDBDD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/tint-insufficient | 1.035 | 1.062 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | glass-strong/mark | 1.045 | 1.068 | #F6DEBE | #F2DCBD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/hover | 1.112 | 1.124 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/press | 1.039 | 1.050 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/track | 1.059 | 1.071 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/field | 1.230 | 1.236 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/field-hover | 1.238 | 1.241 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/field-focus | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/chip | 1.238 | 1.241 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/nav-selected | 1.246 | 1.247 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/secondary-button | 1.245 | 1.246 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/secondary-hover | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/secondary-active | 1.137 | 1.137 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/file-button | 1.245 | 1.246 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/segment-selected | 1.249 | 1.249 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/kbd | 1.127 | 1.249 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-critical | 1.047 | 1.058 | #EFDDDE | #EDDCDD | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-high | 1.003 | 1.013 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-medium | 1.095 | 1.105 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-low | 1.046 | 1.056 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-compliant | 1.033 | 1.043 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-partial | 1.095 | 1.105 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-noncompliant | 1.007 | 1.017 | #F4E1E0 | #F2E0DF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/tint-insufficient | 1.085 | 1.095 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | solid/mark | 1.018 | 1.026 | #F9E1C0 | #F7E0BF | Fail candidate | conservative candidate pairing |
| light | all | canvas-mid | modal-over-scrim | 1.147 | 1.155 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas | 2.691 | 3.029 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass | 3.319 | 3.470 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong | 3.478 | 3.578 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid | 3.665 | 3.704 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/hover | 2.484 | 2.791 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/press | 2.330 | 2.614 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/track | 2.373 | 2.664 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/field | 3.208 | 3.394 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/field-hover | 3.432 | 3.547 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/field-focus | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/chip | 3.432 | 3.547 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/nav-selected | 3.688 | 3.720 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/secondary-button | 3.641 | 3.688 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/secondary-hover | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/secondary-active | 3.443 | 3.443 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/file-button | 3.641 | 3.688 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/segment-selected | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/kbd | 3.413 | 3.785 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-critical | 2.140 | 2.394 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-high | 2.285 | 2.550 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-medium | 2.517 | 2.798 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-low | 2.397 | 2.664 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-compliant | 2.365 | 2.630 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-partial | 2.517 | 2.798 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-noncompliant | 2.235 | 2.497 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/tint-insufficient | 2.495 | 2.771 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | compliant | canvas/mark | 2.337 | 2.556 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/hover | 3.054 | 3.191 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/press | 2.857 | 2.984 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/track | 2.913 | 3.042 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/field | 3.547 | 3.625 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/field-hover | 3.641 | 3.688 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/field-focus | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/chip | 3.641 | 3.688 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/nav-selected | 3.746 | 3.759 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/secondary-button | 3.727 | 3.746 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/secondary-hover | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/secondary-active | 3.443 | 3.443 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/file-button | 3.727 | 3.746 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/segment-selected | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/kbd | 3.413 | 3.785 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-critical | 2.608 | 2.721 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-high | 2.772 | 2.890 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-medium | 3.034 | 3.157 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-low | 2.896 | 3.013 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-compliant | 2.860 | 2.976 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-partial | 3.034 | 3.157 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-noncompliant | 2.715 | 2.832 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/tint-insufficient | 3.007 | 3.129 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass/mark | 2.736 | 2.831 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/hover | 3.198 | 3.289 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/press | 2.990 | 3.074 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/track | 3.049 | 3.135 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/field | 3.629 | 3.681 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/field-hover | 3.691 | 3.722 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/field-focus | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/chip | 3.691 | 3.722 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/nav-selected | 3.760 | 3.768 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/secondary-button | 3.747 | 3.760 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/secondary-hover | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/secondary-active | 3.443 | 3.443 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/file-button | 3.747 | 3.760 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/segment-selected | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/kbd | 3.413 | 3.785 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-critical | 2.725 | 2.801 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-high | 2.894 | 2.973 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-medium | 3.163 | 3.245 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-low | 3.021 | 3.099 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-compliant | 2.983 | 3.061 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-partial | 3.163 | 3.245 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-noncompliant | 2.836 | 2.914 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/tint-insufficient | 3.135 | 3.216 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | compliant | glass-strong/mark | 2.835 | 2.898 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/hover | 3.367 | 3.403 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/press | 3.147 | 3.180 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/track | 3.209 | 3.243 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/field | 3.724 | 3.744 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/field-hover | 3.748 | 3.760 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/field-focus | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/chip | 3.748 | 3.760 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/nav-selected | 3.775 | 3.778 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/secondary-button | 3.770 | 3.775 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/secondary-hover | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/secondary-active | 3.443 | 3.443 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/file-button | 3.770 | 3.775 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/segment-selected | 3.785 | 3.785 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/kbd | 3.413 | 3.785 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-critical | 2.864 | 2.894 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-high | 3.039 | 3.070 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-medium | 3.315 | 3.348 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-low | 3.167 | 3.198 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-compliant | 3.129 | 3.160 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-partial | 3.315 | 3.348 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-noncompliant | 2.979 | 3.009 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/tint-insufficient | 3.285 | 3.317 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | compliant | solid/mark | 2.951 | 2.976 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | compliant | modal-over-scrim | 3.473 | 3.499 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | critical | canvas | 5.794 | 6.523 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | all | critical | glass | 7.148 | 7.472 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | critical | glass-strong | 7.489 | 7.706 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | critical | solid | 7.892 | 7.977 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | critical | canvas/hover | 5.349 | 6.010 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | all | critical | canvas/press | 5.018 | 5.629 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | all | critical | canvas/track | 5.111 | 5.736 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | all | critical | canvas/field | 6.909 | 7.308 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | critical | canvas/field-hover | 7.390 | 7.638 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | critical | canvas/field-focus | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | canvas/chip | 7.390 | 7.638 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | critical | canvas/nav-selected | 7.943 | 8.012 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | critical | canvas/secondary-button | 7.841 | 7.943 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | critical | canvas/secondary-hover | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | canvas/secondary-active | 7.416 | 7.416 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | critical | canvas/file-button | 7.841 | 7.943 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | critical | canvas/segment-selected | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | canvas/kbd | 7.350 | 8.150 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-critical | 4.608 | 5.156 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-high | 4.920 | 5.492 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-medium | 5.421 | 6.025 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-low | 5.162 | 5.738 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-compliant | 5.094 | 5.664 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-partial | 5.421 | 6.025 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-noncompliant | 4.813 | 5.377 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | all | critical | canvas/tint-insufficient | 5.374 | 5.968 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | all | critical | canvas/mark | 5.033 | 5.505 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | all | critical | glass/hover | 6.577 | 6.871 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | all | critical | glass/press | 6.153 | 6.425 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | all | critical | glass/track | 6.273 | 6.551 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | all | critical | glass/field | 7.639 | 7.807 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | critical | glass/field-hover | 7.841 | 7.943 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | critical | glass/field-focus | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass/chip | 7.841 | 7.943 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | critical | glass/nav-selected | 8.067 | 8.095 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | glass/secondary-button | 8.026 | 8.067 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | critical | glass/secondary-hover | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass/secondary-active | 7.416 | 7.416 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | critical | glass/file-button | 8.026 | 8.067 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | critical | glass/segment-selected | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass/kbd | 7.350 | 8.150 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-critical | 5.615 | 5.859 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-high | 5.969 | 6.223 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-medium | 6.533 | 6.800 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-low | 6.236 | 6.489 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-compliant | 6.158 | 6.410 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-partial | 6.533 | 6.800 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-noncompliant | 5.848 | 6.098 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | all | critical | glass/tint-insufficient | 6.476 | 6.738 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | all | critical | glass/mark | 5.891 | 6.097 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/hover | 6.887 | 7.083 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/press | 6.439 | 6.620 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/track | 6.565 | 6.751 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/field | 7.815 | 7.926 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/field-hover | 7.948 | 8.015 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/field-focus | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/chip | 7.948 | 8.015 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/nav-selected | 8.096 | 8.114 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/secondary-button | 8.069 | 8.096 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/secondary-hover | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/secondary-active | 7.416 | 7.416 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/file-button | 8.069 | 8.096 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/segment-selected | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/kbd | 7.350 | 8.150 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-critical | 5.869 | 6.032 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-high | 6.233 | 6.402 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-medium | 6.812 | 6.989 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-low | 6.505 | 6.673 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-compliant | 6.425 | 6.592 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-partial | 6.812 | 6.989 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-noncompliant | 6.108 | 6.275 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/tint-insufficient | 6.751 | 6.925 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | critical | glass-strong/mark | 6.105 | 6.241 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | all | critical | solid/hover | 7.252 | 7.329 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | critical | solid/press | 6.777 | 6.848 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | critical | solid/track | 6.910 | 6.983 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | critical | solid/field | 8.020 | 8.064 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | critical | solid/field-hover | 8.072 | 8.098 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | solid/field-focus | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/chip | 8.072 | 8.098 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | critical | solid/nav-selected | 8.129 | 8.136 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/secondary-button | 8.119 | 8.129 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/secondary-hover | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/secondary-active | 7.416 | 7.416 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | critical | solid/file-button | 8.119 | 8.129 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/segment-selected | 8.150 | 8.150 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/kbd | 7.350 | 8.150 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-critical | 6.168 | 6.232 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-high | 6.544 | 6.611 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-medium | 7.140 | 7.209 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-low | 6.821 | 6.887 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-compliant | 6.738 | 6.804 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-partial | 7.140 | 7.209 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-noncompliant | 6.415 | 6.480 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | all | critical | solid/tint-insufficient | 7.075 | 7.144 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | critical | solid/mark | 6.355 | 6.409 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | all | critical | modal-over-scrim | 7.479 | 7.536 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | all | danger-text | canvas | 4.674 | 5.262 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | all | danger-text | glass | 5.766 | 6.028 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong | 6.041 | 6.216 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | danger-text | solid | 6.366 | 6.435 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/hover | 4.314 | 4.848 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/press | 4.047 | 4.541 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/track | 4.123 | 4.627 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/field | 5.573 | 5.895 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/field-hover | 5.961 | 6.161 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/field-focus | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/chip | 5.961 | 6.161 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/nav-selected | 6.407 | 6.463 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/secondary-button | 6.325 | 6.407 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/secondary-hover | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/secondary-active | 5.982 | 5.982 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/file-button | 6.325 | 6.407 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/segment-selected | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/kbd | 5.929 | 6.574 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | canvas/tint-critical | 3.717 | 4.159 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-high | 3.969 | 4.430 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-medium | 4.372 | 4.860 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-low | 4.164 | 4.628 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-compliant | 4.109 | 4.569 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-partial | 4.372 | 4.860 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-noncompliant | 3.882 | 4.337 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/tint-insufficient | 4.335 | 4.814 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | canvas/mark | 4.060 | 4.440 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | danger-text | glass/hover | 5.305 | 5.543 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | all | danger-text | glass/press | 4.963 | 5.183 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | all | danger-text | glass/track | 5.060 | 5.284 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | all | danger-text | glass/field | 6.162 | 6.297 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | danger-text | glass/field-hover | 6.325 | 6.407 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | danger-text | glass/field-focus | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass/chip | 6.325 | 6.407 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | danger-text | glass/nav-selected | 6.507 | 6.529 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass/secondary-button | 6.474 | 6.507 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | danger-text | glass/secondary-hover | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass/secondary-active | 5.982 | 5.982 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | danger-text | glass/file-button | 6.474 | 6.507 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | danger-text | glass/segment-selected | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass/kbd | 5.929 | 6.574 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-critical | 4.530 | 4.726 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-high | 4.815 | 5.020 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-medium | 5.270 | 5.485 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-low | 5.030 | 5.235 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-compliant | 4.968 | 5.170 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-partial | 5.270 | 5.485 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-noncompliant | 4.717 | 4.919 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | all | danger-text | glass/tint-insufficient | 5.223 | 5.435 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | all | danger-text | glass/mark | 4.752 | 4.918 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/hover | 5.555 | 5.713 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/press | 5.194 | 5.340 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/track | 5.296 | 5.445 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/field | 6.304 | 6.393 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/field-hover | 6.411 | 6.465 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/field-focus | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/chip | 6.411 | 6.465 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/nav-selected | 6.531 | 6.545 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/secondary-button | 6.509 | 6.531 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/secondary-hover | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/secondary-active | 5.982 | 5.982 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/file-button | 6.509 | 6.531 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/segment-selected | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/kbd | 5.929 | 6.574 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-critical | 4.734 | 4.865 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-high | 5.028 | 5.164 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-medium | 5.495 | 5.638 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-low | 5.247 | 5.383 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-compliant | 5.183 | 5.317 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-partial | 5.495 | 5.638 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-noncompliant | 4.927 | 5.061 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/tint-insufficient | 5.446 | 5.586 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | danger-text | glass-strong/mark | 4.924 | 5.034 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | all | danger-text | solid/hover | 5.849 | 5.912 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/press | 5.466 | 5.524 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | danger-text | solid/track | 5.574 | 5.633 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/field | 6.470 | 6.504 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | danger-text | solid/field-hover | 6.511 | 6.532 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/field-focus | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/chip | 6.511 | 6.532 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/nav-selected | 6.557 | 6.563 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/secondary-button | 6.549 | 6.557 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/secondary-hover | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/secondary-active | 5.982 | 5.982 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/file-button | 6.549 | 6.557 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/segment-selected | 6.574 | 6.574 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/kbd | 5.929 | 6.574 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-critical | 4.975 | 5.027 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-high | 5.278 | 5.332 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-medium | 5.759 | 5.815 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-low | 5.502 | 5.555 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-compliant | 5.435 | 5.489 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-partial | 5.759 | 5.815 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-noncompliant | 5.174 | 5.227 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/tint-insufficient | 5.707 | 5.762 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | danger-text | solid/mark | 5.126 | 5.169 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | all | danger-text | modal-over-scrim | 6.033 | 6.078 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | all | high | canvas | 3.049 | 3.433 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | high | glass | 3.762 | 3.932 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong | 3.941 | 4.055 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | high | solid | 4.153 | 4.198 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/hover | 2.815 | 3.163 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/press | 2.641 | 2.962 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/track | 2.690 | 3.019 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/field | 3.636 | 3.846 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/field-hover | 3.889 | 4.020 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/field-focus | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/chip | 3.889 | 4.020 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/nav-selected | 4.180 | 4.216 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/secondary-button | 4.126 | 4.180 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/secondary-hover | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/secondary-active | 3.902 | 3.902 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/file-button | 4.126 | 4.180 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/segment-selected | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/kbd | 3.868 | 4.289 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-critical | 2.425 | 2.714 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-high | 2.589 | 2.890 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-medium | 2.853 | 3.171 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-low | 2.717 | 3.020 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-compliant | 2.681 | 2.981 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-partial | 2.853 | 3.171 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-noncompliant | 2.533 | 2.830 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/tint-insufficient | 2.828 | 3.141 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | high | canvas/mark | 2.649 | 2.897 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/hover | 3.461 | 3.616 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/press | 3.238 | 3.381 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | high | glass/track | 3.301 | 3.447 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | high | glass/field | 4.020 | 4.108 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | high | glass/field-hover | 4.126 | 4.180 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | high | glass/field-focus | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass/chip | 4.126 | 4.180 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | high | glass/nav-selected | 4.245 | 4.260 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass/secondary-button | 4.224 | 4.245 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | high | glass/secondary-hover | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass/secondary-active | 3.902 | 3.902 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/file-button | 4.224 | 4.245 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | high | glass/segment-selected | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass/kbd | 3.868 | 4.289 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-critical | 2.955 | 3.084 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-high | 3.141 | 3.275 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-medium | 3.438 | 3.578 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-low | 3.282 | 3.415 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-compliant | 3.241 | 3.373 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-partial | 3.438 | 3.578 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-noncompliant | 3.077 | 3.209 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | high | glass/tint-insufficient | 3.408 | 3.546 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | high | glass/mark | 3.100 | 3.209 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/hover | 3.624 | 3.727 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/press | 3.389 | 3.484 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/track | 3.455 | 3.553 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/field | 4.113 | 4.171 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/field-hover | 4.183 | 4.218 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/field-focus | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/chip | 4.183 | 4.218 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/nav-selected | 4.261 | 4.270 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/secondary-button | 4.246 | 4.261 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/secondary-hover | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/secondary-active | 3.902 | 3.902 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/file-button | 4.246 | 4.261 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/segment-selected | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/kbd | 3.868 | 4.289 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-critical | 3.089 | 3.174 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-high | 3.280 | 3.369 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-medium | 3.585 | 3.678 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-low | 3.423 | 3.512 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-compliant | 3.381 | 3.469 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-partial | 3.585 | 3.678 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-noncompliant | 3.214 | 3.302 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/tint-insufficient | 3.553 | 3.645 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | high | glass-strong/mark | 3.213 | 3.285 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | high | solid/hover | 3.816 | 3.857 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/press | 3.566 | 3.604 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | high | solid/track | 3.637 | 3.675 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/field | 4.221 | 4.244 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | high | solid/field-hover | 4.248 | 4.262 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/field-focus | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/chip | 4.248 | 4.262 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/nav-selected | 4.278 | 4.282 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/secondary-button | 4.273 | 4.278 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/secondary-hover | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/secondary-active | 3.902 | 3.902 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/file-button | 4.273 | 4.278 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/segment-selected | 4.289 | 4.289 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/kbd | 3.868 | 4.289 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-critical | 3.246 | 3.280 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-high | 3.444 | 3.479 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-medium | 3.757 | 3.794 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-low | 3.589 | 3.624 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-compliant | 3.546 | 3.581 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-partial | 3.757 | 3.794 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-noncompliant | 3.376 | 3.410 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/tint-insufficient | 3.723 | 3.760 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | high | solid/mark | 3.344 | 3.373 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | high | modal-over-scrim | 3.936 | 3.966 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas | 1.803 | 2.030 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass | 2.224 | 2.325 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong | 2.331 | 2.398 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid | 2.456 | 2.482 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/hover | 1.664 | 1.870 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/press | 1.561 | 1.752 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/track | 1.590 | 1.785 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/field | 2.150 | 2.274 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/field-hover | 2.300 | 2.377 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/field-focus | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/chip | 2.300 | 2.377 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/nav-selected | 2.472 | 2.493 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/secondary-button | 2.440 | 2.472 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/secondary-hover | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/secondary-active | 2.308 | 2.308 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/file-button | 2.440 | 2.472 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/segment-selected | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/kbd | 2.287 | 2.536 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-critical | 1.434 | 1.605 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-high | 1.531 | 1.709 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-medium | 1.687 | 1.875 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-low | 1.606 | 1.786 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-compliant | 1.585 | 1.763 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-partial | 1.687 | 1.875 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-noncompliant | 1.498 | 1.673 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/tint-insufficient | 1.672 | 1.857 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | canvas/mark | 1.566 | 1.713 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/hover | 2.047 | 2.138 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/press | 1.915 | 1.999 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/track | 1.952 | 2.038 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/field | 2.377 | 2.429 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/field-hover | 2.440 | 2.472 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/field-focus | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/chip | 2.440 | 2.472 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/nav-selected | 2.510 | 2.519 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/secondary-button | 2.497 | 2.510 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/secondary-hover | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/secondary-active | 2.308 | 2.308 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/file-button | 2.497 | 2.510 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/segment-selected | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/kbd | 2.287 | 2.536 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-critical | 1.747 | 1.823 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-high | 1.857 | 1.937 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-medium | 2.033 | 2.116 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-low | 1.941 | 2.019 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-compliant | 1.916 | 1.995 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-partial | 2.033 | 2.116 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-noncompliant | 1.820 | 1.898 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/tint-insufficient | 2.015 | 2.097 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass/mark | 1.833 | 1.897 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/hover | 2.143 | 2.204 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/press | 2.004 | 2.060 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/track | 2.043 | 2.101 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/field | 2.432 | 2.466 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/field-hover | 2.473 | 2.494 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/field-focus | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/chip | 2.473 | 2.494 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/nav-selected | 2.519 | 2.525 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/secondary-button | 2.511 | 2.519 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/secondary-hover | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/secondary-active | 2.308 | 2.308 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/file-button | 2.511 | 2.519 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/segment-selected | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/kbd | 2.287 | 2.536 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-critical | 1.826 | 1.877 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-high | 1.940 | 1.992 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-medium | 2.120 | 2.175 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-low | 2.024 | 2.077 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-compliant | 1.999 | 2.051 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-partial | 2.120 | 2.175 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-noncompliant | 1.901 | 1.953 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/tint-insufficient | 2.101 | 2.155 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | glass-strong/mark | 1.900 | 1.942 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/hover | 2.257 | 2.281 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/press | 2.109 | 2.131 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/track | 2.150 | 2.173 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/field | 2.496 | 2.509 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/field-hover | 2.512 | 2.520 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/field-focus | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/chip | 2.512 | 2.520 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/nav-selected | 2.530 | 2.532 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/secondary-button | 2.526 | 2.530 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/secondary-hover | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/secondary-active | 2.308 | 2.308 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/file-button | 2.526 | 2.530 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/segment-selected | 2.536 | 2.536 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/kbd | 2.287 | 2.536 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-critical | 1.919 | 1.939 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-high | 2.036 | 2.057 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-medium | 2.222 | 2.243 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-low | 2.122 | 2.143 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-compliant | 2.097 | 2.117 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-partial | 2.222 | 2.243 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-noncompliant | 1.996 | 2.017 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/tint-insufficient | 2.202 | 2.223 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | solid/mark | 1.978 | 1.994 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | insufficient | modal-over-scrim | 2.327 | 2.345 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas | 2.397 | 2.699 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | low | glass | 2.958 | 3.092 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong | 3.099 | 3.188 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | low | solid | 3.265 | 3.301 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/hover | 2.213 | 2.487 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/press | 2.076 | 2.329 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/track | 2.115 | 2.373 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/field | 2.859 | 3.024 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/field-hover | 3.058 | 3.160 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/field-focus | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/chip | 3.058 | 3.160 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/nav-selected | 3.287 | 3.315 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/secondary-button | 3.244 | 3.287 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/secondary-hover | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/secondary-active | 3.068 | 3.068 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/file-button | 3.244 | 3.287 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/segment-selected | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/kbd | 3.041 | 3.372 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-critical | 1.907 | 2.134 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-high | 2.036 | 2.272 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-medium | 2.243 | 2.493 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-low | 2.136 | 2.374 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-compliant | 2.108 | 2.344 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-partial | 2.243 | 2.493 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-noncompliant | 1.991 | 2.225 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/tint-insufficient | 2.223 | 2.470 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | low | canvas/mark | 2.082 | 2.278 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/hover | 2.721 | 2.843 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/press | 2.546 | 2.658 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | low | glass/track | 2.595 | 2.710 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | low | glass/field | 3.161 | 3.230 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | low | glass/field-hover | 3.244 | 3.287 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | low | glass/field-focus | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass/chip | 3.244 | 3.287 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | low | glass/nav-selected | 3.338 | 3.349 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass/secondary-button | 3.321 | 3.338 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | low | glass/secondary-hover | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass/secondary-active | 3.068 | 3.068 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/file-button | 3.321 | 3.338 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | low | glass/segment-selected | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass/kbd | 3.041 | 3.372 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-critical | 2.323 | 2.424 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-high | 2.470 | 2.575 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-medium | 2.703 | 2.813 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-low | 2.580 | 2.685 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-compliant | 2.548 | 2.652 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-partial | 2.703 | 2.813 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-noncompliant | 2.420 | 2.523 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | low | glass/tint-insufficient | 2.679 | 2.788 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | low | glass/mark | 2.438 | 2.523 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/hover | 2.849 | 2.931 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/press | 2.664 | 2.739 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/track | 2.716 | 2.793 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/field | 3.234 | 3.279 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/field-hover | 3.289 | 3.316 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/field-focus | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/chip | 3.289 | 3.316 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/nav-selected | 3.350 | 3.357 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/secondary-button | 3.339 | 3.350 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/secondary-hover | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/secondary-active | 3.068 | 3.068 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/file-button | 3.339 | 3.350 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/segment-selected | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/kbd | 3.041 | 3.372 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-critical | 2.428 | 2.496 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-high | 2.579 | 2.649 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-medium | 2.818 | 2.892 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-low | 2.691 | 2.761 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-compliant | 2.658 | 2.728 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-partial | 2.818 | 2.892 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-noncompliant | 2.527 | 2.596 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/tint-insufficient | 2.793 | 2.865 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | low | glass-strong/mark | 2.526 | 2.582 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | low | solid/hover | 3.000 | 3.032 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/press | 2.804 | 2.833 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | low | solid/track | 2.859 | 2.889 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/field | 3.319 | 3.336 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | low | solid/field-hover | 3.340 | 3.351 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/field-focus | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/chip | 3.340 | 3.351 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/nav-selected | 3.364 | 3.367 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/secondary-button | 3.359 | 3.364 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/secondary-hover | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/secondary-active | 3.068 | 3.068 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/file-button | 3.359 | 3.364 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/segment-selected | 3.372 | 3.372 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/kbd | 3.041 | 3.372 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-critical | 2.552 | 2.579 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-high | 2.708 | 2.735 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-medium | 2.954 | 2.983 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-low | 2.822 | 2.850 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-compliant | 2.788 | 2.815 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-partial | 2.954 | 2.983 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-noncompliant | 2.654 | 2.681 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/tint-insufficient | 2.927 | 2.956 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | low | solid/mark | 2.629 | 2.652 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | low | modal-over-scrim | 3.095 | 3.118 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas | 1.527 | 1.719 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass | 1.884 | 1.969 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong | 1.974 | 2.031 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | medium | solid | 2.080 | 2.103 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/hover | 1.410 | 1.584 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/press | 1.322 | 1.484 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/track | 1.347 | 1.512 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/field | 1.821 | 1.926 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/field-hover | 1.948 | 2.013 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/chip | 1.948 | 2.013 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/nav-selected | 2.094 | 2.112 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/secondary-button | 2.067 | 2.093 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/file-button | 2.067 | 2.093 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-critical | 1.215 | 1.359 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-high | 1.297 | 1.448 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-medium | 1.429 | 1.588 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-low | 1.361 | 1.512 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-compliant | 1.342 | 1.493 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-partial | 1.429 | 1.588 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-noncompliant | 1.269 | 1.417 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/tint-insufficient | 1.416 | 1.573 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | medium | canvas/mark | 1.326 | 1.451 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/hover | 1.733 | 1.811 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/press | 1.622 | 1.693 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/track | 1.653 | 1.727 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/field | 2.013 | 2.058 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/field-hover | 2.067 | 2.093 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/chip | 2.067 | 2.093 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/nav-selected | 2.126 | 2.133 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/secondary-button | 2.115 | 2.126 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/file-button | 2.115 | 2.126 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-critical | 1.480 | 1.544 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-high | 1.573 | 1.640 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-medium | 1.722 | 1.792 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-low | 1.644 | 1.710 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-compliant | 1.623 | 1.689 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-partial | 1.722 | 1.792 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-noncompliant | 1.541 | 1.607 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/tint-insufficient | 1.707 | 1.776 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass/mark | 1.553 | 1.607 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/hover | 1.815 | 1.867 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/press | 1.697 | 1.745 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/track | 1.730 | 1.779 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/field | 2.060 | 2.089 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/field-hover | 2.095 | 2.113 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/chip | 2.095 | 2.113 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/nav-selected | 2.134 | 2.139 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/secondary-button | 2.127 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/file-button | 2.127 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-critical | 1.547 | 1.590 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-high | 1.643 | 1.687 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-medium | 1.795 | 1.842 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-low | 1.714 | 1.759 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-compliant | 1.693 | 1.737 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-partial | 1.795 | 1.842 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-noncompliant | 1.610 | 1.654 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/tint-insufficient | 1.779 | 1.825 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | medium | glass-strong/mark | 1.609 | 1.645 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/hover | 1.911 | 1.932 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/press | 1.786 | 1.805 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/track | 1.821 | 1.841 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/field | 2.114 | 2.125 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/field-hover | 2.128 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/chip | 2.128 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/nav-selected | 2.143 | 2.144 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/secondary-button | 2.140 | 2.143 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/file-button | 2.140 | 2.143 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-critical | 1.626 | 1.643 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-high | 1.725 | 1.742 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-medium | 1.882 | 1.900 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-low | 1.798 | 1.815 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-compliant | 1.776 | 1.793 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-partial | 1.882 | 1.900 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-noncompliant | 1.691 | 1.708 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/tint-insufficient | 1.865 | 1.883 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | medium | solid/mark | 1.675 | 1.689 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | medium | modal-over-scrim | 1.971 | 1.986 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas | 4.720 | 5.314 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | all | muted | glass | 5.823 | 6.087 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | muted | glass-strong | 6.101 | 6.277 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | muted | solid | 6.429 | 6.498 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | muted | canvas/hover | 4.357 | 4.896 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/press | 4.087 | 4.585 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/track | 4.163 | 4.673 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/field | 5.629 | 5.954 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | muted | canvas/field-hover | 6.020 | 6.222 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | muted | canvas/field-focus | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | canvas/chip | 6.020 | 6.222 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | muted | canvas/nav-selected | 6.471 | 6.527 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | muted | canvas/secondary-button | 6.387 | 6.471 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | muted | canvas/secondary-hover | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | canvas/secondary-active | 6.041 | 6.041 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | muted | canvas/file-button | 6.387 | 6.471 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | muted | canvas/segment-selected | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | canvas/kbd | 5.988 | 6.639 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | canvas/tint-critical | 3.754 | 4.200 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-high | 4.008 | 4.474 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-medium | 4.416 | 4.908 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-low | 4.205 | 4.674 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-compliant | 4.149 | 4.614 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-partial | 4.416 | 4.908 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-noncompliant | 3.921 | 4.380 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/tint-insufficient | 4.378 | 4.862 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | muted | canvas/mark | 4.100 | 4.484 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | muted | glass/hover | 5.358 | 5.597 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | all | muted | glass/press | 5.013 | 5.234 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | all | muted | glass/track | 5.110 | 5.336 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | all | muted | glass/field | 6.223 | 6.360 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | muted | glass/field-hover | 6.387 | 6.471 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | muted | glass/field-focus | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass/chip | 6.387 | 6.471 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | muted | glass/nav-selected | 6.572 | 6.594 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | glass/secondary-button | 6.538 | 6.572 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | muted | glass/secondary-hover | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass/secondary-active | 6.041 | 6.041 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | muted | glass/file-button | 6.538 | 6.572 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | muted | glass/segment-selected | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass/kbd | 5.988 | 6.639 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-critical | 4.574 | 4.773 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-high | 4.863 | 5.070 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-medium | 5.322 | 5.539 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-low | 5.080 | 5.286 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-compliant | 5.017 | 5.221 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-partial | 5.322 | 5.539 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-noncompliant | 4.764 | 4.968 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | all | muted | glass/tint-insufficient | 5.275 | 5.488 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | all | muted | glass/mark | 4.799 | 4.967 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/hover | 5.610 | 5.770 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/press | 5.246 | 5.393 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/track | 5.348 | 5.499 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/field | 6.367 | 6.457 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/field-hover | 6.475 | 6.529 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/field-focus | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/chip | 6.475 | 6.529 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/nav-selected | 6.595 | 6.610 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/secondary-button | 6.573 | 6.595 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/secondary-hover | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/secondary-active | 6.041 | 6.041 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/file-button | 6.573 | 6.595 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/segment-selected | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/kbd | 5.988 | 6.639 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-critical | 4.781 | 4.913 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-high | 5.078 | 5.215 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-medium | 5.549 | 5.693 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-low | 5.299 | 5.436 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-compliant | 5.234 | 5.370 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-partial | 5.549 | 5.693 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-noncompliant | 4.976 | 5.111 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/tint-insufficient | 5.500 | 5.641 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | muted | glass-strong/mark | 4.973 | 5.084 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | all | muted | solid/hover | 5.907 | 5.970 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | muted | solid/press | 5.520 | 5.579 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | muted | solid/track | 5.629 | 5.689 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | muted | solid/field | 6.534 | 6.569 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | muted | solid/field-hover | 6.576 | 6.597 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | solid/field-focus | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/chip | 6.576 | 6.597 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | muted | solid/nav-selected | 6.622 | 6.628 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/secondary-button | 6.614 | 6.622 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/secondary-hover | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/secondary-active | 6.041 | 6.041 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | muted | solid/file-button | 6.614 | 6.622 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/segment-selected | 6.639 | 6.639 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/kbd | 5.988 | 6.639 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-critical | 5.025 | 5.077 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-high | 5.331 | 5.385 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-medium | 5.816 | 5.873 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-low | 5.556 | 5.610 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-compliant | 5.489 | 5.543 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-partial | 5.816 | 5.873 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-noncompliant | 5.225 | 5.279 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | all | muted | solid/tint-insufficient | 5.764 | 5.820 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | muted | solid/mark | 5.177 | 5.221 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | all | muted | modal-over-scrim | 6.093 | 6.139 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas | 3.866 | 4.353 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass | 4.770 | 4.986 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong | 4.997 | 5.142 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | noncompliant | solid | 5.266 | 5.323 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/hover | 3.569 | 4.010 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/press | 3.348 | 3.756 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/track | 3.410 | 3.828 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/field | 4.610 | 4.877 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/field-hover | 4.931 | 5.097 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/field-focus | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/chip | 4.931 | 5.097 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/nav-selected | 5.300 | 5.346 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/secondary-button | 5.232 | 5.300 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/secondary-hover | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/secondary-active | 4.948 | 4.948 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/file-button | 5.232 | 5.300 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/segment-selected | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/kbd | 4.905 | 5.438 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-critical | 3.075 | 3.441 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-high | 3.283 | 3.665 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-medium | 3.617 | 4.020 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-low | 3.445 | 3.829 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-compliant | 3.399 | 3.779 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-partial | 3.617 | 4.020 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-noncompliant | 3.212 | 3.588 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/tint-insufficient | 3.586 | 3.983 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | canvas/mark | 3.358 | 3.673 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/hover | 4.389 | 4.585 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/press | 4.106 | 4.287 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/track | 4.186 | 4.371 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/field | 5.097 | 5.209 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/field-hover | 5.232 | 5.300 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/field-focus | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/chip | 5.232 | 5.300 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/nav-selected | 5.383 | 5.401 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/secondary-button | 5.355 | 5.383 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/secondary-hover | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/secondary-active | 4.948 | 4.948 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/file-button | 5.355 | 5.383 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/segment-selected | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/kbd | 4.905 | 5.438 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass/tint-critical | 3.747 | 3.910 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-high | 3.983 | 4.153 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-medium | 4.359 | 4.537 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-low | 4.161 | 4.330 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-compliant | 4.109 | 4.277 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-partial | 4.359 | 4.537 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-noncompliant | 3.902 | 4.069 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/tint-insufficient | 4.321 | 4.496 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass/mark | 3.931 | 4.068 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/hover | 4.595 | 4.726 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/press | 4.297 | 4.418 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/track | 4.381 | 4.504 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/field | 5.215 | 5.289 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/field-hover | 5.304 | 5.348 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/field-focus | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/chip | 5.304 | 5.348 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/nav-selected | 5.402 | 5.414 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/secondary-button | 5.384 | 5.402 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/secondary-hover | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/secondary-active | 4.948 | 4.948 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/file-button | 5.384 | 5.402 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/segment-selected | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/kbd | 4.905 | 5.438 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-critical | 3.916 | 4.025 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-high | 4.159 | 4.272 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-medium | 4.545 | 4.664 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-low | 4.340 | 4.453 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-compliant | 4.287 | 4.399 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-partial | 4.545 | 4.664 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-noncompliant | 4.076 | 4.187 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | glass-strong/tint-insufficient | 4.505 | 4.621 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | noncompliant | glass-strong/mark | 4.074 | 4.165 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | solid/hover | 4.839 | 4.890 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/press | 4.522 | 4.569 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/track | 4.611 | 4.660 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/field | 5.352 | 5.381 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/field-hover | 5.386 | 5.404 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/field-focus | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/chip | 5.386 | 5.404 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/nav-selected | 5.424 | 5.429 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/secondary-button | 5.418 | 5.424 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/secondary-hover | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/secondary-active | 4.948 | 4.948 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/file-button | 5.418 | 5.424 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/segment-selected | 5.438 | 5.438 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/kbd | 4.905 | 5.438 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/tint-critical | 4.116 | 4.159 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | solid/tint-high | 4.366 | 4.411 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | solid/tint-medium | 4.764 | 4.811 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/tint-low | 4.551 | 4.596 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/tint-compliant | 4.496 | 4.540 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | solid/tint-partial | 4.764 | 4.811 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/tint-noncompliant | 4.280 | 4.324 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | solid/tint-insufficient | 4.721 | 4.767 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | noncompliant | solid/mark | 4.240 | 4.276 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | noncompliant | modal-over-scrim | 4.991 | 5.028 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | all | partial | canvas | 1.527 | 1.719 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass | 1.884 | 1.969 | #ECF0F6 | #F5F4FA | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong | 1.974 | 2.031 | #F3F5F9 | #F9F8FB | Fail candidate | conservative candidate pairing |
| light | all | partial | solid | 2.080 | 2.103 | #FAFBFD | #FDFCFE | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/hover | 1.410 | 1.584 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/press | 1.322 | 1.484 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/track | 1.347 | 1.512 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/field | 1.821 | 1.926 | #E9ECF2 | #F2F2F6 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/field-hover | 1.948 | 2.013 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/chip | 1.948 | 2.013 | #F2F4F7 | #F8F7FA | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/nav-selected | 2.094 | 2.112 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/secondary-button | 2.067 | 2.093 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/file-button | 2.067 | 2.093 | #FAFBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-critical | 1.215 | 1.359 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-high | 1.297 | 1.448 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-medium | 1.429 | 1.588 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-low | 1.361 | 1.512 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-compliant | 1.342 | 1.493 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-partial | 1.429 | 1.588 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-noncompliant | 1.269 | 1.417 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/tint-insufficient | 1.416 | 1.573 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | all | partial | canvas/mark | 1.326 | 1.451 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/hover | 1.733 | 1.811 | #E3E7EE | #EBEBF1 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/press | 1.622 | 1.693 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/track | 1.653 | 1.727 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/field | 2.013 | 2.058 | #F6F8FB | #FAFAFC | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/field-hover | 2.067 | 2.093 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/chip | 2.067 | 2.093 | #F9FBFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/nav-selected | 2.126 | 2.133 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/secondary-button | 2.115 | 2.126 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/file-button | 2.115 | 2.126 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-critical | 1.480 | 1.544 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-high | 1.573 | 1.640 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-medium | 1.722 | 1.792 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-low | 1.644 | 1.710 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-compliant | 1.623 | 1.689 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-partial | 1.722 | 1.792 | #EDE5DB | #F4E9DD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-noncompliant | 1.541 | 1.607 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/tint-insufficient | 1.707 | 1.776 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass/mark | 1.553 | 1.607 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/hover | 1.815 | 1.867 | #E9ECF1 | #EFEFF3 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/press | 1.697 | 1.745 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/track | 1.730 | 1.779 | #E4E7EC | #E9E9EE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/field | 2.060 | 2.089 | #F9FAFC | #FCFCFD | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/field-hover | 2.095 | 2.113 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/chip | 2.095 | 2.113 | #FBFCFD | #FDFDFE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/nav-selected | 2.134 | 2.139 | #FEFEFF | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/secondary-button | 2.127 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/file-button | 2.127 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-critical | 1.547 | 1.590 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-high | 1.643 | 1.687 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-medium | 1.795 | 1.842 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-low | 1.714 | 1.759 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-compliant | 1.693 | 1.737 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-partial | 1.795 | 1.842 | #F2E9DD | #F7ECDF | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-noncompliant | 1.610 | 1.654 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/tint-insufficient | 1.779 | 1.825 | #E6EAF0 | #EBECF2 | Fail candidate | conservative candidate pairing |
| light | all | partial | glass-strong/mark | 1.609 | 1.645 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/hover | 1.911 | 1.932 | #F0F2F4 | #F2F3F5 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/press | 1.786 | 1.805 | #E9EAED | #EBEBEE | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/track | 1.821 | 1.841 | #EBECEF | #EDEDF0 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/field | 2.114 | 2.125 | #FDFDFE | #FEFEFE | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/field-hover | 2.128 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/field-focus | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/chip | 2.128 | 2.134 | #FEFEFE | #FEFEFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/nav-selected | 2.143 | 2.144 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/secondary-button | 2.140 | 2.143 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/secondary-hover | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/secondary-active | 1.954 | 1.954 | #F3F4F8 | #F3F4F8 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/file-button | 2.140 | 2.143 | #FEFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/segment-selected | 2.148 | 2.148 | #FFFFFF | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/kbd | 1.937 | 2.148 | #F2F3F7 | #FFFFFF | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-critical | 1.626 | 1.643 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-high | 1.725 | 1.742 | #F6E2DE | #F8E3DE | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-medium | 1.882 | 1.900 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-low | 1.798 | 1.815 | #E0EEE8 | #E2EFE9 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-compliant | 1.776 | 1.793 | #DEEDE8 | #E0EEE8 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-partial | 1.882 | 1.900 | #F9EFE0 | #FBEFE1 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-noncompliant | 1.691 | 1.708 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/tint-insufficient | 1.865 | 1.883 | #EDEFF3 | #EFF0F3 | Fail candidate | conservative candidate pairing |
| light | all | partial | solid/mark | 1.675 | 1.689 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | all | partial | modal-over-scrim | 1.971 | 1.986 | #F4F5F7 | #F6F6F7 | Fail candidate | conservative candidate pairing |
| light | all | text | canvas | 12.385 | 13.942 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | all | text | glass | 15.278 | 15.971 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | text | glass-strong | 16.008 | 16.470 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | text | solid | 16.868 | 17.051 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | text | canvas/hover | 11.432 | 12.846 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | all | text | canvas/press | 10.724 | 12.031 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | all | text | canvas/track | 10.924 | 12.261 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | all | text | canvas/field | 14.768 | 15.621 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | text | canvas/field-hover | 15.796 | 16.326 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | text | canvas/field-focus | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | canvas/chip | 15.796 | 16.326 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | text | canvas/nav-selected | 16.978 | 17.124 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text | canvas/secondary-button | 16.759 | 16.977 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text | canvas/secondary-hover | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | canvas/secondary-active | 15.850 | 15.850 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text | canvas/file-button | 16.759 | 16.977 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text | canvas/segment-selected | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | canvas/kbd | 15.710 | 17.420 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-critical | 9.849 | 11.021 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-high | 10.516 | 11.739 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-medium | 11.586 | 12.878 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-low | 11.034 | 12.264 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-compliant | 10.887 | 12.106 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-partial | 11.586 | 12.878 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-noncompliant | 10.287 | 11.492 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | all | text | canvas/tint-insufficient | 11.486 | 12.757 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | all | text | canvas/mark | 10.757 | 11.766 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | all | text | glass/hover | 14.058 | 14.687 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | all | text | glass/press | 13.152 | 13.733 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | all | text | glass/track | 13.407 | 14.001 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | all | text | glass/field | 16.327 | 16.686 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | text | glass/field-hover | 16.759 | 16.977 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text | glass/field-focus | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass/chip | 16.759 | 16.977 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text | glass/nav-selected | 17.242 | 17.301 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | glass/secondary-button | 17.154 | 17.242 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text | glass/secondary-hover | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass/secondary-active | 15.850 | 15.850 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text | glass/file-button | 17.154 | 17.242 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text | glass/segment-selected | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass/kbd | 15.710 | 17.420 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass/tint-critical | 12.002 | 12.524 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | all | text | glass/tint-high | 12.758 | 13.301 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | all | text | glass/tint-medium | 13.963 | 14.533 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | text | glass/tint-low | 13.329 | 13.870 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | all | text | glass/tint-compliant | 13.163 | 13.700 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | all | text | glass/tint-partial | 13.963 | 14.533 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | text | glass/tint-noncompliant | 12.499 | 13.034 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | all | text | glass/tint-insufficient | 13.841 | 14.401 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | all | text | glass/mark | 12.592 | 13.032 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | all | text | glass-strong/hover | 14.719 | 15.138 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | text | glass-strong/press | 13.763 | 14.150 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | all | text | glass-strong/track | 14.033 | 14.428 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | all | text | glass-strong/field | 16.705 | 16.941 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text | glass-strong/field-hover | 16.989 | 17.132 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text | glass-strong/field-focus | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/chip | 16.989 | 17.132 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text | glass-strong/nav-selected | 17.305 | 17.343 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/secondary-button | 17.247 | 17.304 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/secondary-hover | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/secondary-active | 15.850 | 15.850 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text | glass-strong/file-button | 17.247 | 17.304 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/segment-selected | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/kbd | 15.710 | 17.420 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-critical | 12.545 | 12.892 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-high | 13.323 | 13.684 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-medium | 14.559 | 14.938 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-low | 13.903 | 14.263 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-compliant | 13.733 | 14.090 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-partial | 14.559 | 14.938 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-noncompliant | 13.055 | 13.411 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | all | text | glass-strong/tint-insufficient | 14.430 | 14.802 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | text | glass-strong/mark | 13.048 | 13.340 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | all | text | solid/hover | 15.499 | 15.665 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | text | solid/press | 14.484 | 14.637 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | text | solid/track | 14.770 | 14.926 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | text | solid/field | 17.143 | 17.235 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text | solid/field-hover | 17.253 | 17.309 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | solid/field-focus | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/chip | 17.253 | 17.309 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text | solid/nav-selected | 17.376 | 17.391 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/secondary-button | 17.353 | 17.376 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/secondary-hover | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/secondary-active | 15.850 | 15.850 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text | solid/file-button | 17.353 | 17.376 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/segment-selected | 17.420 | 17.420 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/kbd | 15.710 | 17.420 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text | solid/tint-critical | 13.184 | 13.321 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | all | text | solid/tint-high | 13.987 | 14.129 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | all | text | solid/tint-medium | 15.260 | 15.409 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | text | solid/tint-low | 14.578 | 14.720 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | text | solid/tint-compliant | 14.403 | 14.543 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | all | text | solid/tint-partial | 15.260 | 15.409 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | text | solid/tint-noncompliant | 13.711 | 13.851 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | all | text | solid/tint-insufficient | 15.123 | 15.269 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | text | solid/mark | 13.583 | 13.698 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | all | text | modal-over-scrim | 15.986 | 16.106 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas | 6.953 | 7.827 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | all | text-2 | glass | 8.577 | 8.967 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong | 8.987 | 9.247 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | all | text-2 | solid | 9.470 | 9.573 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/hover | 6.418 | 7.212 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/press | 6.021 | 6.755 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/track | 6.133 | 6.883 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/field | 8.291 | 8.770 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/field-hover | 8.868 | 9.166 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/field-focus | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/chip | 8.868 | 9.166 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/nav-selected | 9.532 | 9.614 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/secondary-button | 9.409 | 9.532 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/secondary-hover | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/secondary-active | 8.898 | 8.898 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/file-button | 9.409 | 9.532 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/segment-selected | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/kbd | 8.820 | 9.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-critical | 5.530 | 6.188 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-high | 5.904 | 6.591 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-medium | 6.505 | 7.230 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-low | 6.195 | 6.885 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-compliant | 6.112 | 6.797 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-partial | 6.505 | 7.230 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-noncompliant | 5.776 | 6.452 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/tint-insufficient | 6.448 | 7.162 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | all | text-2 | canvas/mark | 6.039 | 6.606 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/hover | 7.892 | 8.245 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/press | 7.384 | 7.710 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | all | text-2 | glass/track | 7.527 | 7.861 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | all | text-2 | glass/field | 9.166 | 9.368 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | all | text-2 | glass/field-hover | 9.409 | 9.532 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text-2 | glass/field-focus | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass/chip | 9.409 | 9.532 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text-2 | glass/nav-selected | 9.680 | 9.714 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass/secondary-button | 9.631 | 9.680 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text-2 | glass/secondary-hover | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass/secondary-active | 8.898 | 8.898 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/file-button | 9.631 | 9.680 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text-2 | glass/segment-selected | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass/kbd | 8.820 | 9.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-critical | 6.738 | 7.031 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-high | 7.163 | 7.468 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-medium | 7.839 | 8.159 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-low | 7.483 | 7.787 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-compliant | 7.390 | 7.691 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-partial | 7.839 | 8.159 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-noncompliant | 7.017 | 7.318 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | all | text-2 | glass/tint-insufficient | 7.771 | 8.085 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | all | text-2 | glass/mark | 7.069 | 7.317 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/hover | 8.264 | 8.499 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/press | 7.727 | 7.944 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/track | 7.878 | 8.100 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/field | 9.378 | 9.511 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/field-hover | 9.538 | 9.618 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/field-focus | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/chip | 9.538 | 9.618 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/nav-selected | 9.715 | 9.737 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/secondary-button | 9.683 | 9.715 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/secondary-hover | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/secondary-active | 8.898 | 8.898 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/file-button | 9.683 | 9.715 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/segment-selected | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/kbd | 8.820 | 9.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-critical | 7.043 | 7.238 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-high | 7.480 | 7.682 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-medium | 8.174 | 8.387 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-low | 7.806 | 8.008 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-compliant | 7.710 | 7.910 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-partial | 8.174 | 8.387 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-noncompliant | 7.330 | 7.530 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/tint-insufficient | 8.101 | 8.310 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | all | text-2 | glass-strong/mark | 7.326 | 7.490 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | all | text-2 | solid/hover | 8.702 | 8.795 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/press | 8.132 | 8.218 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | all | text-2 | solid/track | 8.292 | 8.380 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/field | 9.624 | 9.676 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | all | text-2 | solid/field-hover | 9.687 | 9.718 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/field-focus | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/chip | 9.687 | 9.718 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/nav-selected | 9.755 | 9.764 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/secondary-button | 9.743 | 9.755 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/secondary-hover | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/secondary-active | 8.898 | 8.898 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/file-button | 9.743 | 9.755 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/segment-selected | 9.780 | 9.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/kbd | 8.820 | 9.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-critical | 7.402 | 7.479 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-high | 7.853 | 7.933 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-medium | 8.567 | 8.651 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-low | 8.185 | 8.264 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-compliant | 8.086 | 8.165 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-partial | 8.567 | 8.651 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-noncompliant | 7.698 | 7.776 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/tint-insufficient | 8.490 | 8.573 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | all | text-2 | solid/mark | 7.626 | 7.690 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | all | text-2 | modal-over-scrim | 8.975 | 9.043 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas | 11.156 | 12.558 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass | 13.762 | 14.387 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong | 14.419 | 14.835 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid | 15.194 | 15.359 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/hover | 10.298 | 11.571 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/press | 9.660 | 10.837 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/track | 9.840 | 11.044 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/field | 13.303 | 14.071 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/field-hover | 14.229 | 14.706 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/field-focus | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/chip | 14.229 | 14.706 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/nav-selected | 15.293 | 15.425 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/secondary-button | 15.096 | 15.293 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/secondary-hover | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/secondary-active | 14.277 | 14.277 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/file-button | 15.096 | 15.293 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/segment-selected | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/kbd | 14.151 | 15.692 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-critical | 8.872 | 9.927 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-high | 9.472 | 10.574 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-medium | 10.436 | 11.600 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-low | 9.939 | 11.047 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-compliant | 9.806 | 10.905 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-partial | 10.436 | 11.600 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-noncompliant | 9.266 | 10.352 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/tint-insufficient | 10.346 | 11.491 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | graphite | accent-text | canvas/mark | 9.690 | 10.598 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/hover | 12.663 | 13.229 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/press | 11.847 | 12.370 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/track | 12.077 | 12.612 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/field | 14.707 | 15.030 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/field-hover | 15.096 | 15.293 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/field-focus | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/chip | 15.096 | 15.293 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/nav-selected | 15.531 | 15.585 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/secondary-button | 15.452 | 15.531 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/secondary-hover | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/secondary-active | 14.277 | 14.277 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/file-button | 15.452 | 15.531 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/segment-selected | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/kbd | 14.151 | 15.692 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-critical | 10.811 | 11.281 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-high | 11.492 | 11.981 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-medium | 12.577 | 13.091 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-low | 12.006 | 12.494 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-compliant | 11.857 | 12.340 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-partial | 12.577 | 13.091 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-noncompliant | 11.258 | 11.741 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/tint-insufficient | 12.467 | 12.972 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass/mark | 11.342 | 11.739 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/hover | 13.259 | 13.636 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/press | 12.398 | 12.746 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/track | 12.640 | 12.997 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/field | 15.047 | 15.260 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/field-hover | 15.303 | 15.432 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/field-focus | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/chip | 15.303 | 15.432 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/nav-selected | 15.587 | 15.622 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/secondary-button | 15.535 | 15.587 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/secondary-hover | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/secondary-active | 14.277 | 14.277 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/file-button | 15.535 | 15.587 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/segment-selected | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/kbd | 14.151 | 15.692 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-critical | 11.300 | 11.613 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-high | 12.001 | 12.326 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-medium | 13.114 | 13.456 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-low | 12.523 | 12.848 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-compliant | 12.370 | 12.691 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-partial | 13.114 | 13.456 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-noncompliant | 11.760 | 12.081 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/tint-insufficient | 12.998 | 13.333 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | graphite | accent-text | glass-strong/mark | 11.754 | 12.016 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/hover | 13.961 | 14.111 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/press | 13.047 | 13.184 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/track | 13.304 | 13.445 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/field | 15.442 | 15.525 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/field-hover | 15.541 | 15.591 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/field-focus | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/chip | 15.541 | 15.591 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/nav-selected | 15.651 | 15.665 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/secondary-button | 15.631 | 15.651 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/secondary-hover | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/secondary-active | 14.277 | 14.277 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/file-button | 15.631 | 15.651 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/segment-selected | 15.692 | 15.692 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/kbd | 14.151 | 15.692 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-critical | 11.875 | 11.999 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-high | 12.599 | 12.727 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-medium | 13.746 | 13.880 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-low | 13.132 | 13.260 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-compliant | 12.973 | 13.100 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-partial | 13.746 | 13.880 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-noncompliant | 12.350 | 12.477 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/tint-insufficient | 13.622 | 13.754 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | graphite | accent-text | solid/mark | 12.235 | 12.338 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | graphite | accent-text | modal-over-scrim | 14.400 | 14.508 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | graphite | canvas-mid | canvas/tint-accent | 1.304 | 1.459 | #CACAD3 | #BAC0CC | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | compliant | canvas/tint-accent | 2.076 | 2.323 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | critical | canvas/tint-accent | 4.472 | 5.002 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | danger-text | canvas/tint-accent | 3.607 | 4.035 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | high | canvas/tint-accent | 2.353 | 2.633 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | insufficient | canvas/tint-accent | 1.391 | 1.557 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | low | canvas/tint-accent | 1.850 | 2.070 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | medium | canvas/tint-accent | 1.179 | 1.318 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | muted | canvas/tint-accent | 3.643 | 4.075 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | noncompliant | canvas/tint-accent | 2.984 | 3.338 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | partial | canvas/tint-accent | 1.179 | 1.318 | #BAC0CC | #CACAD3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | text | canvas/tint-accent | 9.557 | 10.692 | #BAC0CC | #CACAD3 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | text-2 | canvas/tint-accent | 5.366 | 6.003 | #BAC0CC | #CACAD3 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | accent-text | canvas/accent-soft | 12.664 | 12.664 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text | canvas/accent-soft | 14.060 | 14.060 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text-2 | canvas/accent-soft | 7.893 | 7.893 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | muted | canvas/accent-soft | 5.359 | 5.359 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | canvas-mid | glass/tint-accent | 1.146 | 1.195 | #D7D7DD | #CFD4DB | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | compliant | glass/tint-accent | 2.534 | 2.644 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | critical | glass/tint-accent | 5.457 | 5.693 | #CFD4DB | #D7D7DD | Pass | conservative candidate pairing; pill uses text |
| light | graphite | danger-text | glass/tint-accent | 4.402 | 4.592 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | high | glass/tint-accent | 2.872 | 2.996 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | insufficient | glass/tint-accent | 1.698 | 1.772 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | low | glass/tint-accent | 2.258 | 2.356 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | medium | glass/tint-accent | 1.438 | 1.500 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | muted | glass/tint-accent | 4.446 | 4.638 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | noncompliant | glass/tint-accent | 3.641 | 3.799 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | partial | glass/tint-accent | 1.438 | 1.500 | #CFD4DB | #D7D7DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | text | glass/tint-accent | 11.664 | 12.168 | #CFD4DB | #D7D7DD | Pass | conservative candidate pairing; pill uses text |
| light | graphite | text-2 | glass/tint-accent | 6.549 | 6.831 | #CFD4DB | #D7D7DD | Pass | conservative candidate pairing; pill uses text |
| light | graphite | accent-text | glass/accent-soft | 12.664 | 12.664 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text | glass/accent-soft | 14.060 | 14.060 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text-2 | glass/accent-soft | 7.893 | 7.893 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | muted | glass/accent-soft | 5.359 | 5.359 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | canvas-mid | glass-strong/tint-accent | 1.113 | 1.143 | #DADADF | #D5D8DD | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | compliant | glass-strong/tint-accent | 2.649 | 2.722 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | critical | glass-strong/tint-accent | 5.705 | 5.862 | #D5D8DD | #DADADF | Pass | conservative candidate pairing; pill uses text |
| light | graphite | danger-text | glass-strong/tint-accent | 4.602 | 4.729 | #D5D8DD | #DADADF | Pass | conservative candidate pairing; pill uses text |
| light | graphite | high | glass-strong/tint-accent | 3.002 | 3.085 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | insufficient | glass-strong/tint-accent | 1.775 | 1.824 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | low | glass-strong/tint-accent | 2.361 | 2.426 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | medium | glass-strong/tint-accent | 1.504 | 1.545 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | muted | glass-strong/tint-accent | 4.648 | 4.775 | #D5D8DD | #DADADF | Pass | conservative candidate pairing; pill uses text |
| light | graphite | noncompliant | glass-strong/tint-accent | 3.807 | 3.912 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | partial | glass-strong/tint-accent | 1.504 | 1.545 | #D5D8DD | #DADADF | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | text | glass-strong/tint-accent | 12.194 | 12.530 | #D5D8DD | #DADADF | Pass | conservative candidate pairing; pill uses text |
| light | graphite | text-2 | glass-strong/tint-accent | 6.846 | 7.034 | #D5D8DD | #DADADF | Pass | conservative candidate pairing; pill uses text |
| light | graphite | accent-text | glass-strong/accent-soft | 12.664 | 12.664 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text | glass-strong/accent-soft | 14.060 | 14.060 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text-2 | glass-strong/accent-soft | 7.893 | 7.893 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | muted | glass-strong/accent-soft | 5.359 | 5.359 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | canvas-mid | solid/tint-accent | 1.076 | 1.088 | #DDDEE1 | #DBDDE0 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | compliant | solid/tint-accent | 2.785 | 2.814 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | critical | solid/tint-accent | 5.997 | 6.059 | #DBDDE0 | #DDDEE1 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | danger-text | solid/tint-accent | 4.838 | 4.888 | #DBDDE0 | #DDDEE1 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | high | solid/tint-accent | 3.156 | 3.189 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | insufficient | solid/tint-accent | 1.866 | 1.886 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | low | solid/tint-accent | 2.482 | 2.507 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | medium | solid/tint-accent | 1.581 | 1.597 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | muted | solid/tint-accent | 4.886 | 4.936 | #DBDDE0 | #DDDEE1 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | noncompliant | solid/tint-accent | 4.002 | 4.043 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | partial | solid/tint-accent | 1.581 | 1.597 | #DBDDE0 | #DDDEE1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | graphite | text | solid/tint-accent | 12.819 | 12.951 | #DBDDE0 | #DDDEE1 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | text-2 | solid/tint-accent | 7.197 | 7.271 | #DBDDE0 | #DDDEE1 | Pass | conservative candidate pairing; pill uses text |
| light | graphite | accent-text | solid/accent-soft | 12.664 | 12.664 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text | solid/accent-soft | 14.060 | 14.060 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | text-2 | solid/accent-soft | 7.893 | 7.893 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | muted | solid/accent-soft | 5.359 | 5.359 | #E6E7E8 | #E6E7E8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | graphite | on-accent | primary-button | 10.080 | 15.692 | #3E424D | #1E2330 | Pass | declared component pairing |
| light | graphite | on-accent | primary-kbd | 6.285 | 9.409 | #5C6069 | #424651 | Pass | declared component pairing |
| light | azure | accent-text | canvas | 4.005 | 4.508 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass | 4.940 | 5.164 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong | 5.176 | 5.325 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | azure | accent-text | solid | 5.454 | 5.513 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/hover | 3.697 | 4.154 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/press | 3.468 | 3.890 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/track | 3.532 | 3.964 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/field | 4.775 | 5.051 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/field-hover | 5.108 | 5.279 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/field-focus | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/chip | 5.108 | 5.279 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/nav-selected | 5.490 | 5.537 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/secondary-button | 5.419 | 5.490 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/secondary-hover | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/secondary-active | 5.125 | 5.125 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/file-button | 5.419 | 5.490 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/segment-selected | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/kbd | 5.080 | 5.633 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-critical | 3.185 | 3.564 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-high | 3.400 | 3.796 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-medium | 3.746 | 4.164 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-low | 3.568 | 3.966 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-compliant | 3.520 | 3.915 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-partial | 3.746 | 4.164 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-noncompliant | 3.326 | 3.716 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/tint-insufficient | 3.714 | 4.125 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | canvas/mark | 3.478 | 3.804 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/hover | 4.546 | 4.749 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/press | 4.253 | 4.441 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/track | 4.335 | 4.527 | #DEE2E9 | #E6E6EC | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/field | 5.279 | 5.395 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/field-hover | 5.419 | 5.490 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/field-focus | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/chip | 5.419 | 5.490 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/nav-selected | 5.575 | 5.594 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/secondary-button | 5.547 | 5.575 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/secondary-hover | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/secondary-active | 5.125 | 5.125 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/file-button | 5.547 | 5.575 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/segment-selected | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/kbd | 5.080 | 5.633 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/tint-critical | 3.881 | 4.050 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/tint-high | 4.125 | 4.301 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/tint-medium | 4.515 | 4.699 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/tint-low | 4.310 | 4.485 | #D4E5E3 | #DBE8E6 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/tint-compliant | 4.256 | 4.430 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/tint-partial | 4.515 | 4.699 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | azure | accent-text | glass/tint-noncompliant | 4.041 | 4.215 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/tint-insufficient | 4.475 | 4.656 | #E1E5ED | #E8E9F0 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass/mark | 4.071 | 4.214 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/hover | 4.760 | 4.895 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/press | 4.450 | 4.575 | #E2E5EA | #E7E7EC | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/track | 4.537 | 4.665 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/field | 5.401 | 5.478 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/field-hover | 5.493 | 5.539 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/field-focus | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/chip | 5.493 | 5.539 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/nav-selected | 5.595 | 5.608 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/secondary-button | 5.577 | 5.595 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/secondary-hover | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/secondary-active | 5.125 | 5.125 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/file-button | 5.577 | 5.595 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/segment-selected | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/kbd | 5.080 | 5.633 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-critical | 4.056 | 4.169 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-high | 4.308 | 4.425 | #EFDDDB | #F4DFDC | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-medium | 4.708 | 4.830 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-low | 4.496 | 4.612 | #D9E9E6 | #DEEBE7 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-compliant | 4.440 | 4.556 | #D7E8E5 | #DCEAE7 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-partial | 4.708 | 4.830 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-noncompliant | 4.221 | 4.337 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | glass-strong/tint-insufficient | 4.666 | 4.786 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | azure | accent-text | glass-strong/mark | 4.219 | 4.314 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | solid/hover | 5.012 | 5.065 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/press | 4.683 | 4.733 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/track | 4.776 | 4.826 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/field | 5.543 | 5.573 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/field-hover | 5.579 | 5.597 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/field-focus | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/chip | 5.579 | 5.597 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/nav-selected | 5.618 | 5.623 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/secondary-button | 5.611 | 5.618 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/secondary-hover | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/secondary-active | 5.125 | 5.125 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/file-button | 5.611 | 5.618 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/segment-selected | 5.633 | 5.633 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/kbd | 5.080 | 5.633 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-critical | 4.263 | 4.307 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | solid/tint-high | 4.523 | 4.569 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-medium | 4.934 | 4.983 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-low | 4.714 | 4.760 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-compliant | 4.657 | 4.703 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-partial | 4.934 | 4.983 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/tint-noncompliant | 4.433 | 4.479 | #F2E0DF | #F4E1E0 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | solid/tint-insufficient | 4.890 | 4.937 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | azure | accent-text | solid/mark | 4.392 | 4.429 | #F7E0BF | #F9E1C0 | Fail candidate | conservative candidate pairing |
| light | azure | accent-text | modal-over-scrim | 5.169 | 5.208 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | azure | canvas-mid | canvas/tint-accent | 1.206 | 1.343 | #C7D3E8 | #B6CAE0 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | compliant | canvas/tint-accent | 2.256 | 2.512 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | critical | canvas/tint-accent | 4.858 | 5.410 | #B6CAE0 | #C7D3E8 | Pass | conservative candidate pairing; pill uses text |
| light | azure | danger-text | canvas/tint-accent | 3.918 | 4.364 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | high | canvas/tint-accent | 2.556 | 2.847 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | insufficient | canvas/tint-accent | 1.512 | 1.683 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | low | canvas/tint-accent | 2.010 | 2.238 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | medium | canvas/tint-accent | 1.280 | 1.426 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | muted | canvas/tint-accent | 3.957 | 4.407 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | noncompliant | canvas/tint-accent | 3.241 | 3.610 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | partial | canvas/tint-accent | 1.280 | 1.426 | #B6CAE0 | #C7D3E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | text | canvas/tint-accent | 10.383 | 11.563 | #B6CAE0 | #C7D3E8 | Pass | conservative candidate pairing; pill uses text |
| light | azure | text-2 | canvas/tint-accent | 5.829 | 6.492 | #B6CAE0 | #C7D3E8 | Pass | conservative candidate pairing; pill uses text |
| light | azure | accent-text | canvas/accent-soft | 4.804 | 4.804 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text | canvas/accent-soft | 14.858 | 14.858 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text-2 | canvas/accent-soft | 8.342 | 8.342 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | muted | canvas/accent-soft | 5.663 | 5.663 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | canvas-mid | glass/tint-accent | 1.064 | 1.108 | #D4E1F2 | #CCDDEF | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | compliant | glass/tint-accent | 2.735 | 2.848 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | critical | glass/tint-accent | 5.890 | 6.133 | #CCDDEF | #D4E1F2 | Pass | conservative candidate pairing; pill uses text |
| light | azure | danger-text | glass/tint-accent | 4.751 | 4.947 | #CCDDEF | #D4E1F2 | Pass | conservative candidate pairing; pill uses text |
| light | azure | high | glass/tint-accent | 3.099 | 3.228 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | insufficient | glass/tint-accent | 1.833 | 1.908 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | low | glass/tint-accent | 2.437 | 2.538 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | medium | glass/tint-accent | 1.552 | 1.616 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | muted | glass/tint-accent | 4.798 | 4.996 | #CCDDEF | #D4E1F2 | Pass | conservative candidate pairing; pill uses text |
| light | azure | noncompliant | glass/tint-accent | 3.930 | 4.092 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | partial | glass/tint-accent | 1.552 | 1.616 | #CCDDEF | #D4E1F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | text | glass/tint-accent | 12.588 | 13.109 | #CCDDEF | #D4E1F2 | Pass | conservative candidate pairing; pill uses text |
| light | azure | text-2 | glass/tint-accent | 7.067 | 7.360 | #CCDDEF | #D4E1F2 | Pass | conservative candidate pairing; pill uses text |
| light | azure | accent-text | glass/accent-soft | 4.804 | 4.804 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text | glass/accent-soft | 14.858 | 14.858 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text-2 | glass/accent-soft | 8.342 | 8.342 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | muted | glass/accent-soft | 5.663 | 5.663 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | canvas-mid | glass-strong/tint-accent | 1.034 | 1.061 | #D7E4F3 | #D2E2F2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | compliant | glass-strong/tint-accent | 2.855 | 2.930 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | critical | glass-strong/tint-accent | 6.148 | 6.310 | #D2E2F2 | #D7E4F3 | Pass | conservative candidate pairing; pill uses text |
| light | azure | danger-text | glass-strong/tint-accent | 4.959 | 5.090 | #D2E2F2 | #D7E4F3 | Pass | conservative candidate pairing; pill uses text |
| light | azure | high | glass-strong/tint-accent | 3.235 | 3.321 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | insufficient | glass-strong/tint-accent | 1.913 | 1.963 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | low | glass-strong/tint-accent | 2.544 | 2.611 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | medium | glass-strong/tint-accent | 1.620 | 1.663 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | muted | glass-strong/tint-accent | 5.008 | 5.140 | #D2E2F2 | #D7E4F3 | Pass | conservative candidate pairing; pill uses text |
| light | azure | noncompliant | glass-strong/tint-accent | 4.102 | 4.210 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | partial | glass-strong/tint-accent | 1.620 | 1.663 | #D2E2F2 | #D7E4F3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | text | glass-strong/tint-accent | 13.140 | 13.487 | #D2E2F2 | #D7E4F3 | Pass | conservative candidate pairing; pill uses text |
| light | azure | text-2 | glass-strong/tint-accent | 7.377 | 7.572 | #D2E2F2 | #D7E4F3 | Pass | conservative candidate pairing; pill uses text |
| light | azure | accent-text | glass-strong/accent-soft | 4.804 | 4.804 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text | glass-strong/accent-soft | 14.858 | 14.858 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text-2 | glass-strong/accent-soft | 8.342 | 8.342 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | muted | glass-strong/accent-soft | 5.663 | 5.663 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | canvas-mid | solid/tint-accent | 1.001 | 1.011 | #DAE7F5 | #D8E7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | compliant | solid/tint-accent | 2.996 | 3.026 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | critical | solid/tint-accent | 6.452 | 6.516 | #D8E7F5 | #DAE7F5 | Pass | conservative candidate pairing; pill uses text |
| light | azure | danger-text | solid/tint-accent | 5.204 | 5.256 | #D8E7F5 | #DAE7F5 | Pass | conservative candidate pairing; pill uses text |
| light | azure | high | solid/tint-accent | 3.395 | 3.429 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | insufficient | solid/tint-accent | 2.008 | 2.028 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | low | solid/tint-accent | 2.670 | 2.696 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | medium | solid/tint-accent | 1.700 | 1.717 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | muted | solid/tint-accent | 5.256 | 5.308 | #D8E7F5 | #DAE7F5 | Pass | conservative candidate pairing; pill uses text |
| light | azure | noncompliant | solid/tint-accent | 4.305 | 4.348 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | partial | solid/tint-accent | 1.700 | 1.717 | #D8E7F5 | #DAE7F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | azure | text | solid/tint-accent | 13.790 | 13.927 | #D8E7F5 | #DAE7F5 | Pass | conservative candidate pairing; pill uses text |
| light | azure | text-2 | solid/tint-accent | 7.742 | 7.819 | #D8E7F5 | #DAE7F5 | Pass | conservative candidate pairing; pill uses text |
| light | azure | accent-text | solid/accent-soft | 4.804 | 4.804 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text | solid/accent-soft | 14.858 | 14.858 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | text-2 | solid/accent-soft | 8.342 | 8.342 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | muted | solid/accent-soft | 5.663 | 5.663 | #E4EEF8 | #E4EEF8 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | azure | on-accent | primary-button | 4.328 | 5.633 | #2A7CCB | #0767C2 | Fail candidate | declared component pairing |
| light | azure | on-accent | primary-kbd | 3.329 | 4.166 | #4C91D3 | #2F7FCC | Fail candidate | declared component pairing |
| light | cobalt | accent-text | canvas | 4.820 | 5.426 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass | 5.946 | 6.216 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong | 6.230 | 6.410 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid | 6.565 | 6.636 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/hover | 4.449 | 5.000 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/press | 4.174 | 4.683 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/track | 4.252 | 4.772 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/field | 5.748 | 6.080 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/field-hover | 6.148 | 6.354 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/field-focus | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/chip | 6.148 | 6.354 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/nav-selected | 6.608 | 6.665 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/secondary-button | 6.523 | 6.608 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/secondary-hover | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/secondary-active | 6.169 | 6.169 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/file-button | 6.523 | 6.608 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/segment-selected | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/kbd | 6.115 | 6.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-critical | 3.833 | 4.289 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-high | 4.093 | 4.569 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-medium | 4.509 | 5.012 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-low | 4.294 | 4.773 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-compliant | 4.237 | 4.712 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-partial | 4.509 | 5.012 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-noncompliant | 4.004 | 4.473 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/tint-insufficient | 4.470 | 4.965 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | canvas/mark | 4.187 | 4.579 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | cobalt | accent-text | glass/hover | 5.471 | 5.716 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/press | 5.119 | 5.345 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/track | 5.218 | 5.449 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/field | 6.354 | 6.494 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/field-hover | 6.523 | 6.608 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/field-focus | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/chip | 6.523 | 6.608 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/nav-selected | 6.711 | 6.734 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/secondary-button | 6.676 | 6.711 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/secondary-hover | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/secondary-active | 6.169 | 6.169 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/file-button | 6.676 | 6.711 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/segment-selected | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/kbd | 6.115 | 6.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-critical | 4.671 | 4.874 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-high | 4.966 | 5.177 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-medium | 5.434 | 5.656 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-low | 5.188 | 5.398 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-compliant | 5.123 | 5.332 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-partial | 5.434 | 5.656 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-noncompliant | 4.865 | 5.073 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/tint-insufficient | 5.387 | 5.605 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass/mark | 4.901 | 5.072 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/hover | 5.729 | 5.892 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/press | 5.357 | 5.507 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/track | 5.461 | 5.616 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/field | 6.501 | 6.593 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/field-hover | 6.612 | 6.668 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/field-focus | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/chip | 6.612 | 6.668 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/nav-selected | 6.735 | 6.750 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/secondary-button | 6.712 | 6.735 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/secondary-hover | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/secondary-active | 6.169 | 6.169 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/file-button | 6.712 | 6.735 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/segment-selected | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/kbd | 6.115 | 6.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-critical | 4.882 | 5.018 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-high | 5.185 | 5.326 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-medium | 5.666 | 5.814 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-low | 5.411 | 5.551 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-compliant | 5.345 | 5.484 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-partial | 5.666 | 5.814 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-noncompliant | 5.081 | 5.220 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/tint-insufficient | 5.616 | 5.761 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | glass-strong/mark | 5.078 | 5.192 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/hover | 6.032 | 6.097 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/press | 5.637 | 5.697 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/track | 5.748 | 5.809 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/field | 6.672 | 6.708 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/field-hover | 6.715 | 6.737 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/field-focus | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/chip | 6.715 | 6.737 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/nav-selected | 6.763 | 6.768 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/secondary-button | 6.754 | 6.763 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/secondary-hover | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/secondary-active | 6.169 | 6.169 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/file-button | 6.754 | 6.763 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/segment-selected | 6.780 | 6.780 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/kbd | 6.115 | 6.780 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-critical | 5.131 | 5.184 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-high | 5.444 | 5.499 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-medium | 5.939 | 5.997 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-low | 5.674 | 5.729 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-compliant | 5.606 | 5.660 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-partial | 5.939 | 5.997 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-noncompliant | 5.336 | 5.391 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/tint-insufficient | 5.886 | 5.943 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | solid/mark | 5.287 | 5.331 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | cobalt | accent-text | modal-over-scrim | 6.222 | 6.269 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | cobalt | canvas-mid | canvas/tint-accent | 1.225 | 1.365 | #CAD0EA | #BAC7E2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | compliant | canvas/tint-accent | 2.219 | 2.474 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | critical | canvas/tint-accent | 4.778 | 5.327 | #BAC7E2 | #CAD0EA | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | danger-text | canvas/tint-accent | 3.854 | 4.297 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | high | canvas/tint-accent | 2.514 | 2.803 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | insufficient | canvas/tint-accent | 1.487 | 1.658 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | low | canvas/tint-accent | 1.977 | 2.204 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | medium | canvas/tint-accent | 1.259 | 1.404 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | muted | canvas/tint-accent | 3.892 | 4.339 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | noncompliant | canvas/tint-accent | 3.188 | 3.554 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | partial | canvas/tint-accent | 1.259 | 1.404 | #BAC7E2 | #CAD0EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | text | canvas/tint-accent | 10.212 | 11.385 | #BAC7E2 | #CAD0EA | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | text-2 | canvas/tint-accent | 5.733 | 6.392 | #BAC7E2 | #CAD0EA | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | accent-text | canvas/accent-soft | 5.719 | 5.719 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text | canvas/accent-soft | 14.694 | 14.694 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text-2 | canvas/accent-soft | 8.249 | 8.249 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | muted | canvas/accent-soft | 5.600 | 5.600 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | canvas-mid | glass/tint-accent | 1.079 | 1.125 | #D7DDF4 | #D0DAF1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | compliant | glass/tint-accent | 2.693 | 2.806 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | critical | glass/tint-accent | 5.800 | 6.043 | #D0DAF1 | #D7DDF4 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | danger-text | glass/tint-accent | 4.679 | 4.874 | #D0DAF1 | #D7DDF4 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | high | glass/tint-accent | 3.052 | 3.180 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | insufficient | glass/tint-accent | 1.805 | 1.880 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | low | glass/tint-accent | 2.400 | 2.500 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | medium | glass/tint-accent | 1.529 | 1.593 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | muted | glass/tint-accent | 4.725 | 4.922 | #D0DAF1 | #D7DDF4 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | noncompliant | glass/tint-accent | 3.870 | 4.032 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | partial | glass/tint-accent | 1.529 | 1.593 | #D0DAF1 | #D7DDF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | text | glass/tint-accent | 12.397 | 12.916 | #D0DAF1 | #D7DDF4 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | text-2 | glass/tint-accent | 6.960 | 7.251 | #D0DAF1 | #D7DDF4 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | accent-text | glass/accent-soft | 5.719 | 5.719 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text | glass/accent-soft | 14.694 | 14.694 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text-2 | glass/accent-soft | 8.249 | 8.249 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | muted | glass/accent-soft | 5.600 | 5.600 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | canvas-mid | glass-strong/tint-accent | 1.049 | 1.077 | #DAE0F5 | #D5DEF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | compliant | glass-strong/tint-accent | 2.812 | 2.887 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | critical | glass-strong/tint-accent | 6.056 | 6.218 | #D5DEF4 | #DAE0F5 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | danger-text | glass-strong/tint-accent | 4.885 | 5.015 | #D5DEF4 | #DAE0F5 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | high | glass-strong/tint-accent | 3.187 | 3.272 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | insufficient | glass-strong/tint-accent | 1.885 | 1.935 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | low | glass-strong/tint-accent | 2.506 | 2.573 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | medium | glass-strong/tint-accent | 1.596 | 1.639 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | muted | glass-strong/tint-accent | 4.934 | 5.065 | #D5DEF4 | #DAE0F5 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | noncompliant | glass-strong/tint-accent | 4.041 | 4.149 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | partial | glass-strong/tint-accent | 1.596 | 1.639 | #D5DEF4 | #DAE0F5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | text | glass-strong/tint-accent | 12.945 | 13.289 | #D5DEF4 | #DAE0F5 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | text-2 | glass-strong/tint-accent | 7.267 | 7.461 | #D5DEF4 | #DAE0F5 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | accent-text | glass-strong/accent-soft | 5.719 | 5.719 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text | glass-strong/accent-soft | 14.694 | 14.694 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text-2 | glass-strong/accent-soft | 8.249 | 8.249 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | muted | glass-strong/accent-soft | 5.600 | 5.600 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | canvas-mid | solid/tint-accent | 1.016 | 1.026 | #DDE4F7 | #DCE3F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | compliant | solid/tint-accent | 2.952 | 2.982 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | critical | solid/tint-accent | 6.358 | 6.421 | #DCE3F7 | #DDE4F7 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | danger-text | solid/tint-accent | 5.128 | 5.180 | #DCE3F7 | #DDE4F7 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | high | solid/tint-accent | 3.346 | 3.379 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | insufficient | solid/tint-accent | 1.978 | 1.998 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | low | solid/tint-accent | 2.631 | 2.657 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | medium | solid/tint-accent | 1.676 | 1.692 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | muted | solid/tint-accent | 5.179 | 5.231 | #DCE3F7 | #DDE4F7 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | noncompliant | solid/tint-accent | 4.242 | 4.285 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | partial | solid/tint-accent | 1.676 | 1.692 | #DCE3F7 | #DDE4F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | cobalt | text | solid/tint-accent | 13.589 | 13.725 | #DCE3F7 | #DDE4F7 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | text-2 | solid/tint-accent | 7.629 | 7.706 | #DCE3F7 | #DDE4F7 | Pass | conservative candidate pairing; pill uses text |
| light | cobalt | accent-text | solid/accent-soft | 5.719 | 5.719 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text | solid/accent-soft | 14.694 | 14.694 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | text-2 | solid/accent-soft | 8.249 | 8.249 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | muted | solid/accent-soft | 5.600 | 5.600 | #E6ECFA | #E6ECFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | cobalt | on-accent | primary-button | 5.050 | 6.780 | #3E68D7 | #1F4FD1 | Pass | declared component pairing |
| light | cobalt | on-accent | primary-kbd | 3.750 | 4.836 | #5D80DE | #436BD8 | Fail candidate | declared component pairing |
| light | midnight | accent-text | canvas | 7.868 | 8.857 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass | 9.706 | 10.146 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong | 10.169 | 10.463 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid | 10.716 | 10.832 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/hover | 7.263 | 8.161 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/press | 6.813 | 7.643 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/track | 6.940 | 7.789 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/field | 9.382 | 9.924 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/field-hover | 10.035 | 10.372 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/field-focus | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/chip | 10.035 | 10.372 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/nav-selected | 10.785 | 10.879 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/secondary-button | 10.646 | 10.785 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/secondary-hover | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/secondary-active | 10.069 | 10.069 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/file-button | 10.646 | 10.785 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/segment-selected | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/kbd | 9.980 | 11.067 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-critical | 6.257 | 7.001 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-high | 6.681 | 7.458 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-medium | 7.360 | 8.181 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-low | 7.010 | 7.791 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-compliant | 6.916 | 7.691 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-partial | 7.360 | 8.181 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-noncompliant | 6.535 | 7.301 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/tint-insufficient | 7.297 | 8.104 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | midnight | accent-text | canvas/mark | 6.834 | 7.475 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/hover | 8.931 | 9.330 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/press | 8.355 | 8.724 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/track | 8.517 | 8.895 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/field | 10.372 | 10.600 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/field-hover | 10.647 | 10.785 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/field-focus | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/chip | 10.647 | 10.785 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/nav-selected | 10.954 | 10.991 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/secondary-button | 10.897 | 10.954 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/secondary-hover | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/secondary-active | 10.069 | 10.069 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/file-button | 10.897 | 10.954 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/segment-selected | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/kbd | 9.980 | 11.067 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-critical | 7.625 | 7.956 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-high | 8.105 | 8.450 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-medium | 8.870 | 9.233 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-low | 8.468 | 8.811 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-compliant | 8.362 | 8.703 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-partial | 8.870 | 9.233 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-noncompliant | 7.940 | 8.280 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/tint-insufficient | 8.793 | 9.148 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass/mark | 7.999 | 8.279 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/hover | 9.351 | 9.617 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/press | 8.744 | 8.989 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/track | 8.915 | 9.166 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/field | 10.612 | 10.762 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/field-hover | 10.792 | 10.883 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/field-focus | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/chip | 10.792 | 10.883 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/nav-selected | 10.993 | 11.018 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/secondary-button | 10.957 | 10.993 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/secondary-hover | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/secondary-active | 10.069 | 10.069 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/file-button | 10.957 | 10.993 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/segment-selected | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/kbd | 9.980 | 11.067 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-critical | 7.969 | 8.190 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-high | 8.464 | 8.693 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-medium | 9.249 | 9.490 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-low | 8.832 | 9.061 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-compliant | 8.724 | 8.951 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-partial | 9.249 | 9.490 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-noncompliant | 8.294 | 8.520 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/tint-insufficient | 9.167 | 9.403 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | midnight | accent-text | glass-strong/mark | 8.289 | 8.475 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/hover | 9.846 | 9.952 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/press | 9.201 | 9.298 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/track | 9.383 | 9.482 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/field | 10.890 | 10.949 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/field-hover | 10.961 | 10.996 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/field-focus | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/chip | 10.961 | 10.996 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/nav-selected | 11.038 | 11.048 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/secondary-button | 11.024 | 11.038 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/secondary-hover | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/secondary-active | 10.069 | 10.069 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/file-button | 11.024 | 11.038 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/segment-selected | 11.067 | 11.067 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/kbd | 9.980 | 11.067 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-critical | 8.375 | 8.462 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-high | 8.885 | 8.976 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-medium | 9.694 | 9.789 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-low | 9.261 | 9.352 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-compliant | 9.150 | 9.239 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-partial | 9.694 | 9.789 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-noncompliant | 8.710 | 8.799 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/tint-insufficient | 9.607 | 9.700 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | midnight | accent-text | solid/mark | 8.629 | 8.702 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | midnight | accent-text | modal-over-scrim | 10.156 | 10.232 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | midnight | canvas-mid | canvas/tint-accent | 1.265 | 1.413 | #CACDDD | #B9C4D5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | compliant | canvas/tint-accent | 2.143 | 2.394 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | critical | canvas/tint-accent | 4.615 | 5.155 | #B9C4D5 | #CACDDD | Pass | conservative candidate pairing; pill uses text |
| light | midnight | danger-text | canvas/tint-accent | 3.723 | 4.158 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | high | canvas/tint-accent | 2.429 | 2.713 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | insufficient | canvas/tint-accent | 1.436 | 1.604 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | low | canvas/tint-accent | 1.910 | 2.133 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | medium | canvas/tint-accent | 1.216 | 1.359 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | muted | canvas/tint-accent | 3.760 | 4.199 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | noncompliant | canvas/tint-accent | 3.080 | 3.440 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | partial | canvas/tint-accent | 1.216 | 1.359 | #B9C4D5 | #CACDDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | text | canvas/tint-accent | 9.865 | 11.018 | #B9C4D5 | #CACDDD | Pass | conservative candidate pairing; pill uses text |
| light | midnight | text-2 | canvas/tint-accent | 5.538 | 6.186 | #B9C4D5 | #CACDDD | Pass | conservative candidate pairing; pill uses text |
| light | midnight | accent-text | canvas/accent-soft | 9.123 | 9.123 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text | canvas/accent-soft | 14.360 | 14.360 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text-2 | canvas/accent-soft | 8.062 | 8.062 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | muted | canvas/accent-soft | 5.473 | 5.473 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | canvas-mid | glass/tint-accent | 1.114 | 1.161 | #D7DAE7 | #CFD7E4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | compliant | glass/tint-accent | 2.609 | 2.720 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | critical | glass/tint-accent | 5.619 | 5.858 | #CFD7E4 | #D7DAE7 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | danger-text | glass/tint-accent | 4.532 | 4.725 | #CFD7E4 | #D7DAE7 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | high | glass/tint-accent | 2.957 | 3.083 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | insufficient | glass/tint-accent | 1.748 | 1.823 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | low | glass/tint-accent | 2.325 | 2.424 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | medium | glass/tint-accent | 1.481 | 1.544 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | muted | glass/tint-accent | 4.577 | 4.772 | #CFD7E4 | #D7DAE7 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | noncompliant | glass/tint-accent | 3.749 | 3.909 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | partial | glass/tint-accent | 1.481 | 1.544 | #CFD7E4 | #D7DAE7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | text | glass/tint-accent | 12.010 | 12.520 | #CFD7E4 | #D7DAE7 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | text-2 | glass/tint-accent | 6.743 | 7.029 | #CFD7E4 | #D7DAE7 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | accent-text | glass/accent-soft | 9.123 | 9.123 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text | glass/accent-soft | 14.360 | 14.360 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text-2 | glass/accent-soft | 8.062 | 8.062 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | muted | glass/accent-soft | 5.473 | 5.473 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | canvas-mid | glass-strong/tint-accent | 1.082 | 1.111 | #DADEE8 | #D5DBE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | compliant | glass-strong/tint-accent | 2.726 | 2.800 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | critical | glass-strong/tint-accent | 5.871 | 6.030 | #D5DBE6 | #DADEE8 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | danger-text | glass-strong/tint-accent | 4.736 | 4.864 | #D5DBE6 | #DADEE8 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | high | glass-strong/tint-accent | 3.090 | 3.173 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | insufficient | glass-strong/tint-accent | 1.827 | 1.876 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | low | glass-strong/tint-accent | 2.429 | 2.495 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | medium | glass-strong/tint-accent | 1.547 | 1.589 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | muted | glass-strong/tint-accent | 4.782 | 4.912 | #D5DBE6 | #DADEE8 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | noncompliant | glass-strong/tint-accent | 3.917 | 4.023 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | partial | glass-strong/tint-accent | 1.547 | 1.589 | #D5DBE6 | #DADEE8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | text | glass-strong/tint-accent | 12.548 | 12.888 | #D5DBE6 | #DADEE8 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | text-2 | glass-strong/tint-accent | 7.045 | 7.236 | #D5DBE6 | #DADEE8 | Pass | conservative candidate pairing; pill uses text |
| light | midnight | accent-text | glass-strong/accent-soft | 9.123 | 9.123 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text | glass-strong/accent-soft | 14.360 | 14.360 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text-2 | glass-strong/accent-soft | 8.062 | 8.062 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | muted | glass-strong/accent-soft | 5.473 | 5.473 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | canvas-mid | solid/tint-accent | 1.047 | 1.058 | #DDE1EA | #DBE0E9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | compliant | solid/tint-accent | 2.864 | 2.893 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | critical | solid/tint-accent | 6.167 | 6.230 | #DBE0E9 | #DDE1EA | Pass | conservative candidate pairing; pill uses text |
| light | midnight | danger-text | solid/tint-accent | 4.975 | 5.025 | #DBE0E9 | #DDE1EA | Pass | conservative candidate pairing; pill uses text |
| light | midnight | high | solid/tint-accent | 3.246 | 3.279 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | insufficient | solid/tint-accent | 1.919 | 1.939 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | low | solid/tint-accent | 2.552 | 2.578 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | medium | solid/tint-accent | 1.625 | 1.642 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | muted | solid/tint-accent | 5.024 | 5.075 | #DBE0E9 | #DDE1EA | Pass | conservative candidate pairing; pill uses text |
| light | midnight | noncompliant | solid/tint-accent | 4.115 | 4.157 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | partial | solid/tint-accent | 1.625 | 1.642 | #DBE0E9 | #DDE1EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | midnight | text | solid/tint-accent | 13.182 | 13.316 | #DBE0E9 | #DDE1EA | Pass | conservative candidate pairing; pill uses text |
| light | midnight | text-2 | solid/tint-accent | 7.401 | 7.476 | #DBE0E9 | #DDE1EA | Pass | conservative candidate pairing; pill uses text |
| light | midnight | accent-text | solid/accent-soft | 9.123 | 9.123 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text | solid/accent-soft | 14.360 | 14.360 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | text-2 | solid/accent-soft | 8.062 | 8.062 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | muted | solid/accent-soft | 5.473 | 5.473 | #E6E9EF | #E6E9EF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | midnight | on-accent | primary-button | 7.365 | 11.067 | #3C5686 | #1C3A72 | Pass | declared component pairing |
| light | midnight | on-accent | primary-kbd | 4.937 | 6.942 | #5B7199 | #405A89 | Pass | declared component pairing |
| light | teal | accent-text | canvas | 4.204 | 4.733 | #D3DAE5 | #E6E5EE | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass | 5.186 | 5.422 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong | 5.434 | 5.591 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | teal | accent-text | solid | 5.726 | 5.788 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/hover | 3.881 | 4.361 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/press | 3.641 | 4.084 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/track | 3.708 | 4.162 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/field | 5.013 | 5.303 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/field-hover | 5.362 | 5.542 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/field-focus | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/chip | 5.362 | 5.542 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/nav-selected | 5.763 | 5.813 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/secondary-button | 5.689 | 5.763 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/secondary-hover | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/secondary-active | 5.381 | 5.381 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/file-button | 5.689 | 5.763 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/segment-selected | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/kbd | 5.333 | 5.914 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-critical | 3.344 | 3.741 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-high | 3.570 | 3.985 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-medium | 3.933 | 4.372 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-low | 3.746 | 4.163 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-compliant | 3.696 | 4.110 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-partial | 3.933 | 4.372 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-noncompliant | 3.492 | 3.901 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/tint-insufficient | 3.899 | 4.331 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | canvas/mark | 3.652 | 3.994 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/hover | 4.772 | 4.986 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/press | 4.465 | 4.662 | #DCE0E7 | #E4E4EA | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/track | 4.551 | 4.753 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/field | 5.543 | 5.664 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/field-hover | 5.689 | 5.763 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/field-focus | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/chip | 5.689 | 5.763 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/nav-selected | 5.853 | 5.873 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/secondary-button | 5.823 | 5.853 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/secondary-hover | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/secondary-active | 5.381 | 5.381 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/file-button | 5.823 | 5.853 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/segment-selected | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/kbd | 5.333 | 5.914 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/tint-critical | 4.074 | 4.251 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/tint-high | 4.331 | 4.515 | #EAD9D8 | #F1DCDB | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/tint-medium | 4.740 | 4.934 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/tint-low | 4.525 | 4.709 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/tint-compliant | 4.468 | 4.651 | #D2E3E2 | #D9E7E5 | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/tint-partial | 4.740 | 4.934 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/tint-noncompliant | 4.243 | 4.425 | #E6D7DA | #EEDADD | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass/tint-insufficient | 4.699 | 4.889 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass/mark | 4.274 | 4.424 | #EDD8BB | #F4DBBD | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass-strong/hover | 4.997 | 5.139 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/press | 4.672 | 4.804 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/track | 4.764 | 4.898 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/field | 5.671 | 5.751 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/field-hover | 5.767 | 5.816 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/field-focus | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/chip | 5.767 | 5.816 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/nav-selected | 5.874 | 5.887 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/secondary-button | 5.855 | 5.874 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/secondary-hover | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/secondary-active | 5.381 | 5.381 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/file-button | 5.855 | 5.874 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/segment-selected | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/kbd | 5.333 | 5.914 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-critical | 4.259 | 4.376 | #E7D7DA | #EBD9DC | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-high | 4.523 | 4.645 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-medium | 4.942 | 5.071 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-low | 4.720 | 4.842 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-compliant | 4.662 | 4.783 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-partial | 4.942 | 5.071 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-noncompliant | 4.432 | 4.553 | #ECDBDD | #F1DDDE | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | glass-strong/tint-insufficient | 4.899 | 5.025 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | teal | accent-text | glass-strong/mark | 4.430 | 4.529 | #F2DCBD | #F6DEBE | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | solid/hover | 5.262 | 5.318 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/press | 4.917 | 4.969 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/track | 5.014 | 5.067 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/field | 5.820 | 5.851 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/field-hover | 5.857 | 5.876 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/field-focus | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/chip | 5.857 | 5.876 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/nav-selected | 5.899 | 5.904 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/secondary-button | 5.891 | 5.899 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/secondary-hover | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/secondary-active | 5.381 | 5.381 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/file-button | 5.891 | 5.899 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/segment-selected | 5.914 | 5.914 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/kbd | 5.333 | 5.914 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-critical | 4.476 | 4.522 | #EDDCDD | #EFDDDE | Fail candidate | conservative candidate pairing |
| light | teal | accent-text | solid/tint-high | 4.748 | 4.796 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-medium | 5.180 | 5.231 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-low | 4.949 | 4.997 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-compliant | 4.889 | 4.937 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-partial | 5.180 | 5.231 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-noncompliant | 4.654 | 4.702 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/tint-insufficient | 5.134 | 5.183 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | teal | accent-text | solid/mark | 4.611 | 4.650 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | teal | accent-text | modal-over-scrim | 5.427 | 5.468 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | teal | canvas-mid | canvas/tint-accent | 1.205 | 1.342 | #C7D4DE | #B7CBD7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | compliant | canvas/tint-accent | 2.257 | 2.514 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | critical | canvas/tint-accent | 4.860 | 5.414 | #B7CBD7 | #C7D4DE | Pass | conservative candidate pairing; pill uses text |
| light | teal | danger-text | canvas/tint-accent | 3.920 | 4.367 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | high | canvas/tint-accent | 2.558 | 2.849 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | insufficient | canvas/tint-accent | 1.512 | 1.685 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | low | canvas/tint-accent | 2.011 | 2.240 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | medium | canvas/tint-accent | 1.281 | 1.427 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | muted | canvas/tint-accent | 3.959 | 4.410 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | noncompliant | canvas/tint-accent | 3.243 | 3.612 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | partial | canvas/tint-accent | 1.281 | 1.427 | #B7CBD7 | #C7D4DE | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | text | canvas/tint-accent | 10.388 | 11.571 | #B7CBD7 | #C7D4DE | Pass | conservative candidate pairing; pill uses text |
| light | teal | text-2 | canvas/tint-accent | 5.832 | 6.496 | #B7CBD7 | #C7D4DE | Pass | conservative candidate pairing; pill uses text |
| light | teal | accent-text | canvas/accent-soft | 5.048 | 5.048 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text | canvas/accent-soft | 14.870 | 14.870 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text-2 | canvas/accent-soft | 8.348 | 8.348 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | muted | canvas/accent-soft | 5.667 | 5.667 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | canvas-mid | glass/tint-accent | 1.063 | 1.107 | #D4E2E8 | #CDDEE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | compliant | glass/tint-accent | 2.737 | 2.850 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | critical | glass/tint-accent | 5.894 | 6.138 | #CDDEE6 | #D4E2E8 | Pass | conservative candidate pairing; pill uses text |
| light | teal | danger-text | glass/tint-accent | 4.754 | 4.951 | #CDDEE6 | #D4E2E8 | Pass | conservative candidate pairing; pill uses text |
| light | teal | high | glass/tint-accent | 3.102 | 3.230 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | insufficient | glass/tint-accent | 1.834 | 1.910 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | low | glass/tint-accent | 2.439 | 2.540 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | medium | glass/tint-accent | 1.553 | 1.618 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | muted | glass/tint-accent | 4.801 | 5.000 | #CDDEE6 | #D4E2E8 | Pass | conservative candidate pairing; pill uses text |
| light | teal | noncompliant | glass/tint-accent | 3.933 | 4.096 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | partial | glass/tint-accent | 1.553 | 1.618 | #CDDEE6 | #D4E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | text | glass/tint-accent | 12.598 | 13.120 | #CDDEE6 | #D4E2E8 | Pass | conservative candidate pairing; pill uses text |
| light | teal | text-2 | glass/tint-accent | 7.073 | 7.366 | #CDDEE6 | #D4E2E8 | Pass | conservative candidate pairing; pill uses text |
| light | teal | accent-text | glass/accent-soft | 5.048 | 5.048 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text | glass/accent-soft | 14.870 | 14.870 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text-2 | glass/accent-soft | 8.348 | 8.348 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | muted | glass/accent-soft | 5.667 | 5.667 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | canvas-mid | glass-strong/tint-accent | 1.033 | 1.060 | #D7E5EA | #D2E2E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | compliant | glass-strong/tint-accent | 2.857 | 2.933 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | critical | glass-strong/tint-accent | 6.153 | 6.315 | #D2E2E8 | #D7E5EA | Pass | conservative candidate pairing; pill uses text |
| light | teal | danger-text | glass-strong/tint-accent | 4.963 | 5.094 | #D2E2E8 | #D7E5EA | Pass | conservative candidate pairing; pill uses text |
| light | teal | high | glass-strong/tint-accent | 3.238 | 3.324 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | insufficient | glass-strong/tint-accent | 1.915 | 1.965 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | low | glass-strong/tint-accent | 2.546 | 2.613 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | medium | glass-strong/tint-accent | 1.622 | 1.664 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | muted | glass-strong/tint-accent | 5.012 | 5.145 | #D2E2E8 | #D7E5EA | Pass | conservative candidate pairing; pill uses text |
| light | teal | noncompliant | glass-strong/tint-accent | 4.106 | 4.214 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | partial | glass-strong/tint-accent | 1.622 | 1.664 | #D2E2E8 | #D7E5EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | text | glass-strong/tint-accent | 13.151 | 13.498 | #D2E2E8 | #D7E5EA | Pass | conservative candidate pairing; pill uses text |
| light | teal | text-2 | glass-strong/tint-accent | 7.384 | 7.578 | #D2E2E8 | #D7E5EA | Pass | conservative candidate pairing; pill uses text |
| light | teal | accent-text | glass-strong/accent-soft | 5.048 | 5.048 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text | glass-strong/accent-soft | 14.870 | 14.870 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text-2 | glass-strong/accent-soft | 8.348 | 8.348 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | muted | glass-strong/accent-soft | 5.667 | 5.667 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | canvas-mid | solid/tint-accent | 1.000 | 1.010 | #DBE8EC | #D9E8EB | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | compliant | solid/tint-accent | 2.999 | 3.028 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | critical | solid/tint-accent | 6.458 | 6.522 | #D9E8EB | #DBE8EC | Pass | conservative candidate pairing; pill uses text |
| light | teal | danger-text | solid/tint-accent | 5.209 | 5.261 | #D9E8EB | #DBE8EC | Pass | conservative candidate pairing; pill uses text |
| light | teal | high | solid/tint-accent | 3.398 | 3.432 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | insufficient | solid/tint-accent | 2.010 | 2.029 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | low | solid/tint-accent | 2.672 | 2.699 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | medium | solid/tint-accent | 1.702 | 1.719 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | muted | solid/tint-accent | 5.261 | 5.313 | #D9E8EB | #DBE8EC | Pass | conservative candidate pairing; pill uses text |
| light | teal | noncompliant | solid/tint-accent | 4.309 | 4.352 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | partial | solid/tint-accent | 1.702 | 1.719 | #D9E8EB | #DBE8EC | Fail candidate | conservative candidate pairing; pill uses text |
| light | teal | text | solid/tint-accent | 13.803 | 13.940 | #D9E8EB | #DBE8EC | Pass | conservative candidate pairing; pill uses text |
| light | teal | text-2 | solid/tint-accent | 7.749 | 7.826 | #D9E8EB | #DBE8EC | Pass | conservative candidate pairing; pill uses text |
| light | teal | accent-text | solid/accent-soft | 5.048 | 5.048 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text | solid/accent-soft | 14.870 | 14.870 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | text-2 | solid/accent-soft | 8.348 | 8.348 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | muted | solid/accent-soft | 5.667 | 5.667 | #E4EFF1 | #E4EFF1 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | teal | on-accent | primary-button | 4.440 | 5.914 | #2D8291 | #0B6E7F | Fail candidate | declared component pairing |
| light | teal | on-accent | primary-kbd | 3.368 | 4.263 | #4F96A3 | #328593 | Fail candidate | declared component pairing |
| light | violet | accent-text | canvas | 4.616 | 5.196 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass | 5.694 | 5.952 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong | 5.966 | 6.138 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | violet | accent-text | solid | 6.286 | 6.354 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/hover | 4.261 | 4.787 | #CBD2DD | #DDDCE6 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/press | 3.997 | 4.484 | #C5CBD7 | #D6D6DF | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/track | 4.071 | 4.569 | #C6CDD9 | #D8D7E1 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/field | 5.504 | 5.822 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/field-hover | 5.887 | 6.084 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/field-focus | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/chip | 5.887 | 6.084 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/nav-selected | 6.327 | 6.382 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/secondary-button | 6.246 | 6.327 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/secondary-hover | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/secondary-active | 5.907 | 5.907 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/file-button | 6.246 | 6.327 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/segment-selected | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/kbd | 5.855 | 6.492 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-critical | 3.671 | 4.107 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-high | 3.919 | 4.375 | #D4C6C9 | #E4CFD1 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-medium | 4.318 | 4.799 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-low | 4.112 | 4.571 | #BED1D4 | #CEDBDC | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-compliant | 4.057 | 4.512 | #BCD0D3 | #CCDADB | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-partial | 4.318 | 4.799 | #D7D2CC | #E7DBD3 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-noncompliant | 3.834 | 4.283 | #D0C3CB | #E1CDD3 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/tint-insufficient | 4.281 | 4.754 | #CBD2DE | #DBDCE6 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | canvas/mark | 4.009 | 4.385 | #DCC9AF | #E9D0B5 | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | glass/hover | 5.239 | 5.473 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/press | 4.902 | 5.118 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/track | 4.997 | 5.218 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/field | 6.085 | 6.219 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/field-hover | 6.246 | 6.327 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/field-focus | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/chip | 6.246 | 6.327 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/nav-selected | 6.426 | 6.448 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/secondary-button | 6.393 | 6.426 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/secondary-hover | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/secondary-active | 5.907 | 5.907 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/file-button | 6.393 | 6.426 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/segment-selected | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/kbd | 5.855 | 6.492 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-critical | 4.473 | 4.667 | #E1D3D8 | #E8D6DA | Fail candidate | conservative candidate pairing |
| light | violet | accent-text | glass/tint-high | 4.755 | 4.957 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-medium | 5.204 | 5.416 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-low | 4.967 | 5.169 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-compliant | 4.906 | 5.106 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-partial | 5.204 | 5.416 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-noncompliant | 4.658 | 4.858 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/tint-insufficient | 5.158 | 5.367 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass/mark | 4.693 | 4.857 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/hover | 5.486 | 5.642 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/press | 5.129 | 5.274 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/track | 5.230 | 5.377 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/field | 6.225 | 6.314 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/field-hover | 6.331 | 6.385 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/field-focus | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/chip | 6.331 | 6.385 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/nav-selected | 6.449 | 6.463 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/secondary-button | 6.428 | 6.449 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/secondary-hover | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/secondary-active | 5.907 | 5.907 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/file-button | 6.428 | 6.449 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/segment-selected | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/kbd | 5.855 | 6.492 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-critical | 4.675 | 4.805 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-high | 4.965 | 5.100 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-medium | 5.426 | 5.567 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-low | 5.181 | 5.316 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-compliant | 5.118 | 5.251 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-partial | 5.426 | 5.567 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-noncompliant | 4.865 | 4.998 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/tint-insufficient | 5.378 | 5.516 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | violet | accent-text | glass-strong/mark | 4.863 | 4.972 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/hover | 5.776 | 5.838 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/press | 5.398 | 5.455 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/track | 5.504 | 5.563 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/field | 6.389 | 6.423 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/field-hover | 6.430 | 6.451 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/field-focus | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/chip | 6.430 | 6.451 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/nav-selected | 6.476 | 6.481 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/secondary-button | 6.467 | 6.476 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/secondary-hover | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/secondary-active | 5.907 | 5.907 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/file-button | 6.467 | 6.476 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/segment-selected | 6.492 | 6.492 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/kbd | 5.855 | 6.492 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-critical | 4.913 | 4.964 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-high | 5.213 | 5.266 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-medium | 5.687 | 5.743 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-low | 5.433 | 5.486 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-compliant | 5.368 | 5.420 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-partial | 5.687 | 5.743 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-noncompliant | 5.110 | 5.162 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/tint-insufficient | 5.636 | 5.691 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | violet | accent-text | solid/mark | 5.062 | 5.105 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | violet | accent-text | modal-over-scrim | 5.958 | 6.003 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | violet | canvas-mid | canvas/tint-accent | 1.217 | 1.358 | #D5CEEA | #C4C4E2 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | compliant | canvas/tint-accent | 2.231 | 2.489 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | critical | canvas/tint-accent | 4.804 | 5.360 | #C4C4E2 | #D5CEEA | Pass | conservative candidate pairing; pill uses text |
| light | violet | danger-text | canvas/tint-accent | 3.875 | 4.323 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | high | canvas/tint-accent | 2.528 | 2.821 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | insufficient | canvas/tint-accent | 1.495 | 1.668 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | low | canvas/tint-accent | 1.988 | 2.218 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | medium | canvas/tint-accent | 1.266 | 1.413 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | muted | canvas/tint-accent | 3.913 | 4.366 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | noncompliant | canvas/tint-accent | 3.205 | 3.576 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | partial | canvas/tint-accent | 1.266 | 1.413 | #C4C4E2 | #D5CEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | text | canvas/tint-accent | 10.267 | 11.456 | #C4C4E2 | #D5CEEA | Pass | conservative candidate pairing; pill uses text |
| light | violet | text-2 | canvas/tint-accent | 5.764 | 6.432 | #C4C4E2 | #D5CEEA | Pass | conservative candidate pairing; pill uses text |
| light | violet | accent-text | canvas/accent-soft | 5.500 | 5.500 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text | canvas/accent-soft | 14.758 | 14.758 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text-2 | canvas/accent-soft | 8.285 | 8.285 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | muted | canvas/accent-soft | 5.625 | 5.625 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | canvas-mid | glass/tint-accent | 1.073 | 1.118 | #E2DBF4 | #DAD7F1 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | compliant | glass/tint-accent | 2.708 | 2.822 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | critical | glass/tint-accent | 5.832 | 6.078 | #DAD7F1 | #E2DBF4 | Pass | conservative candidate pairing; pill uses text |
| light | violet | danger-text | glass/tint-accent | 4.704 | 4.903 | #DAD7F1 | #E2DBF4 | Pass | conservative candidate pairing; pill uses text |
| light | violet | high | glass/tint-accent | 3.069 | 3.199 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | insufficient | glass/tint-accent | 1.815 | 1.891 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | low | glass/tint-accent | 2.413 | 2.515 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | medium | glass/tint-accent | 1.537 | 1.602 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | muted | glass/tint-accent | 4.751 | 4.951 | #DAD7F1 | #E2DBF4 | Pass | conservative candidate pairing; pill uses text |
| light | violet | noncompliant | glass/tint-accent | 3.891 | 4.056 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | partial | glass/tint-accent | 1.537 | 1.602 | #DAD7F1 | #E2DBF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | text | glass/tint-accent | 12.465 | 12.991 | #DAD7F1 | #E2DBF4 | Pass | conservative candidate pairing; pill uses text |
| light | violet | text-2 | glass/tint-accent | 6.998 | 7.294 | #DAD7F1 | #E2DBF4 | Pass | conservative candidate pairing; pill uses text |
| light | violet | accent-text | glass/accent-soft | 5.500 | 5.500 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text | glass/accent-soft | 14.758 | 14.758 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text-2 | glass/accent-soft | 8.285 | 8.285 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | muted | glass/accent-soft | 5.625 | 5.625 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | canvas-mid | glass-strong/tint-accent | 1.043 | 1.071 | #E5DEF5 | #E0DCF4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | compliant | glass-strong/tint-accent | 2.828 | 2.904 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | critical | glass-strong/tint-accent | 6.090 | 6.254 | #E0DCF4 | #E5DEF5 | Pass | conservative candidate pairing; pill uses text |
| light | violet | danger-text | glass-strong/tint-accent | 4.912 | 5.044 | #E0DCF4 | #E5DEF5 | Pass | conservative candidate pairing; pill uses text |
| light | violet | high | glass-strong/tint-accent | 3.205 | 3.291 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | insufficient | glass-strong/tint-accent | 1.895 | 1.946 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | low | glass-strong/tint-accent | 2.520 | 2.587 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | medium | glass-strong/tint-accent | 1.605 | 1.648 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | muted | glass-strong/tint-accent | 4.961 | 5.094 | #E0DCF4 | #E5DEF5 | Pass | conservative candidate pairing; pill uses text |
| light | violet | noncompliant | glass-strong/tint-accent | 4.064 | 4.173 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | partial | glass-strong/tint-accent | 1.605 | 1.648 | #E0DCF4 | #E5DEF5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | text | glass-strong/tint-accent | 13.016 | 13.366 | #E0DCF4 | #E5DEF5 | Pass | conservative candidate pairing; pill uses text |
| light | violet | text-2 | glass-strong/tint-accent | 7.308 | 7.504 | #E0DCF4 | #E5DEF5 | Pass | conservative candidate pairing; pill uses text |
| light | violet | accent-text | glass-strong/accent-soft | 5.500 | 5.500 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text | glass-strong/accent-soft | 14.758 | 14.758 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text-2 | glass-strong/accent-soft | 8.285 | 8.285 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | muted | glass-strong/accent-soft | 5.625 | 5.625 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | canvas-mid | solid/tint-accent | 1.010 | 1.020 | #E8E2F7 | #E6E1F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | compliant | solid/tint-accent | 2.969 | 2.999 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | critical | solid/tint-accent | 6.393 | 6.458 | #E6E1F7 | #E8E2F7 | Pass | conservative candidate pairing; pill uses text |
| light | violet | danger-text | solid/tint-accent | 5.157 | 5.209 | #E6E1F7 | #E8E2F7 | Pass | conservative candidate pairing; pill uses text |
| light | violet | high | solid/tint-accent | 3.365 | 3.399 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | insufficient | solid/tint-accent | 1.989 | 2.010 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | low | solid/tint-accent | 2.645 | 2.672 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | medium | solid/tint-accent | 1.685 | 1.702 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | muted | solid/tint-accent | 5.208 | 5.261 | #E6E1F7 | #E8E2F7 | Pass | conservative candidate pairing; pill uses text |
| light | violet | noncompliant | solid/tint-accent | 4.266 | 4.309 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | partial | solid/tint-accent | 1.685 | 1.702 | #E6E1F7 | #E8E2F7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | violet | text | solid/tint-accent | 13.665 | 13.803 | #E6E1F7 | #E8E2F7 | Pass | conservative candidate pairing; pill uses text |
| light | violet | text-2 | solid/tint-accent | 7.672 | 7.750 | #E6E1F7 | #E8E2F7 | Pass | conservative candidate pairing; pill uses text |
| light | violet | accent-text | solid/accent-soft | 5.500 | 5.500 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text | solid/accent-soft | 14.758 | 14.758 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | text-2 | solid/accent-soft | 8.285 | 8.285 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | muted | solid/accent-soft | 5.625 | 5.625 | #EFEAFA | #EFEAFA | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | violet | on-accent | primary-button | 4.844 | 6.492 | #7F5AD7 | #6A3FD0 | Pass | declared component pairing |
| light | violet | on-accent | primary-kbd | 3.618 | 4.642 | #9374DD | #825ED8 | Fail candidate | declared component pairing |
| light | plum | accent-text | canvas | 5.612 | 6.318 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass | 6.923 | 7.238 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong | 7.254 | 7.463 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | plum | accent-text | solid | 7.644 | 7.727 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/hover | 5.181 | 5.821 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/press | 4.860 | 5.452 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/track | 4.950 | 5.556 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/field | 6.692 | 7.079 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/field-hover | 7.158 | 7.398 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/field-focus | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/chip | 7.158 | 7.398 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/nav-selected | 7.693 | 7.760 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/secondary-button | 7.594 | 7.693 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/secondary-hover | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/secondary-active | 7.182 | 7.182 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/file-button | 7.594 | 7.693 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/segment-selected | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/kbd | 7.119 | 7.894 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-critical | 4.463 | 4.994 | #CBBFC9 | #DBC9D1 | Fail candidate | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-high | 4.765 | 5.320 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-medium | 5.250 | 5.836 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-low | 5.000 | 5.557 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-compliant | 4.933 | 5.486 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-partial | 5.250 | 5.836 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-noncompliant | 4.662 | 5.208 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/tint-insufficient | 5.205 | 5.781 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | plum | accent-text | canvas/mark | 4.875 | 5.332 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/hover | 6.370 | 6.655 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/press | 5.960 | 6.223 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/track | 6.075 | 6.345 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/field | 7.399 | 7.561 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/field-hover | 7.594 | 7.693 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/field-focus | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/chip | 7.594 | 7.693 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/nav-selected | 7.813 | 7.840 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/secondary-button | 7.773 | 7.813 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/secondary-hover | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/secondary-active | 7.182 | 7.182 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/file-button | 7.773 | 7.813 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/segment-selected | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/kbd | 7.119 | 7.894 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-critical | 5.439 | 5.675 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-high | 5.781 | 6.028 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-medium | 6.327 | 6.586 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-low | 6.040 | 6.285 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-compliant | 5.965 | 6.208 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-partial | 6.327 | 6.586 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-noncompliant | 5.664 | 5.906 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/tint-insufficient | 6.272 | 6.526 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass/mark | 5.706 | 5.906 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/hover | 6.670 | 6.860 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/press | 6.237 | 6.412 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/track | 6.359 | 6.538 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/field | 7.570 | 7.677 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/field-hover | 7.698 | 7.763 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/field-focus | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/chip | 7.698 | 7.763 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/nav-selected | 7.842 | 7.859 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/secondary-button | 7.815 | 7.842 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/secondary-hover | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/secondary-active | 7.182 | 7.182 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/file-button | 7.815 | 7.842 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/segment-selected | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/kbd | 7.119 | 7.894 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-critical | 5.685 | 5.842 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-high | 6.037 | 6.201 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-medium | 6.598 | 6.769 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-low | 6.300 | 6.463 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-compliant | 6.223 | 6.385 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-partial | 6.598 | 6.769 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-noncompliant | 5.916 | 6.077 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/tint-insufficient | 6.539 | 6.708 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | plum | accent-text | glass-strong/mark | 5.913 | 6.045 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/hover | 7.024 | 7.099 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/press | 6.563 | 6.633 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/track | 6.693 | 6.764 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/field | 7.768 | 7.810 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/field-hover | 7.818 | 7.844 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/field-focus | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/chip | 7.818 | 7.844 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/nav-selected | 7.874 | 7.881 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/secondary-button | 7.864 | 7.874 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/secondary-hover | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/secondary-active | 7.182 | 7.182 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/file-button | 7.864 | 7.874 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/segment-selected | 7.894 | 7.894 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/kbd | 7.119 | 7.894 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-critical | 5.974 | 6.036 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-high | 6.338 | 6.403 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-medium | 6.915 | 6.983 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-low | 6.606 | 6.671 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-compliant | 6.527 | 6.590 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-partial | 6.915 | 6.983 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-noncompliant | 6.213 | 6.277 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/tint-insufficient | 6.853 | 6.919 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | plum | accent-text | solid/mark | 6.155 | 6.207 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | plum | accent-text | modal-over-scrim | 7.244 | 7.299 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | plum | canvas-mid | canvas/tint-accent | 1.240 | 1.386 | #D9CBDD | #C8C2D6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | compliant | canvas/tint-accent | 2.186 | 2.442 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | critical | canvas/tint-accent | 4.707 | 5.259 | #C8C2D6 | #D9CBDD | Pass | conservative candidate pairing; pill uses text |
| light | plum | danger-text | canvas/tint-accent | 3.797 | 4.242 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | high | canvas/tint-accent | 2.477 | 2.768 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | insufficient | canvas/tint-accent | 1.465 | 1.637 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | low | canvas/tint-accent | 1.947 | 2.176 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | medium | canvas/tint-accent | 1.241 | 1.386 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | muted | canvas/tint-accent | 3.834 | 4.284 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | noncompliant | canvas/tint-accent | 3.141 | 3.509 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | partial | canvas/tint-accent | 1.241 | 1.386 | #C8C2D6 | #D9CBDD | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | text | canvas/tint-accent | 10.060 | 11.241 | #C8C2D6 | #D9CBDD | Pass | conservative candidate pairing; pill uses text |
| light | plum | text-2 | canvas/tint-accent | 5.648 | 6.311 | #C8C2D6 | #D9CBDD | Pass | conservative candidate pairing; pill uses text |
| light | plum | accent-text | canvas/accent-soft | 6.599 | 6.599 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text | canvas/accent-soft | 14.563 | 14.563 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text-2 | canvas/accent-soft | 8.176 | 8.176 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | muted | canvas/accent-soft | 5.550 | 5.550 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | canvas-mid | glass/tint-accent | 1.093 | 1.139 | #E5D9E7 | #DED5E5 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | compliant | glass/tint-accent | 2.658 | 2.772 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | critical | glass/tint-accent | 5.725 | 5.970 | #DED5E5 | #E5D9E7 | Pass | conservative candidate pairing; pill uses text |
| light | plum | danger-text | glass/tint-accent | 4.618 | 4.816 | #DED5E5 | #E5D9E7 | Pass | conservative candidate pairing; pill uses text |
| light | plum | high | glass/tint-accent | 3.013 | 3.142 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | insufficient | glass/tint-accent | 1.781 | 1.858 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | low | glass/tint-accent | 2.369 | 2.470 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | medium | glass/tint-accent | 1.509 | 1.574 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | muted | glass/tint-accent | 4.664 | 4.863 | #DED5E5 | #E5D9E7 | Pass | conservative candidate pairing; pill uses text |
| light | plum | noncompliant | glass/tint-accent | 3.820 | 3.984 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | partial | glass/tint-accent | 1.509 | 1.574 | #DED5E5 | #E5D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | text | glass/tint-accent | 12.237 | 12.761 | #DED5E5 | #E5D9E7 | Pass | conservative candidate pairing; pill uses text |
| light | plum | text-2 | glass/tint-accent | 6.870 | 7.164 | #DED5E5 | #E5D9E7 | Pass | conservative candidate pairing; pill uses text |
| light | plum | accent-text | glass/accent-soft | 6.599 | 6.599 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text | glass/accent-soft | 14.563 | 14.563 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text-2 | glass/accent-soft | 8.176 | 8.176 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | muted | glass/accent-soft | 5.550 | 5.550 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | canvas-mid | glass-strong/tint-accent | 1.062 | 1.091 | #E8DCE9 | #E4D9E7 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | compliant | glass-strong/tint-accent | 2.777 | 2.853 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | critical | glass-strong/tint-accent | 5.981 | 6.144 | #E4D9E7 | #E8DCE9 | Pass | conservative candidate pairing; pill uses text |
| light | plum | danger-text | glass-strong/tint-accent | 4.824 | 4.956 | #E4D9E7 | #E8DCE9 | Pass | conservative candidate pairing; pill uses text |
| light | plum | high | glass-strong/tint-accent | 3.148 | 3.233 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | insufficient | glass-strong/tint-accent | 1.861 | 1.912 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | low | glass-strong/tint-accent | 2.475 | 2.542 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | medium | glass-strong/tint-accent | 1.576 | 1.619 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | muted | glass-strong/tint-accent | 4.872 | 5.005 | #E4D9E7 | #E8DCE9 | Pass | conservative candidate pairing; pill uses text |
| light | plum | noncompliant | glass-strong/tint-accent | 3.991 | 4.100 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | partial | glass-strong/tint-accent | 1.576 | 1.619 | #E4D9E7 | #E8DCE9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | text | glass-strong/tint-accent | 12.784 | 13.132 | #E4D9E7 | #E8DCE9 | Pass | conservative candidate pairing; pill uses text |
| light | plum | text-2 | glass-strong/tint-accent | 7.177 | 7.373 | #E4D9E7 | #E8DCE9 | Pass | conservative candidate pairing; pill uses text |
| light | plum | accent-text | glass-strong/accent-soft | 6.599 | 6.599 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text | glass-strong/accent-soft | 14.563 | 14.563 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text-2 | glass-strong/accent-soft | 8.176 | 8.176 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | muted | glass-strong/accent-soft | 5.550 | 5.550 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | canvas-mid | solid/tint-accent | 1.028 | 1.038 | #ECDFEB | #EADEEA | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | compliant | solid/tint-accent | 2.917 | 2.947 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | critical | solid/tint-accent | 6.282 | 6.347 | #EADEEA | #ECDFEB | Pass | conservative candidate pairing; pill uses text |
| light | plum | danger-text | solid/tint-accent | 5.068 | 5.120 | #EADEEA | #ECDFEB | Pass | conservative candidate pairing; pill uses text |
| light | plum | high | solid/tint-accent | 3.306 | 3.340 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | insufficient | solid/tint-accent | 1.955 | 1.975 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | low | solid/tint-accent | 2.599 | 2.626 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | medium | solid/tint-accent | 1.656 | 1.673 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | muted | solid/tint-accent | 5.118 | 5.170 | #EADEEA | #ECDFEB | Pass | conservative candidate pairing; pill uses text |
| light | plum | noncompliant | solid/tint-accent | 4.192 | 4.235 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | partial | solid/tint-accent | 1.656 | 1.673 | #EADEEA | #ECDFEB | Fail candidate | conservative candidate pairing; pill uses text |
| light | plum | text | solid/tint-accent | 13.428 | 13.566 | #EADEEA | #ECDFEB | Pass | conservative candidate pairing; pill uses text |
| light | plum | text-2 | solid/tint-accent | 7.539 | 7.616 | #EADEEA | #ECDFEB | Pass | conservative candidate pairing; pill uses text |
| light | plum | accent-text | solid/accent-soft | 6.599 | 6.599 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text | solid/accent-soft | 14.563 | 14.563 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | text-2 | solid/accent-soft | 8.176 | 8.176 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | muted | solid/accent-soft | 5.550 | 5.550 | #F2E8F0 | #F2E8F0 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | plum | on-accent | primary-button | 5.711 | 7.894 | #974A8B | #862D78 | Pass | declared component pairing |
| light | plum | on-accent | primary-kbd | 4.119 | 5.445 | #A8679D | #994F8E | Fail candidate | declared component pairing |
| light | slate | accent-text | canvas | 5.821 | 6.553 | #D3DAE5 | #E6E5EE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass | 7.181 | 7.507 | #ECF0F6 | #F5F4FA | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong | 7.524 | 7.741 | #F3F5F9 | #F9F8FB | Pass | conservative candidate pairing |
| light | slate | accent-text | solid | 7.928 | 8.014 | #FAFBFD | #FDFCFE | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/hover | 5.373 | 6.038 | #CBD2DD | #DDDCE6 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/press | 5.041 | 5.655 | #C5CBD7 | #D6D6DF | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/track | 5.134 | 5.763 | #C6CDD9 | #D8D7E1 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/field | 6.941 | 7.342 | #E9ECF2 | #F2F2F6 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/field-hover | 7.425 | 7.674 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/field-focus | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/chip | 7.425 | 7.674 | #F2F4F7 | #F8F7FA | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/nav-selected | 7.980 | 8.049 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/secondary-button | 7.877 | 7.980 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/secondary-hover | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/secondary-active | 7.450 | 7.450 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/file-button | 7.877 | 7.980 | #FAFBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/segment-selected | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/kbd | 7.384 | 8.188 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-critical | 4.629 | 5.180 | #CBBFC9 | #DBC9D1 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-high | 4.943 | 5.518 | #D4C6C9 | #E4CFD1 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-medium | 5.446 | 6.053 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-low | 5.186 | 5.764 | #BED1D4 | #CEDBDC | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-compliant | 5.117 | 5.690 | #BCD0D3 | #CCDADB | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-partial | 5.446 | 6.053 | #D7D2CC | #E7DBD3 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-noncompliant | 4.835 | 5.402 | #D0C3CB | #E1CDD3 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/tint-insufficient | 5.399 | 5.996 | #CBD2DE | #DBDCE6 | Pass | conservative candidate pairing |
| light | slate | accent-text | canvas/mark | 5.056 | 5.530 | #DCC9AF | #E9D0B5 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/hover | 6.607 | 6.903 | #E3E7EE | #EBEBF1 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/press | 6.182 | 6.455 | #DCE0E7 | #E4E4EA | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/track | 6.302 | 6.581 | #DEE2E9 | #E6E6EC | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/field | 7.674 | 7.843 | #F6F8FB | #FAFAFC | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/field-hover | 7.877 | 7.980 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/field-focus | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/chip | 7.877 | 7.980 | #F9FBFC | #FCFCFD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/nav-selected | 8.104 | 8.132 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/secondary-button | 8.063 | 8.104 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/secondary-hover | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/secondary-active | 7.450 | 7.450 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/file-button | 8.063 | 8.104 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/segment-selected | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/kbd | 7.384 | 8.188 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-critical | 5.641 | 5.886 | #E1D3D8 | #E8D6DA | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-high | 5.997 | 6.252 | #EAD9D8 | #F1DCDB | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-medium | 6.563 | 6.831 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-low | 6.265 | 6.519 | #D4E5E3 | #DBE8E6 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-compliant | 6.187 | 6.439 | #D2E3E2 | #D9E7E5 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-partial | 6.563 | 6.831 | #EDE5DB | #F4E9DD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-noncompliant | 5.875 | 6.126 | #E6D7DA | #EEDADD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/tint-insufficient | 6.506 | 6.769 | #E1E5ED | #E8E9F0 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass/mark | 5.918 | 6.125 | #EDD8BB | #F4DBBD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/hover | 6.918 | 7.115 | #E9ECF1 | #EFEFF3 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/press | 6.469 | 6.651 | #E2E5EA | #E7E7EC | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/track | 6.596 | 6.782 | #E4E7EC | #E9E9EE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/field | 7.851 | 7.963 | #F9FAFC | #FCFCFD | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/field-hover | 7.985 | 8.052 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/field-focus | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/chip | 7.985 | 8.052 | #FBFCFD | #FDFDFE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/nav-selected | 8.133 | 8.152 | #FEFEFF | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/secondary-button | 8.106 | 8.133 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/secondary-hover | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/secondary-active | 7.450 | 7.450 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/file-button | 8.106 | 8.133 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/segment-selected | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/kbd | 7.384 | 8.188 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-critical | 5.896 | 6.059 | #E7D7DA | #EBD9DC | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-high | 6.262 | 6.432 | #EFDDDB | #F4DFDC | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-medium | 6.843 | 7.021 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-low | 6.535 | 6.704 | #D9E9E6 | #DEEBE7 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-compliant | 6.455 | 6.622 | #D7E8E5 | #DCEAE7 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-partial | 6.843 | 7.021 | #F2E9DD | #F7ECDF | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-noncompliant | 6.136 | 6.304 | #ECDBDD | #F1DDDE | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/tint-insufficient | 6.782 | 6.957 | #E6EAF0 | #EBECF2 | Pass | conservative candidate pairing |
| light | slate | accent-text | glass-strong/mark | 6.133 | 6.270 | #F2DCBD | #F6DEBE | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/hover | 7.285 | 7.363 | #F0F2F4 | #F2F3F5 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/press | 6.808 | 6.880 | #E9EAED | #EBEBEE | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/track | 6.942 | 7.016 | #EBECEF | #EDEDF0 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/field | 8.057 | 8.101 | #FDFDFE | #FEFEFE | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/field-hover | 8.109 | 8.136 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/field-focus | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/chip | 8.109 | 8.136 | #FEFEFE | #FEFEFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/nav-selected | 8.167 | 8.174 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/secondary-button | 8.156 | 8.167 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/secondary-hover | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/secondary-active | 7.450 | 7.450 | #F3F4F8 | #F3F4F8 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/file-button | 8.156 | 8.167 | #FEFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/segment-selected | 8.188 | 8.188 | #FFFFFF | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/kbd | 7.384 | 8.188 | #F2F3F7 | #FFFFFF | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-critical | 6.197 | 6.261 | #EDDCDD | #EFDDDE | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-high | 6.574 | 6.641 | #F6E2DE | #F8E3DE | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-medium | 7.172 | 7.243 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-low | 6.852 | 6.919 | #E0EEE8 | #E2EFE9 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-compliant | 6.770 | 6.836 | #DEEDE8 | #E0EEE8 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-partial | 7.172 | 7.243 | #F9EFE0 | #FBEFE1 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-noncompliant | 6.444 | 6.510 | #F2E0DF | #F4E1E0 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/tint-insufficient | 7.108 | 7.177 | #EDEFF3 | #EFF0F3 | Pass | conservative candidate pairing |
| light | slate | accent-text | solid/mark | 6.384 | 6.438 | #F7E0BF | #F9E1C0 | Pass | conservative candidate pairing |
| light | slate | accent-text | modal-over-scrim | 7.514 | 7.570 | #F4F5F7 | #F6F6F7 | Pass | conservative candidate pairing |
| light | slate | canvas-mid | canvas/tint-accent | 1.227 | 1.369 | #CED0DC | #BEC7D4 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | compliant | canvas/tint-accent | 2.213 | 2.469 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | critical | canvas/tint-accent | 4.766 | 5.317 | #BEC7D4 | #CED0DC | Pass | conservative candidate pairing; pill uses text |
| light | slate | danger-text | canvas/tint-accent | 3.844 | 4.289 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | high | canvas/tint-accent | 2.508 | 2.798 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | insufficient | canvas/tint-accent | 1.483 | 1.655 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | low | canvas/tint-accent | 1.972 | 2.200 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | medium | canvas/tint-accent | 1.256 | 1.401 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | muted | canvas/tint-accent | 3.882 | 4.332 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | noncompliant | canvas/tint-accent | 3.180 | 3.548 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | partial | canvas/tint-accent | 1.256 | 1.401 | #BEC7D4 | #CED0DC | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | text | canvas/tint-accent | 10.187 | 11.365 | #BEC7D4 | #CED0DC | Pass | conservative candidate pairing; pill uses text |
| light | slate | text-2 | canvas/tint-accent | 5.719 | 6.381 | #BEC7D4 | #CED0DC | Pass | conservative candidate pairing; pill uses text |
| light | slate | accent-text | canvas/accent-soft | 6.901 | 6.901 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text | canvas/accent-soft | 14.683 | 14.683 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text-2 | canvas/accent-soft | 8.243 | 8.243 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | muted | canvas/accent-soft | 5.596 | 5.596 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | canvas-mid | glass/tint-accent | 1.081 | 1.127 | #DBDDE6 | #D4DAE3 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | compliant | glass/tint-accent | 2.689 | 2.802 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | critical | glass/tint-accent | 5.790 | 6.034 | #D4DAE3 | #DBDDE6 | Pass | conservative candidate pairing; pill uses text |
| light | slate | danger-text | glass/tint-accent | 4.670 | 4.867 | #D4DAE3 | #DBDDE6 | Pass | conservative candidate pairing; pill uses text |
| light | slate | high | glass/tint-accent | 3.047 | 3.175 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | insufficient | glass/tint-accent | 1.802 | 1.878 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | low | glass/tint-accent | 2.396 | 2.497 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | medium | glass/tint-accent | 1.526 | 1.590 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | muted | glass/tint-accent | 4.717 | 4.915 | #D4DAE3 | #DBDDE6 | Pass | conservative candidate pairing; pill uses text |
| light | slate | noncompliant | glass/tint-accent | 3.863 | 4.026 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | partial | glass/tint-accent | 1.526 | 1.590 | #D4DAE3 | #DBDDE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | text | glass/tint-accent | 12.376 | 12.897 | #D4DAE3 | #DBDDE6 | Pass | conservative candidate pairing; pill uses text |
| light | slate | text-2 | glass/tint-accent | 6.948 | 7.241 | #D4DAE3 | #DBDDE6 | Pass | conservative candidate pairing; pill uses text |
| light | slate | accent-text | glass/accent-soft | 6.901 | 6.901 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text | glass/accent-soft | 14.683 | 14.683 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text-2 | glass/accent-soft | 8.243 | 8.243 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | muted | glass/accent-soft | 5.596 | 5.596 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | canvas-mid | glass-strong/tint-accent | 1.051 | 1.079 | #DEE1E8 | #D9DEE6 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | compliant | glass-strong/tint-accent | 2.808 | 2.883 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | critical | glass-strong/tint-accent | 6.047 | 6.209 | #D9DEE6 | #DEE1E8 | Pass | conservative candidate pairing; pill uses text |
| light | slate | danger-text | glass-strong/tint-accent | 4.878 | 5.009 | #D9DEE6 | #DEE1E8 | Pass | conservative candidate pairing; pill uses text |
| light | slate | high | glass-strong/tint-accent | 3.182 | 3.268 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | insufficient | glass-strong/tint-accent | 1.882 | 1.932 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | low | glass-strong/tint-accent | 2.502 | 2.569 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | medium | glass-strong/tint-accent | 1.594 | 1.637 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | muted | glass-strong/tint-accent | 4.926 | 5.058 | #D9DEE6 | #DEE1E8 | Pass | conservative candidate pairing; pill uses text |
| light | slate | noncompliant | glass-strong/tint-accent | 4.035 | 4.143 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | partial | glass-strong/tint-accent | 1.594 | 1.637 | #D9DEE6 | #DEE1E8 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | text | glass-strong/tint-accent | 12.925 | 13.272 | #D9DEE6 | #DEE1E8 | Pass | conservative candidate pairing; pill uses text |
| light | slate | text-2 | glass-strong/tint-accent | 7.256 | 7.451 | #D9DEE6 | #DEE1E8 | Pass | conservative candidate pairing; pill uses text |
| light | slate | accent-text | glass-strong/accent-soft | 6.901 | 6.901 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text | glass-strong/accent-soft | 14.683 | 14.683 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text-2 | glass-strong/accent-soft | 8.243 | 8.243 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | muted | glass-strong/accent-soft | 5.596 | 5.596 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | canvas-mid | solid/tint-accent | 1.017 | 1.027 | #E2E4EA | #E0E3E9 | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | compliant | solid/tint-accent | 2.948 | 2.978 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | critical | solid/tint-accent | 6.350 | 6.414 | #E0E3E9 | #E2E4EA | Pass | conservative candidate pairing; pill uses text |
| light | slate | danger-text | solid/tint-accent | 5.122 | 5.173 | #E0E3E9 | #E2E4EA | Pass | conservative candidate pairing; pill uses text |
| light | slate | high | solid/tint-accent | 3.341 | 3.375 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | insufficient | solid/tint-accent | 1.976 | 1.996 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | low | solid/tint-accent | 2.627 | 2.654 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | medium | solid/tint-accent | 1.673 | 1.690 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | muted | solid/tint-accent | 5.172 | 5.225 | #E0E3E9 | #E2E4EA | Pass | conservative candidate pairing; pill uses text |
| light | slate | noncompliant | solid/tint-accent | 4.237 | 4.280 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | partial | solid/tint-accent | 1.673 | 1.690 | #E0E3E9 | #E2E4EA | Fail candidate | conservative candidate pairing; pill uses text |
| light | slate | text | solid/tint-accent | 13.571 | 13.708 | #E0E3E9 | #E2E4EA | Pass | conservative candidate pairing; pill uses text |
| light | slate | text-2 | solid/tint-accent | 7.619 | 7.696 | #E0E3E9 | #E2E4EA | Pass | conservative candidate pairing; pill uses text |
| light | slate | accent-text | solid/accent-soft | 6.901 | 6.901 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text | solid/accent-soft | 14.683 | 14.683 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | text-2 | solid/accent-soft | 8.243 | 8.243 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | muted | solid/accent-soft | 5.596 | 5.596 | #EAECEF | #EAECEF | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| light | slate | on-accent | primary-button | 5.626 | 8.188 | #576882 | #3C506E | Pass | declared component pairing |
| light | slate | on-accent | primary-kbd | 3.979 | 5.341 | #728196 | #5B6C85 | Fail candidate | declared component pairing |
| light | all | canvas-mid | tooltip | 13.942 | 13.942 | #141A26 | #141A26 | Pass | declared component pairing |
| light | all | literal-white | destructive-button | 5.438 | 5.438 | #C0392B | #C0392B | Pass | declared component pairing |
| dark | all | canvas-mid | canvas | 1.000 | 1.059 | #1C1D2A | #28202C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass | 1.167 | 1.245 | #282938 | #352C39 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong | 1.263 | 1.349 | #2E2F3D | #3A313F | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid | 1.076 | 1.081 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/hover | 1.149 | 1.225 | #272835 | #332B37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/press | 1.304 | 1.392 | #30313D | #3B343F | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/track | 1.304 | 1.392 | #30313D | #3B343F | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/field | 1.149 | 1.225 | #272835 | #332B37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/field-hover | 8.731 | 8.869 | #BBBBBF | #BEBCC0 | Pass | conservative candidate pairing |
| dark | all | canvas-mid | canvas/field-focus | 1.262 | 1.347 | #2E2F3B | #39323D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/chip | 1.149 | 1.225 | #272835 | #332B37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/nav-selected | 1.304 | 1.392 | #30313D | #3B343F | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/secondary-button | 1.222 | 1.305 | #2C2D39 | #37303B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/secondary-hover | 1.393 | 1.488 | #353641 | #403943 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/secondary-active | 1.149 | 1.225 | #272835 | #332B37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/file-button | 1.347 | 1.439 | #33343F | #3E3641 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/segment-selected | 1.544 | 1.648 | #3C3D48 | #463F4A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/kbd | 1.262 | 1.347 | #2E2F3B | #39323D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-critical | 1.089 | 1.156 | #381D27 | #411F28 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-high | 1.248 | 1.333 | #462627 | #4F2929 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-medium | 1.536 | 1.640 | #4B3A2B | #543C2D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-low | 1.365 | 1.435 | #233938 | #2C3C3A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-compliant | 1.325 | 1.391 | #203737 | #2A3A39 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-partial | 1.536 | 1.640 | #4B3A2B | #543C2D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-noncompliant | 1.188 | 1.266 | #40232A | #49262C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/tint-insufficient | 1.491 | 1.580 | #383A49 | #413D4A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | canvas/mark | 2.023 | 2.143 | #644A2C | #6C4C2D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/hover | 1.358 | 1.452 | #333442 | #3F3643 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/press | 1.546 | 1.650 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/track | 1.546 | 1.650 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/field | 1.358 | 1.452 | #333442 | #3F3643 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/field-hover | 9.087 | 9.221 | #BFBFC3 | #C2C0C4 | Pass | conservative candidate pairing |
| dark | all | canvas-mid | glass/field-focus | 1.496 | 1.598 | #393A48 | #453D49 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/chip | 1.358 | 1.452 | #333442 | #3F3643 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/nav-selected | 1.546 | 1.650 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/secondary-button | 1.448 | 1.547 | #373846 | #433B47 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/secondary-hover | 1.651 | 1.761 | #40414E | #4B434F | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/secondary-active | 1.358 | 1.452 | #333442 | #3F3643 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/file-button | 1.597 | 1.705 | #3E3F4C | #49414D | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/segment-selected | 1.825 | 1.943 | #464754 | #514955 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/kbd | 1.496 | 1.598 | #393A48 | #453D49 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-critical | 1.236 | 1.317 | #412632 | #4B2833 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-high | 1.433 | 1.533 | #4F3032 | #593233 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-medium | 1.783 | 1.900 | #544336 | #5E4537 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-low | 1.580 | 1.658 | #2D4343 | #364544 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-compliant | 1.531 | 1.606 | #2A4142 | #344343 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-partial | 1.783 | 1.900 | #544336 | #5E4537 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-noncompliant | 1.359 | 1.452 | #4A2D35 | #532F36 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/tint-insufficient | 1.733 | 1.832 | #414454 | #4B4655 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass/mark | 2.294 | 2.423 | #6C5235 | #745336 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/hover | 1.472 | 1.573 | #383947 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/press | 1.674 | 1.785 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/track | 1.674 | 1.785 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/field | 1.472 | 1.573 | #383947 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/field-hover | 9.252 | 9.384 | #C0C1C5 | #C4C1C5 | Pass | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/field-focus | 1.620 | 1.729 | #3F404D | #4A424E | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/chip | 1.472 | 1.573 | #383947 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/nav-selected | 1.674 | 1.785 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/secondary-button | 1.569 | 1.675 | #3C3E4B | #48404C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/secondary-hover | 1.786 | 1.902 | #454653 | #504854 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/secondary-active | 1.472 | 1.573 | #383947 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/file-button | 1.729 | 1.842 | #434451 | #4E4652 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/segment-selected | 1.969 | 2.093 | #4B4C58 | #564E5A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/kbd | 1.620 | 1.729 | #3F404D | #4A424E | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-critical | 1.315 | 1.400 | #462B36 | #4F2D37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-high | 1.530 | 1.634 | #533436 | #5D3637 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-medium | 1.911 | 2.032 | #59483A | #624A3B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-low | 1.691 | 1.774 | #314747 | #3B4948 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-compliant | 1.638 | 1.717 | #2E4546 | #384747 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-partial | 1.911 | 2.032 | #59483A | #624A3B | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-noncompliant | 1.450 | 1.547 | #4E3139 | #58333A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/tint-insufficient | 1.857 | 1.960 | #464858 | #4F4A59 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | glass-strong/mark | 2.429 | 2.560 | #705539 | #78573A | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/hover | 1.047 | 1.054 | #1F222C | #20222C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/press | 1.181 | 1.190 | #282B35 | #2A2B35 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/track | 1.181 | 1.190 | #282B35 | #2A2B35 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/field | 1.047 | 1.054 | #1F222C | #20222C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/field-hover | 8.517 | 8.533 | #B8B9BC | #B9B9BC | Pass | conservative candidate pairing |
| dark | all | canvas-mid | solid/field-focus | 1.145 | 1.153 | #262932 | #282933 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/chip | 1.047 | 1.054 | #1F222C | #20222C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/nav-selected | 1.181 | 1.190 | #282B35 | #2A2B35 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/secondary-button | 1.110 | 1.118 | #242630 | #252730 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/secondary-hover | 1.261 | 1.270 | #2D3039 | #2F3039 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/secondary-active | 1.047 | 1.054 | #1F222C | #20222C | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/file-button | 1.220 | 1.229 | #2B2D37 | #2C2E37 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/segment-selected | 1.397 | 1.408 | #343740 | #363740 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/kbd | 1.145 | 1.153 | #262932 | #282933 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-critical | 1.014 | 1.021 | #311720 | #321820 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-high | 1.150 | 1.159 | #3F2120 | #402120 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-medium | 1.403 | 1.414 | #443424 | #453524 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-low | 1.255 | 1.261 | #1C3431 | #1D3431 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-compliant | 1.220 | 1.226 | #193230 | #1B3230 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-partial | 1.403 | 1.414 | #443424 | #453524 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-noncompliant | 1.098 | 1.106 | #391E23 | #3A1E23 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/tint-insufficient | 1.363 | 1.372 | #313541 | #323541 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | solid/mark | 1.871 | 1.884 | #5E4526 | #5F4526 | Fail candidate | conservative candidate pairing |
| dark | all | canvas-mid | modal-over-scrim | 1.080 | 1.083 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas | 4.162 | 4.409 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass | 3.540 | 3.776 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong | 3.269 | 3.491 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid | 4.743 | 4.767 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | compliant | canvas/hover | 3.600 | 3.837 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/press | 3.167 | 3.382 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/track | 3.167 | 3.382 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/field | 3.600 | 3.837 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/field-hover | 1.980 | 2.012 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/field-focus | 3.272 | 3.494 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/chip | 3.600 | 3.837 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/nav-selected | 3.167 | 3.382 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/secondary-button | 3.380 | 3.607 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/secondary-hover | 2.962 | 3.164 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/secondary-active | 3.600 | 3.837 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/file-button | 3.063 | 3.272 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/segment-selected | 2.674 | 2.855 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/kbd | 3.272 | 3.494 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-critical | 3.813 | 4.048 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-high | 3.306 | 3.534 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-medium | 2.688 | 2.870 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-low | 3.073 | 3.230 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-compliant | 3.169 | 3.328 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-partial | 2.688 | 2.870 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-noncompliant | 3.482 | 3.713 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/tint-insufficient | 2.791 | 2.957 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | canvas/mark | 2.058 | 2.179 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/hover | 3.037 | 3.245 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/press | 2.672 | 2.853 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/track | 2.672 | 2.853 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/field | 3.037 | 3.245 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/field-hover | 2.061 | 2.092 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/field-focus | 2.760 | 2.947 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/chip | 3.037 | 3.245 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/nav-selected | 2.672 | 2.853 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/secondary-button | 2.850 | 3.045 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/secondary-hover | 2.504 | 2.670 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/secondary-active | 3.037 | 3.245 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/file-button | 2.586 | 2.760 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/segment-selected | 2.270 | 2.416 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/kbd | 2.760 | 2.947 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-critical | 3.348 | 3.567 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-high | 2.877 | 3.077 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-medium | 2.320 | 2.472 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-low | 2.659 | 2.791 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-compliant | 2.745 | 2.880 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-partial | 2.320 | 2.472 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-noncompliant | 3.036 | 3.243 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/tint-insufficient | 2.406 | 2.544 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass/mark | 1.820 | 1.922 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/hover | 2.803 | 2.994 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/press | 2.470 | 2.634 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/track | 2.470 | 2.634 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/field | 2.803 | 2.994 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/field-hover | 2.099 | 2.128 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/field-focus | 2.550 | 2.721 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/chip | 2.803 | 2.994 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/nav-selected | 2.470 | 2.634 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/secondary-button | 2.632 | 2.810 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/secondary-hover | 2.318 | 2.469 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/secondary-active | 2.803 | 2.994 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/file-button | 2.393 | 2.550 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/segment-selected | 2.107 | 2.239 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/kbd | 2.550 | 2.721 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-critical | 3.149 | 3.353 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-high | 2.697 | 2.881 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-medium | 2.170 | 2.308 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-low | 2.486 | 2.608 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-compliant | 2.567 | 2.692 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-partial | 2.170 | 2.308 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-noncompliant | 2.849 | 3.039 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/tint-insufficient | 2.249 | 2.374 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | glass-strong/mark | 1.722 | 1.815 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/hover | 4.182 | 4.209 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/press | 3.706 | 3.732 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/track | 3.706 | 3.732 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/field | 4.182 | 4.209 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/field-hover | 1.932 | 1.936 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/field-focus | 3.825 | 3.851 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/chip | 4.182 | 4.209 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/nav-selected | 3.706 | 3.732 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/secondary-button | 3.944 | 3.971 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/secondary-hover | 3.471 | 3.496 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/secondary-active | 4.182 | 4.209 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/file-button | 3.588 | 3.613 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/segment-selected | 3.132 | 3.155 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/kbd | 3.825 | 3.851 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-critical | 4.320 | 4.349 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-high | 3.805 | 3.834 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-medium | 3.117 | 3.141 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-low | 3.495 | 3.514 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-compliant | 3.596 | 3.614 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-partial | 3.117 | 3.141 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-noncompliant | 3.987 | 4.017 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/tint-insufficient | 3.214 | 3.235 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | solid/mark | 2.340 | 2.356 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | compliant | modal-over-scrim | 4.760 | 4.776 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | critical | canvas | 1.933 | 2.047 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass | 1.644 | 1.754 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong | 1.518 | 1.621 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid | 2.202 | 2.214 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/hover | 1.671 | 1.782 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/press | 1.470 | 1.571 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/track | 1.470 | 1.571 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/field | 1.671 | 1.782 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/field-hover | 4.265 | 4.332 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/field-focus | 1.519 | 1.622 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/chip | 1.671 | 1.782 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/nav-selected | 1.470 | 1.571 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/secondary-button | 1.569 | 1.675 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/secondary-hover | 1.375 | 1.469 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/secondary-active | 1.671 | 1.782 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/file-button | 1.422 | 1.519 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/segment-selected | 1.242 | 1.326 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/kbd | 1.519 | 1.622 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-critical | 1.770 | 1.880 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-high | 1.535 | 1.641 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-medium | 1.248 | 1.333 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-low | 1.427 | 1.500 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-compliant | 1.472 | 1.545 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-partial | 1.248 | 1.333 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-noncompliant | 1.617 | 1.724 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/tint-insufficient | 1.296 | 1.373 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | critical | canvas/mark | 1.000 | 1.047 | #634B2E | #6C4C2D | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/hover | 1.410 | 1.507 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/press | 1.241 | 1.325 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/track | 1.241 | 1.325 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/field | 1.410 | 1.507 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/field-hover | 4.439 | 4.504 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/field-focus | 1.282 | 1.369 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/chip | 1.410 | 1.507 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/nav-selected | 1.241 | 1.325 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/secondary-button | 1.323 | 1.414 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/secondary-hover | 1.163 | 1.240 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/secondary-active | 1.410 | 1.507 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/file-button | 1.201 | 1.282 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/segment-selected | 1.054 | 1.122 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/kbd | 1.282 | 1.369 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-critical | 1.555 | 1.656 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-high | 1.336 | 1.429 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-medium | 1.077 | 1.148 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-low | 1.235 | 1.296 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-compliant | 1.275 | 1.337 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-partial | 1.077 | 1.148 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-noncompliant | 1.410 | 1.506 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/tint-insufficient | 1.117 | 1.181 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass/mark | 1.121 | 1.183 | #6C5235 | #745336 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/hover | 1.302 | 1.390 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/press | 1.147 | 1.223 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/track | 1.147 | 1.223 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/field | 1.302 | 1.390 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/field-hover | 4.519 | 4.584 | #C0C1C5 | #C4C1C5 | Pass | conservative candidate pairing |
| dark | all | critical | glass-strong/field-focus | 1.184 | 1.263 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/chip | 1.302 | 1.390 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/nav-selected | 1.147 | 1.223 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/secondary-button | 1.222 | 1.305 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/secondary-hover | 1.076 | 1.146 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/secondary-active | 1.302 | 1.390 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/file-button | 1.111 | 1.184 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/segment-selected | 1.000 | 1.040 | #524D59 | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/kbd | 1.184 | 1.263 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-critical | 1.462 | 1.557 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-high | 1.253 | 1.338 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-medium | 1.008 | 1.072 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-low | 1.154 | 1.211 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-compliant | 1.192 | 1.250 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-partial | 1.008 | 1.072 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-noncompliant | 1.323 | 1.411 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/tint-insufficient | 1.044 | 1.103 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | critical | glass-strong/mark | 1.187 | 1.250 | #705539 | #78573A | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/hover | 1.942 | 1.954 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/press | 1.721 | 1.733 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/track | 1.721 | 1.733 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/field | 1.942 | 1.954 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/field-hover | 4.160 | 4.168 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/field-focus | 1.776 | 1.788 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/chip | 1.942 | 1.954 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/nav-selected | 1.721 | 1.733 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/secondary-button | 1.831 | 1.844 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/secondary-hover | 1.612 | 1.623 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/secondary-active | 1.942 | 1.954 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/file-button | 1.666 | 1.678 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/segment-selected | 1.454 | 1.465 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/kbd | 1.776 | 1.788 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-critical | 2.006 | 2.019 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-high | 1.767 | 1.780 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-medium | 1.448 | 1.459 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-low | 1.623 | 1.632 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-compliant | 1.670 | 1.678 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-partial | 1.448 | 1.459 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-noncompliant | 1.852 | 1.865 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/tint-insufficient | 1.492 | 1.502 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | critical | solid/mark | 1.087 | 1.094 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | critical | modal-over-scrim | 2.210 | 2.218 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas | 5.654 | 5.989 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | danger-text | glass | 4.809 | 5.130 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | danger-text | glass-strong | 4.440 | 4.743 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid | 6.443 | 6.476 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/hover | 4.890 | 5.213 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/press | 4.301 | 4.594 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/track | 4.301 | 4.594 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/field | 4.890 | 5.213 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/field-hover | 1.458 | 1.481 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/field-focus | 4.445 | 4.746 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/chip | 4.890 | 5.213 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/nav-selected | 4.301 | 4.594 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/secondary-button | 4.591 | 4.900 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/secondary-hover | 4.024 | 4.298 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/secondary-active | 4.890 | 5.213 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/file-button | 4.161 | 4.445 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/segment-selected | 3.633 | 3.878 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/kbd | 4.445 | 4.746 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-critical | 5.179 | 5.499 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-high | 4.491 | 4.800 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-medium | 3.651 | 3.899 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-low | 4.174 | 4.388 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-compliant | 4.305 | 4.520 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-partial | 3.651 | 3.899 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-noncompliant | 4.730 | 5.043 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | danger-text | canvas/tint-insufficient | 3.791 | 4.017 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | canvas/mark | 2.795 | 2.960 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/hover | 4.126 | 4.409 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/press | 3.630 | 3.875 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/track | 3.630 | 3.875 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/field | 4.126 | 4.409 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/field-hover | 1.517 | 1.540 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/field-focus | 3.749 | 4.004 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/chip | 4.126 | 4.409 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/nav-selected | 3.630 | 3.875 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/secondary-button | 3.872 | 4.136 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/secondary-hover | 3.401 | 3.627 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/secondary-active | 4.126 | 4.409 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/file-button | 3.514 | 3.749 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/segment-selected | 3.083 | 3.282 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/kbd | 3.749 | 4.004 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-critical | 4.548 | 4.846 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | danger-text | glass/tint-high | 3.908 | 4.180 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-medium | 3.151 | 3.358 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-low | 3.612 | 3.792 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-compliant | 3.729 | 3.912 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-partial | 3.151 | 3.358 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-noncompliant | 4.125 | 4.405 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/tint-insufficient | 3.268 | 3.456 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass/mark | 2.472 | 2.610 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/hover | 3.808 | 4.068 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/press | 3.356 | 3.579 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/track | 3.356 | 3.579 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/field | 3.808 | 4.068 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/field-hover | 1.545 | 1.567 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/field-focus | 3.464 | 3.696 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/chip | 3.808 | 4.068 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/nav-selected | 3.356 | 3.579 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/secondary-button | 3.576 | 3.817 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/secondary-hover | 3.149 | 3.354 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/secondary-active | 3.808 | 4.068 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/file-button | 3.251 | 3.464 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/segment-selected | 2.862 | 3.041 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/kbd | 3.464 | 3.696 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-critical | 4.277 | 4.555 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-high | 3.664 | 3.914 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-medium | 2.948 | 3.135 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-low | 3.377 | 3.543 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-compliant | 3.487 | 3.657 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-partial | 2.948 | 3.135 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-noncompliant | 3.870 | 4.129 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/tint-insufficient | 3.055 | 3.226 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | glass-strong/mark | 2.339 | 2.465 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/hover | 5.681 | 5.718 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/press | 5.034 | 5.069 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/track | 5.034 | 5.069 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/field | 5.681 | 5.718 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/field-hover | 1.422 | 1.425 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/field-focus | 5.195 | 5.232 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/chip | 5.681 | 5.718 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/nav-selected | 5.034 | 5.069 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/secondary-button | 5.358 | 5.394 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/secondary-hover | 4.715 | 4.749 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/secondary-active | 5.681 | 5.718 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/file-button | 4.873 | 4.908 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/segment-selected | 4.254 | 4.286 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/kbd | 5.195 | 5.232 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-critical | 5.868 | 5.907 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-high | 5.168 | 5.208 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-medium | 4.235 | 4.267 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/tint-low | 4.748 | 4.773 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-compliant | 4.885 | 4.910 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-partial | 4.235 | 4.267 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/tint-noncompliant | 5.416 | 5.456 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | danger-text | solid/tint-insufficient | 4.366 | 4.394 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | solid/mark | 3.179 | 3.201 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | danger-text | modal-over-scrim | 6.466 | 6.488 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | high | canvas | 3.672 | 3.890 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass | 3.124 | 3.332 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong | 2.884 | 3.081 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | high | solid | 4.185 | 4.207 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/hover | 3.176 | 3.386 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/press | 2.794 | 2.984 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/track | 2.794 | 2.984 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/field | 3.176 | 3.386 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/field-hover | 2.244 | 2.280 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/field-focus | 2.887 | 3.083 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/chip | 3.176 | 3.386 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/nav-selected | 2.794 | 2.984 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/secondary-button | 2.982 | 3.183 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/secondary-hover | 2.614 | 2.792 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/secondary-active | 3.176 | 3.386 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/file-button | 2.703 | 2.887 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/segment-selected | 2.360 | 2.519 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/kbd | 2.887 | 3.083 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-critical | 3.364 | 3.572 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-high | 2.917 | 3.118 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-medium | 2.372 | 2.533 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-low | 2.712 | 2.850 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-compliant | 2.797 | 2.936 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-partial | 2.372 | 2.533 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-noncompliant | 3.072 | 3.276 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/tint-insufficient | 2.463 | 2.609 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | high | canvas/mark | 1.816 | 1.923 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/hover | 2.680 | 2.864 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/press | 2.358 | 2.517 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/track | 2.358 | 2.517 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/field | 2.680 | 2.864 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/field-hover | 2.336 | 2.370 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/field-focus | 2.435 | 2.601 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/chip | 2.680 | 2.864 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/nav-selected | 2.358 | 2.517 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/secondary-button | 2.515 | 2.686 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/secondary-hover | 2.209 | 2.356 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/secondary-active | 2.680 | 2.864 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/file-button | 2.282 | 2.435 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/segment-selected | 2.003 | 2.132 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/kbd | 2.435 | 2.601 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-critical | 2.954 | 3.148 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-high | 2.538 | 2.715 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-medium | 2.047 | 2.181 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-low | 2.346 | 2.463 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-compliant | 2.422 | 2.541 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-partial | 2.047 | 2.181 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-noncompliant | 2.679 | 2.862 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/tint-insufficient | 2.123 | 2.245 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass/mark | 1.606 | 1.696 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/hover | 2.474 | 2.642 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/press | 2.180 | 2.325 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/track | 2.180 | 2.325 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/field | 2.474 | 2.642 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/field-hover | 2.378 | 2.412 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/field-focus | 2.250 | 2.401 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/chip | 2.474 | 2.642 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/nav-selected | 2.180 | 2.325 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/secondary-button | 2.323 | 2.479 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/secondary-hover | 2.045 | 2.178 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/secondary-active | 2.474 | 2.642 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/file-button | 2.112 | 2.250 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/segment-selected | 1.859 | 1.976 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/kbd | 2.250 | 2.401 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-critical | 2.778 | 2.958 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-high | 2.380 | 2.542 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-medium | 1.915 | 2.036 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-low | 2.193 | 2.301 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-compliant | 2.265 | 2.375 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-partial | 1.915 | 2.036 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-noncompliant | 2.514 | 2.682 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/tint-insufficient | 1.984 | 2.095 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | high | glass-strong/mark | 1.520 | 1.601 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/hover | 3.690 | 3.714 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/press | 3.270 | 3.293 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/track | 3.270 | 3.293 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/field | 3.690 | 3.714 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/field-hover | 2.189 | 2.194 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/field-focus | 3.375 | 3.398 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/chip | 3.690 | 3.714 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/nav-selected | 3.270 | 3.293 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/secondary-button | 3.480 | 3.504 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/secondary-hover | 3.062 | 3.085 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/secondary-active | 3.690 | 3.714 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/file-button | 3.166 | 3.188 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/segment-selected | 2.763 | 2.784 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/kbd | 3.375 | 3.398 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-critical | 3.812 | 3.837 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-high | 3.357 | 3.383 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-medium | 2.751 | 2.772 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-low | 3.084 | 3.100 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-compliant | 3.173 | 3.189 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-partial | 2.751 | 2.772 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-noncompliant | 3.518 | 3.544 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/tint-insufficient | 2.836 | 2.854 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | high | solid/mark | 2.065 | 2.079 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | high | modal-over-scrim | 4.200 | 4.214 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas | 6.211 | 6.579 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | insufficient | glass | 5.283 | 5.635 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass-strong | 4.878 | 5.210 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | insufficient | solid | 7.078 | 7.114 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/hover | 5.371 | 5.726 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/press | 4.725 | 5.047 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/track | 4.725 | 5.047 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/field | 5.371 | 5.726 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/field-hover | 1.327 | 1.348 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/field-focus | 4.883 | 5.214 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/chip | 5.371 | 5.726 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/nav-selected | 4.725 | 5.047 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/secondary-button | 5.043 | 5.383 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/secondary-hover | 4.420 | 4.722 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/secondary-active | 5.371 | 5.726 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/file-button | 4.571 | 4.883 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/segment-selected | 3.991 | 4.260 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/kbd | 4.883 | 5.214 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-critical | 5.689 | 6.041 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-high | 4.934 | 5.273 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-medium | 4.011 | 4.283 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-low | 4.586 | 4.820 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-compliant | 4.730 | 4.966 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-partial | 4.011 | 4.283 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-noncompliant | 5.196 | 5.540 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | insufficient | canvas/tint-insufficient | 4.165 | 4.412 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | canvas/mark | 3.070 | 3.252 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/hover | 4.533 | 4.843 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/press | 3.987 | 4.257 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/track | 3.987 | 4.257 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/field | 4.533 | 4.843 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/field-hover | 1.381 | 1.402 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/field-focus | 4.118 | 4.398 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/chip | 4.533 | 4.843 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/nav-selected | 3.987 | 4.257 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/secondary-button | 4.253 | 4.543 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/secondary-hover | 3.736 | 3.985 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/secondary-active | 4.533 | 4.843 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/file-button | 3.860 | 4.119 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/segment-selected | 3.387 | 3.605 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/kbd | 4.118 | 4.398 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-critical | 4.997 | 5.323 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/tint-high | 4.293 | 4.592 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-medium | 3.462 | 3.689 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-low | 3.967 | 4.165 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-compliant | 4.097 | 4.297 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-partial | 3.462 | 3.689 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/tint-noncompliant | 4.531 | 4.839 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass/tint-insufficient | 3.590 | 3.796 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass/mark | 2.716 | 2.868 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/hover | 4.183 | 4.468 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/press | 3.687 | 3.931 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/track | 3.687 | 3.931 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/field | 4.183 | 4.468 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/field-hover | 1.406 | 1.426 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/field-focus | 3.806 | 4.060 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/chip | 4.183 | 4.468 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/nav-selected | 3.687 | 3.931 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/secondary-button | 3.928 | 4.193 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/secondary-hover | 3.459 | 3.684 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/secondary-active | 4.183 | 4.468 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/file-button | 3.571 | 3.806 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/segment-selected | 3.144 | 3.341 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/kbd | 3.806 | 4.060 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-critical | 4.699 | 5.003 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-high | 4.025 | 4.300 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-medium | 3.238 | 3.444 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-low | 3.709 | 3.892 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-compliant | 3.831 | 4.017 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-partial | 3.238 | 3.444 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-noncompliant | 4.252 | 4.536 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/tint-insufficient | 3.356 | 3.543 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | glass-strong/mark | 2.570 | 2.708 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | solid/hover | 6.241 | 6.281 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/press | 5.530 | 5.569 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/track | 5.530 | 5.569 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/field | 6.241 | 6.281 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/field-hover | 1.295 | 1.297 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | solid/field-focus | 5.707 | 5.747 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/chip | 6.241 | 6.281 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/nav-selected | 5.530 | 5.569 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/secondary-button | 5.886 | 5.926 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/secondary-hover | 5.179 | 5.217 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/secondary-active | 6.241 | 6.281 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/file-button | 5.354 | 5.392 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/segment-selected | 4.673 | 4.708 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/kbd | 5.707 | 5.747 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-critical | 6.446 | 6.489 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-high | 5.677 | 5.721 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-medium | 4.652 | 4.688 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-low | 5.216 | 5.243 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-compliant | 5.366 | 5.393 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-partial | 4.652 | 4.688 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-noncompliant | 5.950 | 5.994 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/tint-insufficient | 4.796 | 4.827 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | insufficient | solid/mark | 3.492 | 3.516 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | insufficient | modal-over-scrim | 7.103 | 7.127 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | low | canvas | 4.671 | 4.948 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | low | glass | 3.973 | 4.238 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong | 3.668 | 3.918 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | low | solid | 5.323 | 5.350 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | low | canvas/hover | 4.040 | 4.307 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/press | 3.554 | 3.796 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/track | 3.554 | 3.796 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/field | 4.040 | 4.307 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/field-hover | 1.765 | 1.793 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/field-focus | 3.672 | 3.921 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/chip | 4.040 | 4.307 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/nav-selected | 3.554 | 3.796 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/secondary-button | 3.793 | 4.049 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/secondary-hover | 3.324 | 3.551 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/secondary-active | 4.040 | 4.307 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/file-button | 3.438 | 3.672 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/segment-selected | 3.002 | 3.204 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/kbd | 3.672 | 3.921 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-critical | 4.279 | 4.543 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-high | 3.711 | 3.966 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-medium | 3.017 | 3.221 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-low | 3.449 | 3.625 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-compliant | 3.557 | 3.735 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-partial | 3.017 | 3.221 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-noncompliant | 3.907 | 4.167 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/tint-insufficient | 3.132 | 3.318 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | low | canvas/mark | 2.309 | 2.445 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/hover | 3.409 | 3.642 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/press | 2.999 | 3.201 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/track | 2.999 | 3.201 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/field | 3.409 | 3.642 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/field-hover | 1.837 | 1.864 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/field-focus | 3.097 | 3.308 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/chip | 3.409 | 3.642 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/nav-selected | 2.999 | 3.201 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/secondary-button | 3.199 | 3.417 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/secondary-hover | 2.810 | 2.997 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/secondary-active | 3.409 | 3.642 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/file-button | 2.903 | 3.098 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/segment-selected | 2.547 | 2.712 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/kbd | 3.097 | 3.308 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-critical | 3.758 | 4.003 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-high | 3.228 | 3.453 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-medium | 2.604 | 2.774 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-low | 2.984 | 3.132 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-compliant | 3.081 | 3.232 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-partial | 2.604 | 2.774 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-noncompliant | 3.408 | 3.640 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/tint-insufficient | 2.700 | 2.855 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass/mark | 2.042 | 2.157 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/hover | 3.146 | 3.361 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/press | 2.773 | 2.957 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/track | 2.773 | 2.957 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/field | 3.146 | 3.361 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/field-hover | 1.870 | 1.897 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/field-focus | 2.862 | 3.054 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/chip | 3.146 | 3.361 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/nav-selected | 2.773 | 2.957 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/secondary-button | 2.954 | 3.153 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/secondary-hover | 2.602 | 2.771 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/secondary-active | 3.146 | 3.361 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/file-button | 2.686 | 2.862 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/segment-selected | 2.364 | 2.513 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/kbd | 2.862 | 3.054 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-critical | 3.534 | 3.763 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-high | 3.027 | 3.234 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-medium | 2.435 | 2.590 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-low | 2.790 | 2.927 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-compliant | 2.881 | 3.021 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-partial | 2.435 | 2.590 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-noncompliant | 3.198 | 3.411 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/tint-insufficient | 2.524 | 2.665 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | low | glass-strong/mark | 1.933 | 2.037 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/hover | 4.693 | 4.724 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | low | solid/press | 4.159 | 4.188 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/track | 4.159 | 4.188 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/field | 4.693 | 4.724 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | low | solid/field-hover | 1.721 | 1.725 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/field-focus | 4.292 | 4.322 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/chip | 4.693 | 4.724 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | low | solid/nav-selected | 4.159 | 4.188 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/secondary-button | 4.426 | 4.456 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/secondary-hover | 3.895 | 3.923 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/secondary-active | 4.693 | 4.724 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | low | solid/file-button | 4.026 | 4.055 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/segment-selected | 3.515 | 3.541 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/kbd | 4.292 | 4.322 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-critical | 4.848 | 4.880 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | low | solid/tint-high | 4.270 | 4.303 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-medium | 3.499 | 3.526 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-low | 3.923 | 3.943 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-compliant | 4.036 | 4.056 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-partial | 3.499 | 3.526 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-noncompliant | 4.475 | 4.508 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/tint-insufficient | 3.607 | 3.630 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | low | solid/mark | 2.626 | 2.645 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | low | modal-over-scrim | 5.342 | 5.360 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | medium | canvas | 7.333 | 7.768 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | medium | glass | 6.237 | 6.654 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong | 5.759 | 6.151 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | medium | solid | 8.357 | 8.400 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/hover | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/press | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | medium | canvas/track | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | medium | canvas/field | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/field-hover | 1.124 | 1.142 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | medium | canvas/field-focus | 5.765 | 6.156 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | medium | canvas/chip | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/nav-selected | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | medium | canvas/secondary-button | 5.954 | 6.356 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/secondary-hover | 5.219 | 5.575 | #403943 | #353641 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/secondary-active | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/file-button | 5.397 | 5.765 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | all | medium | canvas/segment-selected | 4.712 | 5.030 | #463F4A | #3C3D48 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/kbd | 5.765 | 6.156 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-critical | 6.717 | 7.133 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-high | 5.825 | 6.226 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-medium | 4.736 | 5.057 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-low | 5.414 | 5.691 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-compliant | 5.584 | 5.863 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-partial | 4.736 | 5.057 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-noncompliant | 6.134 | 6.541 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | medium | canvas/tint-insufficient | 4.917 | 5.209 | #413D4A | #383A49 | Pass | conservative candidate pairing |
| dark | all | medium | canvas/mark | 3.625 | 3.839 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/hover | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | medium | glass/press | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | medium | glass/track | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | medium | glass/field | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | medium | glass/field-hover | 1.170 | 1.187 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/field-focus | 4.862 | 5.193 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | medium | glass/chip | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | medium | glass/nav-selected | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | medium | glass/secondary-button | 5.021 | 5.364 | #433B47 | #373846 | Pass | conservative candidate pairing |
| dark | all | medium | glass/secondary-hover | 4.411 | 4.705 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/secondary-active | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | medium | glass/file-button | 4.557 | 4.863 | #49414D | #3E3F4C | Pass | conservative candidate pairing |
| dark | all | medium | glass/segment-selected | 3.999 | 4.257 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/kbd | 4.862 | 5.193 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-critical | 5.899 | 6.285 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-high | 5.068 | 5.422 | #593233 | #4F3032 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-medium | 4.087 | 4.356 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/tint-low | 4.684 | 4.918 | #364544 | #2D4343 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-compliant | 4.837 | 5.074 | #344343 | #2A4142 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-partial | 4.087 | 4.356 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/tint-noncompliant | 5.350 | 5.714 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | all | medium | glass/tint-insufficient | 4.239 | 4.482 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass/mark | 3.206 | 3.386 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/hover | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/press | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/track | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/field | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/field-hover | 1.191 | 1.208 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/field-focus | 4.493 | 4.794 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/chip | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/nav-selected | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/secondary-button | 4.638 | 4.950 | #48404C | #3C3E4B | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/secondary-hover | 4.084 | 4.350 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/secondary-active | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/file-button | 4.216 | 4.493 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/segment-selected | 3.712 | 3.945 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/kbd | 4.493 | 4.794 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-critical | 5.548 | 5.907 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-high | 4.753 | 5.076 | #5D3637 | #533436 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-medium | 3.823 | 4.066 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-low | 4.379 | 4.595 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-compliant | 4.523 | 4.743 | #384747 | #2E4546 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-partial | 3.823 | 4.066 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-noncompliant | 5.020 | 5.355 | #58333A | #4E3139 | Pass | conservative candidate pairing |
| dark | all | medium | glass-strong/tint-insufficient | 3.962 | 4.184 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | medium | glass-strong/mark | 3.034 | 3.198 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | medium | solid/hover | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | medium | solid/press | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | medium | solid/track | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | medium | solid/field | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | medium | solid/field-hover | 1.096 | 1.099 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | medium | solid/field-focus | 6.738 | 6.785 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | medium | solid/chip | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | medium | solid/nav-selected | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | medium | solid/secondary-button | 6.949 | 6.996 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | medium | solid/secondary-hover | 6.115 | 6.159 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | medium | solid/secondary-active | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | medium | solid/file-button | 6.321 | 6.366 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | medium | solid/segment-selected | 5.518 | 5.558 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | medium | solid/kbd | 6.738 | 6.785 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-critical | 7.611 | 7.662 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-high | 6.703 | 6.755 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-medium | 5.492 | 5.535 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-low | 6.159 | 6.191 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-compliant | 6.336 | 6.368 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-partial | 5.492 | 5.535 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-noncompliant | 7.025 | 7.077 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | medium | solid/tint-insufficient | 5.662 | 5.699 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | medium | solid/mark | 4.123 | 4.152 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | medium | modal-over-scrim | 8.386 | 8.415 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | muted | canvas | 6.035 | 6.393 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | muted | glass | 5.133 | 5.476 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | muted | glass-strong | 4.740 | 5.063 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | muted | solid | 6.877 | 6.913 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/hover | 5.219 | 5.564 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/press | 4.591 | 4.904 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | muted | canvas/track | 4.591 | 4.904 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | muted | canvas/field | 5.219 | 5.564 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/field-hover | 1.366 | 1.387 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/field-focus | 4.745 | 5.066 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | muted | canvas/chip | 5.219 | 5.564 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/nav-selected | 4.591 | 4.904 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | muted | canvas/secondary-button | 4.900 | 5.231 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/secondary-hover | 4.295 | 4.588 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/secondary-active | 5.219 | 5.564 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/file-button | 4.442 | 4.745 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/segment-selected | 3.878 | 4.139 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/kbd | 4.745 | 5.066 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | muted | canvas/tint-critical | 5.528 | 5.870 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/tint-high | 4.794 | 5.124 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/tint-medium | 3.897 | 4.162 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/tint-low | 4.456 | 4.684 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/tint-compliant | 4.596 | 4.825 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | muted | canvas/tint-partial | 3.897 | 4.162 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/tint-noncompliant | 5.049 | 5.383 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | muted | canvas/tint-insufficient | 4.047 | 4.287 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | muted | canvas/mark | 2.984 | 3.160 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/hover | 4.404 | 4.706 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/press | 3.874 | 4.136 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/track | 3.874 | 4.136 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/field | 4.404 | 4.706 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/field-hover | 1.422 | 1.442 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/field-focus | 4.002 | 4.274 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/chip | 4.404 | 4.706 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/nav-selected | 3.874 | 4.136 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/secondary-button | 4.133 | 4.415 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/secondary-hover | 3.630 | 3.872 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/secondary-active | 4.404 | 4.706 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/file-button | 3.750 | 4.002 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/segment-selected | 3.291 | 3.503 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/kbd | 4.002 | 4.274 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-critical | 4.855 | 5.172 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | muted | glass/tint-high | 4.171 | 4.462 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-medium | 3.364 | 3.585 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-low | 3.855 | 4.047 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-compliant | 3.981 | 4.176 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-partial | 3.364 | 3.585 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-noncompliant | 4.403 | 4.702 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/tint-insufficient | 3.489 | 3.689 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass/mark | 2.639 | 2.786 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/hover | 4.065 | 4.342 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/press | 3.582 | 3.820 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/track | 3.582 | 3.820 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/field | 4.065 | 4.342 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/field-hover | 1.447 | 1.468 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/field-focus | 3.698 | 3.945 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/chip | 4.065 | 4.342 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/nav-selected | 3.582 | 3.820 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/secondary-button | 3.817 | 4.074 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/secondary-hover | 3.361 | 3.580 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/secondary-active | 4.065 | 4.342 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/file-button | 3.470 | 3.698 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/segment-selected | 3.055 | 3.246 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/kbd | 3.698 | 3.945 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-critical | 4.566 | 4.862 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-high | 3.911 | 4.178 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-medium | 3.146 | 3.346 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-low | 3.604 | 3.782 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-compliant | 3.723 | 3.903 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-partial | 3.146 | 3.346 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-noncompliant | 4.131 | 4.407 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/tint-insufficient | 3.261 | 3.443 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | muted | glass-strong/mark | 2.497 | 2.632 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | muted | solid/hover | 6.064 | 6.103 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | muted | solid/press | 5.373 | 5.411 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | muted | solid/track | 5.373 | 5.411 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | muted | solid/field | 6.064 | 6.103 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | muted | solid/field-hover | 1.332 | 1.335 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | muted | solid/field-focus | 5.546 | 5.584 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | muted | solid/chip | 6.064 | 6.103 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | muted | solid/nav-selected | 5.373 | 5.411 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | muted | solid/secondary-button | 5.719 | 5.758 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | muted | solid/secondary-hover | 5.033 | 5.069 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | muted | solid/secondary-active | 6.064 | 6.103 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | muted | solid/file-button | 5.202 | 5.239 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | muted | solid/segment-selected | 4.541 | 4.575 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | muted | solid/kbd | 5.546 | 5.584 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-critical | 6.264 | 6.305 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-high | 5.517 | 5.559 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-medium | 4.520 | 4.555 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-low | 5.068 | 5.095 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-compliant | 5.214 | 5.241 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-partial | 4.520 | 4.555 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-noncompliant | 5.782 | 5.824 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | muted | solid/tint-insufficient | 4.660 | 4.690 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | muted | solid/mark | 3.393 | 3.417 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | muted | modal-over-scrim | 6.902 | 6.926 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | noncompliant | canvas | 2.896 | 3.068 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass | 2.464 | 2.628 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong | 2.275 | 2.430 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid | 3.301 | 3.318 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/hover | 2.505 | 2.670 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/press | 2.204 | 2.354 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/track | 2.204 | 2.354 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/field | 2.505 | 2.670 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/field-hover | 2.846 | 2.891 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/field-focus | 2.277 | 2.432 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/chip | 2.505 | 2.670 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/nav-selected | 2.204 | 2.354 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/secondary-button | 2.352 | 2.510 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/secondary-hover | 2.061 | 2.202 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/secondary-active | 2.505 | 2.670 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/file-button | 2.132 | 2.277 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/segment-selected | 1.861 | 1.987 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/kbd | 2.277 | 2.432 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-critical | 2.653 | 2.817 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-high | 2.301 | 2.459 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-medium | 1.871 | 1.997 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-low | 2.139 | 2.248 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-compliant | 2.206 | 2.316 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-partial | 1.871 | 1.997 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-noncompliant | 2.423 | 2.584 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/tint-insufficient | 1.942 | 2.058 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | canvas/mark | 1.432 | 1.516 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/hover | 2.114 | 2.259 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/press | 1.859 | 1.985 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/track | 1.859 | 1.985 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/field | 2.114 | 2.259 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/field-hover | 2.962 | 3.006 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/field-focus | 1.921 | 2.051 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/chip | 2.114 | 2.259 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/nav-selected | 1.859 | 1.985 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/secondary-button | 1.983 | 2.119 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/secondary-hover | 1.742 | 1.858 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/secondary-active | 2.114 | 2.259 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/file-button | 1.800 | 1.921 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/segment-selected | 1.579 | 1.681 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/kbd | 1.921 | 2.051 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-critical | 2.330 | 2.482 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-high | 2.002 | 2.141 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-medium | 1.614 | 1.720 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-low | 1.850 | 1.942 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-compliant | 1.910 | 2.004 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-partial | 1.614 | 1.720 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-noncompliant | 2.113 | 2.257 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/tint-insufficient | 1.674 | 1.770 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass/mark | 1.266 | 1.337 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/hover | 1.951 | 2.084 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/press | 1.719 | 1.833 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/track | 1.719 | 1.833 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/field | 1.951 | 2.084 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/field-hover | 3.016 | 3.059 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/field-focus | 1.775 | 1.893 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/chip | 1.951 | 2.084 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/nav-selected | 1.719 | 1.833 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/secondary-button | 1.832 | 1.955 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/secondary-hover | 1.613 | 1.718 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/secondary-active | 1.951 | 2.084 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/file-button | 1.665 | 1.775 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/segment-selected | 1.466 | 1.558 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/kbd | 1.775 | 1.893 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-critical | 2.191 | 2.333 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-high | 1.877 | 2.005 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-medium | 1.510 | 1.606 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-low | 1.730 | 1.815 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-compliant | 1.787 | 1.873 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-partial | 1.510 | 1.606 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-noncompliant | 1.983 | 2.115 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/tint-insufficient | 1.565 | 1.652 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | glass-strong/mark | 1.199 | 1.263 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/hover | 2.910 | 2.929 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/press | 2.579 | 2.597 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/track | 2.579 | 2.597 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/field | 2.910 | 2.929 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/field-hover | 2.776 | 2.781 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/field-focus | 2.662 | 2.680 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/chip | 2.910 | 2.929 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/nav-selected | 2.579 | 2.597 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/secondary-button | 2.745 | 2.763 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/secondary-hover | 2.415 | 2.433 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/secondary-active | 2.910 | 2.929 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/file-button | 2.497 | 2.515 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/segment-selected | 2.179 | 2.196 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/kbd | 2.662 | 2.680 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-critical | 3.006 | 3.026 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-high | 2.648 | 2.668 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-medium | 2.169 | 2.186 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-low | 2.433 | 2.445 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-compliant | 2.503 | 2.515 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-partial | 2.169 | 2.186 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-noncompliant | 2.775 | 2.795 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/tint-insufficient | 2.236 | 2.251 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | solid/mark | 1.628 | 1.640 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | noncompliant | modal-over-scrim | 3.312 | 3.324 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | all | partial | canvas | 7.333 | 7.768 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | partial | glass | 6.237 | 6.654 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong | 5.759 | 6.151 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | partial | solid | 8.357 | 8.400 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/hover | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/press | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | partial | canvas/track | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | partial | canvas/field | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/field-hover | 1.124 | 1.142 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | all | partial | canvas/field-focus | 5.765 | 6.156 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | partial | canvas/chip | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/nav-selected | 5.579 | 5.959 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | partial | canvas/secondary-button | 5.954 | 6.356 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/secondary-hover | 5.219 | 5.575 | #403943 | #353641 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/secondary-active | 6.342 | 6.761 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/file-button | 5.397 | 5.765 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | all | partial | canvas/segment-selected | 4.712 | 5.030 | #463F4A | #3C3D48 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/kbd | 5.765 | 6.156 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-critical | 6.717 | 7.133 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-high | 5.825 | 6.226 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-medium | 4.736 | 5.057 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-low | 5.414 | 5.691 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-compliant | 5.584 | 5.863 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-partial | 4.736 | 5.057 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-noncompliant | 6.134 | 6.541 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | partial | canvas/tint-insufficient | 4.917 | 5.209 | #413D4A | #383A49 | Pass | conservative candidate pairing |
| dark | all | partial | canvas/mark | 3.625 | 3.839 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/hover | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | partial | glass/press | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | partial | glass/track | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | partial | glass/field | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | partial | glass/field-hover | 1.170 | 1.187 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/field-focus | 4.862 | 5.193 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | partial | glass/chip | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | partial | glass/nav-selected | 4.708 | 5.026 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | partial | glass/secondary-button | 5.021 | 5.364 | #433B47 | #373846 | Pass | conservative candidate pairing |
| dark | all | partial | glass/secondary-hover | 4.411 | 4.705 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/secondary-active | 5.351 | 5.718 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | partial | glass/file-button | 4.557 | 4.863 | #49414D | #3E3F4C | Pass | conservative candidate pairing |
| dark | all | partial | glass/segment-selected | 3.999 | 4.257 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/kbd | 4.862 | 5.193 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-critical | 5.899 | 6.285 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-high | 5.068 | 5.422 | #593233 | #4F3032 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-medium | 4.087 | 4.356 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/tint-low | 4.684 | 4.918 | #364544 | #2D4343 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-compliant | 4.837 | 5.074 | #344343 | #2A4142 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-partial | 4.087 | 4.356 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/tint-noncompliant | 5.350 | 5.714 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | all | partial | glass/tint-insufficient | 4.239 | 4.482 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass/mark | 3.206 | 3.386 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/hover | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/press | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/track | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/field | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/field-hover | 1.191 | 1.208 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/field-focus | 4.493 | 4.794 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/chip | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/nav-selected | 4.353 | 4.641 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/secondary-button | 4.638 | 4.950 | #48404C | #3C3E4B | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/secondary-hover | 4.084 | 4.350 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/secondary-active | 4.939 | 5.276 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/file-button | 4.216 | 4.493 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/segment-selected | 3.712 | 3.945 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/kbd | 4.493 | 4.794 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-critical | 5.548 | 5.907 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-high | 4.753 | 5.076 | #5D3637 | #533436 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-medium | 3.823 | 4.066 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-low | 4.379 | 4.595 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-compliant | 4.523 | 4.743 | #384747 | #2E4546 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-partial | 3.823 | 4.066 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-noncompliant | 5.020 | 5.355 | #58333A | #4E3139 | Pass | conservative candidate pairing |
| dark | all | partial | glass-strong/tint-insufficient | 3.962 | 4.184 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | all | partial | glass-strong/mark | 3.034 | 3.198 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | partial | solid/hover | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | partial | solid/press | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | partial | solid/track | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | partial | solid/field | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | partial | solid/field-hover | 1.096 | 1.099 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | all | partial | solid/field-focus | 6.738 | 6.785 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | partial | solid/chip | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | partial | solid/nav-selected | 6.529 | 6.575 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | partial | solid/secondary-button | 6.949 | 6.996 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | partial | solid/secondary-hover | 6.115 | 6.159 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | partial | solid/secondary-active | 7.368 | 7.416 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | partial | solid/file-button | 6.321 | 6.366 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | partial | solid/segment-selected | 5.518 | 5.558 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | partial | solid/kbd | 6.738 | 6.785 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-critical | 7.611 | 7.662 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-high | 6.703 | 6.755 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-medium | 5.492 | 5.535 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-low | 6.159 | 6.191 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-compliant | 6.336 | 6.368 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-partial | 5.492 | 5.535 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-noncompliant | 7.025 | 7.077 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | partial | solid/tint-insufficient | 5.662 | 5.699 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | partial | solid/mark | 4.123 | 4.152 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | all | partial | modal-over-scrim | 8.386 | 8.415 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | text | canvas | 13.199 | 13.982 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | text | glass | 11.226 | 11.976 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong | 10.366 | 11.072 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | text | solid | 15.042 | 15.119 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | text | canvas/hover | 11.415 | 12.169 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text | canvas/press | 10.042 | 10.726 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text | canvas/track | 10.042 | 10.726 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text | canvas/field | 11.415 | 12.169 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text | canvas/field-hover | 1.576 | 1.601 | #BEBCC0 | #BBBBBF | Fail candidate | conservative candidate pairing |
| dark | all | text | canvas/field-focus | 10.377 | 11.081 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | text | canvas/chip | 11.415 | 12.169 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text | canvas/nav-selected | 10.042 | 10.726 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text | canvas/secondary-button | 10.718 | 11.440 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | text | canvas/secondary-hover | 9.394 | 10.035 | #403943 | #353641 | Pass | conservative candidate pairing |
| dark | all | text | canvas/secondary-active | 11.415 | 12.169 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text | canvas/file-button | 9.714 | 10.377 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | all | text | canvas/segment-selected | 8.482 | 9.053 | #463F4A | #3C3D48 | Pass | conservative candidate pairing |
| dark | all | text | canvas/kbd | 10.377 | 11.081 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-critical | 12.091 | 12.839 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-high | 10.485 | 11.206 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-medium | 8.524 | 9.102 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-low | 9.746 | 10.244 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-compliant | 10.051 | 10.553 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-partial | 8.524 | 9.102 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-noncompliant | 11.042 | 11.774 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | text | canvas/tint-insufficient | 8.850 | 9.377 | #413D4A | #383A49 | Pass | conservative candidate pairing |
| dark | all | text | canvas/mark | 6.525 | 6.910 | #6C4C2D | #644A2C | Pass | conservative candidate pairing |
| dark | all | text | glass/hover | 9.632 | 10.292 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text | glass/press | 8.473 | 9.046 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text | glass/track | 8.473 | 9.046 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text | glass/field | 9.632 | 10.292 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text | glass/field-hover | 1.516 | 1.539 | #C2C0C4 | #BFBFC3 | Fail candidate | conservative candidate pairing |
| dark | all | text | glass/field-focus | 8.752 | 9.347 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | text | glass/chip | 9.632 | 10.292 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text | glass/nav-selected | 8.473 | 9.046 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text | glass/secondary-button | 9.038 | 9.655 | #433B47 | #373846 | Pass | conservative candidate pairing |
| dark | all | text | glass/secondary-hover | 7.940 | 8.468 | #4B434F | #40414E | Pass | conservative candidate pairing |
| dark | all | text | glass/secondary-active | 9.632 | 10.292 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text | glass/file-button | 8.203 | 8.753 | #49414D | #3E3F4C | Pass | conservative candidate pairing |
| dark | all | text | glass/segment-selected | 7.198 | 7.662 | #514955 | #464754 | Pass | conservative candidate pairing |
| dark | all | text | glass/kbd | 8.752 | 9.347 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-critical | 10.619 | 11.313 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-high | 9.123 | 9.759 | #593233 | #4F3032 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-medium | 7.357 | 7.840 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-low | 8.431 | 8.852 | #364544 | #2D4343 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-compliant | 8.706 | 9.132 | #344343 | #2A4142 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-partial | 7.357 | 7.840 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-noncompliant | 9.630 | 10.285 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | all | text | glass/tint-insufficient | 7.630 | 8.067 | #4B4655 | #414454 | Pass | conservative candidate pairing |
| dark | all | text | glass/mark | 5.771 | 6.094 | #745336 | #6C5235 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/hover | 8.890 | 9.496 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/press | 7.835 | 8.354 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/track | 7.835 | 8.354 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/field | 8.890 | 9.496 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/field-hover | 1.490 | 1.511 | #C4C1C5 | #C0C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | text | glass-strong/field-focus | 8.087 | 8.629 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/chip | 8.890 | 9.496 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/nav-selected | 7.835 | 8.354 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/secondary-button | 8.348 | 8.910 | #48404C | #3C3E4B | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/secondary-hover | 7.351 | 7.829 | #504854 | #454653 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/secondary-active | 8.890 | 9.496 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/file-button | 7.589 | 8.088 | #4E4652 | #434451 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/segment-selected | 6.682 | 7.100 | #564E5A | #4B4C58 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/kbd | 8.087 | 8.629 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-critical | 9.986 | 10.633 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-high | 8.554 | 9.137 | #5D3637 | #533436 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-medium | 6.881 | 7.318 | #624A3B | #59483A | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-low | 7.883 | 8.271 | #3B4948 | #314747 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-compliant | 8.142 | 8.536 | #384747 | #2E4546 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-partial | 6.881 | 7.318 | #624A3B | #59483A | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-noncompliant | 9.036 | 9.639 | #58333A | #4E3139 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/tint-insufficient | 7.132 | 7.530 | #4F4A59 | #464858 | Pass | conservative candidate pairing |
| dark | all | text | glass-strong/mark | 5.462 | 5.756 | #78573A | #705539 | Pass | conservative candidate pairing |
| dark | all | text | solid/hover | 13.262 | 13.348 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text | solid/press | 11.752 | 11.835 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text | solid/track | 11.752 | 11.835 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text | solid/field | 13.262 | 13.348 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text | solid/field-hover | 1.638 | 1.642 | #B9B9BC | #B8B9BC | Fail candidate | conservative candidate pairing |
| dark | all | text | solid/field-focus | 12.129 | 12.213 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | text | solid/chip | 13.262 | 13.348 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text | solid/nav-selected | 11.752 | 11.835 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text | solid/secondary-button | 12.508 | 12.593 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | text | solid/secondary-hover | 11.007 | 11.087 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | text | solid/secondary-active | 13.262 | 13.348 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text | solid/file-button | 11.377 | 11.459 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | text | solid/segment-selected | 9.932 | 10.005 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | text | solid/kbd | 12.129 | 12.213 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-critical | 13.700 | 13.791 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-high | 12.065 | 12.159 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-medium | 9.886 | 9.963 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-low | 11.085 | 11.143 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-compliant | 11.404 | 11.462 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-partial | 9.886 | 9.963 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-noncompliant | 12.645 | 12.738 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | text | solid/tint-insufficient | 10.192 | 10.258 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | text | solid/mark | 7.421 | 7.473 | #5F4526 | #5E4526 | Pass | conservative candidate pairing |
| dark | all | text | modal-over-scrim | 15.095 | 15.147 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas | 8.349 | 8.844 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | all | text-2 | glass | 7.101 | 7.575 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong | 6.557 | 7.004 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | all | text-2 | solid | 9.514 | 9.563 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/hover | 7.220 | 7.697 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/press | 6.352 | 6.785 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/track | 6.352 | 6.785 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/field | 7.220 | 7.697 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/field-hover | 1.000 | 1.013 | #BEBCC0 | #BBBBBF | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | canvas/field-focus | 6.564 | 7.009 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/chip | 7.220 | 7.697 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/nav-selected | 6.352 | 6.785 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/secondary-button | 6.779 | 7.236 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/secondary-hover | 5.942 | 6.347 | #403943 | #353641 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/secondary-active | 7.220 | 7.697 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/file-button | 6.145 | 6.564 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/segment-selected | 5.365 | 5.726 | #463F4A | #3C3D48 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/kbd | 6.564 | 7.009 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-critical | 7.648 | 8.121 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-high | 6.632 | 7.088 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-medium | 5.392 | 5.757 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-low | 6.164 | 6.480 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-compliant | 6.358 | 6.675 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-partial | 5.392 | 5.757 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-noncompliant | 6.984 | 7.447 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/tint-insufficient | 5.598 | 5.931 | #413D4A | #383A49 | Pass | conservative candidate pairing |
| dark | all | text-2 | canvas/mark | 4.127 | 4.371 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass/hover | 6.093 | 6.510 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/press | 5.360 | 5.722 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/track | 5.360 | 5.722 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/field | 6.093 | 6.510 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/field-hover | 1.028 | 1.043 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass/field-focus | 5.536 | 5.912 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/chip | 6.093 | 6.510 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/nav-selected | 5.360 | 5.722 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/secondary-button | 5.717 | 6.107 | #433B47 | #373846 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/secondary-hover | 5.022 | 5.356 | #4B434F | #40414E | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/secondary-active | 6.093 | 6.510 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/file-button | 5.188 | 5.537 | #49414D | #3E3F4C | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/segment-selected | 4.553 | 4.847 | #514955 | #464754 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/kbd | 5.536 | 5.912 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-critical | 6.717 | 7.156 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-high | 5.770 | 6.173 | #593233 | #4F3032 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-medium | 4.654 | 4.959 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-low | 5.333 | 5.599 | #364544 | #2D4343 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-compliant | 5.507 | 5.776 | #344343 | #2A4142 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-partial | 4.654 | 4.959 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-noncompliant | 6.091 | 6.505 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/tint-insufficient | 4.826 | 5.103 | #4B4655 | #414454 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass/mark | 3.650 | 3.855 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass-strong/hover | 5.623 | 6.007 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/press | 4.956 | 5.284 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/track | 4.956 | 5.284 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/field | 5.623 | 6.007 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/field-hover | 1.046 | 1.061 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass-strong/field-focus | 5.116 | 5.458 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/chip | 5.623 | 6.007 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/nav-selected | 4.956 | 5.284 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/secondary-button | 5.280 | 5.636 | #48404C | #3C3E4B | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/secondary-hover | 4.650 | 4.952 | #504854 | #454653 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/secondary-active | 5.623 | 6.007 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/file-button | 4.800 | 5.116 | #4E4652 | #434451 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/segment-selected | 4.226 | 4.491 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass-strong/kbd | 5.116 | 5.458 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-critical | 6.316 | 6.726 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-high | 5.411 | 5.780 | #5D3637 | #533436 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-medium | 4.353 | 4.629 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-low | 4.986 | 5.231 | #3B4948 | #314747 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-compliant | 5.150 | 5.400 | #384747 | #2E4546 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-partial | 4.353 | 4.629 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-noncompliant | 5.715 | 6.097 | #58333A | #4E3139 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/tint-insufficient | 4.511 | 4.763 | #4F4A59 | #464858 | Pass | conservative candidate pairing |
| dark | all | text-2 | glass-strong/mark | 3.455 | 3.641 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | solid/hover | 8.389 | 8.443 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/press | 7.433 | 7.486 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/track | 7.433 | 7.486 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/field | 8.389 | 8.443 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/field-hover | 1.036 | 1.038 | #B9B9BC | #B8B9BC | Fail candidate | conservative candidate pairing |
| dark | all | text-2 | solid/field-focus | 7.672 | 7.725 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/chip | 8.389 | 8.443 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/nav-selected | 7.433 | 7.486 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/secondary-button | 7.912 | 7.965 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/secondary-hover | 6.962 | 7.013 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/secondary-active | 8.389 | 8.443 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/file-button | 7.196 | 7.248 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/segment-selected | 6.282 | 6.329 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/kbd | 7.672 | 7.725 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-critical | 8.665 | 8.723 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-high | 7.632 | 7.691 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-medium | 6.253 | 6.302 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-low | 7.012 | 7.048 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-compliant | 7.214 | 7.250 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-partial | 6.253 | 6.302 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-noncompliant | 7.998 | 8.057 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/tint-insufficient | 6.447 | 6.488 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | all | text-2 | solid/mark | 4.694 | 4.727 | #5F4526 | #5E4526 | Pass | conservative candidate pairing |
| dark | all | text-2 | modal-over-scrim | 9.548 | 9.581 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas | 12.951 | 13.719 | #28202C | #1C1D2A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass | 11.016 | 11.752 | #352C39 | #282938 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong | 10.172 | 10.865 | #3A313F | #2E2F3D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid | 14.760 | 14.836 | #151621 | #131621 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/hover | 11.201 | 11.941 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/press | 9.854 | 10.525 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/track | 9.854 | 10.525 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/field | 11.201 | 11.941 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/field-hover | 1.547 | 1.571 | #BEBCC0 | #BBBBBF | Fail candidate | conservative candidate pairing |
| dark | graphite | accent-text | canvas/field-focus | 10.182 | 10.873 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/chip | 11.201 | 11.941 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/nav-selected | 9.854 | 10.525 | #3B343F | #30313D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/secondary-button | 10.517 | 11.226 | #37303B | #2C2D39 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/secondary-hover | 9.218 | 9.846 | #403943 | #353641 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/secondary-active | 11.201 | 11.941 | #332B37 | #272835 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/file-button | 9.532 | 10.182 | #3E3641 | #33343F | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/segment-selected | 8.322 | 8.883 | #463F4A | #3C3D48 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/kbd | 10.182 | 10.873 | #39323D | #2E2F3B | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-critical | 11.864 | 12.598 | #411F28 | #381D27 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-high | 10.288 | 10.996 | #4F2929 | #462627 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-medium | 8.364 | 8.931 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-low | 9.563 | 10.052 | #2C3C3A | #233938 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-compliant | 9.863 | 10.355 | #2A3A39 | #203737 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-partial | 8.364 | 8.931 | #543C2D | #4B3A2B | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-noncompliant | 10.834 | 11.553 | #49262C | #40232A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/tint-insufficient | 8.684 | 9.201 | #413D4A | #383A49 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | canvas/mark | 6.403 | 6.781 | #6C4C2D | #644A2C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/hover | 9.452 | 10.099 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/press | 8.315 | 8.877 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/track | 8.315 | 8.877 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/field | 9.452 | 10.099 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/field-hover | 1.488 | 1.510 | #C2C0C4 | #BFBFC3 | Fail candidate | conservative candidate pairing |
| dark | graphite | accent-text | glass/field-focus | 8.588 | 9.172 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/chip | 9.452 | 10.099 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/nav-selected | 8.315 | 8.877 | #473F4B | #3B3D4A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/secondary-button | 8.869 | 9.474 | #433B47 | #373846 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/secondary-hover | 7.791 | 8.309 | #4B434F | #40414E | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/secondary-active | 9.452 | 10.099 | #3F3643 | #333442 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/file-button | 8.049 | 8.589 | #49414D | #3E3F4C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/segment-selected | 7.063 | 7.518 | #514955 | #464754 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/kbd | 8.588 | 9.172 | #453D49 | #393A48 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-critical | 10.419 | 11.100 | #4B2833 | #412632 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-high | 8.952 | 9.576 | #593233 | #4F3032 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-medium | 7.219 | 7.693 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-low | 8.273 | 8.685 | #364544 | #2D4343 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-compliant | 8.543 | 8.961 | #344343 | #2A4142 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-partial | 7.219 | 7.693 | #5E4537 | #544336 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-noncompliant | 9.449 | 10.092 | #532F36 | #4A2D35 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/tint-insufficient | 7.487 | 7.916 | #4B4655 | #414454 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass/mark | 5.663 | 5.980 | #745336 | #6C5235 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/hover | 8.724 | 9.318 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/press | 7.688 | 8.198 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/track | 7.688 | 8.198 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/field | 8.724 | 9.318 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/field-hover | 1.462 | 1.483 | #C4C1C5 | #C0C1C5 | Fail candidate | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/field-focus | 7.936 | 8.467 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/chip | 8.724 | 9.318 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/nav-selected | 7.688 | 8.198 | #4C4450 | #41424F | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/secondary-button | 8.191 | 8.743 | #48404C | #3C3E4B | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/secondary-hover | 7.213 | 7.682 | #504854 | #454653 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/secondary-active | 8.724 | 9.318 | #443C48 | #383947 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/file-button | 7.447 | 7.936 | #4E4652 | #434451 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/segment-selected | 6.556 | 6.967 | #564E5A | #4B4C58 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/kbd | 7.936 | 8.467 | #4A424E | #3F404D | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-critical | 9.798 | 10.433 | #4F2D37 | #462B36 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-high | 8.394 | 8.966 | #5D3637 | #533436 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-medium | 6.752 | 7.181 | #624A3B | #59483A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-low | 7.735 | 8.115 | #3B4948 | #314747 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-compliant | 7.989 | 8.376 | #384747 | #2E4546 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-partial | 6.752 | 7.181 | #624A3B | #59483A | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-noncompliant | 8.866 | 9.458 | #58333A | #4E3139 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/tint-insufficient | 6.998 | 7.389 | #4F4A59 | #464858 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | glass-strong/mark | 5.359 | 5.648 | #78573A | #705539 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/hover | 13.014 | 13.098 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/press | 11.531 | 11.613 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/track | 11.531 | 11.613 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/field | 13.014 | 13.098 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/field-hover | 1.608 | 1.611 | #B9B9BC | #B8B9BC | Fail candidate | conservative candidate pairing |
| dark | graphite | accent-text | solid/field-focus | 11.901 | 11.984 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/chip | 13.014 | 13.098 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/nav-selected | 11.531 | 11.613 | #2A2B35 | #282B35 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/secondary-button | 12.273 | 12.357 | #252730 | #242630 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/secondary-hover | 10.800 | 10.879 | #2F3039 | #2D3039 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/secondary-active | 13.014 | 13.098 | #20222C | #1F222C | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/file-button | 11.164 | 11.244 | #2C2E37 | #2B2D37 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/segment-selected | 9.746 | 9.817 | #363740 | #343740 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/kbd | 11.901 | 11.984 | #282933 | #262932 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-critical | 13.443 | 13.532 | #321820 | #311720 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-high | 11.839 | 11.931 | #402120 | #3F2120 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-medium | 9.700 | 9.776 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-low | 10.877 | 10.934 | #1D3431 | #1C3431 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-compliant | 11.191 | 11.247 | #1B3230 | #193230 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-partial | 9.700 | 9.776 | #453524 | #443424 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-noncompliant | 12.408 | 12.499 | #3A1E23 | #391E23 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/tint-insufficient | 10.001 | 10.065 | #323541 | #313541 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | solid/mark | 7.281 | 7.333 | #5F4526 | #5E4526 | Pass | conservative candidate pairing |
| dark | graphite | accent-text | modal-over-scrim | 14.812 | 14.863 | #141621 | #131621 | Pass | conservative candidate pairing |
| dark | graphite | canvas-mid | canvas/tint-accent | 1.897 | 2.014 | #484A55 | #524C57 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | compliant | canvas/tint-accent | 2.190 | 2.324 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | critical | canvas/tint-accent | 1.017 | 1.079 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | danger-text | canvas/tint-accent | 2.974 | 3.157 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | high | canvas/tint-accent | 1.932 | 2.051 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | insufficient | canvas/tint-accent | 3.267 | 3.468 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | low | canvas/tint-accent | 2.457 | 2.608 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | medium | canvas/tint-accent | 3.858 | 4.095 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | muted | canvas/tint-accent | 3.175 | 3.370 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | noncompliant | canvas/tint-accent | 1.524 | 1.617 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | partial | canvas/tint-accent | 3.858 | 4.095 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | text | canvas/tint-accent | 6.944 | 7.370 | #524C57 | #484A55 | Pass | conservative candidate pairing; pill uses text |
| dark | graphite | text-2 | canvas/tint-accent | 4.392 | 4.662 | #524C57 | #484A55 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | accent-text | canvas/accent-soft | 8.212 | 8.752 | #46404B | #3C3E4A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text | canvas/accent-soft | 8.369 | 8.919 | #46404B | #3C3E4A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text-2 | canvas/accent-soft | 5.294 | 5.641 | #46404B | #3C3E4A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | muted | canvas/accent-soft | 3.827 | 4.078 | #46404B | #3C3E4A | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | canvas-mid | glass/tint-accent | 2.209 | 2.336 | #525360 | #5C5561 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | compliant | glass/tint-accent | 1.888 | 1.996 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | critical | glass/tint-accent | 1.079 | 1.141 | #525360 | #5C5561 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | danger-text | glass/tint-accent | 2.564 | 2.712 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | high | glass/tint-accent | 1.666 | 1.761 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | insufficient | glass/tint-accent | 2.817 | 2.979 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | low | glass/tint-accent | 2.119 | 2.240 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | medium | glass/tint-accent | 3.326 | 3.517 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | muted | glass/tint-accent | 2.737 | 2.894 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | noncompliant | glass/tint-accent | 1.314 | 1.389 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | partial | glass/tint-accent | 3.326 | 3.517 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | text | glass/tint-accent | 5.986 | 6.330 | #5C5561 | #525360 | Pass | conservative candidate pairing; pill uses text |
| dark | graphite | text-2 | glass/tint-accent | 3.787 | 4.004 | #5C5561 | #525360 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | accent-text | glass/accent-soft | 6.995 | 7.434 | #514A56 | #474855 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text | glass/accent-soft | 7.129 | 7.576 | #514A56 | #474855 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text-2 | glass/accent-soft | 4.509 | 4.792 | #514A56 | #474855 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | muted | glass/accent-soft | 3.259 | 3.464 | #514A56 | #474855 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | canvas-mid | glass-strong/tint-accent | 2.365 | 2.496 | #565864 | #605A65 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | compliant | glass-strong/tint-accent | 1.766 | 1.864 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | critical | glass-strong/tint-accent | 1.155 | 1.219 | #565864 | #605A65 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | danger-text | glass-strong/tint-accent | 2.399 | 2.532 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | high | glass-strong/tint-accent | 1.559 | 1.645 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | insufficient | glass-strong/tint-accent | 2.636 | 2.782 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | low | glass-strong/tint-accent | 1.982 | 2.092 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | medium | glass-strong/tint-accent | 3.112 | 3.284 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | muted | glass-strong/tint-accent | 2.561 | 2.703 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | noncompliant | glass-strong/tint-accent | 1.229 | 1.297 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | partial | glass-strong/tint-accent | 3.112 | 3.284 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | text | glass-strong/tint-accent | 5.601 | 5.912 | #605A65 | #565864 | Pass | conservative candidate pairing; pill uses text |
| dark | graphite | text-2 | glass-strong/tint-accent | 3.543 | 3.739 | #605A65 | #565864 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | accent-text | glass-strong/accent-soft | 6.505 | 6.901 | #564F5B | #4B4D5A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text | glass-strong/accent-soft | 6.629 | 7.033 | #564F5B | #4B4D5A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text-2 | glass-strong/accent-soft | 4.193 | 4.449 | #564F5B | #4B4D5A | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | muted | glass-strong/accent-soft | 3.031 | 3.216 | #564F5B | #4B4D5A | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | canvas-mid | solid/tint-accent | 1.728 | 1.740 | #42444E | #43454E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | compliant | solid/tint-accent | 2.534 | 2.552 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | critical | solid/tint-accent | 1.177 | 1.185 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | danger-text | solid/tint-accent | 3.442 | 3.466 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | high | solid/tint-accent | 2.236 | 2.252 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | insufficient | solid/tint-accent | 3.781 | 3.808 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | low | solid/tint-accent | 2.844 | 2.864 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | medium | solid/tint-accent | 4.465 | 4.496 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | muted | solid/tint-accent | 3.674 | 3.700 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | noncompliant | solid/tint-accent | 1.763 | 1.776 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | partial | solid/tint-accent | 4.465 | 4.496 | #43454E | #42444E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | graphite | text | solid/tint-accent | 8.036 | 8.092 | #43454E | #42444E | Pass | conservative candidate pairing; pill uses text |
| dark | graphite | text-2 | solid/tint-accent | 5.083 | 5.119 | #43454E | #42444E | Pass | conservative candidate pairing; pill uses text |
| dark | graphite | accent-text | solid/accent-soft | 9.584 | 9.653 | #363842 | #353842 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text | solid/accent-soft | 9.767 | 9.838 | #363842 | #353842 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | text-2 | solid/accent-soft | 6.178 | 6.223 | #363842 | #353842 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | muted | solid/accent-soft | 4.466 | 4.498 | #363842 | #353842 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | graphite | on-accent | primary-button | 14.560 | 14.978 | #E6E9EF | #EAECF1 | Pass | declared component pairing |
| dark | graphite | on-accent | primary-kbd | 12.206 | 12.550 | #D4D6DC | #D7D9DE | Pass | declared component pairing |
| dark | azure | accent-text | canvas | 2.796 | 2.962 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass | 2.379 | 2.537 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong | 2.196 | 2.346 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid | 3.187 | 3.203 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/hover | 2.418 | 2.578 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/press | 2.128 | 2.272 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/track | 2.128 | 2.272 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/field | 2.418 | 2.578 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/field-hover | 2.948 | 2.994 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/field-focus | 2.198 | 2.348 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/chip | 2.418 | 2.578 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/nav-selected | 2.128 | 2.272 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/secondary-button | 2.271 | 2.424 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/secondary-hover | 1.990 | 2.126 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/secondary-active | 2.418 | 2.578 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/file-button | 2.058 | 2.199 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/segment-selected | 1.797 | 1.918 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/kbd | 2.198 | 2.348 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-critical | 2.562 | 2.720 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-high | 2.221 | 2.374 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-medium | 1.806 | 1.928 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-low | 2.065 | 2.170 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-compliant | 2.130 | 2.236 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-partial | 1.806 | 1.928 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-noncompliant | 2.339 | 2.494 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/tint-insufficient | 1.875 | 1.987 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | canvas/mark | 1.382 | 1.464 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/hover | 2.041 | 2.181 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/press | 1.795 | 1.917 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/track | 1.795 | 1.917 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/field | 2.041 | 2.181 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/field-hover | 3.068 | 3.113 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/field-focus | 1.854 | 1.980 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/chip | 2.041 | 2.181 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/nav-selected | 1.795 | 1.917 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/secondary-button | 1.915 | 2.046 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/secondary-hover | 1.682 | 1.794 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/secondary-active | 2.041 | 2.181 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/file-button | 1.738 | 1.855 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/segment-selected | 1.525 | 1.623 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/kbd | 1.854 | 1.980 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-critical | 2.250 | 2.397 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-high | 1.933 | 2.068 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-medium | 1.559 | 1.661 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-low | 1.786 | 1.875 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-compliant | 1.845 | 1.935 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-partial | 1.559 | 1.661 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-noncompliant | 2.040 | 2.179 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/tint-insufficient | 1.617 | 1.709 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass/mark | 1.223 | 1.291 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/hover | 1.884 | 2.012 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/press | 1.660 | 1.770 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/track | 1.660 | 1.770 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/field | 1.884 | 2.012 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/field-hover | 3.123 | 3.168 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/field-focus | 1.713 | 1.828 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/chip | 1.884 | 2.012 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/nav-selected | 1.660 | 1.770 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/secondary-button | 1.769 | 1.888 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/secondary-hover | 1.557 | 1.659 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/secondary-active | 1.884 | 2.012 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/file-button | 1.608 | 1.714 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/segment-selected | 1.416 | 1.504 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/kbd | 1.713 | 1.828 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-critical | 2.116 | 2.253 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-high | 1.812 | 1.936 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-medium | 1.458 | 1.550 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-low | 1.670 | 1.752 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-compliant | 1.725 | 1.809 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-partial | 1.458 | 1.550 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-noncompliant | 1.914 | 2.042 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/tint-insufficient | 1.511 | 1.595 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | glass-strong/mark | 1.157 | 1.219 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/hover | 2.810 | 2.828 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/press | 2.490 | 2.507 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/track | 2.490 | 2.507 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/field | 2.810 | 2.828 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/field-hover | 2.875 | 2.881 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/field-focus | 2.570 | 2.588 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/chip | 2.810 | 2.828 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/nav-selected | 2.490 | 2.507 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/secondary-button | 2.650 | 2.668 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/secondary-hover | 2.332 | 2.349 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/secondary-active | 2.810 | 2.828 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/file-button | 2.410 | 2.428 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/segment-selected | 2.104 | 2.120 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/kbd | 2.570 | 2.588 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-critical | 2.902 | 2.922 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-high | 2.556 | 2.576 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-medium | 2.094 | 2.111 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-low | 2.349 | 2.361 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-compliant | 2.416 | 2.428 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-partial | 2.094 | 2.111 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-noncompliant | 2.679 | 2.699 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/tint-insufficient | 2.159 | 2.173 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | solid/mark | 1.572 | 1.583 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | azure | accent-text | modal-over-scrim | 3.198 | 3.209 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | azure | canvas-mid | canvas/tint-accent | 1.208 | 1.261 | #172D4B | #21304D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | compliant | canvas/tint-accent | 3.495 | 3.651 | #21304D | #172D4B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | critical | canvas/tint-accent | 1.623 | 1.695 | #21304D | #172D4B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | danger-text | canvas/tint-accent | 4.748 | 4.960 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | high | canvas/tint-accent | 3.084 | 3.222 | #21304D | #172D4B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | insufficient | canvas/tint-accent | 5.216 | 5.448 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | low | canvas/tint-accent | 3.922 | 4.097 | #21304D | #172D4B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | medium | canvas/tint-accent | 6.158 | 6.433 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | muted | canvas/tint-accent | 5.068 | 5.294 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | noncompliant | canvas/tint-accent | 2.432 | 2.541 | #21304D | #172D4B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | partial | canvas/tint-accent | 6.158 | 6.433 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text | canvas/tint-accent | 11.084 | 11.578 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text-2 | canvas/tint-accent | 7.011 | 7.324 | #21304D | #172D4B | Pass | conservative candidate pairing; pill uses text |
| dark | azure | accent-text | canvas/accent-soft | 2.478 | 2.598 | #232B44 | #192942 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text | canvas/accent-soft | 11.694 | 12.264 | #232B44 | #192942 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text-2 | canvas/accent-soft | 7.397 | 7.757 | #232B44 | #192942 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | muted | canvas/accent-soft | 5.347 | 5.607 | #232B44 | #192942 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | canvas-mid | glass/tint-accent | 1.386 | 1.448 | #213756 | #2B3957 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | compliant | glass/tint-accent | 3.045 | 3.182 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | critical | glass/tint-accent | 1.414 | 1.478 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | danger-text | glass/tint-accent | 4.136 | 4.322 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | high | glass/tint-accent | 2.687 | 2.808 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | insufficient | glass/tint-accent | 4.544 | 4.748 | #2B3957 | #213756 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | low | glass/tint-accent | 3.417 | 3.571 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | medium | glass/tint-accent | 5.365 | 5.606 | #2B3957 | #213756 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | muted | glass/tint-accent | 4.415 | 4.614 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | noncompliant | glass/tint-accent | 2.119 | 2.214 | #2B3957 | #213756 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | partial | glass/tint-accent | 5.365 | 5.606 | #2B3957 | #213756 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text | glass/tint-accent | 9.657 | 10.091 | #2B3957 | #213756 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text-2 | glass/tint-accent | 6.108 | 6.383 | #2B3957 | #213756 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | accent-text | glass/accent-soft | 2.141 | 2.249 | #2E354F | #23334E | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text | glass/accent-soft | 10.105 | 10.615 | #2E354F | #23334E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text-2 | glass/accent-soft | 6.391 | 6.714 | #2E354F | #23334E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | muted | glass/accent-soft | 4.620 | 4.853 | #2E354F | #23334E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | canvas-mid | glass-strong/tint-accent | 1.478 | 1.545 | #253B5A | #2F3D5C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | compliant | glass-strong/tint-accent | 2.854 | 2.982 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | critical | glass-strong/tint-accent | 1.325 | 1.385 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | danger-text | glass-strong/tint-accent | 3.876 | 4.051 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | high | glass-strong/tint-accent | 2.518 | 2.632 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | insufficient | glass-strong/tint-accent | 4.258 | 4.451 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | low | glass-strong/tint-accent | 3.202 | 3.347 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | medium | glass-strong/tint-accent | 5.028 | 5.255 | #2F3D5C | #253B5A | Pass | conservative candidate pairing; pill uses text |
| dark | azure | muted | glass-strong/tint-accent | 4.138 | 4.325 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | noncompliant | glass-strong/tint-accent | 1.986 | 2.076 | #2F3D5C | #253B5A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | partial | glass-strong/tint-accent | 5.028 | 5.255 | #2F3D5C | #253B5A | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text | glass-strong/tint-accent | 9.049 | 9.458 | #2F3D5C | #253B5A | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text-2 | glass-strong/tint-accent | 5.724 | 5.983 | #2F3D5C | #253B5A | Pass | conservative candidate pairing; pill uses text |
| dark | azure | accent-text | glass-strong/accent-soft | 1.997 | 2.099 | #323A54 | #283853 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text | glass-strong/accent-soft | 9.426 | 9.907 | #323A54 | #283853 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text-2 | glass-strong/accent-soft | 5.963 | 6.266 | #323A54 | #283853 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | muted | glass-strong/accent-soft | 4.310 | 4.530 | #323A54 | #283853 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | canvas-mid | solid/tint-accent | 1.118 | 1.123 | #102844 | #102845 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | compliant | solid/tint-accent | 3.925 | 3.943 | #102845 | #102844 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | critical | solid/tint-accent | 1.822 | 1.831 | #102845 | #102844 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | danger-text | solid/tint-accent | 5.331 | 5.357 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | high | solid/tint-accent | 3.463 | 3.479 | #102845 | #102844 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | insufficient | solid/tint-accent | 5.857 | 5.884 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | low | solid/tint-accent | 4.405 | 4.425 | #102845 | #102844 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | medium | solid/tint-accent | 6.915 | 6.947 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | muted | solid/tint-accent | 5.691 | 5.718 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | noncompliant | solid/tint-accent | 2.731 | 2.744 | #102845 | #102844 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | azure | partial | solid/tint-accent | 6.915 | 6.947 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text | solid/tint-accent | 12.447 | 12.505 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | text-2 | solid/tint-accent | 7.873 | 7.910 | #102845 | #102844 | Pass | conservative candidate pairing; pill uses text |
| dark | azure | accent-text | solid/accent-soft | 2.800 | 2.812 | #11233B | #11233A | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text | solid/accent-soft | 13.214 | 13.275 | #11233B | #11233A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | text-2 | solid/accent-soft | 8.358 | 8.397 | #11233B | #11233A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | muted | solid/accent-soft | 6.042 | 6.069 | #11233B | #11233A | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | azure | on-accent | primary-button | 3.982 | 5.151 | #3C82CC | #1C6EC4 | Fail candidate | declared component pairing |
| dark | azure | on-accent | primary-kbd | 3.098 | 3.838 | #5B96D4 | #4085CD | Fail candidate | declared component pairing |
| dark | cobalt | accent-text | canvas | 2.323 | 2.461 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass | 1.976 | 2.108 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong | 1.825 | 1.949 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid | 2.648 | 2.661 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/hover | 2.009 | 2.142 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/press | 1.768 | 1.888 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/track | 1.768 | 1.888 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/field | 2.009 | 2.142 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/field-hover | 3.548 | 3.604 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/field-focus | 1.826 | 1.950 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/chip | 2.009 | 2.142 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/nav-selected | 1.768 | 1.888 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/secondary-button | 1.887 | 2.014 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/secondary-hover | 1.653 | 1.766 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/secondary-active | 2.009 | 2.142 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/file-button | 1.710 | 1.827 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/segment-selected | 1.493 | 1.594 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/kbd | 1.826 | 1.950 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-critical | 2.128 | 2.260 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-high | 1.846 | 1.973 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-medium | 1.500 | 1.602 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-low | 1.715 | 1.803 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-compliant | 1.769 | 1.858 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-partial | 1.500 | 1.602 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-noncompliant | 1.944 | 2.072 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/tint-insufficient | 1.558 | 1.651 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | canvas/mark | 1.149 | 1.216 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/hover | 1.695 | 1.812 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/press | 1.491 | 1.592 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/track | 1.491 | 1.592 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/field | 1.695 | 1.812 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/field-hover | 3.693 | 3.747 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/field-focus | 1.541 | 1.645 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/chip | 1.695 | 1.812 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/nav-selected | 1.491 | 1.592 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/secondary-button | 1.591 | 1.700 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/secondary-hover | 1.398 | 1.491 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/secondary-active | 1.695 | 1.812 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/file-button | 1.444 | 1.541 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/segment-selected | 1.267 | 1.349 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/kbd | 1.541 | 1.645 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-critical | 1.869 | 1.991 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-high | 1.606 | 1.718 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-medium | 1.295 | 1.380 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-low | 1.484 | 1.558 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-compliant | 1.532 | 1.607 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-partial | 1.295 | 1.380 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-noncompliant | 1.695 | 1.810 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/tint-insufficient | 1.343 | 1.420 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass/mark | 1.016 | 1.073 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/hover | 1.565 | 1.672 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/press | 1.379 | 1.471 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/track | 1.379 | 1.471 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/field | 1.565 | 1.672 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/field-hover | 3.759 | 3.813 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/field-focus | 1.424 | 1.519 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/chip | 1.565 | 1.672 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/nav-selected | 1.379 | 1.471 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/secondary-button | 1.469 | 1.568 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/secondary-hover | 1.294 | 1.378 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/secondary-active | 1.565 | 1.672 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/file-button | 1.336 | 1.424 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/segment-selected | 1.176 | 1.250 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/kbd | 1.424 | 1.519 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-critical | 1.758 | 1.872 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-high | 1.506 | 1.608 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-medium | 1.211 | 1.288 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-low | 1.388 | 1.456 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-compliant | 1.433 | 1.503 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-partial | 1.211 | 1.288 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-noncompliant | 1.590 | 1.697 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/tint-insufficient | 1.255 | 1.325 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | glass-strong/mark | 1.000 | 1.040 | #6F573C | #78573A | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/hover | 2.334 | 2.350 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/press | 2.069 | 2.083 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/track | 2.069 | 2.083 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/field | 2.334 | 2.350 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/field-hover | 3.461 | 3.467 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/field-focus | 2.135 | 2.150 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/chip | 2.334 | 2.350 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/nav-selected | 2.069 | 2.083 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/secondary-button | 2.202 | 2.217 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/secondary-hover | 1.937 | 1.951 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/secondary-active | 2.334 | 2.350 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/file-button | 2.003 | 2.017 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/segment-selected | 1.748 | 1.761 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/kbd | 2.135 | 2.150 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-critical | 2.411 | 2.427 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-high | 2.124 | 2.140 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-medium | 1.740 | 1.754 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-low | 1.951 | 1.961 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-compliant | 2.007 | 2.017 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-partial | 1.740 | 1.754 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-noncompliant | 2.226 | 2.242 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/tint-insufficient | 1.794 | 1.806 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | solid/mark | 1.306 | 1.315 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | cobalt | accent-text | modal-over-scrim | 2.657 | 2.666 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | cobalt | canvas-mid | canvas/tint-accent | 1.166 | 1.220 | #1D284F | #262A50 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | compliant | canvas/tint-accent | 3.614 | 3.783 | #262A50 | #1D284F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | critical | canvas/tint-accent | 1.678 | 1.756 | #262A50 | #1D284F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | danger-text | canvas/tint-accent | 4.910 | 5.138 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | high | canvas/tint-accent | 3.189 | 3.338 | #262A50 | #1D284F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | insufficient | canvas/tint-accent | 5.393 | 5.645 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | low | canvas/tint-accent | 4.056 | 4.245 | #262A50 | #1D284F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | medium | canvas/tint-accent | 6.368 | 6.664 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | muted | canvas/tint-accent | 5.241 | 5.485 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | noncompliant | canvas/tint-accent | 2.515 | 2.632 | #262A50 | #1D284F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | partial | canvas/tint-accent | 6.368 | 6.664 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text | canvas/tint-accent | 11.462 | 11.996 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text-2 | canvas/tint-accent | 7.250 | 7.588 | #262A50 | #1D284F | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | accent-text | canvas/accent-soft | 2.105 | 2.211 | #272846 | #1C2545 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text | canvas/accent-soft | 11.962 | 12.564 | #272846 | #1C2545 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text-2 | canvas/accent-soft | 7.566 | 7.947 | #272846 | #1C2545 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | muted | canvas/accent-soft | 5.469 | 5.744 | #272846 | #1C2545 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | canvas-mid | glass/tint-accent | 1.334 | 1.398 | #26325A | #30345B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | compliant | glass/tint-accent | 3.155 | 3.305 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | critical | glass/tint-accent | 1.465 | 1.535 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | danger-text | glass/tint-accent | 4.285 | 4.490 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | high | glass/tint-accent | 2.784 | 2.916 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | insufficient | glass/tint-accent | 4.708 | 4.932 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | low | glass/tint-accent | 3.540 | 3.709 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | medium | glass/tint-accent | 5.558 | 5.823 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | muted | glass/tint-accent | 4.574 | 4.793 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | noncompliant | glass/tint-accent | 2.195 | 2.300 | #30345B | #26325A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | partial | glass/tint-accent | 5.558 | 5.823 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text | glass/tint-accent | 10.004 | 10.482 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text-2 | glass/tint-accent | 6.328 | 6.630 | #30345B | #26325A | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | accent-text | glass/accent-soft | 1.823 | 1.919 | #313152 | #272F51 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text | glass/accent-soft | 10.354 | 10.901 | #313152 | #272F51 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text-2 | glass/accent-soft | 6.550 | 6.895 | #313152 | #272F51 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | muted | glass/accent-soft | 4.734 | 4.984 | #313152 | #272F51 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | canvas-mid | glass-strong/tint-accent | 1.422 | 1.490 | #2B365E | #34385F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | compliant | glass-strong/tint-accent | 2.959 | 3.101 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | critical | glass-strong/tint-accent | 1.374 | 1.440 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | danger-text | glass-strong/tint-accent | 4.020 | 4.212 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | high | glass-strong/tint-accent | 2.611 | 2.736 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | insufficient | glass-strong/tint-accent | 4.416 | 4.627 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | low | glass-strong/tint-accent | 3.321 | 3.480 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | medium | glass-strong/tint-accent | 5.213 | 5.463 | #34385F | #2B365E | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | muted | glass-strong/tint-accent | 4.291 | 4.496 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | noncompliant | glass-strong/tint-accent | 2.059 | 2.158 | #34385F | #2B365E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | partial | glass-strong/tint-accent | 5.213 | 5.463 | #34385F | #2B365E | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text | glass-strong/tint-accent | 9.384 | 9.834 | #34385F | #2B365E | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text-2 | glass-strong/tint-accent | 5.936 | 6.220 | #34385F | #2B365E | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | accent-text | glass-strong/accent-soft | 1.702 | 1.792 | #363656 | #2B3455 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text | glass-strong/accent-soft | 9.667 | 10.182 | #363656 | #2B3455 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text-2 | glass-strong/accent-soft | 6.115 | 6.440 | #363656 | #2B3455 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | muted | glass-strong/accent-soft | 4.420 | 4.655 | #363656 | #2B3455 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | canvas-mid | solid/tint-accent | 1.081 | 1.086 | #162247 | #172348 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | compliant | solid/tint-accent | 4.061 | 4.079 | #172348 | #162247 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | critical | solid/tint-accent | 1.886 | 1.894 | #172348 | #162247 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | danger-text | solid/tint-accent | 5.517 | 5.542 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | high | solid/tint-accent | 3.583 | 3.600 | #172348 | #162247 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | insufficient | solid/tint-accent | 6.060 | 6.088 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | low | solid/tint-accent | 4.558 | 4.578 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | medium | solid/tint-accent | 7.155 | 7.187 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | muted | solid/tint-accent | 5.889 | 5.915 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | noncompliant | solid/tint-accent | 2.826 | 2.839 | #172348 | #162247 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | cobalt | partial | solid/tint-accent | 7.155 | 7.187 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text | solid/tint-accent | 12.879 | 12.937 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | text-2 | solid/tint-accent | 8.147 | 8.183 | #172348 | #162247 | Pass | conservative candidate pairing; pill uses text |
| dark | cobalt | accent-text | solid/accent-soft | 2.379 | 2.390 | #161F3D | #151F3D | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text | solid/accent-soft | 13.516 | 13.580 | #161F3D | #151F3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | text-2 | solid/accent-soft | 8.549 | 8.590 | #161F3D | #151F3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | muted | solid/accent-soft | 6.180 | 6.209 | #161F3D | #151F3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | cobalt | on-accent | primary-button | 4.281 | 5.623 | #5074E0 | #345DDB | Fail candidate | declared component pairing |
| dark | cobalt | on-accent | primary-kbd | 3.278 | 4.117 | #6C8AE5 | #5477E1 | Fail candidate | declared component pairing |
| dark | midnight | accent-text | canvas | 1.423 | 1.508 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass | 1.211 | 1.291 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong | 1.118 | 1.194 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid | 1.622 | 1.630 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/hover | 1.231 | 1.312 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/press | 1.083 | 1.157 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/track | 1.083 | 1.157 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/field | 1.231 | 1.312 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/field-hover | 5.791 | 5.883 | #BBBBBF | #BEBCC0 | Pass | conservative candidate pairing |
| dark | midnight | accent-text | canvas/field-focus | 1.119 | 1.195 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/chip | 1.231 | 1.312 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/nav-selected | 1.083 | 1.157 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/secondary-button | 1.156 | 1.234 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/secondary-hover | 1.013 | 1.082 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/secondary-active | 1.231 | 1.312 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/file-button | 1.048 | 1.119 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/segment-selected | 1.024 | 1.093 | #3C3D48 | #463F4A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/kbd | 1.119 | 1.195 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-critical | 1.304 | 1.384 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-high | 1.131 | 1.208 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-medium | 1.019 | 1.088 | #4B3A2B | #543C2D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-low | 1.051 | 1.105 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-compliant | 1.084 | 1.138 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-partial | 1.019 | 1.088 | #4B3A2B | #543C2D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-noncompliant | 1.191 | 1.270 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/tint-insufficient | 1.000 | 1.048 | #373B4A | #413D4A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | canvas/mark | 1.342 | 1.421 | #644A2C | #6C4C2D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/hover | 1.039 | 1.110 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/press | 1.025 | 1.094 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/track | 1.025 | 1.094 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/field | 1.039 | 1.110 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/field-hover | 6.027 | 6.116 | #BFBFC3 | #C2C0C4 | Pass | conservative candidate pairing |
| dark | midnight | accent-text | glass/field-focus | 1.000 | 1.060 | #393B49 | #453D49 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/chip | 1.039 | 1.110 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/nav-selected | 1.025 | 1.094 | #3B3D4A | #473F4B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/secondary-button | 1.000 | 1.041 | #3F3A47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/secondary-hover | 1.095 | 1.168 | #40414E | #4B434F | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/secondary-active | 1.039 | 1.110 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/file-button | 1.059 | 1.131 | #3E3F4C | #49414D | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/segment-selected | 1.210 | 1.288 | #464754 | #514955 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/kbd | 1.000 | 1.060 | #393B49 | #453D49 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-critical | 1.145 | 1.220 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-high | 1.000 | 1.052 | #573233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-medium | 1.183 | 1.260 | #544336 | #5E4537 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-low | 1.048 | 1.100 | #2D4343 | #364544 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-compliant | 1.015 | 1.065 | #2A4142 | #344343 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-partial | 1.183 | 1.260 | #544336 | #5E4537 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-noncompliant | 1.038 | 1.109 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/tint-insufficient | 1.149 | 1.215 | #414454 | #4B4655 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass/mark | 1.522 | 1.607 | #6C5235 | #745336 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/hover | 1.000 | 1.043 | #3D3A47 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/press | 1.110 | 1.184 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/track | 1.110 | 1.184 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/field | 1.000 | 1.043 | #3D3A47 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/field-hover | 6.136 | 6.224 | #C0C1C5 | #C4C1C5 | Pass | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/field-focus | 1.075 | 1.147 | #3F404D | #4A424E | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/chip | 1.000 | 1.043 | #3D3A47 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/nav-selected | 1.110 | 1.184 | #41424F | #4C4450 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/secondary-button | 1.041 | 1.111 | #3C3E4B | #48404C | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/secondary-hover | 1.184 | 1.261 | #454653 | #504854 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/secondary-active | 1.000 | 1.043 | #3D3A47 | #443C48 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/file-button | 1.147 | 1.222 | #434451 | #4E4652 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/segment-selected | 1.306 | 1.388 | #4B4C58 | #564E5A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/kbd | 1.075 | 1.147 | #3F404D | #4A424E | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-critical | 1.077 | 1.147 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-high | 1.015 | 1.084 | #533436 | #5D3637 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-medium | 1.267 | 1.348 | #59483A | #624A3B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-low | 1.121 | 1.176 | #314747 | #3B4948 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-compliant | 1.086 | 1.139 | #2E4546 | #384747 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-partial | 1.267 | 1.348 | #59483A | #624A3B | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-noncompliant | 1.000 | 1.039 | #54323A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/tint-insufficient | 1.231 | 1.300 | #464858 | #4F4A59 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | glass-strong/mark | 1.611 | 1.698 | #705539 | #78573A | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/hover | 1.430 | 1.439 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/press | 1.267 | 1.276 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/track | 1.267 | 1.276 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/field | 1.430 | 1.439 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/field-hover | 5.649 | 5.660 | #B8B9BC | #B9B9BC | Pass | conservative candidate pairing |
| dark | midnight | accent-text | solid/field-focus | 1.308 | 1.317 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/chip | 1.430 | 1.439 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/nav-selected | 1.267 | 1.276 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/secondary-button | 1.349 | 1.358 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/secondary-hover | 1.187 | 1.196 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/secondary-active | 1.430 | 1.439 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/file-button | 1.227 | 1.236 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/segment-selected | 1.071 | 1.079 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/kbd | 1.308 | 1.317 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-critical | 1.477 | 1.487 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-high | 1.301 | 1.311 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-medium | 1.066 | 1.074 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-low | 1.195 | 1.202 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-compliant | 1.230 | 1.236 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-partial | 1.066 | 1.074 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-noncompliant | 1.364 | 1.374 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/tint-insufficient | 1.099 | 1.106 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | solid/mark | 1.241 | 1.250 | #5E4526 | #5F4526 | Fail candidate | conservative candidate pairing |
| dark | midnight | accent-text | modal-over-scrim | 1.628 | 1.633 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | midnight | canvas-mid | canvas/tint-accent | 1.077 | 1.126 | #1C233A | #25263B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | compliant | canvas/tint-accent | 3.914 | 4.095 | #25263B | #1C233A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | critical | canvas/tint-accent | 1.817 | 1.901 | #25263B | #1C233A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | danger-text | canvas/tint-accent | 5.317 | 5.562 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | high | canvas/tint-accent | 3.454 | 3.613 | #25263B | #1C233A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | insufficient | canvas/tint-accent | 5.841 | 6.111 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | low | canvas/tint-accent | 4.393 | 4.596 | #25263B | #1C233A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | medium | canvas/tint-accent | 6.896 | 7.214 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | muted | canvas/tint-accent | 5.675 | 5.938 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | noncompliant | canvas/tint-accent | 2.724 | 2.850 | #25263B | #1C233A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | partial | canvas/tint-accent | 6.896 | 7.214 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text | canvas/tint-accent | 12.412 | 12.986 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text-2 | canvas/tint-accent | 7.851 | 8.214 | #25263B | #1C233A | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | accent-text | canvas/accent-soft | 1.363 | 1.431 | #262437 | #1C2236 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text | canvas/accent-soft | 12.636 | 13.266 | #262437 | #1C2236 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text-2 | canvas/accent-soft | 7.993 | 8.391 | #262437 | #1C2236 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | muted | canvas/accent-soft | 5.778 | 6.066 | #262437 | #1C2236 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | canvas-mid | glass/tint-accent | 1.224 | 1.284 | #252D45 | #2F2F46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | compliant | glass/tint-accent | 3.434 | 3.601 | #2F2F46 | #252D45 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | critical | glass/tint-accent | 1.595 | 1.672 | #2F2F46 | #252D45 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | danger-text | glass/tint-accent | 4.665 | 4.892 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | high | glass/tint-accent | 3.030 | 3.178 | #2F2F46 | #252D45 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | insufficient | glass/tint-accent | 5.124 | 5.374 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | low | glass/tint-accent | 3.854 | 4.042 | #2F2F46 | #252D45 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | medium | glass/tint-accent | 6.050 | 6.345 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | muted | glass/tint-accent | 4.979 | 5.222 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | noncompliant | glass/tint-accent | 2.390 | 2.506 | #2F2F46 | #252D45 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | partial | glass/tint-accent | 6.050 | 6.345 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text | glass/tint-accent | 10.890 | 11.421 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text-2 | glass/tint-accent | 6.888 | 7.224 | #2F2F46 | #252D45 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | accent-text | glass/accent-soft | 1.185 | 1.248 | #312E42 | #262C41 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text | glass/accent-soft | 10.989 | 11.576 | #312E42 | #262C41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text-2 | glass/accent-soft | 6.951 | 7.322 | #312E42 | #262C41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | muted | glass/accent-soft | 5.024 | 5.293 | #312E42 | #262C41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | canvas-mid | glass-strong/tint-accent | 1.303 | 1.367 | #2A3149 | #34334A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | compliant | glass-strong/tint-accent | 3.225 | 3.384 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | critical | glass-strong/tint-accent | 1.498 | 1.571 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | danger-text | glass-strong/tint-accent | 4.381 | 4.597 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | high | glass-strong/tint-accent | 2.846 | 2.986 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | insufficient | glass-strong/tint-accent | 4.813 | 5.050 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | low | glass-strong/tint-accent | 3.619 | 3.798 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | medium | glass-strong/tint-accent | 5.682 | 5.962 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | muted | glass-strong/tint-accent | 4.676 | 4.907 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | noncompliant | glass-strong/tint-accent | 2.244 | 2.355 | #34334A | #2A3149 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | partial | glass-strong/tint-accent | 5.682 | 5.962 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text | glass-strong/tint-accent | 10.227 | 10.732 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text-2 | glass-strong/tint-accent | 6.469 | 6.788 | #34334A | #2A3149 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | accent-text | glass-strong/accent-soft | 1.108 | 1.168 | #353347 | #2B3146 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text | glass-strong/accent-soft | 10.272 | 10.829 | #353347 | #2B3146 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text-2 | glass-strong/accent-soft | 6.497 | 6.849 | #353347 | #2B3146 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | muted | glass-strong/accent-soft | 4.697 | 4.951 | #353347 | #2B3146 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | canvas-mid | solid/tint-accent | 1.004 | 1.008 | #151E33 | #161E33 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | compliant | solid/tint-accent | 4.372 | 4.391 | #161E33 | #151E33 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | critical | solid/tint-accent | 2.030 | 2.039 | #161E33 | #151E33 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | danger-text | solid/tint-accent | 5.939 | 5.965 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | high | solid/tint-accent | 3.858 | 3.875 | #161E33 | #151E33 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | insufficient | solid/tint-accent | 6.525 | 6.553 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | low | solid/tint-accent | 4.907 | 4.928 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | medium | solid/tint-accent | 7.703 | 7.737 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | muted | solid/tint-accent | 6.340 | 6.368 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | noncompliant | solid/tint-accent | 3.043 | 3.056 | #161E33 | #151E33 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | midnight | partial | solid/tint-accent | 7.703 | 7.737 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text | solid/tint-accent | 13.866 | 13.927 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | text-2 | solid/tint-accent | 8.770 | 8.809 | #161E33 | #151E33 | Pass | conservative candidate pairing; pill uses text |
| dark | midnight | accent-text | solid/accent-soft | 1.532 | 1.539 | #161C2E | #151C2E | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text | solid/accent-soft | 14.203 | 14.269 | #161C2E | #151C2E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | text-2 | solid/accent-soft | 8.984 | 9.025 | #161C2E | #151C2E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | muted | solid/accent-soft | 6.494 | 6.524 | #161C2E | #151C2E | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | midnight | on-accent | primary-button | 5.500 | 7.874 | #50689C | #33508C | Pass | declared component pairing |
| dark | midnight | on-accent | primary-kbd | 3.928 | 5.230 | #6C81AC | #546C9E | Fail candidate | declared component pairing |
| dark | teal | accent-text | canvas | 2.664 | 2.822 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass | 2.266 | 2.417 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong | 2.092 | 2.234 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid | 3.035 | 3.051 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/hover | 2.304 | 2.456 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/press | 2.027 | 2.165 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/track | 2.027 | 2.165 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/field | 2.304 | 2.456 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/field-hover | 3.094 | 3.143 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/field-focus | 2.094 | 2.236 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/chip | 2.304 | 2.456 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/nav-selected | 2.027 | 2.165 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/secondary-button | 2.163 | 2.309 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/secondary-hover | 1.896 | 2.025 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/secondary-active | 2.304 | 2.456 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/file-button | 1.960 | 2.094 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/segment-selected | 1.712 | 1.827 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/kbd | 2.094 | 2.236 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-critical | 2.440 | 2.591 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-high | 2.116 | 2.261 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-medium | 1.720 | 1.837 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-low | 1.967 | 2.067 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-compliant | 2.028 | 2.130 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-partial | 1.720 | 1.837 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-noncompliant | 2.228 | 2.376 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/tint-insufficient | 1.786 | 1.892 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | canvas/mark | 1.317 | 1.394 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/hover | 1.944 | 2.077 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/press | 1.710 | 1.826 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/track | 1.710 | 1.826 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/field | 1.944 | 2.077 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/field-hover | 3.221 | 3.268 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/field-focus | 1.766 | 1.886 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/chip | 1.944 | 2.077 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/nav-selected | 1.710 | 1.826 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/secondary-button | 1.824 | 1.948 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/secondary-hover | 1.602 | 1.709 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/secondary-active | 1.944 | 2.077 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/file-button | 1.655 | 1.766 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/segment-selected | 1.452 | 1.546 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/kbd | 1.766 | 1.886 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-critical | 2.143 | 2.283 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-high | 1.841 | 1.969 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-medium | 1.485 | 1.582 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-low | 1.702 | 1.786 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-compliant | 1.757 | 1.843 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-partial | 1.485 | 1.582 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-noncompliant | 1.943 | 2.075 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/tint-insufficient | 1.540 | 1.628 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass/mark | 1.165 | 1.230 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/hover | 1.794 | 1.916 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/press | 1.581 | 1.686 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/track | 1.581 | 1.686 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/field | 1.794 | 1.916 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/field-hover | 3.279 | 3.326 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/field-focus | 1.632 | 1.741 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/chip | 1.794 | 1.916 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/nav-selected | 1.581 | 1.686 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/secondary-button | 1.685 | 1.798 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/secondary-hover | 1.484 | 1.580 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/secondary-active | 1.794 | 1.916 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/file-button | 1.532 | 1.632 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/segment-selected | 1.348 | 1.433 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/kbd | 1.632 | 1.741 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-critical | 2.015 | 2.146 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-high | 1.726 | 1.844 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-medium | 1.389 | 1.477 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-low | 1.591 | 1.669 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-compliant | 1.643 | 1.723 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-partial | 1.389 | 1.477 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-noncompliant | 1.823 | 1.945 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/tint-insufficient | 1.439 | 1.520 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | glass-strong/mark | 1.102 | 1.162 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/hover | 2.676 | 2.694 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/press | 2.372 | 2.388 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/track | 2.372 | 2.388 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/field | 2.676 | 2.694 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/field-hover | 3.019 | 3.024 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/field-focus | 2.448 | 2.465 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/chip | 2.676 | 2.694 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/nav-selected | 2.372 | 2.388 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/secondary-button | 2.524 | 2.541 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/secondary-hover | 2.221 | 2.237 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/secondary-active | 2.676 | 2.694 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/file-button | 2.296 | 2.312 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/segment-selected | 2.004 | 2.019 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/kbd | 2.448 | 2.465 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-critical | 2.765 | 2.783 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-high | 2.435 | 2.454 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-medium | 1.995 | 2.010 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-low | 2.237 | 2.249 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-compliant | 2.301 | 2.313 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-partial | 1.995 | 2.010 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-noncompliant | 2.552 | 2.571 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/tint-insufficient | 2.057 | 2.070 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | solid/mark | 1.498 | 1.508 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | teal | accent-text | modal-over-scrim | 3.046 | 3.057 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | teal | canvas-mid | canvas/tint-accent | 1.200 | 1.255 | #182F3D | #22313E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | compliant | canvas/tint-accent | 3.514 | 3.675 | #22313E | #182F3D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | critical | canvas/tint-accent | 1.632 | 1.706 | #22313E | #182F3D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | danger-text | canvas/tint-accent | 4.774 | 4.992 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | high | canvas/tint-accent | 3.101 | 3.243 | #22313E | #182F3D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | insufficient | canvas/tint-accent | 5.244 | 5.484 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | low | canvas/tint-accent | 3.944 | 4.124 | #22313E | #182F3D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | medium | canvas/tint-accent | 6.192 | 6.474 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | muted | canvas/tint-accent | 5.096 | 5.328 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | noncompliant | canvas/tint-accent | 2.446 | 2.557 | #22313E | #182F3D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | partial | canvas/tint-accent | 6.192 | 6.474 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text | canvas/tint-accent | 11.145 | 11.654 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text-2 | canvas/tint-accent | 7.050 | 7.371 | #22313E | #182F3D | Pass | conservative candidate pairing; pill uses text |
| dark | teal | accent-text | canvas/accent-soft | 2.368 | 2.485 | #232C39 | #192A38 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text | canvas/accent-soft | 11.732 | 12.314 | #232C39 | #192A38 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text-2 | canvas/accent-soft | 7.421 | 7.789 | #232C39 | #192A38 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | muted | canvas/accent-soft | 5.364 | 5.630 | #232C39 | #192A38 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | canvas-mid | glass/tint-accent | 1.377 | 1.441 | #223848 | #2C3A49 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | compliant | glass/tint-accent | 3.060 | 3.201 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | critical | glass/tint-accent | 1.421 | 1.486 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | danger-text | glass/tint-accent | 4.157 | 4.348 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | high | glass/tint-accent | 2.700 | 2.824 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | insufficient | glass/tint-accent | 4.567 | 4.777 | #2C3A49 | #223848 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | low | glass/tint-accent | 3.434 | 3.592 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | medium | glass/tint-accent | 5.392 | 5.640 | #2C3A49 | #223848 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | muted | glass/tint-accent | 4.437 | 4.641 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | noncompliant | glass/tint-accent | 2.130 | 2.228 | #2C3A49 | #223848 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | partial | glass/tint-accent | 5.392 | 5.640 | #2C3A49 | #223848 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text | glass/tint-accent | 9.705 | 10.151 | #2C3A49 | #223848 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text-2 | glass/tint-accent | 6.139 | 6.421 | #2C3A49 | #223848 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | accent-text | glass/accent-soft | 2.045 | 2.150 | #2E3645 | #233443 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text | glass/accent-soft | 10.134 | 10.655 | #2E3645 | #233443 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text-2 | glass/accent-soft | 6.410 | 6.740 | #2E3645 | #233443 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | muted | glass/accent-soft | 4.634 | 4.872 | #2E3645 | #233443 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | canvas-mid | glass-strong/tint-accent | 1.470 | 1.538 | #263D4C | #303F4D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | compliant | glass-strong/tint-accent | 2.866 | 2.999 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | critical | glass-strong/tint-accent | 1.331 | 1.392 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | danger-text | glass-strong/tint-accent | 3.894 | 4.073 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | high | glass-strong/tint-accent | 2.529 | 2.646 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | insufficient | glass-strong/tint-accent | 4.277 | 4.475 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | low | glass-strong/tint-accent | 3.217 | 3.365 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | medium | glass-strong/tint-accent | 5.050 | 5.283 | #303F4D | #263D4C | Pass | conservative candidate pairing; pill uses text |
| dark | teal | muted | glass-strong/tint-accent | 4.156 | 4.348 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | noncompliant | glass-strong/tint-accent | 1.995 | 2.087 | #303F4D | #263D4C | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | partial | glass-strong/tint-accent | 5.050 | 5.283 | #303F4D | #263D4C | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text | glass-strong/tint-accent | 9.090 | 9.510 | #303F4D | #263D4C | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text-2 | glass-strong/tint-accent | 5.750 | 6.015 | #303F4D | #263D4C | Pass | conservative candidate pairing; pill uses text |
| dark | teal | accent-text | glass-strong/accent-soft | 1.907 | 2.006 | #333B49 | #283948 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text | glass-strong/accent-soft | 9.451 | 9.940 | #333B49 | #283948 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text-2 | glass-strong/accent-soft | 5.978 | 6.287 | #333B49 | #283948 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | muted | glass-strong/accent-soft | 4.321 | 4.545 | #333B49 | #283948 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | canvas-mid | solid/tint-accent | 1.111 | 1.116 | #112935 | #112A36 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | compliant | solid/tint-accent | 3.951 | 3.969 | #112A36 | #112935 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | critical | solid/tint-accent | 1.834 | 1.843 | #112A36 | #112935 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | danger-text | solid/tint-accent | 5.366 | 5.391 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | high | solid/tint-accent | 3.486 | 3.502 | #112A36 | #112935 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | insufficient | solid/tint-accent | 5.895 | 5.922 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | low | solid/tint-accent | 4.434 | 4.454 | #112A36 | #112935 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | medium | solid/tint-accent | 6.960 | 6.992 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | muted | solid/tint-accent | 5.728 | 5.754 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | noncompliant | solid/tint-accent | 2.749 | 2.762 | #112A36 | #112935 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | teal | partial | solid/tint-accent | 6.960 | 6.992 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text | solid/tint-accent | 12.528 | 12.585 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | text-2 | solid/tint-accent | 7.925 | 7.961 | #112A36 | #112935 | Pass | conservative candidate pairing; pill uses text |
| dark | teal | accent-text | solid/accent-soft | 2.677 | 2.689 | #132430 | #122430 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text | solid/accent-soft | 13.265 | 13.327 | #132430 | #122430 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | text-2 | solid/accent-soft | 8.391 | 8.430 | #132430 | #122430 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | muted | solid/accent-soft | 6.065 | 6.093 | #132430 | #122430 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | teal | on-accent | primary-button | 4.070 | 5.311 | #308997 | #0E7686 | Fail candidate | declared component pairing |
| dark | teal | on-accent | primary-kbd | 3.149 | 3.919 | #519CA8 | #358C99 | Fail candidate | declared component pairing |
| dark | violet | accent-text | canvas | 2.426 | 2.570 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass | 2.064 | 2.202 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong | 1.906 | 2.035 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid | 2.765 | 2.779 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/hover | 2.098 | 2.237 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/press | 1.846 | 1.972 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/track | 1.846 | 1.972 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/field | 2.098 | 2.237 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/field-hover | 3.397 | 3.451 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/field-focus | 1.907 | 2.037 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/chip | 2.098 | 2.237 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/nav-selected | 1.846 | 1.972 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/secondary-button | 1.970 | 2.103 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/secondary-hover | 1.727 | 1.845 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/secondary-active | 2.098 | 2.237 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/file-button | 1.786 | 1.908 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/segment-selected | 1.559 | 1.664 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/kbd | 1.907 | 2.037 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-critical | 2.223 | 2.360 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-high | 1.927 | 2.060 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-medium | 1.567 | 1.673 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-low | 1.791 | 1.883 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-compliant | 1.848 | 1.940 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-partial | 1.567 | 1.673 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-noncompliant | 2.030 | 2.164 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/tint-insufficient | 1.627 | 1.724 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | canvas/mark | 1.199 | 1.270 | #6C4C2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/hover | 1.771 | 1.892 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/press | 1.558 | 1.663 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/track | 1.558 | 1.663 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/field | 1.771 | 1.892 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/field-hover | 3.536 | 3.588 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/field-focus | 1.609 | 1.718 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/chip | 1.771 | 1.892 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/nav-selected | 1.558 | 1.663 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/secondary-button | 1.661 | 1.775 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/secondary-hover | 1.459 | 1.557 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/secondary-active | 1.771 | 1.892 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/file-button | 1.508 | 1.609 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/segment-selected | 1.323 | 1.408 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/kbd | 1.609 | 1.718 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-critical | 1.952 | 2.080 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-high | 1.677 | 1.794 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-medium | 1.352 | 1.441 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-low | 1.550 | 1.627 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-compliant | 1.600 | 1.679 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-partial | 1.352 | 1.441 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-noncompliant | 1.770 | 1.891 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/tint-insufficient | 1.403 | 1.483 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass/mark | 1.061 | 1.120 | #745336 | #6C5235 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/hover | 1.634 | 1.746 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/press | 1.440 | 1.536 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/track | 1.440 | 1.536 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/field | 1.634 | 1.746 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/field-hover | 3.600 | 3.651 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/field-focus | 1.487 | 1.586 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/chip | 1.634 | 1.746 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/nav-selected | 1.440 | 1.536 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/secondary-button | 1.535 | 1.638 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/secondary-hover | 1.351 | 1.439 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/secondary-active | 1.634 | 1.746 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/file-button | 1.395 | 1.487 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/segment-selected | 1.228 | 1.305 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/kbd | 1.487 | 1.586 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-critical | 1.836 | 1.955 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-high | 1.573 | 1.680 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-medium | 1.265 | 1.345 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-low | 1.449 | 1.520 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-compliant | 1.497 | 1.569 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-partial | 1.265 | 1.345 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-noncompliant | 1.661 | 1.772 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/tint-insufficient | 1.311 | 1.384 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | glass-strong/mark | 1.004 | 1.058 | #78573A | #705539 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/hover | 2.438 | 2.454 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/press | 2.160 | 2.175 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/track | 2.160 | 2.175 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/field | 2.438 | 2.454 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/field-hover | 3.314 | 3.320 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/field-focus | 2.230 | 2.245 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/chip | 2.438 | 2.454 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/nav-selected | 2.160 | 2.175 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/secondary-button | 2.299 | 2.315 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/secondary-hover | 2.023 | 2.038 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/secondary-active | 2.438 | 2.454 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/file-button | 2.091 | 2.106 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/segment-selected | 1.826 | 1.839 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/kbd | 2.230 | 2.245 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-critical | 2.518 | 2.535 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-high | 2.218 | 2.235 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-medium | 1.817 | 1.831 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-low | 2.038 | 2.048 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-compliant | 2.096 | 2.107 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-partial | 1.817 | 1.831 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-noncompliant | 2.324 | 2.342 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/tint-insufficient | 1.873 | 1.886 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | solid/mark | 1.364 | 1.374 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | violet | accent-text | modal-over-scrim | 2.775 | 2.784 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | violet | canvas-mid | canvas/tint-accent | 1.178 | 1.242 | #2D244F | #372750 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | compliant | canvas/tint-accent | 3.549 | 3.744 | #372750 | #2D244F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | critical | canvas/tint-accent | 1.648 | 1.739 | #372750 | #2D244F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | danger-text | canvas/tint-accent | 4.820 | 5.086 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | high | canvas/tint-accent | 3.131 | 3.304 | #372750 | #2D244F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | insufficient | canvas/tint-accent | 5.295 | 5.587 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | low | canvas/tint-accent | 3.982 | 4.202 | #372750 | #2D244F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | medium | canvas/tint-accent | 6.252 | 6.596 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | muted | canvas/tint-accent | 5.145 | 5.429 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | noncompliant | canvas/tint-accent | 2.469 | 2.606 | #372750 | #2D244F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | partial | canvas/tint-accent | 6.252 | 6.596 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text | canvas/tint-accent | 11.253 | 11.873 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text-2 | canvas/tint-accent | 7.118 | 7.510 | #372750 | #2D244F | Pass | conservative candidate pairing; pill uses text |
| dark | violet | accent-text | canvas/accent-soft | 2.168 | 2.293 | #332546 | #282245 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text | canvas/accent-soft | 11.797 | 12.472 | #332546 | #282245 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text-2 | canvas/accent-soft | 7.462 | 7.889 | #332546 | #282245 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | muted | canvas/accent-soft | 5.394 | 5.703 | #332546 | #282245 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | canvas-mid | glass/tint-accent | 1.349 | 1.425 | #372E59 | #41305B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | compliant | glass/tint-accent | 3.093 | 3.267 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | critical | glass/tint-accent | 1.436 | 1.517 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | danger-text | glass/tint-accent | 4.201 | 4.439 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | high | glass/tint-accent | 2.729 | 2.883 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | insufficient | glass/tint-accent | 4.615 | 4.876 | #41305B | #372E59 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | low | glass/tint-accent | 3.471 | 3.667 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | medium | glass/tint-accent | 5.449 | 5.757 | #41305B | #372E59 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | muted | glass/tint-accent | 4.485 | 4.738 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | noncompliant | glass/tint-accent | 2.152 | 2.274 | #41305B | #372E59 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | partial | glass/tint-accent | 5.449 | 5.757 | #41305B | #372E59 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text | glass/tint-accent | 9.809 | 10.362 | #41305B | #372E59 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text-2 | glass/tint-accent | 6.204 | 6.554 | #41305B | #372E59 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | accent-text | glass/accent-soft | 1.875 | 1.987 | #3D2F51 | #332D50 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text | glass/accent-soft | 10.199 | 10.810 | #3D2F51 | #332D50 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text-2 | glass/accent-soft | 6.451 | 6.837 | #3D2F51 | #332D50 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | muted | glass/accent-soft | 4.663 | 4.943 | #3D2F51 | #332D50 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | canvas-mid | glass-strong/tint-accent | 1.439 | 1.520 | #3B325E | #45345F | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | compliant | glass-strong/tint-accent | 2.901 | 3.064 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | critical | glass-strong/tint-accent | 1.347 | 1.423 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | danger-text | glass-strong/tint-accent | 3.941 | 4.162 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | high | glass-strong/tint-accent | 2.560 | 2.703 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | insufficient | glass-strong/tint-accent | 4.329 | 4.572 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | low | glass-strong/tint-accent | 3.256 | 3.439 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | medium | glass-strong/tint-accent | 5.112 | 5.398 | #45345F | #3B325E | Pass | conservative candidate pairing; pill uses text |
| dark | violet | muted | glass-strong/tint-accent | 4.207 | 4.443 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | noncompliant | glass-strong/tint-accent | 2.019 | 2.132 | #45345F | #3B325E | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | partial | glass-strong/tint-accent | 5.112 | 5.398 | #45345F | #3B325E | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text | glass-strong/tint-accent | 9.201 | 9.717 | #45345F | #3B325E | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text-2 | glass-strong/tint-accent | 5.820 | 6.146 | #45345F | #3B325E | Pass | conservative candidate pairing; pill uses text |
| dark | violet | accent-text | glass-strong/accent-soft | 1.751 | 1.855 | #423456 | #373255 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text | glass-strong/accent-soft | 9.523 | 10.092 | #423456 | #373255 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text-2 | glass-strong/accent-soft | 6.024 | 6.384 | #423456 | #373255 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | muted | glass-strong/accent-soft | 4.354 | 4.615 | #423456 | #373255 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | canvas-mid | solid/tint-accent | 1.089 | 1.095 | #261F47 | #281F47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | compliant | solid/tint-accent | 4.025 | 4.048 | #281F47 | #261F47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | critical | solid/tint-accent | 1.869 | 1.880 | #281F47 | #261F47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | danger-text | solid/tint-accent | 5.468 | 5.499 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | high | solid/tint-accent | 3.552 | 3.572 | #281F47 | #261F47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | insufficient | solid/tint-accent | 6.007 | 6.041 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | low | solid/tint-accent | 4.517 | 4.543 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | medium | solid/tint-accent | 7.092 | 7.132 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | muted | solid/tint-accent | 5.837 | 5.870 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | noncompliant | solid/tint-accent | 2.801 | 2.817 | #281F47 | #261F47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | violet | partial | solid/tint-accent | 7.092 | 7.132 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text | solid/tint-accent | 12.765 | 12.838 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | text-2 | solid/tint-accent | 8.074 | 8.121 | #281F47 | #261F47 | Pass | conservative candidate pairing; pill uses text |
| dark | violet | accent-text | solid/accent-soft | 2.469 | 2.483 | #221D3D | #211D3D | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text | solid/accent-soft | 13.433 | 13.510 | #221D3D | #211D3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | text-2 | solid/accent-soft | 8.497 | 8.545 | #221D3D | #211D3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | muted | solid/accent-soft | 6.142 | 6.177 | #221D3D | #211D3D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | violet | on-accent | primary-button | 4.503 | 5.982 | #7F62DC | #6A48D6 | Pass | declared component pairing |
| dark | violet | on-accent | primary-kbd | 3.408 | 4.322 | #937BE1 | #8265DD | Fail candidate | declared component pairing |
| dark | plum | accent-text | canvas | 1.995 | 2.114 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass | 1.697 | 1.811 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong | 1.567 | 1.674 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid | 2.274 | 2.286 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/hover | 1.726 | 1.840 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/press | 1.518 | 1.622 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/track | 1.518 | 1.622 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/field | 1.726 | 1.840 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/field-hover | 4.131 | 4.196 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/field-focus | 1.569 | 1.675 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/chip | 1.726 | 1.840 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/nav-selected | 1.518 | 1.622 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/secondary-button | 1.620 | 1.730 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/secondary-hover | 1.420 | 1.517 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/secondary-active | 1.726 | 1.840 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/file-button | 1.469 | 1.569 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/segment-selected | 1.282 | 1.369 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/kbd | 1.569 | 1.675 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-critical | 1.828 | 1.941 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-high | 1.585 | 1.694 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-medium | 1.289 | 1.376 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-low | 1.473 | 1.549 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-compliant | 1.520 | 1.595 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-partial | 1.289 | 1.376 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-noncompliant | 1.669 | 1.780 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/tint-insufficient | 1.338 | 1.418 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | canvas/mark | 1.000 | 1.045 | #6A4B2D | #644A2C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/hover | 1.456 | 1.556 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/press | 1.281 | 1.368 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/track | 1.281 | 1.368 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/field | 1.456 | 1.556 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/field-hover | 4.299 | 4.363 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/field-focus | 1.323 | 1.413 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/chip | 1.456 | 1.556 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/nav-selected | 1.281 | 1.368 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/secondary-button | 1.366 | 1.460 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/secondary-hover | 1.200 | 1.280 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/secondary-active | 1.456 | 1.556 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/file-button | 1.240 | 1.323 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/segment-selected | 1.088 | 1.158 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/kbd | 1.323 | 1.413 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-critical | 1.605 | 1.710 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-high | 1.379 | 1.475 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-medium | 1.112 | 1.185 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-low | 1.275 | 1.338 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-compliant | 1.316 | 1.381 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-partial | 1.112 | 1.185 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-noncompliant | 1.456 | 1.555 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/tint-insufficient | 1.154 | 1.220 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass/mark | 1.085 | 1.146 | #6C5235 | #745336 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/hover | 1.344 | 1.436 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/press | 1.184 | 1.263 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/track | 1.184 | 1.263 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/field | 1.344 | 1.436 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/field-hover | 4.377 | 4.440 | #C0C1C5 | #C4C1C5 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/field-focus | 1.223 | 1.304 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/chip | 1.344 | 1.436 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/nav-selected | 1.184 | 1.263 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/secondary-button | 1.262 | 1.347 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/secondary-hover | 1.111 | 1.184 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/secondary-active | 1.344 | 1.436 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/file-button | 1.147 | 1.223 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/segment-selected | 1.010 | 1.073 | #564E5A | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/kbd | 1.223 | 1.304 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-critical | 1.510 | 1.607 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-high | 1.293 | 1.381 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-medium | 1.040 | 1.106 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-low | 1.192 | 1.250 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-compliant | 1.231 | 1.291 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-partial | 1.040 | 1.106 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-noncompliant | 1.366 | 1.457 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/tint-insufficient | 1.078 | 1.138 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | glass-strong/mark | 1.149 | 1.211 | #705539 | #78573A | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/hover | 2.005 | 2.018 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/press | 1.777 | 1.789 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/track | 1.777 | 1.789 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/field | 2.005 | 2.018 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/field-hover | 4.029 | 4.037 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/field-focus | 1.834 | 1.846 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/chip | 2.005 | 2.018 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/nav-selected | 1.777 | 1.789 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/secondary-button | 1.891 | 1.904 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/secondary-hover | 1.664 | 1.676 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/secondary-active | 2.005 | 2.018 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/file-button | 1.720 | 1.732 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/segment-selected | 1.501 | 1.513 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/kbd | 1.834 | 1.846 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-critical | 2.071 | 2.085 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-high | 1.824 | 1.838 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-medium | 1.495 | 1.506 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-low | 1.676 | 1.685 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-compliant | 1.724 | 1.733 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-partial | 1.495 | 1.506 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-noncompliant | 1.912 | 1.926 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/tint-insufficient | 1.541 | 1.551 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | solid/mark | 1.122 | 1.130 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | plum | accent-text | modal-over-scrim | 2.282 | 2.290 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | plum | canvas-mid | canvas/tint-accent | 1.127 | 1.193 | #33213B | #3D233D | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | compliant | canvas/tint-accent | 3.694 | 3.913 | #3D233D | #33213B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | critical | canvas/tint-accent | 1.715 | 1.817 | #3D233D | #33213B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | danger-text | canvas/tint-accent | 5.018 | 5.315 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | high | canvas/tint-accent | 3.260 | 3.452 | #3D233D | #33213B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | insufficient | canvas/tint-accent | 5.513 | 5.839 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | low | canvas/tint-accent | 4.146 | 4.391 | #3D233D | #33213B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | medium | canvas/tint-accent | 6.509 | 6.893 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | muted | canvas/tint-accent | 5.357 | 5.673 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | noncompliant | canvas/tint-accent | 2.571 | 2.723 | #3D233D | #33213B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | partial | canvas/tint-accent | 6.509 | 6.893 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text | canvas/tint-accent | 11.716 | 12.408 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text-2 | canvas/tint-accent | 7.411 | 7.848 | #3D233D | #33213B | Pass | conservative candidate pairing; pill uses text |
| dark | plum | accent-text | canvas/accent-soft | 1.835 | 1.945 | #372238 | #2D2036 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text | canvas/accent-soft | 12.137 | 12.868 | #372238 | #2D2036 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text-2 | canvas/accent-soft | 7.677 | 8.139 | #372238 | #2D2036 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | muted | canvas/accent-soft | 5.549 | 5.884 | #372238 | #2D2036 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | canvas-mid | glass/tint-accent | 1.286 | 1.365 | #3D2A46 | #472C47 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | compliant | glass/tint-accent | 3.230 | 3.428 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | critical | glass/tint-accent | 1.500 | 1.592 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | danger-text | glass/tint-accent | 4.387 | 4.657 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | high | glass/tint-accent | 2.850 | 3.025 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | insufficient | glass/tint-accent | 4.819 | 5.116 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | low | glass/tint-accent | 3.625 | 3.847 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | medium | glass/tint-accent | 5.690 | 6.040 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | muted | glass/tint-accent | 4.683 | 4.971 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | noncompliant | glass/tint-accent | 2.248 | 2.386 | #472C47 | #3D2A46 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | partial | glass/tint-accent | 5.690 | 6.040 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text | glass/tint-accent | 10.242 | 10.871 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text-2 | glass/tint-accent | 6.478 | 6.876 | #472C47 | #3D2A46 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | accent-text | glass/accent-soft | 1.591 | 1.692 | #422C43 | #372A42 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text | glass/accent-soft | 10.522 | 11.192 | #422C43 | #372A42 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text-2 | glass/accent-soft | 6.655 | 7.079 | #422C43 | #372A42 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | muted | glass/accent-soft | 4.811 | 5.117 | #422C43 | #372A42 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | canvas-mid | glass-strong/tint-accent | 1.370 | 1.454 | #412F4A | #4B304B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | compliant | glass-strong/tint-accent | 3.032 | 3.217 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | critical | glass-strong/tint-accent | 1.408 | 1.494 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | danger-text | glass-strong/tint-accent | 4.119 | 4.370 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | high | glass-strong/tint-accent | 2.676 | 2.839 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | insufficient | glass-strong/tint-accent | 4.525 | 4.801 | #4B304B | #412F4A | Pass | conservative candidate pairing; pill uses text |
| dark | plum | low | glass-strong/tint-accent | 3.403 | 3.610 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | medium | glass-strong/tint-accent | 5.342 | 5.668 | #4B304B | #412F4A | Pass | conservative candidate pairing; pill uses text |
| dark | plum | muted | glass-strong/tint-accent | 4.397 | 4.665 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | noncompliant | glass-strong/tint-accent | 2.110 | 2.239 | #4B304B | #412F4A | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | partial | glass-strong/tint-accent | 5.342 | 5.668 | #4B304B | #412F4A | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text | glass-strong/tint-accent | 9.616 | 10.202 | #4B304B | #412F4A | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text-2 | glass-strong/tint-accent | 6.083 | 6.453 | #4B304B | #412F4A | Pass | conservative candidate pairing; pill uses text |
| dark | plum | accent-text | glass-strong/accent-soft | 1.486 | 1.581 | #463148 | #3C2F47 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text | glass-strong/accent-soft | 9.832 | 10.457 | #463148 | #3C2F47 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text-2 | glass-strong/accent-soft | 6.219 | 6.614 | #463148 | #3C2F47 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | muted | glass-strong/accent-soft | 4.496 | 4.781 | #463148 | #3C2F47 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | canvas-mid | solid/tint-accent | 1.045 | 1.052 | #2C1B34 | #2E1B34 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | compliant | solid/tint-accent | 4.193 | 4.219 | #2E1B34 | #2C1B34 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | critical | solid/tint-accent | 1.947 | 1.959 | #2E1B34 | #2C1B34 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | danger-text | solid/tint-accent | 5.695 | 5.731 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | high | solid/tint-accent | 3.700 | 3.723 | #2E1B34 | #2C1B34 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | insufficient | solid/tint-accent | 6.257 | 6.296 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | low | solid/tint-accent | 4.705 | 4.735 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | medium | solid/tint-accent | 7.387 | 7.433 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | muted | solid/tint-accent | 6.079 | 6.118 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | noncompliant | solid/tint-accent | 2.918 | 2.936 | #2E1B34 | #2C1B34 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | plum | partial | solid/tint-accent | 7.387 | 7.433 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text | solid/tint-accent | 13.296 | 13.380 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | text-2 | solid/tint-accent | 8.410 | 8.463 | #2E1B34 | #2C1B34 | Pass | conservative candidate pairing; pill uses text |
| dark | plum | accent-text | solid/accent-soft | 2.089 | 2.102 | #271A2F | #261A2F | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text | solid/accent-soft | 13.820 | 13.904 | #271A2F | #261A2F | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | text-2 | solid/accent-soft | 8.741 | 8.795 | #271A2F | #261A2F | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | muted | solid/accent-soft | 6.319 | 6.357 | #271A2F | #261A2F | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | plum | on-accent | primary-button | 4.804 | 6.426 | #A6559A | #97398A | Pass | declared component pairing |
| dark | plum | on-accent | primary-kbd | 3.597 | 4.605 | #B470AA | #A8599D | Fail candidate | declared component pairing |
| dark | slate | accent-text | canvas | 1.924 | 2.038 | #28202C | #1C1D2A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass | 1.636 | 1.746 | #352C39 | #282938 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong | 1.511 | 1.614 | #3A313F | #2E2F3D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid | 2.192 | 2.204 | #151621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/hover | 1.664 | 1.774 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/press | 1.464 | 1.563 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/track | 1.464 | 1.563 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/field | 1.664 | 1.774 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/field-hover | 4.285 | 4.352 | #BBBBBF | #BEBCC0 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/field-focus | 1.512 | 1.615 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/chip | 1.664 | 1.774 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/nav-selected | 1.464 | 1.563 | #3B343F | #30313D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/secondary-button | 1.562 | 1.667 | #37303B | #2C2D39 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/secondary-hover | 1.369 | 1.463 | #403943 | #353641 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/secondary-active | 1.664 | 1.774 | #332B37 | #272835 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/file-button | 1.416 | 1.512 | #3E3641 | #33343F | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/segment-selected | 1.236 | 1.320 | #463F4A | #3C3D48 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/kbd | 1.512 | 1.615 | #39323D | #2E2F3B | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-critical | 1.762 | 1.871 | #411F28 | #381D27 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-high | 1.528 | 1.633 | #4F2929 | #462627 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-medium | 1.242 | 1.327 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-low | 1.420 | 1.493 | #2C3C3A | #233938 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-compliant | 1.465 | 1.538 | #2A3A39 | #203737 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-partial | 1.242 | 1.327 | #543C2D | #4B3A2B | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-noncompliant | 1.609 | 1.716 | #49262C | #40232A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/tint-insufficient | 1.290 | 1.367 | #413D4A | #383A49 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | canvas/mark | 1.000 | 1.051 | #644A2D | #6C4C2D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/hover | 1.404 | 1.500 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/press | 1.235 | 1.319 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/track | 1.235 | 1.319 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/field | 1.404 | 1.500 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/field-hover | 4.459 | 4.525 | #BFBFC3 | #C2C0C4 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/field-focus | 1.276 | 1.362 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/chip | 1.404 | 1.500 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/nav-selected | 1.235 | 1.319 | #473F4B | #3B3D4A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/secondary-button | 1.317 | 1.407 | #433B47 | #373846 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/secondary-hover | 1.157 | 1.234 | #4B434F | #40414E | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/secondary-active | 1.404 | 1.500 | #3F3643 | #333442 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/file-button | 1.196 | 1.276 | #49414D | #3E3F4C | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/segment-selected | 1.049 | 1.117 | #514955 | #464754 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/kbd | 1.276 | 1.362 | #453D49 | #393A48 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-critical | 1.548 | 1.649 | #4B2833 | #412632 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-high | 1.330 | 1.422 | #593233 | #4F3032 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-medium | 1.072 | 1.143 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-low | 1.229 | 1.290 | #364544 | #2D4343 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-compliant | 1.269 | 1.331 | #344343 | #2A4142 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-partial | 1.072 | 1.143 | #5E4537 | #544336 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-noncompliant | 1.404 | 1.499 | #532F36 | #4A2D35 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/tint-insufficient | 1.112 | 1.176 | #4B4655 | #414454 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass/mark | 1.126 | 1.189 | #6C5235 | #745336 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/hover | 1.296 | 1.384 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/press | 1.142 | 1.218 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/track | 1.142 | 1.218 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/field | 1.296 | 1.384 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/field-hover | 4.540 | 4.605 | #C0C1C5 | #C4C1C5 | Pass | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/field-focus | 1.179 | 1.258 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/chip | 1.296 | 1.384 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/nav-selected | 1.142 | 1.218 | #4C4450 | #41424F | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/secondary-button | 1.217 | 1.299 | #48404C | #3C3E4B | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/secondary-hover | 1.071 | 1.141 | #504854 | #454653 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/secondary-active | 1.296 | 1.384 | #443C48 | #383947 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/file-button | 1.106 | 1.179 | #4E4652 | #434451 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/segment-selected | 1.000 | 1.035 | #514D59 | #4B4C58 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/kbd | 1.179 | 1.258 | #4A424E | #3F404D | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-critical | 1.455 | 1.550 | #4F2D37 | #462B36 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-high | 1.247 | 1.332 | #5D3637 | #533436 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-medium | 1.003 | 1.067 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-low | 1.149 | 1.205 | #3B4948 | #314747 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-compliant | 1.187 | 1.244 | #384747 | #2E4546 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-partial | 1.003 | 1.067 | #624A3B | #59483A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-noncompliant | 1.317 | 1.405 | #58333A | #4E3139 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/tint-insufficient | 1.040 | 1.098 | #4F4A59 | #464858 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | glass-strong/mark | 1.192 | 1.256 | #705539 | #78573A | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/hover | 1.933 | 1.946 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/press | 1.713 | 1.725 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/track | 1.713 | 1.725 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/field | 1.933 | 1.946 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/field-hover | 4.179 | 4.187 | #B8B9BC | #B9B9BC | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/field-focus | 1.768 | 1.780 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/chip | 1.933 | 1.946 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/nav-selected | 1.713 | 1.725 | #2A2B35 | #282B35 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/secondary-button | 1.823 | 1.835 | #252730 | #242630 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/secondary-hover | 1.604 | 1.616 | #2F3039 | #2D3039 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/secondary-active | 1.933 | 1.946 | #20222C | #1F222C | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/file-button | 1.658 | 1.670 | #2C2E37 | #2B2D37 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/segment-selected | 1.448 | 1.458 | #363740 | #343740 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/kbd | 1.768 | 1.780 | #282933 | #262932 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-critical | 1.997 | 2.010 | #321820 | #311720 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-high | 1.759 | 1.772 | #402120 | #3F2120 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-medium | 1.441 | 1.452 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-low | 1.616 | 1.624 | #1D3431 | #1C3431 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-compliant | 1.662 | 1.671 | #1B3230 | #193230 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-partial | 1.441 | 1.452 | #453524 | #443424 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-noncompliant | 1.843 | 1.857 | #3A1E23 | #391E23 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/tint-insufficient | 1.485 | 1.495 | #323541 | #313541 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | solid/mark | 1.082 | 1.089 | #5F4526 | #5E4526 | Fail candidate | conservative candidate pairing |
| dark | slate | accent-text | modal-over-scrim | 2.200 | 2.208 | #141621 | #131621 | Fail candidate | conservative candidate pairing |
| dark | slate | canvas-mid | canvas/tint-accent | 1.142 | 1.200 | #232839 | #2C2B3B | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | compliant | canvas/tint-accent | 3.674 | 3.861 | #2C2B3B | #232839 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | critical | canvas/tint-accent | 1.706 | 1.793 | #2C2B3B | #232839 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | danger-text | canvas/tint-accent | 4.991 | 5.245 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | high | canvas/tint-accent | 3.242 | 3.407 | #2C2B3B | #232839 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | insufficient | canvas/tint-accent | 5.483 | 5.762 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | low | canvas/tint-accent | 4.123 | 4.333 | #2C2B3B | #232839 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | medium | canvas/tint-accent | 6.473 | 6.803 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | muted | canvas/tint-accent | 5.327 | 5.599 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | noncompliant | canvas/tint-accent | 2.557 | 2.687 | #2C2B3B | #232839 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | partial | canvas/tint-accent | 6.473 | 6.803 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text | canvas/tint-accent | 11.652 | 12.245 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text-2 | canvas/tint-accent | 7.370 | 7.745 | #2C2B3B | #232839 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | accent-text | canvas/accent-soft | 1.760 | 1.855 | #2B2837 | #212535 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text | canvas/accent-soft | 12.076 | 12.725 | #2B2837 | #212535 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text-2 | canvas/accent-soft | 7.639 | 8.049 | #2B2837 | #212535 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | muted | canvas/accent-soft | 5.522 | 5.818 | #2B2837 | #212535 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | canvas-mid | glass/tint-accent | 1.308 | 1.376 | #2D3244 | #363445 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | compliant | glass/tint-accent | 3.204 | 3.372 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | critical | glass/tint-accent | 1.488 | 1.566 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | danger-text | glass/tint-accent | 4.352 | 4.580 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | high | glass/tint-accent | 2.827 | 2.975 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | insufficient | glass/tint-accent | 4.781 | 5.032 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | low | glass/tint-accent | 3.596 | 3.784 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | medium | glass/tint-accent | 5.645 | 5.941 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | muted | glass/tint-accent | 4.646 | 4.889 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | noncompliant | glass/tint-accent | 2.230 | 2.346 | #363445 | #2D3244 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | partial | glass/tint-accent | 5.645 | 5.941 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text | glass/tint-accent | 10.161 | 10.693 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text-2 | glass/tint-accent | 6.427 | 6.764 | #363445 | #2D3244 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | accent-text | glass/accent-soft | 1.523 | 1.609 | #363242 | #2B2F41 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text | glass/accent-soft | 10.449 | 11.038 | #363242 | #2B2F41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text-2 | glass/accent-soft | 6.609 | 6.982 | #363242 | #2B2F41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | muted | glass/accent-soft | 4.778 | 5.047 | #363242 | #2B2F41 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | canvas-mid | glass-strong/tint-accent | 1.395 | 1.468 | #313648 | #3B3849 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | compliant | glass-strong/tint-accent | 3.003 | 3.160 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | critical | glass-strong/tint-accent | 1.395 | 1.468 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | danger-text | glass-strong/tint-accent | 4.080 | 4.293 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | high | glass-strong/tint-accent | 2.650 | 2.789 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | insufficient | glass-strong/tint-accent | 4.482 | 4.716 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | low | glass-strong/tint-accent | 3.371 | 3.547 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | medium | glass-strong/tint-accent | 5.291 | 5.568 | #3B3849 | #313648 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | muted | glass-strong/tint-accent | 4.355 | 4.583 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | noncompliant | glass-strong/tint-accent | 2.090 | 2.199 | #3B3849 | #313648 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | partial | glass-strong/tint-accent | 5.291 | 5.568 | #3B3849 | #313648 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text | glass-strong/tint-accent | 9.524 | 10.022 | #3B3849 | #313648 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text-2 | glass-strong/tint-accent | 6.024 | 6.339 | #3B3849 | #313648 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | accent-text | glass-strong/accent-soft | 1.421 | 1.502 | #3A3646 | #303445 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text | glass-strong/accent-soft | 9.752 | 10.304 | #3A3646 | #303445 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text-2 | glass-strong/accent-soft | 6.168 | 6.517 | #3A3646 | #303445 | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | muted | glass-strong/accent-soft | 4.459 | 4.711 | #3A3646 | #303445 | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | canvas-mid | solid/tint-accent | 1.059 | 1.064 | #1C2332 | #1D2332 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | compliant | solid/tint-accent | 4.144 | 4.165 | #1D2332 | #1C2332 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | critical | solid/tint-accent | 1.924 | 1.934 | #1D2332 | #1C2332 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | danger-text | solid/tint-accent | 5.629 | 5.658 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | high | solid/tint-accent | 3.656 | 3.675 | #1D2332 | #1C2332 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | insufficient | solid/tint-accent | 6.184 | 6.215 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | low | solid/tint-accent | 4.650 | 4.674 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | medium | solid/tint-accent | 7.301 | 7.338 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | muted | solid/tint-accent | 6.009 | 6.039 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | noncompliant | solid/tint-accent | 2.884 | 2.898 | #1D2332 | #1C2332 | Fail candidate | conservative candidate pairing; pill uses text |
| dark | slate | partial | solid/tint-accent | 7.301 | 7.338 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text | solid/tint-accent | 13.141 | 13.208 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | text-2 | solid/tint-accent | 8.312 | 8.354 | #1D2332 | #1C2332 | Pass | conservative candidate pairing; pill uses text |
| dark | slate | accent-text | solid/accent-soft | 1.994 | 2.005 | #1B1F2D | #1A1F2D | Fail candidate | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text | solid/accent-soft | 13.683 | 13.754 | #1B1F2D | #1A1F2D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | text-2 | solid/accent-soft | 8.655 | 8.700 | #1B1F2D | #1A1F2D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | muted | solid/accent-soft | 6.256 | 6.288 | #1B1F2D | #1A1F2D | Pass | declared component pairing for text and accent-text; candidate for text-2 and muted |
| dark | slate | on-accent | primary-button | 4.697 | 6.554 | #637592 | #4A5E80 | Pass | declared component pairing |
| dark | slate | on-accent | primary-kbd | 3.462 | 4.486 | #7C8BA3 | #677894 | Fail candidate | declared component pairing |
| dark | all | canvas-mid | tooltip | 13.982 | 13.982 | #E8EBF2 | #E8EBF2 | Pass | declared component pairing |
| dark | all | literal-white | destructive-button | 5.438 | 5.438 | #C0392B | #C0392B | Pass | declared component pairing |
