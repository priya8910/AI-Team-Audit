Part A — Tokenizer audit

Files:
- scripts/prepare_corpus.py  : prepare a real multilingual corpus using the public OPUS-100 dataset by default; includes a FLORES-200 manual fallback when access is authorized
- scripts/audit_fertility.py : run the controlled fertility experiments that reveal the bug and the metric issues
- scripts/corrected_analysis.py : final corrected multilingual analysis for eng/hin/kan/tam

Run:
1. Prepare a real multilingual corpus:
   python your-submission/partA/scripts/prepare_corpus.py --outdir your-submission/partA/corpus --max_examples 2000

2. Run the corrected multilingual analysis:
   python your-submission/partA/scripts/corrected_analysis.py --corpus_dir your-submission/partA/corpus --output your-submission/partA/corrected_analysis/results.json

3. Run the small audit experiment on the sample files included in the repo:
   python your-submission/partA/scripts/audit_fertility.py --tokenizer gpt2

Final results are written to your-submission/partA/corrected_analysis/results.json and the real corpus files live under your-submission/partA/corpus/.
