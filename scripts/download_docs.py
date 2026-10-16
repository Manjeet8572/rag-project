import os
import requests

DOCS = {
    "fastapi_tutorial.md": "https://raw.githubusercontent.com/tiangolo/fastapi/master/docs/en/docs/tutorial/first-steps.md",
    "pydantic_models.md": "https://raw.githubusercontent.com/pydantic/pydantic/main/docs/concepts/models.md",
    "langchain_quickstart.md": "https://raw.githubusercontent.com/langchain-ai/langchain/master/docs/docs/get_started/quickstart.md",
    "python_readme.md": "https://raw.githubusercontent.com/python/cpython/main/README.md"
}

os.makedirs("data", exist_ok=True)

for filename, url in DOCS.items():
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(f"data/{filename}", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Failed: {filename} - {e}")

print("Download complete!")