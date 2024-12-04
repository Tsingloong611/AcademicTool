# main_window.py

import sys
import os

from PySide6.QtWidgets import QMainWindow, QDockWidget, QApplication, QFrame, QMessageBox, QVBoxLayout
from PySide6.QtCore import Qt, Slot
from views.scenario_manager import ScenarioManager
from views.status_bar import StatusBar
from views.tabs.tab_widget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("情景管理系统")
        self.resize(1200, 600)

        # 设置样式
        self.load_styles()

        # 创建中央部件：标签页
        self.tab_widget = TabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建情景管理器的 QDockWidget
        self.create_scenario_manager_dock()

        # 创建状态栏的 QDockWidget
        self.create_status_bar_dock()

        # 根据情景是否存在设置占位消息
        self.update_placeholder_message()

    def create_scenario_manager_dock(self):
        # 创建 QDockWidget
        dock = QDockWidget("情景管理器", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )

        dock.setObjectName("ScenarioManagerDock")  # 设置对象名称以便查找

        # 创建一个透明背景的 QFrame 作为容器
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 设置情景管理器作为 QFrame 的内容
        self.scenario_manager = ScenarioManager()
        layout.addWidget(self.scenario_manager)

        # 将 QFrame 设置为 QDockWidget 的内容
        dock.setWidget(frame)

        # 将 QDockWidget 添加到主窗口的左侧
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # 连接信号
        self.scenario_manager.scenario_selected.connect(self.handle_scenario_selected)
        self.scenario_manager.add_requested.connect(self.handle_add_requested)
        self.scenario_manager.edit_requested.connect(self.handle_edit_requested)
        self.scenario_manager.delete_requested.connect(self.handle_delete_requested)

    def create_status_bar_dock(self):
        # 创建 QDockWidget
        dock_status = QDockWidget("状态栏", self)
        dock_status.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_status.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetFloatable
        )

        dock_status.setObjectName("StatusBarDock")  # 设置对象名称以便查找

        # 创建一个带边框和圆角的 QFrame 作为容器
        frame_status = QFrame()
        frame_status.setStyleSheet("""
            QFrame {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        layout_status = QVBoxLayout(frame_status)
        layout_status.setContentsMargins(10, 10, 10, 10)
        layout_status.setSpacing(10)

        # 设置状态栏作为 QFrame 的内容
        self.status_bar_widget = StatusBar()
        self.status_bar_widget.setObjectName("StatusBarWidget")  # 用于样式表
        layout_status.addWidget(self.status_bar_widget)

        # 将 QFrame 设置为 QDockWidget 的内容
        dock_status.setWidget(frame_status)

        # 将 QDockWidget 添加到主窗口的左侧
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_status)

        # 获取两个 DockWidget
        scenario_dock = self.findChild(QDockWidget, "ScenarioManagerDock")
        status_dock = self.findChild(QDockWidget, "StatusBarDock")

        if scenario_dock and status_dock:
            # 使用 splitDockWidget 将状态栏 dock 分割到情景管理器 dock 的下方
            self.splitDockWidget(scenario_dock, status_dock, Qt.Vertical)
            # 设置情景管理器和状态栏的初始高度比例为3:1
            # 总高度为600，比例3:1，即450:150
            self.resizeDocks([scenario_dock, status_dock], [450, 150], Qt.Vertical)
        else:
            # 如果找不到 dock，添加到左侧
            self.addDockWidget(Qt.LeftDockWidgetArea, dock_status)

    @Slot(int, str, str)
    def handle_scenario_selected(self, scenario_id, scenario_name, scenario_description):
        user = "当前用户: 用户名"  # 替换为实际的用户信息
        database = "当前数据库: 数据库名称"  # 替换为实际的数据库信息
        owl_status = "正常"  # 或根据实际情况设置
        bayes_status = "正常"  # 或根据实际情况设置
        self.status_bar_widget.update_status(user, database, scenario_name, owl_status, bayes_status, scenario_description)

    @Slot()
    def handle_add_requested(self):
        """
        处理增加情景后的逻辑。
        例如，更新占位消息。
        """
        self.update_placeholder_message()

    @Slot(int)
    def handle_edit_requested(self, scenario_id):
        """
        处理编辑情景后的逻辑。
        例如，更新状态栏或占位消息。
        """
        self.update_placeholder_message()

    @Slot(int)
    def handle_delete_requested(self, scenario_id):
        """
        处理删除情景后的逻辑。
        例如，更新占位消息。
        """
        self.update_placeholder_message()

    def load_styles(self):
        """加载拆分后的样式表"""
        styles_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "styles")
        style_files = [
            "global.qss",
            "mainwindow.qss",
            "dockwidget.qss",
            "button.qss",
            "listwidget.qss",
            "tabwidget.qss",
            "tooltip.qss",
            "messagebox.qss",
            "dialog.qss"
        ]

        combined_style = ""
        for style_file in style_files:
            path = os.path.join(styles_dir, style_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    combined_style += f.read() + "\n"
                print(f"Loaded {style_file} successfully.")  # 添加调试信息
            except Exception as e:
                print(f"Error loading {style_file}: {e}")

        self.setStyleSheet(combined_style)

    def update_placeholder_message(self):
        """
        根据情景是否存在，更新 TabWidget 的占位消息。
        """
        if hasattr(self.scenario_manager, 'scenarios') and self.scenario_manager.scenarios:
            self.tab_widget.show_placeholder(has_scenarios=True)
        else:
            self.tab_widget.show_placeholder(has_scenarios=False)


