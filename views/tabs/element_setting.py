# -*- coding: utf-8 -*-
# @Time    : 12/7/2024 10:00 AM
# @FileName: element_setting.py
# @Software: PyCharm

from PySide6.QtCore import Signal, Qt, QObject, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QGroupBox, QGridLayout,
    QSizePolicy, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFileDialog, QFrame, QApplication, QTabWidget, QFormLayout, QTextEdit, QStackedLayout, QButtonGroup, QTextBrowser,
    QListWidget
)
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator
from PySide6.QtWidgets import QStyledItemDelegate
import sys
import json

from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog


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
    combobox = QComboBox()
    combobox.addItem("<空>")
    for item in enum_values:
        combobox.addItem(item)

    if initial_value in enum_values:
        combobox.setCurrentText(initial_value)
    else:
        combobox.setCurrentText("<空>")

    combobox.setEditable(True)
    combobox.lineEdit().setReadOnly(True)
    combobox.lineEdit().setAlignment(Qt.AlignCenter)

    view = combobox.view()
    delegate = CenteredItemDelegate(view)
    view.setItemDelegate(delegate)

    no_wheel_filter = NoWheelEventFilter(combobox)
    combobox.installEventFilter(no_wheel_filter)

    return combobox


class SaveResultDialog(QDialog):
    def __init__(self, saved_categories, detailed_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("保存结果"))
        self.setModal(True)
        self.resize(300, 250)

        main_layout = QVBoxLayout(self)

        summary_label = QLabel(self.tr("已保存的情景要素类别:"))
        summary_label.setFont(QFont("SimSun", 14, QFont.Bold))
        main_layout.addWidget(summary_label)

        self.summary_list = QListWidget()
        for item in saved_categories:
            self.summary_list.addItem(item['category'])
        self.summary_list.setSelectionMode(QListWidget.NoSelection)
        self.summary_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #f9f9f9;
                alternate-background-color: #e9e7e3
            }
        """)
        main_layout.addWidget(self.summary_list)

        button_layout = QHBoxLayout()

        self.view_details_button = QPushButton(self.tr("查看详情"))
        self.view_details_button.clicked.connect(lambda: self.open_details_dialog(detailed_info))
        self.view_details_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.view_details_button.setFixedWidth(85)

        self.ok_button = QPushButton(self.tr("确定"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ok_button.setFixedWidth(50)

        button_layout.addWidget(self.view_details_button)
        button_layout.addWidget(self.ok_button)

        main_layout.addLayout(button_layout)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)

    def open_details_dialog(self, detailed_info):
        details_dialog = DetailsDialog(detailed_info, parent=self)
        details_dialog.exec()


class DetailsDialog(QDialog):
    def __init__(self, detailed_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("详细信息"))
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.details_browser = QTextBrowser()
        self.details_browser.setHtml(detailed_info)
        layout.addWidget(self.details_browser)

        close_button = QPushButton(self.tr("确定"))
        close_button.clicked.connect(self.accept)
        close_button.setFixedWidth(50)
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()
        close_button_layout.addWidget(close_button)
        close_button_layout.addStretch()
        layout.addLayout(close_button_layout)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.default_font = self.font()
        self.selected_font = QFont(self.font())
        self.selected_font.setBold(True)
        self.uploaded = False
        self.selected = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()

    def set_uploaded(self, uploaded: bool):
        self.uploaded = uploaded
        self.update_style()

    def update_style(self):
        if self.uploaded:
            color = "#0078d7"
        else:
            color = "black"

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
        self.checkbox.setMinimumSize(20, 20)

        self.label = ClickableLabel(self.tr(label_text))
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label.setMinimumHeight(20)
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
        self.setWindowTitle(self.tr("编辑行为: ") + behavior_name)
        self.setFixedSize(400, 200)
        self.setStyleSheet("""

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

            /* 输入框选中时的蓝色边框 */
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        behavior_label = QLabel(self.tr("正在编辑行为: ") + behavior_name)
        behavior_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        behavior_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(behavior_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.subject_editor = self.create_editor(is_subject_enum, subject_enum_values, subject,
                                                 self.tr("请输入行为主体（如：司机）"))
        self.object_editor = self.create_editor(is_object_enum, object_enum_values, obj, self.tr("请输入行为对象（如：行人）"))

        form_layout.addRow(self.tr("行为主体:"), self.subject_editor)
        form_layout.addRow(self.tr("行为对象:"), self.object_editor)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.tr("保存"))
        self.save_button.setFixedWidth(50)
        self.cancel_button = QPushButton(self.tr("取消"))
        self.cancel_button.setFixedWidth(50)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

    def create_editor(self, is_enum, enum_values, initial_value, placeholder_text):
        if is_enum and enum_values:
            editor = create_centered_combobox(enum_values, initial_value)
        else:
            editor = QLineEdit()
            editor.setText(initial_value)
            editor.setPlaceholderText(placeholder_text)
            editor.setAlignment(Qt.AlignCenter)

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
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return editor

    def validate_and_accept(self):
        subject = self.subject_editor.currentText() if isinstance(self.subject_editor,
                                                                  QComboBox) else self.subject_editor.text().strip()
        obj = self.object_editor.currentText() if isinstance(self.object_editor,
                                                             QComboBox) else self.object_editor.text().strip()

        if not subject or subject == "<空>":
            CustomWarningDialog(self.tr("输入错误"), self.tr("行为主体不能为空！")).exec_()
            return

        if not obj or obj == "<空>":
            CustomWarningDialog(self.tr("输入错误"), self.tr("行为对象不能为空！")).exec_()
            return

        self.accept()

    def get_values(self):
        subject = self.subject_editor.currentText() if isinstance(self.subject_editor,
                                                                  QComboBox) else self.subject_editor.text().strip()
        obj = self.object_editor.currentText() if isinstance(self.object_editor,
                                                             QComboBox) else self.object_editor.text().strip()

        return subject if subject != "<空>" else "", obj if obj != "<空>" else ""


class ElementSettingTab(QWidget):
    """情景要素设置标签页"""

    save_requested = Signal()

    def __init__(self):
        super().__init__()
        self.current_selected_category = None
        self.attribute_editors = {}
        self.init_ui()
        self.attribute_button.setChecked(True)
        self.switch_model_display("Attribute")

    def init_ui(self):
        self.setStyleSheet("""
QGroupBox {
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    font-weight: bold;
    color: #333333;
    background-color: #E8E8E8;
    border-radius: 10px;
    border-bottom-left-radius: 0px;
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
                background-color: white;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }

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

            QLabel#placeholder{
                color: gray;
                font-size: 20pt;
                border-radius: 10px;
                border: 0px solid #c0c0c0;
                background-color: #ffffff;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7;
            }

            /* 属性模型和行为模型按钮样式 */
            QPushButton#AttributeButton{
                border: #f0f0f0; /* 边框颜色 */
                border-right: 1px solid #f0f0f0; /* 右侧边框 */
                border-left-radius:10 px;
                background-color: transparent; /* 背景透明 */
                padding:10px 0;
                font-size: 16px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
            }
            QPushButton#BehaviorButton{
                border: #f0f0f0; /* 边框颜色 */
                border-left:1px solid #f0f0f0; /* 左侧侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
                background-color: transparent; /* 背景透明 */
                padding:10px 0;
                font-size: 16px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
            }

            QPushButton#AttributeButton:hover{
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border-right:1px solid #f0f0f0; /* 右侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }
            QPushButton#BehaviorButton:hover{
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border-left:1px solid #f0f0f0; /* 左侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }

            QPushButton#AttributeButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border-right:1px solid #f0f0f0; /* 右侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }
            QPushButton#BehaviorButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border-left:1px solid #f0f0f0; /* 左侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }

            QPushButton#BehaviorButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border-left:1px solid #f0f0f0; /* 左侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }

            QPushButton#AttributeButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border-right:1px solid #f0f0f0; /* 右侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }

            QWidget#AttributeDisplay, QWidget#BehaviorDisplay, QWidget#DefaultDisplay {
                background-color: white;
            }

            QPushButton#save_button, QPushButton#generate_button {

            }

            QPushButton#save_button:hover, QPushButton#generate_button:hover {

            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 0, 20, 10)

        self.categories = [
            "道路环境要素", "气象环境要素", "车辆致灾要素", "车辆承灾要素",
            "道路承灾要素", "人类承灾要素", "应急资源要素",
            "应急行为要素"
        ]
        element_group_box = QGroupBox(self.tr("涉及的情景要素"))
        element_layout = QGridLayout()
        element_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                background-color: #ffffff;
            }
        """)

        self.checkboxes = {}
        for i, category in enumerate(self.categories):
            checkbox = CustomCheckBoxWithLabel(category)
            self.checkboxes[category] = checkbox
            row = i // 4
            column = i % 4

            alignment = Qt.AlignCenter

            element_layout.addWidget(checkbox, row, column, 1, 1, alignment)

            checkbox.label.clicked.connect(lambda checked_cat=category: self.handle_label_clicked(checked_cat))

        element_group_box_layout = QVBoxLayout()
        element_group_box_layout.addSpacing(5)
        element_group_box_layout.addLayout(element_layout)
        element_group_box_layout.setContentsMargins(0, 12, 0, 12)
        element_group_box.setLayout(element_group_box_layout)
        main_layout.addWidget(element_group_box, 1)

        model_container = QFrame()
        model_container.setObjectName("ModelContainer")
        model_container.setStyleSheet("""
            QFrame#ModelContainer {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: white;
            }
        """)
        model_layout = QVBoxLayout(model_container)
        model_layout.setContentsMargins(0, 0, 0, 10)
        model_layout.setSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.attribute_button = QPushButton(self.tr("属性模型"))
        self.attribute_button.setObjectName("AttributeButton")
        self.attribute_button.setStyleSheet("""
            border-top-left-radius:10px;
        """
        )
        self.attribute_button.setCheckable(True)
        self.attribute_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.behavior_button = QPushButton(self.tr("行为模型"))
        self.behavior_button.setObjectName("BehaviorButton")
        self.behavior_button.setStyleSheet("""
            border-top-right-radius: 10px;
        """)
        self.behavior_button.setCheckable(True)
        self.behavior_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.attribute_button)
        self.button_group.addButton(self.behavior_button)

        button_layout.addWidget(self.attribute_button)
        button_layout.addWidget(self.behavior_button)
        model_layout.addLayout(button_layout)

        self.model_stacked_layout = QStackedLayout()

        self.default_display_widget = QWidget()
        self.default_display_layout = QVBoxLayout(self.default_display_widget)
        self.default_display_layout.setContentsMargins(0, 0, 0, 0)
        self.default_display_layout.setAlignment(Qt.AlignCenter)
        default_label = QLabel(self.tr("请选择模型类别"))
        default_label.setStyleSheet("""
            color: gray;
            font-size: 20pt;
            border-radius: 10px;
            border: 0px solid #c0c0c0;
        """)
        self.default_display_layout.addWidget(default_label)

        self.attribute_display_widget = QWidget()
        self.attribute_display_widget.setObjectName("AttributeDisplay")
        self.attribute_display_layout = QVBoxLayout(self.attribute_display_widget)
        self.attribute_display_layout.setContentsMargins(10, 0, 10, 0)
        self.attribute_display_layout.setSpacing(0)

        self.attribute_scroll = QScrollArea()
        self.attribute_scroll.setWidgetResizable(True)
        self.attribute_scroll.setFrameStyle(QFrame.NoFrame)

        self.attribute_content_widget = QWidget()
        self.attribute_content_layout = QGridLayout(self.attribute_content_widget)
        self.attribute_content_layout.setSpacing(20)
        self.attribute_content_layout.setContentsMargins(15, 15, 15, 15)
        self.attribute_content_layout.setAlignment(Qt.AlignTop)
        self.attribute_content_layout.setColumnMinimumWidth(0, 100)
        self.attribute_content_layout.setColumnMinimumWidth(1, 200)
        self.attribute_content_layout.setColumnMinimumWidth(2, 100)
        self.attribute_content_layout.setColumnMinimumWidth(3, 200)

        self.attribute_content_widget.setLayout(self.attribute_content_layout)
        self.attribute_content_widget.setStyleSheet("background-color: white;")
        self.attribute_content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.attribute_placeholder = QLabel(self.tr("等待上传情景要素模型"))
        self.attribute_placeholder.setAlignment(Qt.AlignCenter)
        self.attribute_placeholder.setObjectName("placeholder")

        self.attribute_switch_layout = QVBoxLayout()
        self.attribute_switch_layout.setContentsMargins(0, 0, 0, 0)
        self.attribute_switch_layout.setSpacing(0)
        self.attribute_switch_layout.addWidget(self.attribute_content_widget)
        self.attribute_switch_layout.addWidget(self.attribute_placeholder)
        self.attribute_switch_layout.setStretch(0, 1)
        self.attribute_switch_layout.setStretch(1, 0)

        self.attribute_content_widget.hide()
        self.attribute_placeholder.show()

        attribute_container = QWidget()
        attribute_container.setLayout(self.attribute_switch_layout)
        self.attribute_scroll.setWidget(attribute_container)

        self.attribute_display_layout.addWidget(self.attribute_scroll)

        self.behavior_display_widget = QWidget()
        self.behavior_display_widget.setObjectName("BehaviorDisplay")
        self.behavior_display_layout = QVBoxLayout(self.behavior_display_widget)
        self.behavior_display_layout.setContentsMargins(10, 0, 10, 0)
        self.behavior_display_layout.setSpacing(0)

        self.behavior_table = QTableWidget()
        self.behavior_table.setColumnCount(3)
        self.behavior_table.setHorizontalHeaderLabels([self.tr("行为名称"), self.tr("行为主体"), self.tr("行为对象")])
        self.behavior_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.behavior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.behavior_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.behavior_table.setSelectionMode(QTableWidget.SingleSelection)

        self.apply_three_line_table_style(self.behavior_table)

        self.behavior_table.horizontalHeader().setStretchLastSection(True)
        self.behavior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.behavior_table.verticalHeader().setVisible(False)
        self.behavior_table.setAlternatingRowColors(True)
        self.behavior_table.setStyleSheet("alternate-background-color: #e9e7e3")

        self.behavior_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.behavior_table.setShowGrid(False)
        self.behavior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.behavior_placeholder = QLabel(self.tr("等待上传情景要素模型"))
        self.behavior_placeholder.setAlignment(Qt.AlignCenter)
        self.behavior_placeholder.setObjectName("placeholder")
        self.behavior_placeholder.hide()

        self.behavior_display_layout.addWidget(self.behavior_table)
        self.behavior_display_layout.addWidget(self.behavior_placeholder)

        self.model_stacked_layout.addWidget(self.default_display_widget)
        self.model_stacked_layout.addWidget(self.attribute_display_widget)
        self.model_stacked_layout.addWidget(self.behavior_display_widget)

        model_layout.addLayout(self.model_stacked_layout)

        main_layout.addWidget(model_container, 5)

        self.init_attribute_model()
        self.init_behavior_model()

        button_layout_main = QHBoxLayout()
        button_layout_main.setAlignment(Qt.AlignRight)
        self.save_button = QPushButton(self.tr("保存"))
        self.save_button.setFixedWidth(110)
        self.save_button.setObjectName("save_button")
        self.save_button.setToolTip(self.tr("点击保存当前配置的要素数据"))

        self.generate_button = QPushButton(self.tr("生成情景模型"))
        self.generate_button.setFixedWidth(110)
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setToolTip(self.tr("点击生成情景级孪生模型"))

        button_layout_main.addWidget(self.save_button)
        button_layout_main.addWidget(self.generate_button)

        main_layout.addLayout(button_layout_main)

        self.save_button.clicked.connect(self.handle_save)
        self.behavior_table.cellDoubleClicked.connect(self.open_behavior_editor)
        self.generate_button.clicked.connect(self.handle_generate)
        self.attribute_button.clicked.connect(lambda: self.switch_model_display("Attribute"))
        self.behavior_button.clicked.connect(lambda: self.switch_model_display("Behavior"))

        self.populate_initial_display()

        self.static_data = {
            "道路环境要素": {
                "attributes": {
                    "道路名称": " ",
                    "道路类型": "主路",
                    "行车道数": " ",
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
                    "燃爆情景": "是",
                    "车辆位置": "KW0058+500",
                    "抛锚情景": "是",
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

        self.category_data = {category: json.loads(json.dumps(data)) for category, data in self.static_data.items()}

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
                "燃爆情景": ["是", "否"],
                "抛锚情景": ["是", "否"],
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

        self.category_to_attributes = {
            category: list(data.get("attributes", {}).keys())
            for category, data in self.static_data.items()
        }

        self.attribute_editors = {category: {} for category in self.categories}

    def init_attribute_model(self):
        pass

    def init_behavior_model(self):
        pass

    def apply_three_line_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black; 
                background-color: white;
    alternate-background-color: #e9e7e3;
            }
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item {
                border: none;
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            QTableWidget:focus {
                outline: none;
            }
        """)
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
        """)
        table.horizontalHeader().repaint()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def reset_behavior_model(self, placeholder_text=None):
        if placeholder_text is None:
            placeholder_text = self.tr("等待上传情景要素模型")
        self.behavior_table.hide()
        self.behavior_placeholder.setText(self.tr(placeholder_text))
        self.behavior_placeholder.show()

    def populate_behavior_model(self, behaviors):
        if behaviors:
            self.behavior_placeholder.hide()
            self.behavior_table.show()

            self.behavior_table.setRowCount(len(behaviors))
            for row_idx, behavior in enumerate(behaviors):
                name_item = QTableWidgetItem(behavior.get("name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 0, name_item)

                subject_item = QTableWidgetItem(behavior.get("subject", ""))
                object_item = QTableWidgetItem(behavior.get("object", ""))
                subject_item.setTextAlignment(Qt.AlignCenter)
                object_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 1, subject_item)
                self.behavior_table.setItem(row_idx, 2, object_item)

            self.apply_three_line_table_style(self.behavior_table)
            self.force_refresh_table_headers(self.behavior_table)
        else:
            self.reset_behavior_model(self.tr("没有行为模型"))

    def load_models_data(self, category):
        print(f"Loading data for category: {category}")
        data = self.category_data.get(category, {})
        attributes = data.get("attributes", {})
        behaviors = data.get("behavior", [])

        print(f"Attributes: {attributes}")
        print(f"Behaviors: {behaviors}")

        current_attribute_labels = self.category_to_attributes.get(category, [])

        if current_attribute_labels:
            self.clear_layout(self.attribute_content_layout)

            groups_per_row = 2
            row = 0
            col = 0
            for label_text in current_attribute_labels:
                label = QLabel(self.tr(label_text))

                enums = self.category_attribute_enums.get(category, {}).get(label_text, None)
                if enums:
                    editor = create_centered_combobox(enums, attributes.get(label_text, "<空>"))
                else:
                    editor = QLineEdit()
                    editor.setText(attributes.get(label_text, ""))
                    editor.setPlaceholderText(self.tr(f"请输入{label_text}"))
                    editor.setAlignment(Qt.AlignCenter)

                if label_text in ["行车道数", "载重量", "交通流量", "人口密度"]:
                    validator = QIntValidator(0, 1000, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)
                elif label_text in ["气温", "风速"]:
                    validator = QDoubleValidator(-50.0, 100.0, 2, self)
                    if isinstance(editor, QLineEdit):
                        editor.setValidator(validator)

                self.attribute_content_layout.addWidget(label, row, col * 2)
                self.attribute_content_layout.addWidget(editor, row, col * 2 + 1)

                self.attribute_editors[category][label_text] = editor

                col += 1
                if col >= groups_per_row:
                    col = 0
                    row += 1

            self.attribute_content_widget.show()
            self.attribute_placeholder.hide()
        else:
            self.attribute_display_widget.hide()
            self.attribute_placeholder.setText(self.tr("没有属性模型"))
            self.attribute_placeholder.show()

        self.populate_behavior_model(behaviors)

        print(f"Finished loading data for category: {category}")

    def open_behavior_editor(self, row, column):
        sender = self.sender()
        if sender != self.behavior_table:
            print("open_behavior_editor called by unknown sender")
            return

        print(f"open_behavior_editor called on row: {row}, column: {column}")
        selected_row = row
        if selected_row < 0:
            CustomWarningDialog(self.tr("警告"), self.tr("请选择一个行为进行编辑！"), parent=self).exec()
            return

        behavior_name_item = self.behavior_table.item(selected_row, 0)
        subject_item = self.behavior_table.item(selected_row, 1)
        object_item = self.behavior_table.item(selected_row, 2)

        if not behavior_name_item:
            CustomWarningDialog(self.tr("警告"), self.tr("行为名称为空，无法编辑。"), parent=self).exec()
            return

        behavior_name = behavior_name_item.text()
        subject = subject_item.text() if subject_item else ""
        obj = object_item.text() if object_item else ""

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

        dialog = EditBehaviorDialog(
            behavior_name,
            subject,
            obj,
            is_subject_enum=enum_config["is_subject_enum"],
            subject_enum_values=enum_config["subject_enum_values"],
            is_object_enum=enum_config["is_object_enum"],
            object_enum_values=enum_config["object_enum_values"],
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            new_subject, new_object = dialog.get_values()

            if isinstance(self.behavior_table.item(selected_row, 1), QTableWidgetItem):
                self.behavior_table.item(selected_row, 1).setText(new_subject)
            else:
                self.behavior_table.setItem(selected_row, 1, QTableWidgetItem(new_subject))

            if isinstance(self.behavior_table.item(selected_row, 2), QTableWidgetItem):
                self.behavior_table.item(selected_row, 2).setText(new_object)
            else:
                self.behavior_table.setItem(selected_row, 2, QTableWidgetItem(new_object))

            if self.current_selected_category:
                if selected_row < len(self.category_data[self.current_selected_category]["behavior"]):
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["subject"] = new_subject
                    self.category_data[self.current_selected_category]["behavior"][selected_row]["object"] = new_object
                else:
                    self.category_data[self.current_selected_category]["behavior"].append({
                        "name": behavior_name,
                        "subject": new_subject,
                        "object": new_object
                    })

    def update_current_category_data(self):
        if not self.current_selected_category:
            return

        category = self.current_selected_category
        attributes = {}
        behaviors = []

        current_attribute_editors = self.attribute_editors.get(category, {})

        for key, editor in current_attribute_editors.items():
            if isinstance(editor, QLineEdit):
                value = editor.text()
            elif isinstance(editor, QComboBox):
                value = editor.currentText()
                if value == "<空>":
                    value = ""
            else:
                value = ""
            attributes[key] = value
            print(f"Collected attribute: {key} = {value}")

        if self.behavior_table:
            for row in range(self.behavior_table.rowCount()):
                behavior_name = self.behavior_table.item(row, 0).text() if self.behavior_table.item(row, 0) else ""
                behavior_subject = self.behavior_table.item(row, 1).text() if self.behavior_table.item(row, 1) else ""
                behavior_object = self.behavior_table.item(row, 2).text() if self.behavior_table.item(row, 2) else ""
                if behavior_name.strip():
                    behaviors.append({
                        "name": behavior_name,
                        "subject": behavior_subject,
                        "object": behavior_object
                    })
                    print(f"Collected behavior: {behavior_name}, {behavior_subject}, {behavior_object}")

        self.category_data[category]["attributes"] = attributes
        self.category_data[category]["behavior"] = behaviors

        print(f"Updated category_data for {category}: {self.category_data[category]}")

    def populate_initial_display(self):
        self.model_stacked_layout.setCurrentWidget(self.default_display_widget)
        self.attribute_display_widget.hide()
        self.behavior_display_widget.hide()

    def handle_label_clicked(self, category):
        print(f"handle_label_clicked called with category: {category}")

        if self.current_selected_category:
            self.update_current_category_data()

        if self.current_selected_category:
            self.checkboxes[self.current_selected_category].set_selected(False)
        self.checkboxes[category].set_selected(True)
        self.current_selected_category = category

        upload_success = self.upload_model_file(category)
        if upload_success:
            self.load_models_data(category)
            self.checkboxes[category].checkbox.setChecked(True)
        else:
            self.load_models_data(category)

    def upload_model_file(self, category):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle(self.tr("选择要素模型文件"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("JSON 文件 (*.json);;所有文件 (*)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print(f"Selected file for {category}: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.checkboxes[category].label.set_uploaded(True)
                    CustomInformationDialog(self.tr("上传成功"), self.tr(f"已成功上传并加载要素模型文件:\n{file_path}"),
                                            parent=self).exec()
                    return True
                except Exception as e:
                    CustomWarningDialog(self.tr("上传失败"), self.tr(f"无法解析文件:\n{str(e)}"), parent=self).exec()
                    return False
        else:
            return False

    def handle_save(self):
        if self.current_selected_category and self.checkboxes[self.current_selected_category].checkbox.isChecked():
            self.update_current_category_data()

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
            CustomInformationDialog(self.tr("保存结果"), self.tr("没有要保存的要素。"), parent=self).exec()
            return

        detailed_info = """
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
                    margin-bottom: 20px;
                }
                h3 {
                    color: #005a9e;
                    margin-top: 30px;
                    margin-bottom: 10px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th, td {
                    border: 1px solid #cccccc;
                    padding: 10px;
                    text-align: center;
                }
                th {
                    background-color: #f0f0f0;
                }
                .no-behavior {
                    color: #ff0000;
                    font-style: italic;
                    text-align: center;
                }
            </style>
        </head>
        <body>
        <h2>""" + self.tr("保存结果详情") + """</h2>
        """

        for item in saved_categories:
            detailed_info += f"<h3>{self.tr('类别')}: {item['category']}</h3>"

            detailed_info += """
            <b>""" + self.tr("属性") + """:</b>
            <table>
                <tr>
                    <th>""" + self.tr("属性名称") + """</th>
                    <th>""" + self.tr("属性值") + """</th>
                </tr>
            """
            for key, value in item['attributes'].items():
                detailed_info += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
                """
            detailed_info += "</table>"

            detailed_info += "<b>" + self.tr("行为模型") + ":</b>"
            if item['behaviors']:
                detailed_info += """
                <table>
                    <tr>
                        <th>""" + self.tr("行为名称") + """</th>
                        <th>""" + self.tr("行为主体") + """</th>
                        <th>""" + self.tr("行为对象") + """</th>
                    </tr>
                """
                for behavior in item['behaviors']:
                    detailed_info += f"""
                    <tr>
                        <td>{behavior['name']}</td>
                        <td>{behavior['subject']}</td>
                        <td>{behavior['object']}</td>
                    </tr>
                    """
                detailed_info += "</table>"
            else:
                detailed_info += "<p class='no-behavior'>" + self.tr("无行为模型") + "</p>"

        detailed_info += "</body></html>"

        save_dialog = SaveResultDialog(saved_categories, detailed_info, parent=self)
        save_dialog.exec()

        self.save_requested.emit()

    def handle_generate(self):
        CustomInformationDialog(" ", self.tr("已成功生成情景级孪生模型。"), parent=self).exec()

    def switch_model_display(self, model_type):
        if self.focusWidget():
            self.focusWidget().clearFocus()

        self.update_current_category_data()

        if model_type == "Attribute":
            self.model_stacked_layout.setCurrentWidget(self.attribute_display_widget)
            self.behavior_display_widget.hide()
            self.attribute_display_widget.show()
        elif model_type == "Behavior":
            self.model_stacked_layout.setCurrentWidget(self.behavior_display_widget)
            self.attribute_display_widget.hide()
            self.behavior_display_widget.show()

    def reset_inputs(self):
        for checkbox in self.checkboxes.values():
            checkbox.checkbox.setChecked(False)
            checkbox.label.set_selected(False)
            checkbox.label.set_uploaded(False)

        self.current_selected_category = None
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText(self.tr("等待上传情景要素模型"))
        self.attribute_placeholder.show()
        self.reset_behavior_model()


class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("情景要素设置"))
        self.resize(1000, 700)
        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.element_setting_tab = ElementSettingTab()
        self.tab_widget.addTab(self.element_setting_tab, self.tr("要素设置"))

        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
