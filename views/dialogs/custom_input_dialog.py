# -*- coding: utf-8 -*-
# @Time    : 12/6/2024 5:53 PM
# @FileName: custom_input_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton


class CustomInputDialog(QDialog):
    accepted_text = Signal(str)

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 150)
        self.setStyleSheet("""
        background : white;
        color: black;

                    QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """)

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

        ok_button = QPushButton(self.tr("确认"))
        ok_button.clicked.connect(self._accept_input)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton(self.tr("取消"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        # 设置固定的按钮宽度
        for i in range(button_layout.count()):
            button_layout.itemAt(i).widget().setFixedWidth(50)

    def get_input(self):
        return self.input_field.text()


    def _accept_input(self):
        txt = self.get_input()
        self.accepted_text.emit(txt)
        self.close()
