"""
audit_fertility.py

Minimal experiments to test hypotheses about fertility.py behavior.

Usage:
    python audit_fertility.py --tokenizer gpt2

This script runs fertility.py logic on small inputs and compares results
against controlled implementations to expose bugs or conceptual issues.
"""

import subprocess
import sys
import os
import argparse
import json
import unicodedata

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'fertility.py'))


def run_fertility(corpus_spec, tokenizer):
    cmd = [sys.executable, SCRIPT, '--tokenizer', tokenizer]
    for lang, path in corpus_spec.items():
        cmd += ['--corpus', f'{lang}={path}']
    print('Running:', ' '.join(cmd))
    out = subprocess.check_output(cmd, text=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tokenizer', default='gpt2')
    args = ap.parse_args()

    # Prepare tiny corpus files
    tmpdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'corpus'))
    os.makedirs(tmpdir, exist_ok=True)
    s1 = 'This  is  a test.'  # double spaces
    s2 = 'नमस्ते दुनिया'     # hindi greeting (no punctuation)
    s3 = 'This\tis\t a\t test.'  # irregular whitespace including tabs
    s4 = 'Cafe\u0301'  # canonically equivalent to 'Café' under NFC
    s5 = 'ENGLISH CITY'
    f1 = os.path.join(tmpdir, 'test_eng.txt')
    f2 = os.path.join(tmpdir, 'test_hin.txt')
    with open(f1, 'w', encoding='utf-8') as f:
        f.write(s1 + '\n')
    with open(f2, 'w', encoding='utf-8') as f:
        f.write(s2 + '\n')

    print('\n=== Running original fertility.py on test files ===')
    out = run_fertility({'eng': f1, 'hin': f2}, args.tokenizer)
    print(out)

    print('\n=== Minimal reproduction checks for the A2 audit ===')
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    import fertility as fert

    tok = fert.load_tokenizer(args.tokenizer)

    def count_words_via_split(s):
        return len(s.split())

    def count_words_via_space(s):
        return len(s.split(' '))

    # Bug / metric demonstration: multiple spaces and tabs distort the denominator.
    for label, sample in [('double_space', s1), ('tabbed_whitespace', s3), ('unicode_nfc', s4), ('uppercase_case', s5)]:
        raw = sample
        lower = raw.lower()
        token_count_raw = len(tok(raw))
        token_count_lower = len(tok(lower))
        words_space = count_words_via_space(raw)
        words_whitespace = count_words_via_split(raw)
        print(f'{label}: raw_tokens={token_count_raw}, lower_tokens={token_count_lower}, split(" ")={words_space}, split()={words_whitespace}, normalized={unicodedata.normalize("NFC", raw)}')

    # Suspicious-looking behavior that is actually acceptable: lowercasing removes case noise but does not change the word count for this case.
    print('\nLowercasing check: ', s5.lower(), '->', len(tok(s5.lower())), 'tokens vs', len(tok(s5)), 'tokens')

    # Controlled analysis for the main examples
    print('\n=== Running controlled analyze to compare whitespace splitting and lowercasing behavior ===')
    lines_eng = [s1]
    lines_hin = [s2]

    def analyze_control(lines, encode):
        per_line = []
        for line in lines:
            raw = line
            lc = raw.lower()
            tokens = encode(lc)
            words = raw.split()
            chars = len(raw)
            per_line.append((len(tokens), len(words), chars))
        return per_line

    pe = analyze_control(lines_eng, tok)
    ph = analyze_control(lines_hin, tok)
    print('eng (tokens, words, chars):', pe)
    print('hin (tokens, words, chars):', ph)

    print('\nWrite a small JSON record to partA/results/experiment1.json')
    res = {'original_output': out, 'controlled': {'eng': pe, 'hin': ph}, 'additional_checks': {'double_space': {'split_space': count_words_via_space(s1), 'split_whitespace': count_words_via_split(s1)}, 'tabbed_whitespace': {'split_space': count_words_via_space(s3), 'split_whitespace': count_words_via_split(s3)}, 'unicode_nfc': {'nfc': unicodedata.normalize('NFC', s4), 'nfd': s4}}}
    with open(os.path.join(os.path.dirname(__file__), '..', 'results', 'experiment1.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Saved results to', os.path.join(os.path.dirname(__file__), '..', 'results', 'experiment1.json'))


if __name__ == '__main__':
    main()
