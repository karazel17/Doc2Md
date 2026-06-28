"""test_facade.py：ConverterFacade 调用 word/txt/html converter（不依赖 MinerU）。"""

from pathlib import Path

import pytest

from core.config import AppConfig
from core.converter_facade import ConvertResult, ConverterFacade


@pytest.fixture
def txt_fixture(tmp_path):
    """创建一个测试用 TXT 文件。"""
    f = tmp_path / "sample.txt"
    f.write_text("Hello Doc2Md\n第二行内容", encoding="utf-8")
    return f


@pytest.fixture
def html_fixture(tmp_path):
    """创建一个测试用 HTML 文件。"""
    f = tmp_path / "page.html"
    f.write_text(
        "<html><body><h1>标题</h1><p>段落内容</p></body></html>",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def facade():
    """默认配置的 ConverterFacade。"""
    return ConverterFacade(AppConfig())


def test_convert_txt_success(txt_fixture, tmp_path, facade):
    """TXT 文件应成功转换。"""
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = facade.convert_one(txt_fixture, txt_fixture.parent, out_dir)

    assert isinstance(result, ConvertResult)
    assert result.success is True
    assert result.input_path == txt_fixture
    assert result.output_path is not None
    assert result.output_path.suffix == ".md"
    assert result.output_path.exists()

    content = result.output_path.read_text(encoding="utf-8")
    assert "Hello Doc2Md" in content
    assert "第二行内容" in content


def test_convert_html_success(html_fixture, tmp_path, facade):
    """HTML 文件应成功转换为 Markdown。"""
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = facade.convert_one(html_fixture, html_fixture.parent, out_dir)

    assert result.success is True
    assert result.output_path.exists()
    content = result.output_path.read_text(encoding="utf-8")
    assert "标题" in content
    assert "段落内容" in content


def test_convert_unsupported_format(tmp_path, facade):
    """不支持的格式应返回失败结果（不抛异常）。"""
    unsupported = tmp_path / "file.xyz"
    unsupported.write_text("unknown", encoding="utf-8")

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = facade.convert_one(unsupported, tmp_path, out_dir)

    assert result.success is False
    assert "不支持" in result.message or "unsupported" in result.error


def test_convert_preserves_directory_structure(tmp_path, facade):
    """转换应保留目录结构。"""
    # 创建嵌套文件
    sub = tmp_path / "input" / "sub"
    sub.mkdir(parents=True)
    txt = sub / "note.txt"
    txt.write_text("内容", encoding="utf-8")

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = facade.convert_one(txt, tmp_path / "input", out_dir)

    assert result.success is True
    # 输出应在 output/sub/note.md
    expected = out_dir / "sub" / "note.md"
    assert result.output_path == expected
    assert expected.exists()


def test_convert_result_fields(txt_fixture, tmp_path, facade):
    """ConvertResult 字段应完整。"""
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = facade.convert_one(txt_fixture, txt_fixture.parent, out_dir)

    assert hasattr(result, "input_path")
    assert hasattr(result, "output_path")
    assert hasattr(result, "success")
    assert hasattr(result, "elapsed")
    assert hasattr(result, "message")
    assert hasattr(result, "error")
    assert isinstance(result.elapsed, float)
    assert result.elapsed >= 0
