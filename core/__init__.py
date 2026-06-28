"""Doc2Md 核心层：配置管理、常量、转换门面。"""

from .config import AppConfig, MinerUConfig, LLMConfig, ConfigManager
from .constants import (
    APP_NAME,
    APP_VERSION,
    SUPPORTED_FILE_TYPES,
    FILE_TYPE_EXTENSIONS,
    DEFAULT_OUTPUT_DIR_NAME,
)
from .converter_facade import ConvertResult, ConverterFacade

__all__ = [
    "AppConfig",
    "MinerUConfig",
    "LLMConfig",
    "ConfigManager",
    "APP_NAME",
    "APP_VERSION",
    "SUPPORTED_FILE_TYPES",
    "FILE_TYPE_EXTENSIONS",
    "DEFAULT_OUTPUT_DIR_NAME",
    "ConvertResult",
    "ConverterFacade",
]
