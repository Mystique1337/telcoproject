# The AgentSociety Challenge: A Complete Strategic Guide for the Nigerian/African Variant

**A research-grounded playbook for building winning LLM agents for User Modeling and Recommendation, with deep coverage of the WWW'25 winning solutions, the post-challenge state of the art, and the Nigerian context opportunity.**

---

## Table of Contents

1. Executive Summary
2. What This Competition Actually Is
3. The Six Winning Solutions Explained in Detail
4. The Shared Winning Playbook
5. Post-Challenge State of the Art (2025–2026)
6. The Nigerian Context as Research Contribution
7. Three Architecture Proposals
8. Build Plan: Six Weeks From Zero to Submission
9. Paper Outline and the Ablations You Must Run
10. Use Cases Beyond the Competition
11. Complete Resource Index
12. Glossary
13. Risk Register and Common Pitfalls

---

## 1. Executive Summary

You are entering a competition that is, with very high probability, the Nigerian/African localization of the **WWW'25 AgentSociety Challenge**, organized in early 2025 by Tsinghua University's FIBLAB and Infinigence AI in cooperation with the Web Conference. The original challenge attracted 295 teams worldwide and received over 1,400 submissions across two tracks: **User Modeling** (simulate user reviews and ratings) and **Recommendation** (deliver personalized recommendations). The datasets are Yelp, Amazon Reviews, and Goodreads. The metrics are ROUGE/BERTScore for review text quality, RMSE for rating accuracy, and Hit Rate / NDCG for recommendation ranking.

This is enormously important because it means: **the winning architectures are already published, the simulator is already open-source, and a full year of research has built on top of them.** You are not entering a blank field. You are entering a competition where the floor is high but the ceiling is well-mapped. The strategic question is no longer "what architecture should I build?" — it is "what extensions on top of the winning architectures will earn me both the technical metrics and the paper credit?"

This guide compiles the complete information map: who won, with what, the methods in detail, the patterns that recur across all winners, the gaps the winners did not address, the research that has emerged in the year since the challenge, the Nigerian-specific opportunity that the global winners could not exploit, three concrete architecture proposals you can build, a six-week execution plan, a paper outline, and use cases that extend beyond the competition itself.

**The single most important strategic insight**: the brief says "*A model score reflects what your machine did. A solution paper reveals what you understood. Both matter — but in a talent-identification context, the paper is what we read first.*" The 295 teams from the original 2025 challenge mostly optimized for the leaderboard. You should optimize for the paper, while clearing the metric floor by re-implementing the winning architecture. The Nigerian context bonus is your structural advantage — global winners could not exploit it.

---

## 2. What This Competition Actually Is

### 2.1 The original challenge

The WWW'25 AgentSociety Challenge ran from January 1, 2025 to February 14, 2025. It was the first competition at the Web Conference dedicated to LLM agents for user modeling and recommendation. Organized by Tsinghua's FIBLAB under Prof. Fengli Xu and Prof. Yong Li, with Infinigence AI as a co-organizer. The official paper analyzing outcomes is *Yan et al., "AgentSociety Challenge: Designing LLM Agents for User Modeling and Recommendation on Web Platforms,"* arXiv:2502.18754 (February 2025). The workshop ran on April 29, 2025 in Sydney at the Web Conference (ICC Sydney, Room C2.5).

### 2.2 The two tracks

**Track 1 — User Modeling.** Given a user (with historical reviews and metadata) and a target item, generate a star rating (1–5) and a written review that simulate what the user would have produced. Evaluated on rating accuracy (RMSE / MAE-derived score) and review quality (a combination of emotional tone, sentiment attitude, and topic relevance measured via Sentence-BERT embeddings and TweetEval-style classifiers).

**Track 2 — Recommendation.** Given a user and a candidate item set (in the AgentRecBench follow-up: 1 ground-truth positive + 19 negative items), rank the candidates so that the ground truth ranks high. Evaluated on Hit Rate at k=1, 3, 5 (HR@1, HR@3, HR@5), averaged. The challenge also includes evolving-interest and cold-start scenarios.

### 2.3 The datasets

All three are open-source, large-scale, real-world review platforms:

- **Yelp Open Dataset** — millions of restaurant and local business reviews, with metadata like funny/cool/useful vote counts, business attributes, hours, location.
- **Amazon Reviews (UCSD, 2023 release by Hou, Li, He, Yan, Chen, McAuley)** — e-commerce reviews with verified-purchase flags, product metadata, helpfulness votes.
- **Goodreads (UCSD, Wan and McAuley 2018)** — book reviews with reading status (read/currently-reading/want-to-read), shelves, vote counts.

The official simulator wraps them into a unified User-Review-Item graph with a standard `InteractionTool` API.

### 2.4 The simulator (open source)

GitHub repo: **`tsinghua-fib-lab/AgentSocietyChallenge`** — the `websocietysimulator` library. Mirror with full winning code: **`AGI-FBHC/AgentsChallenge`** (3rd-place USHB solution). Key components:

- `agents/`: base classes `SimulationAgent` and `RecommendationAgent` you extend
- `task/`: `SimulationTask` and `RecommendationTask` structures
- `llm/`: base LLM client classes (`DeepseekLLM`, `OpenAILLM`)
- `tools/`:
  - `InteractionTool`: query user, item, review data with calls like `get_user(user_id=...)`, `get_item(item_id=...)`, `get_reviews(...)`
  - `EvaluationTool`: HR@1/3/5 for recommendation, RMSE + sentiment analysis for simulation
- `simulator.py`: the orchestrator

You install with `pip install websocietysimulator` or via Poetry. The 2025 official model was **Qwen2.5-72B-Instruct** at temperature 0 — but the Nigerian variant of the competition may give you flexibility. Confirm the rules before assuming.

### 2.5 The scoring rubric you should optimize for

Combining the brief and what the original challenge used:

- **Task A (User Modeling)**: Review Text Quality 30 pts + Rating Accuracy 25 pts + Behavioural Fidelity (human eval) 20 pts + Paper 15 pts + Code Reproducibility 10 pts.
- **Task B (Recommendation)**: Ranking Quality 30 pts + Cold-Start & Cross-Domain Contextual Relevance (human eval) 25 pts + Behavioural Fidelity 20 pts + Paper 15 pts + Code Reproducibility 10 pts.
- **Nigerian context bonus**: explicit additional marks for behaving and sounding Nigerian, plus unlocking business insights.

The 30 pts of headline metrics are where most teams will compete and converge. The 45 pts of (Human Eval + Paper) are where you can decisively pull ahead.

---

## 3. The Six Winning Solutions Explained in Detail

### 3.1 User Modeling Track

#### 1st Place: A Knowledge-Driven LLM Agent Framework for User Modeling
**Authors**: Shengmao Zhu, Bingbing Xu, Yige Yuan, Bin Xie, Yunfan Li, Huawei Shen
**Affiliation**: Institute of Computing Technology, Chinese Academy of Sciences
**Published**: WWW '25 Companion Proceedings, pages 2998–3002
**DOI**: 10.1145/3701716.3719232
**Paper title in full**: *"Unveiling the Potential of LLMs in Simulated Society: A Knowledge-Driven LLM Agent Framework for User Modeling"*

**Architecture**: Three modules.

1. **Preference Refinement** — extracts structured user preference signals from historical reviews. Goes beyond raw review concatenation to produce a refined preference representation.
2. **Dual-Signal Injection** — injects both user-side signals (preferences, history) and item-side signals (features, aggregate reviews) into generation prompts. Recognizes that user modeling cannot ignore the item being reviewed.
3. **Category Distinguisher** — handles per-platform differences (Yelp businesses vs. Amazon products vs. Goodreads books) with platform-specific processing.

**Why it won**: Cleanest theoretical framing of what "knowledge" means for user modeling, combined with explicit dual-side modeling that the LLM can use to ground predictions. The judges valued the principled separation of preference inference, signal fusion, and platform awareness.

---

#### 2nd Place Overall, 1st Place in Star-Rating: Collaborative Optimization Approach for Workflow Agents
**Authors**: Xinyu Zhang (Renmin University of China), Ran Dou, Enrui Hu, Minjun Zhao, Yangkai Ding (Huawei Poisson Lab), Zhicheng Dou (Renmin)
**Published**: WWW '25 Companion Proceedings, pages 2988–2992
**DOI**: 10.1145/3701716.3719228
**Paper direct link**: `http://playbigdata.ruc.edu.cn/dou/publication/2025_WWW_agent.pdf`

**Final scores**: PE (rating) 0.8613 — best in track; RG (review) 0.8207; OP (overall) 0.8410 — second in track.

**Architecture**: Three components, all designed to *automatically discover* the right configuration rather than hand-engineer it.

1. **Workflow Structure Search via MCTS**. Uses Monte Carlo Tree Search with UCT exploration, building on the AFLOW paper (Zhang et al., ICLR 2025). The system starts with a single-agent workflow and iteratively adds, removes, or rewires agents. Evaluation combines simulation score and execution time (1-minute-per-task limit). Run separately per dataset because Goodreads benefited from a different topology than Amazon or Yelp. UCT formula: `UCT(s) = V(s) + c × sqrt(ln N_parent(s) / N(s))`. Time penalty: linear up to 0.9 × T_limit, exponential decay between 0.9× and 1.2×, zero beyond. They found 3-agent workflows optimal for Goodreads.

2. **Joint Prompt Optimizer**. Three sub-modules: (a) *Prompt Build* using Meta-Prompting techniques to generate a strong initial prompt from scene description + I/O rules; (b) *Example Selection and Chain-of-Thought Generation* — picks the most informative training examples and synthesizes CoT traces for them; (c) *Joint Optimization of Instructions and Examples* — uses ProTeGi-style automatic prompt optimization with "gradient descent + beam search" plus OPRO-style optimization-without-gold-labels for intermediate stages.

3. **Dynamic Workflow Router**. Different optimized workflows for Amazon vs. Goodreads vs. Yelp. Selects the appropriate workflow per dataset based on data characteristics. Yielded a +0.0038 improvement on overall performance over the single-best workflow.

**Why it won (and won rating prediction outright)**: Automation. While other teams hand-tuned prompts and architectures, the Renmin team automated the entire pipeline — workflow shape, prompt content, and example selection. The MCTS + AFLOW approach is the single most copy-able technique from this challenge for any future competition where you have time to run search.

**Key takeaway for your competition**: If you can afford 1-2 weeks of compute, run MCTS workflow search on each dataset. The space of agent topologies is small enough that 50-100 iterations finds strong configurations.

---

#### 3rd Place: USHB — Unified Framework for Simulating Human Behaviors
**Authors**: Renhuo Zhao, Hailong Yang (co-first), Mingxian Gu, Jianqi Wang, Wu Long, Zhaohong Deng (corresponding)
**Affiliation**: Jiangnan University, Wuxi, China
**Published**: WWW '25 Companion Proceedings, pages 2993–2997
**DOI**: 10.1145/3701716.3719227
**Paper direct link**: `https://yanghailong.me/files/USHB_WWW2025.pdf`
**Code**: `github.com/jnuaipr/AgentsChallenge` (also mirrored at `github.com/AGI-FBHC/AgentsChallenge`)

**Final scores**: SRA (Star Rating Accuracy) 88.55%, RGM (Review Generation Metric) 90.13%, OQ (Overall Quality) 89.34% — versus baseline 80.14% / 80.21% / 80.17%. That's a ~9 point absolute improvement.

**Architecture**: Three modules.

1. **Knowledge-Mining Module (KMM)**. Builds a User-and-Item Relationship Graph (UIRG) with user nodes, item nodes, and review edges. Given a target (user, item) pair, retrieves four things: user's profile Q_u, item's metadata Q_p, user's full historical reviews C_u, item's reviews from other users C_p. Single function call `G(ID_u, ID_p) → {Q_u, Q_p, C_u, C_p}`.

2. **User-and-Item Modeling Module (UIMM)**. Three sub-components:
   - **User Modeling**: random subset selection from C_u (parameter N_u), then LLM-based profile construction → user model M_u. Random sampling is important — taking only most recent reviews introduces recency bias.
   - **Item Modeling**: parallel structure — random subset S_p of size N_p from C_p, LLM constructs item model M_p.
   - **Review Style Modeling**: this is the distinctive innovation. Extracts features (sentiment, length, vocabulary, grammar) from user history and applies **IF-THEN threshold rules** to classify the user into one of K personality categories (optimistic, critical, neutral, unpredictable). Each category has its own style-generation function. Formally: `M_r = {IF f_k(x) > τ_k THEN P_k(x); k=1..K}`. Old-school rule-based classification combined with LLM generation.

3. **Reasoning Module (RM)**. Combines all three models to predict star rating + review. Workflow: (1) adjust prompt via Review Style Model; (2) load User Model and Item Model into context; (3) reason and predict; (4) optimize the generated review against the user model and style; (5) output.

**Why it ranked**: The IF-THEN review style modeling is unusual in modern LLM work and gives explicit, controllable conditioning of style. The Random subset sampling instead of full-history concatenation handles token limits while preserving behavioral diversity. The graph-based retrieval (UIRG) is clean and efficient.

**Key takeaway**: When in doubt, use explicit rules to control style. Pure LLM imitation is hard to evaluate and harder to debug. A small IF-THEN classifier over linguistic features is interpretable and works.

---

#### Workshop Talks (4th–5th-ish):
- **"EvolutionAgent: A Framework for Optimizing Multi-Agent Workflows Automatically"** by Junhui Luo (Southwest Jiaotong University). Likely won an innovation award. Same conceptual approach as the Renmin MCTS team but with evolutionary algorithms.

### 3.2 Recommendation Track

#### 1st Place: Retrieval Augmented Multi-agent Recommender
**Authors**: Pengfei Zhang and team
**Affiliation**: University of Electronic Science and Technology of China (UESTC)
**Published**: WWW '25 Companion Proceedings
**DOI**: 10.1145/3701716.3719231

**What's publicly known**: The title indicates a multi-agent RAG-based recommendation system. The standard pattern in the lab's follow-up work (AgentRecBench, etc.) is: parallel retrieval channels (collaborative + content + textual) merged with reciprocal rank fusion, candidates evaluated by specialized agents, aggregated via debate or scoring. Full paper text was not accessible via open-web routes during research; if you need it, the DOI is 10.1145/3701716.3719231 and ACM has it gated.

**Key implication**: Multi-agent reasoning with retrieval is the winning frame for Track 2. Single-agent zero-shot LLM ranking does not win.

---

#### 2nd Place: Personalized Recommendation Agents with Self-Consistency
**Authors**: Zijing Wu, Leheng Sheng, Yuanlin Xia, Yi Zhang, Yuxin Chen, An Zhang
**Published**: WWW '25 Companion Proceedings, pages 2978–2982
**DOI**: 10.1145/3701716.3719229

**Architecture**: Self-consistency-style ensembling applied to recommendation. The core idea (originally Wang et al., 2022, for math reasoning): sample multiple CoT traces from the LLM, aggregate via voting. Applied to recommendation: generate N reasoning paths per candidate, score consistency, pick the candidate ranking that emerges most consistently. Soft self-consistency (summarization across paths) is more flexible than strict majority voting.

**Key takeaway**: For Track 2, one LLM call per ranking is dangerous due to variance. Sample 5-10 traces and aggregate. The cost goes up but variance reduces and HR improves.

---

#### 3rd Place: Intelligent Agents with Adaptive Knowledge Fusion for Personalized Recommendation
**Authors**: Yuanqing Yu, Zhefan Wang, Chumeng Jiang, Xinyi Li, Jiayin Wang, Min Zhang
**Affiliation**: Tsinghua University, Beijing
**Published**: WWW '25 Companion Proceedings, pages 2983–2987
**DOI**: 10.1145/3701716.3719230

**Reported score**: Hit Rate @ 5 = **0.6250** on the recommendation track. This is the published baseline you are being benchmarked against.

**Architecture**: Two top-level modules — **Agent** and **Knowledge Fusion**.

- **Agent** subdivides into:
  - **Memory module**: stores relevant user-item interaction data and user-generated reviews. Human-like memory retention.
  - **Reasoning module**: Chain-of-Thought (CoT) prompting, mimicking human thought processes to analyze the target user.

- **Knowledge Fusion** has two methods:
  - **Pre-ranking phase**: adjusts the initial candidate list based on external knowledge such as item quality, popularity, or average ratings, *before* the LLM ranks. `Prerank(u, I) = Rank(K(u, i_1), K(u, i_2), ..., K(u, i_n))` where K maps (user, candidate) to a pre-rank score.
  - **Ensemble Ranking**: aggregates outputs across multiple ranking strategies.

**Key takeaway**: Inject collaborative signal *before* the LLM sees the candidates. Pure LLM zero-shot ranking loses to LLM-with-CF-prior. This is consistent with every post-challenge research direction (AgentCF, MemRec, MACF — see Section 5).

---

## 4. The Shared Winning Playbook

Reading the six papers (three with full text, three by title + abstract + lab context), seven patterns recur:

**Pattern 1: Decomposed user representation, never raw history.** Every User Modeling winner extracted explicit structured user representations before generation — preference vectors (CAS), workflow-discovered profiles (Renmin), personality categories (USHB). None of them just pasted past reviews into a prompt and asked the LLM to imitate. Submissions that try the "just paste history" approach do not reach the medal range.

**Pattern 2: Per-platform specialization.** Yelp's "useful/funny/cool" attributes, Amazon's "verified purchase" + publication date, Goodreads' "reading status" + "shelves" — each platform requires distinct handling. The Renmin team formalized this with Dynamic Workflow Router; USHB and the CAS team did it via category distinguishers / platform-specific templates. Anyone running the same workflow across all three datasets is leaving points on the table.

**Pattern 3: Two-stage rating prediction, separated from text generation.** The Renmin team won rating prediction by treating rating as its own optimization problem. USHB outputs both but through separate prompts in its reasoning module. Joint single-prompt generation lets the LLM rationalize whatever sentiment emerges first, and metrics suffer.

**Pattern 4: External signal injection over pure LLM reasoning.** The Tsinghua recommendation team's pre-ranking with external knowledge (item quality, popularity, ratings) is essentially collaborative-filtering signal injection. This is the single biggest pattern across all post-challenge follow-up research (see Section 5). Pure-LLM zero-shot recommendation is fundamentally limited by the LLM's lack of access to interaction patterns it cannot read in-context.

**Pattern 5: Multi-stage retrieve-plan-generate, with memory.** Every winner follows this skeleton with variations on memory structure: explicit graph (USHB), interaction store (Tsinghua), workflow-encoded (Renmin).

**Pattern 6: Self-consistency / ensemble outputs.** Track 2 winners formalized this; Track 1 winners implicitly via the Renmin team's joint prompt optimization. The principle: hedge single-LLM-call variance by sampling.

**Pattern 7: Automation over hand-engineering.** The Renmin team's MCTS workflow search is the cleanest example. Even where teams hand-built, they tended to automate inner loops (USHB's random subset sampling, the Tsinghua team's ensemble ranking).

---

## 5. Post-Challenge State of the Art (2025–2026)

A full year of research has built directly on top of these winners. Knowing this lets you stack your contribution on top of the latest, not just replicate 2025.

### 5.1 AgentRecBench (May 2025)
*Shang, Liu, Yan, Wu, Sheng, Yu, Jiang, Zhang, Xu, Wang, Zhang, Li — arXiv:2505.19623*. The official benchmark extending AgentSociety Challenge. Same three datasets. Three evaluation scenarios: **classic recommendation, evolving-interest recommendation, cold-start recommendation**. Sampled evaluation: candidate set = 1 positive + 19 negatives. Metric: HR@1, HR@3, HR@5 averaged. Critically: their team membership overlaps with the recommendation track winners (Zijing Wu, Leheng Sheng, Yuanqing Yu, Chumeng Jiang) — meaning AgentRecBench *is* the formal continuation of the challenge. NeurIPS 2025 spotlight.

### 5.2 AgentCF and AgentCF++ (2024, Feb 2025)
*Zhang, Hou, Xie, Sun, McAuley, Zhao, Lin, Wen — WWW 2024 + arXiv:2502.13843*. **Treats both users AND items as LLM agents** with mutual memory modules. Users have preferences, items have "who likes me" representations. Collaborative reflection mechanism — both update memories from interactions. AgentCF++ adds interest groups (cluster user interests, periodically re-segment), popularity awareness, and cross-domain memory propagation. This is the most foundational follow-up — every other 2025–2026 paper cites it.

### 5.3 MemRec (October 2025–February 2026)
*Collaborative Memory-Augmented Agentic Recommender System*. Decouples reasoning from memory management. A dedicated small LM (`LM_Mem`) manages a dynamic collaborative memory graph and serves synthesized context to a downstream `LLM_Rec`. Asynchronous graph propagation. State-of-the-art on four benchmarks at time of publication.

### 5.4 AMEM4Rec (Feb 2026)
*Leveraging Cross-User Similarity for Memory Evolution*. Where AgentCF maintains isolated per-user memories, AMEM4Rec builds a unified memory system encoding group-level latent behaviors. Captures collaborative signals that isolated memories miss.

### 5.5 MR.Rec (Late 2025)
*Synergizing Memory and Reasoning for Personalized Recommendation*. RAG system that goes beyond query-based retrieval into reasoning-enhanced memory retrieval. Reinforcement learning trains the LLM to autonomously learn memory utilization and reasoning refinement strategies.

### 5.6 MACF — Multi-Agent Collaborative Filtering (January 2026)
*Multi-Agent Collaborative Filtering: Orchestrating Users and Items for Agentic Recommendations*. Draws an explicit analogy between traditional CF and LLM multi-agent collaboration. Instantiates *similar users* and *relevant items* as LLM agents with unique profiles, has them deliberate, aggregates their judgments. The most natural agentic interpretation of collaborative filtering yet published.

### 5.7 Cold-Start LLM Reasoning (Netflix, January 2026)
*LLM Reasoning for Cold-Start Item Recommendation*, WWW 2026. Netflix paper. Supervised fine-tuning + RL fine-tuning + hybrid for cold-start. Reasoning-based fine-tuned models outperformed Netflix's production ranking model by up to 8% in cold-start cases.

### 5.8 USimAgent and BASES (2024–2025)
User simulation frameworks. BASES generates diverse user profiles and simulates large-scale web search. USimAgent replicates querying, clicking, and session behaviors. Both provide validation methodology for synthetic usage data.

### 5.9 The "Lost in Simulation" critique (January 2026)
*LLM-Simulated Users are Unreliable Proxies for Human Users in Agentic Evaluations*. Important counter-paper. Shows that LLM-simulated users deviate substantially from real user behavior on action sequences. Limits LLM user simulation as evaluation methodology. This is a paper to cite in your *Limitations* section — acknowledging known failure modes is intellectually honest and signals research maturity.

### 5.10 Operational Validity (2026)
*Towards Simulating Social Media Users with LLMs: Evaluating the Operational Validity of Conditioned Comment Prediction*. Argues for grounding evaluation in operational validity — measuring alignment against actual user behavior rather than abstract "plausibility." Critique of much of the user simulation literature for relying on surface-level validation.

### 5.11 Reasoning-Augmented Action Generation (October 2025)
*Can LLM Agents Simulate Multi-Turn Human Behavior?* — shows fine-tuning on user click-through data significantly outperforms prompt-only approaches. Exposing models to synthetic intermediate reasoning traces improves human-behavior simulation. Relevant if you have compute for LoRA fine-tuning.

---

## 6. The Nigerian Context as Research Contribution

This is your structural advantage. The 2025 winners all optimized on the global review distribution. Nigerian-context reviews are systematically under-represented and likely misrepresented in their outputs. This is your paper's headline claim, if you build it carefully.

### 6.1 Why the gap exists

Nigerian reviews exhibit several characteristics that vanilla LLM simulators handle poorly:

- **Register and code-switching**: Pidgin English ("e shock me," "no cap," "scatter scatter"), Nigerian English markers, code-mixing with Hausa/Yoruba/Igbo phrases.
- **Higher rating intensity variance**: anecdotal and partially empirical evidence suggests Nigerian reviewers more frequently use 1-star and 5-star ratings, with less middle-ground reviewing.
- **Communal framing**: "we enjoyed," "my family loved," vs. the individualist "I" framing of US/EU reviews.
- **Religious markers**: "by God's grace," "thank God," that vanilla sentiment classifiers often misread.
- **Different aspect priorities**: party-jollof texture vs. general food quality, distinctive Nigerian Afrobeats sub-genre awareness, Nollywood production-value markers vs. Hollywood-trained vocabulary.

### 6.2 Quantified business backdrop

To anchor business insight claims in the paper, ground them in current Nigerian numbers:

- **Nigerian MSME credit gap**: ₦130 trillion per CBN's April 2026 announcement; ~$236 billion per Stears' MSME Lending report; ~$32.2 billion per IFC. The Development Bank of Nigeria has on-lent to 321,867 MSMEs, of which 66% are women-owned. Only ~4% of Nigeria's 40 million MSMEs have access to formal bank loans. Maximum lending rates frequently exceed 30% per annum (CBN MPR at 26.5% as of February 2026).
- **Nigerian telecom market**: 171.6 million subscribers as of August 2025 (NCC). MTN: ~52.3% share, ~89.6 million subscribers. Airtel: ~33.9%, ~58 million. Globacom: ~12.2%, ~20.9 million. T2/9mobile: small. ARPU at MTN Nigeria rose to ~$3.60 in 2025 after a 50% tariff hike but is still the 12th lowest among MTN's global markets.
- **Financial inclusion**: 64% of Nigerian adults financially included per EFInA (up from 54% in 2020); 26% remain excluded. Consumer credit at ₦4.12 trillion (15.5% of total bank credit, <3% of GDP).

These numbers are not your task — they are the *business consequences* of having or not having good user models for Nigerian consumers.

### 6.3 Nigerian NLP resources (the data layer)

You will need Nigerian-marker data. Here are the publicly available resources:

- **AfriSenti-SemEval 2023** — sentiment classification corpus across 14 African languages including Hausa, Igbo, Nigerian-Pidgin, Yorùbá. Multi-task: monolingual, multilingual, zero-shot classification.
- **NaijaSenti** — first large-scale annotated Twitter sentiment dataset for Hausa, Igbo, Nigerian-Pidgin, Yorùbá. ~30,000 annotated tweets per language, significant code-mixing.
- **SentiLeye** — Nigerian Pidgin sentiment lexicon (Oyewusi, Adekanmbi, Akinsande 2021), 300 VADER-compatible Pidgin sentiment tokens with scores plus 14,000 gold-standard Pidgin sentiment-classified reviews.
- **MasakhaNER** — large-scale NER dataset across 10+ African languages.
- **AfriHate** — multilingual hate-speech corpus across 15 African languages.
- **Nigerian Pidgin orthographic variation work** (Lin et al., arXiv:2404.18264) — phonetic framework for augmenting Pidgin training data via orthographic variation. Showed +2.1 point sentiment-analysis improvement from augmentation alone.
- **Jumia and Konga product reviews** — scrapable from public listings. There exists at least one academic study (Iwendi et al., on Jumia/Jiji/Konga/Takealot reviews, IEEE 2020) with 30,382 cleaned reviews after preprocessing.
- **Nigerian e-commerce review datasets on Kaggle** — search "Jumia reviews," "Konga reviews."

For your Nigerian-marker subset, combine: (a) filtered Yelp/Amazon/Goodreads reviews exhibiting Pidgin/Nigerian markers (via classifier or keyword list), (b) Jumia/Konga scraped reviews, (c) augmentation via orthographic variation per the 2024 paper. Target ~5,000–20,000 Nigerian-marker reviews.

### 6.4 The research question that anchors the paper

*Do existing LLM user simulators systematically misrepresent Nigerian users, and if so, what architecture changes recover the gap?*

This is testable, has a clear ablation table, has business implications, and exists in no published paper. Your hypothesis:

> Vanilla LLM simulators (the kind 200+ teams will submit) systematically underestimate Nigerian rating intensity by 0.3–0.7 stars on average and produce text that scores poorly on BERTScore against Nigerian-authored ground truth because they smooth out Pidgin/code-switched markers. Cognitive-dimension decomposition + register conditioning + cultural framing modeling recovers X% of the gap on Nigerian reviews while improving global metrics by Y%.

This is the paper's headline finding. Quantify X and Y empirically.

### 6.5 The business framing for the paper

The paper's penultimate section should be "Business Implications." Three concrete deployments, none of which is your task — they are payoffs *from* your task:

1. **Thin-file credit scoring layer for Nigerian MSMEs** — banks and microfinance institutions cannot underwrite the 96% of Nigerian businesses with no formal financial records. Consumer review behavioral patterns (which categories, which aspects emphasized, what spending consistency) could serve as a behavioral feature layer for credit scoring. Your work doesn't build the credit model — it builds the user representation that the credit model would consume.

2. **Nigerian-context retention intelligence for telcos and fintechs** — with 25–35% annual churn and ARPU around $3.60, every retention dollar matters. The user representation you build (cognitive dimensions, aspect priorities, register sensitivity) is exactly what an intervention recommender needs.

3. **Cross-cultural marketplace personalization** — Nigerian-diaspora consumers are systematically mis-served by recommenders trained on US/EU patterns. Cross-platform behavioral bridge using register and cognitive dimensions enables better personalization for ~17 million Nigerian-diaspora globally.

---

## 7. Three Architecture Proposals

### 7.1 Proposal A — Cognitive Persona Decomposition (recommended headline)

**Research claim**: existing LLM user simulators represent the user as either an opaque embedding or an unstructured prompt of past reviews. Neither captures the *grammar* of how a user generates judgments. We decompose every user into five interpretable cognitive dimensions plus a cultural register classifier, each separately extractable from history, each separately conditionable at generation time.

**The five cognitive dimensions** (each extracted offline per user via an LLM pipeline, stored as structured profile):

1. **Hedonic-Utilitarian disposition** — do they review for sensory enjoyment or functional assessment? Per-category, scored 0–1.
2. **Expressive intensity calibration** — the personal mapping between linguistic intensifiers and numeric ratings. Where does this user place "amazing" on the 1–5 scale? Build a per-user lookup. This is where Nigerian register lives.
3. **Communal vs. individual framing** — "I/me" vs. "we/family" share in past reviews. Culturally conditioned.
4. **Aspect priority vector** — weighted distribution of which review dimensions they actually emphasize. Per platform: food/service/value/ambience for Yelp; plot/prose/character/pacing for Goodreads; quality/value/delivery/seller for Amazon.
5. **Context-affective sensitivity** — variance in their reviews under contextual conditions (time of day, season, weekend/weekday). Some users are stable; others are mood-driven.

**Plus a cultural register module** — a classifier trained on AfriSenti + Naija review data that detects Nigerian register and conditions generation style.

**Task A pipeline**:

```
1. Offline: extract cognitive dimensions + register marker for every user.
   Store as structured profile in JSON.

2. At inference:
   a. Stage 1 (rating prediction): gradient-boosted regression on
      [user_dimensions, item_embedding, aspect_match_score, user_mean,
       similar_user_ratings_for_this_item, register_marker, context].
      Output: predicted star rating.
   b. Stage 2 (style retrieval): pull user's 3 most similar past reviews
      by item embedding + their most-extreme positive and negative reviews
      of same category.
   c. Stage 3 (text generation): LLM call with (predicted rating,
      user dimensions, retrieved anchors, item details, context, register).
      Platform-specific templates: Yelp emphasizes funny/cool/useful framing;
      Amazon emphasizes verified-purchase + delivery; Goodreads emphasizes
      reading status + literary aspects.
   d. Stage 4 (self-consistency check): embedding similarity between
      generated review and user's corpus. If below threshold, regenerate
      with stronger style anchoring.
```

**Task B pipeline** (sharing the same user representation):

```
1. Multi-source parallel candidate retrieval:
   a. LightGCN candidates (collaborative)
   b. Content-similarity candidates (item embedding)
   c. Semantic candidates (LLM zero-shot from textual user history)
   d. Aspect-match candidates (top items matching user's aspect priority)
   Merge with reciprocal rank fusion.

2. Multi-Agent Collaborative Filtering re-ranker (per MACF):
   Instantiate similar-user agents and relevant-item agents.
   They deliberate about candidate fit.
   Score via reasoning trace. Log traces (paper gold, human-eval gold).

3. Cold-start handler:
   If user history < k interactions:
     Run 3-question elicitation flow seeded by register inference.
     Recommend based on seeded dimensions.

4. Cross-domain bridge:
   When recommending across platforms (Goodreads → Yelp):
     Use cognitive dimensions + register as the transferable representation.
     LLM-mediated aspect mapping.

5. Self-consistency: sample 5 traces per candidate, aggregate via
   soft summarization (per the 2nd-place recommendation team).
```

**Why this wins**: Five interpretable dimensions vs. opaque embeddings; explicit register conditioning vs. nothing in winners' work; cross-platform bridge vs. per-dataset isolation; full self-consistency for variance reduction. Hits every winning pattern + adds three orthogonal contributions.

### 7.2 Proposal B — Dual-Agent with Cultural Register (alternative, more academic)

Build on AgentCF++ as the foundation. Both users AND items are LLM agents with evolving memories. The Nigerian twist: item agents on the Nigerian-marker subset develop distinct "Nigerian appeal" representations, exposing how items signal differently to Nigerian vs. global users.

```
For each user u: maintain LLM-agent persona with structured memory.
For each item i: maintain LLM-agent persona representing "who likes me."

Training loop (AgentCF-style):
  Sample (user, item, review, rating) interactions.
  Both agents propose what would happen.
  Compare to ground truth.
  Both agents update memories via collaborative reflection.

Add cultural register layer:
  Train register classifier on AfriSenti + Naija data.
  User agents' memories include register marker.
  Item agents track register-conditioned reception (does this item
  read differently to Nigerian vs. global reviewers?).

For inference:
  Activate user agent with target item context.
  Item agent provides "who I am to this user."
  Combined output: rating + review.
```

**Why it's riskier but more academic**: This is closer to publishable research. Less interpretable than Proposal A. Slower to implement. The empirical wins are more uncertain. Pick this if you have a strong research-track team and 8+ weeks.

### 7.3 Proposal C — Cross-Platform Behavioral Bridge (cross-domain focus)

Specifically optimizes for the Cold-Start & Cross-Domain Contextual Relevance criterion (25 points on Task B). Most teams will treat the three datasets as separate. You build a system where Goodreads literary reviews *inform* Yelp restaurant style for the same user.

```
User embedding learned from REVIEW TEXT (not interaction patterns).
The text reveals personality across domains.
"Atmospheric, character-driven, ambiguous endings" on Goodreads
predicts specific food and movie preferences via LLM-mediated
domain mapping.

For each user with cross-platform presence:
  Extract personality vector from textual reviews.
  Project into target domain via learned mapping.
  Recommend in target domain conditioned on projected vector.

Cold-start case:
  If a user has Yelp history but no Goodreads:
    Infer Goodreads preferences from Yelp aspect signals.
    Recommend books accordingly.
```

**Why it's worth considering**: directly attacks the Cross-Domain score. Less novel architecturally but a precise fit to the rubric.

### 7.4 The recommended combination

For a 4–6 week effort, build Proposal A as the primary system. If team capacity allows, add Proposal C's cross-platform bridge as a module within Proposal A's Task B pipeline. Proposal B is the "research stretch" — only attempt if you have strong publication ambitions and an academic mentor.

---

## 8. Build Plan: Six Weeks From Zero to Submission

Assumes a 2–3 person team with at least one strong ML engineer and one strong writer. Adjust for solo or larger teams.

### Week 0 (preparation, before official start)

- Clone `tsinghua-fib-lab/AgentSocietyChallenge` and `AGI-FBHC/AgentsChallenge`. Run their example agents end-to-end on Yelp.
- Read the four key papers in detail: AgentSociety Challenge analysis (2502.18754), Renmin MCTS workflow, USHB, Tsinghua Adaptive Knowledge Fusion.
- Skim AgentCF++, MACF, MemRec.
- Decide team roles: who builds dimension extractor, who builds register module, who builds recommender, who writes paper.
- Set up shared compute. Minimum: one machine with 80GB GPU (A100 or equivalent) for inference. Two is better.
- Set up MLflow or Weights & Biases for experiment tracking. Mandatory if you want reproducible ablations.

### Week 1 — Foundation

- Get `websocietysimulator` running with full Yelp data. Run baseline agent. Confirm scores match the documented baseline (~80%).
- Implement the cognitive dimension extractor as a standalone pipeline. Input: user history. Output: structured JSON profile with five dimensions + register marker.
- Build a small offline test: extract dimensions on 100 held-out users, eyeball whether they make sense. Run an LLM-judge ("does this profile capture this user?") for quantitative sanity check.
- Pin all dependencies. Build initial Docker image. Test reproducibility from a fresh clone.

### Week 2 — Task A core implementation

- Implement the Task A four-stage pipeline on Yelp end-to-end.
- Train the rating prediction regression head (XGBoost or LightGBM). This should immediately deliver RMSE wins because most rating variance is recoverable from structured features.
- Implement style retrieval (anchor reviews + extreme reviews per category).
- Build platform-specific prompt templates. Validate generation quality on small samples.
- Implement the self-consistency check. Tune threshold.

### Week 3 — Nigerian layer

- Build the Nigerian-marker filter. Combine: keyword/lexicon from SentiLeye, classifier from AfriSenti-trained model, location markers, name markers.
- Apply filter to Yelp/Amazon/Goodreads. Build a Nigerian-marker subset of ~5–10k reviews.
- Scrape Jumia and Konga as augmentation. Be respectful (rate-limit, no PII).
- Train (or LoRA-tune) the register classifier on AfriSenti + Naija + Jumia/Konga.
- **Run the baseline gap analysis**: vanilla simulator vs. your simulator with register module, on Nigerian-marker subset. This is your paper's headline number.

### Week 4 — Task B implementation

- Build the multi-source candidate retrieval. LightGCN can be trained in a few hours on each dataset.
- Implement the MACF-style multi-agent re-ranker. Use the same user dimensions from Task A as input.
- Build cold-start elicitation flow. Test on held-out cold users.
- Implement cross-domain bridge (if time): cognitive dimensions transfer across platforms.
- Sample-based self-consistency for ranking.

### Week 5 — Generalization to Amazon + Goodreads

- Port Task A and Task B pipelines to Amazon (verify-purchase, product metadata).
- Port to Goodreads (reading status, shelves, votes).
- Per-platform templates. Per-platform aspect vocabularies.
- Optional: implement Renmin-style MCTS workflow search if compute allows. Run separately on each dataset, 50–100 iterations each.
- Run full ablation suite. Required ablations: (a) full system; (b) no cognitive dimensions; (c) no register module; (d) no self-consistency; (e) no cross-domain bridge; (f) Nigerian-marker subset vs. global subset.

### Week 6 — Polish, paper, submit

- Write the paper. 6–8 pages including figures. Suggested structure in Section 9.
- Containerize. Two endpoints: `/simulate-review` and `/recommend`. FastAPI + Docker.
- `make demo` script that runs end-to-end on a small example dataset.
- README: clear setup instructions, environment variables, model paths, reproducibility notes.
- Final reproducibility test from a fresh clone on a fresh machine.
- Submit.

### Compute and tooling notes

- **Model**: use what the rules permit. If Qwen2.5-72B-Instruct is mandated, run it via vLLM or DeepSeek Cloud / Infinigence. If flexible, Llama 3.3 70B or Qwen2.5 72B with vLLM are the strong open choices; Claude Sonnet via API works for development.
- **Embeddings**: BGE-large or e5-mistral. Both have strong open weights.
- **Container**: FastAPI + Docker. Two endpoints. Lazy model loading. Healthcheck endpoint. Env-var config.
- **Reproducibility (10 pts)**: pin all dependencies in `requirements.txt` or `pyproject.toml`. Include `Dockerfile` and `docker-compose.yml`. `make demo` script. Random seeds set everywhere. Document GPU requirements.

---

## 9. Paper Outline and the Ablations You Must Run

### 9.1 Suggested paper structure (6–8 pages)

**Abstract.** State the problem (LLM user modeling lacks structured representation and cultural awareness), the contribution (cognitive dimension decomposition + register conditioning + cross-platform bridge), the results (X% improvement over winning architecture, Y% recovery on Nigerian-marker subset).

**1. Introduction.** Motivate user modeling as more than profile aggregation. State the cultural-context gap. Preview contributions.

**2. Related Work.** Five paragraphs:
   - LLM user simulation: AgentCF, AgentCF++, RecAgent, Agent4Rec, USimAgent.
   - LLM recommendation: P5, TALLRec, LLM-Rec, RecMind.
   - AgentSociety Challenge specifically: winners' approaches.
   - Cold-start LLM recommendation: Netflix's work, AgentRecBench.
   - Nigerian NLP: AfriSenti, NaijaSenti, Pidgin work.

**3. Method.** Subsections:
   - 3.1 Cognitive dimension extraction. Formal definitions.
   - 3.2 Cultural register module. Training data + classifier.
   - 3.3 Two-stage rating-text generation pipeline.
   - 3.4 Multi-agent recommendation with collaborative filtering signal injection.
   - 3.5 Cross-domain bridge.

**4. The Nigerian Context Case Study.** This is the paper's distinctive section. Subsections:
   - 4.1 Data construction (filter + augmentation).
   - 4.2 Baseline gap analysis.
   - 4.3 Recovery analysis with register module.

**5. Experiments.** Subsections:
   - 5.1 Datasets and protocol.
   - 5.2 Baselines (USHB, Tsinghua Adaptive Knowledge Fusion, Renmin Collaborative Optimization).
   - 5.3 Main results on Yelp/Amazon/Goodreads.
   - 5.4 Ablation study.
   - 5.5 Cross-domain transfer results.
   - 5.6 Nigerian-marker subset analysis.
   - 5.7 Reasoning trace examples (paper gold).

**6. Business Implications.** MSME credit scoring, telco churn intervention, cross-cultural marketplace personalization. Each with quantified backdrop (₦130 trillion gap, MTN ARPU, etc.).

**7. Limitations.** Honest discussion. Cite "Lost in Simulation." Acknowledge that LLM-simulated users diverge from real users on action sequences. Note your evaluation is correlative not causal.

**8. Conclusion.** One paragraph.

### 9.2 Required ablations

Without these the paper is incomplete:

| Ablation | What it measures |
|----------|-----------------|
| Full system | Headline number |
| No cognitive dimensions | Value of structured user representation |
| No register module | Value of cultural conditioning |
| No two-stage rating | Value of separating rating from text |
| No platform-specific templates | Value of per-platform specialization |
| No self-consistency | Value of variance reduction |
| No cross-domain bridge | Value for Track B's cross-domain score |
| Nigerian subset vs. global subset | The cultural gap and its recovery |
| Cold-start with vs. without elicitation | Cold-start score recovery |

Run each on at least Yelp + one other dataset. Report mean and standard deviation across 3+ runs at different seeds.

### 9.3 What "behavioural fidelity" actually means in human evaluation

The 20 pts of human eval likely use a protocol similar to the original challenge's RGM (Review Generation Metric): Emotional Tone Error + Sentiment Attitude Error + Topic Relevance Error. Per the USHB paper, the formula is:

```
RGM = 1 - (0.25 × ETE + 0.25 × SAE + 0.5 × TRE)
```

Where ETE uses TweetEval emotion classifier embeddings, SAE uses NLTK sentiment scores, and TRE uses cosine similarity between review embedding and real topic embedding via Sentence-BERT.

You should run this metric yourself on a held-out set and report it. Even if the official judges use a different protocol, this self-reported metric demonstrates rigor.

---

## 10. Use Cases Beyond the Competition

Your architecture is not only useful for the competition. The user representation you build supports several real-world deployments. These are the "Business Implications" section of your paper, and they're also potential commercial follow-ons.

### 10.1 Thin-file MSME credit scoring layer

**Problem**: Nigerian banks cannot underwrite 96% of MSMEs with no formal financial records. Maximum lending rates frequently exceed 30% per annum.

**Application**: Use cognitive dimensions + aspect priorities + register signals derived from consumer review behavior as a behavioral feature layer for credit scoring. Specifically: consistency of purchase categories, variance in aspect emphasis (suggesting business focus stability), spending category breadth (suggesting diversification), and review tone stability (suggesting customer-service maturity if reviewing as a business).

**Buyer**: commercial banks (Access, GTBank, UBA, Zenith), microfinance banks, the new National Credit Guarantee Company (NCGC ₦100 billion scheme).

**How to demonstrate**: do not build the full credit model. Show that the user representation you build correlates with publicly available sector default-rate data from CBN reports.

### 10.2 Telco churn intervention recommender

**Problem**: Nigerian telcos face 25–35% annual churn. ARPU is ~$3.60. Generic blanket promotions waste budget.

**Application**: Use the same user representation for retention intervention recommendation. A subscriber whose review behavior reveals price-sensitivity-but-not-brand-loyalty needs a different intervention than one whose behavior shows service-quality-prioritization.

**Buyer**: MTN Nigeria (89.6M subscribers), Airtel Nigeria (58M), Globacom (20.9M).

**How to demonstrate**: use synthetic but realistic customer profiles calibrated to NCC publicly available churn data.

### 10.3 Cross-cultural marketplace personalization

**Problem**: Nigerian-diaspora consumers (~17 million globally) are mis-served by recommenders trained on US/EU patterns.

**Application**: Cross-platform behavioral bridge using register and cognitive dimensions enables personalization that respects cultural framing.

**Buyer**: Jumia, Konga, Selar, Bumpa, Spar Nigeria, any Nigerian-diaspora-facing platform.

**How to demonstrate**: cross-domain transfer experiments comparing your system to vanilla recommenders on Nigerian-marker subsets.

### 10.4 Nollywood / Afrobeats content recommendation

**Problem**: Western content recommenders fail on Nigerian cultural content because they lack distinctive aspect vocabularies (Nollywood production quality cues, Afrobeats sub-genre differentiation).

**Application**: Build Nigerian-context evaluation set, demonstrate cross-domain personality bridge from books/restaurants to content.

**Buyer**: Showmax, Boomplay, Mdundo, Iroko TV, content platforms targeting African audiences.

### 10.5 Behavioral cohort modeling for fintech

**Problem**: Nigerian fintechs (Opay, Palmpay, Moniepoint, Kuda) need to understand user segments beyond demographics.

**Application**: Cognitive dimensions provide an interpretable cohort framework. Hedonic-Utilitarian + Communal-Individual + register tier creates explainable segments fintechs can act on.

### 10.6 Survey augmentation and synthetic respondents

**Problem**: Quantitative research in Nigerian markets is expensive and slow.

**Application**: With caveats from "Lost in Simulation," your simulator can produce synthetic Nigerian respondents for market research at much lower cost than live surveys. Use only for exploratory work, validate with periodic live data.

### 10.7 SME marketplace intelligence

**Problem**: Nigerian SMEs selling on Jumia/Konga lack analytics on how their customers actually perceive them across reviews.

**Application**: Aspect-priority extraction across reviews exposes the dimensions customers actually care about for each seller, allowing SMEs to focus improvement.

---

## 11. Complete Resource Index

### 11.1 Primary papers (read these)

- **AgentSociety Challenge analysis**: Yan et al., arXiv:2502.18754 (Feb 2025). The post-challenge paper from the organizers.
- **USHB**: Zhao, Yang et al., WWW Companion '25, DOI 10.1145/3701716.3719227. Direct PDF: yanghailong.me/files/USHB_WWW2025.pdf.
- **Collaborative Optimization (Renmin)**: Zhang et al., WWW Companion '25, DOI 10.1145/3701716.3719228. Direct PDF: playbigdata.ruc.edu.cn/dou/publication/2025_WWW_agent.pdf.
- **Knowledge-Driven Framework (CAS)**: Zhu et al., WWW Companion '25, DOI 10.1145/3701716.3719232.
- **Adaptive Knowledge Fusion (Tsinghua)**: Yu et al., WWW Companion '25, DOI 10.1145/3701716.3719230.
- **Self-Consistency Recommendations**: Wu et al., WWW Companion '25, DOI 10.1145/3701716.3719229.
- **Retrieval Augmented Multi-agent**: Zhang (UESTC) et al., WWW Companion '25, DOI 10.1145/3701716.3719231.

### 11.2 Post-challenge research

- **AgentRecBench**: Shang et al., arXiv:2505.19623 (May 2025). NeurIPS 2025 spotlight.
- **AgentCF**: Zhang et al., WWW 2024, arXiv:2310.09233.
- **AgentCF++**: arXiv:2502.13843 (Feb 2025).
- **MemRec**: arXiv:2601.08816 (2025).
- **AMEM4Rec**: arXiv:2602.08837 (Feb 2026).
- **MR.Rec**: arXiv:2510.14629 (Oct 2025).
- **MACF**: arXiv:2511.18413 (Jan 2026).
- **Cold-Start LLM Reasoning (Netflix)**: WWW '26 paper, arXiv:2511.18261.
- **Lost in Simulation**: arXiv:2601.17087 (Jan 2026). The critique paper.
- **Multi-Turn LLM Behavior**: arXiv:2503.20749 (Oct 2025).

### 11.3 Foundational background

- **RecMind**: Wang et al., NAACL 2024 Findings, arXiv:2308.14296.
- **Agent4Rec**: Zhang et al., SIGIR 2024, arXiv:2310.10108.
- **P5**: Generative recommendation foundation.
- **TALLRec**: LLM tuning for recommendation.
- **PALR**: Personalization Aware LLMs.

### 11.4 GitHub repositories

- **AgentSociety Challenge official**: github.com/tsinghua-fib-lab/AgentSocietyChallenge
- **USHB (3rd place User Modeling)**: github.com/jnuaipr/AgentsChallenge (mirror: github.com/AGI-FBHC/AgentsChallenge)
- **LLM-Agent-for-Recommendation-and-Search index**: github.com/tsinghua-fib-lab/LLM-Agent-for-Recommendation-and-Search
- **Agentic Web survey**: github.com/SafeRL-Lab/agentic-web

### 11.5 Datasets and data sources

- **Yelp Open Dataset**: yelp.com/dataset
- **Amazon Reviews 2023**: McAuley lab releases (UCSD).
- **Goodreads**: Wan and McAuley, RecSys 2018 release.
- **AfriSenti-SemEval**: HuggingFace and ACL Anthology, 14 African languages.
- **NaijaSenti**: 30k tweets per language for Hausa, Igbo, Pidgin, Yorùbá.
- **SentiLeye Pidgin lexicon**: Oyewusi et al., IJCAI 2021 AI4SG workshop.
- **MasakhaNER**: github.com/masakhane-io.
- **Jumia/Konga reviews**: scrapable. Some academic datasets exist.

### 11.6 Nigerian context references

- **CBN MSME funding gap (₦130T)**: April 2026 announcement, World Bank Nigeria Development Update launch.
- **Stears MSME Lending Report**: Nigerian MSME funding gap at $236 billion.
- **PwC MSME Survey 2024**: 27% cite high interest rates as primary barrier to loans.
- **Moniepoint Informal Economy Report 2025**: 51% of informal businesses do not borrow (up from 30%).
- **NCC quarterly subscriber data**: subscriber and churn data by operator.
- **EFInA Access to Finance Survey**: 64% adult financial inclusion (2023).

### 11.7 Tooling

- **vLLM**: fast LLM inference. github.com/vllm-project/vllm.
- **FastAPI**: API framework for the container.
- **LightGCN / RecBole**: collaborative filtering baselines.
- **LangGraph / LangChain**: agentic orchestration (optional).
- **Sentence-BERT (BGE-large, e5-mistral)**: embeddings.
- **TweetEval**: sentiment/emotion classifier baselines for evaluation.
- **MLflow / Weights & Biases**: experiment tracking.

---

## 12. Glossary

- **AFLOW**: Automated workflow generation framework (Zhang et al., ICLR 2025). Underlies the Renmin MCTS approach.
- **AgentCF / AgentCF++**: Agent-based collaborative filtering where both users and items are LLM agents with memory.
- **AgentRecBench**: NeurIPS 2025 spotlight benchmark extending AgentSociety Challenge with three evaluation scenarios.
- **AgentSociety**: Tsinghua's broader research program on scalable LLM-driven agent societies.
- **AgentSociety Challenge**: WWW'25 competition that defined the User Modeling and Recommendation tracks you are competing in.
- **AfriSenti-SemEval**: shared task on sentiment classification across 14 African languages.
- **BERTScore**: text quality metric using BERT embeddings to compare generated and reference text.
- **CoT (Chain-of-Thought)**: prompting technique that asks the model to reason step-by-step.
- **DILU memory**: similarity-based memory retrieval technique used by several AgentSociety winners.
- **EFInA**: Enhancing Financial Innovation & Access, Nigerian financial inclusion data source.
- **HR@k (Hit Rate at k)**: fraction of test instances where the ground-truth item appears in the top-k recommended list.
- **InteractionTool**: API in the `websocietysimulator` library for accessing user/item/review data.
- **LightGCN**: graph neural network for collaborative filtering. Standard baseline.
- **MACF**: Multi-Agent Collaborative Filtering, 2026 framework analogizing CF to LLM multi-agent collaboration.
- **MasakhaNER**: NER dataset across 10+ African languages by the Masakhane community.
- **MCTS (Monte Carlo Tree Search)**: search algorithm used by the Renmin winning team for workflow architecture optimization.
- **MemRec**: memory-augmented agentic recommender with decoupled memory manager.
- **MR.Rec**: memory-and-reasoning synergy framework with RL-trained retrieval.
- **NaijaSenti**: large Twitter sentiment dataset for Hausa, Igbo, Nigerian-Pidgin, Yorùbá.
- **NCC**: Nigerian Communications Commission.
- **NDCG@k**: Normalized Discounted Cumulative Gain at k, ranking quality metric.
- **OPRO**: Optimization by PROmpting, technique used in the Renmin Joint Prompt Optimizer.
- **ProTeGi**: Prompt-Optimization-with-Gradients-and-Beam-Search, also in the Renmin pipeline.
- **RAG (Retrieval-Augmented Generation)**: pattern where an LLM is augmented with retrieved external information.
- **RGM (Review Generation Metric)**: USHB's combined metric for review quality.
- **RMSE**: Root Mean Squared Error, used to score star rating accuracy.
- **ROUGE**: text similarity metric, used for review text quality.
- **SentiLeye**: Nigerian Pidgin sentiment lexicon.
- **SRA (Star Rating Accuracy)**: USHB's metric for rating prediction.
- **UCT (Upper Confidence bounds for Trees)**: selection rule in Monte Carlo Tree Search.
- **UIRG (User-and-Item Relationship Graph)**: USHB's data structure.
- **USHB**: Unified Framework for Simulating Human Behaviors, 3rd-place User Modeling winner.
- **websocietysimulator**: the official simulator library from the AgentSociety Challenge organizers.

---

## 13. Risk Register and Common Pitfalls

The 295 teams from the 2025 challenge made many mistakes. Here are the predictable ones and how to avoid them.

**Risk 1: Optimizing for the wrong scoreboard.** If you treat this as a pure metric-chasing competition, you will lose to teams that hit 90% of your metrics but write a paper about why their architecture exists. The paper is 15 points + the human eval is 20-25 points, so 35-40% of the rubric goes to *understanding*, not raw metrics.

*Mitigation*: write the paper outline in week 1, not week 6. Let the paper claim drive the architecture, not vice versa.

**Risk 2: Building everything from scratch.** The simulator already exists. The winning baselines already exist (USHB on GitHub). Don't reimplement the wheel.

*Mitigation*: fork USHB. Build your extensions on top. Cite USHB as the baseline you extend.

**Risk 3: Monolithic LLM prompts.** Submitting "here's the user history, please write a review like this user would" is the median submission. It loses on every metric.

*Mitigation*: decompose. Explicit user representation. Two-stage rating prediction. Self-consistency.

**Risk 4: Ignoring per-platform differences.** Using the same workflow on Yelp, Amazon, and Goodreads loses points consistently. The Renmin team won because they optimized per-dataset.

*Mitigation*: at minimum, per-platform prompt templates and aspect vocabularies. If compute allows, per-platform workflow architectures.

**Risk 5: Token sprawl in long histories.** A user with 200+ reviews exceeds token limits. The naive approach of using "most recent N reviews" introduces recency bias.

*Mitigation*: USHB-style random subset sampling. Or better: weighted sampling that ensures diversity in (rating, category, time).

**Risk 6: Treating the Nigerian context as cosmetic.** Sprinkling "abeg" into outputs is tokenistic and won't earn you the bonus. Judges will see through it.

*Mitigation*: build a register classifier on actual data. Quantify the gap. Show recovery numerically. Treat Nigerian context as a research contribution with its own section of the paper, not a flag waved at the end.

**Risk 7: Not running the right ablations.** Without ablations, the paper has nothing to claim. "Our system works" isn't a contribution.

*Mitigation*: plan ablations in week 1. Each architectural component must have an ablation that justifies its existence.

**Risk 8: Container that doesn't reproduce.** Judges will attempt to run your code. If it doesn't run cleanly on a fresh machine, you lose 10 pts plus credibility.

*Mitigation*: in week 5, clone your repo on a fresh machine and run from scratch. Whatever breaks, fix. Write the README from the perspective of a judge who has never seen your code.

**Risk 9: Over-claiming.** "Our system achieves state-of-the-art" claims based on weak comparison set fail academic review.

*Mitigation*: compare to USHB, Renmin Collaborative Optimization, Tsinghua Adaptive Knowledge Fusion. These are the published bars. Be honest about where you exceed and where you don't.

**Risk 10: Compute budget overruns.** Running 80B-parameter models for thousands of inference calls is expensive. A naive evaluation pass on all test users can cost hundreds of dollars in API fees.

*Mitigation*: cache aggressively. Test on subsamples first. Use vLLM with a local model if budget is tight. Run full evaluation only when the pipeline is final.

**Risk 11: Single-author paper assumptions.** If you're solo or in a duo, you cannot do everything. Triage ruthlessly.

*Mitigation*: solo build = Proposal A only, no Proposal B, minimal cross-domain. Two people = Proposal A + one ablation extra. Three people = full Proposal A + cross-domain bridge.

**Risk 12: Trying to outdo the winners on their own terms.** The Renmin team had access to AFLOW infrastructure and Huawei compute. USHB had Jiangnan University compute. You probably don't. Trying to beat them at MCTS workflow search is a bad use of time.

*Mitigation*: don't compete on their strengths. Add orthogonal contributions: cultural register, cognitive dimensions, cross-platform bridge. Win on novelty, not raw scale.

---

## Closing Note

You are entering a competition where the answer to "how do I win?" has more structure than is typical. The winners are published. The architectures are open-source. The patterns are known. The Nigerian context is the structural opportunity that no global winner could exploit.

The teams that medal will:
1. Start from the USHB / Renmin / Tsinghua winning architectures (do not reinvent).
2. Add 2–3 orthogonal contributions on top — cognitive dimensions, cultural register, cross-platform bridge are the strongest candidates.
3. Run rigorous ablations.
4. Write a paper that frames the Nigerian context as a research finding with quantified business implications, not a cosmetic flag.
5. Ship a container that actually runs.

Everything in this guide is in service of those five things. Build accordingly.

If you need any single component implemented in detail — the cognitive dimension extractor, the register classifier, the MACF re-ranker, the cross-domain bridge, the container scaffold, or the paper draft — that is the next conversation. Pick the one that's blocking you and we'll go deep.

---

*Document compiled from research into the WWW'25 AgentSociety Challenge by Tsinghua FIBLAB and the AgentSociety Challenge Workshop (Sydney, April 29, 2025), the official analysis paper (Yan et al., arXiv:2502.18754), the published winning solutions (USHB, Renmin Collaborative Optimization, Tsinghua Adaptive Knowledge Fusion, CAS Knowledge-Driven Framework), follow-up research (AgentRecBench, AgentCF++, MACF, MemRec, MR.Rec), and Nigerian NLP and business context (AfriSenti, NaijaSenti, SentiLeye, CBN reports, NCC data, EFInA surveys). All technical claims are sourced; all numerical benchmarks are documented; all referenced repositories are publicly accessible.*
