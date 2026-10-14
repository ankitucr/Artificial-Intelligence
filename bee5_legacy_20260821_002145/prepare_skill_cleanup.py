import json
import shutil
from pathlib import Path
from collections import Counter

ROOT = Path("permanent_skills")
REPORT = Path("forensic_classification_v2.json")
STAGING = Path("skill_cleanup_staging")

if not REPORT.exists():
    raise SystemExit("forensic_classification_v2.json not found")

data = json.loads(
    REPORT.read_text(
        encoding="utf-8"
    )
)

# Fresh staging directory
if STAGING.exists():
    shutil.rmtree(STAGING)

STAGING.mkdir()

BUCKETS = {
    "PLACEHOLDER": "PLACEHOLDER",
    "BROKEN_SYNTAX": "BROKEN",
    "BROKEN_RUNTIME": "BROKEN",
    "INFRASTRUCTURE_BROKEN": "BROKEN",
    "INFRASTRUCTURE": "INFRASTRUCTURE",
    "INFRASTRUCTURE_GENERATOR": "GENERATORS",
    "NETWORK": "NETWORK",
    "NETWORK_BROKEN": "BROKEN",
    "REAL_CAPABILITY": "REAL_CAPABILITIES",
    "REAL_DUPLICATE_CANDIDATE": "DUPLICATE_CANDIDATES",
    "UNTESTED": "UNTESTED",
    "DATA_OR_SCRIPT": "UNTESTED",
}

counts = Counter()

manifest = []

for item in data["skills"]:

    name = item["file"]
    decision = item["decision"]

    source = ROOT / name

    bucket = BUCKETS.get(
        decision,
        "REVIEW"
    )

    target_dir = STAGING / bucket
    target_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    target = target_dir / name

    if source.exists():
        shutil.copy2(
            source,
            target
        )

    counts[bucket] += 1

    manifest.append({
        "file": name,
        "decision": decision,
        "bucket": bucket,
        "source": str(source),
        "staged": str(target),
    })


# ------------------------------------------------------------
# Duplicate group information
# ------------------------------------------------------------

groups = data.get(
    "duplicate_groups",
    []
)

(STAGING / "duplicate_groups.json").write_text(
    json.dumps(
        groups,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

# ------------------------------------------------------------
# Manifest
# ------------------------------------------------------------

(STAGING / "cleanup_manifest.json").write_text(
    json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

# ------------------------------------------------------------
# Human report
# ------------------------------------------------------------

with (STAGING / "README.txt").open(
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "BEE5 SKILL CLEANUP STAGING\n"
    )

    f.write(
        "===========================\n\n"
    )

    f.write(
        "IMPORTANT:\n"
        "Original permanent_skills files were NOT modified.\n"
        "This directory contains COPIES only.\n\n"
    )

    for bucket, count in sorted(
        counts.items()
    ):
        f.write(
            f"{bucket:<24} : {count}\n"
        )

    f.write("\n")

    f.write(
        "Recommended next action:\n"
    )

    f.write(
        "1. Remove obvious placeholders.\n"
        "2. Separate legacy infrastructure.\n"
        "3. Review network skills.\n"
        "4. Resolve duplicate groups.\n"
        "5. Keep verified capabilities.\n"
    )

print()
print("=" * 72)
print("        BEE5 CLEANUP STAGING CREATED")
print("=" * 72)
print()

for bucket, count in sorted(
    counts.items()
):
    print(
        f"{bucket:<24}: {count}"
    )

print()
print(
    f"Staging directory: {STAGING.resolve()}"
)

print()
print(
    "Original permanent_skills was NOT modified."
)
