# scenario_manager.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
    QMessageBox, QLineEdit, QListWidgetItem, QFrame, QLabel, QDialog, QTextEdit
)
from PySide6.QtGui import QIcon, QFont, QCursor
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPoint, QEvent


class ScenarioDialog(QDialog):
    def __init__(self, parent=None, scenario=None):
        super().__init__(parent)
        self.setWindowTitle("情景信息")
        self.scenario = scenario
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 描述输入
        desc_layout = QVBoxLayout()
        desc_label = QLabel("描述:")
        self.desc_input = QTextEdit()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)

        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 连接信号
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 如果是编辑模式，填充现有数据
        if self.scenario:
            self.name_input.setText(self.scenario.name)
            self.desc_input.setText(self.scenario.description)

    def get_data(self):
        """获取输入的数据"""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        return name, description


class CustomToolTip(QLabel):
    def __init__(self, text, parent=None, duration=3000):
        super().__init__(parent)

        # 设置提示框的文本，如果没有内容则设置为默认文本
        self.text = text.strip() if text and text.strip() else "没有描述信息"
        self.setText(self.text)

        # 设置样式表，定义圆角、背景色、阴影等
        self.setStyleSheet("""
            QLabel {
                background-color: #f7f7f7;
                color: #333333;
                border-radius: 8px;       /* 圆角 */
                padding: 8px;             /* 内边距 */
                font-size: 11pt;          /* 字体大小 */
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2); /* 阴影效果 */
            }
        """)

        # 设置窗口类型为 ToolTip，并确保窗口保持在最前
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 创建定时器，用于控制提示框的显示时间
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # 只触发一次
        self.timer.timeout.connect(self.hide)  # 超时后隐藏提示框

        # 安装事件过滤器以捕捉鼠标事件
        self.installEventFilter(self)

    def show_at(self, pos, duration=3000):
        """
        显示提示框在指定位置并设置显示时长
        :param pos: 提示框显示的位置（全局坐标）
        :param duration: 提示框显示的时长（毫秒）
        """
        if not self.text.strip():  # 如果内容为空，不显示提示框
            return

        self.move(pos)  # 移动到指定位置
        self.show()  # 显示提示框
        self.timer.start(duration)  # 设置显示时长

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                # 鼠标进入提示框，停止定时器
                self.timer.stop()
            elif event.type() == QEvent.Leave:
                # 鼠标离开提示框，隐藏提示框
                self.hide()
        return super().eventFilter(obj, event)

class ScenarioManager(QWidget):
    scenario_selected = Signal(int, str, str)
    add_requested = Signal()
    edit_requested = Signal(int)    # 支持单选编辑
    delete_requested = Signal(int)  # 支持单选删除

    def __init__(self):
        super().__init__()

        self.setObjectName("ScenarioManager")
        self.init_ui()
        self.current_tooltip = None  # 用于追踪当前显示的 ToolTip
        self.list_widget.setFocusPolicy(Qt.NoFocus)

        # 安装事件过滤器到 list_widget 的 viewport
        self.list_widget.viewport().installEventFilter(self)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 减少整体边距
        layout.setSpacing(5)  # 减少整体间距

        # 搜索功能
        self.init_search(layout)

        # 分隔线
        self.init_separator(layout)

        # 操作按钮组
        self.init_buttons(layout)

        # 情景列表
        self.init_list_widget(layout)

    def init_search(self, parent_layout):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入情景名称进行查找...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.real_time_search)  # 实现实时搜索

        search_layout.addWidget(self.search_input)
        parent_layout.addLayout(search_layout)

    def init_separator(self, parent_layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(2)  # 确保分隔线有足够的高度显示
        line.setStyleSheet("""
            QFrame {
                background-color: #dcdcdc;  /* 设置分隔线颜色 */
            }
        """)
        parent_layout.addWidget(line)

    def init_buttons(self, parent_layout):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)  # 减少按钮之间的间距
        button_layout.setContentsMargins(0, 5, 0, 5)  # 减少按钮组的边距

        # 使用辅助方法创建按钮
        self.add_button = self.create_button("➕ 增加", "resources/icons/add.png", self.add_requested.emit)
        self.edit_button = self.create_button("✏️ 修改", "resources/icons/edit.png", self.on_edit_requested)
        self.delete_button = self.create_button("❌ 删除", "resources/icons/delete.png", self.on_delete_requested)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        parent_layout.addLayout(button_layout)

    def create_button(self, text, icon_path, callback):
        button = QPushButton(text)
        button.setIcon(QIcon(icon_path))
        button.setToolTip(text)
        button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        button.setFixedHeight(35)  # 调整按钮高度
        button.clicked.connect(callback)
        return button

    def init_list_widget(self, parent_layout):
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ScenarioList")
        self.list_widget.setMouseTracking(True)  # 开启鼠标追踪以支持悬浮提示
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)  # 支持单选
        parent_layout.addWidget(self.list_widget)

        # 信号与槽
        self.list_widget.itemClicked.connect(self.select_scenario)
        self.list_widget.itemEntered.connect(self.show_tooltip)  # 悬浮显示描述

        # 启用项悬浮事件
        self.list_widget.setMouseTracking(True)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("""
            QListWidget::item:hover {
                background-color: #e6f7ff;
            }
        """)

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

    @Slot(str)
    def real_time_search(self, text):
        """实时搜索情景"""
        query = text.strip().lower()
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

        if self.list_widget.count() == 0 and query:
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

            # 如果没有描述信息，设置为默认
            if not full_description.strip():
                full_description = "没有描述信息"

            # 计算显示位置（鼠标下方偏移一点）
            mouse_pos = QCursor.pos()  # 获取全局鼠标位置
            offset_pos = QPoint(mouse_pos.x() + 10, mouse_pos.y() + 20)  # 向右和向下偏移

            # 创建新的 ToolTip
            self.current_tooltip = CustomToolTip(full_description, None, duration=5000)  # 父窗口设为 None
            self.current_tooltip.show_at(offset_pos)
            self.current_tooltip.raise_()  # 确保提示框在最前

    def eventFilter(self, obj, event):
        if obj == self.list_widget.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.position().toPoint()
                item = self.list_widget.itemAt(pos)
                if not item:
                    # 鼠标不在任何项目上，隐藏工具提示
                    if self.current_tooltip:
                        print("Hiding tooltip: Mouse not over any item")
                        self.current_tooltip.hide()
                        self.current_tooltip.deleteLater()
                        self.current_tooltip = None
            elif event.type() == QEvent.Leave:
                # 鼠标离开列表区域，隐藏工具提示
                if self.current_tooltip:
                    print("Hiding tooltip: Mouse left list widget")
                    self.current_tooltip.hide()
                    self.current_tooltip.deleteLater()
                    self.current_tooltip = None
        return super().eventFilter(obj, event)

    @Slot()
    def on_edit_requested(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "修改失败", "请先选择要修改的情景。")
            return
        scenario_id = selected_items[0].data(Qt.UserRole)
        self.edit_requested.emit(scenario_id)

    @Slot()
    def on_delete_requested(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "删除失败", "请先选择要删除的情景。")
            return

        scenario_names = [item.text().split(" - ")[0] for item in selected_items]
        scenario_id = selected_items[0].data(Qt.UserRole)
        scenario_name = scenario_names[0]
        reply = QMessageBox.question(
            self, '确认删除',
            f'您确定要删除情景 "{scenario_name}" 吗?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.delete_requested.emit(scenario_id)
            QMessageBox.information(self, "删除成功", "情景已成功删除。")
        else:
            QMessageBox.information(self, "取消删除", "您已取消删除操作。")