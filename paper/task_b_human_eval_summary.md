# Task B Human Eval - Recommendation Relevance (blind A/B)

NaijaReviewer-8B vs Claude Sonnet 4 as the recommendation re-ranker. Raters judged which of two blind, randomised product lists is more contextually relevant for each Nigerian persona, and rated each list 1-5.

- Raters: **3**
- Scenarios in master: **24**
- Decisive votes (excluding Equal/Skip): **59**
- Ties (Equal votes): **12**

## Headline

**NaijaReviewer-8B win-rate: 25.4%  (95% CI [16.1%, 37.8%])**

Mean relevance (1-5): **NaijaReviewer-8B 3.00** vs **Claude 3.68** (over 72 paired ratings).

Inter-rater agreement (Krippendorff alpha, nominal): **0.22**

## Per-rater breakdown

| Rater | Naija wins | Other wins | Ties | Decisive | Naija win-rate | 95% CI | rel Naija | rel Other |
|---|---|---|---|---|---|---|---|---|
| Christianah | 6 | 16 | 2 | 22 | 27.3% | [13.2%, 48.2%] | 2.62 | 3.92 |
| Uvere_Amarachi_061714 | 3 | 12 | 9 | 15 | 20.0% | [7.0%, 45.2%] | 3.79 | 4.25 |
| ashinze | 6 | 16 | 1 | 22 | 27.3% | [13.2%, 48.2%] | 2.58 | 2.88 |
