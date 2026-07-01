import pytest
from .bug_reporter import BugReport
from pathlib import Path

# Глобальный коллектор отчетов
reports = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Перехват падающих тестов"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Определяем модуль из пути теста
        module_parts = item.nodeid.split("::")[0].split("/")
        module = module_parts[-2] if len(module_parts) >= 2 else module_parts[0]
        
        # Создаем отчет
        report = BugReport(
            title=f"Ошибка в тесте: {item.nodeid}",
            module=module
        )
        
        # Добавляем шаги
        report.add_step(f"Запустить тест: {item.nodeid}")
        report.set_expected("Тест должен пройти успешно")
        
        # Получаем информацию об ошибке
        if hasattr(rep, 'longreprtext'):
            report.set_actual(rep.longreprtext[:500])  # Ограничиваем длину
        elif hasattr(rep, 'longrepr'):
            report.set_actual(str(rep.longrepr)[:500])
        else:
            report.set_actual("Неизвестная ошибка")
        
        report.set_stack_trace()
        
        # Добавляем параметры теста если есть
        if hasattr(item, 'callspec'):
            params = item.callspec.params
            if params:
                report.set_test_data(params)
        
        reports.append(report)


@pytest.fixture
def bug_reporter():
    """Фикстура для создания баг-репортов в тестах"""
    def create_report(title: str, test_data=None) -> BugReport:
        report = BugReport(title=title, module="custom")
        if test_data:
            report.set_test_data(test_data)
        reports.append(report)
        return report
    return create_report


def save_reports():
    """Сохранить все отчеты"""
    if not reports:
        return []
    
    saved_files = []
    for report in reports:
        saved_files.append(report.save_markdown())
    return saved_files


def get_report_summary() -> str:
    """Получить сводку по отчетам"""
    if not reports:
        return "Баг-репортов нет. Все тесты прошли успешно!"
    
    summary = f"Найдено {len(reports)} баг-репортов\n\n"
    
    # Группировка по модулям
    modules = {}
    for report in reports:
        module = report.module
        if module not in modules:
            modules[module] = []
        modules[module].append(report)
    
    for module, module_reports in modules.items():
        summary += f"Модуль: {module}\n"
        for i, report in enumerate(module_reports, 1):
            summary += f"   {i}. {report.title}\n"
        summary += "\n"
    
    return summary


def pytest_sessionfinish(session):
    """Сохранить отчеты после завершения сессии"""
    if reports:
        saved_files = save_reports()
        
        print(f"\n{'='*70}")
        print("ОТЧЕТ ПО БАГАМ")
        print('='*70)
        print(get_report_summary())
        print("\nФайлы отчетов:")
        for file in saved_files:
            print(f"   {file}")
        print('='*70)
    else:
        print("\nВсе тесты прошли успешно! Баг-репортов нет.")