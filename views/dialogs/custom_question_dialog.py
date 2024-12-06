# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_question_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from black.concurrency import cancel


class CustomQuestionDialog(QDialog):
    def __init__(self, title, message,position=1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(200, 100)
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

        # 问题消息
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 按钮布局
        button_layout = QHBoxLayout()

        yes_button = QPushButton("确认")
        yes_button.clicked.connect(self.accept)
        button_layout.addWidget(yes_button)


        no_button = QPushButton("取消")
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(no_button)
        if position == 1:
            yes_button.setStyleSheet("""
                QPushButton {
                    background-color: white; /* 设置背景颜色为白色 */
                    color: black;           /* 设置文字颜色为黑色 */
                }
                QPushButton:pressed {
                    background-color: lightgray; /* 按钮被按下时的背景色 */
                }
            """)
        else:
            no_button.setStyleSheet("""
                QPushButton {
                    background-color: white; /* 设置背景颜色为白色 */
                    color: black;           /* 设置文字颜色为黑色 */
                }
                QPushButton:pressed {
                    background-color: lightgray; /* 按钮被按下时的背景色 */
                }
            """)

        layout.addLayout(button_layout)

    def ask(self):
        return self.exec() == QDialog.Accepted
