# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_information_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class CustomInformationDialog(QDialog):
    def __init__(self, title, message, buttons=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(250, 100)
        self.setStyleSheet("""* {
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

        # 信息内容
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.result = None

        for text, role in buttons or [("确认", "accept")]:
            button = QPushButton(text)
            button.clicked.connect(self.accept if role == "accept" else self.reject)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

    def get_result(self):
        return self.exec()
