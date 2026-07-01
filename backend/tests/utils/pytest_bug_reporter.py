import pytest

from .bug_reporter import BugReport

reports: list[BugReport] = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):  # type: ignore[no-untyped-def]
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        module_parts = item.nodeid.split("::")[0].split("/")
        module = module_parts[-2] if len(module_parts) >= 2 else module_parts[0]

        report = BugReport(
            title=f"Test failure: {item.nodeid}",
            module=module,
        )
        report.add_step(f"Run test: {item.nodeid}")
        report.set_expected("The test should pass successfully")

        if hasattr(rep, "longreprtext"):
            report.set_actual(rep.longreprtext[:500])
        elif hasattr(rep, "longrepr"):
            report.set_actual(str(rep.longrepr)[:500])
        else:
            report.set_actual("Unknown error")

        report.set_stack_trace()

        if hasattr(item, "callspec"):
            params = item.callspec.params
            if params:
                report.set_test_data(params)

        reports.append(report)


@pytest.fixture
def bug_reporter():
    def create_report(title: str, test_data=None) -> BugReport:
        report = BugReport(title=title, module="custom")
        if test_data:
            report.set_test_data(test_data)
        reports.append(report)
        return report

    return create_report


def save_reports() -> list[str]:
    if not reports:
        return []

    return [report.save_markdown() for report in reports]


def get_report_summary() -> str:
    if not reports:
        return "No bug reports. All tests passed successfully."

    summary = [f"Found {len(reports)} bug reports", ""]
    modules: dict[str, list[BugReport]] = {}

    for report in reports:
        modules.setdefault(report.module, []).append(report)

    for module, module_reports in modules.items():
        summary.append(f"Module: {module}")
        for index, report in enumerate(module_reports, start=1):
            summary.append(f"  {index}. {report.title}")
        summary.append("")

    return "\n".join(summary)


def pytest_sessionfinish(session):  # type: ignore[no-untyped-def]
    del session
    if reports:
        saved_files = save_reports()
        print("\n" + "=" * 70)
        print("BUG REPORT SUMMARY")
        print("=" * 70)
        print(get_report_summary())
        print("\nSaved report files:")
        for file in saved_files:
            print(f"  {file}")
        print("=" * 70)
    else:
        print("\nAll tests passed successfully. No bug reports.")
