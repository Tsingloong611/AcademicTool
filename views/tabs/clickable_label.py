# -*- coding: utf-8 -*-
# @Time    : 12/4/2024 2:35 PM
# @FileName: clickable_label.py
# @Software: PyCharm
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手形，提示可点击

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发射点击信号
        super().mousePressEvent(event)