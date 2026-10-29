"""
Text -> Gloss conversion for the Text-to-Sign (avatar) feature.

Takes a free-text sentence (e.g. typed by a police officer) and converts it
into a sequence of words drawn ONLY from the supported vocabulary, since the
avatar can only replay signs we have recorded clips for.

Mirrors the existing translate_gloss() pattern (same Groq model/client setup).
"""

import os
import json
from groq import Groq

MODEL = "openai/gpt-oss-20b"

VOCAB = [
    "I", "You", "He", "She", "We", "They", "Mother", "Father", "Friend", "Teacher",
    "Student", "School", "College", "Home", "Hospital", "Doctor", "Police", "Water",
    "Food", "Help", "Come", "Go", "Stop", "Give", "Take", "Eat", "Drink", "Sleep",
    "Work", "Study", "Learn", "Want", "Need", "Like", "Know", "Understand", "What",
    "Where", "Who", "Why", "How", "Yes", "No", "Please", "Thankyou", "Sorry",
    "Hello", "Today", "Tomorrow", "Now",
]

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable not set")
        _client = Groq(api_key=api_key)
    return _client


def text_to_gloss(sentence: str) -> dict:
    """
    Convert free text into an ordered list of vocabulary words that best
    conveys the meaning, using ONLY words from VOCAB.

    Returns:
        {
            "success": True,
            "gloss": ["Police", "Where", "Hospital"],
            "unsupported": []   # concepts that couldn't be mapped to any vocab word
        }
        or
        {"success": False, "error": "..."}
    """
    if not sentence or not sentence.strip():
        return {"success": False, "error": "Empty input sentence"}

    vocab_str = ", ".join(VOCAB)

    prompt = f"""You are converting an English sentence into Indian Sign Language gloss,
using ONLY words from this fixed vocabulary list (case-sensitive, use EXACT spelling):

{vocab_str}

Rules:
- Output ONLY words from the list above, in the natural ISL gloss order (do not add articles, verb tenses, or words not in the list).
- If a concept in the sentence has no matching word in the list, OMIT it rather than inventing a word.
- Keep the gloss as short and clear as possible while preserving meaning.
- Respond with STRICT JSON only, no explanation, in this exact format:
{{"gloss": ["Word1", "Word2", "Word3"]}}

Sentence: "{sentence.strip()}"
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()

        parsed = json.loads(content)
        gloss = parsed.get("gloss", [])

        # Validate every word is actually in our vocab (case-sensitive match to VOCAB)
        vocab_set = {w.lower(): w for w in VOCAB}
        clean_gloss = []
        unsupported = []
        for word in gloss:
            key = word.strip().lower()
            if key in vocab_set:
                clean_gloss.append(vocab_set[key])
            else:
                unsupported.append(word)

        return {
            "success": True,
            "gloss": clean_gloss,
            "unsupported": unsupported,
        }

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Failed to parse Groq response as JSON: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}