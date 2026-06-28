"""Doc2Md 配置管理。

配置持久化到 ~/.doc2md/config.json，文件权限 0600 保护 API Key。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("doc2md")

# 配置目录与文件路径
CONFIG_DIR = Path.home() / ".doc2md"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class MinerUConfig:
    """MinerU 转换配置。"""

    enabled: bool = True
    model_dir: str = ""  # 空=用默认；优先级高于环境变量
    mode: str = "auto"  # auto | txt | ocr


@dataclass
class LLMConfig:
    """LLM 增强配置（V1 仅预留接口，不实现图像描述）。"""

    enabled: bool = False
    base_url: str = ""  # OpenAI 兼容 API 地址
    api_key: str = ""
    model: str = "gpt-4o-mini"
    image_describe: bool = False  # V2+ 实现


@dataclass
class AppConfig:
    """应用总配置。"""

    input_dir: str = ""
    output_dir: str = ""
    file_types: list[str] = field(
        default_factory=lambda: ["PDF", "Word", "PPT", "EPUB", "TXT", "HTML"]
    )
    enable_ocr: bool = True
    concurrency: int = 1  # V1 顺序转换；V2+ 支持并发
    mineru: MinerUConfig = field(default_factory=MinerUConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    theme: str = "system"  # system | light | dark
    window_width: int = 1100
    window_height: int = 720


def _mask_api_key(key: str) -> str:
    """掩码 API Key 用于日志输出。"""
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


class ConfigManager:
    """配置管理器：加载与保存 AppConfig。"""

    @staticmethod
    def load() -> AppConfig:
        """从磁盘加载配置。文件不存在或损坏时返回默认配置。"""
        if not CONFIG_FILE.exists():
            logger.info("配置文件不存在，使用默认配置")
            return AppConfig()

        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"配置文件读取失败，使用默认配置: {e}")
            return AppConfig()

        # 兼容嵌套 dataclass：mineru / llm
        mineru_data = data.pop("mineru", {}) or {}
        llm_data = data.pop("llm", {}) or {}

        # 字段过滤，避免未知字段导致 dataclass 构造失败
        valid_top = {k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__}
        valid_mineru = {
            k: v for k, v in mineru_data.items() if k in MinerUConfig.__dataclass_fields__
        }
        valid_llm = {k: v for k, v in llm_data.items() if k in LLMConfig.__dataclass_fields__}

        try:
            cfg = AppConfig(
                **valid_top,
                mineru=MinerUConfig(**valid_mineru),
                llm=LLMConfig(**valid_llm),
            )
            logger.info(
                f"配置加载成功 | MinerU: {cfg.mineru.enabled} | LLM: {cfg.llm.enabled} "
                f"(key={_mask_api_key(cfg.llm.api_key)})"
            )
            return cfg
        except TypeError as e:
            logger.warning(f"配置字段不匹配，使用默认配置: {e}")
            return AppConfig()

    @staticmethod
    def save(cfg: AppConfig) -> None:
        """保存配置到磁盘，并设置 0600 权限保护 API Key。"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(
                json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.chmod(CONFIG_FILE, 0o600)
            logger.info(f"配置已保存到 {CONFIG_FILE}")
        except OSError as e:
            logger.error(f"配置保存失败: {e}")
            raise
