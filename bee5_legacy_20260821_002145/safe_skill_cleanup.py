from pathlib import Path
from datetime import datetime
import shutil
import json

ROOT = Path.cwd()
PERMANENT = ROOT / "permanent_skills"
STAGING = ROOT / "skill_cleanup_staging"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP = ROOT / f"permanent_skills_backup_{STAMP}"
ARCHIVE = ROOT / f"skill_archive_{STAMP}"

print("=" * 80)
print("BEE5 SAFE SKILL CLEANUP")
print("=" * 80)
print(f"Root       : {ROOT}")
print(f"Backup     : {BACKUP}")
print(f"Archive    : {ARCHIVE}")
print("Mode       : SAFE / REVERSIBLE")
print("Permanent deletion: NO")
print("=" * 80)

if not PERMANENT.exists():
    raise SystemExit("ERROR: permanent_skills directory not found.")

# ------------------------------------------------------------------
# 1. FULL BACKUP
# ------------------------------------------------------------------

print("\n[1/5] Creating full backup...")

shutil.copytree(
    PERMANENT,
    BACKUP,
    dirs_exist_ok=False
)

print(f"Backup created: {BACKUP}")

# ------------------------------------------------------------------
# 2. CONFIRMED PLACEHOLDERS
# ------------------------------------------------------------------

placeholder_dir = STAGING / "PLACEHOLDER"

placeholder_files = sorted(
    p.name for p in placeholder_dir.glob("*.py")
) if placeholder_dir.exists() else []

# ------------------------------------------------------------------
# 3. CLEARLY BROKEN INFRASTRUCTURE
# ------------------------------------------------------------------

broken_infrastructure = {
    "skill_module_48.py",
    "skill_module_69.py",
    "skill_module_8.py",
    "skill_module_neural_network_node.py",
}

# ------------------------------------------------------------------
# 4. ARCHIVE — NEVER DELETE
# ------------------------------------------------------------------

archived = []

def archive_file(filename, category):
    source = PERMANENT / filename

    if not source.exists():
        return False

    target_dir = ARCHIVE / category
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / filename

    shutil.move(str(source), str(target))

    archived.append({
        "file": filename,
        "category": category,
        "from": str(source),
        "to": str(target),
    })

    return True


print("\n[2/5] Archiving confirmed placeholders...")

for filename in placeholder_files:
    archive_file(filename, "PLACEHOLDERS")

print(f"Placeholder files archived: "
      f"{sum(x['category'] == 'PLACEHOLDERS' for x in archived)}")


print("\n[3/5] Archiving clearly broken infrastructure...")

for filename in sorted(broken_infrastructure):
    archive_file(filename, "BROKEN_INFRASTRUCTURE")

print(f"Broken infrastructure archived: "
      f"{sum(x['category'] == 'BROKEN_INFRASTRUCTURE' for x in archived)}")


# ------------------------------------------------------------------
# 5. REPORT
# ------------------------------------------------------------------

print("\n[4/5] Generating cleanup report...")

remaining = sorted(
    p.name for p in PERMANENT.glob("*.py")
)

report = {
    "timestamp": STAMP,
    "mode": "SAFE_REVERSIBLE",
    "permanent_deletion": False,
    "backup": str(BACKUP),
    "archive": str(ARCHIVE),
    "placeholder_candidates": len(placeholder_files),
    "broken_infrastructure_candidates": len(broken_infrastructure),
    "archived": archived,
    "remaining_skill_files": remaining,
}

report_path = ROOT / f"skill_cleanup_report_{STAMP}.json"

report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

# ------------------------------------------------------------------
# VERIFICATION
# ------------------------------------------------------------------

print("\n[5/5] Verification...")

archive_count = sum(
    1 for _ in ARCHIVE.rglob("*.py")
)

backup_count = sum(
    1 for _ in BACKUP.rglob("*.py")
)

remaining_count = len(remaining)

print()
print("=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print(f"Archived Python files : {archive_count}")
print(f"Backup Python files   : {backup_count}")
print(f"Remaining Python files: {remaining_count}")
print(f"Backup                : {BACKUP}")
print(f"Archive               : {ARCHIVE}")
print(f"Report                : {report_path}")
print("=" * 80)

print("\nIMPORTANT:")
print("• Nothing was permanently deleted.")
print("• Full original permanent_skills backup exists.")
print("• Duplicate candidates were NOT deleted.")
print("• Remaining skills require no immediate action.")
