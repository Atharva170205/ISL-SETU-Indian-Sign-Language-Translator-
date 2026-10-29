import sys
sys.path.insert(0, ".")
from core.text_to_gloss import text_to_gloss

test_sentences = [
    "Where is the hospital?",
    "Do you need help?",
    "I want water please",
    "What is your name?",
]

for s in test_sentences:
    result = text_to_gloss(s)
    print(f"{s!r} -> {result}")