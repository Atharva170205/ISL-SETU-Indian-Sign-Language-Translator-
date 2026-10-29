from huggingface_hub import HfApi
from collections import defaultdict

REPO = "ISL500/ISL-DATA"

VOCAB = [
    "I", "You", "He", "She", "We", "They",
    "Mother", "Father", "Friend", "Teacher", "Student",
    "School", "College", "Home", "Hospital", "Doctor", "Police",
    "Water", "Food", "Help", "Come", "Go", "Stop", "Give", "Take",
    "Eat", "Drink", "Sleep", "Work", "Study", "Learn",
    "Want", "Need", "Like", "Know", "Understand",
    "What", "Where", "Who", "Why", "How",
    "Yes", "No", "Please", "Thank You", "Sorry", "Hello",
    "Today", "Tomorrow", "Now"
]

def normalize(s):
    return s.lower().replace(" ", "").replace("_", "").replace("-", "")

api = HfApi()
files = api.list_repo_files(REPO, repo_type="dataset")

word_counts = defaultdict(set)
word_file_count = defaultdict(int)
word_users = defaultdict(set)

for f in files:
    if "Landmarks/MediaPipe/" in f and f.endswith(".h5"):
        parts = f.split("/")
        user = parts[2] if len(parts) > 2 else "unknown"
        fname = parts[-1]
        word = fname.split("__session")[0]
        norm = normalize(word)
        word_counts[norm].add(word)
        word_file_count[norm] += 1
        word_users[norm].add(user)

with open("vocab_match_report.txt", "w") as out:
    out.write(f"Total unique word labels in dataset: {len(word_counts)}\n\n")
    found, missing = [], []
    for v in VOCAB:
        norm = normalize(v)
        if norm in word_counts:
            found.append(v)
            out.write(f"FOUND   '{v}' -> {word_counts[norm]} | "
                       f"{word_file_count[norm]} clips | {len(word_users[norm])} signers\n")
        else:
            missing.append(v)
            out.write(f"MISSING '{v}'\n")
    out.write(f"\nSummary: {len(found)} found, {len(missing)} missing\n")
    out.write(f"Missing words: {missing}\n")

print("Done. Report written to vocab_match_report.txt")