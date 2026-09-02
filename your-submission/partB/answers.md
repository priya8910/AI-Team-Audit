Part B — Capacity reconciliation (B1, B2, B3, B4)

B1 — KV-cache bytes per token (exact arithmetic using the model's stated units)

Model spec (bench/model_spec.md):
- layers = 28
- KV heads (GQA) = 8
- head_dim = 128
- KV stores both K and V
- KV precision = fp16 = 2 bytes per value
- GPU memory = 24 GB
- gpu_memory_utilization = 0.92
- non-KV overhead = 1.6 GB

Derivation (bytes/token):
- bytes per value = 2
- K + V => factor 2
- values per head = 128
- KV heads = 8
- layers = 28

KV bytes/token = 28 × 8 × 128 × 2 × 2
= 114,688 bytes/token

Primary capacity calculation using the stated units:
- usable KV memory = (24 × 0.92 - 1.6) GB
- = 20.48 GB
- = 20.48 × 10^9 bytes

Available KV bytes = 20.48 × 10^9 = 20,480,000,000 bytes
Max tokens cached = floor(20,480,000,000 / 114,688) = 178,571 tokens
Max concurrent 4096-token sequences = floor(178,571 / 4096) = 43 sequences

Sensitivity check (not the primary answer):
- If someone silently treated the model-spec GB as GiB, then 20.48 GiB would imply 191,739 tokens and 46 sequences.
- That is a useful sensitivity analysis, but it is not the primary result because the specification explicitly states memory in GB and not GiB.

Evidence / reproducible command used:
- python partB/calculations/kv_capacity.py
- Script output includes the primary 20.48 GB result and the GiB sensitivity value.

B2 — Observed throughput at long context vs. forecasted effect of the recommended change

OBSERVED (from bench/bench_log.csv, prompt_len = 3584):
- batch 24: reported_tok_s = 1607.4, wall_clock_s = 61.16, num_requests = 24, preempted_seqs = 0, kv_cache_util = 0.93
- batch 48: reported_tok_s = 1298.5, wall_clock_s = 151.41, num_requests = 48, preempted_seqs = 23, kv_cache_util = 0.97
- Generated-token goodput at batch 24 = 24 × 512 / 61.16 = 200.93 tok/s
- Generated-token goodput at batch 48 = 48 × 512 / 151.41 = 162.28 tok/s
- Difference = 38.65 tok/s lower at batch 48, or about 19.2% worse

This is a measured benchmark result, not a prediction.

PREDICTED EFFECT OF RECOMMENDED CHANGE:
- Recommendation: cap long-context concurrency at batch 24 (or dynamically limit concurrent sequences when prompt_len > 3000) to keep the long-context run below the preemption threshold.
- The predicted goodput after this cap is approximately the observed batch-24 long-context goodput: about 200.9 generated tok/s.
- This is an evidence-based forecast from the benchmark data, not a newly observed deployment result. It is falsifiable: after deployment, measure generated goodput and preemptions under the same prompt_len=3584, gen_len=512 profile.

Mechanism diagnosis:
- The throughput counter `reported_tok_s` is total model-tokens processed, not generated-token output. It is dominated by the prompt prefix: `reported_tok_s = num_requests × (prompt_len + gen_len) / wall_clock_s`.
- The drop at batch 32 and 48 is associated with non-zero preemptions and kv_cache_util ≈ 0.97, which is consistent with coming into KV-cache saturation and scheduler churn.
- The root cause is memory pressure in the long-context regime, not an inherent increase in per-request work.

B3 — Report misreading and the correct serving-cost metric

Exactly what `reported_tok_s` measures:
- `reported_tok_s = (num_requests × (prompt_len + gen_len)) / wall_clock_s`
- For each row, this includes the prompt tokens and generated tokens together.

Two independent derivations of generated goodput for the batch-24 long-context row:
- Row: batch=24, prompt_len=3584, gen_len=512, num_requests=24, wall_clock_s=61.16, reported_tok_s=1607.4

Method 1 (direct):
- generated_tokens = 24 × 512 = 12,288
- generated_goodput = 12,288 / 61.16 = 200.925 tok/s

Method 2 (from total-token throughput):
- generated fraction = 512 / (3584 + 512) = 512 / 4096 = 0.125
- generated_goodput = 1607.4 × 0.125 = 200.925 tok/s

These two methods agree. This shows that `reported_tok_s` is total-token throughput, not generated output goodput. The old report's claim that "batch 48 should deliver ~3200 tok/s" was an extrapolation from the wrong metric.

Operational serving-cost proxy:
- For routing and cost decisions, the right single number is the average input tokens per request for a fixed unit of work, ideally `tokens_per_parallel_sentence` using the same multilingual tokenizer on a parallel corpus.
- Why this is the correct denominator: it holds the semantic unit constant (one sentence or one request) while comparing languages. This is directly tied to serving cost and avoids the distortions of `tok/word` and `tok/char` across scripts and morphology.
- `tok/word` is a descriptive fertility metric, not a direct cost proxy. `tok/char` is similarly descriptive but is still a ratio over a writing-system property, not the cost per fixed request.

B4 — One production counter to confirm the mechanism

The single counter to monitor is `peak_kv_cache_utilization` (`kv_cache_util`).

What it measures:
- It is the peak fraction of the GPU KV-cache reserved during the run.

Why it confirms/refutes the mechanism:
- The working hypothesis is that long-context requests get near the KV-cache limit, which triggers scheduler preemption, latency spikes, and lower generated goodput. If `kv_cache_util` rises toward ~0.95–0.98 in the same runs where goodput falls and preempted sequences appear, that confirms the memory-pressure mechanism. If it stays well below that threshold while goodput keeps dropping, the mechanism is weakened.

Expected trend if the hypothesis is correct:
- In the degraded long-context regime, `kv_cache_util` should remain high and preemptions should rise alongside the loss in generated-token throughput. The expected pattern is near-saturation K/V usage combined with more scheduling churn, not a pure compute bottleneck.

Reproducible commands referenced in this section:
- python partB/calculations/kv_capacity.py
- python -c "import csv; rows=list(csv.DictReader(open('bench/bench_log.csv'))); print([r for r in rows if r['prompt_len']=='3584'])"


