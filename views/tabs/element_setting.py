# -*- coding: utf-8 -*-
# @Time    : 12/7/2024 10:00 AM
# @FileName: element_setting.py
# @Software: PyCharm

from PySide6.QtCore import Signal, Qt, QObject, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QGroupBox, QGridLayout,
    QSizePolicy, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFileDialog, QFrame, QApplication, QTabWidget, QFormLayout, QTextEdit
)
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator
from PySide6.QtWidgets import QStyledItemDelegate
import sys
import json

# 假设 CustomInformationDialog 和 CustomWarningDialog 在项目的其他地方定义
# 为了完整性，这里提供简单的实现

class CustomInformationDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # 信息标签
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("确认")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

class CustomWarningDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # 警告标签
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

class CenteredItemDelegate(QStyledItemDelegate):
    """自定义委托，使 QComboBox 的下拉项内容居中显示。"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class NoWheelEventFilter(QObject):
    """事件过滤器，禁用滚轮事件。"""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            return True  # 事件被过滤，不传递下去
        return super().eventFilter(obj, event)

def create_centered_combobox(enum_values, initial_value):
    """
    创建一个居中对齐的 QComboBox，并禁用滚轮事件。
    """
    combobox = QComboBox()
    combobox.addItem("<空>")
    for item in enum_values:
        combobox.addItem(item)

    if initial_value in enum_values:
        combobox.setCurrentText(initial_value)
    else:
        combobox.setCurrentText("<空>")

    # 使 QComboBox 可编辑，以便设置对齐方式
    combobox.setEditable(True)
    # 设置 lineEdit 为只读，防止用户输入新项
    combobox.lineEdit().setReadOnly(True)
    # 设置文本居中对齐
    combobox.lineEdit().setAlignment(Qt.AlignCenter)

    # 获取 QComboBox 的视图并应用自定义委托以居中显示下拉项
    view = combobox.view()
    delegate = CenteredItemDelegate(view)
    view.setItemDelegate(delegate)

    # 安装事件过滤器以禁用滚轮事件
    no_wheel_filter = NoWheelEventFilter(combobox)
    combobox.installEventFilter(no_wheel_filter)

    return combobox

class SaveResultDialog(QDialog):
    def __init__(self, save_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存成功")
        self.setModal(True)
        self.resize(600, 400)  # 调整大小以适应内容

        layout = QVBoxLayout(self)

        # 创建一个 QTextEdit 用于显示保存的信息，并设置为只读
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(save_message)  # 使用 setHtml 方法
        text_edit.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # 默认左上对齐
        layout.addWidget(text_edit)

        # 添加一个关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手形，提示可点击
        self.default_font = self.font()
        self.selected_font = QFont(self.font())
        self.selected_font.setBold(True)
        self.uploaded = False  # 新增属性，表示是否已上传文件
        self.selected = False  # 新增属性，表示是否被选中

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发射点击信号
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()

    def set_uploaded(self, uploaded: bool):
        self.uploaded = uploaded
        self.update_style()

    def update_style(self):
        """根据上传状态和选中状态更新样式"""
        if self.uploaded:
            color = "#0078d7"  # 蓝色
        else:
            color = "black"  # 默认颜色

        if self.selected:
            self.setFont(self.selected_font)
        else:
            self.setFont(self.default_font)

        self.setStyleSheet(f"color: {color};")

class CustomCheckBoxWithLabel(QWidget):
    def __init__(self, label_text):
        super().__init__()
        self.init_ui(label_text)

    def init_ui(self, label_text):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.checkbox.setMinimumSize(20, 20)  # 设置勾选框的最小尺寸

        self.label = ClickableLabel(label_text)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label.setMinimumHeight(20)  # 设置标签的最小高度
        self.checkbox.setObjectName(label_text)
        self.label.setObjectName(label_text)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)

    def set_selected(self, selected: bool):
        self.label.set_selected(selected)

class EditBehaviorDialog(QDialog):
    def __init__(self, behavior_name, subject, obj, is_subject_enum=False, is_object_enum=False,
                 subject_enum_values=None, object_enum_values=None, parent=None):
        super().__init__(parent)
        self.init_ui(behavior_name, subject, obj, is_subject_enum, is_object_enum, subject_enum_values,
                     object_enum_values)

    def init_ui(self, behavior_name, subject, obj, is_subject_enum, is_object_enum, subject_enum_values,
                object_enum_values):
        self.setWindowTitle(f"编辑行为: {behavior_name}")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            * {
                font-family: "Microsoft YaHei", "Times New Roman", Arial, sans-serif; /* 统一字体 */
                font-size: 16pt; /* 统一字体大小 */
                color: #333333; /* 默认字体颜色 */
                text-shadow: none; /* 去除文字阴影 */
            }
            QDialog {
                background-color: #ffffff; /* 白色背景 */
                color: #333333;            /* 深灰色文字 */
                border: 1px solid #dcdcdc; /* 浅灰色边框 */
                border-radius: 8px;        /* 圆角边框 */
            }

            QDialog QLabel {
                background: transparent; /* 背景透明 */
                color: #333333;          /* 深灰色文字 */
                font-size: 14pt;         /* 字体大小 */
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }

            QDialog QPushButton {
                padding: 8px 16px;
                font-size: 14pt;
                border: 1px solid #0078d7; /* 蓝色边框 */
                border-radius: 6px;
                background-color: #0078d7; /* 蓝色背景 */
                color: #ffffff;
                transition: background-color 0.3s, border-color 0.3s;
            }

            QDialog QPushButton:hover {
                background-color: #005a9e; /* 深蓝色背景 */
                border-color: #005a9e;
            }

            QDialog QPushButton:pressed {
                background-color: #004578; /* 更深蓝色背景 */
                border-color: #00315b;
            }

            /* 输入框选中时的蓝色边框 */
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
            
        """)

        # 主布局
        layout = QVBoxLayout(self)

        # 行为名称显示（不可编辑）
        behavior_label = QLabel(f"正在编辑行为: {behavior_name}")
        behavior_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        behavior_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        layout.addWidget(behavior_label)

        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # 创建行为主体和行为对象编辑器
        self.subject_editor = self.create_editor(is_subject_enum, subject_enum_values, subject,
                                                 "请输入行为主体（如：司机）")
        self.object_editor = self.create_editor(is_object_enum, object_enum_values, obj, "请输入行为对象（如：行人）")

        # 添加到表单布局
        form_layout.addRow("行为主体:", self.subject_editor)
        form_layout.addRow("行为对象:", self.object_editor)
        layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: white; /* 设置背景颜色为白色 */
                color: black;           /* 设置文字颜色为黑色 */
            }
            QPushButton:pressed {
                background-color: lightgray; /* 按钮被按下时的背景色 */
            }
        """)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 连接信号与槽
        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

    def create_editor(self, is_enum, enum_values, initial_value, placeholder_text):
        """
        根据是否为枚举类型创建合适的编辑器。
        """
        if is_enum and enum_values:
            editor = create_centered_combobox(enum_values, initial_value)
        else:
            editor = QLineEdit()
            editor.setText(initial_value)
            editor.setPlaceholderText(placeholder_text)
            editor.setAlignment(Qt.AlignCenter)  # 居中对齐

        # 统一控件高度
        editor.setMinimumHeight(30)
        editor.setStyleSheet("""
            QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """)
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 使控件宽度填满布局
        return editor

    def validate_and_accept(self):
        """
        校验输入是否合法，如果合法则关闭对话框。
        """
        subject = self.subject_editor.currentText() if isinstance(self.subject_editor,
                                                                  QComboBox) else self.subject_editor.text().strip()
        obj = self.object_editor.currentText() if isinstance(self.object_editor,
                                                             QComboBox) else self.object_editor.text().strip()

        if not subject or subject == "<空>":
            CustomWarningDialog("输入错误", "行为主体不能为空！").exec_()
            return

        if not obj or obj == "<空>":
            CustomWarningDialog("输入错误", "行为对象不能为空！").exec_()
            return

        self.accept()

    def get_values(self):
        """
        获取输入值。
        """
        subject = self.subject_editor.currentText() if isinstance(self.subject_editor,
                                                                  QComboBox) else self.subject_editor.text().strip()
        obj = self.object_editor.currentText() if isinstance(self.object_editor,
                                                             QComboBox) else self.object_editor.text().strip()

        # 确保返回的值中没有 "<空>"，返回空字符串代替
        return subject if subject != "<空>" else "", obj if obj != "<空>" else ""

class ElementSettingTab(QWidget):
    save_requested = Signal()

    def __init__(self):
        super().__init__()
        self.current_selected_category = None  # 当前选中的类别
        self.init_ui()
        generate_requested = Signal()

    def init_ui(self):
        # 设置整体背景颜色和字体
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                font-weight: bold;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QCheckBox {
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;  /* 确保输入框背景为白色 */
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }


            /* 自定义滚动条样式 */
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            /* 设定占位符标签的样式 */
            QLabel#placeholder {
                background-color: white;
                color: #666666;
                /* font-style: italic; */  /* 移除斜体 */
                border: none;
            }

            /* 输入框选中时的蓝色边框 */
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 10)  # 左, 上, 右, 下 设置底部为10以对齐状态栏

        # 1. 情景要素类别选择区域
        self.categories = [
            "道路环境要素", "气象环境要素", "车辆致灾要素", "车辆承灾要素",
            "道路承灾要素", "人类承灾要素", "应急资源要素",
            "应急行为要素"
        ]
        element_group_box = QGroupBox("涉及的情景要素")
        element_layout = QGridLayout()

        self.checkboxes = {}
        for i, category in enumerate(self.categories):
            checkbox = CustomCheckBoxWithLabel(category)
            self.checkboxes[category] = checkbox
            row = i // 4  # 每行4个
            column = i % 4

            alignment = Qt.AlignCenter

            element_layout.addWidget(checkbox, row, column, 1, 1, alignment)

            # 连接标签点击信号，使用默认参数绑定当前的 category
            checkbox.label.clicked.connect(lambda checked_cat=category: self.handle_label_clicked(checked_cat))

        # 在布局顶部添加间距
        element_group_box_layout = QVBoxLayout()
        element_group_box_layout.addSpacing(5)  # 调整间距大小，适当增加标题和内容间的距离
        element_group_box_layout.addLayout(element_layout)
        element_group_box_layout.setContentsMargins(0, 12, 0, 12)  # 调整 GroupBox 内部边距
        element_group_box.setLayout(element_group_box_layout)
        main_layout.addWidget(element_group_box)

        # 2. 属性模型区域
        self.attribute_group_box = QGroupBox("属性模型")
        self.attribute_scroll = QScrollArea()
        self.attribute_scroll.setWidgetResizable(True)
        self.attribute_scroll.setFrameStyle(QFrame.NoFrame)

        # 使用 QGridLayout 实现两列布局
        self.attribute_content_widget = QWidget()
        self.attribute_content_layout = QGridLayout(self.attribute_content_widget)
        self.attribute_content_layout.setSpacing(20)
        self.attribute_content_layout.setContentsMargins(15, 15, 15, 15)
        self.attribute_content_layout.setAlignment(Qt.AlignTop)
        self.attribute_content_layout.setSizeConstraint(QGridLayout.SetMinimumSize)  # 设置大小约束

        self.attribute_content_widget.setLayout(self.attribute_content_layout)
        self.attribute_content_widget.setStyleSheet("background-color: white;")
        self.attribute_content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 占位符页面
        self.attribute_placeholder = QLabel("等待选择情景要素")
        self.attribute_placeholder.setAlignment(Qt.AlignCenter)
        self.attribute_placeholder.setObjectName("placeholder")

        # 创建一个布局来切换显示内容或占位符
        self.attribute_switch_layout = QVBoxLayout()
        self.attribute_switch_layout.setContentsMargins(0, 0, 0, 0)
        self.attribute_switch_layout.setSpacing(0)
        self.attribute_switch_layout.addWidget(self.attribute_content_widget)
        self.attribute_switch_layout.addWidget(self.attribute_placeholder)
        self.attribute_switch_layout.setStretch(0, 1)
        self.attribute_switch_layout.setStretch(1, 0)

        # 设置初始显示为占位符
        self.attribute_content_widget.hide()
        self.attribute_placeholder.show()

        # 设置容器
        attribute_container = QWidget()
        attribute_container.setLayout(self.attribute_switch_layout)
        self.attribute_scroll.setWidget(attribute_container)

        # 设置属性模型区域的边框样式，保持 GroupBox 的边框
        self.attribute_group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc; /* 保持边框 */
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                font-weight: bold;
                color: #333333;
            }
        """)

        # 设置属性模型区域的布局
        attribute_group_box_layout = QVBoxLayout()
        attribute_group_box_layout.addSpacing(5)  # 设置标题与内容的间距
        attribute_group_box_layout.setContentsMargins(20, 12, 32, 12)  # 调整 GroupBox 内部边距
        attribute_group_box_layout.addWidget(self.attribute_scroll)
        self.attribute_group_box.setLayout(attribute_group_box_layout)

        main_layout.addWidget(self.attribute_group_box)

        # 3. 行为模型区域
        behavior_group_box = QGroupBox("行为模型")

        # 创建行为模型的布局并设置为实例属性
        self.behavior_group_box_layout = QVBoxLayout()
        self.behavior_group_box_layout.setContentsMargins(30, 25, 32, 10)  # 设置左上右下的外边距
        self.behavior_group_box_layout.setSpacing(10)  # 设置内部控件之间的间距
        behavior_group_box.setLayout(self.behavior_group_box_layout)

        # 创建表格，使用标准 QTableWidget 并安装事件过滤器
        self.behavior_table = QTableWidget()
        self.behavior_table.setColumnCount(3)
        self.behavior_table.setHorizontalHeaderLabels(["行为名称", "行为主体", "行为对象"])
        self.behavior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # 应用三线表样式
        self.apply_three_line_table_style(self.behavior_table)

        self.behavior_table.horizontalHeader().setStretchLastSection(True)
        self.behavior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.behavior_table.verticalHeader().setVisible(False)
        self.behavior_table.setAlternatingRowColors(True)  # 使用交替行颜色区分

        self.behavior_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用默认编辑功能

        # 移除默认的网格线
        self.behavior_table.setShowGrid(False)

        # 设置行为表格的尺寸策略
        self.behavior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 安装事件过滤器以禁用滚轮事件
        no_wheel_filter_table = NoWheelEventFilter(self.behavior_table)
        self.behavior_table.installEventFilter(no_wheel_filter_table)

        # 创建占位符标签
        self.behavior_placeholder = QLabel("等待选择情景要素")
        self.behavior_placeholder.setAlignment(Qt.AlignCenter)
        self.behavior_placeholder.setObjectName("placeholder")
        self.behavior_placeholder.hide()  # 初始隐藏

        # 添加到布局
        self.behavior_group_box_layout.addWidget(self.behavior_table)
        self.behavior_group_box_layout.addWidget(self.behavior_placeholder)

        main_layout.addWidget(behavior_group_box)

        # 使用 QSizePolicy 和 stretch factors 来动态分配空间，并保持属性模型和行为模型高度一致
        main_layout.setStretchFactor(element_group_box, 0)
        main_layout.setStretchFactor(self.attribute_group_box, 2)
        main_layout.setStretchFactor(behavior_group_box, 2)

        # 4. 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("save_button")
        self.save_button.setToolTip("点击保存当前配置的要素数据")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: white; /* 设置背景颜色为白色 */
                color: black;           /* 设置文字颜色为黑色 */
            }
            QPushButton:hover {
                background-color: #f0f8ff; /* 浅蓝色背景 */
            }
            QPushButton:pressed {
                background-color: #cce5ff; /* 更深蓝色背景 */
            }
        """)
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.generate_button = QPushButton("生成情景级孪生模型")
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setToolTip("点击生成情景级孪生模型")

        self.generate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 将按钮添加到布局中，不使用 addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.generate_button)

        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)

        # 设置按钮区域的下边距为0
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 连接保存按钮信号
        self.save_button.clicked.connect(self.handle_save)

        # 连接行为表格的双击信号到编辑槽
        self.behavior_table.cellDoubleClicked.connect(self.open_behavior_editor)

        # 连接生成按钮信号
        self.generate_button.clicked.connect(self.handle_generate)

        # 初始化界面显示
        # 不自动选择任何类别，显示占位符
        self.populate_initial_display()

        # 初始化数据
        self.static_data = {
            "道路环境要素": {
                "attributes": {
                    "道路名称": "主干道",
                    "道路类型": "高速",
                    "行车道数": "4",
                    "起始桩号": "0km",
                    "终点桩号": "10km",
                    "封闭情况": "开放",
                    "受损情况": "轻微",
                    "污染情况": "无污染"
                },
                "behavior": [
                    {"name": "信号控制", "subject": "交通灯", "object": "车辆"},
                    {"name": "限速", "subject": "交通标志", "object": "司机"},
                    {"name": "测试", "subject": "交通标志", "object": "司机"},
                    {"name": "测试3", "subject": "交通标志", "object": "司机"},
                    {"name": "测试1", "subject": "交通标志", "object": "司机"},
                ]
            },
            "气象环境要素": {
                "attributes": {
                    "气温": "25°C",
                    "湿度": "60%",
                    "降雨量": "5mm",
                    "风速": "10km/h",
                    "天气状况": "晴",
                    "能见度": "良好",
                    "气压": "1013hPa",
                    "云量": "少量"
                },
                "behavior": [
                    {"name": "降雨影响", "subject": "雨水", "object": "车辆行驶"},
                    {"name": "风速限制", "subject": "气象监测", "object": "车辆"}
                ]
            },
            "车辆致灾要素": {
                "attributes": {
                    "车辆类型": "货车",
                    "碰撞情况": "是",
                    "燃爆情况": "是",
                    "车辆位置": "KW0058+500",
                    "抛锚情况": "是",
                    "侧翻情况": "是",
                    "行驶方向": "正向",
                    "车辆货物": "废纸"
                },
                "behavior": [
                    {"name": "车辆运载", "subject": "车辆致灾要素", "object": "车辆货物"},
                    {"name": "车辆撞击", "subject": "车辆致灾要素", "object": "车辆承灾要素"},
                    {"name": "车辆抛洒", "subject": "车辆致灾要素", "object": "车辆货物"},
                ]
            },
            "车辆承灾要素": {
                "attributes": {
                    "车辆类型": "货车",
                    "载重量": "10吨",
                    "车辆状态": "运行",
                    "燃料类型": "柴油",
                    "车辆编号": "ABC123",
                    "驾驶员": "张三",
                    "行驶速度": "80km/h",
                    "车况": "良好"
                },
                "behavior": [
                    {"name": "紧急制动", "subject": "驾驶员", "object": "车辆"},
                    {"name": "变道避让", "subject": "驾驶员", "object": "前方车辆"}
                ]
            },
            "道路承灾要素": {
                "attributes": {
                    "道路承载能力": "高",
                    "路面状况": "平整",
                    "交通流量": "高",
                    "交通设施": "完善",
                    "应急通道": "畅通",
                    "道路维护": "定期",
                    "照明情况": "良好",
                    "路标标识": "清晰"
                },
                "behavior": [
                    {"name": "快速疏导", "subject": "交警", "object": "车辆"},
                    {"name": "交通管制", "subject": "交警", "object": "司机"}
                ]
            },
            "人类承灾要素": {
                "attributes": {
                    "人口密度": "高",
                    "应急响应能力": "强",
                    "医疗设施": "充足",
                    "避难所数量": "5",
                    "救援队伍": "20人",
                    "公众培训": "定期",
                    "通讯设施": "良好",
                    "公共交通": "便利"
                },
                "behavior": [
                    {"name": "紧急疏散", "subject": "政府", "object": "居民"},
                    {"name": "医疗救助", "subject": "医疗人员", "object": "受灾人员"}
                ]
            },
            "应急资源要素": {
                "attributes": {
                    "应急物资": "充足",
                    "设备状态": "良好",
                    "储备位置": "多个",
                    "运输工具": "多样",
                    "人员配置": "足够",
                    "通讯设备": "完备",
                    "能源供应": "稳定",
                    "后勤支持": "有效"
                },
                "behavior": [
                    {"name": "物资分发", "subject": "后勤人员", "object": "受灾区域"},
                    {"name": "设备维护", "subject": "技术人员", "object": "应急设备"}
                ]
            },
            "应急行为要素": {
                "attributes": {
                    "应急预案": "完备",
                    "演练频率": "每月",
                    "协调机制": "高效",
                    "决策流程": "快速",
                    "信息发布": "及时",
                    "资源调配": "合理",
                    "人员培训": "系统",
                    "心理支持": "全面"
                },
                "behavior": [

                ]
            }
        }

        # Initialize category_data with deep copies to prevent shared references
        self.category_data = {category: json.loads(json.dumps(data)) for category, data in self.static_data.items()}

        # 定义每个类别中哪些属性是枚举类型及其选项
        self.category_attribute_enums = {
            "道路环境要素": {
                "道路类型": ["高速", "城市", "农村"],
                "封闭情况": ["开放", "封闭"],
                "受损情况": ["无", "轻微", "严重"],
                "污染情况": ["无污染", "轻度污染", "中度污染", "重度污染"]
            },
            "气象环境要素": {
                "天气状况": ["晴", "阴", "雨", "雪", "雾"],
                "能见度": ["良好", "中等", "差"]
            },
            "车辆致灾要素": {
                "车辆类型": ["货车", "轿车", "SUV", "摩托车"],
                "碰撞情况": ["是", "否"],
                "燃爆情况": ["是", "否"],
                "抛锚情况": ["是", "否"],
                "侧翻情况": ["是", "否"],
                "行驶方向": ["正向", "逆向"],
            },
            "车辆承灾要素": {
                "车辆类型": ["货车", "轿车", "SUV", "摩托车"],
                "车辆状态": ["运行", "维修", "故障"]
            },
            "道路承灾要素": {
                "道路承载能力": ["低", "中", "高"],
                "路面状况": ["平整", "坑洼", "破损"],
                "交通设施": ["完善", "一般", "缺乏"],
                "照明情况": ["良好", "中等", "差"]
            },
            "人类承灾要素": {
                "人口密度": ["低", "中", "高"],
                "应急响应能力": ["弱", "中", "强"],
                "医疗设施": ["充足", "一般", "不足"],
                "通讯设施": ["完备", "一般", "缺乏"],
                "公共交通": ["便利", "一般", "不便"]
            },
            "应急资源要素": {
                "设备状态": ["良好", "一般", "损坏"],
                "运输工具": ["多样", "有限"],
                "人员配置": ["足够", "不足"]
            },
            "应急行为要素": {
                "协调机制": ["高效", "中等", "低效"],
                "决策流程": ["快速", "中等", "缓慢"],
                "信息发布": ["及时", "一般", "延迟"],
                "资源调配": ["合理", "一般", "不合理"],
                "人员培训": ["系统", "一般", "缺乏"],
                "心理支持": ["全面", "一般", "不足"]
            },
        }

    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到指定的表格"""
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; /* 底部线 */
            }
            QHeaderView::section {
                border-top: 1px solid black;    /* 表头顶部线 */
                border-bottom: 1px solid black; /* 表头底部线 */
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center; /* 表头内容居中 */
            }
            QTableWidget::item {
                border: none; /* 中间行无边框 */
                padding: 5px;
                text-align: center; /* 单元格内容居中 */
            }
            /* 设置选中行的样式 */
            QTableWidget::item:selected {
                background-color: #cce5ff; /* 选中背景颜色 */
                color: black;             /* 选中文字颜色 */
                border: none;             /* 选中时无边框 */
            }
            QTableWidget:focus {
                outline: none; /* 禁用焦点边框 */
            }
        """)

        # 确保表头刷新样式
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        """确保表头样式刷新，防止表头下的线丢失"""
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;    /* 表头顶部线 */
                border-bottom: 1px solid black; /* 表头底部线 */
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center; /* 表头内容居中 */
            }
        """)
        table.horizontalHeader().repaint()  # 使用 repaint() 确保样式应用

    def clear_layout(self, layout):
        """辅助方法：清空布局中的所有控件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def reset_behavior_model(self, placeholder_text="等待上传情景要素模型"):
        """辅助方法：重置行为模型区域到占位符状态"""
        # 隐藏表格
        self.behavior_table.hide()
        # 显示占位符
        self.behavior_placeholder.setText(placeholder_text)
        self.behavior_placeholder.show()

    def populate_behavior_model(self, behaviors):
        """辅助方法：填充行为模型数据"""
        if behaviors:
            # 显示表格
            self.behavior_placeholder.hide()
            self.behavior_table.show()

            self.behavior_table.setRowCount(len(behaviors))
            for row_idx, behavior in enumerate(behaviors):
                # 行为名称保持只读
                name_item = QTableWidgetItem(behavior.get("name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 0, name_item)

                # 行为主体和行为对象可编辑
                subject_item = QTableWidgetItem(behavior.get("subject", ""))
                object_item = QTableWidgetItem(behavior.get("object", ""))
                subject_item.setTextAlignment(Qt.AlignCenter)
                object_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 1, subject_item)
                self.behavior_table.setItem(row_idx, 2, object_item)

            # 应用样式和调整布局
            self.apply_three_line_table_style(self.behavior_table)
            self.force_refresh_table_headers(self.behavior_table)
        else:
            # 如果没有行为模型，显示占位符
            self.reset_behavior_model("没有行为模型")

    def load_models_data(self, category):
        print(f"Loading data for category: {category}")  # 调试信息

        data = self.category_data.get(category, {})
        attributes = data.get("attributes", {})
        behaviors = data.get("behavior", [])

        # 根据类别选择相应的属性_labels
        category_to_attributes = {
            "道路环境要素": [
                "道路名称", "道路类型", "行车道数",
                "起始桩号", "终点桩号", "封闭情况",
                "受损情况", "污染情况"
            ],
            "气象环境要素": [
                "气温", "湿度", "降雨量",
                "风速", "天气状况", "能见度",
                "气压", "云量"
            ],
            "车辆致灾要素": [
                "车辆类型",
                "碰撞情况",
                "燃爆情况",
                "抛锚情况",
                "侧翻情况",
                "行驶方向"
            ],
            "车辆承灾要素": [
                "车辆类型", "载重量", "车辆状态",
                "燃料类型", "车辆编号", "驾驶员",
                "行驶速度", "车况"
            ],
            "道路承灾要素": [
                "道路承载能力", "路面状况", "交通流量",
                "交通设施", "应急通道", "道路维护",
                "照明情况", "路标标识"
            ],
            "人类承灾要素": [
                "人口密度", "应急响应能力", "医疗设施",
                "避难所数量", "救援队伍", "公众培训",
                "通讯设施", "公共交通"
            ],
            "应急资源要素": [
                "应急物资", "设备状态", "储备位置",
                "运输工具", "人员配置", "通讯设备",
                "能源供应", "后勤支持"
            ],
            "应急行为要素": [
            ],
        }

        current_attribute_labels = category_to_attributes.get(category, [])

        if current_attribute_labels:
            # 切换到内容页面
            self.attribute_content_widget.show()
            self.attribute_placeholder.hide()

            # 清空现有的属性内容布局
            self.clear_layout(self.attribute_content_layout)

            # Populate Attribute Model 使用 QGridLayout，每行两个属性
            columns = 2
            row = 0
            col = 0
            for label_text in current_attribute_labels:
                label = QLabel(label_text)

                # 检查该属性是否为枚举类型
                enums = self.category_attribute_enums.get(category, {}).get(label_text, None)
                if enums:
                    # 创建 CenteredComboBox
                    editor = create_centered_combobox(enums, attributes.get(label_text, "<空>"))
                else:
                    # 创建 QLineEdit
                    editor = QLineEdit()
                    editor.setText(attributes.get(label_text, ""))
                    editor.setPlaceholderText(f"请输入{label_text}")
                    editor.setAlignment(Qt.AlignCenter)  # 居中对齐

                # 根据字段类型设置验证器
                if label_text in ["行车道数", "载重量", "交通流量", "人口密度"]:
                    validator = QIntValidator(0, 1000, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif label_text in ["气温", "风速"]:
                    validator = QDoubleValidator(-50.0, 100.0, 2, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif isinstance(editor, QComboBox):
                    # 禁止用户输入新项，保持选择列表
                    # 取消此行以保持 QComboBox 可编辑，实现居中对齐
                    # editor.setEditable(False)
                    pass  # 保持编辑模式

                # 添加标签和编辑器到布局
                self.attribute_content_layout.addWidget(label, row, col * 2)
                self.attribute_content_layout.addWidget(editor, row, col * 2 + 1)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1
        else:
            # 如果没有属性模型，显示“没有属性模型”
            self.attribute_content_widget.hide()
            self.attribute_placeholder.setText("没有属性模型")
            self.attribute_placeholder.show()

        # 刷新布局
        self.attribute_content_widget.adjustSize()
        self.attribute_content_layout.update()

        # 重置滚动条的位置到顶部
        self.attribute_scroll.verticalScrollBar().setValue(0)

        # Populate Behavior Model
        self.populate_behavior_model(behaviors)

    def handle_label_clicked(self, category):
        print(f"handle_label_clicked called with category: {category}")  # 调试信息

        # 如果当前选中的类别被勾选且被修改，先保存当前的数据到 self.category_data
        if self.current_selected_category and self.checkboxes[self.current_selected_category].checkbox.isChecked():
            self.update_current_category_data()

        if self.current_selected_category:
            # 恢复之前选中的标签字体和颜色
            self.checkboxes[self.current_selected_category].set_selected(False)
        # 设置当前选中的标签字体加粗
        self.checkboxes[category].set_selected(True)
        self.current_selected_category = category
        # 弹出文件上传对话框
        upload_success = self.upload_model_file(category)
        if upload_success:
            # 加载对应的属性模型和行为模型数据
            self.load_models_data(category)
        else:
            # 如果未上传成功，加载默认数据
            self.load_models_data(category)

    def upload_model_file(self, category):
        # 弹出文件选择对话框
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择要素模型文件")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("JSON 文件 (*.json);;所有文件 (*)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print(f"Selected file for {category}: {file_path}")  # 调试信息
                # 文件类型验证和解析（暂时不做校验）
                # 请根据您的需求决定是否需要解析 JSON 文件
                # 目前只设置已上传状态并显示上传成功对话框
                self.checkboxes[category].label.set_uploaded(True)
                CustomInformationDialog("上传成功", f"已成功上传并加载要素模型文件:\n{file_path}", parent=self).exec()
                return True
        else:
            # 用户取消上传，不改变上传状态
            return False

    def open_behavior_editor(self, row, column):
        sender = self.sender()
        if sender != self.behavior_table:
            print("open_behavior_editor called by unknown sender")  # 调试信息
            return

        print(f"open_behavior_editor called on row: {row}, column: {column}")  # 调试信息
        selected_row = row
        if selected_row < 0:
            CustomWarningDialog("警告", "请选择一个行为进行编辑！", parent=self).exec()
            return

        # 获取当前行的数据
        behavior_name_item = self.behavior_table.item(selected_row, 0)
        subject_item = self.behavior_table.item(selected_row, 1)
        object_item = self.behavior_table.item(selected_row, 2)

        if not behavior_name_item:
            CustomWarningDialog("警告", "行为名称为空，无法编辑。", parent=self).exec()
            return

        behavior_name = behavior_name_item.text()
        subject = subject_item.text() if subject_item else ""
        obj = object_item.text() if object_item else ""

        # 判断当前行为是否需要枚举
        enum_data = {
            "信号控制": {"is_subject_enum": True, "subject_enum_values": ["交通灯", "交警"],
                         "is_object_enum": True, "object_enum_values": ["车辆", "行人"]},
            "限速": {"is_subject_enum": False, "subject_enum_values": None,
                     "is_object_enum": True, "object_enum_values": ["司机", "车辆"]},
            "车辆运载": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆货物"]},
            "车辆撞击": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆承灾要素"]},
            "车辆抛洒": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆货物"]},
        }
        enum_config = enum_data.get(behavior_name, {"is_subject_enum": False, "subject_enum_values": None,
                                                    "is_object_enum": False, "object_enum_values": None})

        # 弹出编辑窗口
        dialog = EditBehaviorDialog(
            behavior_name,
            subject,
            obj,
            is_subject_enum=enum_config["is_subject_enum"],
            is_object_enum=enum_config["is_object_enum"],
            subject_enum_values=enum_config["subject_enum_values"],
            object_enum_values=enum_config["object_enum_values"],
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            # 获取修改后的值
            new_subject, new_object = dialog.get_values()

            # 更新表格中的值
            if isinstance(self.behavior_table.item(selected_row, 1), QTableWidgetItem):
                self.behavior_table.item(selected_row, 1).setText(new_subject)
            else:
                self.behavior_table.setItem(selected_row, 1, QTableWidgetItem(new_subject))

            if isinstance(self.behavior_table.item(selected_row, 2), QTableWidgetItem):
                self.behavior_table.item(selected_row, 2).setText(new_object)
            else:
                self.behavior_table.setItem(selected_row, 2, QTableWidgetItem(new_object))

            # 更新 self.category_data
            if self.current_selected_category:
                if selected_row < len(self.category_data[self.current_selected_category]["behavior"]):
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["subject"] = new_subject
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["object"] = new_object
                else:
                    # 如果行为列表较短，添加新的行为
                    self.category_data[self.current_selected_category]["behavior"].append({
                        "name": behavior_name,
                        "subject": new_subject,
                        "object": new_object
                    })

    def update_current_category_data(self):
        """辅助方法：从GUI收集当前类别的属性和行为，并更新self.category_data"""
        if not self.current_selected_category:
            return

        category = self.current_selected_category
        attributes = {}
        behaviors = []

        # 收集属性数据
        category_to_attributes = {
            "道路环境要素": [
                "道路名称", "道路类型", "行车道数",
                "起始桩号", "终点桩号", "封闭情况",
                "受损情况", "污染情况"
            ],
            "气象环境要素": [
                "气温", "湿度", "降雨量",
                "风速", "天气状况", "能见度",
                "气压", "云量"
            ],
            "车辆致灾要素": [
                "车辆类型",
                "碰撞情况",
                "燃爆情况",
                "抛锚情况",
                "侧翻情况",
                "行驶方向"
            ],
            "车辆承灾要素": [
                "车辆类型", "载重量", "车辆状态",
                "燃料类型", "车辆编号", "驾驶员",
                "行驶速度", "车况"
            ],
            "道路承灾要素": [
                "道路承载能力", "路面状况", "交通流量",
                "交通设施", "应急通道", "道路维护",
                "照明情况", "路标标识"
            ],
            "人类承灾要素": [
                "人口密度", "应急响应能力", "医疗设施",
                "避难所数量", "救援队伍", "公众培训",
                "通讯设施", "公共交通"
            ],
            "应急资源要素": [
                "应急物资", "设备状态", "储备位置",
                "运输工具", "人员配置", "通讯设备",
                "能源供应", "后勤支持"
            ],
            "应急行为要素": [
            ],
        }

        current_attribute_labels = category_to_attributes.get(category, [])

        if current_attribute_labels:
            # 遍历属性布局，收集数据
            for row in range(self.attribute_content_layout.rowCount()):
                label_widget = self.attribute_content_layout.itemAtPosition(row, 0).widget()
                editor_widget = self.attribute_content_layout.itemAtPosition(row, 1).widget()
                if isinstance(label_widget, QLabel) and isinstance(editor_widget, (QLineEdit, QComboBox)):
                    key = label_widget.text()
                    if key in current_attribute_labels:
                        if isinstance(editor_widget, QLineEdit):
                            value = editor_widget.text()
                        elif isinstance(editor_widget, QComboBox):
                            value = editor_widget.currentText()
                            if value == "<空>":
                                value = ""
                        attributes[key] = value
        else:
            # 没有属性模型
            pass

        # 收集行为模型数据
        if self.behavior_table.isVisible():
            for row in range(self.behavior_table.rowCount()):
                behavior_name = self.behavior_table.item(row, 0).text() if self.behavior_table.item(row, 0) else ""
                behavior_subject = self.behavior_table.item(row, 1).text() if self.behavior_table.item(row, 1) else ""
                behavior_object = self.behavior_table.item(row, 2).text() if self.behavior_table.item(row, 2) else ""
                if behavior_name.strip():  # 仅保存有行为名称的行
                    behaviors.append({
                        "name": behavior_name,
                        "subject": behavior_subject,
                        "object": behavior_object
                    })

        # 更新 self.category_data
        self.category_data[category]["attributes"] = attributes
        self.category_data[category]["behavior"] = behaviors

    def handle_save(self):
        """收集所有被勾选的要素数据并模拟保存操作"""
        # 如果当前选中的类别被勾选，则先保存当前界面的数据到 self.category_data
        if self.current_selected_category and self.checkboxes[self.current_selected_category].checkbox.isChecked():
            self.update_current_category_data()

        # 收集所有被勾选的要素数据
        saved_categories = []
        for category, checkbox in self.checkboxes.items():
            if checkbox.checkbox.isChecked():
                data = self.category_data.get(category, {})
                attributes = data.get("attributes", {})
                behaviors = data.get("behavior", [])

                saved_categories.append({
                    "category": category,
                    "attributes": attributes,
                    "behaviors": behaviors
                })

        if not saved_categories:
            CustomInformationDialog("保存结果", "没有要保存的要素。", parent=self).exec()
            return

        # 显示保存的数据（使用自定义对话框）
        save_message = ""
        for item in saved_categories:
            save_message += f"类别: {item['category']}\n"
            save_message += "属性:\n"
            for key, value in item['attributes'].items():
                save_message += f"  {key}: {value}\n"
            save_message += "行为模型:\n"
            if item['behaviors']:
                for behavior in item['behaviors']:
                    save_message += f"  行为名称: {behavior['name']}\n"
                    save_message += f"  行为主体: {behavior['subject']}\n"
                    save_message += f"  行为对象: {behavior['object']}\n"
            else:
                save_message += "  无行为模型\n"
            save_message += "\n"

        save_dialog = SaveResultDialog(save_message, self)
        save_dialog.exec()

        # 发射保存完成的信号
        self.save_requested.emit()

    def populate_initial_display(self):
        """在属性模型和行为模型区域显示“等待选择情景要素”"""
        # 1. 属性模型区域
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText("等待上传情景要素模型")
        self.attribute_placeholder.show()

        # 2. 行为模型区域
        self.reset_behavior_model()

    def handle_generate(self):
        # 模拟生成情景级孪生模型
        CustomInformationDialog(" ", "已成功生成情景级孪生模型。", parent=self).exec()
        # 发射生成完成的信号
        self.generate_requested.emit()


    def load_models_data(self, category):
        print(f"Loading data for category: {category}")  # 调试信息

        data = self.category_data.get(category, {})
        attributes = data.get("attributes", {})
        behaviors = data.get("behavior", [])

        # 根据类别选择相应的属性_labels
        category_to_attributes = {
            "道路环境要素": [
                "道路名称", "道路类型", "行车道数",
                "起始桩号", "终点桩号", "封闭情况",
                "受损情况", "污染情况"
            ],
            "气象环境要素": [
                "气温", "湿度", "降雨量",
                "风速", "天气状况", "能见度",
                "气压", "云量"
            ],
            "车辆致灾要素": [
                "车辆类型",
                "碰撞情况",
                "燃爆情况",
                "抛锚情况",
                "侧翻情况",
                "行驶方向"
            ],
            "车辆承灾要素": [
                "车辆类型", "载重量", "车辆状态",
                "燃料类型", "车辆编号", "驾驶员",
                "行驶速度", "车况"
            ],
            "道路承灾要素": [
                "道路承载能力", "路面状况", "交通流量",
                "交通设施", "应急通道", "道路维护",
                "照明情况", "路标标识"
            ],
            "人类承灾要素": [
                "人口密度", "应急响应能力", "医疗设施",
                "避难所数量", "救援队伍", "公众培训",
                "通讯设施", "公共交通"
            ],
            "应急资源要素": [
                "应急物资", "设备状态", "储备位置",
                "运输工具", "人员配置", "通讯设备",
                "能源供应", "后勤支持"
            ],
            "应急行为要素": [
            ],
        }

        current_attribute_labels = category_to_attributes.get(category, [])

        if current_attribute_labels:
            # 切换到内容页面
            self.attribute_content_widget.show()
            self.attribute_placeholder.hide()

            # 清空现有的属性内容布局
            self.clear_layout(self.attribute_content_layout)

            # Populate Attribute Model 使用 QGridLayout，每行两个属性
            columns = 2
            row = 0
            col = 0
            for label_text in current_attribute_labels:
                label = QLabel(label_text)

                # 检查该属性是否为枚举类型
                enums = self.category_attribute_enums.get(category, {}).get(label_text, None)
                if enums:
                    # 创建 CenteredComboBox
                    editor = create_centered_combobox(enums, attributes.get(label_text, "<空>"))
                else:
                    # 创建 QLineEdit
                    editor = QLineEdit()
                    editor.setText(attributes.get(label_text, ""))
                    editor.setPlaceholderText(f"请输入{label_text}")
                    editor.setAlignment(Qt.AlignCenter)  # 居中对齐

                # 根据字段类型设置验证器
                if label_text in ["行车道数", "载重量", "交通流量", "人口密度"]:
                    validator = QIntValidator(0, 1000, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif label_text in ["气温", "风速"]:
                    validator = QDoubleValidator(-50.0, 100.0, 2, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif isinstance(editor, QComboBox):
                    # 禁止用户输入新项，保持选择列表
                    # 取消此行以保持 QComboBox 可编辑，实现居中对齐
                    # editor.setEditable(False)
                    pass  # 保持编辑模式

                # 添加标签和编辑器到布局
                self.attribute_content_layout.addWidget(label, row, col * 2)
                self.attribute_content_layout.addWidget(editor, row, col * 2 + 1)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1
        else:
            # 如果没有属性模型，显示“没有属性模型”
            self.attribute_content_widget.hide()
            self.attribute_placeholder.setText("没有属性模型")
            self.attribute_placeholder.show()

        # 刷新布局
        self.attribute_content_widget.adjustSize()
        self.attribute_content_layout.update()

        # 重置滚动条的位置到顶部
        self.attribute_scroll.verticalScrollBar().setValue(0)

        # Populate Behavior Model
        self.populate_behavior_model(behaviors)

    def handle_label_clicked(self, category):
        print(f"handle_label_clicked called with category: {category}")  # 调试信息

        # 如果当前选中的类别被勾选且被修改，先保存当前的数据到 self.category_data
        if self.current_selected_category and self.checkboxes[self.current_selected_category].checkbox.isChecked():
            self.update_current_category_data()

        if self.current_selected_category:
            # 恢复之前选中的标签字体和颜色
            self.checkboxes[self.current_selected_category].set_selected(False)
        # 设置当前选中的标签字体加粗
        self.checkboxes[category].set_selected(True)
        self.current_selected_category = category
        # 弹出文件上传对话框
        upload_success = self.upload_model_file(category)
        if upload_success:
            # 加载对应的属性模型和行为模型数据
            self.load_models_data(category)
        else:
            # 如果未上传成功，加载默认数据
            self.load_models_data(category)

    def upload_model_file(self, category):
        # 弹出文件选择对话框
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择要素模型文件")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("JSON 文件 (*.json);;所有文件 (*)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print(f"Selected file for {category}: {file_path}")  # 调试信息
                # 文件类型验证和解析（暂时不做校验）
                # 请根据您的需求决定是否需要解析 JSON 文件
                # 目前只设置已上传状态并显示上传成功对话框
                self.checkboxes[category].label.set_uploaded(True)
                CustomInformationDialog("上传成功", f"已成功上传并加载要素模型文件:\n{file_path}", parent=self).exec()
                return True
        else:
            # 用户取消上传，不改变上传状态
            return False

    def open_behavior_editor(self, row, column):
        sender = self.sender()
        if sender != self.behavior_table:
            print("open_behavior_editor called by unknown sender")  # 调试信息
            return

        print(f"open_behavior_editor called on row: {row}, column: {column}")  # 调试信息
        selected_row = row
        if selected_row < 0:
            CustomWarningDialog("警告", "请选择一个行为进行编辑！", parent=self).exec()
            return

        # 获取当前行的数据
        behavior_name_item = self.behavior_table.item(selected_row, 0)
        subject_item = self.behavior_table.item(selected_row, 1)
        object_item = self.behavior_table.item(selected_row, 2)

        if not behavior_name_item:
            CustomWarningDialog("警告", "行为名称为空，无法编辑。", parent=self).exec()
            return

        behavior_name = behavior_name_item.text()
        subject = subject_item.text() if subject_item else ""
        obj = object_item.text() if object_item else ""

        # 判断当前行为是否需要枚举
        enum_data = {
            "信号控制": {"is_subject_enum": True, "subject_enum_values": ["交通灯", "交警"],
                         "is_object_enum": True, "object_enum_values": ["车辆", "行人"]},
            "限速": {"is_subject_enum": False, "subject_enum_values": None,
                     "is_object_enum": True, "object_enum_values": ["司机", "车辆"]},
            "车辆运载": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆货物"]},
            "车辆撞击": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆承灾要素"]},
            "车辆抛洒": {"is_subject_enum": True, "subject_enum_values": ["车辆致灾要素"],
                     "is_object_enum": True, "object_enum_values": ["车辆货物"]},
        }
        enum_config = enum_data.get(behavior_name, {"is_subject_enum": False, "subject_enum_values": None,
                                                    "is_object_enum": False, "object_enum_values": None})

        # 弹出编辑窗口
        dialog = EditBehaviorDialog(
            behavior_name,
            subject,
            obj,
            is_subject_enum=enum_config["is_subject_enum"],
            is_object_enum=enum_config["is_object_enum"],
            subject_enum_values=enum_config["subject_enum_values"],
            object_enum_values=enum_config["object_enum_values"],
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            # 获取修改后的值
            new_subject, new_object = dialog.get_values()

            # 更新表格中的值
            if isinstance(self.behavior_table.item(selected_row, 1), QTableWidgetItem):
                self.behavior_table.item(selected_row, 1).setText(new_subject)
            else:
                self.behavior_table.setItem(selected_row, 1, QTableWidgetItem(new_subject))

            if isinstance(self.behavior_table.item(selected_row, 2), QTableWidgetItem):
                self.behavior_table.item(selected_row, 2).setText(new_object)
            else:
                self.behavior_table.setItem(selected_row, 2, QTableWidgetItem(new_object))

            # 更新 self.category_data
            if self.current_selected_category:
                if selected_row < len(self.category_data[self.current_selected_category]["behavior"]):
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["subject"] = new_subject
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["object"] = new_object
                else:
                    # 如果行为列表较短，添加新的行为
                    self.category_data[self.current_selected_category]["behavior"].append({
                        "name": behavior_name,
                        "subject": new_subject,
                        "object": new_object
                    })

    def update_current_category_data(self):
        """辅助方法：从GUI收集当前类别的属性和行为，并更新self.category_data"""
        if not self.current_selected_category:
            return

        category = self.current_selected_category
        attributes = {}
        behaviors = []

        # 收集属性数据
        category_to_attributes = {
            "道路环境要素": [
                "道路名称", "道路类型", "行车道数",
                "起始桩号", "终点桩号", "封闭情况",
                "受损情况", "污染情况"
            ],
            "气象环境要素": [
                "气温", "湿度", "降雨量",
                "风速", "天气状况", "能见度",
                "气压", "云量"
            ],
            "车辆致灾要素": [
                "车辆类型",
                "碰撞情况",
                "燃爆情况",
                "抛锚情况",
                "侧翻情况",
                "行驶方向"
            ],
            "车辆承灾要素": [
                "车辆类型", "载重量", "车辆状态",
                "燃料类型", "车辆编号", "驾驶员",
                "行驶速度", "车况"
            ],
            "道路承灾要素": [
                "道路承载能力", "路面状况", "交通流量",
                "交通设施", "应急通道", "道路维护",
                "照明情况", "路标标识"
            ],
            "人类承灾要素": [
                "人口密度", "应急响应能力", "医疗设施",
                "避难所数量", "救援队伍", "公众培训",
                "通讯设施", "公共交通"
            ],
            "应急资源要素": [
                "应急物资", "设备状态", "储备位置",
                "运输工具", "人员配置", "通讯设备",
                "能源供应", "后勤支持"
            ],
            "应急行为要素": [
            ],
        }

        current_attribute_labels = category_to_attributes.get(category, [])

        if current_attribute_labels:
            # 遍历属性布局，收集数据
            for row in range(self.attribute_content_layout.rowCount()):
                label_widget = self.attribute_content_layout.itemAtPosition(row, 0).widget()
                editor_widget = self.attribute_content_layout.itemAtPosition(row, 1).widget()
                if isinstance(label_widget, QLabel) and isinstance(editor_widget, (QLineEdit, QComboBox)):
                    key = label_widget.text()
                    if key in current_attribute_labels:
                        if isinstance(editor_widget, QLineEdit):
                            value = editor_widget.text()
                        elif isinstance(editor_widget, QComboBox):
                            value = editor_widget.currentText()
                            if value == "<空>":
                                value = ""
                        attributes[key] = value
        else:
            # 没有属性模型
            pass

        # 收集行为模型数据
        if self.behavior_table.isVisible():
            for row in range(self.behavior_table.rowCount()):
                behavior_name = self.behavior_table.item(row, 0).text() if self.behavior_table.item(row, 0) else ""
                behavior_subject = self.behavior_table.item(row, 1).text() if self.behavior_table.item(row, 1) else ""
                behavior_object = self.behavior_table.item(row, 2).text() if self.behavior_table.item(row, 2) else ""
                if behavior_name.strip():  # 仅保存有行为名称的行
                    behaviors.append({
                        "name": behavior_name,
                        "subject": behavior_subject,
                        "object": behavior_object
                    })

        # 更新 self.category_data
        self.category_data[category]["attributes"] = attributes
        self.category_data[category]["behavior"] = behaviors

    def handle_save(self):
        """收集所有被勾选的要素数据并模拟保存操作"""
        # 如果当前选中的类别被勾选，则先保存当前界面的数据到 self.category_data
        if self.current_selected_category and self.checkboxes[self.current_selected_category].checkbox.isChecked():
            self.update_current_category_data()

        # 收集所有被勾选的要素数据
        saved_categories = []
        for category, checkbox in self.checkboxes.items():
            if checkbox.checkbox.isChecked():
                data = self.category_data.get(category, {})
                attributes = data.get("attributes", {})
                behaviors = data.get("behavior", [])

                saved_categories.append({
                    "category": category,
                    "attributes": attributes,
                    "behaviors": behaviors
                })

        if not saved_categories:
            CustomInformationDialog("保存结果", "没有要保存的要素。", parent=self).exec()
            return

        # 构建更美观的HTML格式的保存信息
        save_message = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    font-size: 14px;
                    color: #333333;
                }
                h2 {
                    text-align: center;
                    color: #0078d7;
                }
                h3 {
                    color: #005a9e;
                    margin-top: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th, td {
                    border: 1px solid #cccccc;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f0f0f0;
                }
                ul {
                    list-style-type: none;
                    padding-left: 0;
                }
                li {
                    margin-bottom: 5px;
                }
                .no-behavior {
                    color: #ff0000;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
        <h2>保存结果</h2>
        """

        for item in saved_categories:
            save_message += f"<h3>类别: {item['category']}</h3>"

            # 属性表格
            save_message += """
            <b>属性:</b>
            <table>
                <tr>
                    <th>属性名称</th>
                    <th>属性值</th>
                </tr>
            """
            for key, value in item['attributes'].items():
                save_message += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
                """
            save_message += "</table>"

            # 行为模型表格
            save_message += "<b>行为模型:</b>"
            if item['behaviors']:
                save_message += """
                <table>
                    <tr>
                        <th>行为名称</th>
                        <th>行为主体</th>
                        <th>行为对象</th>
                    </tr>
                """
                for behavior in item['behaviors']:
                    save_message += f"""
                    <tr>
                        <td>{behavior['name']}</td>
                        <td>{behavior['subject']}</td>
                        <td>{behavior['object']}</td>
                    </tr>
                    """
                save_message += "</table>"
            else:
                save_message += "<p class='no-behavior'>无行为模型</p>"

        save_message += "</body></html>"

        # 创建并显示保存结果对话框
        save_dialog = SaveResultDialog(save_message, self)
        save_dialog.exec()

        # 发射保存完成的信号
        self.save_requested.emit()

    def populate_initial_display(self):
        """在属性模型和行为模型区域显示“等待选择情景要素”"""
        # 1. 属性模型区域
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText("等待上传情景要素模型")
        self.attribute_placeholder.show()

        # 2. 行为模型区域
        self.reset_behavior_model()

    def handle_generate(self):
        # 模拟生成情景级孪生模型
        CustomInformationDialog(" ", "已成功生成情景级孪生模型。", parent=self).exec()


    def load_models_data(self, category):
        print(f"Loading data for category: {category}")  # 调试信息

        data = self.category_data.get(category, {})
        attributes = data.get("attributes", {})
        behaviors = data.get("behavior", [])

        # 根据类别选择相应的属性_labels
        category_to_attributes = {
            "道路环境要素": [
                "道路名称", "道路类型", "行车道数",
                "起始桩号", "终点桩号", "封闭情况",
                "受损情况", "污染情况"
            ],
            "气象环境要素": [
                "气温", "湿度", "降雨量",
                "风速", "天气状况", "能见度",
                "气压", "云量"
            ],
            "车辆致灾要素": [
                "车辆类型",
                "碰撞情况",
                "燃爆情况",
                "抛锚情况",
                "侧翻情况",
                "行驶方向"
            ],
            "车辆承灾要素": [
                "车辆类型", "载重量", "车辆状态",
                "燃料类型", "车辆编号", "驾驶员",
                "行驶速度", "车况"
            ],
            "道路承灾要素": [
                "道路承载能力", "路面状况", "交通流量",
                "交通设施", "应急通道", "道路维护",
                "照明情况", "路标标识"
            ],
            "人类承灾要素": [
                "人口密度", "应急响应能力", "医疗设施",
                "避难所数量", "救援队伍", "公众培训",
                "通讯设施", "公共交通"
            ],
            "应急资源要素": [
                "应急物资", "设备状态", "储备位置",
                "运输工具", "人员配置", "通讯设备",
                "能源供应", "后勤支持"
            ],
            "应急行为要素": [
            ],
        }

        current_attribute_labels = category_to_attributes.get(category, [])

        if current_attribute_labels:
            # 切换到内容页面
            self.attribute_content_widget.show()
            self.attribute_placeholder.hide()

            # 清空现有的属性内容布局
            self.clear_layout(self.attribute_content_layout)

            # Populate Attribute Model 使用 QGridLayout，每行两个属性
            columns = 2
            row = 0
            col = 0
            for label_text in current_attribute_labels:
                label = QLabel(label_text)

                # 检查该属性是否为枚举类型
                enums = self.category_attribute_enums.get(category, {}).get(label_text, None)
                if enums:
                    # 创建 CenteredComboBox
                    editor = create_centered_combobox(enums, attributes.get(label_text, "<空>"))
                else:
                    # 创建 QLineEdit
                    editor = QLineEdit()
                    editor.setText(attributes.get(label_text, ""))
                    editor.setPlaceholderText(f"请输入{label_text}")
                    editor.setAlignment(Qt.AlignCenter)  # 居中对齐

                # 根据字段类型设置验证器
                if label_text in ["行车道数", "载重量", "交通流量", "人口密度"]:
                    validator = QIntValidator(0, 1000, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif label_text in ["气温", "风速"]:
                    validator = QDoubleValidator(-50.0, 100.0, 2, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif isinstance(editor, QComboBox):
                    # 禁止用户输入新项，保持选择列表
                    # 取消此行以保持 QComboBox 可编辑，实现居中对齐
                    # editor.setEditable(False)
                    pass  # 保持编辑模式

                # 添加标签和编辑器到布局
                self.attribute_content_layout.addWidget(label, row, col * 2)
                self.attribute_content_layout.addWidget(editor, row, col * 2 + 1)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1
        else:
            # 如果没有属性模型，显示“没有属性模型”
            self.attribute_content_widget.hide()
            self.attribute_placeholder.setText("没有属性模型")
            self.attribute_placeholder.show()

        # 刷新布局
        self.attribute_content_widget.adjustSize()
        self.attribute_content_layout.update()

        # 重置滚动条的位置到顶部
        self.attribute_scroll.verticalScrollBar().setValue(0)

        # Populate Behavior Model
        self.populate_behavior_model(behaviors)

class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("情景要素设置")
        self.resize(1000, 700)
        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 添加 ElementSettingTab
        self.element_setting_tab = ElementSettingTab()
        self.tab_widget.addTab(self.element_setting_tab, "要素设置")

        # 可以在这里添加更多的 Tab
        # self.another_tab = AnotherTab()
        # self.tab_widget.addTab(self.another_tab, "另一个标签")

        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
