from huggingface_hub import HfApi

REPO = "ISL500/ISL-DATA"

api = HfApi()
files = api.list_repo_files(REPO, repo_type="dataset")
print(f"Total files: {len(files)}")
for f in files[:80]:
    print(f)