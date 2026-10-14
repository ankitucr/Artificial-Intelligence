from core.error_analyzer import ErrorAnalyzer
from core.recovery_engine import RecoveryEngine


analyzer = ErrorAnalyzer()
recovery = RecoveryEngine()


def check(
    name,
    error,
    expected_type,
    expected_action,
):
    print(f"\n[{name}]")

    diagnosis = analyzer.analyze({
        "success": False,
        "error": error,
    })

    print("Diagnosis:", diagnosis)

    assert diagnosis["error_type"] == expected_type

    decision = recovery.decide(
        diagnosis,
        attempt=1,
    )

    print("Recovery:", decision)

    assert decision["action"] == expected_action


check(
    "MISSING PACKAGE",
    "ModuleNotFoundError: No module named 'requests'",
    "dependency_missing",
    "install_dependency",
)

check(
    "SYNTAX ERROR",
    "SyntaxError: invalid syntax",
    "code_error",
    "repair_code",
)

check(
    "TEST FAILURE",
    "FAILED test_login.py::test_login",
    "test_failure",
    "repair_code",
)

check(
    "CONFIGURATION",
    "Missing environment variable DATABASE_URL",
    "configuration_error",
    "repair_configuration",
)

check(
    "PERMISSION",
    "Permission denied: server.py",
    "permission_error",
    "inspect_permissions",
)

check(
    "NETWORK",
    "Connection timed out while connecting to server",
    "network_error",
    "retry_with_backoff",
)

check(
    "COMMAND POLICY",
    "Only 'python -m py_compile' is allowed through the workspace runtime.",
    "command_policy",
    "change_execution_strategy",
)

print("\n" + "=" * 70)
print("PHASE 32 ERROR ANALYSIS + RECOVERY TEST: PASS")
print("=" * 70)
