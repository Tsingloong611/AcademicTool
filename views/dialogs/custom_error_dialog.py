# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:52 PM
# @FileName: custom_error_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import QVBoxLayout, QDialog, QLabel, QPushButton


class CustomErrorDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
        * {
    font-family: "Microsoft YaHei", "Times New Roman", Arial, sans-serif; /* 统一字体 */
    font-size: 12pt; /* 统一字体大小 */
    color: #333333; /* 默认字体颜色 */
    text-shadow: none; /* 去除文字阴影 */
}
QDialog {
            background-color: #ffffff; /* 白色背景 */
            color: #333333;            /* 深灰色文字 */
            border: 1px solid #dcdcdc; /* 浅灰色边框 */
            border-radius: 8px;        /* 圆角边框 */
        }

        QDialog QLabel {
            background: transparent; /* 背景透明 */
            color: #333333;          /* 深灰色文字 */
            font-size: 12pt;         /* 字体大小 */
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
        }

        QDialog QPushButton {
            padding: 8px 16px;
            font-size: 12pt;
            border: 1px solid #0078d7; /* 蓝色边框 */
            border-radius: 6px;
            background-color: #0078d7; /* 蓝色背景 */
            color: #ffffff;
            transition: background-color 0.3s, border-color 0.3s;
        }

        QDialog QPushButton:hover {
            background-color: #005a9e; /* 深蓝色背景 */
            border-color: #005a9e;
        }

        QDialog QPushButton:pressed {
            background-color: #004578; /* 更深蓝色背景 */
            border-color: #00315b;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 错误图标和消息内容
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(label)

        # 确定按钮
        button = QPushButton("确定")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

    def show_dialog(self):
        self.exec()
