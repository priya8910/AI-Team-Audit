Part A — Tokenizer audit memo (real multilingual corpus)

The tiny smoke-test corpus is not the final answer. It was used only to diagnose bugs and metric failure modes. The final analysis uses a real multilingual public corpus: Helsinki-NLP/OPUS-100, a public sentence-aligned translation corpus accessible without a license wall in this environment.

FLORES-200 attempt: direct HF artifact fetch returned HTTP 401 in this environment, which indicates the dataset is not freely downloadable without accepted terms. The repository therefore uses a reproducible public alternative, and the exact manual FLORES instructions are recorded in the corpus-prep script.

Real corpus used: OPUS-100, language rows sampled from en-hi, en-kn, and en-ta, with 2000 sentences per language file.

Results from `python your-submission/partA/scripts/corrected_analysis.py --corpus_dir your-submission/partA/corpus`:

| language | gpt2 tok/word | gpt2 tok/char | gpt2 tok/sentence | xlm-roberta-base tok/word | xlm-roberta-base tok/char | xlm-roberta-base tok/sentence |
|---|---:|---:|---:|---:|---:|---:|
| eng | 1.306 | 0.239 | 14.551 | 1.454 | 0.266 | 16.194 |
| hin | 7.193 | 1.484 | 96.675 | 1.622 | 0.335 | 21.807 |
| kan | 17.752 | 2.265 | 82.148 | 2.777 | 0.354 | 12.852 |
| tam | 23.944 | 2.624 | 239.986 | 2.650 | 0.290 | 26.565 |

Interpretation:
- GPT-2 is not a valid multilingual-serving baseline for Indian languages. It massively overstates fertility for Kannada and Tamil because it was not trained for these scripts, and therefore it is not a defensible routing metric.
- XLM-R is a far better multilingual baseline. On the same public corpus, Hindi is still somewhat more expensive than English, but the gap is far smaller and more realistic than the GPT-2 distortion: roughly 1.8× for Hindi and 2.9× for Tamil in tokens/word, while Kannada is 3.2× in tokens/word.
- `tokens_per_sentence` is the best single operational metric for routing and cost, because it holds the request unit constant. `tokens_per_word` and `tokens_per_char` are descriptive fertility metrics, not direct serving-cost proxies.

Recommendation (final):
- Do not use GPT-2 fertility or per-line averages as the routing decision metric.
- For serving/cost decisions, use `avg_input_tokens_per_parallel_sentence` computed with a multilingual tokenizer (XLM-R or a better Indic-aware tokenizer) on a real multilingual corpus. The bilingual English-to-Indic corpora above are a defensible first pass; FLORES-200 remains the preferred final benchmark if an authorized access path is available.
- For production, monitor `avg_input_tokens_by_language` with a chosen multilingual tokenizer and compare the same sentence-unit denominator across languages.

Traceability:
- Reproducible corpus prep: `your-submission/partA/scripts/prepare_corpus.py`
- Corrected analysis: `your-submission/partA/scripts/corrected_analysis.py`
- Result artifact: `your-submission/partA/corrected_analysis/results.json`
- Bug audit: `your-submission/partA/scripts/audit_fertility.py`
