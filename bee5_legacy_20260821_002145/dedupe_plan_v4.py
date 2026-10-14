from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict
import hashlib
import json

ROOT = Path("permanent_skills")
STAGING = Path("skill_cleanup_staging/DUPLICATE_CANDIDATES")

def read(p):
    return p.read_text(
        encoding="utf-8",
        errors="replace"
    )

def normalize(text):
    return "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.strip().startswith("#")
    )

def h(text):
    return hashlib.sha256(
        normalize(text).encode()
    ).hexdigest()

candidate_files = sorted(STAGING.glob("*.py"))
candidate_names = {p.name for p in candidate_files}

all_files = sorted(ROOT.glob("*.py"))

# Current files that are NOT duplicate candidates
keepers = [
    p for p in all_files
    if p.name not in candidate_names
]

print("=" * 90)
print("BEE5 DEDUPE PLAN v4")
print("=" * 90)
print(f"Candidates                : {len(candidate_files)}")
print(f"Non-candidate keepers     : {len(keepers)}")
print("Self matching             : DISABLED")
print("File modification         : NONE")
print("=" * 90)

candidate_code = {
    p: normalize(read(p))
    for p in candidate_files
}

keeper_code = {
    p: normalize(read(p))
    for p in keepers
}

# ---------------------------------------------------------
# 1. Exact duplicate against a non-candidate keeper
# ---------------------------------------------------------

exact_against_keeper = []

keeper_hashes = defaultdict(list)

for p, code in keeper_code.items():
    keeper_hashes[h(code)].append(p.name)

for p, code in candidate_code.items():
    matches = keeper_hashes.get(h(code), [])

    if matches:
        exact_against_keeper.append({
            "candidate": p.name,
            "matches": matches
        })

print()
print("=" * 90)
print("EXACT DUPLICATE AGAINST NON-CANDIDATE")
print("=" * 90)

for x in exact_against_keeper:
    print(f"\n{x['candidate']}")
    for m in x["matches"]:
        print(f"  EXACT -> {m}")

print(
    f"\nTotal exact candidate->keeper duplicates: "
    f"{len(exact_against_keeper)}"
)

# ---------------------------------------------------------
# 2. High similarity against a non-candidate keeper
# ---------------------------------------------------------

similar = []

for cp, cc in candidate_code.items():

    if not cc:
        continue

    best = []

    for kp, kc in keeper_code.items():

        if not kc:
            continue

        score = SequenceMatcher(
            None,
            cc,
            kc
        ).ratio()

        if score >= 0.90:
            best.append(
                (
                    score,
                    kp.name
                )
            )

    best.sort(
        reverse=True
    )

    if best:
        similar.append({
            "candidate": cp.name,
            "matches": best[:5]
        })

print()
print("=" * 90)
print("HIGH-SIMILARITY CANDIDATE -> NON-CANDIDATE")
print("=" * 90)

for x in similar:
    print(f"\n{x['candidate']}")

    for score, name in x["matches"]:
        print(
            f"  {score:.3f} -> {name}"
        )

print(
    f"\nCandidates with >=0.90 keeper similarity: "
    f"{len(similar)}"
)

# ---------------------------------------------------------
# 3. Exact duplicate groups inside candidates
# ---------------------------------------------------------

groups = defaultdict(list)

for p, code in candidate_code.items():
    groups[h(code)].append(p.name)

exact_groups = [
    files
    for files in groups.values()
    if len(files) > 1
]

print()
print("=" * 90)
print("EXACT DUPLICATE GROUPS INSIDE CANDIDATES")
print("=" * 90)

for i, files in enumerate(
    sorted(
        exact_groups,
        key=len,
        reverse=True
    ),
    1
):

    print(
        f"\nGROUP {i:02d} "
        f"({len(files)} files)"
    )

    for name in files:
        print(
            f"  {name}"
        )

# ---------------------------------------------------------
# Save plan
# ---------------------------------------------------------

result = {
    "candidate_count": len(candidate_files),
    "keeper_count": len(keepers),
    "exact_against_keeper": exact_against_keeper,
    "similar_against_keeper": similar,
    "exact_candidate_groups": exact_groups,
}

Path(
    "dedupe_plan_v4.json"
).write_text(
    json.dumps(
        result,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("=" * 90)
print("PLAN SAVED")
print("=" * 90)
print(
    "dedupe_plan_v4.json"
)
print("NO FILES MODIFIED")
