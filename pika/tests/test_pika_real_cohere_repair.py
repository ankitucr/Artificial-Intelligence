import asyncio
import json
import tempfile
from pathlib import Path

import requests
from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller

async def main():
    events = []
    original_post = requests.post

    def tracked_post(url, *args, **kwargs):
        if "api.cohere.com" in str(url):
            event = {"url": str(url), "attempted": True}
            events.append(event)
            print("[TRACE] REAL COHERE HTTP REQUEST ATTEMPTED")
            try:
                response = original_post(url, *args, **kwargs)
                event["http_status"] = response.status_code
                print(f"[TRACE] COHERE HTTP STATUS: {response.status_code}")
                return response
            except Exception as exc:
                event["error"] = type(exc).__name__ + ": " + str(exc)[:250]
                print("[TRACE] COHERE NETWORK ERROR:", event["error"])
                raise
        return original_post(url, *args, **kwargs)

    requests.post = tracked_post
    try:
        with tempfile.TemporaryDirectory(prefix="pika_cohere_repair_") as tmp:
            root = Path(tmp)
            (root / "calc.py").write_text(
                "def calculate_total(a, b):\n    return a - b\n",
                encoding="utf-8",
            )
            (root / "test_calc.py").write_text(
                "from calc import calculate_total\n"
                "assert calculate_total(10, 5) == 15\n"
                "print('INDEPENDENT_TEST_PASS')\n",
                encoding="utf-8",
            )

            task = (
                "Fix calculate_total in calc.py. It must add a and b, "
                "not subtract them. The test expects calculate_total(10, 5) == 15."
            )
            diagnosis = {
                "error_type": "test_failure",
                "root_cause": "calculate_total subtracts instead of adding",
                "error_message": "Expected 15 but got 5",
            }
            worker_output = {
                "files": [{
                    "path": "calc.py",
                    "content": "def calculate_total(a, b):\n    return a - b\n",
                }],
                "commands": [["python", "test_calc.py"]],
            }

            print("=== REAL COHERE REPAIR TASK ===")
            generator = RepairCandidateGenerator(
                max_candidates=3, workspace_root=root
            )
            generated = await generator.generate_from_failure(
                task=task,
                diagnosis=diagnosis,
                worker_output=worker_output,
            )

            print("GENERATOR_SUCCESS:", generated.get("success"))
            print("GENERATOR_STAGE:", generated.get("stage", "generation"))
            print("GENERATOR_ERROR:", generated.get("error", "(none)")[:500]
                  if isinstance(generated.get("error", "(none)"), str)
                  else "(none)")
            print("COHERE_HTTP_REQUESTS:", len(events))
            for event in events:
                print("COHERE_HTTP_STATUS:", event.get("http_status", "no response"))
                if event.get("error"):
                    print("COHERE_REQUEST_ERROR:", event["error"])

            if not events:
                print("RESULT: COHERE WAS NOT CALLED; inspect generator validation/key configuration.")
                return

            if not generated.get("success"):
                print("RESULT: COHERE request was attempted, but no validated repair candidate was produced.")
                return

            print("PROVIDER:", generated.get("provider", "Cohere client default"))
            print("MODEL:", generated.get("model", "Cohere client default"))
            print("CANDIDATES_RETURNED:", len(generated.get("candidates", [])))

            controller = Phase33Controller(root, max_candidates=3)
            repaired = controller.repair(
                diagnosis=diagnosis,
                relative_path=generated["target_path"],
                old_text=generated["old_text"],
                candidates=generated["candidates"],
                test_path=generated["test_path"],
                task=task,
            )
            print("PHASE33_SUCCESS:", repaired.get("success"))
            print("INDEPENDENT_TEST_PASSED:", repaired.get("test_passed"))
            print("COMMIT_CONFIRMED:", bool(
                repaired.get("repair", {}).get("commit_passed")
            ))
            print("REPAIR_STAGE:", repaired.get("stage"))
            print("REPAIR_ERROR:", repaired.get("error", "(none)"))

            final_source = (root / "calc.py").read_text(encoding="utf-8")
            print("FINAL_SOURCE:", repr(final_source))
            if repaired.get("success") and "return a + b" in final_source:
                print("RESULT: REAL COHERE CANDIDATE SOLVED THE TASK AND PHASE 33 VERIFIED IT.")
            else:
                print("RESULT: COHERE WAS TRACED; THE REPAIR DID NOT COMPLETE SUCCESSFULLY.")
            print("SAFETY: temporary workspace only; production files unchanged.")
    finally:
        requests.post = original_post

if __name__ == "__main__":
    asyncio.run(main())
