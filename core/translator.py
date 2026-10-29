"""
core/translator.py — Converts a gloss word list into natural sentences
using Groq's LLM API. English is always generated; Hindi/Marathi are
optional and extensible.

Requires environment variable GROQ_API_KEY to be set.
"""

import os
from groq import Groq
GROQ_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a translator that converts Indian Sign Language (ISL) gloss \
sequences into natural, grammatically correct sentences. ISL gloss is a sequence of \
root words signed in a non-strict order, typically omitting articles, prepositions, \
helping verbs (is/am/are/do), and possessives. Your job is to infer the most natural, \
contextually sensible sentence a human would say, given the gloss words.

Rules:
- Do not just concatenate the words — produce fluent, natural sentences.
- Infer tense, articles, and connecting words as needed.
- If the gloss is ambiguous, choose the most common/likely interpretation \
(e.g. emergency, medical, daily conversation context where relevant).
- Keep the sentence concise — do not add information beyond what's implied by the gloss.
- Output ONLY the requested sentence(s), no explanations, no extra commentary.
"""


def _get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Set it with: $env:GROQ_API_KEY='your_key_here' (PowerShell)"
        )
    return Groq(api_key=api_key)


def translate_gloss(gloss_words, languages=("English",)):
    """
    gloss_words: list[str], e.g. ["I", "Hospital", "Go", "Want"]
    languages: tuple of target languages, e.g. ("English", "Hindi", "Marathi")

    Returns: dict mapping language -> sentence string
        e.g. {"English": "I want to go to the hospital.",
              "Hindi": "मुझे अस्पताल जाना है।"}
    """
    if not gloss_words:
        return {lang: "" for lang in languages}

    gloss_str = " ".join(gloss_words)
    lang_list_str = ", ".join(languages)

    user_prompt = f"""ISL gloss sequence: {gloss_str}

Produce the natural sentence in the following language(s): {lang_list_str}.

Respond in this exact format (one line per language, no extra text):
English: <sentence>
Hindi: <sentence>   (only if requested)
Marathi: <sentence> (only if requested)
"""

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=300,
    )

    text = response.choices[0].message.content.strip()

    # Parse "Language: sentence" lines into a dict
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        lang, _, sentence = line.partition(":")
        lang = lang.strip()
        sentence = sentence.strip()
        if lang in languages:
            result[lang] = sentence

    # Fallback: if parsing failed for any requested language, fill with raw text
    for lang in languages:
        if lang not in result:
            result[lang] = text if len(languages) == 1 else "(parse error — see raw output)"

    return result


if __name__ == "__main__":
    # Quick manual test
    test_gloss = ["I", "Hospital", "Go", "Want"]
    out = translate_gloss(test_gloss, languages=("English", "Hindi"))
    print(f"Gloss: {' '.join(test_gloss)}")
    for lang, sentence in out.items():
        print(f"  {lang}: {sentence}")