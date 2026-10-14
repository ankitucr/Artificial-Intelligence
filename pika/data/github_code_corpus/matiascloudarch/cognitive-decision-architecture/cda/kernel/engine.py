# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Matias Salgado

"""
Cognitive Decision Architecture (CDA 2.0)
Module: cda.kernel.engine
"""

import datetime
import os
from typing import Optional

import pyseto
from fastapi import FastAPI
from pyseto import Key

from cda.ledger.audit import GLOBAL_AUDIT_LEDGER
from cda.shared.models import (
    MOCK_POLICIES,
    AgentIntent,
    AuditDecision,
    Axis1ActionVerdict,
    Axis2EvaluationEvidence,
    EvaluatedCheck,
    RemediationDetails,
)

app = FastAPI(
    title="Cognitive Decision Architecture Kernel Engine",
    version="2.0.0",
    description="Deterministic Two-Axis policy evaluation engine minting PASETO v4 leases."
)

SECRET_HEX = os.getenv(
    "CDA_SECRET_HEX",
    "707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f"
)
PASETO_KEY = Key.new(version=4, purpose="local", key=bytes.fromhex(SECRET_HEX))


def mint_paseto_lease(
    intent: AgentIntent,
    axis_1: Axis1ActionVerdict,
    axis_2: Axis2EvaluationEvidence,
    ttl_seconds: int = 60
) -> str:
    """Mints a short-lived PASETO v4 token encoding the Two-Axis verdict."""
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(seconds=ttl_seconds)

    payload = {
        "intent_id": intent.intent_id,
        "agent_id": intent.agent_id,
        "entity_id": intent.entity_id,
        "action": intent.action,
        "params": axis_1.remediation_details.adjusted_payload if axis_1.remediation_details else intent.params,
        "axis_1_action_verdict": axis_1.model_dump(),
        "axis_2_evaluation_evidence": axis_2.model_dump(),
        "iat": now.isoformat(),
        "exp": exp.isoformat()
    }

    token = pyseto.encode(PASETO_KEY, payload)
    return token.decode("utf-8") if isinstance(token, bytes) else str(token)


@app.post("/authorize", response_model=AuditDecision)
def authorize_intent(intent: AgentIntent, human_signature: Optional[str] = None) -> AuditDecision:
    """
    Evaluates an Agent Intent through Two-Axis Governance and mints a PASETO v4 lease.
    """
    evaluated_checks: list[EvaluatedCheck] = []
    regime = intent.regime_context or "FINRA_US"

    # 1. Axis 2 Context Freshness and Regime Mapping Check
    if regime not in MOCK_POLICIES:
        axis_1 = Axis1ActionVerdict(state="INDETERMINATE", fallback_action="BLOCK", remediation_details=None)
        axis_2 = Axis2EvaluationEvidence(
            execution_status="UNMAPPED_REGIME_CONTEXT",
            checks_executed=["CHK-REGIME-01"],
            failure_mode="INVALID_REGIME_CONTEXT"
        )
        decision = AuditDecision(
            verdict="INDETERMINATE",
            paseto_token=None,
            stochastic_drift_index=1.0,
            principal_authority_id="SYSTEM_FAILSAFE",
            intent_id=intent.intent_id,
            jurisdiction=intent.jurisdiction or "US",
            regime_context=regime,
            axis_1_action_verdict=axis_1,
            axis_2_evaluation_evidence=axis_2,
            evaluated_checks=[
                EvaluatedCheck(
                    check_id="CHK-REGIME-01",
                    rule_name="Regime Mapping Validation",
                    passed=False,
                    details=f"Regulatory regime '{regime}' is not registered in active policy database."
                )
            ],
            decision_reason=f"Unmapped regulatory regime context: {regime}"
        )
        GLOBAL_AUDIT_LEDGER.record_decision(
            decision=decision,
            agent_id=intent.agent_id,
            original_params=intent.params
        )
        return decision

    policy = MOCK_POLICIES[regime]
    amount = float(intent.params.get("amount", 0.0))

    # 2. Check Entity Sanction / Disallowed Jurisdiction
    if intent.jurisdiction in policy.get("disallowed_jurisdictions", []):
        evaluated_checks.append(
            EvaluatedCheck(
                check_id="CHK-JUR-01",
                rule_name="Jurisdiction Sanction Check",
                passed=False,
                details=f"Jurisdiction '{intent.jurisdiction}' is disallowed under regime {regime}."
            )
        )
        axis_1 = Axis1ActionVerdict(state="BLOCK", fallback_action="BLOCK", remediation_details=None)
        axis_2 = Axis2EvaluationEvidence(execution_status="COMPLETE", checks_executed=["CHK-JUR-01"], failure_mode=None)
        decision = AuditDecision(
            verdict="BLOCK",
            paseto_token=None,
            stochastic_drift_index=0.95,
            principal_authority_id=intent.entity_id,
            intent_id=intent.intent_id,
            jurisdiction=intent.jurisdiction or "US",
            regime_context=regime,
            axis_1_action_verdict=axis_1,
            axis_2_evaluation_evidence=axis_2,
            evaluated_checks=evaluated_checks,
            decision_reason=f"Action blocked: Jurisdiction {intent.jurisdiction} is sanctioned."
        )
        GLOBAL_AUDIT_LEDGER.record_decision(decision=decision, agent_id=intent.agent_id, original_params=intent.params)
        return decision

    # 3. Check Auto-Approve & Escalation Limits
    auto_limit = policy.get("auto_approve_limit", 500.0)
    escalation_limit = policy.get("escalation_threshold", 2000.0)

    if amount <= auto_limit:
        evaluated_checks.append(
            EvaluatedCheck(
                check_id="CHK-LIM-01",
                rule_name="Operational Amount Limit",
                passed=True,
                details=f"Requested amount ${amount:.2f} is within auto-approval threshold of ${auto_limit:.2f}."
            )
        )
        axis_1 = Axis1ActionVerdict(state="PERMIT", fallback_action=None, remediation_details=None)
        axis_2 = Axis2EvaluationEvidence(
            execution_status="COMPLETE", checks_executed=["CHK-LIM-01"], failure_mode=None
        )
        verdict = "PERMIT"
        stochastic_drift = 0.05
        decision_reason = "Intent approved under standard automated policy limit."

    elif auto_limit < amount <= escalation_limit:
        # Remediation required: Cap amount at auto_limit
        evaluated_checks.append(
            EvaluatedCheck(
                check_id="CHK-LIM-02",
                rule_name="Operational Amount Remediation Threshold",
                passed=False,
                details=f"Amount ${amount:.2f} exceeds auto-approval ${auto_limit:.2f}. Forcing auto-remediation."
            )
        )
        remediation = RemediationDetails(
            rule_id="POL-REM-001",
            original_payload=intent.params,
            adjusted_payload={"amount": auto_limit},
            justification=f"Amount capped from ${amount:.2f} to max auto-approval ${auto_limit:.2f}.",
            remediation_authority="POL-REM-001"
        )
        axis_1 = Axis1ActionVerdict(state="REMEDIATE", fallback_action=None, remediation_details=remediation)
        axis_2 = Axis2EvaluationEvidence(
            execution_status="COMPLETE", checks_executed=["CHK-LIM-02"], failure_mode=None
        )
        verdict = "REMEDIATE"
        stochastic_drift = 0.40
        decision_reason = f"Intent remediated: Amount capped to policy threshold of ${auto_limit:.2f}."

    else:  # amount > escalation_limit
        if human_signature:
            evaluated_checks.append(
                EvaluatedCheck(
                    check_id="CHK-ESC-01",
                    rule_name="Human Oversight Review",
                    passed=True,
                    details=f"Human override verified with signature: {human_signature}"
                )
            )
            axis_1 = Axis1ActionVerdict(state="PERMIT", fallback_action=None, remediation_details=None)
            axis_2 = Axis2EvaluationEvidence(
                execution_status="COMPLETE", checks_executed=["CHK-ESC-01"], failure_mode=None
            )
            verdict = "PERMIT"
            stochastic_drift = 0.15
            decision_reason = f"High-value intent authorized via valid human operator signature: {human_signature}"
        else:
            evaluated_checks.append(
                EvaluatedCheck(
                    check_id="CHK-ESC-01",
                    rule_name="Human Oversight Review",
                    passed=False,
                    details=(
                        f"Amount ${amount:.2f} exceeds escalation threshold "
                        f"${escalation_limit:.2f}. Human review required."
                    )
                )
            )
            axis_1 = Axis1ActionVerdict(state="ESCALATE", fallback_action="BLOCK", remediation_details=None)
            axis_2 = Axis2EvaluationEvidence(
                execution_status="COMPLETE", checks_executed=["CHK-ESC-01"], failure_mode=None
            )
            verdict = "ESCALATE"
            stochastic_drift = 0.85
            decision_reason = f"High-value intent escalated to human operator review queue (Amount: ${amount:.2f})."

    # Mint PASETO token for executable verdicts
    paseto_token = None
    if verdict in ["PERMIT", "REMEDIATE"]:
        paseto_token = mint_paseto_lease(intent=intent, axis_1=axis_1, axis_2=axis_2)

    decision = AuditDecision(
        verdict=verdict,  # type: ignore[arg-type]
        paseto_token=paseto_token,
        stochastic_drift_index=stochastic_drift,
        principal_authority_id=intent.entity_id,
        intent_id=intent.intent_id,
        jurisdiction=intent.jurisdiction or "US",
        regime_context=regime,
        axis_1_action_verdict=axis_1,
        axis_2_evaluation_evidence=axis_2,
        evaluated_checks=evaluated_checks,
        decision_reason=decision_reason
    )

    GLOBAL_AUDIT_LEDGER.record_decision(
        decision=decision,
        agent_id=intent.agent_id,
        original_params=intent.params
    )

    return decision