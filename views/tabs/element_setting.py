# element_setting.py
import copy
import sys
import json
import os
import time
from functools import partial
from multiprocessing.util import debug
from typing import Dict, Any, List

from PySide6.QtCore import Signal, Qt, QObject, QEvent, QTimer, QEventLoop
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QGroupBox, QGridLayout,
    QSizePolicy, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFileDialog, QFrame, QApplication, QTabWidget, QFormLayout, QTextEdit, QStackedLayout, QButtonGroup, QTextBrowser,
    QListWidget, QInputDialog
)
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator, QIcon
from PySide6.QtWidgets import QStyledItemDelegate
from attr import attributes
from debugpy.common.timestamp import current
from pydot.dot_parser import add_elements
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.models import Template, Category
from utils.sysml2json import parse_to_json, sysml2json
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_select_dialog import CustomSelectDialog
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
        self.resize(400, 300)

        main_layout = QVBoxLayout(self)

        summary_label = QLabel(self.tr("已保存的情景要素:"))
        summary_label.setFont(QFont("SimSun", 14, QFont.Bold))
        summary_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(summary_label)

        self.summary_list = QListWidget()
        for item in saved_categories:
            self.summary_list.addItem(item['element_name'])  # 使用 element_name 而非 'element'
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
        self.view_details_button.setFixedWidth(110)

        self.ok_button = QPushButton(self.tr("确定"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ok_button.setFixedWidth(110)

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
        close_button.setFixedWidth(110)
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
        print(f"[DEBUG] Label '{self.text()}' set_selected to {selected}")
        self.update_style()

    def set_uploaded(self, uploaded: bool):
        self.uploaded = uploaded
        print(f"[DEBUG] Label '{self.text()}' set_uploaded to {uploaded}")
        self.update_style()

    def update_style(self):
        if self.uploaded:
            color = "#0078d7"  # 蓝色
        else:
            color = "black"     # 黑色

        if self.selected:
            self.setFont(self.selected_font)
        else:
            self.setFont(self.default_font)

        self.setStyleSheet(f"color: {color};")
        print(f"[DEBUG] Label '{self.text()}' style updated to color: {color}, font-weight: {'bold' if self.selected else 'normal'}")
        self.repaint()

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

class ClickableAttributeWidget(QWidget):
    """一个可点击的属性项控件，包含属性名称和展示框。"""
    clicked = Signal(str)  # 发射属性名称信号

    def __init__(self, attr_name, attr_value, attr_type, parent=None):
        super().__init__(parent)
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.attr_type = attr_type
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.name_label = QLabel(self.attr_name)
        self.name_label.setStyleSheet("font-weight: normal;")  # 默认不加粗
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_label.setCursor(Qt.PointingHandCursor)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value_display = QLineEdit()
        self.value_display.setText(self.format_value())
        self.value_display.setStyleSheet("""QLineEdit:focus {
                border: 1px solid #ccc;}""")

        self.value_display.setReadOnly(True)
        self.value_display.setCursor(Qt.PointingHandCursor)
        self.value_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.value_display, 2)

        # 连接点击事件
        self.name_label.mousePressEvent = self.on_clicked
        self.value_display.mousePressEvent = self.on_clicked

    def format_value(self):
        """格式化属性值以适应显示需求。"""
        if isinstance(self.attr_value, list):
            return ", ".join(map(str, self.attr_value))
        elif self.attr_value is None:
            return ""
        else:
            return str(self.attr_value)

    def on_clicked(self, event):
        """发射属性名称信号，触发编辑对话框。"""
        self.clicked.emit(self.attr_name)

    def highlight(self):
        """将标签设置为蓝色加粗，表示正在编辑。"""

        self.name_label.setStyleSheet("font-weight: bold;")


    def unhighlight(self, is_edit):
        """恢复标签的原始样式。"""
        if is_edit == True:
            self.name_label.setStyleSheet("""            QLabel {
color: #0078d7 !important;
font-weight: normal;
            }""")
            print("转为蓝色")
        else:
            self.name_label.setStyleSheet("font-weight:normal")

class EditAttributeDialog(QDialog):
    """编辑属性值的对话框，显示属性名称和类型，并允许修改属性值。"""
    def __init__(self, attr_name, attr_value, attr_type,attr_type_name,is_required, enum_values=None, parent=None):
        super().__init__(parent)
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.attr_type = attr_type
        self.attr_type_name = attr_type_name
        self.is_required = is_required
        self.enum_values = enum_values
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.tr(f"编辑属性: {self.attr_name}"))
        self.setFixedSize(300, 200)
        layout = QVBoxLayout(self)

        # 显示正在编辑的属性名称和类型
        info_label = QLabel(self.tr(f"正在编辑属性: {self.attr_name}\n类型: {self.attr_type_name}"))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)

        # 编辑属性值
        form_layout = QFormLayout()
        self.value_edit = self.create_editor()
        form_layout.addRow(self.tr("属性值:"), self.value_edit)
        layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.tr("保存"))
        self.cancel_button = QPushButton(self.tr("取消"))
        self.save_button.setFixedWidth(110)
        self.cancel_button.setFixedWidth(110)

        # 设置按钮的大小策略，让它们水平扩展以占满空间
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

        # 将按钮添加到布局
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def create_editor(self):
        """根据属性类型创建相应的编辑控件。"""
        if self.attr_type == "Enum":
            combobox = QComboBox()
            if not self.is_required:
                combobox.addItem("<空>")
                for item in self.enum_values:
                    combobox.addItem(item)
                if self.attr_value in self.enum_values:
                    combobox.setCurrentText(self.attr_value)
                else:
                    combobox.setCurrentText("<空>")
            else:
                for item in self.enum_values:
                    combobox.addItem(item)
                combobox.setCurrentText(self.attr_value)
            return combobox
        elif self.attr_type == "Bool":
            checkbox = QCheckBox()
            checkbox.setChecked(str(self.attr_value).lower() in ["true", "1", "yes"])
            return checkbox
        elif self.attr_type == "int":
            line_edit = QLineEdit()
            line_edit.setText(str(self.attr_value) if self.attr_value is not None else "")
            line_edit.setValidator(QIntValidator())
            return line_edit
        elif self.attr_type == "float":
            line_edit = QLineEdit()
            line_edit.setText(str(self.attr_value) if self.attr_value is not None else "")
            line_edit.setValidator(QDoubleValidator())
            return line_edit
        else:
            line_edit = QLineEdit()
            line_edit.setText(str(self.attr_value) if self.attr_value is not None else "")
            return line_edit


    def validate_and_accept(self):
        """验证输入并接受对话框。"""
        if self.attr_type == "Bool":
            new_value = "True" if self.value_edit.isChecked() else "False"
        elif self.attr_type == "Enum":
            new_value = self.value_edit.currentText()
            if new_value == "<空>":
                new_value = ""
        else:
            new_value = self.value_edit.text().strip()

        if not new_value and self.is_required:
            CustomWarningDialog(self.tr("输入错误"), self.tr("该属性值不能为空！")).exec_()
            return

        self.new_value = new_value
        self.accept()

    def get_value(self):
        """获取编辑后的属性值。"""
        return self.new_value

class EditEntityDialog(QDialog):
    """用于编辑实体的对话框，集成了属性模型和行为模型的布局。"""

    def __init__(self, entity_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑实体")
        self.resize(800, 600)
        self.parent = parent
        self.entity_data = entity_data  # 要编辑的实体数据
        self.init_ui()
        self.update_current_element_data()
        self.behavior_table.cellDoubleClicked.connect(self.behavior_table_cell_double_clicked)
        # 默认显示属性模型
        self.switch_model_display("Attribute")

    def behavior_table_cell_double_clicked(self, row, column):
        """处理行为表格单元格双击事件。"""
        behavior = self.get_behavior_from_row(row)
        if behavior:
            self.open_related_object_editor(behavior, "behavior")

    def get_behavior_from_row(self, row):
        """根据行号获取对应的行为对象。"""
        if hasattr(self, 'current_behaviors') and 0 <= row < len(self.current_behaviors):
            return self.current_behaviors[row]
        return None

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 创建顶部描述信息
        label_layout = QHBoxLayout()
        self.entity_label = QLabel(f"正在编辑实体：{self.entity_data.get('element_name', '')}")
        self.entity_label.setAlignment(Qt.AlignCenter)
        self.entity_label.setStyleSheet("font-weight:bold;color:gray;")
        label_layout.addWidget(self.entity_label)

        main_layout.addLayout(label_layout)

        # 创建模型容器和堆叠布局
        self.setup_model_container()
        self.setup_model_stacked_layout()

        main_layout.addWidget(self.model_container)



    def setup_model_container(self, stretch=5):
        """设置模型容器"""
        self.model_container = QFrame()
        self.model_container.setObjectName("ModelContainer")
        self.model_container.setStyleSheet("""
                    QFrame#ModelContainer {
                        border: 1px solid #ccc;
                        border-radius: 10px;
                        background-color: white;
                    }
                """)
        self.model_layout = QVBoxLayout(self.model_container)
        self.model_layout.setContentsMargins(0, 0, 0, 10)
        self.model_layout.setSpacing(10)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(0)

        self.attribute_button = QPushButton(self.tr("属性模型"))
        self.attribute_button.setObjectName("AttributeButton")
        self.attribute_button.setStyleSheet("""
                    border-top-left-radius:10px;
                """)
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

        self.button_layout.addWidget(self.attribute_button)
        self.button_layout.addWidget(self.behavior_button)
        self.model_layout.addLayout(self.button_layout)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.model_container, stretch=stretch)
        # 绑定按钮事件
        self.attribute_button.clicked.connect(partial(self.switch_model_display, "Attribute"))
        self.behavior_button.clicked.connect(partial(self.switch_model_display, "Behavior"))

    def setup_model_stacked_layout(self):
        """设置模型堆叠布局"""
        self.model_stacked_layout = QStackedLayout()

        # 默认显示页面
        self.default_display_widget = QWidget()
        self.default_display_layout = QVBoxLayout(self.default_display_widget)
        self.default_display_layout.setContentsMargins(0, 0, 0, 0)
        self.default_display_layout.setAlignment(Qt.AlignCenter)
        self.default_label = QLabel(self.tr("请选择模型类别"))
        self.default_label.setStyleSheet("""
                    color: gray;
                    font-size: 20pt;
                    border-radius: 10px;
                    border: 0px solid #c0c0c0;
                    background-color: #ffffff;
                """)
        self.default_display_layout.addWidget(self.default_label)

        # 属性模型显示页面
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
        # 移除固定列宽，改为设置列伸缩因子
        self.attribute_content_layout.setColumnStretch(0, 1)
        self.attribute_content_layout.setColumnStretch(1, 1)
        self.attribute_content_layout.setColumnStretch(2, 1)
        self.attribute_content_layout.setColumnStretch(3, 1)

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

        # 行为模型显示页面
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

        # 将各个页面添加到堆叠布局中
        self.model_stacked_layout.addWidget(self.default_display_widget)
        self.model_stacked_layout.addWidget(self.attribute_display_widget)
        self.model_stacked_layout.addWidget(self.behavior_display_widget)

        self.model_layout.addLayout(self.model_stacked_layout)

    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到表格"""
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
        """强制刷新表头样式"""
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
        """清空布局中的所有小部件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def populate_attribute_model(self, attributes):
        """填充属性模型数据到布局中，并实现每行显示两个属性（四个组件）。"""
        self.clear_layout(self.attribute_content_layout)
        if attributes:
            self.attribute_placeholder.hide()
            self.attribute_content_widget.show()

            row = 0
            column = 0
            for i in range(0, len(attributes), 2):
                for j in range(2):
                    if i + j < len(attributes):
                        attr = attributes[i + j]
                        attr_name = attr.get("attribute_name", "")
                        attr_value = self.show_object_value(attr,"attribute")
                        attr_type = attr.get("attribute_type", "")

                        attr_widget = ClickableAttributeWidget(attr_name, attr_value, attr_type)
                        attr_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 组件大小策略
                        attr_widget.clicked.connect(self.open_attribute_editor)

                        self.attribute_content_layout.addWidget(attr_widget, row, column)
                        column += 1
                row += 1
                column = 0

            # 设置列伸缩因子为两列
            for col in range(2):
                self.attribute_content_layout.setColumnStretch(col, 1)
            # 多余列设置为无效
            for col in range(2, 4):
                self.attribute_content_layout.setColumnStretch(col, 0)

        else:
            self.reset_attribute_model(self.tr("没有属性模型"))

    def show_object_value(self, object,type):
        print(f"[DEBUG] 234324234234显示对象值: {object}")
        if type == 'attribute':
            if self.is_related_data(object):
                # 获取关联数据的id
                related_data_id = object['attribute_value']
                if isinstance(related_data_id, int):
                    related_data_id = [related_data_id]
                # 如果是空值
                if not related_data_id:
                    return []
                related_data_name = []
                for id in related_data_id:
                    for item in self.parent.element_data:
                        if self.parent.element_data[item]['element_id'] == id:
                            related_data_name.append(item)
                print(related_data_name)
                return related_data_name
            else:
                return object['attribute_value']
        elif type == 'behavior':
            related_objects = object['related_objects']
            related_objects_name = []
            for id in related_objects:
                for item in self.parent.element_data:
                    if self.parent.element_data[item]['element_id'] == id:
                        related_objects_name.append(item)
            return related_objects_name

    def is_related_data(self, object):
        """检查对象是否是关联数据。"""
        # 获取所有的基础属性类型ID
        # basic_data_type = ['string', 'enum', 'int', 'float', 'boolean']
        # basic_data_type_id = self.get_result_by_sql(
        #     f"SELECT attribute_type_id FROM attribute_type WHERE code IN {tuple(basic_data_type)}")
        # basic_data_type_id = [row[0] for row in basic_data_type_id]
        if object['is_reference'] == 0 or False:
            return False
        return True

    def switch_model_display(self, model_type):
        """切换显示的模型类型"""
        if self.focusWidget():
            self.focusWidget().clearFocus()

        if model_type == "Attribute":
            self.attribute_button.setChecked(True)
            self.model_stacked_layout.setCurrentWidget(self.attribute_display_widget)
            self.behavior_display_widget.hide()
            self.attribute_display_widget.show()
        elif model_type == "Behavior":
            self.behavior_button.setChecked(True)
            self.model_stacked_layout.setCurrentWidget(self.behavior_display_widget)
            self.attribute_display_widget.hide()
            self.behavior_display_widget.show()

    def open_attribute_editor(self, attr_name):
        """打开属性编辑对话框，允许用户编辑属性值。"""
        if self.entity_data:
            element = self.entity_data
            # 查找属性的值和类型
            attr = next((a for a in element.get("attributes", []) if a["attribute_name"] == attr_name), None)
            is_edit = False
            print(attr)
            attr_widget = None
            for i in range(self.attribute_content_layout.count()):
                item = self.attribute_content_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, ClickableAttributeWidget) and widget.attr_name == attr_name:
                        attr_widget = widget
                        break
            attribute_type_result = self.parent.get_result_by_sql(r"SELECT attribute_type_id FROM attribute_type WHERE code IN ('string','enum','int','float','boolean')")
            print(attribute_type_result)
            valid_attribute_type_ids = [row[0] for row in attribute_type_result]  # 提取所有的 attribute_type_id
            print(valid_attribute_type_ids)
            enum_values = []
            if attr and attr["attribute_type_id"] in valid_attribute_type_ids:
                print("基础类型")
                enum_id_result = self.parent.get_result_by_sql(
                    r"SELECT attribute_type_id FROM attribute_type WHERE code IN ('enum')")
                enum_id = [row[0] for row in enum_id_result][0]  # enumid

                # 解析enum_value字符串为列表
                enum_values_result = self.parent.get_result_by_sql(
                    f"SELECT value FROM enum_value WHERE enum_value_id = {attr['enum_value_id']}")
                print(enum_values_result)




                if attr["attribute_type_id"] == enum_id:
                    # 提取查询结果中的字符串并去掉方括号
                    enum_str = enum_values_result[0][0].strip("[]")  # 获取元组中的字符串，并去掉方括号

                    # 根据中文逗号分割字符串
                    enum_values = [item.strip() for item in enum_str.split("，")]
                    print(enum_values)

                if attr_widget:
                    # 高亮显示正在编辑的标签
                    attr_widget.highlight()

                dialog = EditAttributeDialog(
                    attr_name=attr["attribute_name"],
                    attr_value=self.show_object_value(attr,"attribute"),
                    attr_type=self.parent.get_result_by_sql(f"SELECT code FROM attribute_type WHERE attribute_type_id = {attr['attribute_type_id']};")[0][0],
                    attr_type_name=self.parent.get_result_by_sql(f"SELECT name FROM attribute_type WHERE attribute_type_id = {attr['attribute_type_id']};")[0][0],
                    is_required=attr["is_required"],
                    enum_values=enum_values,
                    parent=self.parent
                )
                if dialog.exec():
                    print("确认更新")
                    new_value = dialog.get_value()
                    is_edit = True  # 确认用户进行了编辑

                    if new_value is not None:
                        # 更新属性值
                        attr["attribute_value"] = new_value
                        # 当前元素名字
                        element_name = element.get("element_name")
                        if element_name == "道路环境要素":
                            for attribute in self.parent.element_data['道路承灾要素']['attributes']:
                                if attribute['attribute_name'] == attr_name:
                                    attribute['attribute_value'] = new_value
                        elif element_name == "道路承灾要素":
                            for attribute in self.parent.element_data['道路环境要素']['attributes']:
                                if attribute['attribute_name'] == attr_name:
                                    attribute['attribute_value'] = new_value
                        # 更新显示
                        self.update_current_element_data()
                    attr_widget.unhighlight(is_edit)
                else:
                    print("用户取消了编辑")
                    attr_widget.unhighlight(is_edit)
            else:
                print("编辑复合属性")
                if attr_widget:
                    # 高亮显示正在编辑的标签
                    attr_widget.highlight()

                self.open_related_object_editor(attr,"attribute")


        else:
            CustomWarningDialog(
                self.tr("编辑错误"),
                self.tr("未选中要素。"),
                parent=self
            ).exec_()

    def reset_attribute_model(self, message=None):
        """重置属性模型，显示占位符信息。"""
        self.clear_layout(self.attribute_content_layout)
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText(message or self.tr("没有属性模型"))
        self.attribute_placeholder.show()
    def reset_behavior_model(self, message=None):
        """重置行为模型，显示占位符信息。"""
        self.behavior_table.setRowCount(0)
        self.behavior_placeholder.setText(message or self.tr("没有行为模型"))
        self.behavior_placeholder.show()
        self.behavior_table.hide()

    def populate_behavior_model(self, behaviors):
        """将行为模型数据填充到表格中。"""

        self.behavior_table.setRowCount(0)  # 清空表格中的所有行
        if behaviors:
            self.behavior_placeholder.hide()
            self.behavior_table.show()

            self.behavior_table.setRowCount(len(behaviors))
            for row_idx, behavior in enumerate(behaviors):
                name_item = QTableWidgetItem(behavior.get("behavior_name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 0, name_item)

                # 处理行为主体名称
                subject = behavior.get("behavior_id", "")
                if isinstance(subject, int):
                    subject_name_result = self.parent.get_result_by_sql(
                        f"SELECT element_name FROM element WHERE element_id = (SELECT element_id FROM behavior WHERE behavior_id = {subject})"
                    )
                    subject_name = subject_name_result[0][0] if subject_name_result else "未知"
                else:
                    subject_name = str(subject)
                subject_item = QTableWidgetItem(subject_name)
                subject_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 1, subject_item)

                # 处理行为对象名称
                object_ids = behavior.get("related_objects", [])
                if isinstance(object_ids, list):
                    object_names = self.show_object_value(behavior, "behavior")

                    object_text = ", ".join(object_names)
                else:
                    object_text = "后续处理" if isinstance(object_ids, int) else str(object_ids)
                object_item = QTableWidgetItem(object_text)
                object_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 2, object_item)

            self.apply_three_line_table_style(self.behavior_table)
            self.force_refresh_table_headers(self.behavior_table)
        else:
            self.reset_behavior_model(self.tr("没有行为模型"))

    def update_current_element_data(self):
        """更新当前选中要素的数据到属性和行为模型显示，并确保类别信息存在。"""
        if self.entity_data:
            element = self.entity_data
            print(f"[DEBUG] 更新当234324前要素数据: {element}")
            # 处理属性模型
            self.current_attributes = element.get("attributes", [])
            self.populate_attribute_model(self.current_attributes)
            # 处理行为模型

            self.current_behaviors = element.get("behaviors", [])
            self.populate_behavior_model(self.current_behaviors)
        else:
            self.reset_attribute_model()
            self.reset_behavior_model()



    def open_related_object_editor(self, object, type):
        print(object)
        is_multi_valued = object['is_multi_valued']
        print(is_multi_valued)
        if type == "attribute":
            print(f"编辑属性模型{object['attribute_name']}，属性类型{object['attribute_type_id']}")
            # 获取关联数据的id
            # related_data_id = self.get_result_by_sql(
            #     f"SELECT associated_element_id FROM attribute_association WHERE attribute_id ={object['attribute_id']}")
            # related_data_id = [row[0] for row in related_data_id]
            # print(related_data_id)
            # # 获取关联数据的名称
            # if len(related_data_id) == 1:
            #     # 只有一个元素，使用 = 而不是 IN
            #     query = f"SELECT element_name FROM element WHERE element_id = {related_data_id[0]}"
            # else:
            #     # 多个元素，使用 IN
            #     query = f"SELECT element_name FROM element WHERE element_id IN {tuple(related_data_id)}"
            #
            # # 执行查询
            # related_data_name = self.get_result_by_sql(query)
            # related_data_name = [row[0] for row in related_data_name]
            # print(related_data_name)
            dialog = EditRelatedObjectDialog(
                object_parent=self.parent.element_data,
                object = object,
                type = type,
                parent=self.parent,
                debug=False,
            )
            if dialog.exec():
                print("确认更新")
            else:
                self.update_current_element_data()
        if type == "behavior":
            print(f"编辑行为模型{object['behavior_name']}")
            dialog = EditRelatedObjectDialog(
                object_parent=self.parent.element_data,
                object=object,
                type=type,
                parent=self.parent,
                debug=False,
            )
            if dialog.exec():
                print("确认更新")
            else:
                self.update_current_element_data()

class NegativeIdGenerator:
    """全局负数 ID 生成器，从 -1 开始，每次 -1。"""
    def __init__(self, start: int = -1):
        self.current = start

    def next_id(self) -> int:
        nid = self.current
        self.current -= 1
        return nid


class EditRelatedObjectDialog(QDialog):
    """复合属性编辑窗口"""

    def __init__(self,object_parent,object,type, parent=None,debug = True):
        super().__init__(parent)
        self.associated_element_id = []
        self.is_add = False
        self.all_entities_name = []
        self.all_entities_id = []
        self.new_entities = dict()
        self.selected_entities = set()  # 初始化选中实体集合
        self.setWindowTitle("复合属性编辑")
        self.resize(800, 600)

        self.object_parent = object_parent
        self.object = object
        self.type = type
        self.parent = parent
        self.debug = debug
        self.init_basic_info()

        self.init_ui()

    def init_basic_info(self):
        """初始化基本信息"""
        if self.type == "attribute":

            self.is_multi_valued = self.object['is_multi_valued']
            self.current_name = self.object['attribute_name']
            self.current_type_id = self.parent.get_result_by_sql(f"SELECT attribute_type_id FROM attribute_type WHERE attribute_type_code = '{self.object['attribute_type_code']}'")[0][0]
            self.current_type_name = self.object['attribute_type_code']
            self.is_required = self.object['is_required']
            self.scenario_id = self.parent.scenario_data["scenario_id"]
            for item_key, item_value in self.object_parent.items():
                attributes = item_value.get("attributes", [])
                for attribute in attributes:
                    if int(attribute["attribute_value_id"]) == int(self.object['attribute_value_id']):
                        self.current_element_name = item_key
                        break

        else:
            self.is_multi_valued = self.object['is_multi_valued']
            self.current_name = self.object['behavior_name']
            self.current_type_id = self.object['object_entity_type_id']
            self.current_type_name = self.parent.get_result_by_sql(f"SELECT entity_type_name FROM entity_type WHERE entity_type_id = {self.object['object_entity_type_id']}")[0][0]
            self.is_required = self.object['is_required']
            self.scenario_id = self.parent.scenario_data["scenario_id"]
            for item_key, item_value in self.object_parent.items():
                behaviors = item_value.get("behaviors", [])
                for behavior in behaviors:
                    if int(behavior["behavior_value_id"]) == int(self.object['behavior_value_id']):
                        self.current_element_name = item_key
                        break


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 创建顶部描述信息
        label_layout = QHBoxLayout()
        self.current_behavior_label = QLabel(f"当前正在编辑复合属性：{self.current_name}，属性类型：{self.current_type_name}")
        self.current_behavior_label.setAlignment(Qt.AlignCenter)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:gray;")
        label_layout.addWidget(self.current_behavior_label)

        main_layout.addLayout(label_layout)

        # 创建表格
        self.resource_table = QTableWidget(0, 3)
        self.resource_table.setHorizontalHeaderLabels(["ID", "选中", "实体名称"])
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.setShowGrid(False)
        self.resource_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resource_table.setColumnHidden(0, True)
        self.parent.apply_three_line_table_style(self.resource_table)


        # 加载初始实体数据并默认勾选
        self.load_entities()

        main_layout.addWidget(self.resource_table)

        self.add_resource_btn = QPushButton("增加")
        self.edit_resource_btn = QPushButton("修改")
        self.delete_resource_btn = QPushButton("删除")

        self.add_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/add.png")))
        self.edit_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/edit.png")))
        self.delete_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/delete.png")))

        self.add_resource_btn.setFixedWidth(110)
        self.edit_resource_btn.setFixedWidth(110)
        self.delete_resource_btn.setFixedWidth(110)


        label_layout.addWidget(self.add_resource_btn)
        label_layout.addWidget(self.edit_resource_btn)
        label_layout.addWidget(self.delete_resource_btn)



        self.setLayout(main_layout)

        # 绑定按钮事件
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)

        # 确保没有任何按钮或表格行被选中，并设置焦点到表格
        self.resource_table.clearSelection()
        self.resource_table.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.NoFocus)


    def load_entities(self):
        """加载初始实体数据并默认勾选"""
        # 清空表格
        self.resource_table.setRowCount(0)
        # 清空实体列表
        self.all_entities_id.clear()
        self.all_entities_name.clear()
        # 清空选中实体集合
        self.selected_entities.clear

        if self.type == "attribute":
            # 获取当前属性类型的 element_type_id
            element_type_id = self.object["reference_target_type_id"]
            print(f"当前属性类型的element_type_id：{element_type_id}")

            for item_key, item_value in self.object_parent.items():
                if item_value["entity_type_id"] == element_type_id:
                    self.all_entities_id.append(item_value["entity_id"])
                    self.all_entities_name.append(item_key)

            # 获取当前属性关联的实体 id
            attributes = self.object_parent.get(f"{self.current_element_name}", {}).get("attributes", [])

            # 遍历属性列表，找到匹配的 attribute_name
            self.associated_element_id = []
            for attribute in attributes:
                if attribute["attribute_name"] == self.current_name:
                    # 获取对应的 attribute_value
                    if isinstance(attribute["attribute_value"], list):
                        self.associated_element_id = attribute["attribute_value"]
                    else:
                        self.associated_element_id = [attribute["attribute_value"]]
                    break  # 找到后退出循环

        elif self.type == "behavior":
            # 获取当前行为类型的 element_type_id
            element_type_id = self.object["object_entity_type_id"]

            for item_key, item_value in self.object_parent.items():
                if item_value["entity_type_id"] == element_type_id:
                    self.all_entities_id.append(item_value["entity_id"])
                    self.all_entities_name.append(item_key)

            behaviors = self.object_parent.get(f"{self.current_element_name}", {}).get("behaviors", [])

            # 遍历行为列表，找到匹配的 behavior_name
            self.associated_element_id = []
            for behavior in behaviors:
                if behavior["behavior_name"] == self.current_name:
                    # 获取对应的 related_objects
                    if isinstance(behavior["object_entities"], list):
                        self.associated_element_id = behavior["object_entities"]
                    else:
                        self.associated_element_id = [behavior["object_entities"]]
                    break

        print("[EDIT RELATED OBJECT DIALOG MAIN INFO]: 捕获到associated_element_id:", self.associated_element_id)

        # 插入所有类型匹配的实体到表格
        for idx, (entity_id, entity_name) in enumerate(zip(self.all_entities_id, self.all_entities_name)):
            self.resource_table.insertRow(idx)

            # 设置ID隐藏列
            id_item = QTableWidgetItem(str(entity_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.resource_table.setItem(idx, 0, id_item)

            # 创建并居中复选框
            checkbox = QCheckBox()
            checkbox.setChecked(entity_id in self.associated_element_id)
            checkbox.setStyleSheet("background-color:transparent;")

            # 将选中状态同步到 selected_entities
            if checkbox.isChecked():
                self.selected_entities.add(entity_id)

            # 连接信号，传递 entity_id
            checkbox.stateChanged.connect(lambda state, eid=entity_id: self.on_checkbox_state_changed(eid, state))

            # 创建用于居中复选框的小部件
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addStretch()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setStyleSheet("background-color:transparent;")

            self.resource_table.setCellWidget(idx, 1, checkbox_widget)

            # 设置实体名称并居中
            name_item = QTableWidgetItem(entity_name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.resource_table.setItem(idx, 2, name_item)

        # 处理 associated_element_id 中不在 all_entities_id 的情况
        additional_entities = [eid for eid in self.associated_element_id if eid not in self.all_entities_id]
        starting_row = self.resource_table.rowCount()

        for idx, additional_id in enumerate(additional_entities):
            self.resource_table.insertRow(starting_row + idx)

            # 设置ID隐藏列
            id_item = QTableWidgetItem(str(additional_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.resource_table.setItem(starting_row + idx, 0, id_item)

            # 创建并居中复选框
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setStyleSheet("background-color:transparent;")

            # 将选中状态同步到 selected_entities
            self.selected_entities.add(additional_id)
            # 连接信号
            checkbox.stateChanged.connect(lambda state, eid=additional_id: self.on_checkbox_state_changed(eid, state))

            # 创建用于居中复选框的小部件
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addStretch()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setStyleSheet("background-color:transparent;")

            self.resource_table.setCellWidget(starting_row + idx, 1, checkbox_widget)

            # 获取实体名称
            name = None
            for item_key, item_value in self.object_parent.items():
                if item_value["element_id"] == additional_id:
                    name = item_key  # 假设 item_key 是名称
                    break
            if name:
                name_item = QTableWidgetItem(name)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.resource_table.setItem(starting_row + idx, 2, name_item)
            else:
                name_item = QTableWidgetItem("")
                name_item.setTextAlignment(Qt.AlignCenter)
                self.resource_table.setItem(starting_row + idx, 2, name_item)

        # 移除名字为空的行
        for row in range(self.resource_table.rowCount()):
            if self.resource_table.item(row, 2) and self.resource_table.item(row, 2).text() == "":
                self.resource_table.removeRow(row)

        # 清除任何选择
        self.resource_table.clearSelection()
        self.resource_table.horizontalHeader().setStretchLastSection(True)  # 自动伸展列宽

        # 发送状态信号
        self.on_checkbox_state_changed(None, None)

        # 如果是新建的，直接弹出编辑对话框
        if self.is_add:
            # 获取最后一行
            last_row = self.resource_table.rowCount() - 1
            # 选中最后一行
            self.resource_table.selectRow(last_row)
            # 弹出编辑对话框
            self.edit_resource()
            self.is_add = False


    def add_resource(self):
        """增加新实体"""
        print("增加新实体")
        # 获取可用实体父级
        parent_id = self.parent.get_result_by_sql(
            f"SELECT element_base_parent_id FROM element_base WHERE element_base_id IN (SELECT element_base_id FROM element_base WHERE element_base_type_id = (SELECT element_type_id FROM element_type WHERE name = '{self.current_type_name}'))")
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 捕获到parent_id:{parent_id}")
        parent_id = [item[0] for item in parent_id]
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 转换后parent_id:{parent_id}")
        # 根据parent_id 获取element_base_name
        # 如果只有一个父类，用 = 号，如果有多个父类，用 in
        if len(parent_id) == 1:
            parent_id = parent_id[0]
            parent_name = self.parent.get_result_by_sql(
                f"SELECT element_base_name FROM element_base WHERE element_base_id = {parent_id}")
        else:
            parent_name = self.parent.get_result_by_sql(
            f"SELECT element_base_name FROM element_base WHERE element_base_id IN {tuple(parent_id)}")
        parent_name = [item[0] for item in parent_name]
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 捕获到parent_name:{parent_name}")
        # 新建时候弹出对话框，询问父类和名称
        # 选择父类，也就是选择element_base_parent_id
        # 选择父类
        parent_name, ok = QInputDialog.getItem(self, "选择父类", "选择父类", parent_name, 0, False)
        if not ok:
            return
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户选择了parent_name:{parent_name}")
        # 根据parent_name 获取element_base_id
        parent_id = self.parent.get_result_by_sql(
            f"SELECT element_base_id FROM element_base WHERE element_base_name = '{parent_name}'")[0][0]
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应parent_id:{parent_id}")
        # 结合element_base_type_id和element_base_parent_id，获取element_base_id
        element_base_id = self.parent.get_result_by_sql(
            f"SELECT element_base_id FROM element_base WHERE element_base_type_id = (SELECT element_type_id FROM element_type WHERE name = '{self.current_type_name}') AND element_base_parent_id = {parent_id}")[0][0]
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应element_base_id:{element_base_id}")

        # 输入名称
        name, ok = QInputDialog.getText(self, "输入名称", "输入名称")
        if not ok:
            return
        # 如果名字为空
        if name == "":
            CustomWarningDialog("输入错误","名字不能为空").exec_()
            return
        print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户输入了name:{name}")
        self.add_element_for_scenario(name, element_base_id)
        self.load_entities()

    # def add_element_for_scenario(self, name, element_base_id):
    #     """为情景增加新实体"""
    #     # 从 element_base 中构建新实体
    #     print(f"[ADD ELEMENT MAIN INFO]: 现在根据{element_base_id}和{name},创建element")
    #     element_row = self.parent.get_result_by_sql(f"SELECT * FROM element_base WHERE element_base_id = '{element_base_id}'")
    #     # 获取实际的element_parent_id
    #     element_parent_id = self.parent.get_result_by_sql(f"SELECT element_id FROM element WHERE element_name = (SELECT element_base_name FROM element_base WHERE element_base_id = {element_base_id})")
    #     element_parent_id = element_parent_id[0][0]
    #     print(f"[ADD ELEMETN MAIN INFO]: 查询到：{element_row}")
    #
    #     data = {
    #         "element_id": f"0000{int(count.increment())}", # 作为一个标记
    #         "element_name": name,
    #         "element_type_id": element_row[0][2],
    #         "element_parent_id": element_parent_id,
    #         "attributes": [],
    #         "behaviors": []
    #     }
    #
    #     # 从 attribute_base 中获取属性
    #     attributes_rows = self.parent.get_result_by_sql(f"SELECT * FROM attribute_base WHERE element_base_id = '{element_base_id}'")
    #     for row in attributes_rows:
    #         attribute = {
    #             "attribute_id": f"00000{int(count.increment())}",  # 作为一个标记
    #             "attribute_name": row[1],
    #             "attribute_type_id": row[2],
    #             "is_required": bool(row[3]),
    #             "is_multi_valued": bool(row[4]),
    #             "enum_value_id": row[5],
    #             "attribute_value": "", # 留空，让用户填写
    #         }
    #         data["attributes"].append(attribute)
    #
    #     # 从 behavior_base 中获得行为
    #     behaviors_rows = self.parent.get_result_by_sql(f"SELECT * FROM behavior_base WHERE element_base_id = '{element_base_id}'")
    #     for row in behaviors_rows:
    #         behavior = {
    #             "behavior_id": f"000000{int(count.increment())}",  # 作为一个标记
    #             "behavior_name": row[1],
    #             "is_required": bool(row[2]),
    #             "object_type_id": row[3],
    #             "is_multi_valued": bool(row[4]),
    #             "related_objects": []
    #         }
    #         data["behaviors"].append(behavior)
    #
    #     # 打印json格式的data,有缩进，中文不要转码
    #     print(f"[ADD ELEMETN MAIN INFO]: 新的element数据：{json.dumps(data, ensure_ascii=False, indent=4)}")
    #     # 加入到中介数据object_parent中
    #     # 如果重名，提示用户
    #     # TODO 重名局部域检测
    #     #if f"{name}" in self.object_parent and self.object_parent[f"{name}"]["element_type_id"] == self.parent.get_result_by_sql(f"SELECT element_type_id FROM element_type WHERE name = '{self.current_type_name}'")[0][0]:
    #         # 键已经存在，弹出警告
    #     if f"{name}" in self.object_parent:
    #         CustomWarningDialog("添加失败", "已存在同名实体，请更改名称后重试").exec_()
    #         return
    #     else:
    #         try:
    #             # 键不存在，插入新数据
    #             self.object_parent[f"{name}"] = data
    #         except Exception as e:
    #             print(f"[ADD ELEMENT MAIN INFO]: {e}")
    #             # 这里可以进行其他异常处理
    #             CustomWarningDialog("添加失败", "出现意外错误，请稍后再试").exec_()
    #             return
    #     self.new_entities[name] = data  # 将新建实体存入字典或列表
    #
    #     # 加入到关联列表中
    #     for attribute in self.object_parent[f"{self.current_element_name}"]["attributes"]:
    #         if attribute["attribute_name"] == self.current_name:
    #             # 如果是int，转为list
    #             if isinstance(attribute["attribute_value"], int):
    #                 attribute["attribute_value"] = [attribute["attribute_value"]]
    #             attribute["attribute_value"].append(f"{data['element_id']}")
    #             break
    #
    #     self.previous_selected_entities = set(self.selected_entities)
    #     self.is_add = True
    #     # 打印现在的object_parent，缩进
    #     print(f"[ADD ELEMENT MAIN INFO]: 现在的object_parent数据：{json.dumps(self.object_parent, ensure_ascii=False, indent=4)}")

    def edit_resource(self):
        """修改实体"""
        # 获取选定的实体信息
        selected_items = self.resource_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            entity_name_item = self.resource_table.item(row, 2)
            entity_id_item = self.resource_table.item(row, 0)
            if not entity_name_item or not entity_id_item:
                CustomWarningDialog("错误", "无法获取选定实体的信息。").exec_()
                return

            entity_name = entity_name_item.text()
            entity_id = int(entity_id_item.text())  # 确保为整数

            print(f"尝试修改实体：名称={entity_name}, ID={entity_id}")

            # 获取要编辑的实体数据
            entity_data = None
            for item_key, item_value in self.object_parent.items():
                if item_value["element_name"] == entity_name:
                    entity_data = item_value
                    break

            if not entity_data:
                CustomWarningDialog("错误", "无法找到要编辑的实体。").exec_()
                return

            # 打开编辑对话框
            edit_dialog = EditEntityDialog(entity_data=entity_data, parent=self.parent).exec_()


        else:
            CustomWarningDialog("修改失败", "请先选择要修改的实体。").exec_()

    def delete_resource(self):
        """删除实体"""
        print("删除实体")
        selected_items = self.resource_table.selectedItems()

        if selected_items:
            row = selected_items[0].row()
            # 从第 3 列获取实体名称
            entity_name_item = self.resource_table.item(row, 2)
            entity_state_item = self.resource_table.cellWidget(row, 1)
            entity_id_item = self.resource_table.item(row, 0)
            if not entity_name_item or not entity_id_item:
                QMessageBox.warning(self, "错误", "无法获取选定实体的信息。")
                return
            if entity_state_item.findChild(QCheckBox).isChecked():
                CustomWarningDialog("删除失败", "请先取消选中实体后再删除。").exec_()
                return

            entity_name = entity_name_item.text()
            entity_id = int(entity_id_item.text())  # 确保为整数

            print(f"尝试删除实体：名称={entity_name}, ID={entity_id}")

            # TODO 核心要素不得删除
            core_element = [item[0] for item in self.parent.get_result_by_sql(f"SELECT element_base_name FROM element_base")]
            if entity_name in core_element:
                CustomWarningDialog("删除失败", "核心要素不得删除。").exec_()
                return

            # 遍历是否有正在使用该实体的属性或行为
            for element_key, element in self.object_parent.items():
                if element_key == self.current_element_name:
                    continue
                # 检查属性
                for attribute in element.get("attributes", []):
                    if self.parent.is_related_data(attribute):
                        attribute_values = attribute.get("attribute_value", [])
                        # 确保 attribute_values 是列表
                        if isinstance(attribute_values, int):
                            attribute_values = [attribute_values]
                        elif isinstance(attribute_values, list):
                            attribute_values = [val for val in attribute_values]
                        else:
                            continue  # 不支持的类型，跳过

                        print(f"检查属性 '{attribute['attribute_name']}' 的值: {attribute_values}")

                        if entity_id in attribute_values:
                            CustomWarningDialog(
                                "删除失败",
                                f"该实体被属性 '{attribute['attribute_name']}' 使用，请先解除关联。"
                            ).exec_()
                            return

                # 检查行为
                for behavior in element.get("behaviors", []):
                    related_objects = behavior.get("related_objects", [])
                    # 确保 related_objects 是列表
                    if isinstance(related_objects, int):
                        related_objects = [related_objects]
                    elif isinstance(related_objects, list):
                        related_objects = [obj for obj in related_objects]
                    else:
                        continue  # 不支持的类型，跳过

                    print(f"检查行为 '{behavior['behavior_name']}' 的相关对象: {related_objects}")

                    if entity_id in related_objects:
                        CustomWarningDialog(
                            "删除失败",
                            f"该实体被行为 '{behavior['behavior_name']}' 使用，请先解除关联。"
                        ).exec_()
                        return

            # 从 object_parent 中删除实体
            if entity_name in self.object_parent:
                # 从字典中删除
                self.object_parent.pop(entity_name)
                print(f"已删除实体 '{entity_name}' 从 object_parent。")
                # 从关联列表中删除
                if self.type == "attribute":
                    for attribute in self.object_parent[f"{self.current_element_name}"]["attributes"]:
                        if attribute["attribute_name"] == self.current_name:
                            print(f"删除前：{attribute['attribute_value']}")
                            print(f"删除的实体ID：{entity_id}")
                            # 如果是int，转为list
                            if isinstance(attribute["attribute_value"], int):
                                attribute["attribute_value"] = [attribute["attribute_value"]]
                            # 直接移除实体 ID
                            attribute["attribute_value"].remove(entity_id)
                            break
                elif self.type == "behavior":
                    for behavior in self.object_parent[f"{self.current_element_name}"]["behaviors"]:
                        if behavior["behavior_name"] == self.current_name:
                            print(f"删除前：{behavior['related_objects']}")
                            print(f"删除的实体ID：{entity_id}")
                            # 如果是int，转为list
                            if isinstance(behavior["related_objects"], int):
                                behavior["related_objects"] = [behavior["related_objects"]]
                            # 直接移除实体 ID
                            behavior["related_objects"].remove(entity_id)
                            break

                # 输出格式化的object_parent
                print(
                    f"[DELETE ELEMENT MAIN INFO]: 现在的object_parent数据：{json.dumps(self.object_parent, ensure_ascii=False, indent=4)}")

                self.load_entities()
                CustomWarningDialog("删除成功", f"实体 '{entity_name}' 已删除。").exec_()
            else:
                CustomWarningDialog("删除失败", "无法找到要删除的实体。").exec_()
        else:
            CustomWarningDialog("删除失败", "请先取消选中实体后再删除。").exec_()

    def on_checkbox_state_changed(self, entity_id, state):
        """处理复选框状态变化"""
        # 记录当前的选中状态
        if not self.is_add:
            self.previous_selected_entities = set(self.selected_entities)

        if state == 2:
            self.selected_entities.add(entity_id)
            print(f"实体 {entity_id} 被选中。当前选中列表: {self.selected_entities}")

        else:
            self.selected_entities.discard(entity_id)
            print(f"实体 {entity_id} 被取消选中。当前选中列表: {self.selected_entities}")

        flag = False
        if not self.debug:
            # 如果该属性不是多选项，检查是否选择了多个实体
            if not self.is_multi_valued:
                if len(self.selected_entities) > 1:
                    # 弹出警告框
                    CustomWarningDialog("选择错误", "该属性不支持多选，请只选择一个实体。").exec_()
                    flag = True

                    # 选中刚刚选择的实体，也就是取消之前的选择，就是现在的和之前的做差
                    self.selected_entities = self.selected_entities - self.previous_selected_entities
                    self.previous_selected_entities = self.selected_entities
                    print(f"选中列表已恢复: {self.selected_entities}")

                    # 恢复复选框状态
                    for row in range(self.resource_table.rowCount()):
                        current_entity_id = self.resource_table.item(row, 0).text()
                        if current_entity_id == entity_id:
                            checkbox_widget = self.resource_table.cellWidget(row, 1)
                            if checkbox_widget:
                                checkbox = checkbox_widget.findChild(QCheckBox)
                                if checkbox:
                                    # 阻止信号触发，避免递归调用
                                    checkbox.blockSignals(True)
                                    checkbox.setChecked(entity_id in self.selected_entities)
                                    checkbox.blockSignals(False)
                            break



            # 如果该属性是必选项，检查是否选择了至少一个实体
            if self.is_required and self.previous_selected_entities is not set():
                if not self.selected_entities:
                    # 弹出警告框
                    print(f"214134{self.previous_selected_entities}")
                    if not self.previous_selected_entities or self.previous_selected_entities == {None}:
                        return
                    else:
                        # 如果之前不空，现在空了，才真的要恢复
                        CustomWarningDialog("选择错误", "该属性为必选项，请至少选择一个实体。").exec_()


                    # 恢复之前的选中状态
                    self.selected_entities = self.previous_selected_entities
                    flag = True
                    print(f"选中列表已恢复: {self.selected_entities}")

                    # 恢复复选框状态
                    for row in range(self.resource_table.rowCount()):
                        current_entity_id = self.resource_table.item(row, 0).text()
                        if current_entity_id == entity_id:
                            checkbox_widget = self.resource_table.cellWidget(row, 1)
                            if checkbox_widget:
                                checkbox = checkbox_widget.findChild(QCheckBox)
                                if checkbox:
                                    # 阻止信号触发，避免递归调用
                                    checkbox.blockSignals(True)
                                    checkbox.setChecked(entity_id in self.selected_entities)
                                    checkbox.blockSignals(False)
                            break

        self.update_element()

        if flag:
            # 刷新界面
            self.load_entities()
            return

    def update_element(self):
        # 更新 object_parent
        if self.type == "attribute":
            for attribute in self.object_parent[self.current_element_name]["attributes"]:
                if attribute["attribute_name"] == self.current_name:
                    attribute["attribute_value"] = list(self.selected_entities)
                    break
            # 如果是道路环境要素或者道路承灾要素，同步更新
            if self.current_element_name == "道路环境要素" or self.current_element_name == "道路承灾要素":
                for attribute in self.object_parent["道路环境要素"]["attributes"]:
                    if attribute["attribute_name"] == self.current_name:
                        attribute["attribute_value"] = list(self.selected_entities)
                        break
                for attribute in self.object_parent["道路承灾要素"]["attributes"]:
                    if attribute["attribute_name"] == self.current_name:
                        attribute["attribute_value"] = list(self.selected_entities)
        else:
            for behavior in self.object_parent[self.current_element_name]["behaviors"]:
                if behavior["behavior_name"] == self.current_name:
                    behavior["related_objects"] = list(self.selected_entities)
                    break


class ElementSettingTab(QWidget):
    """情景要素设置标签页"""

    save_requested = Signal()
    # 定义一个信号，传递 SQL 查询字符串
    request_sql_query = Signal(str)
    # 接收查询结果的信号
    receive_sql_result = Signal(list)
    save_to_database_signal= Signal(list)

    def __init__(self):
        super().__init__()
        self.current_selected_element = None
        self.uploaded_files = {}       # 初始化上传文件路径的字典

        self.query_ready = False
        self.query_result = None

        self.init_data()
        self.init_ui()
        self.setup_connections()

        self.session = None
        self.neg_id_gen = NegativeIdGenerator()

        self.switch_model_display("Attribute")

    def init_data(self):
        """初始化数据，加载JSON文件并整理要素数据"""
        # try:
        #     # 使用硬编码路径
        #     json_path = r"D:\PythonProjects\AcademicTool_PySide\test.json"
        #     if not os.path.exists(json_path):
        #         raise FileNotFoundError(f"JSON文件未找到: {json_path}")
        #     with open(json_path, "r", encoding="utf-8") as f:
        #         self.scenario_data = json.load(f)
        #     # 创建一个字典，键为要素名称，值为要素数据
        #     self.element_data = {element["element_name"]: element for element in
        #                          self.scenario_data["scenario"]["elements"]}
        #
        #     self.show_element = [
        #         "道路环境要素", "气象环境要素", "车辆致灾要素", "车辆承灾要素",
        #         "道路承灾要素", "人类承灾要素", "应急资源要素",
        #         "应急行为要素"
        #     ]
        # except Exception as e:
        #     print(f"加载JSON文件失败: {e}")
        #     self.scenario_data = {}
        #     self.element_data = {}
        #     self.show_element = []
        self.scenario_data = {}
        # 创建一个字典，键为要素名称，值为要素数据
        self.element_data = {}

        self.show_element = [
            "道路环境要素", "气象环境要素", "车辆致灾要素", "车辆承灾要素",
            "道路承灾要素", "人类承灾要素", "应急资源要素",
            "应急行为要素"
        ]


    def init_ui(self):
        """初始化用户界面"""
        self.set_style()
        self.setup_main_layout()
        self.setup_element_group_box(1)
        self.setup_model_container(5)
        self.setup_model_stacked_layout()
        self.setup_buttons()
        self.populate_initial_display()

    def set_style(self):
        """设置样式表"""
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
                border-left-radius:10px;
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

    def setup_main_layout(self):
        """设置主布局"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(20, 0, 20, 10)

    def setup_element_group_box(self, stretch=1):
        """设置涉及的情景要素组框，并添加滚动条"""
        self.element_group_box = QGroupBox(self.tr("涉及的情景要素"))
        self.element_group_box.setStyleSheet("""
               QGroupBox {
                   font-size: 16px;
                   font-weight: bold;
                   background-color: #ffffff;
               }
           """)

        # 创建一个垂直布局，用于放置滚动区域
        self.element_group_box_layout = QVBoxLayout()
        self.element_group_box_layout.setContentsMargins(0, 12, 0, 12)
        self.element_group_box_layout.setSpacing(5)

        # 创建一个滚动区域
        self.element_scroll_area = QScrollArea()
        self.element_scroll_area.setWidgetResizable(True)
        self.element_scroll_area.setFrameStyle(QFrame.NoFrame)  # 去掉滚动区域的边框

        # 创建一个容器小部件，用于放置网格布局
        self.element_content_widget = QWidget()
        self.element_layout = QGridLayout(self.element_content_widget)
        self.element_layout.setSpacing(10)
        self.element_layout.setContentsMargins(5, 5, 5, 5)

        # 创建并添加复选框
        self.checkboxes = {}
        for i, element in enumerate(self.show_element):
            checkbox = CustomCheckBoxWithLabel(element)
            self.checkboxes[element] = checkbox
            row = i // 4
            column = i % 4

            alignment = Qt.AlignCenter
            # 连接标签点击信号
            checkbox.label.clicked.connect(partial(self.handle_label_clicked, element, "element"))

            self.element_layout.addWidget(checkbox, row, column, 1, 1, alignment)



        # 将内容小部件设置为滚动区域的子部件
        self.element_scroll_area.setWidget(self.element_content_widget)

        # 将滚动区域添加到组框的布局中
        self.element_group_box_layout.addWidget(self.element_scroll_area)
        self.element_group_box.setLayout(self.element_group_box_layout)
        self.element_group_box.setMaximumHeight(200)  # 设置最大高度以触发滚动条

        # 将组框添加到主布局中，并设置伸缩因子
        self.main_layout.addWidget(self.element_group_box, stretch=stretch)

    def setup_model_container(self, stretch=5):
        """设置模型容器"""
        self.model_container = QFrame()
        self.model_container.setObjectName("ModelContainer")
        self.model_container.setStyleSheet("""
                    QFrame#ModelContainer {
                        border: 1px solid #ccc;
                        border-radius: 10px;
                        background-color: white;
                    }
                """)
        self.model_layout = QVBoxLayout(self.model_container)
        self.model_layout.setContentsMargins(0, 0, 0, 10)
        self.model_layout.setSpacing(10)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(0)

        self.attribute_button = QPushButton(self.tr("属性模型"))
        self.attribute_button.setObjectName("AttributeButton")
        self.attribute_button.setStyleSheet("""
                    border-top-left-radius:10px;
                """)
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

        self.button_layout.addWidget(self.attribute_button)
        self.button_layout.addWidget(self.behavior_button)
        self.model_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.model_container, stretch=stretch)

    def setup_model_stacked_layout(self):
        """设置模型堆叠布局"""
        self.model_stacked_layout = QStackedLayout()

        # 默认显示页面
        self.default_display_widget = QWidget()
        self.default_display_layout = QVBoxLayout(self.default_display_widget)
        self.default_display_layout.setContentsMargins(0, 0, 0, 0)
        self.default_display_layout.setAlignment(Qt.AlignCenter)
        self.default_label = QLabel(self.tr("请选择模型类别"))
        self.default_label.setStyleSheet("""
                    color: gray;
                    font-size: 20pt;
                    border-radius: 10px;
                    border: 0px solid #c0c0c0;
                    background-color: #ffffff;
                """)
        self.default_display_layout.addWidget(self.default_label)

        # 属性模型显示页面
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
        # 移除固定列宽，改为设置列伸缩因子
        self.attribute_content_layout.setColumnStretch(0, 1)
        self.attribute_content_layout.setColumnStretch(1, 1)
        self.attribute_content_layout.setColumnStretch(2, 1)
        self.attribute_content_layout.setColumnStretch(3, 1)

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

        # 行为模型显示页面
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

        # 将各个页面添加到堆叠布局中
        self.model_stacked_layout.addWidget(self.default_display_widget)
        self.model_stacked_layout.addWidget(self.attribute_display_widget)
        self.model_stacked_layout.addWidget(self.behavior_display_widget)

        self.model_layout.addLayout(self.model_stacked_layout)

    def setup_buttons(self):
        """设置底部的保存和生成按钮"""
        self.button_layout_main = QHBoxLayout()
        self.button_layout_main.setAlignment(Qt.AlignRight)

        # 保存按钮
        self.save_button = QPushButton(self.tr("保存"))
        self.save_button.setFixedWidth(110)
        self.save_button.setObjectName("save_button")
        self.save_button.setToolTip(self.tr("点击保存当前配置的要素数据"))

        # 生成情景模型按钮
        self.generate_button = QPushButton(self.tr("生成情景模型"))
        self.generate_button.setFixedWidth(110)
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setToolTip(self.tr("点击生成情景级孪生模型"))

        self.button_layout_main.addWidget(self.save_button)
        self.button_layout_main.addWidget(self.generate_button)

        self.main_layout.addLayout(self.button_layout_main)

    def setup_connections(self):
        """设置信号与槽的连接。"""
        self.save_button.clicked.connect(self.handle_save)
        self.generate_button.clicked.connect(self.handle_generate)
        self.behavior_table.cellDoubleClicked.connect(self.behavior_table_cell_double_clicked)
        self.attribute_button.clicked.connect(lambda: self.switch_model_display("Attribute"))
        self.behavior_button.clicked.connect(lambda: self.switch_model_display("Behavior"))
        self.receive_sql_result.connect(self.handle_sql_result)

    def behavior_table_cell_double_clicked(self, row, column):
        """处理行为表格单元格双击事件。"""
        behavior = self.get_behavior_from_row(row)
        if behavior:
            self.open_related_object_editor(behavior, "behavior")

    def get_behavior_from_row(self, row):
        """根据行号获取对应的行为对象。"""
        if hasattr(self, 'current_behaviors') and 0 <= row < len(self.current_behaviors):
            return self.current_behaviors[row]
        return None

    def clear_layout(self, layout):
        """清空布局中的所有小部件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def populate_initial_display(self):
        """初始化显示，默认显示页面"""
        self.model_stacked_layout.setCurrentWidget(self.default_display_widget)
        self.attribute_display_widget.hide()
        self.behavior_display_widget.hide()

    def reset_behavior_model(self, placeholder_text=None):
        """重置行为模型显示"""
        if placeholder_text is None:
            placeholder_text = self.tr("等待上传情景要素模型")
        self.behavior_table.hide()
        self.behavior_placeholder.setText(self.tr(placeholder_text))
        self.behavior_placeholder.show()

    def populate_behavior_model(self, behaviors):
        """将行为模型数据填充到表格中。"""

        self.behavior_table.setRowCount(0)  # 清空表格中的所有行
        if behaviors:
            self.behavior_placeholder.hide()
            self.behavior_table.show()

            self.behavior_table.setRowCount(len(behaviors))
            for row_idx, behavior in enumerate(behaviors):
                name_item = QTableWidgetItem(behavior.get("behavior_name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 0, name_item)

                # 处理行为主体名称
                subject_name = self.element_data[self.current_selected_entity].get("entity_name", "")
                subject_item = QTableWidgetItem(subject_name)
                subject_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 1, subject_item)

                # 处理行为对象名称
                object_ids = behavior.get("related_objects", [])
                if isinstance(object_ids, list):
                    object_names = self.show_object_value(behavior, "behavior")

                    object_text = ", ".join(object_names)
                else:
                    object_text = "后续处理" if isinstance(object_ids, int) else str(object_ids)
                object_item = QTableWidgetItem(object_text)
                object_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 2, object_item)

            self.apply_three_line_table_style(self.behavior_table)
            self.force_refresh_table_headers(self.behavior_table)
        else:
            self.reset_behavior_model(self.tr("没有行为模型"))

    def apply_three_line_table_style(self, table: QTableWidget):
        """应用三线表样式到表格"""
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
        """强制刷新表头样式"""
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

    def reset_attribute_model(self, placeholder_text=None):
        """重置属性模型显示"""
        if placeholder_text is None:
            placeholder_text = self.tr("等待上传情景要素模型")
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText(self.tr(placeholder_text))
        self.attribute_placeholder.show()

    def populate_attribute_model(self, attributes):
        """填充属性模型数据到布局中，并实现每行显示两个属性（四个组件）。"""
        self.clear_layout(self.attribute_content_layout)
        if attributes:
            self.attribute_placeholder.hide()
            self.attribute_content_widget.show()

            row = 0
            column = 0
            for i in range(0, len(attributes), 2):
                for j in range(2):
                    if i + j < len(attributes):
                        attr = attributes[i + j]
                        attr_name = attr.get("china_default_name", "")
                        attr_value = self.show_object_value(attr,"attribute")
                        attr_type = attr.get("attribute_type", "")

                        attr_widget = ClickableAttributeWidget(attr_name, attr_value, attr_type)
                        attr_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 组件大小策略
                        attr_widget.clicked.connect(self.open_attribute_editor)

                        self.attribute_content_layout.addWidget(attr_widget, row, column)
                        column += 1
                row += 1
                column = 0

            # 设置列伸缩因子为两列
            for col in range(2):
                self.attribute_content_layout.setColumnStretch(col, 1)
            # 多余列设置为无效
            for col in range(2, 4):
                self.attribute_content_layout.setColumnStretch(col, 0)

        else:
            self.reset_attribute_model(self.tr("没有属性模型"))

    def open_attribute_editor(self, attr_name):
        """打开属性编辑对话框，允许用户编辑属性值。"""
        if self.current_selected_entity:
            element = self.element_data[self.current_selected_entity]
            print(f"当前选中编辑的要素：{element}")
            # 查找属性的值和类型
            attr = next((a for a in element.get("attributes", []) if a["china_default_name"] == attr_name), None)
            is_edit = False
            print(attr)
            attr_widget = None
            for i in range(self.attribute_content_layout.count()):
                item = self.attribute_content_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, ClickableAttributeWidget) and widget.attr_name == attr_name:
                        attr_widget = widget
                        break

            enum_values = []
            print(f"当前属性：{attr}")
            if attr and attr["attribute_type_code"] in ["String", "Enum", "Int", "Real", "Bool"]:
                print("基础类型")




                if attr["attribute_type_code"] == "Enum":

                    enum_values_result = self.get_result_by_sql(
                        f"SELECT enum_value FROM enum_value WHERE attribute_definition_id = {attr['attribute_definition_id']};")
                    print(enum_values_result)

                    enum_values = [item[0] for item in enum_values_result]
                    print(enum_values)

                if attr_widget:
                    # 高亮显示正在编辑的标签
                    attr_widget.highlight()

                dialog = EditAttributeDialog(
                    attr_name=attr["attribute_name"],
                    attr_value=self.show_object_value(attr,"attribute"),
                    attr_type=attr["attribute_type_code"],
                    attr_type_name=self.get_result_by_sql(f"SELECT attribute_type_name FROM attribute_type WHERE attribute_type_code = '{attr['attribute_type_code']}';")[0][0],
                    is_required=attr["is_required"],
                    enum_values=enum_values,
                    parent=self
                )
                if dialog.exec():
                    print("确认更新")
                    new_value = dialog.get_value()
                    is_edit = True  # 确认用户进行了编辑

                    if new_value is not None:
                        # 更新属性值
                        attr["attribute_value"] = new_value
                        element_name = element.get("element_name")
                        # if element_name == "道路环境要素":
                        #     for attribute in self.element_data['道路承灾要素']['attributes']:
                        #         if attribute['attribute_name'] == attr_name:
                        #             attribute['attribute_value'] = new_value
                        # elif element_name == "道路承灾要素":
                        #     for attribute in self.element_data['道路环境要素']['attributes']:
                        #         if attribute['attribute_name'] == attr_name:
                        #             attribute['attribute_value'] = new_value
                        # 更新显示
                        self.update_current_element_data()
                    attr_widget.unhighlight(is_edit)
                else:
                    print("用户取消了编辑")
                    attr_widget.unhighlight(is_edit)
            else:
                print("编辑复合属性")
                if attr_widget:
                    # 高亮显示正在编辑的标签
                    attr_widget.highlight()

                self.open_related_object_editor(attr,"attribute")


        else:
            CustomWarningDialog(
                self.tr("编辑错误"),
                self.tr("未选中要素。"),
                parent=self
            ).exec_()

    def show_object_value(self, object,type):
        if type == 'attribute':
            if self.is_related_data(object):
                # 获取关联数据的id
                related_data_id = object['attribute_value']
                if isinstance(related_data_id, int):
                    related_data_id = [related_data_id]
                related_data_name = []
                # 如果是空值
                if not related_data_id:
                    return []
                for id in related_data_id:
                    for item in self.element_data:
                        if self.element_data[item]['element_id'] == id:
                            related_data_name.append(item)
                print(related_data_name)
                return related_data_name
            else:
                return object['attribute_value']
        elif type == 'behavior':
            related_objects = object['object_entities']
            related_objects_name = []
            for id in related_objects:
                for item in self.element_data:
                    if self.element_data[item]['element_id'] == id:
                        related_objects_name.append(item)
            return related_objects_name

    def is_related_data(self, object):
        """检查对象是否是关联数据。"""
        # 获取所有的基础属性类型ID
        # basic_data_type = ['string', 'enum', 'int', 'float', 'boolean']
        # basic_data_type_id = self.get_result_by_sql(
        #     f"SELECT attribute_type_id FROM attribute_type WHERE code IN {tuple(basic_data_type)}")
        # basic_data_type_id = [row[0] for row in basic_data_type_id]
        if object['is_reference'] == 0 or False:
            return False
        return True

    def phrased_upload_data(self, data,element_name):
        """解析上传的数据，将其填充到element_data中"""
        data = sysml2json(data[0])
        extracted_data = []
        print(f"23124{element_name}")

        for item in data:
            name = item.get("@name", "")
            datavalue = item.get("datavalue", "")
            # 清理 datavalue 中多余的双引号
            if isinstance(datavalue, str):
                datavalue = datavalue.strip('"')

            extracted_data.append({"name": name, "datavalue": datavalue})

        # 打印格式化后的数据，有缩进
        print(f"解析结果{json.dumps(extracted_data, indent=4, ensure_ascii=False)}")


        # 更新element_data

    def open_related_object_editor(self, object, type):
        print(object)
        is_multi_valued = object['is_multi_valued']
        print(is_multi_valued)
        if type == "attribute":
            print(f"编辑属性模型{object['attribute_name']}，属性类型{object['attribute_type_code']}")
            # 获取关联数据的id
            # related_data_id = self.get_result_by_sql(
            #     f"SELECT associated_element_id FROM attribute_association WHERE attribute_id ={object['attribute_id']}")
            # related_data_id = [row[0] for row in related_data_id]
            # print(related_data_id)
            # # 获取关联数据的名称
            # if len(related_data_id) == 1:
            #     # 只有一个元素，使用 = 而不是 IN
            #     query = f"SELECT element_name FROM element WHERE element_id = {related_data_id[0]}"
            # else:
            #     # 多个元素，使用 IN
            #     query = f"SELECT element_name FROM element WHERE element_id IN {tuple(related_data_id)}"
            #
            # # 执行查询
            # related_data_name = self.get_result_by_sql(query)
            # related_data_name = [row[0] for row in related_data_name]
            # print(related_data_name)
            dialog = EditRelatedObjectDialog(
                object_parent=self.element_data,
                object = object,
                type = type,
                parent=self,
                debug = False
            )
            if dialog.exec():
                print("确认更新")
            else:
                self.update_current_element_data()
        if type == "behavior":
            print(f"编辑行为模型{object['behavior_name']}")
            dialog = EditRelatedObjectDialog(
                object_parent=self.element_data,
                object=object,
                type=type,
                parent=self,
                debug=False
            )
            if dialog.exec():
                print("确认更新")
            else:
                self.update_current_element_data()


    def update_current_element_data(self):
        """更新当前选中要素的数据到属性和行为模型显示，并确保类别信息存在。"""
        print(self.current_selected_entity)
        if self.current_selected_entity:
            element = self.element_data[self.current_selected_entity]
            print(f"更新要素{self.current_selected_element}的数据")
            print(f"要素数据{json.dumps(element, ensure_ascii=False, indent=2)}")
            # 处理属性模型
            self.current_attributes = element.get("attributes", [])
            print(f"属性模型数据{self.current_attributes}")
            self.populate_attribute_model(self.current_attributes)
            # 处理行为模型

            self.current_behaviors = element.get("behaviors", [])
            print(f"行为模型数据{self.current_behaviors}")
            self.populate_behavior_model(self.current_behaviors)
        else:
            self.reset_attribute_model()
            self.reset_behavior_model()

    def handle_label_clicked(self, element, type):
        """处理标签点击事件，弹出文件上传对话框，并根据上传结果更新样式。"""
        print(f"[DEBUG] Clicked on '{element}' of type '{type}'")
        self.current_selected_element = element

        # 设置当前选中的要素
        new_checkbox = self.checkboxes[element].checkbox
        new_label = self.checkboxes[element].label
        new_label.selected = True

        # 弹出实体窗口
        CustomSelectDialog(
            parent=self
        ).exec()
        # rule = self.get_result_by_sql(
        #     f"SELECT template_restrict FROM template WHERE template_name = '{element}'"
        # )
        # rule = json.loads(rule[0][0])
        # print(f"规则：{rule}")
        #
        # filtered_data = self.filter_entities_by_select_rule(self.element_data, rule)
        # print(f"过滤后的数据：{filtered_data}")
        #
        # # 询问名字
        # ask_name = CustomInputDialog(
        #     self.tr("新建实体"),
        #     self.tr("请输入新建实体的名称"),
        #     parent=self
        # )
        # ask_name.exec()
        # new_entity = self.create_entities_with_negative_ids(element,ask_name.get_input())
        # print(f"新建的实体：{new_entity}")
        #
        # print(f"[DEBUG] Selecting element '{element}'")
        #
        # # 检查是否已经上传过文件
        # already_uploaded = element in self.uploaded_files
        # print(f"[DEBUG] Element '{element}' already uploaded: {already_uploaded}")
        #
        # if already_uploaded:
        #     # 提示是否重新上传
        #     reply = CustomQuestionDialog(
        #         self.tr("重新上传"),
        #         self.tr("该要素已上传文件。是否重新上传？"),
        #         parent=self
        #     ).ask()
        #     if not reply:
        #         # 用户选择不重新上传，保持原有状态
        #         print(f"[DEBUG] User chose not to re-upload element '{element}'")
        #         new_label.set_selected(True)
        #         for element, checkbox in self.checkboxes.items():
        #             if checkbox.checkbox is not new_checkbox:
        #                 checkbox.label.set_selected(False)
        #             checkbox.label.update_style()
        #         # 更新当前要素的数据展示
        #         print(f"[DEBUG] Current selected element: {element}")
        #         self.update_current_element_data()
        #
        #         return
        #
        #
        # # 弹出文件上传对话框
        # file_dialog = QFileDialog(self, self.tr("上传文件"), "", "All Files (*)")
        # file_dialog.setFileMode(QFileDialog.ExistingFile)
        #
        # if file_dialog.exec():
        #     selected_files = file_dialog.selectedFiles()
        #     if selected_files:
        #         # 用户选择了文件，存储上传的文件路径
        #         self.phrased_upload_data(selected_files,element)
        #         self.uploaded_files[element] = selected_files[0]
        #         print(f"[DEBUG] Uploaded file for element '{element}': {selected_files[0]}")
        #         new_checkbox.setChecked(True)
        #         new_label.set_uploaded(True)
        #
        new_checkbox.setChecked(True)
        new_label.set_uploaded(True)
        new_label.set_selected(True)
        for element,checkbox in self.checkboxes.items():
            if checkbox.checkbox is not new_checkbox:
                checkbox.label.set_selected(False)
            checkbox.label.update_style()
        # # 更新当前要素的数据展示
        self.update_current_element_data()
        # print(f"[DEBUG] Current selected element: {element}")

    def filter_entities_by_select_rule(self,
            entity_data: Dict[str, Dict[str, Any]],
            select_rule: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:


        # 1. 从 select_rule 中获取可能的过滤条件
        desired_entity_type = select_rule['select'].get("entity_type", None)
        print(f"desired_entity_type: {desired_entity_type}")
        desired_category_type = select_rule['select'].get("category_type", None)
        print(f"desired_category_type: {desired_category_type}")
        attribute_limit = select_rule['select'].get("attribute", None)

        ENTITY_TYPE_MAP = {
            1: "Vehicle",  # 车辆
            2: "Road",  # 路段
            3: "Meteorology",  # 自然环境
            4: "ResponseResource",  # 应急资源
            5: "ResponseAction",  # 应急行为
            6: "VehiclePart",  # 车辆部件
            7: "VehicleLoad",  # 承载物
            8: "Facility",  # 基础设施
            11: "Lane",  # 车道
            12: "People",  # 人类
            13: "ResponsePlan",  # 应急预案
        }

        # 2. 定义一个帮助函数, 判断单个实体是否匹配
        def match_entity(einfo: Dict[str, Any]) -> bool:
            # (a) 检查 entity_type
            if desired_entity_type:
                # 根据 entity_type_id 转成字符串(如 "Vehicle")
                etid = einfo.get("entity_type_id")
                et_code = ENTITY_TYPE_MAP.get(etid, None)
                if et_code != desired_entity_type:
                    return False

            # (b) 检查 category_type
            if desired_category_type:
                categories = einfo.get("categories", [])
                # categories: List[Dict[str, Any]] with "category_name", etc.

                # 先取该实体所有的 category_name
                entity_cat_names = [c["category_name"] for c in categories if "category_name" in c]

                if isinstance(desired_category_type, str):
                    # 模糊匹配：检查是否有任何 category_name 包含 desired_category_type
                    if not any(desired_category_type in cat for cat in entity_cat_names):
                        return False

                elif isinstance(desired_category_type, list):
                    # 需要该实体包含列表中任意(或全部?) 这里假设只要包含其一即可
                    # 若需“实体包含全部列表”逻辑，可改写
                    intersect = set(entity_cat_names) & set(desired_category_type)
                    if not intersect:
                        return False

            # (c) 检查 attribute
            if attribute_limit:
                for limit in attribute_limit:
                    for key, value in limit.items():
                        for attribute in einfo["attributes"]:
                            if attribute["attribute_name"] == key:
                                # 如果是布尔值, 则转换为字符串
                                print(f"a324324ttribute: {attribute}")
                                if attribute["attribute_type_code"] == "Bool":
                                    # 把true转为1, false转为0
                                    attribute["attribute_value"] = "0" if attribute["attribute_value"] == "False" else attribute["attribute_value"]
                                    attribute["attribute_value"] = "1" if attribute["attribute_value"] == "True" else attribute["attribute_value"]
                                if attribute["attribute_value"] != value:
                                    return False

            # 如果没被任何条件筛掉, 表示匹配
            return True

        # 3. 逐个实体检查, 构造返回结果
        filtered = []
        for ename, einfo in entity_data.items():
            if match_entity(einfo):
                filtered.append(ename)

        return filtered

    def create_entities_with_negative_ids(self, element,name) -> Dict[str, Any]:
        """
        1. 遍历所有 template;
        2. 为每个 template 构造一个“复制品” JSON 对象:
           - entity_id 用负数 ID
           - categories 来自 template_restrict["create"]["category_type"]
           - attributes、behaviors 来自 template.attribute_definitions / template.behavior_definitions
             并将 attribute_value = default_value(若非None)或None
        3. 返回 dict: { "xxx_复制品": { entity JSON }, ... }
        """
        neg_id_gen = self.neg_id_gen  # 从 -1 开始

        # 最终的字典
        replicated_data: Dict[str, Any] = {}
        #抓取指定模板
        templates: List[Template] = self.session.query(Template).filter(Template.template_name == element).all()
        print(f"模板{templates}")

        for tpl in templates:
            # 不要直接 json.loads(tpl.template_restrict)
            if isinstance(tpl.template_restrict, dict):
                restrict_dict = tpl.template_restrict
            elif isinstance(tpl.template_restrict, str):
                # 如果是字符串，再手动 loads
                restrict_dict = json.loads(tpl.template_restrict)
            else:
                raise TypeError(f"template_restrict is unexpected type: {type(tpl.template_restrict)}")

            create_part = restrict_dict.get("create", {})
            cat_names = create_part.get("category_type", [])  # ["AffectedElement","HazardElement"]等
            if isinstance(cat_names, str):
                cat_names = [cat_names]  # 确保是列表
            attribute_limit = create_part.get("attribute", [])

            # 给该“实体”分配一个负数ID
            entity_negative_id = neg_id_gen.next_id()
            entity_key = entity_negative_id  # 作为外层 dict key

            # 构建 entity JSON
            entity_json = {
                "entity_id": entity_negative_id,
                "entity_name": name,
                "entity_type_id": tpl.entity_type_id,
                "entity_parent_id": None,
                "scenario_id": self.scenario_data["scenario_id"],
                "create_time": "2025-01-15 15:04:45",
                "update_time": "2025-01-15 15:04:45",
                "categories": [],
                "attributes": [],
                "behaviors": []
            }

            # 处理分类(来自category_type)
            for cname in cat_names:
                cat_obj = self.session.query(Category).filter(Category.category_name == cname).first()
                print(f"分类{cat_obj}")

                if cat_obj:
                    entity_json["categories"].append({
                        "category_id": cat_obj.category_id,
                        "category_name": cat_obj.category_name,
                        "description": cat_obj.description
                    })
                else:
                    # 如果数据库没有该分类
                    entity_json["categories"].append({
                        "category_id": 0,
                        "category_name": cname,
                        "description": None
                    })

            # 构建 attributes
            for attr_def in tpl.attribute_definitions:
                # 不一定要给每个 AttributeValue 分配负数 ID
                # 若需要可以类似 next_id() => -2, -3...
                attribute_json = {
                    "attribute_value_id": neg_id_gen.next_id(),  # 也可以 neg_id_gen.next_id()
                    "attribute_definition_id": attr_def.attribute_definition_id,
                    "attribute_name": attr_def.attribute_code.attribute_code_name,
                    "china_default_name": attr_def.china_default_name,
                    "english_default_name": attr_def.english_default_name,
                    "attribute_code_name": attr_def.attribute_code.attribute_code_name,
                    "attribute_aspect_name": attr_def.attribute_aspect.attribute_aspect_name,
                    "attribute_type_code": attr_def.attribute_type.attribute_type_code,
                    "is_required": bool(attr_def.is_required),
                    "is_multi_valued": bool(attr_def.is_multi_valued),
                    "is_reference": bool(attr_def.is_reference),
                    "reference_target_type_id": attr_def.reference_target_type_id,
                    "default_value": attr_def.default_value,
                    "description": attr_def.description,
                    "attribute_value": attr_def.default_value if attr_def.default_value is not None else None,
                    "referenced_entities": []
                }
                entity_json["attributes"].append(attribute_json)

            # 形如：[{"CasualtyCondition": "1"}]
            if attribute_limit:
                for limit in attribute_limit:
                    for key, value in limit.items():
                        for attribute in entity_json["attributes"]:
                            if attribute["attribute_code_name"] == key:
                                attribute["attribute_value"] = value


            # 构建 behaviors
            for bhv_def in tpl.behavior_definitions:
                behavior_json = {
                    "behavior_value_id": neg_id_gen.next_id(),  # 同理,可用负数 if needed
                    "behavior_definition_id": bhv_def.behavior_definition_id,
                    "behavior_name": bhv_def.behavior_name,
                    "object_entity_type_id": bhv_def.object_entity_type_id,
                    "is_required": bool(bhv_def.is_required),
                    "is_multi_valued": bool(bhv_def.is_multi_valued),
                    "description": bhv_def.description,
                    "create_time": "2025-01-15 15:04:45",
                    "update_time": "2025-01-15 15:04:45",
                    "object_entities": []
                }
                entity_json["behaviors"].append(behavior_json)

            replicated_data[entity_key] = entity_json

        return replicated_data

    def handle_save(self):
        """处理保存按钮点击事件，仅展示保存的数据。"""
        try:
            saved_elements = []
            # 深拷贝要素数据
            data = copy.deepcopy(self.element_data)
            flag = False
            for element, checkbox in self.checkboxes.items():
                if not checkbox.checkbox.isChecked():
                    data.pop(element, None)
                else:
                    flag = True

            if not flag:
                CustomInformationDialog(
                    self.tr("保存结果"),
                    self.tr("没有要保存的要素。"),
                    parent=self
                ).exec()
                return

            print(f"Data to be saved: {json.dumps(data, ensure_ascii=False, indent=2)}")

            for item in data.values():
                saved_element = {
                    "element_id": item["element_id"],
                    "element_name": item["element_name"],
                    "element_type_id": item["element_type_id"],
                    "element_parent_id": item["element_parent_id"],
                    "attributes": item.get("attributes", []),
                    "behaviors": item.get("behaviors", [])
                }
                saved_elements.append(saved_element)

            # 检测is_required属性是否为空
            for item in saved_elements:
                for attr in item['attributes']:
                    if attr['is_required'] == 1 and not attr['attribute_value']:
                        CustomWarningDialog(
                            self.tr("保存失败"),
                            self.tr(f"{item['element_name']} 的属性 {attr['attribute_name']} 不能为空。"),
                            parent=self
                        ).exec()
                        return
                for behavior in item['behaviors']:
                    if behavior['is_required'] == 1 and not behavior['related_objects']:
                        CustomWarningDialog(
                            self.tr("保存失败"),
                            self.tr(f"{item['element_name']} 的行为 {behavior['behavior_name']} 不能为空。"),
                            parent=self
                        ).exec()
                        return



            print(f"Saving categories: {json.dumps(saved_elements, ensure_ascii=False, indent=2)}")
            # 保存到result,json
            with open("result.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(saved_elements, ensure_ascii=False, indent=2))
                print(f"保存成功，保存路径为{os.path.abspath('result.json')}")

            show_saved_elements = [item for item in saved_elements if item['element_name'] in self.show_element]

            # 生成详细信息的HTML内容
            detailed_info = self.generate_detailed_info_html(show_saved_elements)

            # 显示保存结果对话框
            save_dialog = SaveResultDialog(show_saved_elements, detailed_info, parent=self)
            save_dialog.exec()

            # 触发保存请求信号
            self.save_requested.emit()
            self.save_to_database_signal.emit(saved_elements)

        except Exception as e:
            print(f"保存过程中发生错误: {e}")
            CustomWarningDialog(
                self.tr("保存失败"),
                self.tr(f"保存过程中发生错误:\n{str(e)}"),
                parent=self
            ).exec_()

    def generate_detailed_info_html(self, show_saved_elements):
        """生成保存结果的详细信息HTML内容。"""
        # 去除八大情景要素之外的
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

        for item in show_saved_elements:
            detailed_info += f"<h3>{self.tr('元素')}: {item['element_name']}</h3>"

            detailed_info += """
            <b>""" + self.tr("属性") + """:</b>
            <table>
                <tr>
                    <th>""" + self.tr("属性名称") + """</th>
                    <th>""" + self.tr("属性值") + """</th>
                    <th>""" + self.tr("属性类别") + """</th>
                </tr>
            """
            for attr in item['attributes']:
                detailed_info += f"""
                <tr>
                    <td>{attr['attribute_name']}</td>
                    <td>{str(self.show_object_value(attr,"attribute")).strip("[]").replace("'", "")}</td>
                    <td>{self.get_result_by_sql(f"SELECT name FROM attribute_type WHERE attribute_type_id = {attr['attribute_type_id']}")[0][0]}</td>
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
                    behavior_name = behavior.get('behavior_name', '')
                    behavior_subject = item['element_name']
                    behavior_object = str(self.show_object_value(behavior,"behavior")).strip("[]").replace("'", "")
                    detailed_info += f"""
                    <tr>
                        <td>{behavior_name}</td>
                        <td>{behavior_subject}</td>
                        <td>{behavior_object}</td>
                    </tr>
                    """
                detailed_info += "</table>"
            else:
                detailed_info += "<p class='no-behavior'>" + self.tr("无行为模型") + "</p>"

        detailed_info += "</body></html>"
        return detailed_info

    def handle_generate(self):
        """处理生成情景模型按钮点击事件"""
        CustomInformationDialog(" ", self.tr("已成功生成情景级孪生模型。"), parent=self).exec()

    def switch_model_display(self, model_type):
        """切换显示的模型类型"""
        if self.focusWidget():
            self.focusWidget().clearFocus()

        if model_type == "Attribute":
            self.attribute_button.setChecked(True)
            self.model_stacked_layout.setCurrentWidget(self.attribute_display_widget)
            self.behavior_display_widget.hide()
            self.attribute_display_widget.show()
        elif model_type == "Behavior":
            self.behavior_button.setChecked(True)
            self.model_stacked_layout.setCurrentWidget(self.behavior_display_widget)
            self.attribute_display_widget.hide()
            self.behavior_display_widget.show()

    def reset_inputs(self):
        """重置所有输入项"""
        for checkbox in self.checkboxes.values():
            checkbox.checkbox.setChecked(False)
            checkbox.label.set_selected(False)
            checkbox.label.set_uploaded(False)

        self.current_selected_element = None
        self.attribute_content_widget.hide()
        self.attribute_placeholder.setText(self.tr("等待上传情景要素模型"))
        self.attribute_placeholder.show()
        self.reset_behavior_model()

    def send_sql_request(self, sql_query):
        print("发送查询请求：", sql_query)
        self.request_sql_query.emit(sql_query)
        self.query_ready = False

    def handle_sql_result(self, result):
        """接收到查询结果时调用"""
        print("收到查询结果:", result)
        self.query_result = result  # 将结果保存在类属性中
        self.query_ready = True  # 设置标志为查询完成

    def get_result_by_sql(self, sql_query):
        """触发查询请求并等待结果"""
        self.send_sql_request(sql_query)


        return self.query_result

# 主程序入口
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
