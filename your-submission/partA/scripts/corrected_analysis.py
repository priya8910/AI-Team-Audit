"""
corrected_analysis.py

Run corrected tokenizer fertility analysis on the multilingual corpora under
../corpus. The final audit uses public OPUS-100 sentence pairs because the
FLORES-200 artifacts are blocked here by a 401/terms wall.

Computes per-language:
 - total tokens and total words
 - global fertility = total_tokens / total_words
 - global tokens-per-character = total_tokens / total_chars
 - global tokens-per-sentence = total_tokens / num_lines
 - average per-line fertility (kept for diagnostic comparison only)

Usage:
 python corrected_analysis.py --corpus_dir ../corpus --output ../corrected_analysis/results.json
"""

import argparse
import json
import os
import re
import sys
import unicodedata

try:
   import tiktoken
   HAS_TIKTOK = True
except Exception:
   HAS_TIKTOK = False

try:
   from transformers import AutoTokenizer
   HAS_HF = True
except Exception:
   HAS_HF = False


def load_tokenizers():
   toks = {}
   if HAS_TIKTOK:
       try:
           enc = tiktoken.get_encoding("gpt2")
           toks["gpt2"] = enc.encode
       except Exception as exc:
           print("tiktoken/gpt2 load failed:", exc)
   if HAS_HF:
       try:
           hf_tok = AutoTokenizer.from_pretrained("xlm-roberta-base")
           toks["xlm-roberta-base"] = lambda s, tok=hf_tok: tok.encode(s, add_special_tokens=False)
       except Exception as exc:
           print("HF tokenizer load failed:", exc)
   return toks


def analyze_file(path, encode):
   per_line = []
   total_tokens = 0
   total_words = 0
   total_chars = 0
   total_bytes = 0
   num_lines = 0

   with open(path, "r", encoding="utf-8") as f:
       for raw in f:
           line = unicodedata.normalize("NFC", raw.strip())
           if not line:
               continue
           num_lines += 1

           # Keep the raw casing unless explicitly needed for a case-normalized comparison.
           text = line
           tokens = encode(text)
           words = len(re.split(r"\s+", text.strip())) if text.strip() else 0
           chars = len(text)
           byte_count = len(text.encode("utf-8"))
           per_line.append({
               "tokens": len(tokens),
               "words": words,
               "chars": chars,
               "bytes": byte_count,
           })
           total_tokens += len(tokens)
           total_words += words
           total_chars += chars
           total_bytes += byte_count

   ratios = [p["tokens"] / p["words"] for p in per_line if p["words"] > 0]
   per_line_avg = sum(ratios) / len(ratios) if ratios else None
   per_line_tpc = [p["tokens"] / p["chars"] for p in per_line if p["chars"] > 0]
   per_line_avg_tpc = sum(per_line_tpc) / len(per_line_tpc) if per_line_tpc else None

   global_fertility = total_tokens / total_words if total_words else None
   global_tpc = total_tokens / total_chars if total_chars else None
   global_tpb = total_tokens / total_bytes if total_bytes else None
   global_tps = total_tokens / num_lines if num_lines else None

   return {
       "per_line_avg_fertility": per_line_avg,
       "per_line_avg_tpc": per_line_avg_tpc,
       "global_fertility": global_fertility,
       "global_tpc": global_tpc,
       "global_tpb": global_tpb,
       "global_tps": global_tps,
       "total_tokens": total_tokens,
       "total_words": total_words,
       "total_chars": total_chars,
       "total_bytes": total_bytes,
       "num_lines": num_lines,
   }


def main():
   ap = argparse.ArgumentParser()
   ap.add_argument("--corpus_dir", default=os.path.join(os.path.dirname(__file__), "..", "corpus"))
   ap.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "..", "corrected_analysis", "results.json"))
   ap.add_argument("--include_test", action="store_true", help="Include test_*.txt smoke-test files in the output; default is to ignore them for final evaluation.")
   args = ap.parse_args()

   toks = load_tokenizers()
   if not toks:
       print("No tokenizers available. Install tiktoken and/or transformers.")
       print("python -m pip install tiktoken transformers")
       sys.exit(1)

   corpus_dir = os.path.abspath(args.corpus_dir)
   results = {}
   for fname in sorted(os.listdir(corpus_dir)):
       if not fname.endswith(".txt"):
           continue
       if not args.include_test and fname.startswith("test_"):
           continue
       lang = os.path.splitext(fname)[0]
       path = os.path.join(corpus_dir, fname)
       results[lang] = {}
       for tname, encode in toks.items():
           try:
               results[lang][tname] = analyze_file(path, encode)
           except Exception as exc:
               results[lang][tname] = {"error": str(exc)}

   os.makedirs(os.path.dirname(args.output), exist_ok=True)
   with open(args.output, "w", encoding="utf-8") as f:
       json.dump({"tokenizers": list(toks.keys()), "results": results}, f, indent=2, ensure_ascii=False)
   print("Wrote", args.output)


if __name__ == "__main__":
   main()
