Part C — Decision memo under the actual constraints

Constraints
- One A100-80GB, 2 weeks calendar, one reviewer who is native in Hindi and Kannada, 10 h/week, launch review in 3 weeks, no external API budget.
- Goal: improve casualness in Hindi/Kannada first; Tamil/Telugu/Bengali/Marathi remain out of scope for launch-level quality until native review exists.

Comparison

(a) SFT
- Pros: strongest long-term quality if we can produce enough reviewed data.
- Cost: full supervised fine-tuning is data-bound, not compute-bound. To generalize on style and tone, we need thousands of reviewed high-quality examples, not just a few hundred. With one reviewer working 10 h/week for 2 weeks, the review budget is roughly 20 hours total; at a conservative 30–50 examples/hour, that is about 600–1000 reviewed examples, not enough for a robust SFT dataset unless the reviewer is rewriting at a very high-throughput pace. The A100 is not the bottleneck; the reviewer is.
- Conclusion: too slow for a 3-week launch review.

(b) Inference-time rewriter
- Pros: no need to retrain a model from scratch; easy to iterate; can be tested immediately; can run locally on one A100 with a small open model or a deterministic rewrite prompt layer.
- Cost: synthetic data generation can create 1,000–2,000 rewrite pairs quickly through heuristic casualization, backtranslation, and local model rewriting. Reviewer throughput over 2 weeks is ~20 hours × 30–50 examples/hour ≈ 600–1000 examples reviewed. After filtering, that leaves about 400–800 usable examples for validation and light tuning.
- Serving cost: a rewrite pass is a short second-stage pass on top of the base model; it adds latency but remains manageable under one A100 if the rewrite model is small and inference is batched. This is the lowest-risk option under the hard time window.
- Conclusion: this is the best match to the constraints.

(c) Prompt engineering only
- Pros: zero training, immediate.
- Cons: brittle across languages and registers; quality varies too much between Hindi and Kannada and is particularly poor when the base model chooses a dictionary or colloquial register that is not stable. It is a useful baseline but not a launch-quality control method.
- Conclusion: good as a baseline, not as the main solution.

Recommendation
- Choose (b): a local inference-time rewriter, with a small open multilingual model or a compact rewrite layer, and a tight reviewer loop. This is the only option that can be tested end-to-end within 2 weeks without external API budget and with a single reviewer.
- Important caveat: this should be treated as a Hindi/Kannada launch path only. Tamil, Telugu, Bengali, and Marathi remain unreviewed, so we should not claim launch readiness there without additional reviewer capacity.

Back-of-the-envelope arithmetic
- Synthetic data generation: 1,000–2,000 rewrite pairs in the first 2–3 days, using heuristic casualization templates and local model rewrite passes. This is feasible on a single A100 without external APIs.
- Reviewer throughput: 10 h/week × 2 weeks = 20 h total. At 30–50 reviewed examples/hour, the reviewer can evaluate ~600–1000 examples. After filtering and duplicates, around 400–800 are usable.
- Usable reviewed examples: ~400–800 after the first review pass. This is enough to tune a small rewrite system and to build a holdout set for final selection.
- Training time if applicable: if the rewrite step uses a small local model with LoRA or a compact adapter, a few epochs over 1,000–5,000 synthetic examples is feasible on one A100 within the 2-week window. This is a small, bounded training job, not a full SFT run.
- Serving cost/latency: one extra cheap rewrite pass adds a bounded inference stage; the main risk is not raw compute but style instability. It remains within the A100 budget because the rewrite model is small and the rewrite output is short compared with a full generation.
- Evaluation capacity: 200-sample blind evaluation each week, plus a final 400-sample blind set before launch. This keeps the reviewer workload within the available 20 hours.
- Timeline: Days 1–2 build synthetic pairs; Days 3–7 run baseline + first rewrite; Days 8–12 tune from reviewed examples; Days 13–15 blind review and retrain if needed; Days 16–21 launch decision.

Success metric
- Success metric: at least 70% of the 200-sample blind review set across Hindi and Kannada is rated as "acceptable casualness" by the reviewer compared with the baseline.
- This is intentionally higher than a casual pass/fail threshold because the launch review will be used directly by users; we need a clear quality bar.

Kill criterion
- Kill criterion: if by the end of week 2 the reviewer rates fewer than 50% of a 200-sample blind set as acceptable, then abandon the rewriter path and either revert to a stricter prompt-only baseline or expand review capacity before attempting another launch. This decision is made at the end of week 2, before the launch review deadline.

Day-1 experiment
- Day 1 task: generate a 1,000-example synthetic rewrite dataset from a small prompt set with Hindi/Kannada examples; run a first rewrite pass with a small local instruct model or rewrite prompt; evaluate 100 reviewed examples immediately and keep only the examples that match the rubric.
- Concrete execution: create a 1,000-example prompt-to-casualization set in Hindi and Kannada; review 100 examples on day 1; measure acceptability rate; if >=60% on a 100-sample set, proceed with the rewriter path; otherwise stop and switch to a stricter prompt baseline.
- This is intentionally small enough to execute immediately under the 2-week window.

Why the missing native-speaker review for other languages matters
- Without native review for Tamil, Telugu, Bengali, and Marathi, any launch claim for those languages would be unsupported. The safest approach is to treat them as out-of-scope until a native reviewer or a high-quality multilingual review workflow becomes available. We should freeze launch claims for those languages and only stage the system to Hindi/Kannada first.
