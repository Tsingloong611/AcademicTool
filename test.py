from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox
from PySide6.QtGui import QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("自定义箭头图标示例")

        # 创建下拉框
        combo_box = QComboBox(self)
        combo_box.setGeometry(50, 50, 200, 30)

        # 添加选项
        combo_box.addItems(["选项1", "选项2", "选项3"])

        # 自定义样式表
        combo_box.setStyleSheet("""
            QComboBox {
                border: 1px solid gray;
                border-radius: 5px;
                padding-right: 30px; /* 留出箭头空间 */
            }
            QComboBox::drop-down {
                border: none; /* 隐藏下拉按钮边框 */
                width: 20px; /* 下拉按钮宽度 */
            }
            QComboBox::down-arrow {
                image: url(edit.png); /* 自定义箭头路径 */
                width: 16px;
                height: 16px;
            }
        """)

        # 检查自定义图标是否正确加载
        self.check_icon_availability()

        self.setCentralWidget(combo_box)

    def check_icon_availability(self):
        # 确保箭头图标文件存在
        pixmap = QPixmap("arrow.png")
        if pixmap.isNull():
            print("图标未正确加载！请确保 'arrow.png' 文件存在于项目目录中。")

if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.resize(300, 200)
    window.show()

    app.exec()
