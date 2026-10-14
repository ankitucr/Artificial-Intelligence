# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Matias Salgado

"""
Cognitive Decision Architecture (CDA 2.0)
Module: cda.scripts.simulate_hallucination
"""

from __future__ import annotations

import time

import requests  # type: ignore[import-untyped]

BASE_URL = "http://127.0.0.1:8002"


def run_simulation() -> None:
    """
    Executes an interactive multi-scenario simulation against the unified CDA server (Port 8002).

    Demonstrates:
    1. Standard Within-Policy Intent (PERMIT -> EXECUTED)
    2. Over-Limit Intent (Auto-Capped REMEDIATE)
    3. TOCTOU Context Drift / Freeze (BLOCKED by Gate)
    4. Unmapped Regime Context (INDETERMINATE -> Fail-Closed BLOCK)
    """
    print("\n===========================================================")
    print(" COGNITIVE DECISION ARCHITECTURE (CDA) SIMULATION ENGINE   ")
    print("===========================================================\n")

    # Scenario 1: Standard Compliant Action
    print("--- Scenario 1: Standard Compliant Agent Intent ---")
    payload_1 = {
        "agent_id": "agent-007",
        "jurisdiction": "US",
        "action": "ASSET_TRANSFER",
        "regime": "FINRA_US",
        "risk_score": 0.20,
        "context": {"amount": 250.0},
    }
    try:
        res1 = requests.post(f"{BASE_URL}/evaluate", json=payload_1)
        print(
            f"[Evaluate Endpoint] Status: {res1.status_code} | Verdict:"
            f" {res1.json().get('verdict')}"
        )
    except requests.RequestException as err:
        print(f"❌ Error connecting to server: {err}")

    time.sleep(1)

    # Scenario 2: Hallucinated Excess Amount (Triggers REMEDIATE in Kernel)
    print("\n--- Scenario 2: Hallucinated Amount ($750 vs $500 limit) ---")
    payload_2 = {
        "agent_id": "agent-007",
        "jurisdiction": "US",
        "action": "ASSET_TRANSFER",
        "regime": "FINRA_US",
        "risk_score": 0.55,
        "context": {"amount": 750.0},
    }
    try:
        res2 = requests.post(f"{BASE_URL}/evaluate", json=payload_2)
        print(
            f"[Evaluate Endpoint] Status: {res2.status_code} | Verdict:"
            f" {res2.json().get('verdict')}"
        )
    except requests.RequestException as err:
        print(f"❌ Error connecting to server: {err}")

    time.sleep(1)

    # Scenario 3: Kernel Direct Evaluation with Two-Axis Verification
    print("\n--- Scenario 3: Direct Two-Axis Authorization via Kernel API ---")
    kernel_intent = {
        "entity_id": "usr_001",
        "agent_id": "agent-007",
        "action": "transfer_funds",
        "params": {"amount": 100.0},
        "regime_context": "FINRA_US",
        "jurisdiction": "US",
    }
    try:
        auth_res = requests.post(
            f"{BASE_URL}/kernel/authorize", json=kernel_intent
        ).json()
        print(
            f"[Kernel Authorize] Verdict: {auth_res.get('verdict')} | Token"
            f" Minted: {bool(auth_res.get('paseto_token'))}"
        )

        token = auth_res.get("paseto_token")
        if token:
            # Gate Execution with TOCTOU Freeze check
            gate_payload = {
                "target_service": "payment_gateway",
                "action": "transfer_funds",
                "params": {"amount": 100.0},
                "global_context_freeze": True,  # Force context freeze / TOCTOU drift
            }
            gate_res = requests.post(
                f"{BASE_URL}/gate/execute",
                json=gate_payload,
                headers={"Authorization": f"Bearer {token}"},
            ).json()
            print(
                f"[Gate Execution] Final State: {gate_res.get('final_state')} |"
                f" Reason: {gate_res.get('decision_reason')}"
            )
    except requests.RequestException as err:
        print(f"❌ Error during Two-Axis execution: {err}")

    time.sleep(1)

    # Scenario 4: Unmapped Regulatory Regime Context
    print("\n--- Scenario 4: Unmapped Regulatory Regime Context ---")
    unmapped_intent = {
        "entity_id": "usr_001",
        "agent_id": "agent-007",
        "action": "transfer_funds",
        "params": {"amount": 100.0},
        "regime_context": "UNKNOWN_REGIME_CONTEXT",
        "jurisdiction": "US",
    }
    try:
        auth_unmapped = requests.post(
            f"{BASE_URL}/kernel/authorize", json=unmapped_intent
        ).json()
        print(
            f"[Kernel Authorize] Verdict: {auth_unmapped.get('verdict')} |"
            f" Token Minted: {auth_unmapped.get('paseto_token')}"
        )
        print(
            "[Kernel Axis 2 Status]:"
            f" {auth_unmapped.get('axis_2_evaluation_evidence', {}).get('execution_status')}"
        )
    except requests.RequestException as err:
        print(f"❌ Error during unmapped regime test: {err}")

    print("\n===========================================================")
    print(" SIMULATION COMPLETE - ALL SCENARIOS DISPATCHED SUCCESSFULLY ")
    print("===========================================================\n")


if __name__ == "__main__":
    run_simulation()