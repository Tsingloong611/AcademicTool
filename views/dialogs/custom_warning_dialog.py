# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:52 PM
# @FileName: custom_warning_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class CustomWarningDialog(QDialog):
    def __init__(self, title, message, buttons=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 100)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 消息内容
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
        background : white;
        color: black;

""")

        # 按钮布局
        button_layout = QHBoxLayout()
        self.result = None

        for text, role in buttons or [("确定", "accept")]:
            button = QPushButton(text)
            button.clicked.connect(self.accept if role == "accept" else self.reject)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        # 设置固定的按钮宽度
        for i in range(button_layout.count()):
            button_layout.itemAt(i).widget().setFixedWidth(50)

    def get_result(self):
        return self.exec()
