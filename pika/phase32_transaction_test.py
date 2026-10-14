from pathlib import Path
import shutil

from core.transaction_engine import TransactionEngine


workspace = Path.home() / "pika" / "workspace"
test_file = workspace / "phase32_transaction_test.txt"

if test_file.exists():
    test_file.unlink()

test_file.write_text(
    "ORIGINAL PIKA CONTENT\n",
    encoding="utf-8",
)

engine = TransactionEngine(workspace)

print("=" * 70)
print("PHASE 32 TRANSACTION TEST")
print("=" * 70)

print("\n[1] BEGIN TRANSACTION")

begin = engine.begin(
    ["phase32_transaction_test.txt"],
    transaction_id="TX-PHASE32-TEST",
)

print(begin)
assert begin["success"] is True

print("\n[2] MODIFY FILE")

test_file.write_text(
    "BROKEN NEW CONTENT\n",
    encoding="utf-8",
)

print(test_file.read_text(encoding="utf-8").strip())

assert test_file.read_text(
    encoding="utf-8"
) == "BROKEN NEW CONTENT\n"

print("\n[3] SIMULATE FAILURE")
print("Verification: FAIL")

print("\n[4] ROLLBACK")

rollback = engine.rollback(
    "TX-PHASE32-TEST"
)

print(rollback)
assert rollback["success"] is True

print("\n[5] VERIFY RESTORATION")

content = test_file.read_text(
    encoding="utf-8"
)

print(content.strip())

assert content == "ORIGINAL PIKA CONTENT\n"

print("\n[6] BEGIN SECOND TRANSACTION")

begin2 = engine.begin(
    ["phase32_transaction_test.txt"],
    transaction_id="TX-PHASE32-COMMIT",
)

print(begin2)
assert begin2["success"] is True

test_file.write_text(
    "VALID NEW CONTENT\n",
    encoding="utf-8",
)

print("\n[7] COMMIT")

commit = engine.commit(
    "TX-PHASE32-COMMIT"
)

print(commit)
assert commit["success"] is True

print("\n[8] VERIFY COMMITTED CONTENT")

content = test_file.read_text(
    encoding="utf-8"
)

print(content.strip())

assert content == "VALID NEW CONTENT\n"

print("\n[9] SECURITY CHECK")

try:
    result = engine.begin(
        ["../../.env"],
        transaction_id="TX-PHASE32-SECURITY",
    )

    if result.get("success"):
        raise AssertionError(
            "Workspace traversal was not blocked."
        )

    print(
        "Traversal blocked:",
        result.get("error"),
    )

except ValueError as exc:
    print(
        "Traversal blocked:",
        exc,
    )

print("\n[10] CLEANUP")

test_file.unlink(missing_ok=True)

shutil.rmtree(
    workspace / ".pika" / "transactions",
    ignore_errors=True,
)

print("\n" + "=" * 70)
print("PHASE 32.1 SNAPSHOT + TRANSACTION TEST: PASS")
print("=" * 70)
