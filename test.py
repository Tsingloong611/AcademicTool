from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置主窗口标题
        self.setWindowTitle("布局示例")
        self.setObjectName("MainWindow")

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建左侧容器的QFrame
        left_container_frame = QFrame()
        left_container_frame.setObjectName("LeftContainerFrame")
        left_layout = QVBoxLayout(left_container_frame)

        # 创建左侧上部分的QFrame
        left_top_frame = QFrame()
        left_top_frame.setObjectName("LeftTopFrame")
        left_top_layout = QVBoxLayout(left_top_frame)
        left_top_label = QLabel("左侧上部分")
        left_top_layout.addWidget(left_top_label)

        # 创建左侧下部分的QFrame
        left_bottom_frame = QFrame()
        left_bottom_frame.setObjectName("LeftBottomFrame")
        left_bottom_layout = QVBoxLayout(left_bottom_frame)
        left_bottom_label = QLabel("左侧下部分")
        left_bottom_layout.addWidget(left_bottom_label)

        # 添加左侧上部分和下部分到左侧容器布局，并设置比例
        left_layout.addWidget(left_top_frame, stretch=3)
        left_layout.addWidget(left_bottom_frame, stretch=1)

        # 创建右侧容器的QFrame
        right_container_frame = QFrame()
        right_container_frame.setObjectName("RightContainerFrame")
        right_layout = QVBoxLayout(right_container_frame)
        right_label = QLabel("右侧大部分")
        right_layout.addWidget(right_label)

        # 将左侧和右侧容器的QFrame添加到主布局，并设置比例
        main_layout.addWidget(left_container_frame, stretch=1)
        main_layout.addWidget(right_container_frame, stretch=4)

# 运行应用程序
app = QApplication([])
window = MainWindow()
window.show()
app.exec()