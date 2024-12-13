# model_generation_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QRadioButton, QButtonGroup, QMessageBox, QApplication,
    QStackedLayout, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QWheelEvent, QPainter, QIcon, QFont
from PySide6.QtSvg import QSvgRenderer
import os
import sys

from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog

# 常量定义
ZOOM_IN_ICON = "resources/icons/zoom_in.png"
ZOOM_OUT_ICON = "resources/icons/zoom_out.png"
SVG_FILES = {
    "整体": os.path.join(os.path.dirname(__file__), "temp.svg"),
    "突发事件本体": "emergency_event_ontology.svg",
    "情景本体": "scenario_ontology.svg",
    "情景要素本体": "scenario_element_ontology.svg"
}
CLASS_OPTIONS = {
    "整体": [
        "整体类1", "整体类2"
    ],
    "突发事件本体": [
        "突发事件类1", "突发事件类2", "突发事件类3"
    ],
    "情景本体": [
        "情景类1", "情景类2"
    ],
    "情景要素本体": [
        "情景要素类1", "情景要素类2", "情景要素类3", "情景要素类4"
    ]
}
ATTRIBUTE_SAMPLE_DATA = {
    "整体类1": [
        ("属性1", "范围1"),
        ("属性2", "范围2"),
    ],
    "突发事件类1": [
        ("属性A", "范围A"),
        ("属性B", "范围B"),
        ("属性C", "范围C"),
    ],
    # 添加其他类的属性数据
}
BEHAVIOR_SAMPLE_DATA = {
    "整体类1": [
        ("行为1", "范围X"),
        ("行为2", "范围Y"),
    ],
    "突发事件类1": [
        ("行为A", "范围A"),
        ("行为B", "范围B"),
    ],
    # 添加其他类的行为数据
}

class ZoomableLabel(QLabel):
    """支持缩放的标签，用于显示SVG图像"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.renderer = QSvgRenderer()
        self.scale_factor = 1.0
        self.image_loaded = False

    def set_svg(self, svg_path):
        """设置并加载SVG图像"""
        if not self.renderer.load(svg_path):
            self.setText("无法加载图像")
            self.image_loaded = False
            return
        self.scale_factor = 1.0
        self.image_loaded = True
        self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
        """实现Ctrl+滚轮缩放功能"""
        if self.image_loaded and event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))  # 限制缩放比例
            self.update_pixmap()
        else:
            super().wheelEvent(event)

    def update_pixmap(self):
        """根据缩放比例更新显示的图像"""
        if self.renderer.isValid() and self.image_loaded:
            size = self.renderer.defaultSize() * self.scale_factor
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            self.renderer.render(painter)
            painter.end()

            super().setPixmap(pixmap)

    def mousePressEvent(self, event):
        """处理鼠标点击事件，当未加载图像时提示用户"""
        if not self.image_loaded and event.button() == Qt.LeftButton:
            CustomWarningDialog("提示", "未选择本体，请选择本体").exec()
        else:
            super().mousePressEvent(event)


class ModelGenerationTab(QWidget):
    """模型生成选项卡"""
    generate_request = Signal()

    def __init__(self):
        super().__init__()
        self.current_ontology = None  # 当前选择的本体
        self.current_class = None  # 当前选择的类
        self.init_ui()

    def init_ui(self):
        """初始化UI组件和布局"""
        self.set_stylesheet()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 10)

        # 上部区域 - 本体选择
        main_layout.addWidget(self.create_ontology_group_box(), 3)  # 占据更多的空间

        # 下部区域 - 左侧类选择和生成按钮，右侧模型切换区域
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)

        # 左侧 - 类选择区域和生成按钮
        left_side_layout = QVBoxLayout()
        left_side_layout.setSpacing(10)

        # 类选择区域
        left_side_layout.addWidget(self.create_class_group_box())

        # 生成推演模型按钮
        self.generate_button = QPushButton("生成推演模型")
        self.generate_button.clicked.connect(self.handle_generate)
        # 占满左右空间
        self.generate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_side_layout.addWidget(self.generate_button)

        lower_layout.addLayout(left_side_layout, 1)

        # 右侧 - 模型切换区域（圆角长方形）
        right_side_layout = QVBoxLayout()
        right_side_layout.setSpacing(0)
        right_side_layout.setContentsMargins(0, 0, 0, 0)

        model_switch_container = QFrame()
        model_switch_container.setObjectName("ModelSwitchContainer")
        model_switch_container.setStyleSheet("""
            QFrame#ModelSwitchContainer {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #ffffff;
            }
        """)
        model_switch_layout = QVBoxLayout(model_switch_container)
        model_switch_layout.setContentsMargins(0, 0, 0, 10)
        model_switch_layout.setSpacing(10)

        # 模型切换按钮布局（水平排列）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)  # 紧靠边框
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.attribute_button = QPushButton("属性模型")
        self.attribute_button.setObjectName("AttributeButton")
        self.attribute_button.setCheckable(True)
        self.attribute_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.attribute_button.setStyleSheet("""
                    border-top-left-radius: 10px;
        """)
        self.attribute_button.clicked.connect(lambda: self.show_tab(0))

        self.behavior_button = QPushButton("行为模型")
        self.behavior_button.setObjectName("BehaviorButton")
        self.behavior_button.setCheckable(True)
        self.behavior_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.behavior_button.setStyleSheet("""
                    border-top-right-radius: 10px;
        """)
        self.behavior_button.clicked.connect(lambda: self.show_tab(1))

        self.tab_button_group = QButtonGroup(self)
        self.tab_button_group.setExclusive(True)
        self.tab_button_group.addButton(self.attribute_button)
        self.tab_button_group.addButton(self.behavior_button)

        button_layout.addWidget(self.attribute_button)
        button_layout.addWidget(self.behavior_button)

        model_switch_layout.addLayout(button_layout)

        # QStackedLayout 内容
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setSpacing(0)

        self.attribute_widget = self.create_attribute_widget()
        self.behavior_widget = self.create_behavior_widget()

        self.stacked_layout.addWidget(self.attribute_widget)
        self.stacked_layout.addWidget(self.behavior_widget)

        model_switch_layout.addLayout(self.stacked_layout)

        right_side_layout.addWidget(model_switch_container)

        lower_layout.addLayout(right_side_layout, 3)

        main_layout.addLayout(lower_layout, 1)

        self.setLayout(main_layout)

    def set_stylesheet(self):
        """设置整体样式表"""
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
    padding: 2px 10px;
    font-weight: bold;
    color: #333333;
    background-color: #E8E8E8; /* 设置圆角灰色背景 */
    border-radius: 10px; /* 圆角效果 */
    border-bottom-left-radius: 0px; /* 左下角无圆角 */
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
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #f1f1f1;
                width: 8px;
                height: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 20px;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            
            QLabel#placeholder{
    color: gray;
    font-size: 20pt;
    border-radius: 10px;
    border: 0px solid #c0c0c0;
}



            /* 圆角区域样式 */
            QFrame#ModelSwitchContainer {

            }

            /* 属性模型和行为模型按钮样式 */
            QPushButton#AttributeButton{
                border: #f0f0f0; /* 边框颜色 */
                border-right: 1px solid #f0f0f0; /* 右侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
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
                border-right:1px solid #f0f0f0; /* 右侧侧侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }
            QPushButton#BehaviorButton:hover{
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border-left:1px solid #f0f0f0; /* 左侧侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }

            QPushButton#AttributeButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border-right:1px solid #f0f0f0; /* 右侧侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }
            QPushButton#BehaviorButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border-left:1px solid #f0f0f0; /* 左侧侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }


            QPushButton#BehaviorButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border-left:1px solid #f0f0f0; /* 左侧侧边框 */
                border-right-radius: 10px; /* 右侧圆角边框 */
            }
            
            QPushButtonAttributeButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border-right:1px solid #f0f0f0; /* 右侧侧边框 */
                border-left-radius: 10px; /* 左侧圆角边框 */
            }

            /* 表格样式 */
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

    def create_ontology_group_box(self):
        """创建本体选择区域"""
        ontology_group_box = QGroupBox("本体模型")
        ontology_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
            }
        """)
        ontology_layout = QVBoxLayout()
        ontology_layout.setContentsMargins(15, 15, 15, 10)
        ontology_layout.setSpacing(10)

        # 下拉框和缩放按钮布局
        combo_zoom_layout = QHBoxLayout()
        combo_zoom_layout.setSpacing(5)
        combo_zoom_layout.setContentsMargins(0, 0, 0, 0)

        self.ontology_combo = QComboBox()
        self.ontology_combo.addItem("请选择本体")
        self.ontology_combo.addItems(list(SVG_FILES.keys()))
        self.ontology_combo.setCurrentIndex(0)
        self.ontology_combo.model().item(0).setEnabled(False)
        self.ontology_combo.currentIndexChanged.connect(self.handle_ontology_selection)

        # 缩放按钮
        self.zoom_in_button = self.create_zoom_button(ZOOM_IN_ICON, "放大图像(按住 Ctrl 并滚动鼠标滚轮)", self.zoom_in)
        self.zoom_out_button = self.create_zoom_button(ZOOM_OUT_ICON, "缩小图像(按住 Ctrl 并滚动鼠标滚轮)", self.zoom_out)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)

        combo_zoom_layout.addWidget(self.ontology_combo)
        combo_zoom_layout.addStretch()
        combo_zoom_layout.addWidget(self.zoom_in_button)
        combo_zoom_layout.addWidget(self.zoom_out_button)

        ontology_layout.addLayout(combo_zoom_layout)

        # 图像加载区域
        self.ontology_scroll_area = QScrollArea()
        self.ontology_scroll_area.setWidgetResizable(True)
        self.ontology_scroll_area.setStyleSheet("border: none;")

        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setSpacing(5)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.ontology_image_label = ZoomableLabel()
        self.ontology_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ontology_image_label.setText("图形加载区")
        image_layout.addWidget(self.ontology_image_label, 1)

        self.ontology_scroll_area.setWidget(image_container)
        ontology_layout.addWidget(self.ontology_scroll_area, 1)

        ontology_group_box.setLayout(ontology_layout)
        return ontology_group_box

    def create_zoom_button(self, icon_path, tooltip, callback):
        """创建缩放按钮"""
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            button.setText("缩放")
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(24, 24))
        button.clicked.connect(callback)
        return button

    def create_class_group_box(self):
        """创建类选择区域"""
        class_group_box = QGroupBox("类")
        class_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
            }
        """)

        class_scroll_area = QScrollArea()
        class_scroll_area.setWidgetResizable(True)
        class_scroll_area.setStyleSheet("border: none;")

        class_content = QWidget()
        class_layout = QGridLayout(class_content)
        class_layout.setContentsMargins(0, 0, 0, 0)
        class_layout.setSpacing(10)

        self.class_button_group = QButtonGroup(self)
        self.class_button_group.setExclusive(True)
        self.class_button_group.buttonClicked.connect(self.handle_class_selection)

        # 初始占位符
        self.class_placeholder_label = QLabel("请选择本体")
        self.class_placeholder_label.setObjectName("placeholder")
        self.class_placeholder_label.setAlignment(Qt.AlignCenter)

        class_layout.addWidget(self.class_placeholder_label, 0, 0, 1, 2)

        class_scroll_area.setWidget(class_content)

        class_layout_container = QVBoxLayout()
        class_layout_container.setContentsMargins(15, 15, 15, 10)
        class_layout_container.setSpacing(10)
        class_layout_container.addWidget(class_scroll_area)
        class_group_box.setLayout(class_layout_container)

        self.class_group_box = class_group_box  # 保存引用以便后续更新
        self.class_layout = class_layout  # 保存布局引用
        return class_group_box

    def create_attribute_widget(self):
        """创建属性模型表格"""
        attribute_widget = QWidget()
        attribute_layout = QVBoxLayout(attribute_widget)
        attribute_layout.setContentsMargins(0, 0, 0, 0)
        attribute_layout.setSpacing(5)

        self.attribute_table = QTableWidget()
        self.attribute_table.setColumnCount(2)
        self.attribute_table.setHorizontalHeaderLabels(["属性", "范围"])
        self.apply_table_style(self.attribute_table)
        self.attribute_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.attribute_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.attribute_table.horizontalHeader().setStretchLastSection(True)
        self.attribute_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attribute_table.verticalHeader().setVisible(False)
        self.attribute_table.setAlternatingRowColors(True)  # 使用交替行颜色区分

        self.attribute_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用默认编辑功能

        # 移除默认的网格线
        self.attribute_table.setShowGrid(False)

        # 设置属性表格的尺寸策略
        self.attribute_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 初始占位符
        self.attribute_placeholder_label = QLabel("请选择类")
        self.attribute_placeholder_label.setObjectName("placeholder")
        self.attribute_placeholder_label.setAlignment(Qt.AlignCenter)

        attribute_layout.addWidget(self.attribute_placeholder_label)
        attribute_layout.addWidget(self.attribute_table)
        self.attribute_table.hide()  # 初始隐藏表格

        return attribute_widget

    def create_behavior_widget(self):
        """创建行为模型表格"""
        behavior_widget = QWidget()
        behavior_layout = QVBoxLayout(behavior_widget)
        behavior_layout.setContentsMargins(0, 0, 0, 0)
        behavior_layout.setSpacing(5)

        self.behavior_table = QTableWidget()
        self.behavior_table.setColumnCount(2)
        self.behavior_table.setHorizontalHeaderLabels(["行为", "范围"])
        self.apply_table_style(self.behavior_table)

        self.behavior_table .horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.behavior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.behavior_table.horizontalHeader().setStretchLastSection(True)
        self.behavior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.behavior_table.verticalHeader().setVisible(False)
        self.behavior_table.setAlternatingRowColors(True)  # 使用交替行颜色区分

        self.behavior_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用默认编辑功能

        # 移除默认的网格线
        self.behavior_table.setShowGrid(False)

        # 设置属性表格的尺寸策略
        self.behavior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 初始占位符
        self.behavior_placeholder_label = QLabel("请选择类")
        self.behavior_placeholder_label.setObjectName("placeholder")
        self.behavior_placeholder_label.setAlignment(Qt.AlignCenter)

        behavior_layout.addWidget(self.behavior_placeholder_label)
        behavior_layout.addWidget(self.behavior_table)
        self.behavior_table.hide()  # 初始隐藏表格

        return behavior_widget

    def apply_table_style(self, table: QTableWidget):
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

    def populate_table(self, table: QTableWidget, data: list):
        """填充表格数据"""
        table.setRowCount(len(data))
        for row_idx, (attr, scope) in enumerate(data):
            table.setItem(row_idx, 0, QTableWidgetItem(attr))
            table.setItem(row_idx, 1, QTableWidgetItem(scope))

    def show_tab(self, index):
        """根据按钮索引显示相应的标签页"""
        self.stacked_layout.setCurrentIndex(index)
        if index == 0:
            self.attribute_button.setChecked(True)
            self.behavior_button.setChecked(False)
        elif index == 1:
            self.attribute_button.setChecked(False)
            self.behavior_button.setChecked(True)

    def zoom_in(self):
        """放大图像"""
        if self.ontology_image_label.image_loaded:
            self.ontology_image_label.scale_factor *= 1.1
            self.ontology_image_label.scale_factor = min(self.ontology_image_label.scale_factor, 10.0)
            self.ontology_image_label.update_pixmap()

    def zoom_out(self):
        """缩小图像"""
        if self.ontology_image_label.image_loaded:
            self.ontology_image_label.scale_factor /= 1.1
            self.ontology_image_label.scale_factor = max(self.ontology_image_label.scale_factor, 0.1)
            self.ontology_image_label.update_pixmap()

    def handle_generate(self):
        """处理生成模型的逻辑"""
        CustomInformationDialog("生成成功", "已成功生成推演模型。").exec()
        self.generate_request.emit()

    def handle_ontology_selection(self, index):
        """处理本体模型下拉框的选择"""
        if index == 0:
            self.reset_ontology_selection()
            return

        option = self.ontology_combo.currentText()
        self.current_ontology = option
        svg_filename = SVG_FILES.get(option, "")
        svg_path = os.path.join(os.getcwd(), svg_filename)

        if not os.path.exists(svg_path):
            self.ontology_image_label.setText("无法找到 SVG 文件")
            self.ontology_image_label.image_loaded = False
            self.toggle_zoom_buttons(False)
            CustomWarningDialog("提示", "无法找到对应的图形文件。").exec()
            self.reset_class_selection()
            self.reset_model_tabs_after_ontology()
            return
        else:
            self.ontology_image_label.set_svg(svg_path)
            self.ontology_image_label.image_loaded = True
            self.toggle_zoom_buttons(True)
            # 更新类选择区域
            self.update_class_selection()

            # 重置属性和行为模型区域为“请选择类”
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText("请选择类")
            self.attribute_placeholder_label.show()

            self.behavior_table.hide()
            self.behavior_placeholder_label.setText("请选择类")
            self.behavior_placeholder_label.show()

    def reset_ontology_selection(self):
        """重置本体选择相关的UI组件"""
        self.ontology_combo.setCurrentIndex(0)
        self.ontology_image_label.setText("图形加载区")
        self.ontology_image_label.setStyleSheet("""
            color: gray;
    font-size: 20pt;
    border-radius: 10px;
    border: 0px solid #c0c0c0;""")
        self.ontology_image_label.image_loaded = False
        self.toggle_zoom_buttons(False)
        self.reset_class_selection()
        self.reset_model_tabs_before_ontology()

    def toggle_zoom_buttons(self, enable: bool):
        """启用或禁用缩放按钮"""
        self.zoom_in_button.setEnabled(enable)
        self.zoom_out_button.setEnabled(enable)

    def create_class_button(self, text):
        """创建单个类的单选按钮"""
        radio_button = QRadioButton(text)
        self.class_button_group.addButton(radio_button)
        return radio_button

    def update_class_selection(self):
        """根据选择的本体更新类选择区域"""
        # 清除现有的布局内容
        for i in reversed(range(self.class_layout.count())):
            widget = self.class_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        if self.current_ontology in CLASS_OPTIONS:
            class_options = CLASS_OPTIONS[self.current_ontology]
            self.current_class = None  # 重置当前选择的类
            row, col = 0, 0
            for option in class_options:
                radio_button = self.create_class_button(option)
                self.class_layout.addWidget(radio_button, row, col)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
        else:
            # 如果没有定义该本体的类选项，则显示占位符
            placeholder = QLabel("未定义的本体类")
            placeholder.setObjectName("placeholder")
            placeholder.setAlignment(Qt.AlignCenter)
            self.class_layout.addWidget(placeholder, 0, 0, 1, 2)
            self.current_class = None

    def reset_class_selection(self):
        """重置类选择区域到初始状态"""
        # 清除现有的布局内容
        for i in reversed(range(self.class_layout.count())):
            widget = self.class_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # 添加占位符
        self.class_placeholder_label = QLabel("请选择本体")
        self.class_placeholder_label.setObjectName("placeholder")
        self.class_placeholder_label.setAlignment(Qt.AlignCenter)
        self.class_layout.addWidget(self.class_placeholder_label, 0, 0, 1, 2)
        self.current_class = None

    def handle_class_selection(self, button):
        """处理类选择的逻辑"""
        selected_class = button.text()
        self.current_class = selected_class
        self.update_model_tabs()

    def reset_model_tabs_before_ontology(self):
        """重置属性和行为模型区域到“请选择本体”"""
        # 属性模型
        self.attribute_table.hide()
        self.attribute_placeholder_label.setText("请选择本体")
        self.attribute_placeholder_label.show()

        # 行为模型
        self.behavior_table.hide()
        self.behavior_placeholder_label.setText("请选择本体")
        self.behavior_placeholder_label.show()

        # 禁用模型切换按钮
        self.toggle_model_tabs(False)

    def reset_model_tabs_after_ontology(self):
        """重置属性和行为模型区域到“请选择类”"""
        # 属性模型
        self.attribute_table.hide()
        self.attribute_placeholder_label.setText("请选择类")
        self.attribute_placeholder_label.show()

        # 行为模型
        self.behavior_table.hide()
        self.behavior_placeholder_label.setText("请选择类")
        self.behavior_placeholder_label.show()

    def update_model_tabs(self):
        """根据选择的类更新属性和行为模型区域"""
        if not self.current_class:
            self.reset_model_tabs_after_ontology()
            return

        # 启用模型切换按钮
        self.toggle_model_tabs(True)

        # 更新属性模型
        attributes = ATTRIBUTE_SAMPLE_DATA.get(self.current_class, [])
        if attributes:
            self.attribute_placeholder_label.hide()
            self.attribute_table.show()
            self.populate_table(self.attribute_table, attributes)
        else:
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText("无属性数据")
            self.attribute_placeholder_label.show()

        # 更新行为模型
        behaviors = BEHAVIOR_SAMPLE_DATA.get(self.current_class, [])
        if behaviors:
            self.behavior_placeholder_label.hide()
            self.behavior_table.show()
            self.populate_table(self.behavior_table, behaviors)
        else:
            self.behavior_table.hide()
            self.behavior_placeholder_label.setText("无行为数据")
            self.behavior_placeholder_label.show()

    def toggle_model_tabs(self, enable: bool):
        """启用或禁用属性和行为模型区域"""
        if enable:
            # 启用模型切换按钮
            self.attribute_button.setEnabled(True)
            self.behavior_button.setEnabled(True)
        else:
            # 禁用模型切换按钮并切换到默认页面
            self.attribute_button.setEnabled(False)
            self.behavior_button.setEnabled(False)
            self.stacked_layout.setCurrentWidget(self.attribute_widget)
            self.attribute_button.setChecked(True)
            self.behavior_button.setChecked(False)

    def handle_save(self):
        """收集所有被勾选的要素数据并模拟保存操作"""
        # 假设保存逻辑类似于 element_setting.py，此处仅展示提示
        CustomInformationDialog("保存成功", "已成功保存要素数据。").exec()
        # 如果需要，可以在这里添加实际的保存逻辑
        # self.save_requested.emit()

    def reset_inputs(self):
        """重置所有输入"""
        self.reset_ontology_selection()
        self.generate_button.setChecked(False)
        self.attribute_button.setChecked(True)
        self.behavior_button.setChecked(False)
        self.stacked_layout.setCurrentWidget(self.attribute_widget)

    def load_models_data(self, category):
        """根据选择的类别加载属性和行为数据"""
        print(f"Loading data for category: {category}")  # 调试信息

        # 模拟加载数据
        attributes = ATTRIBUTE_SAMPLE_DATA.get(category, [])
        behaviors = BEHAVIOR_SAMPLE_DATA.get(category, [])

        # 更新属性模型
        if attributes:
            self.attribute_placeholder_label.hide()
            self.attribute_table.show()
            self.populate_table(self.attribute_table, attributes)
        else:
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText("无属性数据")
            self.attribute_placeholder_label.show()

        # 更新行为模型
        if behaviors:
            self.behavior_placeholder_label.hide()
            self.behavior_table.show()
            self.populate_table(self.behavior_table, behaviors)
        else:
            self.behavior_table.hide()
            self.behavior_placeholder_label.setText("无行为数据")
            self.behavior_placeholder_label.show()

