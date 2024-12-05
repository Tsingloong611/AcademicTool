from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton, \
    QGroupBox, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal

class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class CustomCheckBoxWithLabel(QWidget):
    def __init__(self, label_text, is_last=False):
        super().__init__()
        self.init_ui(label_text, is_last)

    def init_ui(self, label_text, is_last):
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.label = ClickableLabel(label_text)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if is_last:
            layout.addStretch(0)  # 不添加额外的弹性空间，标签靠右对齐
        else:
            layout.addStretch(1)  # 添加弹性空间，标签居中

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)

        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        self.label.clicked.connect(self.on_label_clicked)

    def on_checkbox_clicked(self):
        print(f"Checkbox clicked, objectName: '{self.checkbox.objectName()}'")

    def on_label_clicked(self):
        print(f"Label clicked, objectName: '{self.label.objectName()}'")

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setFixedSize(400, 300)

        group_box = QGroupBox("测试勾选框与标签")
        group_layout = QGridLayout()
        categories = ["道路环境要素", "气象环境要素", "车辆致灾要素", "道路承灾要素"]
        for i, category in enumerate(categories):
            checkbox_label = CustomCheckBoxWithLabel(category)
            group_layout.addWidget(checkbox_label, i // 2, i % 2)

        # 设置每行的拉伸因子
        for i in range(group_layout.rowCount()):
            group_layout.setRowStretch(i, 1)

        # 设置每列的拉伸因子
        for j in range(group_layout.columnCount()):
            group_layout.setColumnStretch(j, 1)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()