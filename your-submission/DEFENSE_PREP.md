Defense preparation notes — corrected key numbers and likely questions

1. What changed
- Replaced the tiny smoke-test-only Part A story with a real multilingual public corpus (OPUS-100) and reran the corrected analysis.
- Corrected the B1 arithmetic to use the model-spec units directly (24 GB, 0.92, 1.6 GB), with the binary-GiB result kept as a labeled sensitivity check.
- Rewrote B2/B3 to distinguish observed throughput from generated goodput and to explain the `reported_tok_s` confusion explicitly.
- Strengthened Part C around the actual A100/2-week/reviewer constraints and removed unsupported model-size claims.
- Updated NOTEBOOK.md to record real experiments, environment constraints, and dataset access findings.

2. Which previous conclusions were wrong
- The original Part A conclusion was wrong because it was based only on the tiny smoke-test corpus and the GPT-2 tokenizer, which overstates fertility for Kannada and Tamil.
- The old B1 conclusion (46 sequences) was wrong as a primary answer because it silently assumed GiB instead of the model-spec GB units.
- The old B2/B3 interpretation of `reported_tok_s` as generated output throughput was wrong; the benchmark column includes prompt + generated tokens.
- The earlier Part C claims about a 100–200M rewriter or a 400M–1B target were too arbitrary without a defensible budget and review plan; they were replaced with a constraint-driven recommendation.

3. Final Part A numbers
- Real corpus: OPUS-100, 2,000 sampled sentence pairs per language file.
- Languages: eng, hin, kan, tam.
- Tokenizers: gpt2, xlm-roberta-base.
- Final key numbers:
  - gpt2: eng 1.306 tok/word, hin 7.193, kan 17.752, tam 23.944
  - xlm-roberta-base: eng 1.454 tok/word, hin 1.622, kan 2.777, tam 2.650
  - xlm-roberta-base tokens/sentence: eng 16.194, hin 21.807, kan 12.852, tam 26.565
  - Best operational metric for routing/cost: average tokens per parallel sentence with a multilingual tokenizer.

4. Final Part B numbers
- B1: bytes_per_token = 114,688 bytes/token.
- Primary capacity using model-spec units: usable KV memory = (24 × 0.92 - 1.6) GB = 20.48 GB = 20.48 × 10^9 bytes.
- Max cached tokens = floor(20.48 × 10^9 / 114,688) = 178,571 tokens.
- Max concurrent 4096-token sequences = floor(178,571 / 4096) = 43 sequences.
- Sensitivity check (GiB interpretation): 46 sequences, but this is not the primary answer.
- B2 observed long-context goodput: batch 24 ≈ 200.93 generated tok/s; batch 48 ≈ 162.28 generated tok/s.
- Observed drop: about 38.7 tok/s or 19.2% worse at batch 48.
- Preemptions: 0 at batch 24, 23 at batch 48; kv_cache_util: 0.93 at batch 24, 0.97 at batch 48.
- B4 chosen counter: peak_kv_cache_utilization (`kv_cache_util`).

5. Final Part C recommendation
- Recommendation: a local inference-time rewriter with a tight human review loop, not full SFT and not prompt engineering alone.
- Why: under one A100, 2 weeks, and one reviewer, SFT is data-limited and prompt engineering is too brittle. The rewriter is the only option that can be tested in time.
- Numeric decision rule: success threshold = at least 70% acceptable on a 200-sample blind review set in Hindi and Kannada. Kill criterion = if the reviewer rates fewer than 50% acceptable by the end of week 2, abandon the rewrite path and revert to a stricter prompt-only baseline or expand reviewer capacity.
- Language limitation: Tamil, Telugu, Bengali, and Marathi remain unreviewed and should not be treated as launch-ready without additional native review.

6. Remaining limitations that genuinely cannot be resolved
- FLORES-200 is not directly downloadable here without accepted terms; this is an environment limitation, not an invented dataset issue.
- There is no native reviewer coverage yet for Tamil, Telugu, Bengali, or Marathi; launch claims for those languages remain unsupported.
- The OPUS-100 corpus is a public, legitimate alternative but not the exact FLORES-200 benchmark; it is sufficient for a defensible audit in this environment.

7. Exact commands for reproducing the final results
- python your-submission/partA/scripts/prepare_corpus.py --outdir your-submission/partA/corpus --max_examples 2000
- python your-submission/partA/scripts/corrected_analysis.py --corpus_dir your-submission/partA/corpus --output your-submission/partA/corrected_analysis/results.json
- python your-submission/partB/calculations/kv_capacity.py
- python -c "import csv; rows=list(csv.DictReader(open('bench/bench_log.csv'))); print([r for r in rows if r['prompt_len']=='3584'])"

Likely defense questions
- Why is GPT-2 not the right primary metric for Hindi/Kannada routing?
- Why is `tokens_per_sentence` the right operational denominator instead of `tokens_per_word` or `tokens_per_char`?
- Why did the benchmark `reported_tok_s` column include prompt tokens?
- Why does the GiB interpretation differ from the spec-based answer, and which one is primary?
- Why does the final Part C recommendation not include a full SFT run?
- Why do we not claim launch readiness for Tamil/Telugu/Bengali/Marathi without native review?
