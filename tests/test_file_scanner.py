"""test_file_scanner.py：scan_files 递归、隐藏文件过滤、类型筛选。"""

from pathlib import Path

import pytest

from converters.batch import scan_files


@pytest.fixture
def sample_tree(tmp_path):
    """创建测试目录树。"""
    # 根目录文件
    (tmp_path / "doc1.pdf").write_text("pdf")
    (tmp_path / "doc2.docx").write_text("docx")
    (tmp_path / "notes.txt").write_text("txt")
    (tmp_path / "page.html").write_text("html")

    # 隐藏文件与临时文件（应被过滤）
    (tmp_path / ".hidden.pdf").write_text("hidden")
    (tmp_path / "~temp.docx").write_text("temp")

    # 子目录
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "sub1.pdf").write_text("sub pdf")
    (sub / "sub2.pptx").write_text("pptx")

    # 隐藏子目录（应被跳过）
    hidden_dir = tmp_path / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "inner.pdf").write_text("inner")

    # 不支持的格式
    (tmp_path / "image.jpg").write_text("jpg")
    (tmp_path / "data.json").write_text("json")

    return tmp_path


def test_scan_all_types(sample_tree):
    """扫描所有支持类型。"""
    files = scan_files(sample_tree, ["PDF", "Word", "PPT", "EPUB", "TXT", "HTML"])
    names = sorted(f.name for f in files)

    assert "doc1.pdf" in names
    assert "doc2.docx" in names
    assert "notes.txt" in names
    assert "page.html" in names
    assert "sub1.pdf" in names
    assert "sub2.pptx" in names
    # 不支持的格式不应出现
    assert "image.jpg" not in names
    assert "data.json" not in names


def test_scan_filtered_types(sample_tree):
    """只扫描指定类型。"""
    files = scan_files(sample_tree, ["PDF"])
    names = [f.name for f in files]

    assert "doc1.pdf" in names
    assert "sub1.pdf" in names
    # Word/PPT/TXT/HTML 不应出现
    assert "doc2.docx" not in names
    assert "notes.txt" not in names
    assert "sub2.pptx" not in names


def test_scan_skips_hidden_files(sample_tree):
    """隐藏文件和临时文件应被过滤。"""
    files = scan_files(sample_tree, ["PDF", "Word"])
    names = [f.name for f in files]

    assert ".hidden.pdf" not in names
    assert "~temp.docx" not in names


def test_scan_skips_hidden_dirs(sample_tree):
    """隐藏目录中的文件应被跳过。"""
    files = scan_files(sample_tree, ["PDF"])
    names = [f.name for f in files]

    assert "inner.pdf" not in names


def test_scan_recursive(sample_tree):
    """应递归扫描子目录。"""
    files = scan_files(sample_tree, ["PDF", "PPT"])
    rel_paths = sorted(str(f.relative_to(sample_tree)) for f in files)

    assert "sub/sub1.pdf" in rel_paths
    assert "sub/sub2.pptx" in rel_paths


def test_scan_nonexistent_dir():
    """不存在的目录应抛出 ValueError。"""
    with pytest.raises(ValueError, match="输入目录不存在"):
        scan_files("/nonexistent/path/xyz", ["PDF"])


def test_scan_empty_dir(tmp_path):
    """空目录应返回空列表。"""
    files = scan_files(tmp_path, ["PDF"])
    assert files == []


def test_scan_sorted(sample_tree):
    """结果应排序。"""
    files = scan_files(sample_tree, ["PDF"])
    paths = [str(f) for f in files]
    assert paths == sorted(paths)
