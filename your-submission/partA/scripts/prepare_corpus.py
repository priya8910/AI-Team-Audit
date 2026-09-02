"""
prepare_corpus.py

Build a real multilingual evaluation corpus for Part A without depending on
FLORES-200 direct artifact access, which is blocked in this environment by a
401/terms wall.

Preferred public corpus in this environment: OPUS-100, which is openly
available via the Hugging Face datasets library. We save sentence-aligned
language files under partA/corpus/ as lang.txt (utf-8, one sentence per line).

Usage:
    python prepare_corpus.py --outdir ../corpus --max_examples 2000

The script tries to use public datasets; if that is impossible, it prints the
manual download/command instructions.
"""

import argparse
import os
import unicodedata


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.strip()
    return s


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            if line:
                f.write(line + "\n")


def build_opus_corpus(outdir, max_examples):
    try:
        from datasets import load_dataset
    except Exception as exc:
        print("datasets package not available. Install with: python -m pip install datasets")
        raise SystemExit(1) from exc

    mapping = {
        "eng": ("Helsinki-NLP/opus-100", "en-hi", "en"),
        "hin": ("Helsinki-NLP/opus-100", "en-hi", "hi"),
        "kan": ("Helsinki-NLP/opus-100", "en-kn", "kn"),
        "tam": ("Helsinki-NLP/opus-100", "en-ta", "ta"),
    }

    for lang, (repo, pair, side) in mapping.items():
        ds = load_dataset(repo, pair, split=f"train[:{max_examples}]")
        texts = []
        for row in ds:
            text = row["translation"].get(side, "")
            text = normalize_text(text)
            if text:
                texts.append(text)
        dst = os.path.join(outdir, f"{lang}.txt")
        write_lines(dst, texts)
        print(f"Wrote {len(texts)} lines to {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="../corpus")
    ap.add_argument("--max_examples", type=int, default=2000)
    args = ap.parse_args()

    outdir = os.path.abspath(args.outdir) if os.path.isabs(args.outdir) else os.path.abspath(os.path.join(os.getcwd(), args.outdir))
    os.makedirs(outdir, exist_ok=True)

    print("Preparing multilingual corpus in:", outdir)
    print("Attempt 1: use public OPUS-100 corpora (public, reproducible, no license wall)")
    try:
        build_opus_corpus(outdir, args.max_examples)
        print("Done.")
        return
    except Exception as exc:
        print("Public OPUS-100 access failed:", exc)

    print("Attempt 2: FLORES-200 direct artifact access is blocked in this environment (HTTP 401),")
    print("which is why the final audit uses OPUS-100 instead of FLORES-200.")
    print("If you need a manual FLORES-200 fetch, run:")
    print('  mkdir -p <outdir>')
    print('  curl -L -o <outdir>/eng.txt https://huggingface.co/datasets/google/flores200/resolve/main/devtest/eng.devtest')
    print('  curl -L -o <outdir>/hin.txt https://huggingface.co/datasets/google/flores200/resolve/main/devtest/hin.devtest')
    print('  curl -L -o <outdir>/kan.txt https://huggingface.co/datasets/google/flores200/resolve/main/devtest/kan.devtest')
    print('  curl -L -o <outdir>/tam.txt https://huggingface.co/datasets/google/flores200/resolve/main/devtest/tam.devtest')
    print("Then accept the dataset terms or use an account that has permitted access to the huggingface dataset.")
    print("The environment here does not permit the automated authorized download, so the public OPUS-100 corpus is the practical option.")


if __name__ == "__main__":
    main()
