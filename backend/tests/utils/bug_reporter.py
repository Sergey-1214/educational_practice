import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


class BugReport:
    """Utility object for saving structured test failure reports."""

    def __init__(self, title: str, module: str = "unknown"):
        self.title = title
        self.module = module
        self.timestamp = datetime.now()
        self.data = {
            "title": title,
            "module": module,
            "timestamp": self.timestamp.isoformat(),
            "description": "",
            "steps_to_reproduce": [],
            "expected_behavior": "",
            "actual_behavior": "",
            "test_data": "",
            "stack_trace": "",
            "environment": self._get_environment(),
        }

    def _get_environment(self) -> dict[str, str]:
        import platform

        env = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        }

        try:
            import fastapi

            env["fastapi_version"] = fastapi.__version__
        except Exception:
            pass

        try:
            import pydantic

            env["pydantic_version"] = pydantic.__version__
        except Exception:
            pass

        try:
            import sqlalchemy

            env["sqlalchemy_version"] = sqlalchemy.__version__
        except Exception:
            pass

        return env

    def set_description(self, description: str) -> "BugReport":
        self.data["description"] = description
        return self

    def add_step(self, step: str) -> "BugReport":
        self.data["steps_to_reproduce"].append(step)
        return self

    def set_expected(self, expected: str) -> "BugReport":
        self.data["expected_behavior"] = expected
        return self

    def set_actual(self, actual: str) -> "BugReport":
        self.data["actual_behavior"] = actual
        return self

    def set_test_data(self, data: Any) -> "BugReport":
        if isinstance(data, (dict, list)):
            self.data["test_data"] = json.dumps(data, indent=2, default=str)
        else:
            self.data["test_data"] = str(data)
        return self

    def set_stack_trace(self, exc_info=None) -> "BugReport":
        if exc_info:
            self.data["stack_trace"] = "".join(traceback.format_exception(*exc_info))
        else:
            self.data["stack_trace"] = traceback.format_exc()
        return self

    def save_markdown(self, directory: str = "bug_reports") -> str:
        report_dir = Path(directory)
        report_dir.mkdir(exist_ok=True)

        timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            char for char in self.title if char.isalnum() or char in " _-"
        )[:50]
        filename = f"{timestamp}_{self.module}_{safe_title}.md"
        filepath = report_dir / filename

        md: list[str] = [
            f"# Bug Report: {self.title}",
            "",
            f"**Module:** {self.module}",
            f"**Time:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if self.data["description"]:
            md.extend(["## Description", self.data["description"], ""])

        if self.data["steps_to_reproduce"]:
            md.append("## Steps To Reproduce")
            for index, step in enumerate(self.data["steps_to_reproduce"], start=1):
                md.append(f"{index}. {step}")
            md.append("")

        if self.data["expected_behavior"]:
            md.extend(["## Expected Behavior", self.data["expected_behavior"], ""])

        if self.data["actual_behavior"]:
            md.extend(["## Actual Behavior", self.data["actual_behavior"], ""])

        if self.data["test_data"]:
            md.extend(
                [
                    "## Test Data",
                    "```",
                    self.data["test_data"][:1000],
                    "```",
                    "",
                ]
            )

        if self.data["stack_trace"]:
            md.extend(
                [
                    "## Stack Trace",
                    "```python",
                    self.data["stack_trace"],
                    "```",
                    "",
                ]
            )

        if self.data["environment"]:
            md.append("## Environment")
            for key, value in self.data["environment"].items():
                md.append(f"- **{key}:** {value}")

        with open(filepath, "w", encoding="utf-8") as file:
            file.write("\n".join(md))

        return str(filepath)
