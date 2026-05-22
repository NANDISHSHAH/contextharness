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


def test_scan_applies_ignore_files_and_tracks_skipped_files(tmp_path):
    (tmp_path / ".gitignore").write_text("ignore_me.py\n")
    (tmp_path / ".contextpackignore").write_text("docs/*.md\n")

    (tmp_path / "app.py").write_text("print('ok')\n")
    (tmp_path / "ignore_me.py").write_text("print('skip')\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# guide\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("console.log('skip')\n")
    (tmp_path / "package-lock.json").write_text("{}\n")

    result = RepositoryScanner(tmp_path).scan()
    paths = {f.path for f in result.files}

    assert paths == {"app.py"}
    assert result.files_skipped == 4
