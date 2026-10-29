from huggingface_hub import HfApi

REPO = "ISL500/ISL-DATA"
MISSING = [
    "College", "Home", "Hospital", "Come", "Stop", "Take", 
    "Sleep", "Study", "Learn", "Want", "Need", "Like", 
    "Know", "Understand", "Who", "How", "Sorry", "Now"
]

api = HfApi()
files = api.list_repo_files(REPO, repo_type="dataset")

all_dataset_words = set()
for f in files:
    if "Landmarks/MediaPipe/" in f and f.endswith(".h5"):
        w = f.split("/")[-1].split("__session")[0]
        all_dataset_words.add(w)

print(f"Loaded {len(all_dataset_words)} unique labels.\n")

with open("variants_found.txt", "w") as out:
    for target in MISSING:
        t_low = target.lower()
        # Find any dataset label that contains target or is very close
        matches = [w for w in all_dataset_words if t_low in w.lower()]
        out.write(f"Target: {target}\n")
        if matches:
            # show first 10 matches
            for m in sorted(matches)[:10]:
                out.write(f"   -> candidate: {m}\n")
        else:
            out.write("   -> NO SUBSTRING MATCH\n")
        out.write("\n")

print("Done! Results written to variants_found.txt")