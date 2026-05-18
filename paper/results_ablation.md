# Ablation Study — what contributes the wins?

Each condition is evaluated on the same held-out test split. The full system (A) is the baseline; each subsequent row removes one component. Numbers are point estimates with bootstrap 95% CI in brackets.

| Condition | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Markers/review |
|---|---|---|---|---|---|---|
| **A. Full pipeline (NaijaReviewer-8B)** | 50 | 1.068 [0.980, 1.166] | 0.860 | 0.206 | 48.0% [34.0%, 62.0%] | 3.22 [2.74, 3.72] |
| **B. − register-aware prompt** | 50 | 1.077 [0.927, 1.241] | 0.856 | 0.200 | 6.0% [0.0%, 14.0%] | 0.16 [0.04, 0.32] |
| **C. − structured persona** | 50 | 1.020 [0.980, 1.086] | 0.854 | 0.206 | 4.0% [0.0%, 10.0%] | 0.00 [0.00, 0.00] |
| **D. − fine-tune (base Llama-3.1 70B via NIM)** | 0 | nan | nan | nan | 0.0% | nan |
