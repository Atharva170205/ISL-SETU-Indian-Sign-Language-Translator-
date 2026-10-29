"""
scripts/test_translator.py — No-camera synthetic sentence test.

Parses gloss sequences out of docs/test_sentences.txt, sends each through
core/translator.py (Groq LLM), and prints the real output next to the
expected sentence for manual comparison.

Run:  python scripts/test_translator.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.abspath("."))
from core.translator import translate_gloss

TEST_FILE = os.path.join("docs", "test_sentences.txt")
LANGUAGES = ("English",)  # add "Hindi", "Marathi" here once you want to test those too


def parse_test_file(path):
    """Extract (gloss_words, expected_sentence) pairs from the test file.
    Looks for consecutive 'Gloss: ...' and 'Expected: ...' lines."""
    pairs = []
    gloss = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Gloss:"):
                gloss_str = line[len("Gloss:"):].strip()
                gloss = gloss_str.split()
            elif line.startswith("Expected:") and gloss is not None:
                expected = line[len("Expected:"):].strip()
                pairs.append((gloss, expected))
                gloss = None

    return pairs


def main():
    if not os.path.exists(TEST_FILE):
        print(f"ERROR: {TEST_FILE} not found. Create it first (see docs/test_sentences.txt).")
        return

    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable is not set.")
        print("Set it with: $env:GROQ_API_KEY = 'your_key_here'")
        return

    pairs = parse_test_file(TEST_FILE)
    print(f"Loaded {len(pairs)} test sentences from {TEST_FILE}\n")
    print("=" * 90)

    results = []
    for i, (gloss, expected) in enumerate(pairs, 1):
        gloss_str = " ".join(gloss)
        print(f"\n[{i}/{len(pairs)}] Gloss: {gloss_str}")
        try:
            output = translate_gloss(gloss, languages=LANGUAGES)
            actual = output.get("English", "(no English output)")
        except Exception as e:
            actual = f"ERROR: {e}"

        print(f"  Expected: {expected}")
        print(f"  Groq Out: {actual}")

        match_hint = "✓ close match" if actual.strip().lower() == expected.strip().lower() else ""
        if match_hint:
            print(f"  {match_hint}")

        results.append({
            "gloss": gloss_str,
            "expected": expected,
            "actual": actual,
        })

    print("\n" + "=" * 90)
    print(f"Done. {len(results)} sentences tested.")
    print("Note: exact string matches are rare/not required — judge by whether")
    print("Groq's sentence captures the correct MEANING, not exact wording.")


if __name__ == "__main__":
    main()