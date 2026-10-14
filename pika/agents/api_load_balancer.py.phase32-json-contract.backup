import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from .base import Agent


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class APILoadBalancer:

    PROVIDER = "cohere"
    MODEL = "command-a-03-2025"
    URL = "https://api.cohere.com/v2/chat"

    def __init__(self):
        self.api_key = os.getenv("COHERE_API_KEY")

    async def ask(
        self,
        prompt: str,
        system: str | None = None,
        role: str = "general",
        structured: bool = False,
    ) -> dict[str, Any]:

        if not self.api_key:
            return {
                "success": False,
                "provider": self.PROVIDER,
                "model": self.MODEL,
                "error": "COHERE_API_KEY not found in ~/pika/.env",
                "text": "",
            }

        messages = []

        if system:
            messages.append({
                "role": "system",
                "content": system,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        payload = {
            "model": self.MODEL,
            "messages": messages,
            "max_tokens": 1500,
        }

        # Workspace execution requires machine-readable JSON.
        if structured:
            payload["response_format"] = {
                "type": "json_object",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        mode = "JSON" if structured else "TEXT"

        print(
            f"[API WORKER] Cohere / {self.MODEL} / mode={mode}"
        )

        started = time.time()

        try:
            response = requests.post(
                self.URL,
                headers=headers,
                json=payload,
                timeout=60,
            )

            latency = round(
                time.time() - started,
                3,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "provider": self.PROVIDER,
                    "model": self.MODEL,
                    "latency": latency,
                    "status_code": response.status_code,
                    "error": response.text[:1000],
                    "text": "",
                }

            data = response.json()

            text = self._extract(data)

            if not text:
                return {
                    "success": False,
                    "provider": self.PROVIDER,
                    "model": self.MODEL,
                    "latency": latency,
                    "error": "Empty response from Cohere",
                    "text": "",
                }

            print(
                f"[API WORKER] SUCCESS "
                f"provider={self.PROVIDER} "
                f"model={self.MODEL} "
                f"mode={mode} "
                f"latency={latency}s"
            )

            return {
                "success": True,
                "provider": self.PROVIDER,
                "model": self.MODEL,
                "latency": latency,
                "text": text,
                "raw": data,
            }

        except Exception as exc:
            return {
                "success": False,
                "provider": self.PROVIDER,
                "model": self.MODEL,
                "error": str(exc),
                "text": "",
            }

    @staticmethod
    def _extract(
        data: dict[str, Any],
    ) -> str | None:

        try:
            content = data["message"]["content"]

            if isinstance(content, list):
                for item in content:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "text"
                    ):
                        return item.get("text")

            if isinstance(content, str):
                return content

        except (KeyError, IndexError, TypeError):
            pass

        return None


class APILoadBalancerAgent(Agent):

    name = "api"

    capabilities = [
        "coding",
        "reasoning",
        "generation",
        "analysis",
        "planning",
        "debugging",
    ]

    def __init__(self):
        self.worker = APILoadBalancer()

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        context = context or {}

        role = context.get(
            "role",
            "general",
        )

        plan = context.get(
            "plan",
            [],
        )

        memory = context.get(
            "memory",
            {},
        )

        attempt = context.get(
            "attempt",
            1,
        )

        max_attempts = context.get(
            "max_attempts",
            1,
        )

        previous_feedback = context.get(
            "previous_feedback",
            "",
        )

        workspace = context.get(
            "workspace",
        )

        # Workspace tasks must return strict JSON because
        # PIKA executes the returned files/commands automatically.
        structured = isinstance(workspace, dict)

        if structured:
            system = """
You are the API worker inside PIKA.

PIKA Brain decides WHAT needs to be done.
You execute the assigned task.

WORKSPACE EXECUTION MODE IS ACTIVE.

CRITICAL OUTPUT RULES:
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT use ```json.
- Do NOT use ```python.
- Do NOT add explanations before or after the JSON.
- Do NOT return prose.
- Do NOT claim files were created unless they are represented in the JSON.
- Do NOT claim tests were run unless PIKA actually runs them.
- Every file must contain its COMPLETE final content.
- Paths must be relative to the PIKA workspace.
- Commands must be arrays of command arguments.
- Never use shell syntax.
- Follow the exact JSON structure below.

Required JSON structure:

{
  "files": [
    {
      "path": "relative/path.py",
      "content": "complete file content"
    }
  ],
  "commands": [
    ["python", "relative/path.py"]
  ]
}

If no files are required, return:
{
  "files": [],
  "commands": []
}

If tests need to be run, put the test command in "commands".
Do not describe the test result in prose.

The JSON must be directly parseable by Python json.loads().
"""

        else:
            system = """
You are the API worker inside PIKA.

PIKA Brain decides WHAT needs to be done.
You execute the assigned task.

Rules:
- Do not claim code was tested unless it was actually tested.
- Be precise.
- Prefer working solutions.
- Follow the requested output format.
- If the task asks for code only, return only the code.
- Do not add explanations unless requested.
- If previous evaluator feedback is provided, correct the
  identified problem instead of repeating the same mistake.
"""

        prompt = f"""
TASK:
{task}

ROLE:
{role}

PLAN:
{plan}

RELEVANT MEMORY:
{memory}

CURRENT ATTEMPT:
{attempt}/{max_attempts}

PREVIOUS EVALUATOR FEEDBACK:
{previous_feedback or "None. This is the first attempt."}
"""

        if structured:
            prompt += f"""

WORKSPACE STATE:
{workspace}

You are operating against the real PIKA workspace.

Execute the task by returning the complete file changes and
commands PIKA should execute.

IMPORTANT:
Return ONLY the required JSON object.
"""

        else:
            prompt += """

Execute the task now.
"""

        result = await self.worker.ask(
            prompt=prompt,
            system=system,
            role=role,
            structured=structured,
        )

        return {
            "success": result.get(
                "success",
                False,
            ),
            "agent": self.name,
            "provider": result.get(
                "provider"
            ),
            "model": result.get(
                "model"
            ),
            "output": result.get(
                "text",
                "",
            ),
            "latency": result.get(
                "latency"
            ),
            "error": result.get(
                "error"
            ),
            "raw": result,
        }
