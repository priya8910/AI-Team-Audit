# NOTEBOOK — chronological lab notebook

## Plan

1. Inspect the repo and identify the actual assignment artifacts and benchmark sources.
2. Reproduce the fertility bug on tiny controlled inputs to confirm the failure mode.
3. Test whether FLORES-200 is available; if not, identify a legitimate public alternative and document the exact manual instructions.
4. Build a real multilingual corpus and rerun the corrected analysis.
5. Recompute KV capacity using the model spec's stated units and distinguish primary vs sensitivity analysis.
6. Reinterpret the benchmark log to separate total-token throughput from generated goodput.
7. Consolidate the final numbers into the requested memos and defense prep materials.

---

## Experiment 1 — smoke-test audit of `fertility.py`

### Hypothesis
The original `fertility.py` uses a fragile word denominator (`line.split(" ")`) and converts strings with lowercasing before tokenization; these choices can distort the fertility result even when the tokenizer itself is reasonable.

### Method
Command run:

python your-submission/partA/scripts/audit_fertility.py --tokenizer gpt2

### Result
The original script output on the tiny English/Hindi smoke corpus was:

- eng fertility: 1.17 tok/word
- hin fertility: 11.50 tok/word

The controlled reimplementation produced:

- eng tokens, words, chars = (7, 4, 17)
- hin tokens, words, chars = (23, 2, 13)

### Interpretation
The original word denominator fails because it treats a single space as a hard delimiter; multiple spaces create empty strings and distort the denominator. The effect was real and reproducible on deliberately irregular whitespace.

### Revision
The final analysis uses `split()` with any whitespace and computes global totals rather than per-line averages.

---

## Experiment 1A — whitespace bug in `line.split(" ")`

### Hypothesis
The original `fertility.py` computes `words = line.split(" ")`, which is wrong when the string contains multiple spaces or tabs because it treats consecutive delimiters as empty tokens and changes the denominator.

### Method
Command run:

```bash
python -c "import unicodedata, tiktoken; enc=tiktoken.get_encoding('gpt2'); cases={'normal_single_spaces':'This is a test.','double_spaces':'This  is  a test.','tab_whitespace':'This\tis\t a\t test.'};
for label,s in cases.items():
    tokens=len(enc.encode(s)); orig_words=len(s.split(' ')); corr_words=len(s.split()); orig=tokens/orig_words if orig_words else None; corr=tokens/corr_words if corr_words else None; absdiff=abs((orig or 0)-(corr or 0)); pct=(absdiff/corr*100.0) if corr else None; print(label, {'token_count':tokens,'original_word_count':orig_words,'corrected_word_count':corr_words,'original_tok_per_word':orig,'corrected_tok_per_word':corr,'absolute_difference':absdiff,'percentage_difference':pct})"
```

### Result
Actual executed results from gpt2 on the same inputs:

- normal single spaces: token_count=5, original_word_count=4, corrected_word_count=4, original_tok/word=1.25, corrected_tok/word=1.25, absolute_difference=0.00, percentage_difference=0.00
- double spaces: token_count=7, original_word_count=6, corrected_word_count=4, original_tok/word=1.1666666666666667, corrected_tok/word=1.75, absolute_difference=0.5833333333333333, percentage_difference=33.33%
- tab whitespace: token_count=8, original_word_count=3, corrected_word_count=4, original_tok/word=2.6666666666666665, corrected_tok/word=2.00, absolute_difference=0.6666666666666665, percentage_difference=33.33%

### Interpretation
This is a genuine code bug. The `split(" ")` denominator is systematically wrong for double spaces and tabs because it counts empty elements created by repeated delimiters, which depresses the reported tok/word value whenever whitespace is irregular.

### Revision
The corrected A2 evidence treats the bug as: `split(" ")` is incorrect; the correct denominator is `split()` for whitespace-aware word counting.

---

## Experiment 1B — conceptual problem: arithmetic mean of per-line tok/word vs global total_tokens / total_words

### Hypothesis
The original fertility script computes an arithmetic mean of per-line tok/word ratios, but the coherent global metric for a corpus is `total_tokens / total_words`. These are not equivalent and can diverge materially.

### Method
Command run:

```bash
python -c "import os, unicodedata, tiktoken; enc=tiktoken.get_encoding('gpt2'); base=r'c:\Users\jakku\Downloads\starter_kit\starter_kit\your-submission\partA\corpus';
for fname in ['eng.txt','hin.txt','kan.txt','tam.txt']:
    lines=[]; path=os.path.join(base,fname)
    with open(path,'r',encoding='utf-8') as f:
        for raw in f:
            line=unicodedata.normalize('NFC',raw.strip());
            if line: lines.append(line)
    per_line=[]; total_tokens=0; total_words=0
    for line in lines:
        line=line.lower(); tokens=len(enc.encode(line)); words=len(line.split());
        if words: per_line.append(tokens/words)
        total_tokens += tokens; total_words += words
    mean_per_line=sum(per_line)/len(per_line); global_fert=total_tokens/total_words; diff=abs(global_fert-mean_per_line); pct=(diff/global_fert*100.0) if global_fert else None; print(fname, {'per_line_mean':mean_per_line,'global_total_tokens_over_total_words':global_fert,'absolute_difference':diff,'percentage_difference':pct})"
```

### Result
Actual executed values from the real corpus using gpt2:

- eng.txt: per_line_mean=1.5944249550123477, global_total_tokens_over_total_words=1.3126879403976481, absolute_difference=0.2817370146146996, percentage_difference=21.46%
- hin.txt: per_line_mean=8.07383972059497, global_total_tokens_over_total_words=7.191652406814969, absolute_difference=0.8821873137800011, percentage_difference=12.27%
- kan.txt: per_line_mean=18.03250109455947, global_total_tokens_over_total_words=17.75202593192869, absolute_difference=0.28047516263078265, percentage_difference=1.58%
- tam.txt: per_line_mean=21.684863913048392, global_total_tokens_over_total_words=23.94253217599521, absolute_difference=2.2576682629468188, percentage_difference=9.43%

### Interpretation
This is a conceptual/aggregation problem, not a Python syntax bug. The arithmetic mean of per-line ratios gives each sentence equal weight, while `total_tokens / total_words` weights the corpus by sentence length and token count. The discrepancy is large enough to change which number is reported as the benchmark’s fertility figure.

### Revision
The A2 evidence labels this as a metric-aggregation issue and uses global `total_tokens / total_words` as the corpus-level statistic while retaining per-line averages as a diagnostic only.

---

## Experiment 1C — lowercasing is suspicious-looking but not materially harmful for this benchmark

### Hypothesis
The original script lowercases each line before tokenization: `line = line.lower()`. This looks suspicious because it changes the string before counting tokens, but the benchmark may still be robust if the effect is very small on the real corpus.

### Method
Command run:

```bash
python -c "import os, unicodedata, tiktoken; enc=tiktoken.get_encoding('gpt2'); base=r'c:\Users\jakku\Downloads\starter_kit\starter_kit\your-submission\partA\corpus';
for fname in ['eng.txt','hin.txt','kan.txt','tam.txt']:
    lines=[]; path=os.path.join(base,fname)
    with open(path,'r',encoding='utf-8') as f:
        for raw in f:
            line=unicodedata.normalize('NFC',raw.strip());
            if line: lines.append(line)
    lower_vals=[]; raw_vals=[]
    for line in lines:
        tokens_lower=len(enc.encode(line.lower())); words_lower=len(line.lower().split(' '));
        if words_lower: lower_vals.append(tokens_lower/words_lower)
        tokens_raw=len(enc.encode(line)); words_raw=len(line.split(' '));
        if words_raw: raw_vals.append(tokens_raw/words_raw)
    avg_lower=sum(lower_vals)/len(lower_vals); avg_raw=sum(raw_vals)/len(raw_vals); diff=abs(avg_lower-avg_raw); pct=(diff/avg_raw*100.0) if avg_raw else None; print(fname, {'avg_lowercase':avg_lower,'avg_preserve_case':avg_raw,'absolute_difference':diff,'percentage_difference':pct})"
```

### Result
Actual executed values (gpt2 on the same corpus):

- eng.txt: avg_lowercase=1.5944249550123477, avg_preserve_case=1.619599291100116, absolute_difference=0.025174336087768312, percentage_difference=1.5543558351812192
- hin.txt: avg_lowercase=8.07383972059497, avg_preserve_case=8.075922101282945, absolute_difference=0.0020823806879750606, percentage_difference=0.025785051686472465
- kan.txt: avg_lowercase=18.03250109455947, avg_preserve_case=18.035702630599936, absolute_difference=0.003201536040464248, percentage_difference=0.0177511023886168
- tam.txt: avg_lowercase=21.684863913048392, avg_preserve_case=21.69040019951097, absolute_difference=0.0055362864625791985, percentage_difference=0.025524132388779156

### Interpretation
Suspicious-looking but not materially harmful for this benchmark. The observed differences are small (0.02%-1.55%) and do not change the benchmark ranking or the core conclusion. This does not mean lowercasing is universally harmless; it is only harmless here for this benchmark with the tested tokenizer and corpus.

### Revision
The A2 evidence distinguishes the issue clearly: lowercasing is neither the code bug nor the conceptual metric bug; it is a suspicious-looking but acceptable normalization choice for this benchmark, and the measured effect is small.

---

## Experiment 2 — dataset access and corpus availability check

### Hypothesis
The environment may not permit the FLORES-200 files due to dataset terms, so we need to determine whether a public, reproducible multilingual corpus can be used immediately.

### Method
Attempted HTTP fetch to the FLORES-200 artifact URL and verified the response.

### Result
The direct fetch returned HTTP 401. This means the FLORES-200 files are not available as unauthenticated raw artifacts from this environment.

### Interpretation
This is a real environment limitation, not a fabricated dataset failure. We therefore switched to a public alternative corpus that is available without a license wall: OPUS-100 via the Hugging Face `datasets` library.

### Revision
The corpus-prep script documents both the FLORES manual instructions and the practical OPUS-100 path.

---

## Experiment 3 — real multilingual corpus build

### Hypothesis
A public sentence-aligned corpus such as OPUS-100 is sufficient to run the corrected multilingual analysis and avoid the tiny-sample trap.

### Method
Command run:

python your-submission/partA/scripts/prepare_corpus.py --outdir your-submission/partA/corpus --max_examples 2000

### Result
The script created `eng.txt`, `hin.txt`, `kan.txt`, and `tam.txt` under `your-submission/partA/corpus`.

### Interpretation
This was the first time the final analysis used data larger than the tiny smoke corpus. It also established a reproducible corpus workflow that does not rely on a blocked FLORES download.

### Revision
The final memo and defense prep explicitly say the smoke-test corpus was only for diagnosis; the final Part A result uses the real multilingual corpus.

---

## Experiment 4 — corrected multilingual analysis on the real corpus

### Hypothesis
A multilingual tokenizer like XLM-R will produce more realistic fertility numbers than GPT-2, and the ranking of languages will be different depending on the denominator.

### Method
Command run:

python your-submission/partA/scripts/corrected_analysis.py --corpus_dir your-submission/partA/corpus --output your-submission/partA/corrected_analysis/results.json

### Result
The actual final metrics were:

| language | gpt2 tok/word | gpt2 tok/char | xlm-roberta-base tok/word | xlm-roberta-base tok/char | xlm-roberta-base tok/sentence |
|---|---:|---:|---:|---:|---:|
| eng | 1.306 | 0.239 | 1.454 | 0.266 | 16.194 |
| hin | 7.193 | 1.484 | 1.622 | 0.335 | 21.807 |
| kan | 17.752 | 2.265 | 2.777 | 0.354 | 12.852 |
| tam | 23.944 | 2.624 | 2.650 | 0.290 | 26.565 |

### Interpretation
The huge GPT-2 inflation is a tokenizer limitation, not a property of the language. XLM-R produced a more realistic multilingual comparison, and the language ranking changes depending on the metric. This is why a single descriptive ratio is not enough for the routing decision.

### Revision
The final Part A recommendation uses tokens-per-parallel-sentence with a multilingual tokenizer as the main metric and treats `tok/word` and `tok/char` as descriptive diagnostics.

---

## Experiment 5 — KV capacity arithmetic and GB vs GiB correction

### Hypothesis
The model-spec numbers specify memory in GB, so the KV-cache calculation should use decimal GB unless a separate GiB interpretation is explicitly labeled as a sensitivity check.

### Method
Command run:

python your-submission/partB/calculations/kv_capacity.py

### Result
The script printed the primary result:

- bytes_per_token = 114,688
- available_kv_bytes_primary = 20.48 × 10^9
- max_tokens_cached_primary = 178,571
- concurrent_4096_primary = 43

The sensitivity check (binary GiB interpretation) produced:

- max_tokens_cached_gib_sensitivity = 191,739
- concurrent_4096_gib_sensitivity = 46

### Interpretation
This was a real correction: the earlier 46-sequence number was a GiB-based interpretation, not the primary answer. The primary unit-consistent arithmetic yields 43 sequences because the model spec says 24 GB and 1.6 GB, not 24 GiB and 1.6 GiB.

### Revision
The memo and script now clearly label the binary-GiB value as a sensitivity analysis and keep the primary answer in the model-spec units.

---

## Experiment 6 — throughput log reinterpretation

### Hypothesis
The benchmark throughput column includes both prompt tokens and generated tokens, so it does not equal generated goodput.

### Method
Manual arithmetic from `bench/bench_log.csv` for the prompt_len=3584 long-context rows.

### Result
For batch 24:

- total_tokens = 24 × (3584 + 512) = 98,304
- reported_tok_s = 98,304 / 61.16 = 1607.4
- generated_tokens = 24 × 512 = 12,288
- generated_goodput = 12,288 / 61.16 = 200.925 tok/s

For batch 48:

- generated_tokens = 48 × 512 = 24,576
- generated_goodput = 24,576 / 151.41 = 162.28 tok/s

### Interpretation
This was an important real surprise: `reported_tok_s` is not a pure output metric. It is a total-token throughput counter containing prompt + generation. It also explains the apparent throughput increase at the wrong scale.

### Revision
Part B now distinguishes observed throughput from generated goodput and treats the forecasted effect of a cap at batch 24 as an evidence-based forecast, not a newly observed deployment result.

---

## Experiment 7 — final validation and cleanup

### Hypothesis
The corrected write-up should agree across scripts, memos, and defense prep without stale numbers from the tiny smoke-test corpus.

### Method
Re-ran the relevant scripts and checked the values used in each memo against the actual outputs.

### Result
- Part A stats were regenerated from the real OPUS-100 corpus.
- KV capacity uses the model-spec units as the primary answer.
- B2/B3 use the correct throughput interpretation.
- All required part memos and defense notes were updated to match the actual outputs.

### Interpretation
The repo now contains consistent final numbers grounded in actual data.

### Revision
This notebook captures the final evidence trail and the corrections that were required.

