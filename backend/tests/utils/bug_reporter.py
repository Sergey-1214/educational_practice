import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys


class BugReport:
    """Класс для создания структурированных баг-репортов"""
    
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
            "environment": self._get_environment()
        }
    
    def _get_environment(self) -> Dict[str, str]:
        """Получить информацию об окружении"""
        import platform
        
        env = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "platform": platform.platform()
        }
        
        # Попытка получить версии библиотек
        try:
            import fastapi
            env["fastapi_version"] = fastapi.__version__
        except:
            pass
        
        try:
            import pydantic
            env["pydantic_version"] = pydantic.__version__
        except:
            pass
        
        try:
            import sqlalchemy
            env["sqlalchemy_version"] = sqlalchemy.__version__
        except:
            pass
        
        return env
    
    def set_description(self, description: str) -> 'BugReport':
        self.data["description"] = description
        return self
    
    def add_step(self, step: str) -> 'BugReport':
        self.data["steps_to_reproduce"].append(step)
        return self
    
    def set_expected(self, expected: str) -> 'BugReport':
        self.data["expected_behavior"] = expected
        return self
    
    def set_actual(self, actual: str) -> 'BugReport':
        self.data["actual_behavior"] = actual
        return self
    
    def set_test_data(self, data: Any) -> 'BugReport':
        if isinstance(data, (dict, list)):
            self.data["test_data"] = json.dumps(data, indent=2, default=str)
        else:
            self.data["test_data"] = str(data)
        return self
    
    def set_stack_trace(self, exc_info=None) -> 'BugReport':
        if exc_info:
            self.data["stack_trace"] = "".join(traceback.format_exception(*exc_info))
        else:
            self.data["stack_trace"] = traceback.format_exc()
        return self
    
    def save_markdown(self, directory: str = "bug_reports") -> str:
        """Сохранить отчет в формате Markdown"""
        report_dir = Path(directory)
        report_dir.mkdir(exist_ok=True)
        
        timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in self.title if c.isalnum() or c in " _-")[:50]
        filename = f"{timestamp}_{self.module}_{safe_title}.md"
        filepath = report_dir / filename
        
        md = []
        md.append(f"# Баг-репорт: {self.title}")
        md.append("")
        md.append(f"**Модуль:** {self.module}")
        md.append(f"**Время:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")
        
        if self.data["description"]:
            md.append("## Описание")
            md.append(self.data["description"])
            md.append("")
        
        if self.data["steps_to_reproduce"]:
            md.append("## Шаги воспроизведения")
            for i, step in enumerate(self.data["steps_to_reproduce"], 1):
                md.append(f"{i}. {step}")
            md.append("")
        
        if self.data["expected_behavior"]:
            md.append("## Ожидаемое поведение")
            md.append(self.data["expected_behavior"])
            md.append("")
        
        if self.data["actual_behavior"]:
            md.append("## Фактическое поведение")
            md.append(self.data["actual_behavior"])
            md.append("")
        
        if self.data["test_data"]:
            md.append("## Тестовые данные")
            md.append("```")
            md.append(self.data["test_data"][:1000])  # Ограничение для читаемости
            md.append("```")
            md.append("")
        
        if self.data["stack_trace"]:
            md.append("## Стек-трейс")
            md.append("```python")
            md.append(self.data["stack_trace"])
            md.append("```")
            md.append("")
        
        if self.data["environment"]:
            md.append("## Окружение")
            for key, value in self.data["environment"].items():
                md.append(f"- **{key}:** {value}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md))
        
        return str(filepath)