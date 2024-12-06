# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_input_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import QVBoxLayout, QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton


class CustomInputDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 消息
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 输入框
        self.input_field = QLineEdit()
        layout.addWidget(self.input_field)

        # 按钮布局
        button_layout = QHBoxLayout()

        ok_button = QPushButton("确认")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def get_input(self):
        if self.exec() == QDialog.Accepted:
            return self.input_field.text()
        return None
