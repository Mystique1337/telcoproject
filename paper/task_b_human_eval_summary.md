# Task B Human Eval - Recommendation Relevance (blind A/B)

NaijaReviewer-8B vs Claude Sonnet 4 as the recommendation re-ranker. Raters judged which of two blind, randomised product lists is more contextually relevant for each Nigerian persona, and rated each list 1-5.

- Raters: **2**
- Scenarios in master: **24**
- Decisive votes (excluding Equal/Skip): **44**
- Ties (Equal votes): **3**

## Headline

**NaijaReviewer-8B win-rate: 27.3%  (95% CI [16.3%, 41.8%])**

Mean relevance (1-5): **NaijaReviewer-8B 2.60** vs **Claude 3.40** (over 48 paired ratings).

Inter-rater agreement (Krippendorff alpha, nominal): **0.14**

## Per-rater breakdown

| Rater | Naija wins | Other wins | Ties | Decisive | Naija win-rate | 95% CI | rel Naija | rel Other |
|---|---|---|---|---|---|---|---|---|
| Christianah | 6 | 16 | 2 | 22 | 27.3% | [13.2%, 48.2%] | 2.62 | 3.92 |
| ashinze | 6 | 16 | 1 | 22 | 27.3% | [13.2%, 48.2%] | 2.58 | 2.88 |
