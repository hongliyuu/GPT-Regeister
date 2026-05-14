# -*- coding: utf-8 -*-
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
)


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class NoWheelLineEdit(QLineEdit):
    def wheelEvent(self, event):
        event.ignore()


class NoWheelPlainTextEdit(QPlainTextEdit):
    def wheelEvent(self, event):
        event.ignore()


def line_edit(text: str = "", placeholder: str = "") -> QLineEdit:
    w = NoWheelLineEdit(text)
    w.setPlaceholderText(placeholder)
    return w


def multi_line_edit(text: str = "", placeholder: str = "", max_h: int = 160) -> QPlainTextEdit:
    w = NoWheelPlainTextEdit()
    w.setPlainText(text)
    w.setPlaceholderText(placeholder)
    w.setMaximumHeight(max_h)
    w.setTabChangesFocus(True)
    return w


def spin(min_val: int = 0, max_val: int = 999999, value: int = 0) -> QSpinBox:
    w = NoWheelSpinBox()
    w.setRange(min_val, max_val)
    w.setValue(value)
    return w


def combo(items: list, current: str = "") -> QComboBox:
    w = NoWheelComboBox()
    w.addItems(items)
    if current in items:
        w.setCurrentText(current)
    return w


def check(text: str, checked: bool = False) -> QCheckBox:
    w = QCheckBox(text)
    w.setChecked(checked)
    return w


def separator() -> QFrame:
    f = QFrame()
    f.setObjectName("Separator")
    f.setFrameShape(QFrame.HLine)
    return f


def section_label(text: str) -> QLabel:
    l = QLabel(text)
    l.setObjectName("SectionTitle")
    return l


def hint_label(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color: #606080; font-size: 12px; margin-top: 4px;")
    return l
