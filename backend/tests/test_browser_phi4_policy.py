from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from benchmark.run_browser_phi4 import Phi4BrowserPolicy


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        return text.split()


class FakeBasePolicy:
    def __init__(self):
        self.tokenizer = FakeTokenizer()
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return '{"tool":"finish","target_id":"task","arguments":{}}'


def test_phi4_browser_policy_prompts_from_public_dom_observation_only():
    base = FakeBasePolicy()
    policy = Phi4BrowserPolicy(base)
    action, metadata = policy.next_action(
        "BUR-005",
        {
            "aria_tree": '- button "Görevi bitir [task]"',
            "page_title": "Burs",
            "visible_messages": [],
            "step": 1,
            "status": "running",
            "oracle": {"must_not_leak": True},
            "authorization": {"must_not_leak": True},
            "state": {"must_not_leak": True},
        },
    )
    prompt = base.messages[-1]["content"]
    assert action.tool == "finish"
    assert action.target_id == "task"
    assert metadata["generated_tokens"] > 0
    assert "aria_tree" in prompt
    assert "must_not_leak" not in prompt
    assert '"oracle":' not in prompt
    assert '"authorization":' not in prompt
