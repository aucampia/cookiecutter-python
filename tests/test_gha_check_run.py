"""Cover the two failure paths a normal CI run never reaches.

`devtools/gha-check-run.py` only misbehaves when the GitHub API refuses a
write - a fork PR's read-only token, or a transient error. Neither happens on
an ordinary run, so both are pinned down here instead.
"""

from __future__ import annotations

import email.message
import importlib.util
import json
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent
MODULE_PATH = PROJECT_PATH / "link_project" / "devtools" / "gha-check-run.py"

SARIF_WITH_ONE_RESULT = json.dumps(
    {
        "runs": [
            {
                "results": [
                    {
                        "ruleId": "some-rule",
                        "level": "error",
                        "message": {"text": "a finding"},
                    }
                ]
            }
        ]
    }
)


def load_module() -> ModuleType:
    """Import the script despite its hyphenated, non-importable filename."""
    spec = importlib.util.spec_from_file_location("gha_check_run", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves its stringified annotations
    # (from __future__ import annotations) via sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="module")
def module_fixture() -> ModuleType:
    return load_module()


def emit_sarif_command(sarif: str) -> list[str]:
    """A command that prints `sarif` to stdout and exits 0, like zizmor does."""
    return [sys.executable, "-c", f"import sys; sys.stdout.write({sarif!r})"]


@pytest.mark.parametrize("output_is_sarif", [True, False])
def test_unreported_run_still_fails_on_sarif_findings(
    module: ModuleType, output_is_sarif: bool
) -> None:
    """SARIF findings must fail the build with no check run to publish to.

    zizmor exits 0 even when it found something, so without deriving the exit
    code from the SARIF body a fork PR passes validation despite findings.
    """
    exit_code = module._run_unreported(
        "zizmor",
        emit_sarif_command(SARIF_WITH_ONE_RESULT),
        output_is_sarif=output_is_sarif,
    )
    assert exit_code == (1 if output_is_sarif else 0)


def test_forbidden_check_run_creation_still_derives_exit_code(
    module: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A 403 from the check-runs API must not downgrade to a bare passthrough."""

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise urllib.error.HTTPError(
            "https://api.github.com", 403, "Forbidden", email.message.Message(), None
        )

    monkeypatch.setattr(module, "_create_check_run", forbidden)
    env = module.Env.from_os_environ()
    exit_code = module._run_reported(
        env,
        "zizmor",
        emit_sarif_command(SARIF_WITH_ONE_RESULT),
        output_is_sarif=True,
    )
    assert exit_code == 1


def test_failed_completion_is_retried_by_finalize(
    module: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A completion the API rejected must be retried, not treated as done.

    Otherwise the check run stays `in_progress` forever and blocks the PR.
    """
    state_path = tmp_path / "state.jsonl"
    monkeypatch.setenv("GHA_CHECK_STATE", str(state_path))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GHA_CHECK_HEAD_SHA", "deadbeef")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GHA_CHECK_DRY_RUN", raising=False)

    monkeypatch.setattr(module, "_create_check_run", lambda *a, **k: 4242)

    def failing_complete(*args: Any, **kwargs: Any) -> None:
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(module, "_complete_check_run", failing_complete)

    env = module.Env.from_os_environ()
    module._run_reported(env, "mypy", [sys.executable, "-c", ""])

    record = json.loads(state_path.read_text().splitlines()[-1])
    assert record["event"] == "complete"
    assert record["reported"] is False

    calls: list[tuple[str, str, dict[str, Any]]] = []

    def record_call(
        env: Any, method: str, path: str, payload: dict[str, Any], **kwargs: Any
    ) -> None:
        calls.append((method, path, payload))

    monkeypatch.setattr(module, "_api_call", record_call)
    module.cmd_finalize(object())

    assert calls == [
        (
            "PATCH",
            "/check-runs/4242",
            {
                "name": "mypy",
                "head_sha": "deadbeef",
                "status": "completed",
                "conclusion": "success",
                "completed_at": record["completed_at"],
            },
        )
    ]


def test_successful_completion_is_not_retried(
    module: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The happy path must not double-PATCH every check run in finalize."""
    state_path = tmp_path / "state.jsonl"
    monkeypatch.setenv("GHA_CHECK_STATE", str(state_path))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GHA_CHECK_HEAD_SHA", "deadbeef")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GHA_CHECK_DRY_RUN", raising=False)

    monkeypatch.setattr(module, "_create_check_run", lambda *a, **k: 4242)
    monkeypatch.setattr(module, "_complete_check_run", lambda *a, **k: None)

    env = module.Env.from_os_environ()
    module._run_reported(env, "mypy", [sys.executable, "-c", ""])

    assert json.loads(state_path.read_text().splitlines()[-1])["reported"] is True

    calls: list[str] = []

    def record_call(*args: Any, **kwargs: Any) -> None:
        calls.append("called")

    monkeypatch.setattr(module, "_api_call", record_call)
    module.cmd_finalize(object())
    assert calls == []
