from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS = DATA / "github_code_corpus"
REGISTRY = DATA / "github_skill_registry.json"

EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".kt", ".go", ".rs", ".c", ".h",
    ".cpp", ".hpp", ".cs", ".php", ".rb",
    ".swift", ".dart", ".sh", ".sql",
    ".html", ".css", ".vue", ".svelte",
}

SKIP_PARTS = {
    ".git", "node_modules", "vendor", "dist",
    "build", "__pycache__", ".venv", "venv",
    "coverage", "target", "Pods",
}

MAX_FILE_BYTES = 180_000
MAX_FILES_PER_REPO = 12
MAX_REPOS_PER_LANGUAGE = 2
USER_AGENT = "PIKA-Public-Code-Acquisition/1.0"


def request_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        return None
    return raw.decode("utf-8")


def load_registry():
    if not REGISTRY.exists():
        return {"version": 1, "updated_at": None, "repositories": {}}
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if isinstance(data.get("repositories"), dict):
            return data
    except (OSError, ValueError):
        pass
    return {"version": 1, "updated_at": None, "repositories": {}}


def save_registry(registry):
    registry["updated_at"] = datetime.now(timezone.utc).isoformat()
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    temp = REGISTRY.with_suffix(".tmp")
    temp.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp.replace(REGISTRY)


def search_repositories(language, per_page=MAX_REPOS_PER_LANGUAGE):
    query = urllib.parse.quote(
        f"language:{language} stars:>100"
    )
    url = (
        "https://api.github.com/search/repositories"
        f"?q={query}&sort=stars&order=desc&per_page={per_page}"
    )
    payload = request_json(url)
    return payload.get("items", [])


def eligible_file(item):
    path = item.get("path", "")
    parts = Path(path).parts
    if not path or any(part in SKIP_PARTS for part in parts):
        return False
    if Path(path).suffix.lower() not in EXTENSIONS:
        return False
    if item.get("type") != "blob":
        return False
    size = item.get("size", 0)
    return isinstance(size, int) and 0 < size <= MAX_FILE_BYTES


def acquire_repository(repo, registry):
    full_name = repo["full_name"]
    branch = repo.get("default_branch") or "main"
    existing = registry["repositories"].get(full_name, {})
    if existing.get("downloaded"):
        print(f"  EXISTS: {full_name}")
        return 0

    owner, name = full_name.split("/", 1)
    branch_q = urllib.parse.quote(branch, safe="")
    tree_url = (
        f"https://api.github.com/repos/{full_name}"
        f"/git/trees/{branch_q}?recursive=1"
    )
    tree_data = request_json(tree_url)
    tree = tree_data.get("tree", [])

    files = [item for item in tree if eligible_file(item)]
    files.sort(key=lambda item: (item["path"].count("/"), item["path"]))
    files = files[:MAX_FILES_PER_REPO]

    repo_dir = CORPUS / owner / name
    saved_files = []
    errors = []

    for item in files:
        path = item["path"]
        raw_url = (
            f"https://raw.githubusercontent.com/{full_name}/"
            f"{branch}/{urllib.parse.quote(path, safe='/')}"
        )
        try:
            content = request_text(raw_url)
            if content is None:
                continue
            destination = repo_dir / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            saved_files.append({
                "path": path,
                "sha256": digest,
                "bytes": len(content.encode("utf-8")),
            })
            time.sleep(0.15)
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{path}: {str(exc)[:180]}")

    record = {
        "full_name": full_name,
        "description": repo.get("description"),
        "html_url": repo.get("html_url"),
        "default_branch": branch,
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "license": (repo.get("license") or {}).get("spdx_id", "NOASSERTION"),
        "license_url": (
            (repo.get("license") or {}).get("url")
        ),
        "repository_updated_at": repo.get("updated_at"),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "downloaded": True,
        "files": saved_files,
        "errors": errors,
        "tree_truncated": tree_data.get("truncated", False),
    }
    registry["repositories"][full_name] = record
    save_registry(registry)

    print(
        f"  SAVED: {full_name} | language={record['language']} "
        f"| files={len(saved_files)} | license={record['license']}"
    )
    return len(saved_files)


def run(languages=None):
    languages = languages or ["Python", "JavaScript", "TypeScript"]
    CORPUS.mkdir(parents=True, exist_ok=True)
    registry = load_registry()
    total_repos = 0
    total_files = 0

    print("PIKA GitHub Public Code Acquisition")
    print("Output:", CORPUS)
    print("Registry:", REGISTRY)

    for language in languages:
        print(f"\nSEARCH: {language}")
        try:
            repos = search_repositories(language)
            for repo in repos:
                try:
                    count_before = len(registry["repositories"])
                    count = acquire_repository(repo, registry)
                    total_files += count
                    if len(registry["repositories"]) > count_before:
                        total_repos += 1
                except urllib.error.HTTPError as exc:
                    print(f"  HTTP ERROR {repo.get('full_name')}: {exc.code}")
                    if exc.code in (403, 429):
                        print("GitHub rate limit reached; stopping this run.")
                        save_registry(registry)
                        return
                except Exception as exc:
                    print(f"  SKIP {repo.get('full_name')}: {exc}")

        except urllib.error.HTTPError as exc:
            print(f"Search HTTP ERROR for {language}: {exc.code}")
            if exc.code in (403, 429):
                print("GitHub rate limit reached; stopping.")
                break
        except Exception as exc:
            print(f"Search failed for {language}: {exc}")

    save_registry(registry)
    print("\n========== ACQUISITION REPORT ==========")
    print("New repositories:", total_repos)
    print("Source files saved this run:", total_files)
    print("Repositories in registry:", len(registry["repositories"]))
    print("Registry:", REGISTRY)
    print("Note: downloaded source is collected, not automatically executed.")


if __name__ == "__main__":
    run()
