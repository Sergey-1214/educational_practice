#!/usr/bin/env python
"""
Скрипт для запуска всех тестов с автоматической генерацией баг-репортов
"""

import sys
import pytest


def main():
    """Запуск всех тестов с генерацией отчетов"""
    
    # Аргументы для pytest
    args = sys.argv[1:]
    
    if not args:
        # По умолчанию запускаем все тесты
        args = [
            "-v",
            "--tb=short",
            "--maxfail=10",
            "--disable-warnings"
        ]
    
    # Добавляем флаг для создания отчетов
    # Плагин уже зарегистрирован в conftest.py
    
    print("\n" + "="*70)
    print("ЗАПУСК ТЕСТОВ С ГЕНЕРАЦИЕЙ БАГ-РЕПОРТОВ")
    print("="*70)
    print(f"Команда: pytest {' '.join(args)}")
    print("="*70 + "\n")
    
    # Запускаем pytest
    exit_code = pytest.main(args)
    
    # Проверяем результат
    if exit_code == 0:
        print("\n" + "="*70)
        print("ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("НЕКОТОРЫЕ ТЕСТЫ УПАЛИ")
        print("Баг-репорты сохранены в папке: bug_reports/")
        print("="*70)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
