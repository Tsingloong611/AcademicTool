from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget, QLabel

class CenterAlignedComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)  # 启用编辑模式，便于控制对齐
        self.lineEdit().setReadOnly(True)  # 禁止实际编辑内容
        self.lineEdit().setAlignment(Qt.AlignCenter)  # 设置文本居中对齐


    def showPopup(self):
        super().showPopup()
        # 让下拉选项文本也居中
        self.view().setTextElideMode(Qt.ElideNone)  # 禁用省略模式


app = QApplication([])

# 创建主窗口
window = QWidget()
layout = QVBoxLayout(window)

# 使用自定义居中对齐的 QComboBox
combo_box = CenterAlignedComboBox()
combo_box.addItems(["选项 1", "选项 2", "选项 3"])

layout.addWidget(combo_box)

# 添加其他内容（可选）
label = QLabel("测试 QComboBox 的当前选项居中显示")
layout.addWidget(label)

window.show()

app.exec()
