"""test_config.py：ConfigManager 读写、0600 权限、dataclass 序列化。"""

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import (
    AppConfig,
    ConfigManager,
    CONFIG_DIR,
    CONFIG_FILE,
    LLMConfig,
    MinerUConfig,
)


@pytest.fixture
def temp_config(monkeypatch, tmp_path):
    """用临时目录替代真实配置目录。"""
    fake_dir = tmp_path / ".doc2md"
    fake_file = fake_dir / "config.json"
    monkeypatch.setattr("core.config.CONFIG_DIR", fake_dir)
    monkeypatch.setattr("core.config.CONFIG_FILE", fake_file)
    return fake_dir, fake_file


def test_default_config():
    """默认配置应包含合理的初始值。"""
    cfg = AppConfig()
    assert cfg.enable_ocr is True
    assert cfg.concurrency == 1
    assert cfg.mineru.enabled is True
    assert cfg.mineru.mode == "auto"
    assert cfg.llm.enabled is False
    assert "PDF" in cfg.file_types
    assert "Word" in cfg.file_types


def test_save_and_load(temp_config):
    """保存后加载应得到相同配置。"""
    _, fake_file = temp_config

    cfg = AppConfig(
        output_dir="/tmp/test_output",
        enable_ocr=False,
        mineru=MinerUConfig(enabled=False, model_dir="/tmp/models", mode="ocr"),
        llm=LLMConfig(enabled=True, api_key="sk-test-12345678", model="gpt-4o"),
    )
    ConfigManager.save(cfg)

    # 文件存在
    assert fake_file.exists()

    # 加载
    loaded = ConfigManager.load()
    assert loaded.output_dir == "/tmp/test_output"
    assert loaded.enable_ocr is False
    assert loaded.mineru.enabled is False
    assert loaded.mineru.model_dir == "/tmp/models"
    assert loaded.mineru.mode == "ocr"
    assert loaded.llm.enabled is True
    assert loaded.llm.api_key == "sk-test-12345678"
    assert loaded.llm.model == "gpt-4o"


def test_file_permissions(temp_config):
    """配置文件权限应为 0600（保护 API Key）。"""
    _, fake_file = temp_config

    cfg = AppConfig(llm=LLMConfig(enabled=True, api_key="sk-secret"))
    ConfigManager.save(cfg)

    mode = stat.S_IMODE(fake_file.stat().st_mode)
    assert mode == 0o600, f"期望 0600，实际 {oct(mode)}"


def test_load_nonexistent(temp_config):
    """文件不存在时应返回默认配置。"""
    loaded = ConfigManager.load()
    assert isinstance(loaded, AppConfig)
    assert loaded == AppConfig()


def test_load_corrupt_json(temp_config):
    """JSON 损坏时应返回默认配置。"""
    _, fake_file = temp_config
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text("{ not valid json", encoding="utf-8")

    loaded = ConfigManager.load()
    assert isinstance(loaded, AppConfig)
    assert loaded == AppConfig()


def test_load_unknown_fields(temp_config):
    """未知字段应被忽略，不导致构造失败。"""
    _, fake_file = temp_config
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text(
        json.dumps(
            {
                "output_dir": "/tmp/x",
                "unknown_field": "should be ignored",
                "mineru": {"enabled": True, "unknown": "ignored"},
            }
        ),
        encoding="utf-8",
    )

    loaded = ConfigManager.load()
    assert loaded.output_dir == "/tmp/x"
    assert loaded.mineru.enabled is True


def test_nested_config_roundtrip(temp_config):
    """嵌套 MinerUConfig / LLMConfig 序列化往返。"""
    original = AppConfig(
        mineru=MinerUConfig(enabled=True, model_dir="/models", mode="txt"),
        llm=LLMConfig(
            enabled=True,
            base_url="https://api.deepseek.com/v1",
            api_key="sk-abc",
            model="deepseek-chat",
            image_describe=True,
        ),
    )
    ConfigManager.save(original)
    loaded = ConfigManager.load()

    assert loaded.mineru == original.mineru
    assert loaded.llm == original.llm
