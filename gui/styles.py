# -*- coding: utf-8 -*-

DARK_THEME = """
/* === 全局 === */
QWidget {
    background-color: #1a1b2e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #13141f;
}

/* === 标签页 === */
QTabWidget::pane {
    border: none;
    background-color: #1a1b2e;
    border-radius: 8px;
}

QTabBar::tab {
    background: transparent;
    color: #8888aa;
    padding: 10px 24px;
    margin-right: 4px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #7c8aff;
    border-bottom: 2px solid #7c8aff;
    background: rgba(124, 138, 255, 0.08);
}

QTabBar::tab:hover:!selected {
    color: #b0b8ff;
    background: rgba(124, 138, 255, 0.04);
}

/* === 分组框 === */
QGroupBox {
    background-color: #1f2036;
    border: 1px solid #2a2b4a;
    border-radius: 10px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    color: #b0b8ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #b0b8ff;
}

/* === 滚动区域 === */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #1a1b2e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3a3b5c;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 8px;
    background: #1a1b2e;
}

QScrollBar::handle:horizontal {
    background: #3a3b5c;
    border-radius: 4px;
}

/* === 输入框 === */
QLineEdit {
    background-color: #13141f;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
    selection-background-color: #7c8aff;
}

QLineEdit:focus {
    border: 1px solid #7c8aff;
    background-color: #161728;
}

QLineEdit:hover:!focus {
    border: 1px solid #3e3f6e;
}

QLineEdit:disabled {
    background-color: #1f2036;
    color: #555;
}

QLineEdit::placeholder {
    color: #555577;
}

/* === 多行文本 === */
QPlainTextEdit, QTextEdit {
    background-color: #13141f;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 10px;
    color: #e0e0e0;
    font-size: 13px;
    selection-background-color: #7c8aff;
}

QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #7c8aff;
}

/* === 下拉框 === */
QComboBox {
    background-color: #13141f;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
    min-width: 140px;
}

QComboBox:hover { border: 1px solid #3e3f6e; }
QComboBox:focus { border: 1px solid #7c8aff; }

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1px solid #2a2b4a;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #1f2036;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #7c8aff;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: rgba(124, 138, 255, 0.15);
}

/* === 复选框 === */
QCheckBox {
    spacing: 8px;
    color: #c0c0d0;
    font-size: 13px;
    padding: 4px 0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3a3b5c;
    border-radius: 4px;
    background: #13141f;
}

QCheckBox::indicator:hover {
    border: 2px solid #5a5b8c;
}

QCheckBox::indicator:checked {
    background: #7c8aff;
    border: 2px solid #7c8aff;
}

/* === 数字框 === */
QSpinBox {
    background-color: #13141f;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}

QSpinBox:hover { border: 1px solid #3e3f6e; }
QSpinBox:focus { border: 1px solid #7c8aff; }

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: #1f2036;
    width: 22px;
    border-radius: 3px;
    margin: 2px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #2f2f5e;
}

/* === 按钮 === */
QPushButton {
    background-color: #27284a;
    color: #c0c0ff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #32336a;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #25255a;
}

QPushButton:disabled {
    background-color: #1f2040;
    color: #555577;
}

QPushButton#PrimaryBtn {
    background-color: #7c8aff;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#PrimaryBtn:hover {
    background-color: #96a0ff;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #6570e0;
}

QPushButton#SuccessBtn {
    background-color: #34d399;
    color: #0f172a;
    font-weight: 600;
}

QPushButton#SuccessBtn:hover {
    background-color: #4ade80;
}

QPushButton#SuccessBtn:pressed {
    background-color: #2eb88a;
}

QPushButton#SuccessBtn:disabled {
    background-color: #1a4d3a;
    color: #555;
}

/* === 标签 === */
QLabel {
    color: #a0a0c0;
    background: transparent;
}

QLabel#SectionTitle {
    color: #b0b8ff;
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
}

/* === 分割线 === */
QFrame#Separator {
    background-color: #2a2b4a;
    min-height: 1px;
    max-height: 1px;
}

/* === 状态栏 === */
QStatusBar {
    background-color: #13141f;
    color: #707088;
    border-top: 1px solid #2a2b4a;
    padding: 4px 12px;
    font-size: 12px;
}

QStatusBar::item {
    border: none;
}

/* === 日志输出区 === */
QTextEdit#LogOutput {
    background-color: #0d0e1a;
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    font-family: "Cascadia Code", "Consolas", "JetBrains Mono", monospace;
    font-size: 12px;
    color: #a0b0c0;
    padding: 10px;
}

/* === 自定义标题栏 === */
QWidget#TitleBar {
    background-color: #13141f;
    border-bottom: 1px solid #2a2b4a;
}

QLabel#TitleBarTitle {
    color: #e0e0ff;
    font-size: 14px;
    font-weight: 700;
    background: transparent;
    padding-left: 4px;
}

QPushButton#TitleBarBtn {
    background: transparent;
    color: #707088;
    border: none;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 18px;
    font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
    min-width: 36px;
    min-height: 32px;
    max-width: 36px;
    max-height: 32px;
}

QPushButton#TitleBarBtn:hover {
    background-color: #2a2b4a;
    color: #c0c0d0;
}

QPushButton#TitleBarBtnClose {
    background: transparent;
    color: #707088;
    border: none;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 16px;
    font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
    min-width: 36px;
    min-height: 32px;
    max-width: 36px;
    max-height: 32px;
}

QPushButton#TitleBarBtnClose:hover {
    background-color: #e81123;
    color: #ffffff;
}

QPushButton#TitleBarBtnClose:pressed {
    background-color: #c50f1f;
    color: #ffffff;
}

QMainWindow {
    border: 1px solid #2a2b4a;
}
"""


LIGHT_THEME = """
/* === 全局 === */
QWidget {
    background-color: #f8f9fc;
    color: #1e1e2e;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #eef0f6;
}

/* === 标签页 === */
QTabWidget::pane {
    border: none;
    background-color: #f8f9fc;
    border-radius: 8px;
}

QTabBar::tab {
    background: transparent;
    color: #8b8ba0;
    padding: 10px 24px;
    margin-right: 4px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #6366f1;
    border-bottom: 2px solid #6366f1;
    background: rgba(99, 102, 241, 0.06);
}

QTabBar::tab:hover:!selected {
    color: #818cf8;
    background: rgba(99, 102, 241, 0.03);
}

/* === 分组框 === */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    color: #6366f1;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #6366f1;
}

/* === 滚动区域 === */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #f1f3f8;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 8px;
    background: #f1f3f8;
}

QScrollBar::handle:horizontal {
    background: #d1d5db;
    border-radius: 4px;
}

/* === 输入框 === */
QLineEdit {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1e1e2e;
    font-size: 13px;
    selection-background-color: #6366f1;
}

QLineEdit:focus {
    border: 1px solid #6366f1;
    background-color: #ffffff;
}

QLineEdit:hover:!focus {
    border: 1px solid #c7c8d8;
}

QLineEdit:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
}

QLineEdit::placeholder {
    color: #9ca3af;
}

/* === 多行文本 === */
QPlainTextEdit, QTextEdit {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 10px;
    color: #1e1e2e;
    font-size: 13px;
    selection-background-color: #6366f1;
}

QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #6366f1;
    background-color: #ffffff;
}

/* === 下拉框 === */
QComboBox {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1e1e2e;
    font-size: 13px;
    min-width: 140px;
}

QComboBox:hover { border: 1px solid #c7c8d8; }
QComboBox:focus { border: 1px solid #6366f1; }

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1px solid #e5e7eb;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: rgba(99, 102, 241, 0.08);
}

/* === 复选框 === */
QCheckBox {
    spacing: 8px;
    color: #4b5563;
    font-size: 13px;
    padding: 4px 0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}

QCheckBox::indicator:hover {
    border: 2px solid #818cf8;
}

QCheckBox::indicator:checked {
    background: #6366f1;
    border: 2px solid #6366f1;
}

/* === 数字框 === */
QSpinBox {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1e1e2e;
    font-size: 13px;
}

QSpinBox:hover { border: 1px solid #c7c8d8; }
QSpinBox:focus { border: 1px solid #6366f1; }

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: #e5e7eb;
    width: 22px;
    border-radius: 3px;
    margin: 2px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #d1d5db;
}

/* === 按钮 === */
QPushButton {
    background-color: #e5e7eb;
    color: #374151;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #d1d5db;
    color: #1e1e2e;
}

QPushButton:pressed {
    background-color: #c7c8d8;
}

QPushButton:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
}

QPushButton#PrimaryBtn {
    background-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#PrimaryBtn:hover {
    background-color: #818cf8;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #4f46e5;
}

QPushButton#SuccessBtn {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#SuccessBtn:hover {
    background-color: #34d399;
}

QPushButton#SuccessBtn:pressed {
    background-color: #059669;
}

QPushButton#SuccessBtn:disabled {
    background-color: #d1fae5;
    color: #6ee7b7;
}

/* === 标签 === */
QLabel {
    color: #6b7280;
    background: transparent;
}

QLabel#SectionTitle {
    color: #6366f1;
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
}

/* === 分割线 === */
QFrame#Separator {
    background-color: #e5e7eb;
    min-height: 1px;
    max-height: 1px;
}

/* === 状态栏 === */
QStatusBar {
    background-color: #eef0f6;
    color: #9ca3af;
    border-top: 1px solid #e5e7eb;
    padding: 4px 12px;
    font-size: 12px;
}

QStatusBar::item {
    border: none;
}

/* === 日志输出区 === */
QTextEdit#LogOutput {
    background-color: #1e1e2e;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-family: "Cascadia Code", "Consolas", "JetBrains Mono", monospace;
    font-size: 12px;
    color: #d1d5db;
    padding: 10px;
}

/* === 自定义标题栏 === */
QWidget#TitleBar {
    background-color: #eef0f6;
    border-bottom: 1px solid #e5e7eb;
}

QLabel#TitleBarTitle {
    color: #1e1e2e;
    font-size: 14px;
    font-weight: 700;
    background: transparent;
    padding-left: 4px;
}

QPushButton#TitleBarBtn {
    background: transparent;
    color: #6b7280;
    border: none;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 18px;
    font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
    min-width: 36px;
    min-height: 32px;
    max-width: 36px;
    max-height: 32px;
}

QPushButton#TitleBarBtn:hover {
    background-color: #e5e7eb;
    color: #374151;
}

QPushButton#TitleBarBtnClose {
    background: transparent;
    color: #6b7280;
    border: none;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 16px;
    font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
    min-width: 36px;
    min-height: 32px;
    max-width: 36px;
    max-height: 32px;
}

QPushButton#TitleBarBtnClose:hover {
    background-color: #e81123;
    color: #ffffff;
}

QPushButton#TitleBarBtnClose:pressed {
    background-color: #c2414b;
    color: #ffffff;
}"""
