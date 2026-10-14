from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
import ast
import json

ROOT = Path.cwd()
CAND = ROOT / "skill_cleanup_staging" / "DUPLICATE_CANDIDATES"
ACTIVE = ROOT / "permanent_skills"

def read_code(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def normalize(code):
    lines = []
    for line in code.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        lines.append(s)
    return "\n".join(lines)

def digest(text):
    return hashlib.sha256(
        normalize(text).encode()
    ).hexdigest()[:16]

def functions(code):
    try:
        tree = ast.parse(code)
        return [
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    except Exception:
        return []

def imports(code):
    try:
        tree = ast.parse(code)
        result = []

        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                result.extend(
                    x.name.split(".")[0]
                    for x in n.names
                )
            elif isinstance(n, ast.ImportFrom) and n.module:
                result.append(n.module.split(".")[0])

        return sorted(set(result))
    except Exception:
        return []

candidates = sorted(CAND.glob("*.py"))
active = sorted(ACTIVE.glob("*.py"))

print("=" * 90)
print("BEE5 DUPLICATE FORENSIC ANALYSIS v3")
print("=" * 90)
print(f"Duplicate candidates : {len(candidates)}")
print(f"Active skills        : {len(active)}")
print("MODE                 : READ ONLY")
print("FILES MODIFIED       : NO")
print("=" * 90)

# ------------------------------------------------------------
# Exact normalized duplicates
# ------------------------------------------------------------

groups = defaultdict(list)

for p in candidates:
    code = read_code(p)
    groups[digest(code)].append(p)

exact_groups = [
    (h, files)
    for h, files in groups.items()
    if len(files) > 1
]

print()
print("=" * 90)
print("EXACT DUPLICATE GROUPS")
print("=" * 90)

if not exact_groups:
    print("None")
else:
    for i, (h, files) in enumerate(
        sorted(exact_groups, key=lambda x: len(x[1]), reverse=True),
        1
    ):
        print()
        print(
            f"GROUP {i:03d} | "
            f"{len(files)} files | hash={h}"
        )

        for p in files:
            print(f"    {p.name}")

# ------------------------------------------------------------
# Candidate similarity
# ------------------------------------------------------------

print()
print("=" * 90)
print("HIGH-SIMILARITY CANDIDATE PAIRS")
print("=" * 90)

candidate_data = {
    p: normalize(read_code(p))
    for p in candidates
}

pairs = []

for i, a in enumerate(candidates):
    for b in candidates[i + 1:]:
        aa = candidate_data[a]
        bb = candidate_data[b]

        if not aa or not bb:
            continue

        score = SequenceMatcher(None, aa, bb).ratio()

        if score >= 0.80:
            pairs.append((score, a.name, b.name))

for score, a, b in sorted(pairs, reverse=True):
    print(f"{score:.3f}  {a}  <->  {b}")

if not pairs:
    print("No pairs >= 0.80 similarity.")

# ------------------------------------------------------------
# Compare candidates against active skills
# ------------------------------------------------------------

print()
print("=" * 90)
print("CANDIDATE vs ACTIVE SKILL SIMILARITY")
print("=" * 90)

active_data = {
    p: normalize(read_code(p))
    for p in active
}

matches = []

for cp, cc in candidate_data.items():
    if not cc:
        continue

    best_score = 0
    best_file = None

    for ap, ac in active_data.items():
        if not ac:
            continue

        score = SequenceMatcher(None, cc, ac).ratio()

        if score > best_score:
            best_score = score
            best_file = ap

    if best_file and best_score >= 0.65:
        matches.append(
            (
                best_score,
                cp.name,
                best_file.name
            )
        )

for score, candidate, active_file in sorted(
    matches,
    reverse=True
):
    print(
        f"{score:.3f}  "
        f"{candidate:<55} "
        f"~ {active_file}"
    )

if not matches:
    print("No strong candidate/active matches.")

# ------------------------------------------------------------
# Metadata
# ------------------------------------------------------------

print()
print("=" * 90)
print("CANDIDATE METADATA")
print("=" * 90)

metadata = []

for p in candidates:
    code = read_code(p)

    item = {
        "file": p.name,
        "normalized_hash": digest(code),
        "bytes": len(code.encode("utf-8", errors="replace")),
        "lines": len(code.splitlines()),
        "functions": functions(code),
        "imports": imports(code),
    }

    metadata.append(item)

    print()
    print(p.name)
    print(f"  hash      : {item['normalized_hash']}")
    print(f"  bytes     : {item['bytes']}")
    print(f"  lines     : {item['lines']}")
    print(f"  functions : {item['functions']}")
    print(f"  imports   : {item['imports']}")

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

report = {
    "candidate_count": len(candidates),
    "active_count": len(active),
    "exact_duplicate_groups": [
        {
            "hash": h,
            "files": [p.name for p in files]
        }
        for h, files in exact_groups
    ],
    "high_similarity_pairs": [
        {
            "score": round(score, 4),
            "file_a": a,
            "file_b": b
        }
        for score, a, b in sorted(pairs, reverse=True)
    ],
    "candidate_active_matches": [
        {
            "score": round(score, 4),
            "candidate": c,
            "active": a
        }
        for score, c, a in sorted(matches, reverse=True)
    ],
    "metadata": metadata
}

out = ROOT / "duplicate_forensic_v3.json"

out.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print()
print("=" * 90)
print("ANALYSIS COMPLETE")
print("=" * 90)
print(f"Exact duplicate groups : {len(exact_groups)}")
print(f"Similar pairs           : {len(pairs)}")
print(f"Candidate-active matches: {len(matches)}")
print(f"JSON report             : {out}")
print("FILES MODIFIED          : 0")
print("=" * 90)
