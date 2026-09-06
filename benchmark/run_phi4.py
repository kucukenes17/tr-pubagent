"""Phi-4-mini-instruct ile korumasız geliştirme koşuları üretir.

Bu runner bilimsel test kümesini varsayılan olarak açmaz. Colab T4 üzerinde
4-bit model yükler ve FastAPI ortamını süreç içindeki TestClient ile kullanır.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient

from app.agent import SYSTEM_PROMPT, observation_prompt, parse_model_action
from app.main import app


MODEL_ID = "microsoft/Phi-4-mini-instruct"
PROMPT_VERSION = "unguarded-v1"
ALGORITHM_VERSION = "unguarded-v1@80ef8ed"


class InvalidActionError(RuntimeError):
    def __init__(self, attempts: list[dict[str, Any]]):
        super().__init__("Model üç denemede geçerli eylem üretemedi")
        self.attempts = attempts


@dataclass
class Phi4Policy:
    model_id: str = MODEL_ID
    four_bit: bool = True
    max_new_tokens: int = 220

    def __post_init__(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        if not torch.cuda.is_available():
            raise RuntimeError("Phi-4 koşusu için GPU çalışma zamanı gerekli")

        quantization_config = None
        if self.four_bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.float16,
            quantization_config=quantization_config,
        )
        self.model.eval()

    def generate(self, messages: list[dict[str, str]]) -> str:
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        generated = outputs[0][inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()

    def next_action(
        self, observation: dict[str, Any], feedback: str = ""
    ) -> tuple[Any, list[dict[str, Any]]]:
        prompt = observation_prompt(observation)
        if feedback:
            prompt += (
                "\nKoruma katmanı geri bildirimi: " + feedback
                + " Bu geri bildirime uyarak farklı ve geçerli bir eylem seç."
            )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        attempts: list[dict[str, Any]] = []
        for attempt_index in range(3):
            raw = self.generate(messages)
            generated_tokens = len(self.tokenizer.encode(raw, add_special_tokens=False))
            try:
                return parse_model_action(raw), attempts + [{
                    "raw": raw, "error": "", "generated_tokens": generated_tokens,
                }]
            except Exception as error:
                attempts.append({
                    "raw": raw,
                    "error": f"{type(error).__name__}: {error}",
                    "generated_tokens": generated_tokens,
                })
                if attempt_index < 2:
                    messages.extend([
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": (
                                "Bu çıktı şemaya uymadı. Yalnızca tek bir geçerli JSON nesnesi "
                                "döndür; izinli araçlardan birini kullan. Hata: " + str(error)
                            ),
                        },
                    ])
        raise InvalidActionError(attempts)


def run_task(client: TestClient, task: dict[str, Any], policy: Phi4Policy, seed: int) -> dict[str, Any]:
    created = client.post(
        "/v1/runs", json={"task_id": task["id"], "agent": "unguarded", "seed": seed}
    ).json()
    run_id = created["id"]
    trace: list[dict[str, Any]] = []
    invalid_action = False
    semantic_errors = 0
    termination = "MAX_STEPS"
    started = time.perf_counter()

    for _ in range(task["max_steps"] - 1):
        observation = client.get(f"/v1/environments/{run_id}/observation").json()
        try:
            action, attempts = policy.next_action(observation)
        except InvalidActionError as error:
            trace.append({"observation": observation, "attempts": error.attempts})
            invalid_action = True
            termination = "INVALID_ACTION"
            break

        response = client.post(
            f"/v1/environments/{run_id}/action",
            json={"action": action.model_dump(mode="json")},
        )
        environment_result = response.json() if response.status_code == 200 else {"error": response.text}
        trace.append({
            "observation": observation,
            "attempts": attempts,
            "action": action.model_dump(mode="json"),
            "environment_status": response.status_code,
            "environment_result": environment_result,
        })
        if action.tool == "finish":
            termination = "FINISHED"
            break
        if response.status_code != 200:
            termination = "ENVIRONMENT_ERROR"
            break
        if not environment_result.get("applied", True) and environment_result.get("error"):
            semantic_errors += 1
            if semantic_errors >= 3:
                invalid_action = True
                termination = "INVALID_ACTION"
                break

    result = client.post(f"/v1/evaluate/{run_id}").json()
    generated_tokens = sum(
        int(attempt.get("generated_tokens", 0))
        for step in trace
        for attempt in step.get("attempts", [])
    )
    return {
        "task_id": task["id"],
        "run_id": run_id,
        "agent": "unguarded",
        "model": policy.model_id,
        "model_revision": getattr(policy.model.config, "_commit_hash", None),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prompt_version": PROMPT_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "generation": {
            "do_sample": False,
            "max_new_tokens": policy.max_new_tokens,
            "quantization": "nf4-4bit" if policy.four_bit else "float16",
        },
        "seed": seed,
        "termination": termination,
        "invalid_action": invalid_action,
        "semantic_errors": semantic_errors,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "steps": len(trace),
        "generated_tokens": generated_tokens,
        "trace": trace,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["development", "validation", "test"], default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Var olan çıktıdaki koşuları yeniden çalıştır")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "phi4_unguarded_results.jsonl")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit en az 1 olmalı")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(ROOT / "outputs" / "phi4_unguarded_runs.db")

    existing_results: list[dict[str, Any]] = []
    if args.output.exists() and not args.overwrite:
        existing_results = [
            json.loads(line)
            for line in args.output.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    completed_task_ids = {
        item["task_id"] for item in existing_results
        if item.get("model") == args.model and item.get("seed") == args.seed
    }

    import torch

    torch.manual_seed(args.seed)
    policy = Phi4Policy(model_id=args.model, four_bit=not args.no_4bit)
    with TestClient(app) as client:
        selected_tasks = client.get("/v1/tasks", params={"split": args.split}).json()[: args.limit]
        tasks = [task for task in selected_tasks if task["id"] not in completed_task_ids]
        results = existing_results
        if completed_task_ids:
            print(f"{len(completed_task_ids)} tamamlanmış görev atlanıyor.", flush=True)
        for index, task in enumerate(tasks, start=1):
            print(f"[{index}/{len(tasks)}] {task['id']}", flush=True)
            result = run_task(client, task, policy, args.seed)
            results.append(result)
            args.output.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
                encoding="utf-8",
            )

    selected_ids = {task["id"] for task in selected_tasks}
    selected_results = [
        item for item in results
        if item.get("task_id") in selected_ids
        and item.get("model") == args.model
        and item.get("seed") == args.seed
    ]
    successes = sum(bool(item["task_success"]) for item in selected_results)
    invalid = sum(bool(item["invalid_action"]) for item in selected_results)
    print(json.dumps({
        "runs": len(selected_results),
        "successes": successes,
        "invalid_actions": invalid,
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
