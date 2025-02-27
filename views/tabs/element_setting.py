# element_setting.py
import copy
import sys
import json
import os
import time
import datetime
from functools import partial
from multiprocessing.util import debug
from typing import Dict, Any, List

from PySide6.QtCore import Signal, Qt, QObject, QEvent, QTimer, QEventLoop
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QGroupBox, QGridLayout,
    QSizePolicy, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFileDialog, QFrame, QApplication, QTabWidget, QFormLayout, QTextEdit, QStackedLayout, QButtonGroup, QTextBrowser,
    QListWidget, QInputDialog, QProxyStyle, QStyle
)
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator, QIcon, QColor
from PySide6.QtWidgets import QStyledItemDelegate
from attr import attributes
from debugpy.common.timestamp import current
from pydot.dot_parser import add_elements
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.models import Template, Category
from utils.json2sysml import json_to_sysml2_txt
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_select_dialog import CustomSelectDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.dialogs.entity_type_select import EntityTypeDialog


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
            self.summary_list.addItem(item['entity_name'])  # 使用 element_name 而非 'element'
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
        self.name_label.setStyleSheet(("color: #0078d7 !important;"))


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
            print(f"234234{self.attr_value}")
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
        self.entity_label = QLabel(f"正在编辑实体：{self.entity_data.get('entity_name', '')}")
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
            for attr in attributes:
                # 检查 self.element 的值，决定是否显示该属性
                if self.parent.should_hide_attribute(attr):
                    continue

                attr_name = attr.get("china_default_name", "")
                attr_value = self.show_object_value(attr, "attribute")
                attr_type = attr.get("attribute_type", "")
                if attr.get("attribute_type_code") == "Bool":
                    print(f"266231{attr_value}")
                    attr_value = "是" if attr_value == "True" else "否"

                attr_widget = ClickableAttributeWidget(attr_name, attr_value, attr_type)
                attr_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 组件大小策略
                attr_widget.clicked.connect(self.open_attribute_editor)

                self.attribute_content_layout.addWidget(attr_widget, row, column)
                column += 1

                # 每行显示两个组件，满两列后换行
                if column >= 2:
                    column = 0
                    row += 1

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
                if object['attribute_value']:
                    related_data_id = object['attribute_value']
                if object.get('referenced_entities'):
                    related_data_id = object['referenced_entities']
                    if isinstance(related_data_id, int):
                        related_data_id = [related_data_id]
                else:
                    # 获取所有parent_id是current_selected_entity的元素

                    # related_data_id = self.get_result_by_sql(
                    #     f"SELECT entity_id FROM element WHERE parent_id = {self.current_selected_entity}")
                    related_data_id = []
                    for item in self.parent.element_data:
                        if self.parent.element_data[item]['entity_parent_id'] == self.entity_data['entity_id'] and self.parent.element_data[item]['entity_type_id'] == object['reference_target_type_id']:
                            related_data_id.append(self.parent.element_data[item]['entity_id'])

                if isinstance(related_data_id, int):
                    related_data_id = [related_data_id]
                # 如果是空值
                if not related_data_id:
                    return []
                related_data_name = []
                for id in related_data_id:
                    for item in self.parent.element_data:
                        if self.parent.element_data[item]['entity_id'] == id:
                            related_data_name.append(self.parent.element_data[item]['entity_name'])
                print(related_data_name)
                return related_data_name
            else:
                return object['attribute_value']
        elif type == 'behavior':
            related_objects = object['object_entities']
            related_objects_name = []
            for id in related_objects:
                for item in self.parent.element_data:
                    if self.parent.element_data[item]['entity_id'] == id:
                        related_objects_name.append(self.parent.element_data[item]['entity_name'])
            return related_objects_name

    def is_related_data(self, object):
        """检查对象是否是关联数据。"""
        # 获取所有的基础属性类型ID
        # basic_data_type = ['string', 'enum', 'int', 'float', 'boolean']
        # basic_data_type_id = self.get_result_by_sql(
        #     f"SELECT attribute_type_id FROM attribute_type WHERE code IN {tuple(basic_data_type)}")
        # basic_data_type_id = [row[0] for row in basic_data_type_id]
        if object['is_reference'] == 0 or False or str(object['is_reference']).lower() == 'false':
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

                    enum_values_result = self.parent.get_result_by_sql(
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
                    attr_type_name=self.parent.get_result_by_sql(f"SELECT attribute_type_name FROM attribute_type WHERE attribute_type_code = '{attr['attribute_type_code']}';")[0][0],
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
                name_item = QTableWidgetItem(behavior.get("china_default_name", ""))
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
                object_ids = behavior.get("object_entities", [])
                if isinstance(object_ids, list):
                    object_names = self.show_object_value(behavior, "behavior")

                    object_text = ", ".join([str(name) for name in object_names])

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
            try:
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
            except ValueError as e:
                print(f"创建对话框失败: {e}")
                return
        if type == "behavior":
            print(f"编辑行为模型{object['behavior_name']}")
            try:
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
            except ValueError as e:
                print(f"创建对话框失败: {e}")
                return

class NegativeIdGenerator:
    """全局负数 ID 生成器，从 -1 开始，每次 -1。"""
    def __init__(self, start: int = -1):
        self.current = start

    def next_id(self) -> int:
        nid = self.current
        self.current -= 1
        return nid

class BorderStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        # 针对复选框指示器进行特殊处理
        if element == QStyle.PE_IndicatorCheckBox:
            # 调用默认绘制（系统会绘制复选框和对勾）
            super().drawPrimitive(element, option, painter, widget)
            # 然后在 indicator 上绘制边框
            painter.save()
            painter.setPen(QColor("#AAAAAA"))
            # option.rect 表示指示器的绘制区域
            rect = option.rect
            # 调整矩形（减 1 是为了让边框完整显示在内部）
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            painter.restore()
        else:
            # 其他控件使用默认绘制
            super().drawPrimitive(element, option, painter, widget)

class EditRelatedObjectDialog(QDialog):
    """复合属性编辑窗口"""

    def __init__(self,object_parent,object,type, parent=None,debug = True):
        super().__init__(parent)
        self.has_changes = False
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
        try:
            self.init_basic_info()
            self.init_ui()
        except ValueError as e:
            # 如果初始化失败，确保对话框被正确关闭
            self.reject()
            raise  # 重新抛出异常

    def closeEvent(self, event):
        """重写关闭事件处理"""
        if self.has_changes:
            # 如果有更改，正常接受关闭
            event.accept()
        else:
            # 如果没有更改，恢复到初始状态
            # self.selected_entities = self.previous_selected_entities
            self.update_element()
            event.accept()

    def accept(self):
        """重写接受处理"""
        if not self.has_changes:
            # 如果没有更改，恢复初始状态
            # self.selected_entities = self.previous_selected_entities
            self.update_element()
        super().accept()

    def reject(self):
        """重写取消处理"""
        # 恢复到初始状态
       # self.selected_entities = self.previous_selected_entities
        self.update_element()
        super().reject()

    def init_basic_info(self):
        """初始化基本信息"""
        if self.type == "attribute":

            self.is_multi_valued = self.object['is_multi_valued']
            self.current_name = self.object['attribute_code_name']
            self.current_type_id = self.parent.get_result_by_sql(f"SELECT attribute_type_id FROM attribute_type WHERE attribute_type_code = '{self.object['attribute_type_code']}'")[0][0]
            self.current_type_name = self.object['attribute_type_code'] # 属性类型代码
            self.is_required = self.object['is_required']
            self.scenario_id = self.parent.scenario_data["scenario_id"]
            if self.object['reference_target_type_id']:
                self.target_type_id = self.object['reference_target_type_id']
                self.target_type_name = self.parent.get_result_by_sql(f"SELECT entity_type_name FROM entity_type WHERE entity_type_id = {self.object['reference_target_type_id']}")[0][0]
            else:
                # 弹出对话框选择关联实体类型
                entity_types = self.parent.get_result_by_sql(
                    "SELECT entity_type_id, entity_type_name FROM entity_type WHERE is_item_type = 1")
                if not entity_types:
                    QMessageBox.warning(self, "警告", "没有可用的实体类型。")
                    raise ValueError("没有可用的实体类型")  # 抛出异常而不是直接关闭

                dialog = EntityTypeDialog(entity_types, self)
                result = dialog.exec()

                if result == QDialog.Accepted:
                    self.target_type_id, self.target_type_name = dialog.get_selected_entity()
                else:
                    CustomInformationDialog("未选择任何实体类型", "未选择任何实体类型。").exec_()
                    raise ValueError("未选择任何实体类型")  # 抛出异常而不是直接关闭


            for item_key, item_value in self.object_parent.items():
                attributes = item_value.get("attributes", [])
                for attribute in attributes:
                    if int(attribute["attribute_value_id"]) == int(self.object['attribute_value_id']):
                        self.current_element_name = item_key # 这里实际上是id
                        break

        else:
            self.is_multi_valued = self.object['is_multi_valued']
            self.current_name = self.object['behavior_code_name']
            if self.object['object_entity_type_id']:
                self.current_type_id = self.object['object_entity_type_id']
                self.target_type_name = self.parent.get_result_by_sql(
                    f"SELECT entity_type_name FROM entity_type WHERE entity_type_id = {self.object['object_entity_type_id']}")[
                    0][0]
                self.current_type_name = self.parent.get_result_by_sql(f"SELECT entity_type_name FROM entity_type WHERE entity_type_id = {self.object['object_entity_type_id']}")[0][0]
                self.target_type_id = self.object['object_entity_type_id']
            else:
                # 弹出对话框选择关联实体类型
                entity_types = self.parent.get_result_by_sql(
                    "SELECT entity_type_id, entity_type_name FROM entity_type WHERE is_item_type = 0")
                if not entity_types:
                    QMessageBox.warning(self, "警告", "没有可用的实体类型。")
                    raise ValueError("没有可用的实体类型")
                dialog = EntityTypeDialog(entity_types, self)
                result = dialog.exec()

                if result == QDialog.Accepted:
                    self.current_type_id, self.current_type_name = dialog.get_selected_entity()
                    self.target_type_name = self.current_type_name
                    self.target_type_id = self.current_type_id
                else:
                    CustomInformationDialog("未选择任何实体类型", "未选择任何实体类型。").exec_()
                    raise ValueError("未选择任何实体类型")  # 抛出异常而不是直接关闭

            self.is_required = self.object['is_required']
            self.scenario_id = self.parent.scenario_data["scenario_id"]

            for item_key, item_value in self.object_parent.items():
                behaviors = item_value.get("behaviors", [])
                for behavior in behaviors:
                    if int(behavior["behavior_value_id"]) == int(self.object['behavior_value_id']):
                        self.current_element_name = item_key # 这里实际上是id
                        break


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 创建顶部描述信息
        label_layout = QHBoxLayout()
        self.current_behavior_label = QLabel(f"当前正在编辑复合属性：{self.current_name}，属性类型：{self.current_type_name}, 实体类型：{self.target_type_name}")
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
        self.selected_entities.clear()


        if self.type == "attribute":
            # 获取当前属性类型的 element_type_id
            element_type_id = self.target_type_id
            print(f"当前属性类型的element_type_id：{element_type_id}")

            for item_key, item_value in self.object_parent.items():
                if item_value["entity_type_id"] == element_type_id:
                    self.all_entities_id.append(item_value["entity_id"])
                    self.all_entities_name.append(item_value["entity_name"])

            # 获取当前属性关联的实体 id
            attributes = self.object_parent.get(self.current_element_name, {}).get("attributes", [])

            # 遍历属性列表，找到匹配的 attribute_name
            print(f"324234324{self.current_name}")
            print(f"324234324{attributes}")

            # 重置 associated_element_id
            self.associated_element_id = []

            # 先找到当前正在编辑的属性
            current_attribute = None

            for attribute in attributes:
                if attribute["attribute_code_name"] == self.current_name:
                    current_attribute = attribute
                    break

            print(f"当前3412属性：{current_attribute}")
            print(f"当134前属性:{self.current_name}")

            if current_attribute:
                # 只更新当前编辑属性的关联实体
                for item in self.parent.element_data.keys():
                    if (self.parent.element_data[item]['entity_type_id'] == self.target_type_id and
                            self.parent.element_data[item]['entity_parent_id'] == self.current_element_name):

                        # 如果不是列表，转为列表
                        if not isinstance(current_attribute["attribute_value"], list):
                            current_attribute["attribute_value"] = []
                            current_attribute["referenced_entities"] = []

                        # 避免重复添加
                        if item not in current_attribute["attribute_value"]:
                            current_attribute["attribute_value"].append(item)
                        if item not in current_attribute["referenced_entities"]:
                            current_attribute["referenced_entities"].append(item)

                # 获取当前属性的关联实体
                if isinstance(current_attribute["attribute_value"], list):
                    self.associated_element_id = current_attribute["attribute_value"]
                else:
                    self.associated_element_id = [current_attribute["attribute_value"]]

                # 使用 referenced_entities 作为最终的关联实体列表
                if isinstance(current_attribute["referenced_entities"], list):
                    self.associated_element_id = current_attribute["referenced_entities"]
                else:
                    self.associated_element_id = [current_attribute["referenced_entities"]]


            print(f"当前属性关联的实体IDs: {self.associated_element_id}")

        elif self.type == "behavior":
            # 获取当前行为类型的 element_type_id
            element_type_id = self.target_type_id

            for item_key, item_value in self.object_parent.items():
                if item_value["entity_type_id"] == element_type_id:
                    self.all_entities_id.append(item_value["entity_id"])
                    self.all_entities_name.append(item_value["entity_name"])

            behaviors = self.object_parent.get(self.current_element_name, {}).get("behaviors", [])

            # 遍历行为列表，找到匹配的 behavior_name
            self.associated_element_id = []
            for behavior in behaviors:
                if behavior["behavior_code_name"] == self.current_name:
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
            checkbox.setStyle(BorderStyle(checkbox.style()))

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
                if item_value["entity_id"] == additional_id:
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
        # 从后向前遍历删除空行，这样不会影响索引
        for row in range(self.resource_table.rowCount() - 1, -1, -1):
            item = self.resource_table.item(row, 2)
            if item is None or item.text() == "":
                # 隐藏行
                self.resource_table.hideRow(row)

        # 确保表格状态更新
        self.resource_table.viewport().update()

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
        # 获取新建实体名字
        name, ok = QInputDialog.getText(self, "输入名称", "输入名称")
        if not ok:
            return
        # 如果名字为空
        if name == "":
            CustomWarningDialog("输入错误", "名字不能为空").exec_()
            return
        # 判断是属性还是行为
        if self.type == "attribute":
            # 判断属性类型
            if self.current_type_name == "Item":
                # 调用parent的方法建立实体
                # 获取模板名称
                template_name = self.parent.get_result_by_sql(f"SELECT template_name FROM template WHERE entity_type_id = {self.target_type_id} AND category_id = 5")[0][0]
                new_entity = self.parent.create_entities_with_negative_ids(template_name, name)
                # 打印信息
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 创建了新实体{name}:{template_name}:{new_entity}")
                self.parent.element_data.update(new_entity)
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 更新后的element_data:{self.parent.element_data}")
                self.new_entities.update(new_entity)
                self.is_add = True
                self.load_entities()

            else:
                # 调用parent的方法建立实体
                # 获取符合entity_type_id的模板的类别信息
                # 获取所有类别的 category_id
                category_id = self.parent.get_result_by_sql(
                    f"SELECT category_id FROM template WHERE entity_type_id = {self.target_type_id}")
                category_ids = [item[0] for item in category_id]

                # 确保类别 ID 存在
                if len(category_ids) == 0:
                    CustomWarningDialog("错误", "无法找到类别信息").exec_()
                    return

                # 查询所有类别的名称，并建立 ID 与名称的映射
                if len(category_ids) == 1:
                    query = f"SELECT category_id, category_name FROM category WHERE category_id = {category_ids[0]}"
                else:
                    query = f"SELECT category_id, category_name FROM category WHERE category_id IN {tuple(category_ids)}"

                result = self.parent.get_result_by_sql(query)
                # 构建 ID 与名称的对应关系
                category_map = {row[0]: row[1] for row in result}

                # 打印映射关系用于调试
                print(f"[DEBUG] category_map: {category_map}")
                # 弹出对话框，选择类别
                category_name, ok = QInputDialog.getItem(self, "选择类别", "选择类别", category_map.values(), 0, False)
                if not ok:
                    return
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户选择了类别:{category_name}")
                # 根据类别名称获取类别 ID
                category_id = [key for key, value in category_map.items() if value == category_name][0]
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应category_id:{category_id}")

                # 获取模板名称
                template_name = self.parent.get_result_by_sql(f"SELECT template_name FROM template WHERE entity_type_id = {self.target_type_id} AND category_id = {category_id}")[0][0]
                new_entity = self.parent.create_entities_with_negative_ids(template_name, name)
                # # 打印信息
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 创建了新实体{name}:{template_name}:{new_entity}")
                self.parent.element_data.update(new_entity)
                self.new_entities.update(new_entity)
                self.is_add = True
                self.load_entities()
        else:
            # 判断属性类型
            if self.current_type_name == "Item":
                # 调用parent的方法建立实体
                # 获取模板名称
                template_name = self.parent.get_result_by_sql(
                    f"SELECT template_name FROM template WHERE entity_type_id = {self.target_type_id} AND category_id = 5")[
                    0][0]
                new_entity = self.parent.create_entities_with_negative_ids(template_name, name)
                # 打印信息
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 创建了新实体{name}:{template_name}:{new_entity}")
                self.parent.element_data.update(new_entity)
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 更新后的element_data:{self.parent.element_data}")
                self.new_entities.update(new_entity)
                self.is_add = True
                self.load_entities()

            else:
                # 调用parent的方法建立实体
                # 获取符合entity_type_id的模板的类别信息
                # 获取所有类别的 category_id
                category_id = self.parent.get_result_by_sql(
                    f"SELECT category_id FROM template WHERE entity_type_id = {self.target_type_id}")
                category_ids = [item[0] for item in category_id]

                # 确保类别 ID 存在
                if len(category_ids) == 0:
                    CustomWarningDialog("错误", "无法找到类别信息").exec_()
                    return

                # 查询所有类别的名称，并建立 ID 与名称的映射
                # 如果是一个值，同=
                if len(category_ids) == 1:
                    query = f"SELECT category_id, category_name FROM category WHERE category_id = {category_ids[0]}"

                else:
                    query = f"SELECT category_id, category_name FROM category WHERE category_id IN {tuple(category_ids)}"
                result = self.parent.get_result_by_sql(query)

                # 构建 ID 与名称的对应关系
                category_map = {row[0]: row[1] for row in result}

                # 打印映射关系用于调试
                print(f"[DEBUG] category_map: {category_map}")
                # 弹出对话框，选择类别
                category_name, ok = QInputDialog.getItem(self, "选择类别", "选择类别", category_map.values(), 0, False)
                if not ok:
                    return
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户选择了类别:{category_name}")
                # 根据类别名称获取类别 ID
                category_id = [key for key, value in category_map.items() if value == category_name][0]
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应category_id:{category_id}")

                # 获取模板名称
                template_name = self.parent.get_result_by_sql(
                    f"SELECT template_name FROM template WHERE entity_type_id = {self.target_type_id} AND category_id = {category_id}")[
                    0][0]
                new_entity = self.parent.create_entities_with_negative_ids(template_name, name)
                # # 打印信息
                print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 创建了新实体{name}:{template_name}:{new_entity}")
                self.parent.element_data.update(new_entity)
                self.new_entities.update(new_entity)
                self.is_add = True
                self.load_entities()

        # print("增加新实体")
        # # 获取可用实体父级
        # parent_id = self.parent.get_result_by_sql(
        #     f"SELECT element_base_parent_id FROM element_base WHERE element_base_id IN (SELECT element_base_id FROM element_base WHERE element_base_type_id = (SELECT element_type_id FROM element_type WHERE name = '{self.current_type_name}'))")
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 捕获到parent_id:{parent_id}")
        # parent_id = [item[0] for item in parent_id]
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 转换后parent_id:{parent_id}")
        # # 根据parent_id 获取element_base_name
        # # 如果只有一个父类，用 = 号，如果有多个父类，用 in
        # if len(parent_id) == 1:
        #     parent_id = parent_id[0]
        #     parent_name = self.parent.get_result_by_sql(
        #         f"SELECT element_base_name FROM element_base WHERE element_base_id = {parent_id}")
        # else:
        #     parent_name = self.parent.get_result_by_sql(
        #     f"SELECT element_base_name FROM element_base WHERE element_base_id IN {tuple(parent_id)}")
        # parent_name = [item[0] for item in parent_name]
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 捕获到parent_name:{parent_name}")
        # # 新建时候弹出对话框，询问父类和名称
        # # 选择父类，也就是选择element_base_parent_id
        # # 选择父类
        # parent_name, ok = QInputDialog.getItem(self, "选择父类", "选择父类", parent_name, 0, False)
        # if not ok:
        #     return
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户选择了parent_name:{parent_name}")
        # # 根据parent_name 获取element_base_id
        # parent_id = self.parent.get_result_by_sql(
        #     f"SELECT element_base_id FROM element_base WHERE element_base_name = '{parent_name}'")[0][0]
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应parent_id:{parent_id}")
        # # 结合element_base_type_id和element_base_parent_id，获取element_base_id
        # element_base_id = self.parent.get_result_by_sql(
        #     f"SELECT element_base_id FROM element_base WHERE element_base_type_id = (SELECT element_type_id FROM element_type WHERE name = '{self.current_type_name}') AND element_base_parent_id = {parent_id}")[0][0]
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 对应element_base_id:{element_base_id}")
        #
        # # 输入名称
        # name, ok = QInputDialog.getText(self, "输入名称", "输入名称")
        # if not ok:
        #     return
        # # 如果名字为空
        # if name == "":
        #     CustomWarningDialog("输入错误","名字不能为空").exec_()
        #     return
        # print(f"[EDIT RELATED OBJECT DIALOG MAIN INFO]: 用户输入了name:{name}")
        # self.add_element_for_scenario(name, element_base_id)
        # self.load_entities()

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
                if item_value["entity_id"] == entity_id:
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

        if not selected_items:
            CustomWarningDialog("删除失败", "请选择要删除的实体。").exec_()
            return

        row = selected_items[0].row()
        # 获取实体信息
        entity_name_item = self.resource_table.item(row, 2)
        entity_state_item = self.resource_table.cellWidget(row, 1)
        entity_id_item = self.resource_table.item(row, 0)

        # 如果是最后一个item，不允许删除
        if self.resource_table.rowCount() - 1 == 0:
            CustomWarningDialog("删除失败", "请不要删除最后一个实体。").exec_()
            return

        if not entity_name_item or not entity_id_item:
            CustomWarningDialog("错误", "无法获取选定实体的信息。").exec_()
            return

        if entity_state_item.findChild(QCheckBox).isChecked():
            CustomWarningDialog("删除失败", "请先取消选中实体后再删除。").exec_()
            return

        entity_name = entity_name_item.text()
        entity_id = int(entity_id_item.text())

        print(f"尝试删除实体：名称={entity_name}, ID={entity_id}")

        # 检查是否是核心要素
        core_elements = [item[0] for item in self.parent.get_result_by_sql(
            "SELECT element_base_name FROM element_base")]
        if entity_name in core_elements:
            CustomWarningDialog("删除失败", "核心要素不得删除。").exec_()
            return

        # 检查依赖关系
        try:
            if self._check_entity_dependencies(entity_id, entity_name):
                return

            # 执行删除操作
            if self._perform_entity_deletion(entity_id, entity_name):
                self.selected_entities.discard(entity_id)
                self.load_entities()
                CustomInformationDialog("删除成功", f"实体 '{entity_name}' 已删除。").exec_()
            else:
                CustomWarningDialog("删除失败", "无法找到要删除的实体。").exec_()
        except Exception as e:
            print(f"删除实体时发生错误: {e}")
            CustomWarningDialog("删除失败", f"删除过程中发生错误：{str(e)}").exec_()

    def _check_entity_dependencies(self, entity_id, entity_name):
        """检查实体的依赖关系"""
        for element_key, element in self.object_parent.items():
            if element_key == self.current_element_name:
                continue

            # 检查属性依赖
            for attribute in element.get("attributes", []):
                if self.parent.is_related_data(attribute):
                    attribute_values = attribute.get("referenced_entities", [])
                    if not isinstance(attribute_values, list):
                        attribute_values = [attribute_values] if attribute_values is not None else []

                    if entity_id in attribute_values:
                        CustomWarningDialog(
                            "删除失败",
                            f"该实体被属性 '{attribute.get('attribute_name', '未知属性')}' 使用，请先解除关联。"
                        ).exec_()
                        return True

            # 检查行为依赖
            for behavior in element.get("behaviors", []):
                related_objects = behavior.get("object_entities", [])
                if not isinstance(related_objects, list):
                    related_objects = [related_objects] if related_objects is not None else []

                if entity_id in related_objects:
                    CustomWarningDialog(
                        "删除失败",
                        f"该实体被行为 '{behavior.get('behavior_name', '未知行为')}' 使用，请先解除关联。"
                    ).exec_()
                    return True

        return False

    def _perform_entity_deletion(self, entity_id, entity_name):
        """执行实体删除操作"""
        if entity_id not in self.object_parent:
            return False

        # 从对象父级中删除实体
        self.object_parent.pop(entity_id)
        print(f"已删除实体 '{entity_name}' 从 object_parent")

        # 更新关联数据
        if self.type == "attribute":
            self._update_attribute_references(entity_id)
        elif self.type == "behavior":
            self._update_behavior_references(entity_id)

        return True

    def _update_attribute_references(self, entity_id):
        """更新属性引用"""
        for attribute in self.object_parent[self.current_element_name]["attributes"]:
            if attribute["attribute_code_name"] == self.current_name:
                # 确保 attribute_value 是列表
                if not isinstance(attribute["attribute_value"], list):
                    attribute["attribute_value"] = [attribute["attribute_value"]] if attribute[
                                                                                         "attribute_value"] is not None else []

                # 更新 attribute_value
                if entity_id in attribute["attribute_value"]:
                    attribute["attribute_value"].remove(entity_id)

                # 同时更新 referenced_entities
                if "referenced_entities" in attribute:
                    if not isinstance(attribute["referenced_entities"], list):
                        attribute["referenced_entities"] = [attribute["referenced_entities"]] if attribute[
                                                                                                     "referenced_entities"] is not None else []
                    if entity_id in attribute["referenced_entities"]:
                        attribute["referenced_entities"].remove(entity_id)
                break

    def _update_behavior_references(self, entity_id):
        """更新行为引用"""
        for behavior in self.object_parent[self.current_element_name]["behaviors"]:
            if behavior["behavior_code_name"] == self.current_name:
                if not isinstance(behavior["object_entities"], list):
                    behavior["object_entities"] = [behavior["object_entities"]] if behavior[
                                                                                       "object_entities"] is not None else []

                if entity_id in behavior["object_entities"]:
                    behavior["object_entities"].remove(entity_id)
                break

    def on_checkbox_state_changed(self, entity_id, state):
        """
        处理复选框状态变化

        Args:
            entity_id: 实体ID
            state: 复选框状态 (Qt.Checked=2, Qt.Unchecked=0)
        """
        newest_selection = None
        try:
            # 记录更改前的状态
            self.has_changes = True
            previous_selection = set(self.selected_entities)
            print(f"更改前的选择: {previous_selection}")

            # 更新选中状态
            if state == 2:  # Checked
                self.selected_entities.add(entity_id)
            else:  # Unchecked
                self.selected_entities.discard(entity_id)

            # 如果不是调试模式，执行验证
            if not self.debug:
                validation_error = None

                # 检查是否违反单选限制
                if not self.is_multi_valued and len(self.selected_entities) > 1:
                    validation_error = "该属性不支持多选，请只选择一个实体。"
                    # 保持最新选择的实体
                    self.selected_entities = {entity_id} if state == 2 else set()
                    print(f"最新选择: {self.selected_entities}")
                    newest_selection = self.selected_entities
                    self.update_element()

                # 检查必选项限制
                elif self.is_required and not self.selected_entities and previous_selection:
                    validation_error = "该属性为必选项，请至少选择一个实体。"
                    self.selected_entities = previous_selection

                # 如果有验证错误，显示警告并恢复状态
                if validation_error:
                    CustomWarningDialog("选择错误", validation_error).exec_()
                    self.restore_checkbox_states()
                    return

            # 更新关联数据
            if newest_selection:
                print(f"最新选341择: {newest_selection}")
                self.selected_entities = newest_selection
            self.update_element()

        except Exception as e:
            print(f"Error in on_checkbox_state_changed: {e}")
            # 发生错误时恢复到之前的状态
            self.selected_entities = previous_selection
            self.restore_checkbox_states()

    def restore_checkbox_states(self):
        """恢复复选框状态以匹配 selected_entities"""
        try:
            for row in range(self.resource_table.rowCount()):
                entity_id = int(self.resource_table.item(row, 0).text())
                checkbox_widget = self.resource_table.cellWidget(row, 1)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(entity_id in self.selected_entities)
                        checkbox.blockSignals(False)
        except Exception as e:
            print(f"Error in restore_checkbox_states: {e}")

    def update_element(self):
        print(f"更新 {self.current_element_name} 的 {self.current_name} 属性/行为")
        print(f"当前选择的实体: {self.selected_entities}")
        if self.type == "attribute":
            # Find the current attribute being edited
            current_attribute = None
            for attribute in self.object_parent[self.current_element_name]["attributes"]:
                if attribute["attribute_code_name"] == self.current_name:
                    current_attribute = attribute
                    entity_type_id = self.target_type_id
                    attribute["attribute_value"] = list(self.selected_entities)
                    attribute["referenced_entities"] = list(self.selected_entities)
                    print(f"wqe{entity_type_id},{attribute['attribute_value'], attribute['referenced_entities']}")
                    break

            if not current_attribute:
                return

            # Update parent while checking both entity_type_id AND attribute_code_name
            for item in self.parent.element_data.keys():
                print(f"当前的item:{item}")
                print(f"当前的entity_type_id:{self.parent.element_data[item]['entity_type_id']}")
                print(f"当前的attribute_value:{current_attribute['attribute_value']}")

                is_matching_type = self.parent.element_data[item]["entity_type_id"] == entity_type_id
                is_selected = item in current_attribute["attribute_value"]
                is_referenced = item in current_attribute["referenced_entities"]

                if is_matching_type:
                    if current_attribute['attribute_type_code'] == "Item":
                        if is_selected:
                            # Only update if this item is selected for the current attribute
                            self.parent.element_data[item]["entity_parent_id"] = self.current_element_name
                            print(
                                f"234对应的item:{item},执行更新,当前的attribute_value:{current_attribute['attribute_value']},{self.parent.element_data[item]['entity_parent_id']}")
                        elif not is_referenced:
                            # Only clear parent if this item is not referenced by the current attribute
                            self.parent.element_data[item]["entity_parent_id"] = None
                            print(
                                f"444对应的item:{item},执行更新,当前的attribute_value:{current_attribute['attribute_value']},{self.parent.element_data[item]['entity_parent_id']}")

        else:
            for behavior in self.object_parent[self.current_element_name]["behaviors"]:
                if behavior["behavior_code_name"] == self.current_name:
                    behavior["object_entities"] = list(self.selected_entities)
                    break


class CustomSelectionDialog(QDialog):
    accepted_option = Signal(str)

    def __init__(self, title, message, options, parent=None):
        """
        初始化自定义选择对话框。

        :param title: 对话框标题。
        :param message: 提示信息文本。
        :param options: 可供选择的选项列表（字符串列表）。
        :param parent: 父窗口（可选）。
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 150)
        self.setStyleSheet("""
        background: white;
        color: black;

        QLineEdit, QComboBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #0078d7; /* 蓝色边框 */
        }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 消息标签
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 下拉选择框，添加选项
        self.combo_box = QComboBox(self)
        self.combo_box.addItems(options)
        layout.addWidget(self.combo_box)

        # 按钮布局
        button_layout = QHBoxLayout()

        ok_button = QPushButton(self.tr("确认"))
        ok_button.clicked.connect(self._accept_selection)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton(self.tr("取消"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        # 设置固定的按钮宽度
        for i in range(button_layout.count()):
            button_layout.itemAt(i).widget().setFixedWidth(110)

    def _accept_selection(self):
        """
        当用户点击确认按钮时，记录当前选中的选项，
        通过信号发送该选项并关闭对话框。
        """
        selected = self.combo_box.currentText()
        self.accepted_option.emit(selected)
        self.accept()

    def get_selected_option(self):
        """
        返回当前选中的选项字符串。
        """
        return self.combo_box.currentText()

class ElementSettingTab(QWidget):
    """情景要素设置标签页"""

    save_requested = Signal()
    # 定义一个信号，传递 SQL 查询字符串
    request_sql_query = Signal(str)
    # 接收查询结果的信号
    receive_sql_result = Signal(list)
    save_to_database_signal= Signal(list)
    generate_model_show = Signal()
    refresh_scenario_data = Signal(int)

    def __init__(self):
        super().__init__()


        self.current_selected_element = None
        self.current_selected_entity = None
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
                name_item = QTableWidgetItem(behavior.get("china_default_name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 0, name_item)

                # 处理行为主体名称
                subject_name = self.element_data[self.current_selected_entity].get("entity_name", "")
                subject_item = QTableWidgetItem(subject_name)
                subject_item.setTextAlignment(Qt.AlignCenter)
                self.behavior_table.setItem(row_idx, 1, subject_item)

                # 处理行为对象名称
                object_ids = behavior.get("object_entities", [])
                if isinstance(object_ids, list):
                    object_names = self.show_object_value(behavior, "behavior")

                    object_text = ", ".join([str(name) for name in object_names])

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
        print(f"[DEBUG] 123123当前选中的要素：{self.current_selected_entity}")
        if attributes:
            self.attribute_placeholder.hide()
            self.attribute_content_widget.show()

            row = 0
            column = 0
            for attr in attributes:
                # 检查 self.element 的值，决定是否显示该属性
                if self.should_hide_attribute(attr):
                    continue

                attr_name = attr.get("china_default_name", "")
                attr_value = self.show_object_value(attr, "attribute")
                print(f"{attr_name}_{attr_value}")
                if attr.get("attribute_type_code") == "Bool":
                    print(f"2231{attr_value}")
                    attr_value = "是" if str(attr_value).lower() in ["true","1"] else "否"
                attr_type = attr.get("attribute_type", "")

                attr_widget = ClickableAttributeWidget(attr_name, attr_value, attr_type)
                attr_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 组件大小策略
                attr_widget.clicked.connect(self.open_attribute_editor)

                self.attribute_content_layout.addWidget(attr_widget, row, column)
                column += 1

                # 每行显示两个组件，满两列后换行
                if column >= 2:
                    column = 0
                    row += 1

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
                        print(f"更新{attr}的{new_value}_{attr['attribute_value']}")
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

    def show_object_value(self, object_data, type_name):
        """
        显示对象值，处理属性和行为两种类型

        Args:
            object_data (dict): 包含对象数据的字典
            type_name (str): 对象类型，'attribute' 或 'behavior'

        Returns:
            list/str: 对于关联数据返回名称列表，对于普通属性返回值
        """
        try:
            # 属性类型处理
            if type_name == 'attribute':
                # 检查是否是关联数据
                if self.is_related_data(object_data):
                    related_data_id = []

                    # 如果有直接的属性值
                    if object_data.get('attribute_value'):
                        related_data_id = object_data['attribute_value']
                        if isinstance(related_data_id, int):
                            related_data_id = [related_data_id]
                    if object_data.get('referenced_entities'):
                        related_data_id = object_data['referenced_entities']
                        if isinstance(related_data_id, int):
                            related_data_id = [related_data_id]
                    else:
                        # 获取所有符合条件的关联元素
                        for entity_id, entity_data in self.element_data.items():
                            if (entity_data.get('entity_parent_id') == self.current_selected_entity
                                    and entity_data.get('entity_type_id') == object_data.get(
                                        'reference_target_type_id')):
                                related_data_id.append(entity_data['entity_id'])

                    # 如果没有找到关联数据，返回空列表
                    if not related_data_id:
                        return []

                    # 获取关联数据的名称
                    related_names = []
                    for id in related_data_id:
                        for entity_data in self.element_data.values():
                            if entity_data.get('entity_id') == id:
                                related_names.append(entity_data.get('entity_name', ''))

                    return related_names

                # 非关联数据直接返回属性值
                return object_data.get('attribute_value', '')

            # 行为类型处理
            elif type_name == 'behavior':
                related_objects = object_data.get('object_entities', [])
                if not related_objects:
                    return []

                # 获取相关对象的名称
                related_names = []
                for obj_id in related_objects:
                    for entity_data in self.element_data.values():
                        if entity_data.get('entity_id') == obj_id:
                            related_names.append(entity_data.get('entity_name', ''))

                return related_names

            return []

        except Exception as e:
            print(f"Error in show_object_value: {e}")
            return []

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
            try:
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
            except ValueError as e:
                print(f"创建对话框失败: {e}")
                return

        if type == "behavior":
            print(f"编辑行为模型{object['behavior_name']}")

            try:
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
            except ValueError as e:
                print(f"创建对话框失败: {e}")
                return


    def update_current_element_data(self):
        """更新当前选中要素的数据到属性和行为模型显示，并确保类别信息存在。"""

        if self.current_selected_entity:
            print(self.current_selected_entity)
            element = self.element_data[self.current_selected_entity]
            print(f"更新要素{self.current_selected_element}的数据")
            print(f"要素数据{json.dumps(element, ensure_ascii=False, indent=2)}")
            # 处理属性模型
            self.current_attributes = element.get("attributes", [])
            print(f"属性模型数据{self.current_attributes}")
            # TO DO 解析模板显示规则


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

    def create_entities_with_negative_ids(self, template_name: str, name: str) -> Dict[int, Any]:
        """
        1. 根据 template_name 查找 Template;
        2. 为每个 Template 构造一个“复制品” JSON 对象(负数ID)，结构与 get_scenario_data 输出保持一致：
           {
             entity_id, entity_name, entity_type_id, ...
             categories: [...],
             attributes: [...],
             behaviors: [...]
           }
           其中 attributes/behaviors 字段，与 get_scenario_data 中的 attribute_value / behavior_value 保持同样的键。
        3. 返回形如: { -1: { ... entityJson ... }, -2: { ... }, ... }
        """
        session: Session = self.session
        neg_id_gen = self.neg_id_gen

        # 先查数据库 Template
        tpl_list: List[Template] = session.query(Template).filter(Template.template_name == template_name).all()
        if not tpl_list:
            print(f"[WARN] 未找到名为 {template_name} 的 template，返回空字典。")
            return {}

        # 用于返回的结果
        replicated_data: Dict[int, Any] = {}

        for tpl in tpl_list:
            # 解析 template_restrict
            if isinstance(tpl.template_restrict, dict):
                restrict_dict = tpl.template_restrict
            else:
                restrict_dict = json.loads(tpl.template_restrict)

            # 取 create 下的 category_type
            create_part = restrict_dict.get("create", {})
            cat_names = create_part.get("category_type", [])
            if isinstance(cat_names, str):
                cat_names = [cat_names]

            # 准备 entity 负数ID
            e_id = neg_id_gen.next_id()

            # entity 的基础字段：与 get_scenario_data 对应
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entity_json = {
                "entity_id": e_id,
                "entity_name": name,
                "entity_type_id": tpl.entity_type_id,
                "entity_parent_id": None,
                "scenario_id": self.scenario_data["scenario_id"],  # 你上下文里的场景ID
                "create_time": now_str,
                "update_time": now_str,
                "categories": [],
                "attributes": [],
                "behaviors": []
            }

            # ========== 处理 Categories ==========

            for cname in cat_names:
                cat_obj = session.query(Category).filter_by(category_name=cname).first()
                if cat_obj:
                    entity_json["categories"].append({
                        "category_id": cat_obj.category_id,
                        "category_name": cat_obj.category_name,
                        "description": cat_obj.description
                    })
                else:
                    # 如果数据库不存在该分类，可先用一个占位
                    entity_json["categories"].append({
                        "category_id": 0,
                        "category_name": cname,
                        "description": None
                    })

            # ========== 处理 Attributes ==========
            # template <-> attribute_definitions 多对多
            # 这里产生类似 get_scenario_data 中 attribute_values 的结构
            for attr_def in tpl.attribute_definitions:
                # 给 attribute_value_id 也分配一个负数ID
                av_id = neg_id_gen.next_id()

                # 当我们在 get_scenario_data 中：
                # final_attr_name = av.attribute_name or attr_def.attribute_code.attribute_code_name
                # 这里没有 av.attribute_name(因为是新建), 你可以将其设为 None 或直接用 code_name
                fallback_attr_name = attr_def.attribute_code.attribute_code_name

                attribute_item = {
                    "attribute_value_id": av_id,
                    "attribute_definition_id": attr_def.attribute_definition_id,
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

                    # 我们要类似 get_scenario_data 里: av.attribute_value
                    # 目前还没存任何值 => 可以先初始化为 default_value or None
                    "attribute_value": attr_def.default_value if attr_def.default_value is not None else None,

                    # attribute_name => 在 get_scenario_data 里是 av.attribute_name or code
                    # 这里没有 av.attribute_name, 我们就设为空或直接用 fallback
                    "attribute_name": fallback_attr_name,

                    # referenced_entities => []
                    "referenced_entities": []
                }
                # 如果是人类承灾要素，需要修改属性值
                if template_name == "人类承灾要素":
                    if attribute_item['attribute_code_name'] == 'CasualtyCondition':
                        attribute_item['attribute_value'] = '1'
                entity_json["attributes"].append(attribute_item)

            # ========== 处理 Behaviors ==========
            # template <-> behavior_definitions 多对多
            for bh_def in tpl.behavior_definitions:
                # behavior_value_id => 负数
                bv_id = neg_id_gen.next_id()

                # get_scenario_data 中：
                # final_behavior_name = bv.behavior_name or fallback_code_name
                # 这里“bv.behavior_name”尚不存在(新建), 所以我们可以先赋值 None
                # fallback_code_name = bh_def.behavior_code_ref.behavior_code_name (若 behavior_code_ref 存在)
                code_ref = bh_def.behavior_code_ref
                fallback_code_name = code_ref.behavior_code_name if code_ref else "UnknownBehaviorCode"

                # 你也可以先令 final_behavior_name = None => 让后面回写
                # 或者默认就用 bh_def.china_default_name
                final_behavior_name = None
                print(bh_def.object_entity_type_id)

                behavior_item = {
                    "behavior_value_id": bv_id,
                    "behavior_definition_id": bh_def.behavior_definition_id,

                    "china_default_name": bh_def.china_default_name,
                    "english_default_name": bh_def.english_default_name,

                    "behavior_name": final_behavior_name,  # 先置空; 若需要可用 bh_def.china_default_name
                    "behavior_code_name": fallback_code_name,  # 供 fallback

                    "object_entity_type_id": bh_def.object_entity_type_id,
                    "is_required": bool(bh_def.is_required),
                    "is_multi_valued": bool(bh_def.is_multi_valued),
                    "description": bh_def.description,
                    "create_time": now_str,
                    "update_time": now_str,

                    # object_entities => []
                    "object_entities": []
                }
                entity_json["behaviors"].append(behavior_item)

            # 把本次生成的“复制品”放进返回 dict
            replicated_data[e_id] = entity_json

        return replicated_data

    def load_template_mapping(self):
        """
        加载所有模板并创建一个 (entity_type_id, category_id) -> template_name 的映射。
        """
        try:
            query = "SELECT entity_type_id, category_id, template_name FROM template"
            results = self.get_result_by_sql(query)
            template_mapping = {}
            for row in results:
                entity_type_id, category_id, template_name = row
                template_mapping[(entity_type_id, category_id)] = template_name
            return template_mapping
        except Exception as e:
            print(f"加载模板映射时发生错误: {e}")
            return {}

    def handle_save(self):
        """处理保存按钮点击事件，仅展示保存的数据。"""
        try:
            # 深拷贝要素数据
            data = copy.deepcopy(self.element_data)
            flag = False
            for entity_id, checkbox in self.checkboxes.items():
                if not checkbox.checkbox.isChecked():
                    data.pop(entity_id, None)
                else:
                    flag = True

            if not flag:
                CustomInformationDialog(
                    self.tr("保存结果"),
                    self.tr("没有要保存的要素。"),
                    parent=self
                ).exec()
                return

            # 将筛选后的数据转换为列表
            saved_elements = list(data.values())
            # 检查是否包含了所有8类要素
            with open("check.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(saved_elements, ensure_ascii=False, indent=2))
            with open('check.json', 'r', encoding='utf-8') as f:
                check = json.load(f)
            template = []
            for i in check:
                id = i['entity_type_id']
                categories = i['categories']
                categories_id = [item['category_id'] for item in categories]
                temp = {'id': id, 'categories': categories_id}
                template.append(temp)
            for i in template:
                if len(i['categories']) > 1:
                    for j in i['categories']:
                        temp = {'id': i['id'], 'categories': [j]}
                        template.append(temp)
                    template.remove(i)
            for i in template:
                i['categories'] = i['categories'][0]
            print(f"TemplateInfo: {template}")
            has_template = []
            for item in template:
                result = self.get_result_by_sql(
                    f"SELECT template_name FROM template WHERE entity_type_id = {item['id']} AND category_id = {item['categories']};")
                if result and len(result) > 0:
                    has_template.append(result[0][0])
                else:
                    print(
                        f"Warning: No template found for entity_type_id={item['id']} and category_id={item['categories']}")
                    # 可以选择跳过或使用默认值
                    continue
            print(f"has_template: {has_template}")
            # 规定的8类要素
            # 1. 必须有的要素
            required_must_have = ['道路环境要素', '气象环境要素', '车辆致灾要素']
            # 2. 至少有一个的要素（承灾要素）
            group2_options = ['人类承灾要素', '车辆承灾要素', '道路承灾要素']
            # 3. 可有可无的要素（无需验证）：['应急资源要素', '应急行为要素']            # 缺失的要素
            missing_elements = []
            # 检查必须有的要素
            for element in required_must_have:
                if element not in has_template:
                    missing_elements.append(element)
            # 检查承灾要素：只需有其中一个
            if not any(elem in has_template for elem in group2_options):
                # 改为选择对话框，让用户从预设选项中选择一个承灾要素
                selection_dialog = CustomSelectionDialog(
                    self.tr("缺失承灾要素"),
                    self.tr("请选择补充要素的类别："),
                    options=group2_options,
                    parent=self
                )
                selection_dialog.exec()
                chosen_element = selection_dialog.get_selected_option()
                if not chosen_element:
                    CustomWarningDialog(
                        self.tr("保存失败"),
                        self.tr("未选择任何承灾要素类别，保存失败。"),
                        parent=self
                    ).exec()
                    return
                missing_elements.append(chosen_element)

            print(f"Missing required elements: {missing_elements}")

            # 对缺失的要素逐个提示用户补充
            for element in missing_elements:
                ask_name = CustomInputDialog(
                    self.tr(f"缺失 {element}，尝试从模板补充"),
                    self.tr("请输入补充要素的名称"),
                    parent=self
                )
                ask_name.exec()
                if not ask_name.get_input():
                    # 保存失败
                    CustomWarningDialog(
                        self.tr("保存失败"),
                        self.tr(f"缺少 {element}，保存失败。"),
                        parent=self
                    ).exec()
                    return
                entity = self.create_entities_with_negative_ids(element, ask_name.get_input())
                print(f"新建的实体：{entity}")
                for entity_id, entity_obj in entity.items():
                    saved_elements.append(entity_obj)
                    self.element_data[entity_id] = entity_obj
                # 如果没有输入名字，直接退出


            print(f"Data to be saved: {json.dumps(data, ensure_ascii=False, indent=2)}")

            # 加载模板映射
            template_mapping = self.load_template_mapping()

            # # 检测 is_required 属性是否为空
            # for item in saved_elements:
            #     # 使用 entity_name 代替 element_name
            #     element_name = item.get('entity_name', '未知要素')
            #     for attr in item.get('attributes', []):
            #         if attr.get('is_required', False) and not attr.get('attribute_value'):
            #             CustomWarningDialog(
            #                 self.tr("保存失败"),
            #                 self.tr(f"{element_name} 的属性 {attr.get('attribute_name', '未知属性')} 不能为空。"),
            #                 parent=self
            #             ).exec()
            #             return
            #     for behavior in item.get('behaviors', []):
            #         if behavior.get('is_required', False) and not behavior.get('object_entities'):
            #             CustomWarningDialog(
            #                 self.tr("保存失败"),
            #                 self.tr(
            #                     f"{element_name} 的行为 {behavior.get('behavior_code_name', '未知行为')} 不能为空。"),
            #                 parent=self
            #             ).exec()
            #             return

            # 生成 show_saved_elements
            show_saved_elements = []
            for item in saved_elements:
                entity_type_id = item.get('entity_type_id')
                categories = item.get('categories', [])
                for category in categories:
                    category_id = category.get('category_id')
                    template = template_mapping.get((entity_type_id, category_id))
                    if template and template in self.show_element:
                        show_saved_elements.append(item)
                        break  # 如果至少有一个模板匹配，则包含该要素

            print(f"Saving categories: {json.dumps(show_saved_elements, ensure_ascii=False, indent=2)}")
            # 保存到 result.json
            with open("result.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(saved_elements, ensure_ascii=False, indent=2))
                print(f"保存成功，保存路径为{os.path.abspath('result.json')}")

            # 生成详细信息的 HTML 内容
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
            entity_name = item.get('entity_name', '未知要素')
            detailed_info += f"<h3>{self.tr('元素')}: {entity_name}</h3>"

            detailed_info += """
            <b>""" + self.tr("属性") + """:</b>
            <table>
                <tr>
                    <th>""" + self.tr("属性名称") + """</th>
                    <th>""" + self.tr("属性值") + """</th>
                    <th>""" + self.tr("属性类别") + """</th>
                </tr>
            """
            for attr in item.get('attributes', []):
                attribute_type_code = attr.get('attribute_type_code', '未知类别')
                attribute_value = str(self.show_object_value(attr, "attribute")).strip("[]").replace("'", "")
                attribute_value_display = attribute_value if attribute_value else self.tr("无")
                detailed_info += f"""
                <tr>
                    <td>{attr.get('attribute_name', '未知属性')}</td>
                    <td>{attribute_value_display}</td>
                    <td>{attribute_type_code}</td>
                </tr>
                """
            detailed_info += "</table>"

            detailed_info += "<b>" + self.tr("行为模型") + ":</b>"
            if item.get('behaviors'):
                detailed_info += """
                <table>
                    <tr>
                        <th>""" + self.tr("行为名称") + """</th>
                        <th>""" + self.tr("行为主体") + """</th>
                        <th>""" + self.tr("行为对象") + """</th>
                    </tr>
                """
                for behavior in item['behaviors']:
                    behavior_name = behavior.get('behavior_code_name', '未知行为')
                    behavior_subject = entity_name
                    behavior_object = str(self.show_object_value(behavior, "behavior")).strip("[]").replace("'", "")
                    behavior_object_display = behavior_object if behavior_object else self.tr("无")
                    detailed_info += f"""
                    <tr>
                        <td>{behavior_name}</td>
                        <td>{behavior_subject}</td>
                        <td>{behavior_object_display}</td>
                    </tr>
                    """
                detailed_info += "</table>"
            else:
                detailed_info += "<p class='no-behavior'>" + self.tr("无行为模型") + "</p>"

        detailed_info += "</body></html>"
        return detailed_info

    def handle_generate(self):
        """处理生成情景模型按钮点击事件"""


        # 询问是否保存进行的修改后再进行生成
        reply = CustomQuestionDialog(
            self.tr("保存并生成"),
            self.tr("是否保存当前修改后生成情景模型？"),
            parent=self
        ).ask()
        # 如果用户选择是，则保存并生成
        if reply:
            self.handle_save()


        self.refresh_scenario_data.emit(self.scenario_data['scenario_id'])

        # 将筛选后的数据转换为列表
        data = copy.deepcopy(self.element_data)
        saved_elements = list(data.values())

        # 保存中间检查结果到文件
        with open("check.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(saved_elements, ensure_ascii=False, indent=2))

        # 读取检查文件
        with open('check.json', 'r', encoding='utf-8') as f:
            check = json.load(f)

        # 提取模板信息
        template = []
        for i in check:
            id = i.get('entity_type_id')
            categories = i.get('categories', [])
            if not categories:  # 添加验证
                continue
            categories_id = [item.get('category_id') for item in categories if item.get('category_id')]
            if categories_id:  # 确保有有效的category_id
                temp = {'id': id, 'categories': categories_id}
                template.append(temp)

        # 处理多个categories的情况
        expanded_template = []
        for i in template:
            if len(i['categories']) > 1:
                for j in i['categories']:
                    expanded_template.append({'id': i['id'], 'categories': [j]})
            else:
                expanded_template.append(i)

        # 标准化categories格式
        template = []
        for i in expanded_template:
            if i['categories']:  # 添加验证
                template.append({'id': i['id'], 'categories': i['categories'][0]})

        print(f"TemplateInfo: {template}")

        # 获取模板名称
        has_template = []
        for item in template:
            try:
                query_result = self.get_result_by_sql(
                    f"SELECT template_name FROM template WHERE entity_type_id = {item['id']} AND category_id = {item['categories']};"
                )
                if query_result and query_result[0]:  # 添加验证
                    has_template.append(query_result[0][0])
            except Exception as e:
                print(f"获取模板名称时出错: {e}")
                continue

        print(f"has_template: {has_template}")

        # 1. 必须有的要素
        required_must_have = ['道路环境要素', '气象环境要素', '车辆致灾要素']
        # 2. 至少有一个的要素（承灾要素）
        group2_options = ['人类承灾要素', '车辆承灾要素', '道路承灾要素']
        # 3. 可有可无的要素（无需验证）：['应急资源要素', '应急行为要素']            # 缺失的要素
        missing_elements = []
        # 检查必须有的要素
        for element in required_must_have:
            if element not in has_template:
                missing_elements.append(element)
        # 检查承灾要素：只需有其中一个
        if not any(elem in has_template for elem in group2_options):
                missing_elements.append(group2_options)

        # 如果有缺失的要素，提示用户
        if missing_elements:
            CustomWarningDialog(
                self.tr("生成失败"),
                self.tr(f"缺少以下要素：{missing_elements}，请先补充并保存。"),
                parent=self
            ).exec()
            return

        print(f"开始生成情景级孪生模型{data}")

        for key, value in data.items():
            json_input_str = json.dumps(data[key], ensure_ascii=False)
            json_to_sysml2_txt(json_input_str,data)

        self.generate_model_show.emit()


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

    def should_hide_attribute(self, attr):
        if self.current_selected_element is None:
            return False
        if self.current_selected_element == "道路环境要素":  # 替换 "xxx" 为需要隐藏属性时的特定值
            # 根据条件判断是否隐藏此属性，例如：
            if attr.get("attribute_aspect_name") == 'Affected':
                return True
        elif self.current_selected_element == "道路承灾要素":
            if attr.get("attribute_aspect_name") == 'Environment':
                return True
        return False

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
