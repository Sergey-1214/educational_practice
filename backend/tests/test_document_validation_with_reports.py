import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.modules.documents.schemas import DocumentRead, DocumentStatus


class TestDocumentValidation:
    @pytest.fixture
    def valid_document(self):
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
            updated_at=datetime.now(),
        )

    def test_valid_document_validation(self, valid_document):
        assert valid_document.id is not None
        assert valid_document.user_id is not None
        assert valid_document.file_name.endswith(".pdf")
        assert valid_document.status == DocumentStatus.PROCESSED
        assert valid_document.chunks_count >= 0

    def test_invalid_document_negative_chunks(self, bug_reporter):
        try:
            invalid_doc = DocumentRead(
                id=uuid4(),
                user_id=uuid4(),
                file_name="invalid.pdf",
                content_type="application/pdf",
                size_bytes=1024,
                status=DocumentStatus.UPLOADED,
                chunks_count=-5,
                error_message=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            assert invalid_doc.chunks_count >= 0, (
                f"chunks_count cannot be negative: {invalid_doc.chunks_count}"
            )

        except AssertionError:
            report = bug_reporter("Negative chunks_count in document")
            report.set_description(
                "The chunks_count field can contain negative values."
            )
            report.add_step("Create a document with chunks_count = -5")
            report.add_step("Validate the document")
            report.set_expected("chunks_count should be >= 0")
            report.set_actual("chunks_count = -5 (negative value)")
            report.set_test_data(
                {
                    "chunks_count": -5,
                    "status": "uploaded",
                }
            )
            raise

    def test_invalid_document_status_validation(self, bug_reporter):
        invalid_statuses = ["processing", "invalid", "unknown"]

        for status in invalid_statuses:
            try:
                valid_statuses = ["uploaded", "processed", "failed"]
                assert status in valid_statuses, f"Invalid document status: {status}"

            except AssertionError:
                report = bug_reporter(f"Invalid document status: {status}")
                report.set_description(f"The status '{status}' is not allowed.")
                report.add_step(f"Create a document with status '{status}'")
                report.add_step("Validate the document status")
                report.set_actual(f"Received status: {status}")
                report.set_test_data({"status": status})
                raise

    def test_document_with_missing_fields(self, bug_reporter):
        try:
            doc = {
                "id": uuid4(),
                "content_type": "application/pdf",
                "size_bytes": 1024,
                "status": "uploaded",
            }

            required_fields = ["user_id", "file_name"]
            missing = [field for field in required_fields if field not in doc]

            if missing:
                report = bug_reporter("Required document fields are missing")
                report.set_description(f"Missing fields detected: {missing}")
                report.add_step("Create a document without required fields")
                report.add_step("Validate the document")
                report.set_expected("All required fields should be present")
                report.set_actual(f"Missing fields: {missing}")
                report.set_test_data(doc)

                assert False, f"Missing fields: {missing}"

        except Exception as exc:
            report = bug_reporter("Unexpected error during document validation")
            report.set_description(f"Unexpected error: {exc}")
            report.add_step("Create a document with missing fields")
            report.set_expected("A clear validation error should be raised")
            report.set_actual(str(exc))
            report.set_stack_trace()
            raise
