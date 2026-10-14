# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Matias Salgado

"""
Cognitive Decision Architecture (CDA 2.0)
Module: cda.ledger.audit
"""

import datetime
import hashlib
import json
from typing import Any, Optional

from pydantic import BaseModel

from cda.shared.models import AuditDecision


class LiabilityEnvelope(BaseModel):
    """
    Forensic governance envelope binding intent, decision, and payload hash.
    """

    envelope_id: str
    sequence_id: int
    intent_id: str
    agent_id: str
    principal_authority_id: str
    verdict: str
    original_payload_hash: str
    adjusted_payload_hash: Optional[str] = None
    stochastic_drift_index: float
    timestamp: str
    prev_hash: str
    envelope_hash: str


class AuditLedger:
    """
    Append-only cryptographically verifiable decision ledger using SHA-256 hash chaining.
    """

    def __init__(self) -> None:
        self.ledger: list[LiabilityEnvelope] = []
        self.sequence_counter: int = 0
        self.genesis_hash: str = "0" * 64

    def _calculate_hash(
        self,
        sequence_id: int,
        intent_id: str,
        verdict: str,
        orig_hash: str,
        prev_hash: str,
        timestamp: str,
    ) -> str:
        payload = f"{sequence_id}:{intent_id}:{verdict}:{orig_hash}:{prev_hash}:{timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_decision(
        self,
        decision: AuditDecision,
        agent_id: str,
        original_params: dict[str, Any],
    ) -> LiabilityEnvelope:
        self.sequence_counter += 1
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        orig_json = json.dumps(original_params, sort_keys=True)
        orig_hash = hashlib.sha256(orig_json.encode("utf-8")).hexdigest()

        adj_hash: Optional[str] = None
        if decision.axis_1_action_verdict.remediation_details:
            adj_payload = (
                decision.axis_1_action_verdict.remediation_details.adjusted_payload
            )
            adj_json = json.dumps(adj_payload, sort_keys=True)
            adj_hash = hashlib.sha256(adj_json.encode("utf-8")).hexdigest()

        prev_hash = (
            self.ledger[-1].envelope_hash if self.ledger else self.genesis_hash
        )
        envelope_hash = self._calculate_hash(
            self.sequence_counter,
            decision.intent_id,
            decision.verdict,
            orig_hash,
            prev_hash,
            now_iso,
        )

        envelope = LiabilityEnvelope(
            envelope_id=f"env_{self.sequence_counter:06d}",
            sequence_id=self.sequence_counter,
            intent_id=decision.intent_id,
            agent_id=agent_id,
            principal_authority_id=decision.principal_authority_id,
            verdict=decision.verdict,
            original_payload_hash=orig_hash,
            adjusted_payload_hash=adj_hash,
            stochastic_drift_index=decision.stochastic_drift_index,
            timestamp=now_iso,
            prev_hash=prev_hash,
            envelope_hash=envelope_hash,
        )

        self.ledger.append(envelope)
        return envelope

    append_record = record_decision

    def verify_integrity(self) -> bool:
        if not self.ledger:
            return True

        for i, env in enumerate(self.ledger):
            expected_prev = (
                self.ledger[i - 1].envelope_hash if i > 0 else self.genesis_hash
            )
            if env.prev_hash != expected_prev:
                return False

            recalculated = self._calculate_hash(
                env.sequence_id,
                env.intent_id,
                env.verdict,
                env.original_payload_hash,
                env.prev_hash,
                env.timestamp,
            )
            if recalculated != env.envelope_hash:
                return False

        return True


GLOBAL_AUDIT_LEDGER = AuditLedger()