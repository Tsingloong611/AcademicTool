# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: element_setting.py
# @Software: PyCharm
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QGroupBox, QGridLayout, QSpacerItem,
    QSizePolicy
)

class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手形，提示可点击

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发射点击信号
        super().mousePressEvent(event)

class CustomCheckBoxWithLabel(QWidget):
    def __init__(self, label_text):
        super().__init__()
        self.init_ui(label_text)

    def init_ui(self, label_text):
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.checkbox.setMinimumSize(20, 20)  # 设置勾选框的最小尺寸

        self.label = ClickableLabel(label_text)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label.setMinimumHeight(20)  # 设置标签的最小高度
        # 给checkbox和label设置标识，这里使用objectName
        self.checkbox.setObjectName(label_text)
        self.label.setObjectName(label_text)
        # 使用样式表调整勾选框的外观
        self.checkbox.setStyleSheet("QCheckBox { margin: 0px; }")

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)

        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        self.label.clicked.connect(self.on_label_clicked)

    def on_checkbox_clicked(self):
        print(f"Checkbox clicked, objectName: '{self.checkbox.objectName()}'")

    def on_label_clicked(self):
        print(f"Label clicked, objectName: '{self.label.objectName()}'")

class LineEditWidget(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text)
        self.line_edit = QLineEdit()
        self.line_edit.setFixedWidth(100)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)

class ElementSettingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)

        # 情景要素类别选择区域
        element_group_box = QGroupBox("涉及的情景要素")
        element_layout = QGridLayout()
        categories = [
            "道路环境要素", "气象环境要素", "车辆致灾要素",
            "车辆致灾要素", "道路承灾要素", "人类承灾要素", "应急资源要素",
            "应急行为要素"
        ]
        self.checkboxes = {}
        for i, category in enumerate(categories):
            checkbox = CustomCheckBoxWithLabel(category)
            self.checkboxes[category] = checkbox
            row = i // 4  # 计算行号
            column = i % 4  # 计算列号

            alignment = Qt.AlignCenter

            element_layout.addWidget(checkbox, row, column, 1, 1, alignment)  # 添加组件并设置对齐方式
        element_group_box.setLayout(element_layout)


        # 属性模型区域
        attribute_group_box = QGroupBox("属性模型")
        attribute_layout = QGridLayout()
        attribute_layout.setSpacing(0)  # 设置布局中的控件间隔为0
        attribute_labels = [
            "道路名称", "道路类型", "行车道数",
            "起始桩号", "终点桩号", "封闭情况",
            "受损情况", "污染情况"
        ]
        self.attribute_inputs = {}
        for i, label_text in enumerate(attribute_labels):
            print(label_text)
            line_edit_widget = LineEditWidget(label_text)
            attribute_layout.addWidget(line_edit_widget, i // 2, (i % 2) * 2, Qt.AlignCenter)

        attribute_group_box.setLayout(attribute_layout)

        # 行为模型区域
        behavior_group_box = QGroupBox("行为模型")
        behavior_layout = QVBoxLayout()
        self.behavior_label = QLabel("该要素不具备行为模型")
        self.behavior_label.setAlignment(Qt.AlignCenter)
        behavior_layout.addWidget(self.behavior_label)
        behavior_group_box.setLayout(behavior_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: white; /* 设置背景颜色为白色 */
                color: black;           /* 设置文字颜色为黑色 */
            }
            QPushButton:pressed {
                background-color: lightgray; /* 按钮被按下时的背景色 */
            }
        """)
        self.generate_button = QPushButton("生成情景孪生模型")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.generate_button)

        # 将各部分加入主布局
        main_layout.addWidget(element_group_box)
        main_layout.addWidget(attribute_group_box)
        main_layout.addWidget(behavior_group_box)
        main_layout.addLayout(button_layout)
        for category, checkbox in self.checkboxes.items():
            checkbox.setVisible(True)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = ElementSettingTab()
    window.show()
    app.exec()
