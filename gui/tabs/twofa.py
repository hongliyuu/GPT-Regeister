# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import check, hint_label


class TwoFATab(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        v.setContentsMargins(12, 16, 24, 16)

        card = QGroupBox("\u53cc\u56e0\u7d20\u8ba4\u8bc1")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(20, 28, 20, 20)

        self.twofa_check = check(
            "\u6ce8\u518c\u6210\u529f\u540e\u81ea\u52a8\u8bbe\u7f6e 2FA\uff08TOTP\uff09"
        )
        desc = hint_label(
            "\u5f00\u542f\u540e\uff0c\u6bcf\u6b21\u6ce8\u518c\u6210\u529f\u4f1a\u518d\u6536\u4e00\u5c01\u90ae\u4ef6\u4ee5\u5b8c\u6210 TOTP \u8bbe\u5907\u7ed1\u5b9a"
        )
        card_l.addWidget(self.twofa_check)
        card_l.addWidget(desc)
        v.addWidget(card)
        v.addStretch()

        scroll.setWidget(w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def load_config(self, cfg: dict):
        t = cfg.get("twofa", {})
        self.twofa_check.setChecked(t.get("enabled", False))

    def collect_config(self, cfg: dict):
        cfg["twofa"] = {"enabled": self.twofa_check.isChecked()}
