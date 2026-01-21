# Summary

This paper introduces TRACE, a toolchain for recording expert demonstrations on real websites and transforming them into deterministic, offline-replayable browser environments. The system comprises an instrumented Playwright-based collector, a post-processing pipeline that extracts high-level actions, redacts credentials, and inserts semantic checkpoints, and a replay engine that serves captured network/DOM state to enable reproducible agent evaluation. The authors release a small demo dataset of six captured tasks and an example evaluation harness to illustrate how agents can be assessed using TRACE environments.

---

# Strengths

## Technical Novelty and Innovation

- Proposes a pragmatic "capture-to-replay" pipeline on live websites, turning single expert sessions into shareable, reproducible environments—complementary to replica-based suites like REAL and WebArena.
- Adds practical engineering features beyond standard HAR replay: character-based URL matching and an LM-based tie-breaker for dynamic parameters; DSL conversion of low-level events into high-level tool calls; automated credential extraction; heuristic ignore lists for stability.
- Introduces minimal checkpoint-based evaluation and parsing of human demonstration into a standardized action DSL, which could support denser feedback and RL.

## Experimental Rigor and Validation

- Provides end-to-end artifacts (collector, post-processing scripts, replayer, demo dataset, example evaluation runner) that can be used by the community.
- Demonstrates feasibility across multiple real websites (GitHub, Amazon, Airbnb, Kayak, Uniqlo, Ultimate Guitar), including credentialed flows.

## Clarity of Presentation

- The high-level system description is clear, with a logical breakdown of collection → post-processing → replay → example evaluation.
- The paper positions TRACE relative to a broad benchmark ecosystem and articulates the motivation (cost/fragility of building/maintaining environments).

## Significance of Contributions

- Addresses a recognized bottleneck: scalable, reproducible environments for browser agents without handcrafting full replicas.
- If matured, could democratize environment creation and accelerate research on training/evaluating web/computer-use agents, complementing prior benchmarks and commercial platforms.

---

# Weaknesses

## Technical Limitations or Concerns

- Offline replay feasibility appears tightly coupled to the recorded trajectory: deviations or exploration by agents may lead to missing network entries and failure to match requests, limiting generalization within the environment.
- The LM-based URL matching and checkpoint selection are described but not rigorously evaluated (accuracy, determinism, or failure modes).
- Limited discussion of challenging web features (WebSockets/SSE, service workers, IndexedDB, cross-origin iframes, streaming media, CSRF tokens, CAPTCHAs/anti-bot measures) and how replay handles them.

## Experimental Gaps or Methodological Issues

- No quantitative study of replay fidelity, determinism, or robustness across sites and sessions (e.g., success rate of full replays, sensitivity to time drift, rate of unmatched requests).
- No evaluation of how much agent deviation from the human path the replay can tolerate, nor measurements of coverage breadth (e.g., fraction of requests filtered vs. required).
- The dataset is very small (six tasks), with no baselines demonstrating training/evaluation benefits versus existing benchmarks.
- No ablation quantifying the contribution of the character-based/LM-based matching, ignore-list construction, or checkpointing.

## Clarity or Presentation Issues

- Some duplication and formatting artifacts (e.g., repeated lines in the abstract, figure references/tables with rendering noise) slightly impede readability.
- Implementation details of critical components (e.g., exact matching heuristics, cache semantics, checkpoint LM prompts and consistency) are high-level and would benefit from more specifics.

## Missing Related Work or Comparisons

- While the paper covers many benchmarks, it lacks a deeper technical comparison to network/DOM interception/replay approaches in browser automation tooling and does not benchmark against replica-based environments (e.g., REAL, WebArena) on replay stability and agent tolerance to exploration.
- Safety/ethics/legal considerations are underdeveloped (e.g., redistribution rights for captured site content, handling of PII and credentials beyond extraction, ToS compliance).

---

# Detailed Comments

## Technical Soundness Evaluation

The core idea—freezing live sessions into replayable bundles—is sensible and timely. However, the approach is inherently constrained by coverage: if an agent issues a request not recorded in the HAR (due to a different click path or dynamic parameterization), the replay may fail or fall back to heuristic matching. The paper does not quantify how often this occurs or how well heuristics recover.

Converting low-level events to a higher-level action DSL and extracting credentials/checkpoints is well-motivated, but details on robustness are scarce (e.g., detecting credential forms across varied DOM structures, false positives/negatives in credential extraction).

The LM-based tie-breaker for network matching is a clever hack but introduces non-determinism risk unless carefully cached; the paper states caching exists, but provides no measurements of determinism under repeated runs.

## Experimental Evaluation Assessment

The results section catalogs the six environments and their statistics but does not evaluate:

- Replay determinism (e.g., success rates over N replays, byte-level diffs).
- Deviation tolerance (how far an agent can depart from the human path before replay breaks).
- Stability under disabled internet and time shifts (e.g., clock skew) or site antifraud behaviors.
- Utility for training/evaluation (e.g., do TRACE environments help RL or imitation learning compared to replicas like REAL?).

An example evaluation runner exists, but there is no benchmarking against baselines or related environments (e.g., REAL, WebArena). Without this, it is hard to assess TRACE's value beyond proof of concept.

## Comparison with Related Work

**WebArena and REAL** engineer deterministic environments via replicas and programmatic validators, achieving strong reproducibility and enabling structured evaluation; TRACE offers a lower-cost, higher-scalability pathway by capturing real sites, but loses the breadth of valid behaviors and generalization within an environment unless coverage is addressed. A head-to-head comparison on reproducibility and agent performance would be informative.

**OSWorld, AndroidWorld, and OS‑MAP** emphasize full-computer environments and structured, verifiable evaluation. TRACE focuses on the browser but could bridge toward OS-level capture; comparing TRACE's ability to support dense reward signals and robust evaluation to OSWorld/OS‑MAP would clarify strengths/limits.

**Surfer 2 and AutoGLM** present strong agent architectures; TRACE complements them by potentially supplying realistic, replayable environments. Demonstrating that agents like these can be evaluated or trained on TRACE environments would strengthen the paper.

**COMPUTERRL** highlights production-grade RL infrastructure and verifiable reward design; TRACE could provide the environments, but the paper currently does not show any RL experiments or verifiable reward integration.

**SafeArena** underscores safety risks; TRACE's ability to capture and redistribute real website content raises legal/ethical concerns that need careful treatment and tooling support (e.g., redaction, permissioning).

## Discussion of Broader Impact and Significance

**Positive:** TRACE could democratize access to realistic environments that are otherwise expensive and proprietary, enabling reproducible experiments and potentially fueling RL/finetuning on real-world flows.

**Risks:** Legal/ToS/copyright issues when redistributing captured pages and assets; handling of personal data and secrets; potential to facilitate harmful-agent training unless datasets include safety constraints. The paper should include an explicit ethical guidelines section and tooling to enforce safe sharing.

For ICML's Datasets/Benchmarks audience, the current scale (six tasks) and absence of rigorous evaluation limit immediate impact, but the direction is promising if expanded and validated.

---

# Questions for Authors

1. How robust is offline replay to agent deviations from the human trajectory? Do you have quantitative results showing success rates as a function of deviation (e.g., altered click path, different filter orders) and the fraction of unmatched requests?

2. Which dynamic web features are supported in replay (WebSockets/SSE, service workers, IndexedDB, cross-origin iframes, streaming video/audio)? What are the known unsupported cases and their observed frequency in the wild?

3. How deterministic is the LM-based URL matching and checkpoint selection across replays and machines? Can you provide reproducibility metrics (e.g., variance across 100 runs, cache hit rates, tie-break frequency)?

4. Can you compare TRACE's replay fidelity and agent success to replica-based environments like REAL/WebArena on a common task set? What are the trade-offs in coverage and agent exploration latitude?

5. What is your policy and tooling around legal/ethical data sharing (copyright of captured content, site ToS, PII handling, and credential safety)? How do you ensure that shared bundles are safe and compliant?

6. Do you have plans or preliminary results for using TRACE environments to train agents (imitation or RL) and quantifying benefits over existing benchmarks?

7. How does ignore-list construction generalize across sites and time? Are ignore lists static per site, inferred per session, or reusable across captures?

---

# Overall Assessment

TRACE addresses an important bottleneck by proposing an open-source, practical pipeline to convert live web demonstrations into deterministic, offline-replayable environments. Conceptually and engineering-wise, this is a useful and timely contribution that could broaden access to realistic tasks beyond proprietary platforms and handcrafted replicas.

However, the current paper falls short of ICML standards in empirical validation and scale. The dataset is tiny (six tasks), and there is no rigorous evaluation of replay fidelity, determinism, deviation tolerance, or utility for training/evaluation compared to established environments like REAL and WebArena. Critical components (LM-based matching, checkpointing, credential handling) are described but untested in ablations. Safety/legal/ethical considerations are not adequately discussed given the redistribution of captured content and sensitive flows.

I see promise in the idea and would encourage a resubmission with a substantially expanded dataset, thorough reproducibility and robustness studies, head-to-head comparisons, and clear ethical guidelines. **As it stands, I recommend rejection**, with the hope that the authors build on this solid foundation to deliver a more complete and empirically grounded contribution.
