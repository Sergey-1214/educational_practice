import pytest
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.modules.documents.schemas import DocumentRead, DocumentStatus


class TestDocumentValidation:
    """Тесты валидации документов с созданием баг-репортов"""
    
    @pytest.fixture
    def valid_document(self):
        """Создает валидный документ"""
        return DocumentRead(
            id=uuid4(),
            user_id=uuid4(),
            file_name="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            status=DocumentStatus.PROCESSED,
            chunks_count=10,
            error_message=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_valid_document_validation(self, valid_document):
        """Тест валидации корректного документа - должен пройти"""
        # Проверяем, что документ валиден
        assert valid_document.id is not None
        assert valid_document.user_id is not None
        assert valid_document.file_name.endswith(".pdf")
        assert valid_document.status == DocumentStatus.PROCESSED
        assert valid_document.chunks_count >= 0
        print("✅ Документ валиден")
    
    def test_invalid_document_negative_chunks(self, bug_reporter):
        """Тест документа с отрицательным количеством чанков - должен упасть"""
        try:
            # Создаем документ с отрицательным chunks_count
            invalid_doc = DocumentRead(
                id=uuid4(),
                user_id=uuid4(),
                file_name="invalid.pdf",
                content_type="application/pdf",
                size_bytes=1024,
                status=DocumentStatus.UPLOADED,
                chunks_count=-5,  # Отрицательное значение
                error_message=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Проверяем, что chunks_count >= 0
            assert invalid_doc.chunks_count >= 0, f"chunks_count не может быть отрицательным: {invalid_doc.chunks_count}"
            
        except AssertionError as e:
            # Создаем баг-репорт
            report = bug_reporter("Отрицательное количество чанков в документе")
            report.set_description("Поле chunks_count может принимать отрицательные значения")
            report.add_step("Создать документ с chunks_count = -5")
            report.add_step("Валидировать документ")
            report.set_expected("chunks_count должен быть >= 0")
            report.set_actual(f"chunks_count = -5 (отрицательное значение)")
            report.set_test_data({
                "chunks_count": -5,
                "status": "uploaded"
            })
            raise
    
    def test_invalid_document_status_validation(self, bug_reporter):
        """Тест документа с невалидным статусом"""
        invalid_statuses = ["processing", "invalid", "unknown"]
        
        for status in invalid_statuses:
            try:
                # Проверяем, что статус валидный
                valid_statuses = ["uploaded", "processing", "processed", "failed"]
                assert status in valid_statuses, f"Невалидный статус: {status}"
                
            except AssertionError as e:
                # Создаем баг-репорт
                report = bug_reporter(f"Невалидный статус документа: {status}")
                report.set_description(f"Статус '{status}' недопустим")
                report.add_step(f"Создать документ со статусом '{status}'")
                report.add_step("Проверить статус")
                report.set_actual(f"Получен статус: {status}")
                report.set_test_data({
                    "status": status,
                })
                raise
    
    def test_document_with_missing_fields(self, bug_reporter):
        """Тест документа с пропущенными полями"""
        try:
            # Создаем документ с пропущенными полями
            doc = {
                "id": uuid4(),
                # "user_id" пропущен
                # "file_name" пропущен
                "content_type": "application/pdf",
                "size_bytes": 1024,
                "status": "uploaded"
            }
            
            required_fields = ["user_id", "file_name"]
            missing = [f for f in required_fields if f not in doc]
            
            if missing:
                report = bug_reporter("Пропущены обязательные поля в документе")
                report.set_description(f"Обнаружены пропущенные поля: {missing}")
                report.add_step("Создать документ без обязательных полей")
                report.add_step("Валидировать документ")
                report.set_expected("Все поля присутствуют")
                report.set_actual(f"Отсутствуют поля: {missing}")
                report.set_test_data(doc)
                
                assert False, f"Пропущены поля: {missing}"
                
        except Exception as e:
            # Если ошибка произошла раньше
            report = bug_reporter("Ошибка при валидации документа")
            report.set_description(f"Неожиданная ошибка: {str(e)}")
            report.add_step("Создать документ с пропущенными полями")
            report.set_expected("Понятная ошибка валидации")
            report.set_actual(str(e))
            report.set_stack_trace()
            raise