import ast, hashlib, json, os, time, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CORPUS = DATA / "github_code_corpus"
REGISTRY = DATA / "pika_evolution_registry.json"
INDEX = DATA / "pika_code_index.json"
REPORT = DATA / "pika_evaluation_report.json"
LOG = ROOT / "logs" / "pika_evolution_loop.log"

DOMAINS = {
    "artificial_intelligence":
        '"artificial intelligence" agent memory reasoning',
    "self_evolution":
        '"self improvement" OR "self evolving" AI agent',
}
EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs",
    ".java", ".kt", ".dart", ".rb", ".php", ".cs",
    ".cpp", ".h", ".hpp", ".html", ".css", ".sql"
}
SKIP = {
    "node_modules", ".git", "vendor", "build", "dist",
    "__pycache__", ".venv", "venv", "target"
}
HEADERS = {
    "User-Agent": "PIKA-Public-Code-Learning/1.0",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default

def request(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def api(url):
    return json.loads(request(url).decode("utf-8"))

def search_repos(query):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": query + " fork:false",
        "sort": "updated",
        "order": "desc",
        "per_page": 2,
    })
    return api(url).get("items", [])

def eligible(path):
    p = Path(path)
    return p.suffix.lower() in EXTS and not any(
        part.lower() in SKIP for part in p.parts
    )

def download_repo(repo, registry):
    name = repo["full_name"]
    entry = registry.setdefault(name, {})
    branch = repo.get("default_branch") or "main"
    if entry.get("branch") == branch and entry.get("updated_at") == repo.get("pushed_at") and entry.get("files"):
        return 0, "unchanged"

    tree_url = (
        "https://api.github.com/repos/" + name +
        "/git/trees/" + urllib.parse.quote(branch, safe="") +
        "?recursive=1"
    )
    tree = api(tree_url)
    files = [
        x for x in tree.get("tree", [])
        if x.get("type") == "blob"
        and eligible(x["path"])
        and x.get("size", 0) <= 180000
    ][:12]

    repo_dir = CORPUS / name
    saved, manifest = 0, {}
    old_files = entry.get("files", {})

    for item in files:
        rel = item["path"]
        dest = repo_dir / rel
        old = old_files.get(rel, {})
        try:
            # Reuse unchanged files when the Git tree SHA is identical.
            if old.get("git_sha") == item.get("sha") and dest.is_file():
                manifest[rel] = old
                continue

            raw_url = (
                "https://raw.githubusercontent.com/" + name + "/" +
                urllib.parse.quote(branch, safe="") + "/" +
                urllib.parse.quote(rel, safe="/")
            )
            body = request(raw_url)
            if len(body) > 180000:
                continue
            digest = hashlib.sha256(body).hexdigest()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            manifest[rel] = {
                "git_sha": item.get("sha"),
                "sha256": digest,
                "bytes": len(body),
            }
            saved += 1
        except Exception as exc:
            log(f"FILE SKIP {name}/{rel}: {exc}")

    entry.update({
        "full_name": name,
        "url": repo.get("html_url"),
        "description": repo.get("description"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "license": (repo.get("license") or {}).get("spdx_id"),
        "branch": branch,
        "updated_at": repo.get("pushed_at"),
        "files": manifest,
        "tree_truncated": tree.get("truncated", False),
        "last_scanned": now(),
    })
    return saved, "scanned"

def evaluate_and_index():
    index, hashes = [], {}
    metrics = {
        "files_seen": 0, "duplicates": 0,
        "python_syntax_pass": 0, "python_syntax_fail": 0,
        "python_syntax_not_applicable": 0,
        "bytes_indexed": 0,
    }

    for path in CORPUS.rglob("*"):
        if not path.is_file() or not eligible(str(path.relative_to(CORPUS))):
            continue
        try:
            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace")
        except OSError:
            continue

        digest = hashlib.sha256(data).hexdigest()
        metrics["files_seen"] += 1
        metrics["bytes_indexed"] += len(data)
        duplicate = digest in hashes
        if duplicate:
            metrics["duplicates"] += 1
        else:
            hashes[digest] = str(path.relative_to(CORPUS))

        syntax = "not_applicable"
        if path.suffix.lower() == ".py":
            try:
                ast.parse(text, filename=str(path))
                syntax = "pass"
                metrics["python_syntax_pass"] += 1
            except (SyntaxError, ValueError) as exc:
                syntax = "fail"
                metrics["python_syntax_fail"] += 1
                log(f"PYTHON SYNTAX FAIL {path.relative_to(CORPUS)}: {exc}")
        else:
            metrics["python_syntax_not_applicable"] += 1

        lower = text.lower()
        tags = [
            tag for tag, words in {
                "ai": ("artificial intelligence", "llm", "neural", "model"),
                "agent": ("agent", "planner", "orchestrat"),
                "memory": ("memory", "embedding", "retrieval"),
                "evaluation": ("evaluate", "benchmark", "assert", "test"),
                "self_evolution": ("self-improv", "self-evol", "reflection"),
                "repair": ("repair", "rollback", "patch", "healing"),
            }.items() if any(word in lower for word in words)
        ]
        index.append({
            "path": str(path.relative_to(CORPUS)),
            "sha256": digest,
            "bytes": len(data),
            "language": path.suffix.lower().lstrip("."),
            "duplicate": duplicate,
            "python_syntax": syntax,
            "tags": tags,
        })

    INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return metrics

def cycle():
    start = time.time()
    log("=== PIKA ACQUIRE / INDEX / EVALUATE CYCLE START ===")
    CORPUS.mkdir(parents=True, exist_ok=True)
    registry = read_json(REGISTRY, {"repositories": {}})
    repos = registry.setdefault("repositories", {})
    downloaded = 0
    scanned = 0
    errors = []

    # Preserve the existing language acquisition engine and its four
    # existing task/capability searches, if already implemented there.
    try:
        from core.github_skill_acquisition import run
        log("Running existing GitHub acquisition engine")
        run()
    except Exception as exc:
        errors.append("existing acquisition: " + repr(exc))
        log("EXISTING ENGINE ERROR: " + repr(exc))

    # Add the two requested discovery domains.
    for domain, query in DOMAINS.items():
        log("DISCOVERY DOMAIN: " + domain)
        try:
            for repo in search_repos(query):
                try:
                    count, status = download_repo(repo, repos)
                    downloaded += count
                    scanned += 1
                    log(f"{status.upper()} {repo['full_name']} new_files={count}")
                except Exception as exc:
                    errors.append(repo.get("full_name", "?") + ": " + repr(exc))
                    log("REPO ERROR: " + repr(exc))
        except Exception as exc:
            errors.append(domain + ": " + repr(exc))
            log("SEARCH ERROR " + domain + ": " + repr(exc))

    REGISTRY.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    metrics = evaluate_and_index()
    report = {
        "timestamp": now(),
        "duration_seconds": round(time.time() - start, 2),
        "domains_added": list(DOMAINS),
        "repositories_in_registry": len(repos),
        "repositories_scanned_this_cycle": scanned,
        "new_files_downloaded_by_added_domains": downloaded,
        "evaluation": metrics,
        "errors": errors,
        "limits": [
            "Python AST parsing is not a full correctness test.",
            "Unknown public code is indexed, not executed.",
            "Search API finds repository metadata/README, not every code line.",
            "Semantic Brain integration is not claimed by this loop."
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("CYCLE REPORT: " + json.dumps(report, ensure_ascii=False))
    log("=== CYCLE COMPLETE ===")
    return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval-hours", type=float, default=6)
    args = parser.parse_args()

    if args.daemon:
        while True:
            try:
                cycle()
            except Exception as exc:
                log("CYCLE CRASH RECOVERED: " + repr(exc))
            time.sleep(max(1, args.interval_hours) * 3600)
    else:
        cycle()
