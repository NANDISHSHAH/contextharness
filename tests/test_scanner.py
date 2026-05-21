from contextpack.scanner.scanner import RepositoryScanner


def test_scan_finds_python_files(tmp_path):
    (tmp_path / "main.py").write_text("def hello(): pass\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("")

    result = RepositoryScanner(tmp_path).scan()
    paths = [f.path for f in result.files]
    assert "main.py" in paths
    assert not any("node_modules" in p for p in paths)
    assert result.languages.get("python", 0) >= 1
