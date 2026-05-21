from contextpack.parsers.python_parser import PythonParser


def test_python_parser_extracts_class_and_function():
    code = '''
class UploadService:
    """Handles uploads."""

    def upload(self, path: str) -> None:
        pass

def helper():
    pass
'''
    entities = PythonParser().parse_file("svc.py", code)
    names = {e.name for e in entities}
    assert "UploadService" in names
    assert "upload" in names or "helper" in names
