import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# плагин для сбора баг-репортов
pytest_plugins = [
    "tests.utils.pytest_bug_reporter",
]

pytest_plugins.extend([
    "tests.auth.test_login",
    "tests.auth.test_logout", 
    "tests.auth.test_refresh",
    "tests.auth.test_register",
    "tests.documents.test_delete",
    "tests.documents.test_get_document",
    "tests.documents.test_get_documents",
    "tests.documents.test_upload",
    "tests.history.test_clear_history",
    "tests.history.test_delete_history_item",
    "tests.history.test_get_history",
    "tests.search.test_search",
])