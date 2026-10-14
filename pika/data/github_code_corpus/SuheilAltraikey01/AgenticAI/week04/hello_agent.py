"""COSC726 Lab 3 — hello_agent.py

My gates, dispatcher and loop (Tasks 3, 4, 5).

This file assumes the "given" pieces from Part 1/4/8 of the notebook are
already defined and importable: ORDERS, KNOWN_ORDER_IDS, POLICY_THRESHOLD_DAYS,
Tier, TOOLS, STATE_CHANGING, ok/err, GateError, OBSERVED, StopReason, Stop,
TraceStep, Trace, SYSTEM, propose_step, Step. I copied the notebook's given
code into this file too so it can be read/imported on its own, but the
model client (propose_step / _raw_generate) still needs the real
tokenizer/model loaded — this file does not reload those.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ===========================================================================
# PART 1 — the world and the tools (given, copied here for a standalone file)
# ===========================================================================

ORDERS = {
    "A1032": {"promised": "Tue", "eta": "Fri", "days_late": 3, "status": "delayed_at_depot"},
    "A1044": {"promised": "Mon", "eta": "Mon", "days_late": 0, "status": "out_for_delivery"},
    "A1080": {"promised": "Thu", "eta": "Fri", "days_late": 1, "status": "delayed_in_transit"},
    "A1091": {"promised": "Mon", "eta": "Fri", "days_late": 4, "status": "delayed_at_depot"},
}
KNOWN_ORDER_IDS = set(ORDERS)
POLICY_THRESHOLD_DAYS, POLICY_CREDIT_PERCENT = 3, 10
POLICY_TEXT = ("An order delivered 3 or more days after the promised date "
               "qualifies for a 10% credit. A credit changes the customer "
               "account and requires human approval; it may be proposed but "
               "never applied directly by an agent.")


def ok(**f):
    return {"ok": True, **f}


def err(code, **f):
    return {"ok": False, "error": code, **f}


class Tier(str, Enum):
    READ = "read"
    WRITE = "write"
    CONSEQUENTIAL = "consequential"


def track_order(order_id: str) -> dict:
    row = ORDERS.get(order_id)
    if row is None:
        return err("order_not_found", order_id=order_id,
                   hint="Ask the customer to confirm the ID from their email.")
    return ok(order_id=order_id, **row)


def get_late_delivery_policy() -> dict:
    return ok(policy_id="POL-LATE", text=POLICY_TEXT,
              threshold_days=POLICY_THRESHOLD_DAYS,
              credit_percent=POLICY_CREDIT_PERCENT)


APPROVALS, _next = {}, [2048]


def request_approval(order_id: str, kind: str, amount_percent: int) -> dict:
    if order_id not in ORDERS:
        return err("order_not_found", order_id=order_id)
    ref = f"APR-{_next[0]}"
    _next[0] += 1
    APPROVALS[ref] = {"order_id": order_id, "kind": kind,
                      "amount_percent": amount_percent, "state": "pending"}
    return ok(approval_ref=ref, state="pending", account_changed=False,
              note="Pending human approval. Nothing has been applied.")


def escalate_to_human(reason: str) -> dict:
    return ok(escalated=True, reason=reason)


# ===========================================================================
# PART 2 — Task 1: argument models
# ===========================================================================

class TrackOrderArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(pattern=r"^A[0-9]{4}$")


class NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestApprovalArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(pattern=r"^A[0-9]{4}$")
    kind: Literal["credit", "replacement"]
    amount_percent: int = Field(ge=1, le=100)


class EscalateArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=4)


@dataclass(frozen=True)
class ToolSpec:
    fn: object
    tier: Tier
    description: str
    args_model: type[BaseModel]

    @property
    def schema(self) -> dict:
        return self.args_model.model_json_schema()


TOOLS = {
    "track_order": ToolSpec(track_order, Tier.READ,
        "Look up the delivery status of ONE order by its ID. Read-only. "
        "Returns status, promised date, eta and days_late.", TrackOrderArgs),
    "get_late_delivery_policy": ToolSpec(get_late_delivery_policy, Tier.READ,
        "Return the late-delivery policy and its numeric threshold. Read-only.",
        NoArgs),
    "request_approval": ToolSpec(request_approval, Tier.CONSEQUENTIAL,
        "Create a PENDING approval for a credit. Does NOT apply anything.",
        RequestApprovalArgs),
    "escalate_to_human": ToolSpec(escalate_to_human, Tier.WRITE,
        "Hand the case to a human when evidence is insufficient or the "
        "request is out of scope.", EscalateArgs),
}

STATE_CHANGING = {"request_approval", "escalate_to_human"}


# ===========================================================================
# PART 3 — Task 2: the step contract
# ===========================================================================

ACTIONS = ["track_order", "get_late_delivery_policy",
           "request_approval", "escalate_to_human", "final_answer"]


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thought: str = Field(max_length=400)
    action: Literal["track_order", "get_late_delivery_policy",
                    "request_approval", "escalate_to_human", "final_answer"]
    args: dict = Field(default_factory=dict)


def step_schema_hint() -> str:
    """A compact, promptable description of Step and the available tools."""
    lines = [
        "Reply with exactly one JSON object with these fields:",
        '  "thought": one short sentence (max 400 chars) - your reasoning',
        '  "action": one of ' + ", ".join(f'"{a}"' for a in ACTIONS),
        '  "args": the arguments for that tool, or {"text": "..."} when '
        'action is "final_answer"',
        "",
        "Available tools:",
    ]
    for name, spec in TOOLS.items():
        lines.append(f"  {name}: {spec.description}")
        lines.append(f"    args schema: {json.dumps(spec.schema)}")
    return "\n".join(lines)


# ===========================================================================
# Trace and stop reasons (given)
# ===========================================================================

class StopReason(str, Enum):
    COMPLETE = "complete"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"
    ESCALATED = "escalated"
    CAPPED = "capped"
    MALFORMED = "malformed"


@dataclass
class Stop:
    reason: StopReason
    answer: str | None = None
    detail: str = ""


@dataclass
class TraceStep:
    step: int
    tool: str | None = None
    args: dict | None = None
    tier: str | None = None
    ok: bool | None = None
    error: str | None = None
    state_changed: bool | None = None
    thought: str = ""
    tokens: int = 0


@dataclass
class Trace:
    run_id: str = "run"
    steps: list = field(default_factory=list)
    stop: Stop | None = None

    def add(self, s):
        self.steps.append(s)

    @property
    def total_tokens(self):
        return sum(s.tokens for s in self.steps)


class GateError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code, self.detail = code, detail


OBSERVED = {"days_late": None}


# ===========================================================================
# PART 5 — Task 3: the four gates + tier check
# ===========================================================================

def gate_2_conforms(args: dict, args_model: type[BaseModel]) -> None:
    """args_model.model_validate(args); turn ValidationError into GateError."""
    try:
        args_model.model_validate(args)
    except ValidationError as exc:
        first = exc.errors()[0]
        raise GateError("gate2_conforms", f"{first['loc']}: {first['msg']}")


def gate_3_refers(args: dict) -> None:
    """order_id, when present, must be in KNOWN_ORDER_IDS."""
    oid = args.get("order_id")
    if oid is not None and oid not in KNOWN_ORDER_IDS:
        raise GateError("gate3_refers", f"order_id {oid!r} is not a known order")


def gate_4_coheres(name: str, args: dict, trace: Trace) -> None:
    """request_approval only: refuse unless track_order AND the policy have
    already SUCCEEDED this run, and observed days_late >= the threshold."""
    if name != "request_approval":
        return
    tracked_ok = any(s.tool == "track_order" and s.ok for s in trace.steps)
    policy_ok = any(s.tool == "get_late_delivery_policy" and s.ok
                    for s in trace.steps)
    if not (tracked_ok and policy_ok):
        raise GateError(
            "gate4_coheres",
            "must successfully call track_order and get_late_delivery_policy "
            "before requesting approval")
    days = OBSERVED["days_late"]
    if days is None or days < POLICY_THRESHOLD_DAYS:
        raise GateError(
            "gate4_coheres",
            f"observed days_late={days} is below the {POLICY_THRESHOLD_DAYS}-day threshold")


def require_tier(tier: Tier, allow_consequential: bool) -> None:
    if tier == Tier.CONSEQUENTIAL and not allow_consequential:
        raise GateError("tier_blocked",
                        "consequential actions are disabled for this run")


# ===========================================================================
# PART 6 — Task 4: the dispatcher
# ===========================================================================

def dispatch(step: Step, trace: Trace, allow_consequential: bool = True):
    tstep = TraceStep(step=len(trace.steps) + 1, tool=step.action,
                      args=step.args, thought=step.thought)
    spec = TOOLS.get(step.action)                      # gate 1
    if spec is None:
        tstep.ok, tstep.error, tstep.state_changed = False, "unknown_tool", False
        return err("unknown_tool", name=step.action,
                   hint=f"Available: {', '.join(sorted(TOOLS))}."), tstep
    tstep.tier = spec.tier.value

    try:
        gate_2_conforms(step.args, spec.args_model)
        gate_3_refers(step.args)
        gate_4_coheres(step.action, step.args, trace)
        require_tier(spec.tier, allow_consequential)
    except GateError as g:
        tstep.ok, tstep.error, tstep.state_changed = False, g.code, False
        return err(g.code, detail=g.detail), tstep

    result = spec.fn(**step.args)
    tstep.ok = bool(result.get("ok", False))
    tstep.error = result.get("error")
    tstep.state_changed = tstep.ok and step.action in STATE_CHANGING

    if step.action == "track_order" and tstep.ok:
        OBSERVED["days_late"] = result.get("days_late")

    return result, tstep


# ===========================================================================
# PART 7 — Task 5: the loop
# ===========================================================================
# NOTE: run() calls propose_step(SYSTEM, user), which needs the real model
# client from Part 4 of the notebook (tokenizer/model loaded on a GPU
# runtime). This file doesn't reimplement that part - paste this after the
# notebook's Part 4 cells, or import propose_step/SYSTEM from there, to
# actually execute a run.

def run(email: str, max_steps: int = 6, token_budget: int = 20_000,
        allow_consequential: bool = True, run_id: str = "run") -> Trace:
    OBSERVED["days_late"] = None
    trace = Trace(run_id=run_id)
    observations: list[str] = []
    user = f"CUSTOMER EMAIL:\n{email}\n\nYour next step:"
    last_call_signature = None

    for _ in range(max_steps):
        if trace.total_tokens >= token_budget:
            trace.stop = Stop(StopReason.CAPPED, detail="token budget exhausted")
            return trace

        step, raw, tokens = propose_step(SYSTEM, user)  # from notebook Part 4

        if step is None:
            trace.add(TraceStep(step=len(trace.steps) + 1, tokens=tokens))
            trace.stop = Stop(StopReason.MALFORMED,
                              detail="model could not produce a valid Step "
                                     "after retries")
            return trace

        if step.action == "final_answer":
            trace.add(TraceStep(step=len(trace.steps) + 1,
                                thought=step.thought, tokens=tokens))
            trace.stop = Stop(StopReason.COMPLETE,
                              answer=step.args.get("text", ""))
            return trace

        result, tstep = dispatch(step, trace, allow_consequential)
        tstep.tokens = tokens
        trace.add(tstep)

        if tstep.tool == "request_approval" and tstep.ok:
            trace.stop = Stop(StopReason.PENDING_APPROVAL,
                              answer=result.get("note"),
                              detail=result.get("approval_ref", ""))
            return trace
        if tstep.tool == "escalate_to_human" and tstep.ok:
            trace.stop = Stop(StopReason.ESCALATED,
                              answer=result.get("reason"))
            return trace

        obs = json.dumps(result)

        # no-progress detector: identical call+result as last time -> stop
        signature = (step.action, json.dumps(step.args, sort_keys=True), obs)
        if signature == last_call_signature:
            trace.stop = Stop(StopReason.CAPPED,
                              detail="no progress: repeated identical call")
            return trace
        last_call_signature = signature

        observations.append(obs)
        user = (f"CUSTOMER EMAIL:\n{email}\n\n"
                f"OBSERVATION from {step.action}: {obs}\n\nYour next step:")

    trace.stop = Stop(StopReason.CAPPED, detail="turn cap reached")
    return trace


# ===========================================================================
# Stretch — gate 5, output validation
# ===========================================================================

CLAIM_WORDS = ("applied", "refunded", "credited", "processed", "cancelled", "issued")
NEGATORS = ("nothing", "not ", "no ", "n't", "never", "yet", "pending", "without")


def _negated(t, i, w=60):
    return any(n in t[max(0, i - w):i] for n in NEGATORS)


def audit(trace: Trace) -> dict:
    tools = [s for s in trace.steps if s.tool]
    changed = [s for s in tools if s.state_changed]
    ans = (trace.stop.answer or "") if trace.stop else ""
    low = ans.lower()
    unsupported = []
    for w in CLAIM_WORDS:
        i = low.find(w)
        while i != -1:
            if not _negated(low, i):
                unsupported.append(w)
                break
            i = low.find(w, i + 1)
    return {"actions_attempted": [s.tool for s in tools],
            "actions_succeeded": [s.tool for s in tools if s.ok],
            "gate_refusals": [s.error for s in tools if s.ok is False],
            "state_changes": [s.tool for s in changed],
            "stop_reason": trace.stop.reason.value if trace.stop else None,
            "unsupported_claim_words": unsupported,
            "claim_is_supported": not unsupported or bool(changed),
            "steps_used": len(trace.steps),
            "approx_tokens": trace.total_tokens}


def gate_5_answer_supported(trace: Trace) -> None:
    """Raise unless the final answer is supported by the trace."""
    report = audit(trace)
    if not report["claim_is_supported"]:
        raise GateError(
            "gate5_unsupported_claim",
            f"final answer uses {report['unsupported_claim_words']} with no "
            "matching state change in the trace")
