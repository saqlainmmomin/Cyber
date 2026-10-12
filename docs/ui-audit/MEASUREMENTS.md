# Measurements and verification limits

Host capture data contains 411 rows. The table below transcribes the measured DOM values without inferring geometry from CSS. Raw selector/text samples and foreground/ancestor layers are retained in `rendered-measurements.json`; the portable subset is `rendered-measurements-summary.json`. Captures are under `screenshots/`. The question pane measured 576px inside the 1040px questionnaire main region at 1440.

## Per-screen rendered measurements

Each row identifies viewport and theme. Unused width is viewport minus sidebar minus main border box, including outer gutters. Body block is total characters / maximum rendered characters on one line / block width / font size. A dash means the tool found no eligible prose block, not that it was deferred. Below-14 counts include metadata and controls, so they are a screening measure, not a count of failures. Text samples confirm 12px question guidance and 13px evidence/RFI/report content. The measurement tool records visible main-content text, not all source markup.

| Screen/state | Viewport/theme | Content px | Unused px | Page height px | Overflow | Longest body block chars / line chars / width px / size | Font size:text-node count | Nodes below 14px | Capture |
|---|---|---:|---:|---:|---|---|---|---:|---|
| home | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 14px:4, 13px:9, 16px:2, 12px:5 | 14 | `screenshots/home-1440.png` |
| home | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 14px:4, 13px:9, 16px:2, 12px:5 | 14 | `screenshots/home-1280.png` |
| clients | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 13px:1, 12px:5, 14px:5 | 6 | `screenshots/clients-1440.png` |
| clients | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 13px:1, 12px:5, 14px:5 | 6 | `screenshots/clients-1280.png` |
| client | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 362.328125 / 14px | 28px:1, 14px:9, 13px:3, 16px:3, 12px:4 | 7 | `screenshots/client-1440.png` |
| client | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 362.328125 / 14px | 28px:1, 14px:9, 13px:3, 16px:3, 12px:4 | 7 | `screenshots/client-1280.png` |
| engagements | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 13px:9, 12px:10, 14px:2 | 19 | `screenshots/engagements-1440.png` |
| engagements | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 13px:9, 12px:10, 14px:2 | 19 | `screenshots/engagements-1280.png` |
| portfolio-review | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 14px:3, 12px:5, 13px:2 | 7 | `screenshots/portfolio-review-1440.png` |
| portfolio-review | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 14px:3, 12px:5, 13px:2 | 7 | `screenshots/portfolio-review-1280.png` |
| reports | 1440 / light | 1040 | 144 | 1000 | False | 46 / 46 / 324.53125 / 14px | 28px:1, 14px:25, 12px:6, 13px:8 | 14 | `screenshots/reports-1440.png` |
| reports | 1280 / light | 1024 | 0 | 1000 | False | 46 / 46 / 324.53125 / 14px | 28px:1, 14px:25, 12px:6, 13px:8 | 14 | `screenshots/reports-1280.png` |
| new-engagement | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 13px:12, 12px:1 | 13 | `screenshots/new-engagement-1440.png` |
| new-engagement | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 13px:12, 12px:1 | 13 | `screenshots/new-engagement-1280.png` |
| engagement | 1440 / light | 1040 | 144 | 1000 | False | 44 / 44 / 578.265625 / 14px | 28px:4, 14px:8, 12px:10, 13px:14, 16px:1 | 24 | `screenshots/engagement-1440.png` |
| engagement | 1280 / light | 1024 | 0 | 1000 | False | 44 / 44 / 578.265625 / 14px | 28px:4, 14px:8, 12px:10, 13px:14, 16px:1 | 24 | `screenshots/engagement-1280.png` |
| new-assessment | 1440 / light | 1040 | 144 | 1000 | False | 67 / 67 / 484.5 / 14px | 28px:1, 14px:1, 16px:2, 13px:10, 12px:2 | 12 | `screenshots/new-assessment-1440.png` |
| new-assessment | 1280 / light | 1024 | 0 | 1000 | False | 67 / 67 / 484.5 / 14px | 28px:1, 14px:1, 16px:2, 13px:10, 12px:2 | 12 | `screenshots/new-assessment-1280.png` |
| remediation | 1440 / light | 1040 | 144 | 1980 | False | 71 / 71 / 486.546875 / 14px | 28px:8, 14px:52, 13px:27, 16px:5, 12px:32 | 59 | `screenshots/remediation-1440.png` |
| remediation | 1280 / light | 1024 | 0 | 1980 | False | 71 / 71 / 486.546875 / 14px | 28px:8, 14px:52, 13px:27, 16px:5, 12px:32 | 59 | `screenshots/remediation-1280.png` |
| integrated-reports | 1440 / light | 1040 | 144 | 1167 | False | 118 / 79 / 524.875 / 13px | 28px:1, 14px:5, 13px:11, 16px:5, 12px:4 | 15 | `screenshots/integrated-reports-1440.png` |
| integrated-reports | 1280 / light | 1024 | 0 | 1167 | False | 118 / 79 / 524.875 / 13px | 28px:1, 14px:5, 13px:11, 16px:5, 12px:4 | 15 | `screenshots/integrated-reports-1280.png` |
| requests | 1440 / light | 1040 | 144 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/requests-1440.png` |
| requests | 1280 / light | 1024 | 0 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/requests-1280.png` |
| aws-evidence | 1440 / light | 1040 | 144 | 1000 | False | 169 / 47 / 295.234375 / 13px | 28px:1, 14px:1, 13px:6, 16px:1 | 6 | `screenshots/aws-evidence-1440.png` |
| aws-evidence | 1280 / light | 1024 | 0 | 1000 | False | 169 / 47 / 295.234375 / 13px | 28px:1, 14px:1, 13px:6, 16px:1 | 6 | `screenshots/aws-evidence-1280.png` |
| purge | 1440 / light | 1040 | 144 | 2431 | False | 110 / 110 / 928 / 13px | 28px:1, 14px:42, 13px:27, 16px:5 | 27 | `screenshots/purge-1440.png` |
| purge | 1280 / light | 1024 | 0 | 2431 | False | 110 / 110 / 912 / 13px | 28px:1, 14px:42, 13px:27, 16px:5 | 27 | `screenshots/purge-1280.png` |
| settings | 1440 / light | 1040 | 144 | 1838 | False | 153 / 93 / 592 / 13px | 28px:1, 13px:18, 16px:4, 12px:12, 14px:9 | 30 | `screenshots/settings-1440.png` |
| settings | 1280 / light | 1024 | 0 | 1838 | False | 153 / 93 / 592 / 13px | 28px:1, 13px:18, 16px:4, 12px:12, 14px:9 | 30 | `screenshots/settings-1280.png` |
| evidence-global | 1440 / light | 1040 | 144 | 5219 | False | - | 28px:1, 14px:138, 13px:413, 12px:74 | 487 | `screenshots/evidence-global-1440.png` |
| evidence-global | 1280 / light | 1024 | 0 | 5219 | False | - | 28px:1, 14px:138, 13px:413, 12px:74 | 487 | `screenshots/evidence-global-1280.png` |
| evidence-engagement | 1440 / light | 1040 | 144 | 5151 | False | 48 / 48 / 578.265625 / 14px | 28px:1, 14px:68, 13px:344, 12px:73 | 417 | `screenshots/evidence-engagement-1440.png` |
| evidence-engagement | 1280 / light | 1024 | 0 | 5151 | False | 48 / 48 / 578.265625 / 14px | 28px:1, 14px:68, 13px:344, 12px:73 | 417 | `screenshots/evidence-engagement-1280.png` |
| evidence-assessment | 1440 / light | 1040 | 144 | 4498 | False | 92 / 92 / 624.90625 / 14px | 28px:1, 14px:59, 13px:301, 12px:64 | 365 | `screenshots/evidence-assessment-1440.png` |
| evidence-assessment | 1280 / light | 1024 | 0 | 4498 | False | 92 / 92 / 624.90625 / 14px | 28px:1, 14px:59, 13px:301, 12px:64 | 365 | `screenshots/evidence-assessment-1280.png` |
| evidence-record | 1440 / light | 1040 | 144 | 1978 | False | 88 / 88 / 976 / 13px | 28px:1, 14px:81, 13px:29, 12px:22, 16px:4 | 51 | `screenshots/evidence-record-1440.png` |
| evidence-record | 1280 / light | 1024 | 0 | 1978 | False | 88 / 88 / 960 / 13px | 28px:1, 14px:81, 13px:29, 12px:22, 16px:4 | 51 | `screenshots/evidence-record-1280.png` |
| evidence-reuse | 1440 / light | 1040 | 144 | 5637 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:119, 12px:20 | 139 | `screenshots/evidence-reuse-1440.png` |
| evidence-reuse | 1280 / light | 1024 | 0 | 5637 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:119, 12px:20 | 139 | `screenshots/evidence-reuse-1280.png` |
| desk-review | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/desk-review-1440.png` |
| desk-review | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/desk-review-1280.png` |
| overview | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:13, 13px:20, 12px:1, 16px:2 | 21 | `screenshots/overview-1440.png` |
| overview | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:13, 13px:20, 12px:1, 16px:2 | 21 | `screenshots/overview-1280.png` |
| scope | 1440 / light | 1040 | 144 | 4198 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:51, 13px:67, 16px:2, 12px:43 | 110 | `screenshots/scope-1440.png` |
| scope | 1280 / light | 1024 | 0 | 4217 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:51, 13px:67, 16px:2, 12px:43 | 110 | `screenshots/scope-1280.png` |
| questionnaire | 1440 / light | 1040 | 144 | 4906 | False | 202 / 101 / 576 / 12px | 28px:1, 14px:17, 13px:115, 16px:3, 12px:44, 20px:1 | 159 | `screenshots/questionnaire-1440.png` |
| questionnaire | 1280 / light | 1024 | 0 | 4945 | False | 202 / 100 / 560 / 12px | 28px:1, 14px:17, 13px:115, 16px:3, 12px:44, 20px:1 | 159 | `screenshots/questionnaire-1280.png` |
| report | 1440 / light | 1040 | 144 | 2944 | False | 416 / 138 / 928 / 14px | 28px:2, 14px:38, 13px:44, 12px:29, 16px:11 | 73 | `screenshots/report-1440.png` |
| report | 1280 / light | 1024 | 0 | 2965 | False | 416 / 138 / 912 / 14px | 28px:2, 14px:38, 13px:44, 12px:29, 16px:11 | 73 | `screenshots/report-1280.png` |
| report-summary | 1440 / None | 1424 | 16 | 4469 | False | 416 / 210 / 1424 / 16px | 16px:94, 24px:8, 13.3333px:1, 18.72px:6 | 1 | `screenshots/report-summary-1440.png` |
| report-summary | 1280 / None | 1264 | 16 | 4345 | False | 416 / 195 / 1264 / 16px | 16px:94, 24px:8, 13.3333px:1, 18.72px:6 | 1 | `screenshots/report-summary-1280.png` |
| review-queue | 1440 / light | 1120 | 64 | 1177 | False | 280 / 85 / 674 / 16px | 28px:1, 14px:18, 13px:35, 12px:31, 20px:1, 16px:1 | 66 | `screenshots/review-queue-1440.png` |
| review-queue | 1280 / light | 1024 | 0 | 1177 | False | 280 / 72 / 578 / 16px | 28px:1, 14px:18, 13px:35, 12px:31, 20px:1, 16px:1 | 66 | `screenshots/review-queue-1280.png` |
| conclusions | 1440 / light | 1040 | 144 | 8550 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/conclusions-1440.jpg` |
| conclusions | 1280 / light | 1024 | 0 | 8655 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/conclusions-1280.jpg` |
| findings | 1440 / light | 1040 | 144 | 3047 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:47, 13px:70, 12px:71, 16px:2 | 141 | `screenshots/findings-1440.png` |
| findings | 1280 / light | 1024 | 0 | 3047 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:47, 13px:70, 12px:71, 16px:2 | 141 | `screenshots/findings-1280.png` |
| workpaper | 1440 / light | 1040 | 144 | 1418 | False | 96 / 96 / 658.46875 / 14px | 28px:1, 14px:28, 13px:32, 12px:24, 16px:3, 20px:8 | 56 | `screenshots/workpaper-1440.png` |
| workpaper | 1280 / light | 1024 | 0 | 1418 | False | 96 / 96 / 658.46875 / 14px | 28px:1, 14px:28, 13px:32, 12px:24, 16px:3, 20px:8 | 56 | `screenshots/workpaper-1280.png` |
| snapshots | 1440 / light | 1040 | 144 | 1000 | False | 57 / 57 / 391.78125 / 14px | 28px:1, 14px:1, 13px:17, 12px:7, 16px:2 | 24 | `screenshots/snapshots-1440.png` |
| snapshots | 1280 / light | 1024 | 0 | 1000 | False | 57 / 57 / 391.78125 / 14px | 28px:1, 14px:1, 13px:17, 12px:7, 16px:2 | 24 | `screenshots/snapshots-1280.png` |
| comparison | 1440 / light | 1040 | 144 | 7107 | False | 87 / 87 / 613.203125 / 14px | 28px:3, 14px:3, 13px:284, 12px:115, 20px:3, 16px:3 | 399 | `screenshots/comparison-1440.jpg` |
| comparison | 1280 / light | 1024 | 0 | 7144 | False | 87 / 87 / 613.203125 / 14px | 28px:3, 14px:3, 13px:284, 12px:115, 20px:3, 16px:3 | 399 | `screenshots/comparison-1280.jpg` |
| narrative | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/narrative-1440.png` |
| narrative | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/narrative-1280.png` |
| board-inputs | 1440 / light | 1040 | 144 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/board-inputs-1440.png` |
| board-inputs | 1280 / light | 1024 | 0 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/board-inputs-1280.png` |
| soa | 1440 / light | 1040 | 144 | 17481 | False | 140 / 91 / 574.078125 / 13px | 28px:1, 14px:1, 13px:195, 12px:566 | 761 | `screenshots/soa-1440.jpg` |
| soa | 1280 / light | 1024 | 0 | 17481 | False | 140 / 91 / 574.078125 / 13px | 28px:1, 14px:1, 13px:195, 12px:566 | 761 | `screenshots/soa-1280.jpg` |
| rfi-items | 1440 / light | 1040 | 144 | 20005 | False | 426 / 37 / 771.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/rfi-items-1440.jpg` |
| rfi-items | 1280 / light | 1024 | 0 | 20005 | False | 426 / 37 / 755.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/rfi-items-1280.jpg` |
| rfi-versions | 1440 / light | 1040 | 144 | 1000 | False | 55 / 39 / 295.234375 / 13px | 28px:1, 14px:1, 13px:10, 12px:5, 16px:2 | 15 | `screenshots/rfi-versions-1440.png` |
| rfi-versions | 1280 / light | 1024 | 0 | 1000 | False | 55 / 39 / 295.234375 / 13px | 28px:1, 14px:1, 13px:10, 12px:5, 16px:2 | 15 | `screenshots/rfi-versions-1280.png` |
| rfi-links | 1440 / light | 1040 | 144 | 1000 | False | 51 / 46 / 295.234375 / 13px | 28px:1, 14px:1, 13px:11, 12px:5, 16px:1 | 16 | `screenshots/rfi-links-1440.png` |
| rfi-links | 1280 / light | 1024 | 0 | 1000 | False | 51 / 46 / 295.234375 / 13px | 28px:1, 14px:1, 13px:11, 12px:5, 16px:1 | 16 | `screenshots/rfi-links-1280.png` |
| report-iso | 1440 / light | 1040 | 144 | 15854 | False | 416 / 138 / 928 / 14px | 28px:2, 14px:211, 13px:134, 12px:209, 16px:10 | 343 | `screenshots/report-iso-1440.jpg` |
| report-iso | 1280 / light | 1024 | 0 | 15854 | False | 416 / 138 / 912 / 14px | 28px:2, 14px:211, 13px:134, 12px:209, 16px:10 | 343 | `screenshots/report-iso-1280.jpg` |
| report-summary-iso | 1440 / None | 1424 | 16 | 21681 | False | 416 / 210 / 1424 / 16px | 16px:449, 24px:8, 13.3333px:1, 18.72px:93 | 1 | `screenshots/report-summary-iso-1440.jpg` |
| report-summary-iso | 1280 / None | 1264 | 16 | 21539 | False | 416 / 195 / 1264 / 16px | 16px:449, 24px:8, 13.3333px:1, 18.72px:93 | 1 | `screenshots/report-summary-iso-1280.jpg` |
| nist-overview | 1440 / light | 1040 | 144 | 1000 | False | 73 / 44 / 295.234375 / 13px | 28px:1, 14px:1, 13px:13, 12px:1, 16px:1 | 14 | `screenshots/nist-overview-1440.png` |
| nist-overview | 1280 / light | 1024 | 0 | 1000 | False | 73 / 44 / 295.234375 / 13px | 28px:1, 14px:1, 13px:13, 12px:1, 16px:1 | 14 | `screenshots/nist-overview-1280.png` |
| nist-questionnaire | 1440 / light | 1040 | 144 | 2819 | False | 186 / 97 / 576 / 12px | 28px:1, 14px:9, 13px:68, 16px:3, 12px:30, 20px:1 | 98 | `screenshots/nist-questionnaire-1440.png` |
| nist-questionnaire | 1280 / light | 1024 | 0 | 2839 | False | 186 / 97 / 560 / 12px | 28px:1, 14px:9, 13px:68, 16px:3, 12px:30, 20px:1 | 98 | `screenshots/nist-questionnaire-1280.png` |
| interim-conclusions | 1440 / light | 1040 | 144 | 1754 | False | 84 / 84 / 908 / 14px | 28px:1, 14px:10, 13px:33, 12px:21, 20px:4, 16px:3 | 54 | `screenshots/interim-conclusions-1440.png` |
| interim-conclusions | 1280 / light | 1024 | 0 | 1775 | False | 84 / 84 / 892 / 14px | 28px:1, 14px:10, 13px:33, 12px:21, 20px:4, 16px:3 | 54 | `screenshots/interim-conclusions-1280.png` |
| aws_evidence-ready | 1440 / light | 1040 | 144 | 1063 | False | 104 / 104 / 928 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-ready-1440.png` |
| aws_evidence-ready | 1280 / light | 1024 | 0 | 1063 | False | 104 / 104 / 912 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-ready-1280.png` |
| aws_evidence-pulling | 1440 / light | 1040 | 144 | 1123 | False | 104 / 104 / 928 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-pulling-1440.png` |
| aws_evidence-pulling | 1280 / light | 1024 | 0 | 1123 | False | 104 / 104 / 912 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-pulling-1280.png` |
| aws_evidence-result | 1440 / light | 1040 | 144 | 1394 | False | 104 / 104 / 928 / 14px | 28px:1, 14px:27, 13px:16, 16px:4, 12px:18 | 34 | `screenshots/aws_evidence-result-1440.png` |
| aws_evidence-result | 1280 / light | 1024 | 0 | 1394 | False | 104 / 104 / 912 / 14px | 28px:1, 14px:27, 13px:16, 16px:4, 12px:18 | 34 | `screenshots/aws_evidence-result-1280.png` |
| aws_evidence-error | 1440 / light | 1040 | 144 | 1142 | False | 104 / 104 / 928 / 14px | 28px:1, 14px:8, 13px:15, 16px:3, 12px:10 | 25 | `screenshots/aws_evidence-error-1440.png` |
| aws_evidence-error | 1280 / light | 1024 | 0 | 1142 | False | 104 / 104 / 912 / 14px | 28px:1, 14px:8, 13px:15, 16px:3, 12px:10 | 25 | `screenshots/aws_evidence-error-1280.png` |
| aws_evidence-notconfigured | 1440 / light | 1040 | 144 | 1063 | False | 104 / 104 / 928 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-notconfigured-1440.png` |
| aws_evidence-notconfigured | 1280 / light | 1024 | 0 | 1063 | False | 104 / 104 / 912 / 14px | 28px:1, 14px:8, 13px:13, 16px:3, 12px:10 | 23 | `screenshots/aws_evidence-notconfigured-1280.png` |
| b3-context-complete-default | 1440 / light | 1040 | 144 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:2, 13px:13, 16px:1 | 13 | `screenshots/b3-context-complete-default-1440.png` |
| b3-context-complete-default | 1280 / light | 1024 | 0 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:2, 13px:13, 16px:1 | 13 | `screenshots/b3-context-complete-default-1280.png` |
| b3-followups-loaded | 1440 / light | 1040 | 144 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:2, 13px:8, 12px:2 | 10 | `screenshots/b3-followups-loaded-1440.png` |
| b3-followups-loaded | 1280 / light | 1024 | 0 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:2, 13px:8, 12px:2 | 10 | `screenshots/b3-followups-loaded-1280.png` |
| b3-hub-loading | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:15, 12px:1, 16px:1 | 16 | `screenshots/b3-hub-loading-1440.png` |
| b3-hub-loading | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:15, 12px:1, 16px:1 | 16 | `screenshots/b3-hub-loading-1280.png` |
| b3-hub-error | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:19, 12px:1, 16px:1 | 20 | `screenshots/b3-hub-error-1440.png` |
| b3-hub-error | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:19, 12px:1, 16px:1 | 20 | `screenshots/b3-hub-error-1280.png` |
| b3-question-step-org | 1440 / light | 1040 | 144 | 1328 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:32, 20px:1 | 32 | `screenshots/b3-question-step-org-1440.png` |
| b3-question-step-org | 1280 / light | 1024 | 0 | 1328 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:32, 20px:1 | 32 | `screenshots/b3-question-step-org-1280.png` |
| b3-question-step-data | 1440 / light | 1040 | 144 | 1151 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:27, 20px:1 | 27 | `screenshots/b3-question-step-data-1440.png` |
| b3-question-step-data | 1280 / light | 1024 | 0 | 1151 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:27, 20px:1 | 27 | `screenshots/b3-question-step-data-1280.png` |
| b3-question-step-data-yes | 1440 / light | 1040 | 144 | 1328 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:32, 20px:1 | 32 | `screenshots/b3-question-step-data-yes-1440.png` |
| b3-question-step-data-yes | 1280 / light | 1024 | 0 | 1328 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:32, 20px:1 | 32 | `screenshots/b3-question-step-data-yes-1280.png` |
| b3-question-step-last | 1440 / light | 1040 | 144 | 1113 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:27, 20px:1 | 27 | `screenshots/b3-question-step-last-1440.png` |
| b3-question-step-last | 1280 / light | 1024 | 0 | 1113 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:27, 20px:1 | 27 | `screenshots/b3-question-step-last-1280.png` |
| b3-scope-error | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:25, 16px:2 | 25 | `screenshots/b3-scope-error-1440.png` |
| b3-scope-error | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:25, 16px:2 | 25 | `screenshots/b3-scope-error-1280.png` |
| b3-scope-saving | 1440 / light | 1040 | 144 | 4198 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:51, 13px:67, 16px:2, 12px:43 | 110 | `screenshots/b3-scope-saving-1440.png` |
| b3-scope-saving | 1280 / light | 1024 | 0 | 4217 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:51, 13px:67, 16px:2, 12px:43 | 110 | `screenshots/b3-scope-saving-1280.png` |
| b3-scope-complete-loading | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:21, 16px:2 | 21 | `screenshots/b3-scope-complete-loading-1440.png` |
| b3-scope-complete-loading | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:21, 16px:2 | 21 | `screenshots/b3-scope-complete-loading-1280.png` |
| b3-scope-complete-error | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:25, 16px:2 | 25 | `screenshots/b3-scope-complete-error-1440.png` |
| b3-scope-complete-error | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:9, 13px:25, 16px:2 | 25 | `screenshots/b3-scope-complete-error-1280.png` |
| b3-screening-form-default | 1440 / light | 1040 | 144 | 2983 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-default-1440.png` |
| b3-screening-form-default | 1280 / light | 1024 | 0 | 2983 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-default-1280.png` |
| b3-screening-form-loading | 1440 / light | 1040 | 144 | 3062 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-loading-1440.png` |
| b3-screening-form-loading | 1280 / light | 1024 | 0 | 3062 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-loading-1280.png` |
| b3-screening-form-error | 1440 / light | 1040 | 144 | 3062 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:11, 16px:1, 12px:9 | 20 | `screenshots/b3-screening-form-error-1440.png` |
| b3-screening-form-error | 1280 / light | 1024 | 0 | 3062 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:11, 16px:1, 12px:9 | 20 | `screenshots/b3-screening-form-error-1280.png` |
| b3-screening-form-complete | 1440 / light | 1040 | 144 | 1000 | False | 121 / 107 / 720 / 13px | 28px:1, 14px:2, 13px:11, 16px:1 | 11 | `screenshots/b3-screening-form-complete-1440.png` |
| b3-screening-form-complete | 1280 / light | 1024 | 0 | 1000 | False | 121 / 107 / 720 / 13px | 28px:1, 14px:2, 13px:11, 16px:1 | 11 | `screenshots/b3-screening-form-complete-1280.png` |
| b3-screening-form-screened | 1440 / light | 1040 | 144 | 2983 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-screened-1440.png` |
| b3-screening-form-screened | 1280 / light | 1024 | 0 | 2983 | False | 314 / 103 / 672 / 14px | 28px:1, 14px:19, 13px:9, 16px:1, 12px:9 | 18 | `screenshots/b3-screening-form-screened-1280.png` |
| b3-section-questions-default | 1440 / light | 1040 | 144 | 1596 | False | 144 / 107 / 772 / 14px | 28px:1, 14px:10, 13px:46, 20px:1, 12px:11 | 57 | `screenshots/b3-section-questions-default-1440.png` |
| b3-section-questions-default | 1280 / light | 1024 | 0 | 1596 | False | 144 / 107 / 772 / 14px | 28px:1, 14px:10, 13px:46, 20px:1, 12px:11 | 57 | `screenshots/b3-section-questions-default-1280.png` |
| b3-sections-default | 1440 / light | 1040 | 144 | 1195 | False | 142 / 76 / 576 / 14px | 28px:1, 14px:5, 13px:38, 12px:14, 20px:1 | 52 | `screenshots/b3-sections-default-1440.png` |
| b3-sections-default | 1280 / light | 1024 | 0 | 1218 | False | 142 / 72 / 560 / 14px | 28px:1, 14px:5, 13px:38, 12px:14, 20px:1 | 52 | `screenshots/b3-sections-default-1280.png` |
| b3-sections-saved | 1440 / light | 1040 | 144 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:16, 12px:9, 16px:1 | 25 | `screenshots/b3-sections-saved-1440.png` |
| b3-sections-saved | 1280 / light | 1024 | 0 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:16, 12px:9, 16px:1 | 25 | `screenshots/b3-sections-saved-1280.png` |
| b3-sections-empty | 1440 / light | 1040 | 144 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:8, 16px:1 | 8 | `screenshots/b3-sections-empty-1440.png` |
| b3-sections-empty | 1280 / light | 1024 | 0 | 1000 | False | 114 / 126 / 783.5625 / 14px | 28px:1, 14px:1, 13px:8, 16px:1 | 8 | `screenshots/b3-sections-empty-1280.png` |
| b4-desk_review-ready | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-ready-1440.png` |
| b4-desk_review-ready | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-ready-1280.png` |
| b4-desk_review-running | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-running-1440.png` |
| b4-desk_review-running | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-running-1280.png` |
| b4-desk_review-findings | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-findings-1440.png` |
| b4-desk_review-findings | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-findings-1280.png` |
| b4-desk_review-rerun | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-rerun-1440.png` |
| b4-desk_review-rerun | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-rerun-1280.png` |
| b4-desk_review-error | 1440 / light | 1040 | 144 | 1000 | False | 106 / 106 / 928 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-error-1440.png` |
| b4-desk_review-error | 1280 / light | 1024 | 0 | 1000 | False | 106 / 106 / 912 / 14px | 28px:1, 14px:2, 13px:7, 16px:1, 12px:3 | 10 | `screenshots/b4-desk_review-error-1280.png` |
| b5-analysis-running | 1440 / light | 1040 | 144 | 1000 | False | 88 / 88 / 928 / 13px | 28px:1, 14px:1, 13px:8, 12px:1, 16px:2 | 9 | `screenshots/b5-analysis-running-1440.png` |
| b5-analysis-running | 1280 / light | 1024 | 0 | 1000 | False | 88 / 88 / 912 / 13px | 28px:1, 14px:1, 13px:8, 12px:1, 16px:2 | 9 | `screenshots/b5-analysis-running-1280.png` |
| b5-analysis-complete | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:14, 12px:1, 16px:2 | 15 | `screenshots/b5-analysis-complete-1440.png` |
| b5-analysis-complete | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:14, 12px:1, 16px:2 | 15 | `screenshots/b5-analysis-complete-1280.png` |
| b5-analysis-error | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-error-1440.png` |
| b5-analysis-error | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-error-1280.png` |
| b5-analysis-error-all | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-error-all-1440.png` |
| b5-analysis-error-all | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-error-all-1280.png` |
| b5-analysis-gate | 1440 / light | 1040 | 144 | 1000 | False | 58 / 58 / 420 / 12px | 28px:1, 14px:1, 13px:12, 12px:2, 16px:1 | 14 | `screenshots/b5-analysis-gate-1440.png` |
| b5-analysis-gate | 1280 / light | 1024 | 0 | 1000 | False | 58 / 58 / 420 / 12px | 28px:1, 14px:1, 13px:12, 12px:2, 16px:1 | 14 | `screenshots/b5-analysis-gate-1280.png` |
| b5-analysis-gate-no-override | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-gate-no-override-1440.png` |
| b5-analysis-gate-no-override | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:9, 12px:1, 16px:1 | 10 | `screenshots/b5-analysis-gate-no-override-1280.png` |
| b5-basis-empty | 1440 / light | 1040 | 144 | 1000 | False | 41 / 41 / 263.21875 / 14px | 12px:1, 16px:2, 28px:1, 14px:1, 13px:14 | 15 | `screenshots/b5-basis-empty-1440.png` |
| b5-basis-empty | 1280 / light | 1024 | 0 | 1000 | False | 41 / 41 / 263.21875 / 14px | 12px:1, 16px:2, 28px:1, 14px:1, 13px:14 | 15 | `screenshots/b5-basis-empty-1280.png` |
| b5-basis-filled | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-filled-1440.png` |
| b5-basis-filled | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-filled-1280.png` |
| b5-basis-invalid | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-invalid-1440.png` |
| b5-basis-invalid | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-invalid-1280.png` |
| b5-basis-locked | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-locked-1440.png` |
| b5-basis-locked | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:14 | 16 | `screenshots/b5-basis-locked-1280.png` |
| b5-basis-saved | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:15 | 17 | `screenshots/b5-basis-saved-1440.png` |
| b5-basis-saved | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 12px:2, 16px:2, 28px:1, 14px:1, 13px:15 | 17 | `screenshots/b5-basis-saved-1280.png` |
| b5-board-inputs-empty | 1440 / light | 1040 | 144 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-empty-1440.png` |
| b5-board-inputs-empty | 1280 / light | 1024 | 0 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-empty-1280.png` |
| b5-board-inputs-partly | 1440 / light | 1040 | 144 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-partly-1440.png` |
| b5-board-inputs-partly | 1280 / light | 1024 | 0 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-partly-1280.png` |
| b5-board-inputs-complete | 1440 / light | 1040 | 144 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-complete-1440.png` |
| b5-board-inputs-complete | 1280 / light | 1024 | 0 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-complete-1280.png` |
| b5-board-inputs-dense | 1440 / light | 1040 | 144 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-dense-1440.png` |
| b5-board-inputs-dense | 1280 / light | 1024 | 0 | 4949 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:66, 12px:5, 16px:3 | 71 | `screenshots/b5-board-inputs-dense-1280.png` |
| b5-board-inputs-error | 1440 / light | 1040 | 144 | 4997 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:68, 12px:7, 16px:3 | 75 | `screenshots/b5-board-inputs-error-1440.png` |
| b5-board-inputs-error | 1280 / light | 1024 | 0 | 4997 | False | 131 / 83 / 557.671875 / 13px | 28px:1, 14px:25, 13px:68, 12px:7, 16px:3 | 75 | `screenshots/b5-board-inputs-error-1280.png` |
| b5-conclusion-card-pending | 1440 / light | 1120 | 64 | 1978 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:29, 12px:16, 16px:2, 20px:1 | 45 | `screenshots/b5-conclusion-card-pending-1440.png` |
| b5-conclusion-card-pending | 1280 / light | 1024 | 0 | 2001 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:29, 12px:16, 16px:2, 20px:1 | 45 | `screenshots/b5-conclusion-card-pending-1280.png` |
| b5-conclusion-card-edit | 1440 / light | 1120 | 64 | 2540 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:28, 13px:34, 12px:16, 16px:2, 20px:1 | 50 | `screenshots/b5-conclusion-card-edit-1440.png` |
| b5-conclusion-card-edit | 1280 / light | 1024 | 0 | 2563 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:28, 13px:34, 12px:16, 16px:2, 20px:1 | 50 | `screenshots/b5-conclusion-card-edit-1280.png` |
| b5-conclusion-card-approved | 1440 / light | 1120 | 64 | 2030 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-approved-1440.png` |
| b5-conclusion-card-approved | 1280 / light | 1024 | 0 | 2053 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-approved-1280.png` |
| b5-conclusion-card-edited | 1440 / light | 1120 | 64 | 2005 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-edited-1440.png` |
| b5-conclusion-card-edited | 1280 / light | 1024 | 0 | 2028 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-edited-1280.png` |
| b5-conclusion-card-rejected | 1440 / light | 1120 | 64 | 2030 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:29, 12px:16, 16px:2, 20px:1 | 45 | `screenshots/b5-conclusion-card-rejected-1440.png` |
| b5-conclusion-card-rejected | 1280 / light | 1024 | 0 | 2053 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:29, 12px:16, 16px:2, 20px:1 | 45 | `screenshots/b5-conclusion-card-rejected-1280.png` |
| b5-conclusion-card-blocked | 1440 / light | 1120 | 64 | 2008 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:29, 12px:17, 16px:2, 20px:1 | 46 | `screenshots/b5-conclusion-card-blocked-1440.png` |
| b5-conclusion-card-blocked | 1280 / light | 1024 | 0 | 2031 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:29, 12px:17, 16px:2, 20px:1 | 46 | `screenshots/b5-conclusion-card-blocked-1280.png` |
| b5-conclusion-card-no-citation | 1440 / light | 1120 | 64 | 1949 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:26, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-no-citation-1440.png` |
| b5-conclusion-card-no-citation | 1280 / light | 1024 | 0 | 1949 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:26, 13px:28, 12px:16, 16px:2, 20px:1 | 44 | `screenshots/b5-conclusion-card-no-citation-1280.png` |
| b5-conclusion-card-superseded | 1440 / light | 1120 | 64 | 2084 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:28, 13px:32, 12px:17, 16px:2, 20px:1 | 49 | `screenshots/b5-conclusion-card-superseded-1440.png` |
| b5-conclusion-card-superseded | 1280 / light | 1024 | 0 | 2107 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:28, 13px:32, 12px:17, 16px:2, 20px:1 | 49 | `screenshots/b5-conclusion-card-superseded-1280.png` |
| b5-conclusion-card-locked | 1440 / light | 1120 | 64 | 2136 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:30, 12px:17, 16px:2, 20px:1 | 47 | `screenshots/b5-conclusion-card-locked-1440.png` |
| b5-conclusion-card-locked | 1280 / light | 1024 | 0 | 2159 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:30, 12px:17, 16px:2, 20px:1 | 47 | `screenshots/b5-conclusion-card-locked-1280.png` |
| b5-conclusion-card-conflict | 1440 / light | 1120 | 64 | 2214 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:37, 12px:19, 16px:2, 20px:1 | 56 | `screenshots/b5-conclusion-card-conflict-1440.png` |
| b5-conclusion-card-conflict | 1280 / light | 1024 | 0 | 2237 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:37, 12px:19, 16px:2, 20px:1 | 56 | `screenshots/b5-conclusion-card-conflict-1280.png` |
| b5-conclusion-card-bulk | 1440 / light | 1120 | 64 | 2117 | False | 205 / 111 / 976 / 14px | 28px:1, 14px:27, 13px:30, 12px:16, 16px:2, 20px:1 | 46 | `screenshots/b5-conclusion-card-bulk-1440.png` |
| b5-conclusion-card-bulk | 1280 / light | 1024 | 0 | 2140 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:27, 13px:30, 12px:16, 16px:2, 20px:1 | 46 | `screenshots/b5-conclusion-card-bulk-1280.png` |
| b5-conclusions-default | 1440 / light | 1040 | 144 | 8550 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-default-1440.jpg` |
| b5-conclusions-default | 1280 / light | 1024 | 0 | 8655 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-default-1280.jpg` |
| b5-conclusions-legacy-bulk | 1440 / light | 1040 | 144 | 8550 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-legacy-bulk-1440.jpg` |
| b5-conclusions-legacy-bulk | 1280 / light | 1024 | 0 | 8655 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-legacy-bulk-1280.jpg` |
| b5-conclusions-empty | 1440 / light | 1040 | 144 | 8550 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-empty-1440.jpg` |
| b5-conclusions-empty | 1280 / light | 1024 | 0 | 8655 | False | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:102, 13px:223, 12px:211, 20px:4, 16px:3 | 434 | `screenshots/b5-conclusions-empty-1280.jpg` |
| b5-narrative-empty | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-empty-1440.png` |
| b5-narrative-empty | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-empty-1280.png` |
| b5-narrative-generating | 1440 / light | 1040 | 144 | 1874 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:24, 12px:11, 16px:4 | 35 | `screenshots/b5-narrative-generating-1440.png` |
| b5-narrative-generating | 1280 / light | 1024 | 0 | 1874 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:24, 12px:11, 16px:4 | 35 | `screenshots/b5-narrative-generating-1280.png` |
| b5-narrative-drafted | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-drafted-1440.png` |
| b5-narrative-drafted | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-drafted-1280.png` |
| b5-narrative-partly-accepted | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-partly-accepted-1440.png` |
| b5-narrative-partly-accepted | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-partly-accepted-1280.png` |
| b5-narrative-accepted | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-accepted-1440.png` |
| b5-narrative-accepted | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-accepted-1280.png` |
| b5-narrative-error | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-error-1440.png` |
| b5-narrative-error | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-error-1280.png` |
| b5-narrative-not-released | 1440 / light | 1040 | 144 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-not-released-1440.png` |
| b5-narrative-not-released | 1280 / light | 1024 | 0 | 1787 | False | 91 / 83 / 557.671875 / 13px | 28px:1, 14px:13, 13px:22, 12px:11, 16px:4 | 33 | `screenshots/b5-narrative-not-released-1280.png` |
| b5-recommended-action-empty | 1440 / light | 1120 | 64 | 1088 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:16, 12px:8, 16px:1, 20px:1 | 24 | `screenshots/b5-recommended-action-empty-1440.png` |
| b5-recommended-action-empty | 1280 / light | 1024 | 0 | 1088 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:16, 12px:8, 16px:1, 20px:1 | 24 | `screenshots/b5-recommended-action-empty-1280.png` |
| b5-recommended-action-drafting | 1440 / light | 1120 | 64 | 1052 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:16, 12px:8, 16px:1, 20px:1 | 24 | `screenshots/b5-recommended-action-drafting-1440.png` |
| b5-recommended-action-drafting | 1280 / light | 1024 | 0 | 1052 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:16, 12px:8, 16px:1, 20px:1 | 24 | `screenshots/b5-recommended-action-drafting-1280.png` |
| b5-recommended-action-drafted | 1440 / light | 1120 | 64 | 1170 | False | 94 / 85 / 976 / 13px | 28px:1, 14px:2, 13px:17, 12px:10, 16px:1, 20px:1 | 27 | `screenshots/b5-recommended-action-drafted-1440.png` |
| b5-recommended-action-drafted | 1280 / light | 1024 | 0 | 1170 | False | 94 / 85 / 880 / 13px | 28px:1, 14px:2, 13px:17, 12px:10, 16px:1, 20px:1 | 27 | `screenshots/b5-recommended-action-drafted-1280.png` |
| b5-recommended-action-edited | 1440 / light | 1120 | 64 | 1170 | False | 89 / 80 / 976 / 13px | 28px:1, 14px:2, 13px:17, 12px:10, 16px:1, 20px:1 | 27 | `screenshots/b5-recommended-action-edited-1440.png` |
| b5-recommended-action-edited | 1280 / light | 1024 | 0 | 1170 | False | 89 / 80 / 880 / 13px | 28px:1, 14px:2, 13px:17, 12px:10, 16px:1, 20px:1 | 27 | `screenshots/b5-recommended-action-edited-1280.png` |
| b5-recommended-action-error | 1440 / light | 1120 | 64 | 1144 | False | 74 / 74 / 976 / 13px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-error-1440.png` |
| b5-recommended-action-error | 1280 / light | 1024 | 0 | 1144 | False | 74 / 74 / 880 / 13px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-error-1280.png` |
| b5-recommended-action-saved | 1440 / light | 1120 | 64 | 1000 | False | 138 / 122 / 976 / 16px | 28px:1, 14px:4, 13px:8, 12px:9, 16px:2, 20px:1 | 17 | `screenshots/b5-recommended-action-saved-1440.png` |
| b5-recommended-action-saved | 1280 / light | 1024 | 0 | 1000 | False | 138 / 113 / 880 / 16px | 28px:1, 14px:4, 13px:8, 12px:9, 16px:2, 20px:1 | 17 | `screenshots/b5-recommended-action-saved-1280.png` |
| b5-recommended-action-gaps-required | 1440 / light | 1120 | 64 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-gaps-required-1440.png` |
| b5-recommended-action-gaps-required | 1280 / light | 1024 | 0 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-gaps-required-1280.png` |
| b5-recommended-action-limit | 1440 / light | 1120 | 64 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-limit-1440.png` |
| b5-recommended-action-limit | 1280 / light | 1024 | 0 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-limit-1280.png` |
| b5-recommended-action-stale | 1440 / light | 1120 | 64 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-stale-1440.png` |
| b5-recommended-action-stale | 1280 / light | 1024 | 0 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-stale-1280.png` |
| b5-recommended-action-not-open | 1440 / light | 1120 | 64 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-not-open-1440.png` |
| b5-recommended-action-not-open | 1280 / light | 1024 | 0 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-not-open-1280.png` |
| b5-recommended-action-not-draftable | 1440 / light | 1120 | 64 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-not-draftable-1440.png` |
| b5-recommended-action-not-draftable | 1280 / light | 1024 | 0 | 1144 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:2, 13px:17, 12px:8, 16px:1, 20px:1 | 25 | `screenshots/b5-recommended-action-not-draftable-1280.png` |
| b5-release-blocked | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:6, 12px:1, 16px:2 | 7 | `screenshots/b5-release-blocked-1440.png` |
| b5-release-blocked | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:6, 12px:1, 16px:2 | 7 | `screenshots/b5-release-blocked-1280.png` |
| b5-release-ready | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-ready-1440.png` |
| b5-release-ready | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-ready-1280.png` |
| b5-release-confirm | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-confirm-1440.png` |
| b5-release-confirm | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-confirm-1280.png` |
| b5-release-released | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:11, 12px:1, 16px:1 | 12 | `screenshots/b5-release-released-1440.png` |
| b5-release-released | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:11, 12px:1, 16px:1 | 12 | `screenshots/b5-release-released-1280.png` |
| b5-release-stale | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-stale-1440.png` |
| b5-release-stale | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:1, 13px:10, 12px:1, 16px:1 | 11 | `screenshots/b5-release-stale-1280.png` |
| b5-report-loading-loading | 1440 / light | 1040 | 144 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:8, 12px:5 | 13 | `screenshots/b5-report-loading-loading-1440.png` |
| b5-report-loading-loading | 1280 / light | 1024 | 0 | 1000 | False | 71 / 83 / 486.546875 / 14px | 28px:1, 14px:1, 13px:8, 12px:5 | 13 | `screenshots/b5-report-loading-loading-1280.png` |
| b5-requirement-card-v2 | 1440 / light | 1040 | 144 | 1836 | False | 205 / 111 / 896 / 14px | 28px:1, 14px:22, 13px:24, 12px:12, 16px:1 | 36 | `screenshots/b5-requirement-card-v2-1440.png` |
| b5-requirement-card-v2 | 1280 / light | 1024 | 0 | 1836 | False | 205 / 111 / 880 / 14px | 28px:1, 14px:22, 13px:24, 12px:12, 16px:1 | 36 | `screenshots/b5-requirement-card-v2-1280.png` |
| b5-requirement-card-v2-draft | 1440 / light | 1040 | 144 | 1642 | False | 171 / 145 / 896 / 13px | 28px:1, 14px:22, 13px:24, 12px:12, 16px:1 | 36 | `screenshots/b5-requirement-card-v2-draft-1440.png` |
| b5-requirement-card-v2-draft | 1280 / light | 1024 | 0 | 1642 | False | 171 / 140 / 880 / 13px | 28px:1, 14px:22, 13px:24, 12px:12, 16px:1 | 36 | `screenshots/b5-requirement-card-v2-draft-1280.png` |
| b5-requirement-card-contradiction | 1440 / light | 1040 | 144 | 1577 | False | 171 / 145 / 896 / 13px | 28px:1, 14px:22, 13px:23, 12px:12, 16px:1 | 35 | `screenshots/b5-requirement-card-contradiction-1440.png` |
| b5-requirement-card-contradiction | 1280 / light | 1024 | 0 | 1577 | False | 171 / 140 / 880 / 13px | 28px:1, 14px:22, 13px:23, 12px:12, 16px:1 | 35 | `screenshots/b5-requirement-card-contradiction-1280.png` |
| b5-requirement-card-v1 | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:4, 13px:8, 12px:2, 16px:1 | 10 | `screenshots/b5-requirement-card-v1-1440.png` |
| b5-requirement-card-v1 | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:4, 13px:8, 12px:2, 16px:1 | 10 | `screenshots/b5-requirement-card-v1-1280.png` |
| b5-requirement-card-none | 1440 / light | 1040 | 144 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:8, 12px:1, 16px:1 | 9 | `screenshots/b5-requirement-card-none-1440.png` |
| b5-requirement-card-none | 1280 / light | 1024 | 0 | 1000 | False | 54 / 54 / 368.265625 / 14px | 28px:1, 14px:3, 13px:8, 12px:1, 16px:1 | 9 | `screenshots/b5-requirement-card-none-1280.png` |
| b5-review-finding-card-draft | 1440 / light | 1040 | 144 | 1000 | False | 133 / 133 / 928 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-draft-1440.png` |
| b5-review-finding-card-draft | 1280 / light | 1024 | 0 | 1000 | False | 133 / 123 / 912 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-draft-1280.png` |
| b5-review-finding-card-needs-review | 1440 / light | 1040 | 144 | 1000 | False | 133 / 133 / 928 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-needs-review-1440.png` |
| b5-review-finding-card-needs-review | 1280 / light | 1024 | 0 | 1000 | False | 133 / 123 / 912 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-needs-review-1280.png` |
| b5-review-finding-card-notes | 1440 / light | 1040 | 144 | 1000 | False | 133 / 133 / 928 / 14px | 28px:1, 14px:3, 13px:15, 12px:5, 16px:2 | 20 | `screenshots/b5-review-finding-card-notes-1440.png` |
| b5-review-finding-card-notes | 1280 / light | 1024 | 0 | 1000 | False | 133 / 123 / 912 / 14px | 28px:1, 14px:3, 13px:15, 12px:5, 16px:2 | 20 | `screenshots/b5-review-finding-card-notes-1280.png` |
| b5-review-finding-card-accepted | 1440 / light | 1040 | 144 | 1000 | False | 133 / 133 / 928 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-accepted-1440.png` |
| b5-review-finding-card-accepted | 1280 / light | 1024 | 0 | 1000 | False | 133 / 123 / 912 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-accepted-1280.png` |
| b5-review-finding-card-rejected | 1440 / light | 1040 | 144 | 1000 | False | 133 / 133 / 928 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-rejected-1440.png` |
| b5-review-finding-card-rejected | 1280 / light | 1024 | 0 | 1000 | False | 133 / 123 / 912 / 14px | 28px:1, 14px:3, 13px:14, 12px:5, 16px:2 | 19 | `screenshots/b5-review-finding-card-rejected-1280.png` |
| b5-review-queue-default | 1440 / light | 1120 | 64 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-default-1440.png` |
| b5-review-queue-default | 1280 / light | 1024 | 0 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-default-1280.png` |
| b5-review-queue-shared | 1440 / light | 1120 | 64 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-shared-1440.png` |
| b5-review-queue-shared | 1280 / light | 1024 | 0 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-shared-1280.png` |
| b5-review-queue-done | 1440 / light | 1120 | 64 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-done-1440.png` |
| b5-review-queue-done | 1280 / light | 1024 | 0 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-done-1280.png` |
| b5-review-queue-empty | 1440 / light | 1120 | 64 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-empty-1440.png` |
| b5-review-queue-empty | 1280 / light | 1024 | 0 | 1216 | True | 55 / 55 / 377.109375 / 14px | 28px:1, 14px:1, 13px:111, 12px:138, 16px:1 | 249 | `screenshots/b5-review-queue-empty-1280.png` |
| b6-magic_invalid-expired | 1440 / light | 520 | 920 | 1000 | False | 58 / 44 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-expired-1440.png` |
| b6-magic_invalid-expired | 1280 / light | 520 | 760 | 1000 | False | 58 / 44 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-expired-1280.png` |
| b6-magic_invalid-revoked | 1440 / light | 520 | 920 | 1000 | False | 89 / 49 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-revoked-1440.png` |
| b6-magic_invalid-revoked | 1280 / light | 520 | 760 | 1000 | False | 89 / 49 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-revoked-1280.png` |
| b6-magic_invalid-unknown | 1440 / light | 520 | 920 | 1000 | False | 91 / 47 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-unknown-1440.png` |
| b6-magic_invalid-unknown | 1280 / light | 520 | 760 | 1000 | False | 91 / 47 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b6-magic_invalid-unknown-1280.png` |
| b6-magic_links-default | 1440 / light | 1040 | 144 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-default-1440.png` |
| b6-magic_links-default | 1280 / light | 1024 | 0 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-default-1280.png` |
| b6-magic_links-empty | 1440 / light | 1040 | 144 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-empty-1440.png` |
| b6-magic_links-empty | 1280 / light | 1024 | 0 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-empty-1280.png` |
| b6-magic_links-error | 1440 / light | 1040 | 144 | 1014 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:19, 12px:8, 16px:3 | 27 | `screenshots/b6-magic_links-error-1440.png` |
| b6-magic_links-error | 1280 / light | 1024 | 0 | 1014 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:19, 12px:8, 16px:3 | 27 | `screenshots/b6-magic_links-error-1280.png` |
| b6-magic_links-loading | 1440 / light | 1040 | 144 | 1241 | False | 47 / 47 / 310.75 / 14px | 28px:1, 14px:10, 13px:7, 12px:6, 16px:2 | 13 | `screenshots/b6-magic_links-loading-1440.png` |
| b6-magic_links-loading | 1280 / light | 1024 | 0 | 1241 | False | 47 / 47 / 310.75 / 14px | 28px:1, 14px:10, 13px:7, 12px:6, 16px:2 | 13 | `screenshots/b6-magic_links-loading-1280.png` |
| b6-magic_links-newlink | 1440 / light | 1040 | 144 | 1060 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:20, 12px:8, 16px:3 | 28 | `screenshots/b6-magic_links-newlink-1440.png` |
| b6-magic_links-newlink | 1280 / light | 1024 | 0 | 1060 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:20, 12px:8, 16px:3 | 28 | `screenshots/b6-magic_links-newlink-1280.png` |
| b6-magic_links-revoke | 1440 / light | 1040 | 144 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-revoke-1440.png` |
| b6-magic_links-revoke | 1280 / light | 1024 | 0 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/b6-magic_links-revoke-1280.png` |
| b6-report_snapshots-default | 1440 / light | 1040 | 144 | 1000 | False | 57 / 57 / 391.78125 / 14px | 28px:1, 14px:1, 13px:13, 12px:6, 16px:1 | 19 | `screenshots/b6-report_snapshots-default-1440.png` |
| b6-report_snapshots-default | 1280 / light | 1024 | 0 | 1000 | False | 57 / 57 / 391.78125 / 14px | 28px:1, 14px:1, 13px:13, 12px:6, 16px:1 | 19 | `screenshots/b6-report_snapshots-default-1280.png` |
| b6-rfi-default | 1440 / light | 1040 | 144 | 20005 | False | 426 / 37 / 771.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/b6-rfi-default-1440.jpg` |
| b6-rfi-default | 1280 / light | 1024 | 0 | 20005 | False | 426 / 37 / 755.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/b6-rfi-default-1280.jpg` |
| b6-rfi-error | 1440 / light | 1040 | 144 | 20092 | False | 426 / 37 / 771.671875 / 14px | 28px:1, 14px:923, 13px:1330, 12px:418 | 1748 | `screenshots/b6-rfi-error-1440.jpg` |
| b6-rfi-error | 1280 / light | 1024 | 0 | 20092 | False | 426 / 37 / 755.671875 / 14px | 28px:1, 14px:923, 13px:1330, 12px:418 | 1748 | `screenshots/b6-rfi-error-1280.jpg` |
| b6-rfi-issue | 1440 / light | 1040 | 144 | 1000 | False | 108 / 56 / 392 / 14px | 28px:1, 14px:2, 13px:12, 12px:5, 16px:2, 20px:1 | 17 | `screenshots/b6-rfi-issue-1440.png` |
| b6-rfi-issue | 1280 / light | 1024 | 0 | 1000 | False | 108 / 56 / 392 / 14px | 28px:1, 14px:2, 13px:12, 12px:5, 16px:2, 20px:1 | 17 | `screenshots/b6-rfi-issue-1280.png` |
| b6-rfi-loading | 1440 / light | 1040 | 144 | 1000 | False | - | 28px:1, 14px:1, 13px:7, 12px:2 | 9 | `screenshots/b6-rfi-loading-1440.png` |
| b6-rfi-loading | 1280 / light | 1024 | 0 | 1000 | False | - | 28px:1, 14px:1, 13px:7, 12px:2 | 9 | `screenshots/b6-rfi-loading-1280.png` |
| b6-rfi-noscope | 1440 / light | 1040 | 144 | 20005 | False | 426 / 37 / 771.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/b6-rfi-noscope-1440.jpg` |
| b6-rfi-noscope | 1280 / light | 1024 | 0 | 20005 | False | 426 / 37 / 755.671875 / 14px | 28px:1, 14px:923, 13px:1328, 12px:418 | 1746 | `screenshots/b6-rfi-noscope-1280.jpg` |
| b6-rfi-versions | 1440 / light | 1040 | 144 | 1000 | False | 55 / 39 / 295.234375 / 13px | 28px:1, 14px:1, 13px:10, 12px:5, 16px:2 | 15 | `screenshots/b6-rfi-versions-1440.png` |
| b6-rfi-versions | 1280 / light | 1024 | 0 | 1000 | False | 55 / 39 / 295.234375 / 13px | 28px:1, 14px:1, 13px:10, 12px:5, 16px:2 | 15 | `screenshots/b6-rfi-versions-1280.png` |
| b6-soa-default | 1440 / light | 1040 | 144 | 17481 | False | 140 / 91 / 574.078125 / 13px | 28px:1, 14px:1, 13px:195, 12px:566 | 761 | `screenshots/b6-soa-default-1440.jpg` |
| b6-soa-default | 1280 / light | 1024 | 0 | 17481 | False | 140 / 91 / 574.078125 / 13px | 28px:1, 14px:1, 13px:195, 12px:566 | 761 | `screenshots/b6-soa-default-1280.jpg` |
| b7-404-page | 1440 / light | 1040 | 144 | 1000 | False | 52 / 47 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-404-page-1440.png` |
| b7-404-page | 1280 / light | 1024 | 0 | 1000 | False | 52 / 47 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-404-page-1280.png` |
| b7-404-engagement | 1440 / light | 1040 | 144 | 1000 | False | 84 / 44 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-404-engagement-1440.png` |
| b7-404-engagement | 1280 / light | 1024 | 0 | 1000 | False | 84 / 44 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-404-engagement-1280.png` |
| b7-500-error | 1440 / light | 1040 | 144 | 1000 | False | 106 / 45 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-error-1440.png` |
| b7-500-error | 1280 / light | 1024 | 0 | 1000 | False | 106 / 45 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-error-1280.png` |
| b7-500-down | 1440 / light | 1040 | 144 | 1000 | False | 59 / 46 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-down-1440.png` |
| b7-500-down | 1280 / light | 1024 | 0 | 1000 | False | 59 / 46 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-down-1280.png` |
| b7-500-upstream | 1440 / light | 1040 | 144 | 1000 | False | 74 / 45 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-upstream-1440.png` |
| b7-500-upstream | 1280 / light | 1024 | 0 | 1000 | False | 74 / 45 / 295.234375 / 13px | 20px:1, 13px:4, 12px:1 | 5 | `screenshots/b7-500-upstream-1280.png` |
| b7-empty-states-engagements | 1440 / light | 1040 | 144 | 1000 | False | 75 / 43 / 295.234375 / 13px | 28px:1, 16px:1, 13px:2 | 2 | `screenshots/b7-empty-states-engagements-1440.png` |
| b7-empty-states-engagements | 1280 / light | 1024 | 0 | 1000 | False | 75 / 43 / 295.234375 / 13px | 28px:1, 16px:1, 13px:2 | 2 | `screenshots/b7-empty-states-engagements-1280.png` |
| b7-empty-states-evidence | 1440 / light | 1040 | 144 | 5151 | False | 48 / 48 / 578.265625 / 14px | 28px:1, 14px:68, 13px:344, 12px:73 | 417 | `screenshots/b7-empty-states-evidence-1440.png` |
| b7-empty-states-evidence | 1280 / light | 1024 | 0 | 5151 | False | 48 / 48 / 578.265625 / 14px | 28px:1, 14px:68, 13px:344, 12px:73 | 417 | `screenshots/b7-empty-states-evidence-1280.png` |
| b7-empty-states-review | 1440 / light | 1040 | 144 | 1000 | False | 62 / 45 / 295.234375 / 13px | 28px:1, 14px:1, 16px:1, 13px:2 | 2 | `screenshots/b7-empty-states-review-1440.png` |
| b7-empty-states-review | 1280 / light | 1024 | 0 | 1000 | False | 62 / 45 / 295.234375 / 13px | 28px:1, 14px:1, 16px:1, 13px:2 | 2 | `screenshots/b7-empty-states-review-1280.png` |
| b7-empty-states-search | 1440 / light | 1040 | 144 | 1000 | False | 42 / 42 / 263.5 / 13px | 28px:1, 13px:2, 12px:2, 16px:1 | 4 | `screenshots/b7-empty-states-search-1440.png` |
| b7-empty-states-search | 1280 / light | 1024 | 0 | 1000 | False | 42 / 42 / 263.5 / 13px | 28px:1, 13px:2, 12px:2, 16px:1 | 4 | `screenshots/b7-empty-states-search-1280.png` |
| b7-empty-states-findings | 1440 / light | 1040 | 144 | 1497 | False | 55 / 55 / 375.984375 / 14px | 28px:1, 14px:18, 13px:32, 12px:33, 16px:2 | 65 | `screenshots/b7-empty-states-findings-1440.png` |
| b7-empty-states-findings | 1280 / light | 1024 | 0 | 1497 | False | 55 / 55 / 375.984375 / 14px | 28px:1, 14px:18, 13px:32, 12px:33, 16px:2 | 65 | `screenshots/b7-empty-states-findings-1280.png` |
| b7-empty-states-report | 1440 / light | 1040 | 144 | 1000 | False | 46 / 46 / 324.53125 / 14px | 28px:1, 14px:25, 12px:6, 13px:8 | 14 | `screenshots/b7-empty-states-report-1440.png` |
| b7-empty-states-report | 1280 / light | 1024 | 0 | 1000 | False | 46 / 46 / 324.53125 / 14px | 28px:1, 14px:25, 12px:6, 13px:8 | 14 | `screenshots/b7-empty-states-report-1280.png` |
| b7-htmx-swaps-ok | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:8, 28px:1, 14px:2, 16px:1 | 8 | `screenshots/b7-htmx-swaps-ok-1440.png` |
| b7-htmx-swaps-ok | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:8, 28px:1, 14px:2, 16px:1 | 8 | `screenshots/b7-htmx-swaps-ok-1280.png` |
| b7-htmx-swaps-bad | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:1, 16px:1 | 6 | `screenshots/b7-htmx-swaps-bad-1440.png` |
| b7-htmx-swaps-bad | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:1, 16px:1 | 6 | `screenshots/b7-htmx-swaps-bad-1280.png` |
| b7-link-expired-expired | 1440 / light | 520 | 920 | 1000 | False | 58 / 44 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b7-link-expired-expired-1440.png` |
| b7-link-expired-expired | 1280 / light | 520 | 760 | 1000 | False | 58 / 44 / 295.234375 / 13px | 13px:3, 15px:1, 20px:1, 14px:1 | 3 | `screenshots/b7-link-expired-expired-1280.png` |
| b7-menus-popovers-default | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:11, 28px:1, 14px:6 | 11 | `screenshots/b7-menus-popovers-default-1440.png` |
| b7-menus-popovers-default | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:11, 28px:1, 14px:6 | 11 | `screenshots/b7-menus-popovers-default-1280.png` |
| b7-mobile-shell-default | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:13, 28px:1, 14px:6, 16px:3, 12px:6 | 19 | `screenshots/b7-mobile-shell-default-1440.png` |
| b7-mobile-shell-default | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:13, 28px:1, 14px:6, 16px:3, 12px:6 | 19 | `screenshots/b7-mobile-shell-default-1280.png` |
| b7-modals-delete | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-delete-1440.png` |
| b7-modals-delete | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-delete-1280.png` |
| b7-modals-purge | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:2, 20px:1, 12px:1 | 7 | `screenshots/b7-modals-purge-1440.png` |
| b7-modals-purge | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:2, 20px:1, 12px:1 | 7 | `screenshots/b7-modals-purge-1280.png` |
| b7-modals-send | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-send-1440.png` |
| b7-modals-send | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-send-1280.png` |
| b7-modals-invite | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:7, 28px:1, 14px:1, 20px:1, 12px:1 | 8 | `screenshots/b7-modals-invite-1440.png` |
| b7-modals-invite | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:7, 28px:1, 14px:1, 20px:1, 12px:1 | 8 | `screenshots/b7-modals-invite-1280.png` |
| b7-modals-discard | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-discard-1440.png` |
| b7-modals-discard | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:5, 28px:1, 14px:2, 20px:1 | 5 | `screenshots/b7-modals-discard-1280.png` |
| b7-modals-failed | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:7, 28px:1, 14px:1, 20px:1 | 7 | `screenshots/b7-modals-failed-1440.png` |
| b7-modals-failed | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:7, 28px:1, 14px:1, 20px:1 | 7 | `screenshots/b7-modals-failed-1280.png` |
| b7-skeleton-detail-loading | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:2, 28px:1, 14px:1 | 2 | `screenshots/b7-skeleton-detail-loading-1440.png` |
| b7-skeleton-detail-loading | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:2, 28px:1, 14px:1 | 2 | `screenshots/b7-skeleton-detail-loading-1280.png` |
| b7-skeleton-detail-loaded | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:16, 28px:2, 14px:1, 16px:2 | 16 | `screenshots/b7-skeleton-detail-loaded-1440.png` |
| b7-skeleton-detail-loaded | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:16, 28px:2, 14px:1, 16px:2 | 16 | `screenshots/b7-skeleton-detail-loaded-1280.png` |
| b7-skeleton-table-loading | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:2, 28px:1, 14px:1, 12px:4 | 6 | `screenshots/b7-skeleton-table-loading-1440.png` |
| b7-skeleton-table-loading | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:2, 28px:1, 14px:1, 12px:4 | 6 | `screenshots/b7-skeleton-table-loading-1280.png` |
| b7-skeleton-table-loaded | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:3, 12px:7, 16px:2 | 13 | `screenshots/b7-skeleton-table-loaded-1440.png` |
| b7-skeleton-table-loaded | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:6, 28px:1, 14px:3, 12px:7, 16px:2 | 13 | `screenshots/b7-skeleton-table-loaded-1280.png` |
| b7-toasts-default | 1440 / light | 1184 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:13, 28px:1, 14px:5 | 13 | `screenshots/b7-toasts-default-1440.png` |
| b7-toasts-default | 1280 / light | 1024 | 0 | 1115 | False | 86 / 86 / 591.5 / 14px | 13px:13, 28px:1, 14px:5 | 13 | `screenshots/b7-toasts-default-1280.png` |
| evidence_reuse-default | 1440 / light | 1040 | 144 | 5637 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:119, 12px:20 | 139 | `screenshots/evidence_reuse-default-1440.png` |
| evidence_reuse-default | 1280 / light | 1024 | 0 | 5637 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:119, 12px:20 | 139 | `screenshots/evidence_reuse-default-1280.png` |
| evidence_reuse-error | 1440 / light | 1040 | 144 | 5716 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:121, 12px:20 | 141 | `screenshots/evidence_reuse-error-1440.png` |
| evidence_reuse-error | 1280 / light | 1024 | 0 | 5716 | False | 178 / 90 / 618.234375 / 14px | 28px:1, 14px:59, 13px:121, 12px:20 | 141 | `screenshots/evidence_reuse-error-1280.png` |
| login-default | 1440 / light | 1440 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:3 | 5 | `screenshots/login-default-1440.png` |
| login-default | 1280 / light | 1280 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:3 | 5 | `screenshots/login-default-1280.png` |
| login-error | 1440 / light | 1440 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:5 | 7 | `screenshots/login-error-1440.png` |
| login-error | 1280 / light | 1280 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:5 | 7 | `screenshots/login-error-1280.png` |
| login-loading | 1440 / light | 1440 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:2 | 4 | `screenshots/login-loading-1440.png` |
| login-loading | 1280 / light | 1280 | 0 | 1000 | False | - | 12px:2, 16px:1, 28px:1, 13px:2 | 4 | `screenshots/login-loading-1280.png` |
| workpaper_entry-default | 1440 / light | 1040 | 144 | 2423 | False | 54 / 54 / 794.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-default-1440.png` |
| workpaper_entry-default | 1280 / light | 1024 | 0 | 2453 | False | 54 / 54 / 778.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-default-1280.png` |
| workpaper_entry-legacy | 1440 / light | 1040 | 144 | 2423 | False | 54 / 54 / 794.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-legacy-1440.png` |
| workpaper_entry-legacy | 1280 / light | 1024 | 0 | 2453 | False | 54 / 54 / 778.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-legacy-1280.png` |
| workpaper_entry-excluded | 1440 / light | 1040 | 144 | 2423 | False | 54 / 54 / 794.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-excluded-1440.png` |
| workpaper_entry-excluded | 1280 / light | 1024 | 0 | 2453 | False | 54 / 54 / 778.515625 / 14px | 28px:1, 14px:30, 12px:16, 13px:32, 16px:5 | 48 | `screenshots/workpaper_entry-excluded-1280.png` |
| gallery | 1440 / light | 1440 | 0 | 3994 | False | 82 / 52 / 392 / 14px | 28px:1, 13px:61, 16px:12, 12px:29, 14px:12, 20px:2 | 90 | `screenshots/gallery-1440.png` |
| gallery | 1280 / light | 1280 | 0 | 3994 | False | 82 / 52 / 392 / 14px | 28px:1, 13px:61, 16px:12, 12px:29, 14px:12, 20px:2 | 90 | `screenshots/gallery-1280.png` |
| questionnaire-open | 1440 / light | 1040 | 144 | 6922 | False | 202 / 101 / 576 / 12px | 28px:1, 14px:17, 13px:115, 16px:3, 12px:44, 20px:1 | 159 | `screenshots/questionnaire-open-1440.jpg` |
| questionnaire-open | 1280 / light | 1024 | 0 | 6673 | False | 202 / 100 / 560 / 12px | 28px:1, 14px:17, 13px:115, 16px:3, 12px:44, 20px:1 | 159 | `screenshots/questionnaire-open-1280.jpg` |
| conclusions-expanded | 1440 / light | 1040 | 144 | 10112 | False | 458 / 128 / 848 / 14px | 28px:1, 14px:118, 13px:242, 12px:228, 20px:5, 16px:4 | 470 | `screenshots/conclusions-expanded-1440.jpg` |
| conclusions-expanded | 1280 / light | 1024 | 0 | 10217 | False | 458 / 128 / 832 / 14px | 28px:1, 14px:118, 13px:242, 12px:228, 20px:5, 16px:4 | 470 | `screenshots/conclusions-expanded-1280.jpg` |
| requests | 1440 / dark | 1040 | 144 | 1000 | False | 84 / 43 / 295.234375 / 13px | 28px:1, 14px:10, 13px:17, 12px:8, 16px:3 | 25 | `screenshots/requests-dark-1440.png` |
| evidence-assessment | 1440 / dark | 1040 | 144 | 4498 | False | 92 / 92 / 624.90625 / 14px | 28px:1, 14px:59, 13px:301, 12px:64 | 365 | `screenshots/evidence-assessment-dark-1440.png` |
| questionnaire | 1440 / dark | 1040 | 144 | 4906 | False | 202 / 101 / 576 / 12px | 28px:1, 14px:17, 13px:115, 16px:3, 12px:44, 20px:1 | 159 | `screenshots/questionnaire-dark-1440.png` |
| review-queue | 1440 / dark | 1120 | 64 | 1177 | False | 280 / 85 / 674 / 16px | 28px:1, 14px:18, 13px:35, 12px:31, 20px:1, 16px:1 | 66 | `screenshots/review-queue-dark-1440.png` |
| report | 1440 / dark | 1040 | 144 | 2944 | False | 416 / 138 / 928 / 14px | 28px:2, 14px:38, 13px:44, 12px:29, 16px:11 | 73 | `screenshots/report-dark-1440.png` |
| review-selected | 1440 / light | 1120 | 64 | 1177 | False | - | 28px:1, 14px:18, 13px:35, 12px:31, 20px:1, 16px:1 | 66 | `screenshots/review-selected-1440.png` |
| review-selected | 1280 / light | 1024 | 0 | 1177 | False | - | 28px:1, 14px:18, 13px:35, 12px:31, 20px:1, 16px:1 | 66 | `screenshots/review-selected-1280.png` |
| conclusions-edit | 1440 / light | 1040 | 144 | 5121 | False | - | 28px:1, 14px:44, 13px:73, 12px:51, 20px:6, 16px:5 | 124 | `screenshots/conclusions-edit-1440.png` |
| conclusions-edit | 1280 / light | 1024 | 0 | 5142 | False | - | 28px:1, 14px:44, 13px:73, 12px:51, 20px:6, 16px:5 | 124 | `screenshots/conclusions-edit-1280.png` |
| confirm-dialog | 1440 / light | 1184 | 0 | 1115 | False | - | 13px:6, 28px:1, 14px:2, 20px:1, 12px:1 | 7 | `screenshots/confirm-dialog-1440.png` |
| confirm-dialog | 1280 / light | 1024 | 0 | 1115 | False | - | 13px:6, 28px:1, 14px:2, 20px:1, 12px:1 | 7 | `screenshots/confirm-dialog-1280.png` |
| b6-magic_upload-default | 390 / light | 390 | 0 | 1045 | False | - | 13px:10, 15px:1, 14px:6, 24px:1, 12px:1 | 11 | `screenshots/b6-magic_upload-default-390.png` |
| b6-magic_upload-uploading | 390 / light | 390 | 0 | 1015 | False | - | 13px:9, 15px:1, 14px:7, 24px:1, 12px:1 | 10 | `screenshots/b6-magic_upload-uploading-390.png` |
| b6-magic_upload-done | 390 / light | 390 | 0 | 1000 | False | - | 13px:12, 15px:1, 14px:7, 24px:1, 12px:1 | 13 | `screenshots/b6-magic_upload-done-390.png` |
| b6-magic_upload-error | 390 / light | 390 | 0 | 1152 | False | - | 13px:12, 15px:1, 14px:6, 24px:1, 12px:1 | 13 | `screenshots/b6-magic_upload-error-390.png` |
| evidence-cited | 1440 / light | 1040 | 144 | 3124 | False | - | 28px:1, 14px:26, 13px:49, 12px:35, 20px:5, 16px:4 | 84 | `screenshots/evidence-cited-1440.png` |
| evidence-cited | 1280 / light | 1024 | 0 | 3145 | False | - | 28px:1, 14px:26, 13px:49, 12px:35, 20px:5, 16px:4 | 84 | `screenshots/evidence-cited-1280.png` |

## Content interpretation

Open questionnaire: guidance reaches 101 characters per line at 12px, with 159 visible nodes below 14px. Review queue: longest paragraph reaches 85 characters at 16px, with 66 below-14 nodes. ISO report: longest paragraph reaches 138 characters at 14px, page height 15,854px. RFI items: height 20,005px, 1,746 nodes below 14px. SoA: height 17,481px, 761 nodes below 14px. Evidence record: prose reaches 88 characters at 13px. Mobile upload is 390px wide without horizontal overflow; its default state has eleven below-14 nodes and its error state thirteen. The host reports that eight Tab presses never reach the file input.

These confirm width, size and reading-measure findings. They do not measure human scanning time, fatigue or every navigation/save interaction. The two comparison fixture captures return 404; live comparison captures establish the populated screen.

## Contrast method and complete matrix

The complete [contrast appendix](CONTRAST_APPENDIX.md) contains every source-discovered foreground-token candidate against declared surface families in light and dark, with each accent where needed. It is a conservative superset, not a list of verified DOM pairings. [contrast-data.json](contrast-data.json) retains declaration locations and all ratios; [contrast.py](tools/contrast.py) reproduces them. Source-computed values are rounded to three decimals. WCAG normal text requires 4.5:1; large text and non-text markers can use 3:1 when the applicable conditions hold.

The calculation linearizes sRGB channels, uses relative luminance and `(Llighter + .05)/(Ldarker + .05)`, samples 101 positions on each gradient segment, then composites declared alpha surfaces. Glass includes the CSS saturation approximation on a flat canvas. The min/max ratios cover lightest and darkest gradient contributions and intermediate samples. Nested surfaces are enumerated in the appendix. Blur, content behind overlays, custom firm colors, hover oklab mixing and disabled opacity are not certified. Print reports have a separate palette and are outside this portal audit.

The Playwright measurement tool also records computed foreground and ancestor background/opacity/image layers. Associate these with source tokens before calling a candidate failure an actual usage failure. Validate glass bounds by inspecting real backdrop pixels against the retained captures and migration acceptance.

### Base body tokens against canvas and reading surfaces

| Theme | Text token | Surface | Minimum | Maximum | AA normal |
|---|---|---|---:|---:|---|
| light | muted | canvas | 4.720 | 5.314 | Pass |
| light | muted | glass | 5.823 | 6.087 | Pass |
| light | muted | solid | 6.429 | 6.498 | Pass |
| light | text | canvas | 12.385 | 13.942 | Pass |
| light | text | glass | 15.278 | 15.971 | Pass |
| light | text | solid | 16.868 | 17.051 | Pass |
| light | text-2 | canvas | 6.953 | 7.827 | Pass |
| light | text-2 | glass | 8.577 | 8.967 | Pass |
| light | text-2 | solid | 9.470 | 9.573 | Pass |
| dark | muted | canvas | 6.035 | 6.393 | Pass |
| dark | muted | glass | 5.133 | 5.476 | Pass |
| dark | muted | solid | 6.877 | 6.913 | Pass |
| dark | text | canvas | 13.199 | 13.982 | Pass |
| dark | text | glass | 11.226 | 11.976 | Pass |
| dark | text | solid | 15.042 | 15.119 | Pass |
| dark | text-2 | canvas | 8.349 | 8.844 | Pass |
| dark | text-2 | glass | 7.101 | 7.575 | Pass |
| dark | text-2 | solid | 9.514 | 9.563 | Pass |

### Interpretation

Base text, secondary and muted tokens pass AA normal against the modeled canvas, glass and solid surfaces. Preserve this evidence when deciding whether a reading problem is size, hierarchy, repetition or contrast. Seven non-graphite presets retain light accent-text in dark theme and need pair-specific correction. Some primary gradient endpoint pairings fall below 4.5:1, but endpoint bounds are not proof that the text sits over that endpoint. Semantic amber/orange marker colors must not be used indiscriminately as small text.

The status inventory records where color is a fill, marker or foreground: [STATUS_INVENTORY.md](STATUS_INVENTORY.md). A badge can use a readable text token with a low-contrast colored marker without failing text contrast; inspect its actual anatomy.

## Remaining implementation acceptance

Existing captures and geometry are reconciled. Migration acceptance still needs keyboard/screen-reader links, Back/Forward selection recovery, autosave failure/retry, full-set queue scaling and every theme preset's actual DOM pairings. No browser or mutating application request ran in this docs-only pass.
