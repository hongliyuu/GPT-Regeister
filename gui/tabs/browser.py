# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFormLayout, QScrollArea, QWidget

from gui.widgets import line_edit, spin


class BrowserTab(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_w = QWidget()
        f = QFormLayout(form_w)
        f.setSpacing(12)
        f.setContentsMargins(12, 16, 24, 16)
        f.setHorizontalSpacing(20)

        self.ua_edit = line_edit()
        self.chua_edit = line_edit()
        self.chua_platform_edit = line_edit()
        self.chua_mobile_edit = line_edit()
        self.impersonate_edit = line_edit()
        self.timeout_spin = spin(1, 300, 30)

        f.addRow("User-Agent", self.ua_edit)
        f.addRow("Sec-CH-UA", self.chua_edit)
        f.addRow("Sec-CH-UA-Platform", self.chua_platform_edit)
        f.addRow("Sec-CH-UA-Mobile", self.chua_mobile_edit)
        f.addRow("Impersonate (Chrome\u7248\u672c)", self.impersonate_edit)
        f.addRow("\u8bf7\u6c42\u8d85\u65f6 (\u79d2)", self.timeout_spin)

        scroll.setWidget(form_w)
        layout = self._wrap_scroll(scroll)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @staticmethod
    def _wrap_scroll(scroll):
        from PySide6.QtWidgets import QVBoxLayout
        l = QVBoxLayout()
        l.addWidget(scroll)
        return l

    def load_config(self, cfg: dict):
        b = cfg.get("browser", {})
        self.ua_edit.setText(b.get("user_agent", ""))
        self.chua_edit.setText(b.get("sec_ch_ua", ""))
        self.chua_platform_edit.setText(b.get("sec_ch_ua_platform", ""))
        self.chua_mobile_edit.setText(b.get("sec_ch_ua_mobile", ""))
        self.impersonate_edit.setText(b.get("impersonate", ""))
        self.timeout_spin.setValue(b.get("request_timeout", 30))

    def collect_config(self, cfg: dict):
        cfg["browser"] = {
            "user_agent": self.ua_edit.text(),
            "sec_ch_ua": self.chua_edit.text(),
            "sec_ch_ua_platform": self.chua_platform_edit.text(),
            "sec_ch_ua_mobile": self.chua_mobile_edit.text(),
            "impersonate": self.impersonate_edit.text(),
            "request_timeout": self.timeout_spin.value(),
        }
