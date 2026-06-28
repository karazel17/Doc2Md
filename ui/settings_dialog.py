"""设置对话框：MinerU / LLM / 转换选项 / 外观。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core.config import AppConfig, LLMConfig, MinerUConfig
from core.constants import MINERU_MODES, THEME_OPTIONS


class SettingsDialog(QDialog):
    """设置对话框。

    分组：转换选项 / MinerU / LLM / 外观
    """

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(520)
        self._config = config

        layout = QVBoxLayout(self)

        # ── 转换选项 ──
        convert_group = QGroupBox("转换选项")
        convert_form = QFormLayout(convert_group)

        self._ocr_check = QCheckBox("启用 OCR（对扫描件 PDF）")
        self._ocr_check.setChecked(config.enable_ocr)
        convert_form.addRow(self._ocr_check)

        self._concurrency_spin = QSpinBox()
        self._concurrency_spin.setRange(1, 8)
        self._concurrency_spin.setValue(config.concurrency)
        self._concurrency_spin.setToolTip("V1 仅支持顺序转换，并发将在 V2 支持")
        self._concurrency_spin.setEnabled(False)  # V1 禁用
        convert_form.addRow("并发数（V2）：", self._concurrency_spin)

        layout.addWidget(convert_group)

        # ── MinerU ──
        mineru_group = QGroupBox("MinerU 配置")
        mineru_form = QFormLayout(mineru_group)

        self._mineru_check = QCheckBox("使用 MinerU 转换 PDF（中文 PDF 效果更优）")
        self._mineru_check.setChecked(config.mineru.enabled)
        mineru_form.addRow(self._mineru_check)

        self._mineru_mode = QComboBox()
        self._mineru_mode.addItems(MINERU_MODES)
        self._mineru_mode.setCurrentText(config.mineru.mode)
        self._mineru_mode.setToolTip(
            "auto: 自动判断 | txt: 强制文本模式（快，适合纯文本 PDF）| ocr: 强制 OCR（适合扫描件）"
        )
        mineru_form.addRow("解析模式：", self._mineru_mode)

        # 模型目录选择
        model_dir_layout = QHBoxLayout()
        self._model_dir_edit = QLineEdit(config.mineru.model_dir)
        self._model_dir_edit.setPlaceholderText("留空则使用默认路径或环境变量 MINERU_MODEL_DIR")
        model_dir_layout.addWidget(self._model_dir_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_model_dir)
        model_dir_layout.addWidget(browse_btn)
        mineru_form.addRow("模型目录：", model_dir_layout)

        layout.addWidget(mineru_group)

        # ── LLM 增强 ──
        llm_group = QGroupBox("LLM 增强（可选，用于图像智能描述）")
        llm_form = QFormLayout(llm_group)

        self._llm_check = QCheckBox("启用 LLM 增强")
        self._llm_check.setChecked(config.llm.enabled)
        llm_form.addRow(self._llm_check)

        self._llm_base_url = QLineEdit(config.llm.base_url)
        self._llm_base_url.setPlaceholderText("https://api.openai.com/v1 或 https://api.deepseek.com/v1")
        llm_form.addRow("API Base URL：", self._llm_base_url)

        self._llm_api_key = QLineEdit(config.llm.api_key)
        self._llm_api_key.setEchoMode(QLineEdit.Password)
        self._llm_api_key.setPlaceholderText("sk-...")
        llm_form.addRow("API Key：", self._llm_api_key)

        self._llm_model = QLineEdit(config.llm.model)
        self._llm_model.setPlaceholderText("gpt-4o-mini")
        llm_form.addRow("模型名：", self._llm_model)

        self._image_describe_check = QCheckBox("启用图像描述（V2 实现后生效）")
        self._image_describe_check.setChecked(config.llm.image_describe)
        self._image_describe_check.setEnabled(False)  # V1 禁用
        llm_form.addRow(self._image_describe_check)

        layout.addWidget(llm_group)

        # ── 外观 ──
        theme_group = QGroupBox("外观")
        theme_form = QFormLayout(theme_group)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(THEME_OPTIONS)
        self._theme_combo.setCurrentText(config.theme)
        theme_form.addRow("主题：", self._theme_combo)
        layout.addWidget(theme_group)

        # ── 按钮 ──
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_model_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择 MinerU 模型目录")
        if d:
            self._model_dir_edit.setText(d)

    def _on_accept(self) -> None:
        # 校验 LLM 配置
        if self._llm_check.isChecked() and not self._llm_api_key.text().strip():
            QMessageBox.warning(self, "配置不完整", "启用 LLM 增强需要填写 API Key")
            return
        self.accept()

    def get_config(self) -> AppConfig:
        """返回更新后的配置（不保存到磁盘）。"""
        cfg = self._config
        cfg.enable_ocr = self._ocr_check.isChecked()
        cfg.concurrency = self._concurrency_spin.value()
        cfg.theme = self._theme_combo.currentText()

        cfg.mineru = MinerUConfig(
            enabled=self._mineru_check.isChecked(),
            model_dir=self._model_dir_edit.text().strip(),
            mode=self._mineru_mode.currentText(),
        )

        cfg.llm = LLMConfig(
            enabled=self._llm_check.isChecked(),
            base_url=self._llm_base_url.text().strip(),
            api_key=self._llm_api_key.text().strip(),
            model=self._llm_model.text().strip(),
            image_describe=self._image_describe_check.isChecked(),
        )

        return cfg
