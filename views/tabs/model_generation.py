# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: model_generation.py
# @Software: PyCharm

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ModelGenerationTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("情景模型生成内容展示区域")
        layout.addWidget(label)
        # 这里添加具体的控件和布局