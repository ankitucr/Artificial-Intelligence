from pathlib import Path
from datetime import datetime
import json
import shutil

ROOT = Path("permanent_skills")
PLAN = Path("dedupe_plan_v4.json")

if not PLAN.exists():
    raise SystemExit("dedupe_plan_v4.json not found")

data = json.loads(
    PLAN.read_text(encoding="utf-8")
)

groups = data["exact_candidate_groups"]

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP = Path(f"permanent_skills_backup_dedupe_{STAMP}")
ARCHIVE = Path(f"skill_archive_exact_duplicates_{STAMP}")

print("=" * 80)
print("BEE5 EXACT DUPLICATE CLEANUP")
print("=" * 80)
print(f"Groups        : {len(groups)}")
print(f"Files in groups: {sum(len(g) for g in groups)}")
print("Mode          : SAFE / REVERSIBLE")
print("Permanent delete: NO")
print("=" * 80)

# ------------------------------------------------------------
# Backup current state
# ------------------------------------------------------------

print("\n[1/4] Creating current-state backup...")

shutil.copytree(
    ROOT,
    BACKUP
)

print(f"Backup: {BACKUP}")

# ------------------------------------------------------------
# Select one representative per exact group
# ------------------------------------------------------------

to_archive = []
representatives = []

for group in groups:

    # Keep lexicographically first file.
    keep = sorted(group)[0]

    representatives.append({
        "keep": keep,
        "group": group,
    })

    for name in group:
        if name != keep:
            to_archive.append(name)

print("\n[2/4] Duplicate plan")

for i, item in enumerate(representatives, 1):
    print(f"\nGROUP {i}")
    print(f"  KEEP   : {item['keep']}")

    for name in item["group"]:
        if name != item["keep"]:
            print(f"  ARCHIVE: {name}")

print()
print(f"Files to archive: {len(to_archive)}")

# ------------------------------------------------------------
# Archive
# ------------------------------------------------------------

print("\n[3/4] Archiving exact duplicates...")

ARCHIVE.mkdir(
    parents=True,
    exist_ok=True
)

archived = []

for name in to_archive:

    source = ROOT / name

    if not source.exists():
        print(f"SKIP missing: {name}")
        continue

    target = ARCHIVE / name

    shutil.move(
        str(source),
        str(target)
    )

    archived.append(name)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

report = {
    "timestamp": STAMP,
    "groups": representatives,
    "archived": archived,
    "kept_count": len(representatives),
    "archived_count": len(archived),
    "backup": str(BACKUP),
    "archive": str(ARCHIVE),
}

report_path = Path(
    f"exact_duplicate_cleanup_{STAMP}.json"
)

report_path.write_text(
    json.dumps(
        report,
        indent=2
    ),
    encoding="utf-8"
)

print("\n[4/4] Verification")

remaining = len(
    list(ROOT.glob("*.py"))
)

archived_count = len(
    list(ARCHIVE.glob("*.py"))
)

print()
print("=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print(f"Archived exact duplicates : {archived_count}")
print(f"Remaining permanent skills: {remaining}")
print(f"Backup                     : {BACKUP}")
print(f"Archive                    : {ARCHIVE}")
print(f"Report                     : {report_path}")
print("=" * 80)
print("\nNo permanent file was irreversibly deleted.")
