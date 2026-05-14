# -*- coding: utf-8 -*-
import json

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import check, line_edit, multi_line_edit, section_label, separator, spin


class FlowTab(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        v.setContentsMargins(12, 16, 24, 16)

        card = QGroupBox("Flow \u89e6\u53d1\u914d\u7f6e")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(20, 28, 20, 20)
        card_l.setSpacing(10)

        self.flow_enable_check = check("\u542f\u7528\u6ce8\u518c\u540e Flow \u89e6\u53d1")
        card_l.addWidget(self.flow_enable_check)
        card_l.addWidget(separator())

        ff = QFormLayout()
        ff.setSpacing(10)
        self.flow_url_edit = line_edit()
        self.flow_bearer_edit = line_edit()
        self.flow_cookie_edit = line_edit()
        self.flow_timeout_spin = spin(1, 300, 30)
        ff.addRow("URL", self.flow_url_edit)
        ff.addRow("Bearer Token", self.flow_bearer_edit)
        ff.addRow("Cookie", self.flow_cookie_edit)
        ff.addRow("\u8d85\u65f6 (\u79d2)", self.flow_timeout_spin)
        card_l.addLayout(ff)

        card_l.addWidget(section_label("Payload (JSON)"))
        self.flow_payload_edit = multi_line_edit(
            '{\n  "action": "chat"\n}', max_h=120
        )
        card_l.addWidget(self.flow_payload_edit)

        v.addWidget(card)
        v.addStretch()

        scroll.setWidget(w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def load_config(self, cfg: dict):
        f = cfg.get("flow_trigger", {})
        self.flow_enable_check.setChecked(f.get("enabled", True))
        self.flow_url_edit.setText(f.get("url", ""))
        self.flow_bearer_edit.setText(f.get("bearer", ""))
        self.flow_cookie_edit.setText(f.get("cookie", ""))
        self.flow_timeout_spin.setValue(f.get("timeout", 30))
        payload = f.get("payload", {})
        self.flow_payload_edit.setPlainText(
            json.dumps(payload, indent=2, ensure_ascii=False) if payload else ""
        )

    def collect_config(self, cfg: dict):
        cfg["flow_trigger"] = {
            "enabled": self.flow_enable_check.isChecked(),
            "url": self.flow_url_edit.text(),
            "bearer": self.flow_bearer_edit.text(),
            "cookie": self.flow_cookie_edit.text(),
            "payload": json.loads(self.flow_payload_edit.toPlainText().strip() or "{}"),
            "timeout": self.flow_timeout_spin.value(),
        }
