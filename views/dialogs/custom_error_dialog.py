# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:52 PM
# @FileName: custom_error_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QDialog, QLabel, QPushButton


class CustomErrorDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 200)
        self.setStyleSheet("""
        background : white;
        color: black;
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 错误图标和消息内容
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)  # 设置文字居中
        label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(label)

        # 确定按钮
        button = QPushButton(self.tr("确定"))
        button.clicked.connect(self.accept)
        layout.addWidget(button, alignment=Qt.AlignCenter)
        # 设置固定的按钮宽度
        button.setFixedWidth(110)

    def show_dialog(self):
        self.exec()
