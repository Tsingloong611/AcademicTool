# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_question_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from black.concurrency import cancel


class CustomQuestionDialog(QDialog):
    def __init__(self, title, message,position=1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 100)
        self.setStyleSheet("""
        background : white;
        color: black;

        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 问题消息
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)  # 设置文字居中
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


            """)
        else:
            no_button.setStyleSheet("""


            """)

        layout.addLayout(button_layout)
        # 设置固定的按钮宽度
        for i in range(button_layout.count()):
            button_layout.itemAt(i).widget().setFixedWidth(50)

    def ask(self):
        return self.exec() == QDialog.Accepted
