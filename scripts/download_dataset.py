from huggingface_hub import snapshot_download

REPO = "ISL500/ISL-DATA"

VOCAB = [
    "I", "You", "He", "She", "We", "They",
    "Mother", "Father", "Friend", "Teacher", "Student", "School",
    "Doctor", "Police", "Water", "Food", "Help",
    "Go", "Give", "Eat", "Drink", "Work",
    "What", "Where", "Why", "Yes", "No", "Please", "Thankyou", "Hello",
    "Today", "Tomorrow"
]

# build exact glob patterns -- anchored so "I" doesn't match "Island" etc.
patterns = [f"Landmarks/MediaPipe/*/{w}__session*__clip*.h5" for w in VOCAB]

print(f"Downloading {len(VOCAB)} word classes...")
local_path = snapshot_download(
    repo_id=REPO,
    repo_type="dataset",
    allow_patterns=patterns,
    local_dir="D:/ISL_Setu/data/raw_landmarks",
)
print(f"Done. Files saved under: {local_path}")