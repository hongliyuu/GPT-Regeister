# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFormLayout, QScrollArea, QWidget

from gui.widgets import line_edit


class OpenAITab(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_w = QWidget()
        f = QFormLayout(form_w)
        f.setSpacing(12)
        f.setContentsMargins(12, 16, 24, 16)
        f.setHorizontalSpacing(20)

        self.client_id_edit = line_edit()
        self.scope_edit = line_edit()
        self.audience_edit = line_edit()
        self.redirect_uri_edit = line_edit()
        self.sentinel_sv_edit = line_edit()

        f.addRow("Client ID", self.client_id_edit)
        f.addRow("Scope", self.scope_edit)
        f.addRow("Audience", self.audience_edit)
        f.addRow("Redirect URI", self.redirect_uri_edit)
        f.addRow("Sentinel \u7248\u672c\u53f7", self.sentinel_sv_edit)

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
        o = cfg.get("openai_protocol", {})
        self.client_id_edit.setText(o.get("client_id", ""))
        self.scope_edit.setText(o.get("scope", ""))
        self.audience_edit.setText(o.get("audience", ""))
        self.redirect_uri_edit.setText(o.get("redirect_uri", ""))
        self.sentinel_sv_edit.setText(o.get("sentinel_sv", ""))

    def collect_config(self, cfg: dict):
        cfg["openai_protocol"] = {
            "client_id": self.client_id_edit.text(),
            "scope": self.scope_edit.text(),
            "audience": self.audience_edit.text(),
            "redirect_uri": self.redirect_uri_edit.text(),
            "sentinel_sv": self.sentinel_sv_edit.text(),
        }
