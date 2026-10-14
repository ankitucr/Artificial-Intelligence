import asyncio
import inspect
import json
import os
import shutil
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from core.brain import PIKABrain
from core.runtime import create_runtime, create_tool_runtime
from core.planner import Planner
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


async def main():
    workspace = ROOT / "workspace"
    workspace.mkdir(exist_ok=True)
    testdir = Path(tempfile.mkdtemp(prefix="pika_real_repair_"))
    events = []
    original_post = requests.post

    def tracked_post(url, *args, **kwargs):
        if "api.cohere.com" in str(url):
            event = {"attempted": True}
            events.append(event)
            print("\n[TRACE] COHERE HTTP REQUEST ATTEMPTED")
            try:
                response = original_post(url, *args, **kwargs)
                event["http_status"] = response.status_code
                print("[TRACE] COHERE HTTP STATUS:", response.status_code)
                return response
            except Exception as exc:
                event["error"] = type(exc).__name__ + ": " + str(exc)[:180]
                print("[TRACE] COHERE NETWORK ERROR:", event["error"])
                raise
        return original_post(url, *args, **kwargs)

    try:
        if not os.getenv("COHERE_API_KEY"):
            print("[BLOCKED] COHERE_API_KEY .env mein nahi mili.")
            return

        # Use a unique subdirectory under the real controlled workspace.
        target = workspace / testdir.name
        target.mkdir(parents=True, exist_ok=False)
        (target / "calc.py").write_text(
            "def calculate_total(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (target / "test_calc.py").write_text(
            "from calc import calculate_total\n"
            "assert calculate_total(10, 5) == 15\n"
            "print('INDEPENDENT_TEST_PASS')\n",
            encoding="utf-8",
        )

        print("[SETUP] Wrong code:", (target / "calc.py").read_text().strip())
        print("[SETUP] Expected: calculate_total(10, 5) == 15")
        print("[SETUP] Test folder:", target)

        # Phase 33 expects paths relative to workspace root.
        relative_target = str((target / "calc.py").relative_to(workspace))
        relative_test = str((target / "test_calc.py").relative_to(workspace))
        old_text = (target / "calc.py").read_text()

        router = create_runtime()
        tool_runtime = create_tool_runtime()
        brain = PIKABrain(
            router=router,
            memory=MemoryManager(),
            planner=Planner(),
            evaluator=Evaluator(),
            experience=ExperienceEngine(),
            tool_runtime=tool_runtime,
            max_retries=1,
        )

        print("[BRAIN] Initialized:", type(brain).__name__)
        print("[BRAIN] Phase 33 available:", brain.phase33_controller is not None)
        print("[BRAIN] Cohere generator available:", brain.repair_candidate_generator is not None)

        # Call the same generator used by the Brain's Phase 33 fallback.
        diagnosis = {
            "error_type": "test_failure",
            "root_cause": "calculate_total subtracts instead of adding",
            "error_message": "Expected 15 but got 5",
        }
        worker_output = {
            "files": [{"path": relative_target, "content": old_text}],
            "commands": [["python", relative_test]],
        }
        requests.post = tracked_post
        generated = await brain.repair_candidate_generator.generate_from_failure(
            task=(
                "Fix calculate_total in calc.py. It must return a + b, "
                "not a - b. The independent test expects 15 for inputs 10 and 5."
            ),
            diagnosis=diagnosis,
            worker_output=worker_output,
        )

        print("\n[GENERATION SUCCESS]:", generated.get("success"))
        print("[GENERATION STAGE]:", generated.get("stage"))
        print("[GENERATION ERROR]:", generated.get("error"))
        print("[COHERE REQUEST COUNT]:", len(events))

        if not generated.get("success"):
            print("[RESULT] Cohere did not provide a validated repair candidate.")
            return

        candidates = generated.get("candidates", [])
        print("[CANDIDATE COUNT]:", len(candidates))

        repaired = brain.phase33_controller.repair(
            diagnosis=diagnosis,
            relative_path=relative_target,
            old_text=generated.get("old_text", old_text),
            candidates=candidates,
            test_path=relative_test,
            task="Repair calculate_total so it adds two numbers.",
        )
        print("\n[PHASE33 SUCCESS]:", repaired.get("success"))
        print("[PHASE33 STAGE]:", repaired.get("stage"))
        print("[INDEPENDENT TEST PASSED]:", repaired.get("test_passed"))
        print("[REPAIR DETAILS]:", json.dumps(repaired, ensure_ascii=False, default=str)[:2500])
        print("[FINAL SOURCE]:")
        print((target / "calc.py").read_text())

        passed = repaired.get("success") is True and repaired.get("test_passed") is True
        print("\n[FINAL VERDICT]:", "PASS" if passed else "FAIL")
        print("[REAL COHERE REQUEST]:", bool(events))
        print("[TEMP TEST DIRECTORY]:", target)

    finally:
        requests.post = original_post
        print("\n[NOTE] Temporary test directory is retained for inspection.")
        print("TERMUX SHELL WILL REMAIN OPEN")


if __name__ == "__main__":
    asyncio.run(main())
