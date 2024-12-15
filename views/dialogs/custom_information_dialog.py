# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_information_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class CustomInformationDialog(QDialog):
    def __init__(self, title, message, buttons=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 100)
        self.setStyleSheet("""


                """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 信息内容
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)  # 设置文字居中
        layout.addWidget(label)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.result = None

        for text, role in buttons or [("确认", "accept")]:
            button = QPushButton(text)
            button.clicked.connect(self.accept if role == "accept" else self.reject)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        # 设置固定的按钮宽度
        for i in range(button_layout.count()):
            button_layout.itemAt(i).widget().setFixedWidth(50)

    def get_result(self):
        return self.exec()
