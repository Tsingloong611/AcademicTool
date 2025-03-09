# model_generation_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QMessageBox, QApplication,
    QStackedLayout, QGridLayout, QFrame, QListWidget, QListWidgetItem, QButtonGroup, QSpacerItem
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QWheelEvent, QPainter, QIcon, QFont
from PySide6.QtSvg import QSvgRenderer
import os
import sys

from utils.get_config import get_cfg
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog

# Constants Definition
ZOOM_IN_ICON = "resources/icons/zoom_in.png"
ZOOM_OUT_ICON = "resources/icons/zoom_out.png"


class ZoomableLabel(QLabel):
    """Label supporting zoom functionality for displaying SVG images."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.renderer = QSvgRenderer()
        self.scale_factor = 1.0
        self.image_loaded = False

    def set_svg(self, svg_path):
        """Set and load the SVG image."""
        if not self.renderer.load(svg_path):
            self.setText(self.tr("无法加载图像"))
            self.image_loaded = False
            return
        self.scale_factor = 1.0
        self.image_loaded = True
        self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
        """Implement zoom with Ctrl + mouse wheel."""
        if self.image_loaded and event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))  # Limit zoom factor
            self.update_pixmap()
        else:
            super().wheelEvent(event)

    def update_pixmap(self):
        """Update the displayed image based on the zoom factor."""
        if self.renderer.isValid() and self.image_loaded:
            size = self.renderer.defaultSize() * self.scale_factor
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            self.renderer.render(painter)
            painter.end()

            super().setPixmap(pixmap)

    def mousePressEvent(self, event):
        """Handle mouse click events to prompt user if image not loaded."""
        if not self.image_loaded and event.button() == Qt.LeftButton:
            pass
        else:
            super().mousePressEvent(event)


class ModelGenerationTab(QWidget):
    """Model Generation Tab"""
    generate_request = Signal()
    SVG_FILES = {
        "整体": os.path.join(os.path.dirname(__file__), "temp.svg"),
        "突发事件本体": "emergency_event_ontology.svg",
        "情景本体": "scenario_ontology.svg",
        "情景要素本体": "scenario_element_ontology.svg"
    }
    CLASS_OPTIONS = {
        "整体": [
            "class1", "class2", "class3", "class4"
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
        "class1": [
            ("属性1", "范围1"),
            ("属性2", "范围2"),
        ],
        "class2": [
            ("属性A", "范围A"),
            ("属性B", "范围B"),
            ("属性C", "范围C"),
        ],
        # Add other class attribute data
    }
    BEHAVIOR_SAMPLE_DATA = {
        "class1": [
            ("行为1", "范围X"),
            ("行为2", "范围Y"),
        ],
        "class2": [
            ("行为A", "范围A"),
            ("行为B", "范围B"),
        ],
        # Add other class behavior data
    }

    def __init__(self):
        super().__init__()
        self.current_ontology = None  # Currently selected ontology
        self.current_class = None      # Currently selected class
        self.init_ui()


    def init_ui(self):
        """Initialize UI components and layout."""
        self.set_stylesheet()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)

        # 中部布局 - 本体选择区域
        ontology_group_box = self.create_ontology_group_box()
        main_layout.addWidget(ontology_group_box, stretch=3)

        # 底部布局 - 左右两侧
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)
        lower_layout.setContentsMargins(0, 10, 0, 0)

        # 左侧布局 - 类选择区域
        left_side_layout = QVBoxLayout()
        left_side_layout.setSpacing(10)

        # 类选择区域
        class_group_box = self.create_class_group_box()
        left_side_layout.addWidget(class_group_box, stretch=10)

        lower_layout.addLayout(left_side_layout, 2)

        # 右侧布局 - 模型切换区域（圆角矩形）
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
        model_switch_layout.setSpacing(0)

        # 模型切换按钮布局（水平）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)  # 紧贴边框
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.attribute_button = QPushButton(self.tr("属性模型"))
        self.attribute_button.setObjectName("AttributeButton")
        self.attribute_button.setCheckable(True)
        self.attribute_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.attribute_button.setStyleSheet("""
                    border-top-left-radius: 10px;
        """)
        self.attribute_button.clicked.connect(lambda: self.show_tab(0))

        self.behavior_button = QPushButton(self.tr("行为模型"))
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

        lower_layout.addLayout(right_side_layout, 5)

        main_layout.addLayout(lower_layout, 1)

        self.setLayout(main_layout)

    def set_stylesheet(self):
        """Set the overall stylesheet."""
        self.setStyleSheet(f"""
QGroupBox {{
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    background-color: #ffffff;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    font-weight: bold;
    color: #333333;
    background-color: #E8E8E8; /* Rounded gray background */
    border-radius: 10px; /* Rounded corners */
    border-bottom-left-radius: 0px; /* No bottom-left radius */
}}
QLabel {{
    color: #333333;
}}
QCheckBox {{
    color: #333333;
}}
            QAbstractScrollArea::corner {{
                background: transparent;  /* 或者改成 #ffffff，与主背景相同 */
                border: none;
            }}
QLineEdit {{
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px;
    background-color: white;
}}
QScrollBar:vertical, QScrollBar:horizontal {{
    border: none;
    background: #f1f1f1;
    width: 8px;
    height: 8px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #c1c1c1;
    min-width: 20px;
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0px;
    width: 0px;
    subcontrol-origin: margin;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QLabel#placeholder{{
    color: gray;
    font-size: 20pt;
    border-radius: 10px;
    border: 0px solid #c0c0c0;
}}

/* Rounded area styles */
QFrame#ModelSwitchContainer {{

}}

/* Attribute and Behavior Model buttons styles */
QPushButton#AttributeButton{{
    border: #f0f0f0; /* Border color */
    border-right: 1px solid #f0f0f0; /* Right border */
    border-left-radius: 10px; /* Left rounded border */
    background-color: transparent; /* Transparent background */
    padding:10px 0;
    font-size: 16px; /* Text size */
    font-weight: bold; /* Bold text */
}}
QPushButton#BehaviorButton{{
    border: #f0f0f0; /* Border color */
    border-left:1px solid #f0f0f0; /* Left border */
    border-right-radius: 10px; /* Right rounded border */
    background-color: transparent; /* Transparent background */
    padding:10px 0;
    font-size: 16px; /* Text size */
    font-weight: bold; /* Bold text */
}}

QPushButton#AttributeButton:hover{{
    background-color: #B0E2FF; /* Background color on hover */
    border-right:1px solid #f0f0f0; /* Right border */
    border-left-radius: 10px; /* Left rounded border */
}}
QPushButton#BehaviorButton:hover{{
    background-color: #B0E2FF; /* Background color on hover */
    border-left:1px solid #f0f0f0; /* Left border */
    border-right-radius: 10px; /* Right rounded border */
}}

QPushButton#AttributeButton:checked {{
    background-color: #5dade2; /* Background color when checked */
    color: white; /* Text color when checked */
    border-right:1px solid #f0f0f0; /* Right border */
    border-left-radius: 10px; /* Left rounded border */
}}
QPushButton#BehaviorButton:checked {{
    background-color: #5dade2; /* Background color when checked */
    color: white; /* Text color when checked */
    border-left:1px solid #f0f0f0; /* Left border */
    border-right-radius: 10px; /* Right rounded border */
}}


QPushButton#BehaviorButton:pressed {{
    background-color: #5dade2; /* Background color when pressed */
    border-left:1px solid #f0f0f0; /* Left border */
    border-right-radius: 10px; /* Right rounded border */
}}

QPushButtonAttributeButton:pressed {{
    background-color: #5dade2; /* Background color when pressed */
    border-right:1px solid #f0f0f0; /* Right border */
    border-left-radius: 10px; /* Left rounded border */
}}

/* Table styles */
QTableWidget {{
    border: none;
    font-size: 14px;
    border-bottom: 1px solid black; /* Bottom line */
}}
QHeaderView::section {{
    border-top: 1px solid black;    /* Header top line */
    border-bottom: 1px solid black; /* Header bottom line */
    background-color: #f0f0f0;
    font-weight: bold;
    padding: 4px;
    color: #333333;
    text-align: center; /* Header content centered */
}}
QTableWidget::item {{
    border: none; /* No border for middle rows */
    padding: 5px;
    text-align: center; /* Cell content centered */
}}
/* Selected row styles */
QTableWidget::item:selected {{
    background-color: #cce5ff; /* Selected background color */
    color: black;             /* Selected text color */
    border: none;             /* No border when selected */
}}
QTableWidget:focus {{
    outline: none; /* Disable focus border */
}}
QListWidget {{
    border: 1px solid #c0c0c0;
    border-radius: 10px;
    border-top: none;
    border-bottom: none;
    background-color: white;
    outline: none;
    padding: 0px;
    margin: 0px;
    font-size: 14px;
}}

QListWidget::item {{
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 5px;
    margin: 2px;
}}

QListWidget::item:hover {{
    background-color: #cce5ff;
}}

QListWidget::item:selected {{
    background-color:#5dade2;
    color: white;
}}
""")

    def create_ontology_group_box(self):
        """Create Ontology Selection Area"""
        ontology_group_box = QGroupBox(self.tr("本体模型"))
        ontology_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
            }
        """)
        ontology_layout = QVBoxLayout()
        ontology_layout.setContentsMargins(10, 10, 10, 10)
        ontology_layout.setSpacing(10)

        # Dropdown and Zoom Buttons Layout
        combo_zoom_layout = QHBoxLayout()
        combo_zoom_layout.setSpacing(5)
        combo_zoom_layout.setContentsMargins(0, 0, 0, 0)

        self.ontology_combo = QComboBox()
        self.ontology_combo.addItem(self.tr("请选择本体"))
        if get_cfg()["i18n"]["language"] == "en_US":
            self.create_english_version()
        self.ontology_combo.addItems(list(self.SVG_FILES.keys()))
        self.ontology_combo.setCurrentIndex(0)
        self.ontology_combo.model().item(0).setEnabled(False)
        self.ontology_combo.currentIndexChanged.connect(self.handle_ontology_selection)

        # Zoom Buttons
        self.zoom_in_button = self.create_zoom_button(ZOOM_IN_ICON, self.tr("放大图像(按住 Ctrl 并滚动鼠标滚轮)"), self.zoom_in)
        self.zoom_out_button = self.create_zoom_button(ZOOM_OUT_ICON, self.tr("缩小图像(按住 Ctrl 并滚动鼠标滚轮)"), self.zoom_out)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)

        # 生成推演模型按钮
        self.generate_button = QPushButton(self.tr("生成推演模型"))
        self.generate_button.setFixedWidth(110)
        self.generate_button.clicked.connect(self.handle_generate)

        combo_zoom_layout.addWidget(self.ontology_combo)
        combo_zoom_layout.addStretch()
        combo_zoom_layout.addWidget(self.generate_button)
        combo_zoom_layout.addWidget(self.zoom_in_button)
        combo_zoom_layout.addWidget(self.zoom_out_button)

        ontology_layout.addLayout(combo_zoom_layout)

        # Image Loading Area
        self.ontology_scroll_area = QScrollArea()
        self.ontology_scroll_area.setWidgetResizable(True)
        self.ontology_scroll_area.setStyleSheet("border: none;")

        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setSpacing(5)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.ontology_image_label = ZoomableLabel()
        self.ontology_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ontology_image_label.setText(self.tr("图形加载区"))
        image_layout.addWidget(self.ontology_image_label, 1)

        self.ontology_scroll_area.setWidget(image_container)
        ontology_layout.addWidget(self.ontology_scroll_area, 1)

        ontology_group_box.setLayout(ontology_layout)
        return ontology_group_box

    def create_zoom_button(self, icon_path, tooltip, callback):
        """Create Zoom Button"""
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            button.setText(self.tr("缩放"))
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(24, 24))
        button.clicked.connect(callback)
        return button

    def create_class_group_box(self):
        """Create Class Selection Area"""
        class_group_box = QGroupBox(self.tr("类"))
        class_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
            }
        """)

        class_layout_container = QVBoxLayout()
        class_layout_container.setContentsMargins(15, 12, 15, 10)
        class_layout_container.setSpacing(10)

        self.class_list_widget = QListWidget()
        self.class_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.class_list_widget.itemSelectionChanged.connect(self.handle_class_selection)
        self.class_list_widget.setAlternatingRowColors(True)

        self.class_placeholder_label = QLabel(self.tr("请选择本体"))
        self.class_placeholder_label.setObjectName("placeholder")
        self.class_placeholder_label.setAlignment(Qt.AlignCenter)

        class_layout_container.addWidget(self.class_placeholder_label)
        class_layout_container.addWidget(self.class_list_widget)
        self.class_list_widget.hide()

        class_group_box.setLayout(class_layout_container)
        return class_group_box

    def create_attribute_widget(self):
        """Create Attribute Model Table"""
        attribute_widget = QWidget()
        attribute_layout = QVBoxLayout(attribute_widget)
        attribute_layout.setContentsMargins(10, 10, 10, 0)
        attribute_layout.setSpacing(0)

        self.attribute_table = QTableWidget()
        self.attribute_table.setColumnCount(3)
        self.attribute_table.setHorizontalHeaderLabels([self.tr("属性"), self.tr("范围"), self.tr("值")])
        self.apply_table_style(self.attribute_table)
        self.attribute_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.attribute_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.attribute_table.horizontalHeader().setStretchLastSection(True)
        self.attribute_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attribute_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attribute_table.setSelectionMode(QTableWidget.SingleSelection)
        self.attribute_table.verticalHeader().setVisible(False)
        self.attribute_table.setAlternatingRowColors(True)
        self.attribute_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attribute_table.setShowGrid(False)
        self.attribute_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.attribute_placeholder_label = QLabel(self.tr("请选择类"))
        self.attribute_placeholder_label.setObjectName("placeholder")
        self.attribute_placeholder_label.setAlignment(Qt.AlignCenter)

        attribute_layout.addWidget(self.attribute_placeholder_label)
        attribute_layout.addWidget(self.attribute_table)
        self.attribute_table.hide()

        return attribute_widget

    def create_behavior_widget(self):
        """Create Behavior Model Table"""
        behavior_widget = QWidget()
        behavior_layout = QVBoxLayout(behavior_widget)
        behavior_layout.setContentsMargins(10, 10, 10, 0)
        behavior_layout.setSpacing(5)

        self.behavior_table = QTableWidget()
        self.behavior_table.setColumnCount(3)
        self.behavior_table.setHorizontalHeaderLabels([self.tr("行为"), self.tr("范围"), self.tr("值")])
        self.apply_table_style(self.behavior_table)

        self.behavior_table.horizontalHeader().setFont(QFont("SimSun", 16, QFont.Bold))
        self.behavior_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.behavior_table.horizontalHeader().setStretchLastSection(True)
        self.behavior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.behavior_table.verticalHeader().setVisible(False)
        self.behavior_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.behavior_table.setSelectionMode(QTableWidget.SingleSelection)
        self.behavior_table.setAlternatingRowColors(True)
        self.behavior_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.behavior_table.setShowGrid(False)
        self.behavior_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.behavior_placeholder_label = QLabel(self.tr("请选择类"))
        self.behavior_placeholder_label.setObjectName("placeholder")
        self.behavior_placeholder_label.setAlignment(Qt.AlignCenter)

        behavior_layout.addWidget(self.behavior_placeholder_label)
        behavior_layout.addWidget(self.behavior_table)
        self.behavior_table.hide()

        return behavior_widget

    def apply_table_style(self, table: QTableWidget):
        """Apply three-line table style to the specified table."""
        table.setStyleSheet("""
                    QTableWidget {
                        border: none;
                        font-size: 14px;
                        border-bottom: 1px solid black; /* Bottom line */
                                            background-color: white;
    alternate-background-color: #e9e7e3;
                    }
                    QHeaderView::section {
                        border-top: 1px solid black;    /* Header top line */
                        border-bottom: 1px solid black; /* Header bottom line */
                        background-color: #f0f0f0;
                        font-weight: bold;
                        padding: 4px;
                        color: #333333;
                        text-align: center; /* Header content centered */
                    }
                    QTableWidget::item {
                        border: none; /* No border for middle rows */
                        padding: 5px;
                        text-align: center; /* Cell content centered */
                    }
                    /* Selected row styles */
                    QTableWidget::item:selected {
                        background-color: #cce5ff; /* Selected background color */
                        color: black;             /* Selected text color */
                        border: none;             /* No border when selected */
                    }
                    QTableWidget:focus {
                        outline: none; /* Disable focus border */
                    }
                """)

        # Ensure header styles are refreshed
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        """Ensure that the header styles are refreshed to prevent line loss."""
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

    def populate_table(self, table: QTableWidget, data: list):
        """Populate table data."""
        print(f"Populating table with data: {data}")
        table.setRowCount(len(data))
        for row_idx, (attr, scope, value) in enumerate(data):
            table.setItem(row_idx, 0, QTableWidgetItem(attr))
            table.setItem(row_idx, 1, QTableWidgetItem(scope))
            table.setItem(row_idx, 2, QTableWidgetItem(value))
            table.item(row_idx, 0).setTextAlignment(Qt.AlignCenter)
            table.item(row_idx, 1).setTextAlignment(Qt.AlignCenter)
            table.item(row_idx, 2).setTextAlignment(Qt.AlignCenter)

    def show_tab(self, index):
        """Show the corresponding tab based on button index."""
        self.stacked_layout.setCurrentIndex(index)
        if index == 0:
            self.attribute_button.setChecked(True)
            self.behavior_button.setChecked(False)
        elif index == 1:
            self.attribute_button.setChecked(False)
            self.behavior_button.setChecked(True)

    def zoom_in(self):
        """Zoom in the image."""
        if self.ontology_image_label.image_loaded:
            self.ontology_image_label.scale_factor *= 1.1
            self.ontology_image_label.scale_factor = min(self.ontology_image_label.scale_factor, 10.0)
            self.ontology_image_label.update_pixmap()

    def zoom_out(self):
        """Zoom out the image."""
        if self.ontology_image_label.image_loaded:
            self.ontology_image_label.scale_factor /= 1.1
            self.ontology_image_label.scale_factor = max(self.ontology_image_label.scale_factor, 0.1)
            self.ontology_image_label.update_pixmap()

    def handle_generate(self):
        """Handle the logic for generating the model."""

        self.generate_request.emit()

    def handle_ontology_selection(self, index):
        """Handle ontology selection from the dropdown."""
        if index == 0:
            self.reset_ontology_selection()
            return

        option = self.ontology_combo.currentText()
        self.current_ontology = option
        svg_filename = self.SVG_FILES.get(option, "")
        svg_path = svg_filename
        print(f"Selected ontology: {option}, SVG path: {svg_path}")

        if not os.path.exists(svg_path):
            self.ontology_image_label.setText(self.tr("无法找到 SVG 文件"))
            self.ontology_image_label.image_loaded = False
            self.toggle_zoom_buttons(False)
            CustomWarningDialog(self.tr("提示"), self.tr("无法找到对应的图形文件。")).exec()
            self.reset_class_selection()
            self.reset_model_tabs_after_ontology()
            return
        else:
            self.ontology_image_label.set_svg(svg_path)
            self.ontology_image_label.image_loaded = True
            self.toggle_zoom_buttons(True)
            # Update class selection area
            self.update_class_selection()

            # Reset attribute and behavior model areas to "Please select a class"
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText(self.tr("请选择类"))
            self.attribute_placeholder_label.show()

            self.behavior_table.hide()
            self.behavior_placeholder_label.setText(self.tr("请选择类"))
            self.behavior_placeholder_label.show()

    def reset_ontology_selection(self):
        """Reset ontology selection related UI components."""
        self.ontology_combo.setCurrentIndex(0)
        self.ontology_image_label.setText(self.tr("图形加载区"))
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
        """Enable or disable zoom buttons."""
        self.zoom_in_button.setEnabled(enable)
        self.zoom_out_button.setEnabled(enable)

    def update_class_selection(self):
        """Update class selection area based on selected ontology."""
        self.class_list_widget.clear()
        self.class_placeholder_label.hide()

        if self.current_ontology in self.CLASS_OPTIONS and self.CLASS_OPTIONS[self.current_ontology]:
            class_options = self.CLASS_OPTIONS[self.current_ontology]
            self.current_class = None

            for option in class_options:
                item = QListWidgetItem(option)
                item.setTextAlignment(Qt.AlignCenter)
                self.class_list_widget.addItem(item)

            self.class_list_widget.show()
            self.class_placeholder_label.hide()
        else:
            self.class_placeholder_label.setText(self.tr("该本体没有类"))
            self.class_placeholder_label.show()
            self.class_list_widget.hide()
            self.current_class = None

    def reset_class_selection(self):
        """Reset class selection area to initial state."""
        self.class_list_widget.clear()
        self.class_placeholder_label.setText(self.tr("请选择本体"))
        self.class_placeholder_label.show()
        self.class_list_widget.hide()
        self.current_class = None

    def handle_class_selection(self):
        """Handle class selection logic."""
        selected_items = self.class_list_widget.selectedItems()
        if selected_items:
            selected_class = selected_items[0].text()
            self.current_class = selected_class
            self.update_model_tabs()
        else:
            self.current_class = None
            self.reset_model_tabs_after_ontology()

    def reset_model_tabs_before_ontology(self):
        """Reset attribute and behavior model areas to 'Please select ontology'."""
        self.attribute_table.hide()
        self.attribute_placeholder_label.setText(self.tr("请选择本体"))
        self.attribute_placeholder_label.show()

        self.behavior_table.hide()
        self.behavior_placeholder_label.setText(self.tr("请选择本体"))
        self.behavior_placeholder_label.show()

        self.toggle_model_tabs(True)

    def reset_model_tabs_after_ontology(self):
        """Reset attribute and behavior model areas to 'Please select class'."""
        self.attribute_table.hide()
        self.attribute_placeholder_label.setText(self.tr("请选择类"))
        self.attribute_placeholder_label.show()

        self.behavior_table.hide()
        self.behavior_placeholder_label.setText(self.tr("请选择类"))
        self.behavior_placeholder_label.show()

    def update_model_tabs(self):
        """Update attribute and behavior model areas based on selected class."""
        if not self.current_class:
            self.reset_model_tabs_after_ontology()
            return

        # Update Attribute Model
        attributes = self.ATTRIBUTE_SAMPLE_DATA.get(self.current_class, [])
        if attributes:
            self.attribute_placeholder_label.hide()
            self.attribute_table.show()
            self.populate_table(self.attribute_table, attributes)
        else:
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText(self.tr("无属性数据"))
            self.attribute_placeholder_label.show()

        # Update Behavior Model
        behaviors = self.BEHAVIOR_SAMPLE_DATA.get(self.current_class, [])
        if behaviors:
            self.behavior_placeholder_label.hide()
            self.behavior_table.show()
            self.populate_table(self.behavior_table, behaviors)
        else:
            self.behavior_table.hide()
            self.behavior_placeholder_label.setText(self.tr("无行为数据"))
            self.behavior_placeholder_label.show()

    def toggle_model_tabs(self, enable: bool):
        """Enable or disable attribute and behavior model areas."""
        if enable:
            self.attribute_button.setEnabled(True)
            self.behavior_button.setEnabled(True)
        else:
            self.attribute_button.setEnabled(False)
            self.behavior_button.setEnabled(False)
            self.stacked_layout.setCurrentWidget(self.attribute_widget)
            self.attribute_button.setChecked(True)
            self.behavior_button.setChecked(False)

    def handle_save(self):
        """Collect all checked feature data and simulate save operation."""
        CustomInformationDialog(self.tr("保存成功"), self.tr("已成功保存要素数据。")).exec()

    def reset_inputs(self):
        """Reset all inputs."""
        self.reset_ontology_selection()
        self.generate_button.setChecked(False)
        self.attribute_button.setChecked(True)
        self.behavior_button.setChecked(False)
        self.stacked_layout.setCurrentWidget(self.attribute_widget)

    def load_models_data(self, category):
        """Load attribute and behavior data based on selected category."""
        print(f"Loading data for category: {category}")

        attributes = self.ATTRIBUTE_SAMPLE_DATA.get(category, [])
        behaviors = self.BEHAVIOR_SAMPLE_DATA.get(category, [])

        if attributes:
            self.attribute_placeholder_label.hide()
            self.attribute_table.show()
            self.populate_table(self.attribute_table, attributes)
        else:
            self.attribute_table.hide()
            self.attribute_placeholder_label.setText(self.tr("无属性数据"))
            self.attribute_placeholder_label.show()

        if behaviors:
            self.behavior_placeholder_label.hide()
            self.behavior_table.show()
            self.populate_table(self.behavior_table, behaviors)
        else:
            self.behavior_table.hide()
            self.behavior_placeholder_label.setText(self.tr("无行为数据"))
            self.behavior_placeholder_label.show()

    def create_english_version(self):
        # 定义中英文键映射
        key_translations = {
            "整体": "Overall",
            "突发事件本体": "Emergency Ontology",
            "情景本体": "Scenario Ontology",
            "情景要素本体": "ScenarioElement Ontology"
        }

        print(f"原始svg文件：{self.SVG_FILES}")
        print(f"原始类选项：{self.CLASS_OPTIONS}")

        # 修改 SVG_FILES 字典
        for zh_key in list(self.SVG_FILES.keys()):  # 使用 list() 创建键的副本，避免在迭代时修改字典
            if zh_key in key_translations:
                value = self.SVG_FILES.pop(zh_key)  # 移除原始键值对
                self.SVG_FILES[key_translations[zh_key]] = value  # 添加新键值对

        # 修改 CLASS_OPTIONS 字典
        for zh_key in list(self.CLASS_OPTIONS.keys()):
            if zh_key in key_translations:
                value = self.CLASS_OPTIONS.pop(zh_key)
                self.CLASS_OPTIONS[key_translations[zh_key]] = value

        print(f"修改后的svg文件：{self.SVG_FILES}")
        print(f"修改后的类选项：{self.CLASS_OPTIONS}")