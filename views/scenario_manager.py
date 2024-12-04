from PySide6.QtGui import QIcon, QFont, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
    QMessageBox, QLineEdit, QListWidgetItem, QToolTip, QFrame, QLabel
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPoint



class CustomToolTip(QLabel):
    def __init__(self, text, parent=None, duration=3000):
        super().__init__(parent)

        # 设置提示框的文本
        self.setText(text)

        # 设置样式表，定义圆角、背景色、阴影等
        self.setStyleSheet("""
            QLabel {
                background-color: #f7f7f7;
                color: #333333;
                border: none;             /* 去掉边框 */
                border-radius: 8px;       /* 圆角 */
                padding: 8px;             /* 内边距 */
                font-size: 11pt;          /* 字体大小 */
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.15); /* 添加轻微阴影 */
            }
        """)

        # 设置窗口类型为 ToolTip，无边框和阴影
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        # 创建定时器，用于控制提示框的显示时间
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # 只触发一次
        self.timer.timeout.connect(self.hide)  # 超时后隐藏提示框
        self.timer.start(duration)  # 设置显示时长（毫秒）

    def show_at(self, pos):
        """显示提示框在指定位置"""
        self.move(pos)  # 移动到指定位置
        self.show()  # 显示提示框

class ScenarioManager(QWidget):
    scenario_selected = Signal(int, str, str)
    add_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("ScenarioManager")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.current_tooltip = None  # 用于追踪当前显示的 ToolTip


        # 查找功能（只保留输入框和按钮）
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入情景名称进行查找...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setFixedHeight(40)
        self.search_button = QPushButton("查找")
        self.search_button.setIcon(QIcon("resources/icons/search.png"))
        self.search_button.setToolTip("查找情景")
        self.search_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.search_button.setFixedHeight(40)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 设置按钮间距
        button_layout.setContentsMargins(0, 10, 0, 10)  # 设置上下左右的外边距
        self.add_button = QPushButton("➕ 增加")
        self.add_button.setIcon(QIcon("resources/icons/add.png"))
        self.add_button.setToolTip("增加新情景")
        self.add_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.add_button.setFixedHeight(40)

        self.edit_button = QPushButton("✏️ 修改")
        self.edit_button.setIcon(QIcon("resources/icons/edit.png"))
        self.edit_button.setToolTip("修改选中的情景")
        self.edit_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.edit_button.setFixedHeight(40)

        self.delete_button = QPushButton("❌ 删除")
        self.delete_button.setIcon(QIcon("resources/icons/delete.png"))
        self.delete_button.setToolTip("删除选中的情景")
        self.delete_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.delete_button.setFixedHeight(40)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        # 情景列表
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ScenarioList")
        self.list_widget.setMouseTracking(True)  # 开启鼠标追踪以支持悬浮提示
        layout.addWidget(self.list_widget)

        # 信号与槽
        self.add_button.clicked.connect(self.add_requested.emit)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        self.search_button.clicked.connect(self.search_scenario)
        self.list_widget.itemClicked.connect(self.select_scenario)
        self.list_widget.itemEntered.connect(self.show_tooltip)  # 悬浮显示描述




        self.list_widget.setFocusPolicy(Qt.NoFocus)

    @Slot(QListWidgetItem)
    def select_scenario(self, item):
        scenario_id = item.data(Qt.UserRole)
        scenario_name = item.text().split(" - ")[0]  # 仅获取名称部分
        scenario_description = item.data(Qt.UserRole + 1)

        reply = QMessageBox.question(
            self, '确认选择', f'您确定要选择情景 "{scenario_name}" 吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.scenario_selected.emit(scenario_id, scenario_name, scenario_description)
        else:
            QMessageBox.information(self, "取消选择", "您已取消选择情景。")

    @Slot(list)
    def populate_scenarios(self, scenarios):
        """填充情景列表"""
        self.list_widget.clear()
        self.scenarios = scenarios  # 存储完整的情景数据以支持查找功能
        for scenario in scenarios:
            description = scenario.description
            # 如果描述超过8个字，用 "..." 替代
            if len(description) > 8:
                description = description[:8] + "..."
            item = QListWidgetItem(f"{scenario.name} - {description}")
            item.setData(Qt.UserRole, scenario.id)
            item.setData(Qt.UserRole + 1, scenario.description)
            self.list_widget.addItem(item)

    @Slot()
    def search_scenario(self):
        """查找情景"""
        query = self.search_input.text().strip().lower()
        if not query:
            QMessageBox.warning(self, "查找失败", "请输入情景名称进行查找。")
            return

        self.list_widget.clear()
        for scenario in self.scenarios:
            if query in scenario.name.lower():  # 忽略大小写匹配
                description = scenario.description
                if len(description) > 8:
                    description = description[:8] + "..."
                item = QListWidgetItem(f"{scenario.name} - {description}")
                item.setData(Qt.UserRole, scenario.id)
                item.setData(Qt.UserRole + 1, scenario.description)
                self.list_widget.addItem(item)

        if self.list_widget.count() == 0:
            QMessageBox.information(self, "无结果", "未找到匹配的情景，请尝试其他关键字。")

    @Slot(QListWidgetItem)
    def show_tooltip(self, item):
        """鼠标悬浮显示完整描述"""
        if item:
            full_description = item.data(Qt.UserRole + 1)  # 获取完整描述

            # 隐藏上一个提示框
            if self.current_tooltip:
                self.current_tooltip.hide()
                self.current_tooltip.deleteLater()  # 删除之前的提示框

            # 计算显示位置（鼠标下方偏移一点）
            mouse_pos = QCursor.pos()  # 获取全局鼠标位置
            offset_pos = QPoint(mouse_pos.x() + 10, mouse_pos.y() + 20)  # 向右和向下偏移

            # 创建新的 ToolTip
            self.current_tooltip = CustomToolTip(full_description, self, duration=5000)  # 显示 5 秒
            self.current_tooltip.show_at(offset_pos)

    def leaveEvent(self, event):
        """鼠标离开时隐藏提示框"""
        if self.current_tooltip:
            self.current_tooltip.hide()
            self.current_tooltip.deleteLater()
            self.current_tooltip = None
        super().leaveEvent(event)