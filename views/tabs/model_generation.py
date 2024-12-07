from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
    QLabel, QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QSizePolicy, QRadioButton, QButtonGroup, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QWheelEvent, QTransform, QPainter, QIcon
from PySide6.QtSvg import QSvgRenderer
import os
import sys

from owlready2.setup_develop_mode import current_dir

from views.dialogs.custom_warning_dialog import CustomWarningDialog


class ZoomableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.renderer = QSvgRenderer()
        self.scale_factor = 1.0
        self.image_loaded = False  # 标志位，判断是否加载了图像

    def set_svg(self, svg_path):
        if not self.renderer.load(svg_path):
            self.setText("无法加载图像")
            self.image_loaded = False
            return
        self.scale_factor = 1.0
        self.image_loaded = True
        self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
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
        if self.renderer.isValid() and self.image_loaded:
            # 计算新的大小
            size = self.renderer.defaultSize() * self.scale_factor
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)

            # 渲染 SVG 到 pixmap
            painter = QPainter(pixmap)
            self.renderer.render(painter)
            painter.end()

            # 设置 pixmap
            super().setPixmap(pixmap)


    def mousePressEvent(self, event):
        if not self.image_loaded and event.button() == Qt.LeftButton:
            CustomWarningDialog("提示", "未选择本体，请选择本体").exec()
        else:
            super().mousePressEvent(event)


class ModelGenerationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置整体样式
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
                background-color: white;
            }

            /* 自定义滚动条样式（统一垂直和水平滚动条） */
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

            /* 设定占位符标签的样式 */
            QLabel#placeholder {
                background-color: white;
                color: #666666;
                border: none;
                font-style: italic;
            }

            /* 按钮样式 */
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 10)  # 左, 上, 右, 下

        # 上部区域
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # 左侧 - 本体模型区域
        ontology_group_box = QGroupBox("本体模型")
        ontology_layout = QVBoxLayout()
        ontology_layout.setContentsMargins(15, 15, 15, 10)  # 设置内边距（左、上、右、下）
        ontology_layout.setSpacing(10)  # 设置内部控件之间的间距

        # 创建一个水平布局来放置下拉框和缩放按钮
        combo_zoom_layout = QHBoxLayout()
        combo_zoom_layout.setSpacing(5)
        combo_zoom_layout.setContentsMargins(0, 0, 0, 0)

        # 下拉栏（合并“请选择本体”到下拉框）
        self.ontology_combo = QComboBox()
        self.ontology_combo.addItem("请选择本体")  # 添加占位符
        self.ontology_combo.addItems(["整体", "突发事件本体", "情景本体", "情景要素本体"])
        self.ontology_combo.setCurrentIndex(0)  # 设置占位符为当前选中项

        # 禁用占位符选项，防止用户选择
        self.ontology_combo.model().item(0).setEnabled(False)

        # 连接下拉框选择信号
        self.ontology_combo.currentIndexChanged.connect(self.handle_ontology_selection)

        # 放大按钮
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.zoom_in_button = QPushButton()
        self.zoom_in_button.setIcon(QIcon(os.path.join(current_dir, '../../resources/icons/zoom_in.png')))  # 使用您的放大图标路径
        self.zoom_in_button.setToolTip("放大图像(按住 Ctrl 并滚动鼠标滚轮)")
        self.zoom_in_button.setFixedSize(QSize(24, 24))
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_in_button.setEnabled(False)  # 初始禁用

        # 缩小按钮
        self.zoom_out_button = QPushButton()
        self.zoom_out_button.setIcon(QIcon(os.path.join(current_dir, '../../resources/icons/zoom_out.png')))  # 使用您的缩小图标路径
        self.zoom_out_button.setToolTip("缩小图像(按住 Ctrl 并滚动鼠标滚轮)")
        self.zoom_out_button.setFixedSize(QSize(24, 24))
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_out_button.setEnabled(False)  # 初始禁用

        # 将下拉框和缩放按钮添加到水平布局
        combo_zoom_layout.addWidget(self.ontology_combo)
        combo_zoom_layout.addStretch()  # 添加弹簧，使按钮靠右对齐
        combo_zoom_layout.addWidget(self.zoom_in_button)
        combo_zoom_layout.addWidget(self.zoom_out_button)

        ontology_layout.addLayout(combo_zoom_layout)

        # 图像加载区域（支持缩放）
        self.ontology_scroll_area = QScrollArea()
        self.ontology_scroll_area.setWidgetResizable(True)
        self.ontology_scroll_area.setStyleSheet("border: none;")  # 移除 QScrollArea 的边框

        # 创建一个垂直布局来放置图像
        image_container_layout = QVBoxLayout()
        image_container_layout.setSpacing(5)
        image_container_layout.setContentsMargins(0, 0, 0, 0)

        self.ontology_image_label = ZoomableLabel()
        self.ontology_image_label.setStyleSheet("background-color: #f9f9f9;")
        self.ontology_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 初始显示“图形加载区”
        self.ontology_image_label.setText("图形加载区")
        self.ontology_image_label.image_loaded = False  # 标志位

        image_container_layout.addWidget(self.ontology_image_label, 1)

        container_widget = QWidget()

        container_widget.setLayout(image_container_layout)
        self.ontology_scroll_area.setWidget(container_widget)
        ontology_layout.addWidget(self.ontology_scroll_area, 1)

        ontology_group_box.setLayout(ontology_layout)
        top_layout.addWidget(ontology_group_box, 3)  # 左侧区域占更多比例

        # 右侧 - 类选择、属性模型和行为模型区域
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # 类选择区域
        class_group_box = QGroupBox("类")
        # 移除内部区域的边框和背景
        class_group_box.setStyleSheet("""
            QGroupBox {
                background-color: transparent;
            }
            QGroupBox::title {
                font-weight: bold;
                color: #333333;
            }
        """)
        class_scroll_area = QScrollArea()
        class_scroll_area.setWidgetResizable(True)
        class_scroll_area.setStyleSheet("border: none;")  # 移除滚动条区域的边框
        class_content = QWidget()
        class_content.setStyleSheet("background-color: white;")  # 移除内容区域的背景
        class_layout = QVBoxLayout(class_content)
        class_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        class_layout.setSpacing(5)  # 调整间距
        self.class_button_group = QButtonGroup(self)  # 创建单选按钮组
        class_options = [
            "Scenario", "AbsorptionScenario", "AdaptionScenario",
            "RecoveryScenario", "ScenarioResilience", "ResilienceInfluentialFactors",
            "EconomicFactors", "FunctionFactors", "SafetyFactors", "TimeFactors", "InvolvedScenarioElement"
        ]
        for option in class_options:
            radio_button = QRadioButton(option)
            self.class_button_group.addButton(radio_button)
            class_layout.addWidget(radio_button)
        class_scroll_area.setWidget(class_content)
        class_group_box_layout = QVBoxLayout()
        class_group_box_layout.setContentsMargins(15, 15, 15, 10)  # 设置内边距（左、上、右、下）
        class_group_box_layout.setSpacing(10)  # 设置内部控件之间的间距
        class_group_box_layout.addWidget(class_scroll_area)
        class_group_box.setLayout(class_group_box_layout)

        # 属性模型区域
        attribute_group_box = QGroupBox("属性模型")
        attribute_scroll_area = QScrollArea()
        attribute_scroll_area.setWidgetResizable(True)
        attribute_scroll_area.setStyleSheet("border: none;")  # 移除滚动条区域的边框
        attribute_content = QWidget()
        attribute_content.setStyleSheet("background-color: white;")  # 移除内容区域的背景
        attribute_layout = QVBoxLayout(attribute_content)
        attribute_layout.setContentsMargins(0, 0, 0, 0)
        attribute_layout.setSpacing(5)
        self.attribute_table = QTableWidget(10, 2)
        self.attribute_table.setHorizontalHeaderLabels(["属性", "范围"])
        self.apply_three_line_table_style(self.attribute_table)  # 应用统一的表格样式
        self.force_refresh_table_headers(self.attribute_table)
        self.attribute_table.horizontalHeader().setStretchLastSection(True)
        self.attribute_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attribute_table.verticalHeader().setVisible(False)
        self.attribute_table.setAlternatingRowColors(True)  # 使用交替行颜色区分

        self.attribute_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用默认编辑功能
        self.attribute_table.setShowGrid(False)  # 移除默认的网格线

        attribute_layout.addWidget(self.attribute_table)
        attribute_scroll_area.setWidget(attribute_content)
        attribute_group_box_layout = QVBoxLayout()
        attribute_group_box_layout.setContentsMargins(15, 15, 15, 10)  # 设置内边距（左、上、右、下）
        attribute_group_box_layout.setSpacing(10)  # 设置内部控件之间的间距
        attribute_group_box_layout.addWidget(attribute_scroll_area)
        attribute_group_box.setLayout(attribute_group_box_layout)

        # 行为模型区域
        behavior_group_box = QGroupBox("行为模型")

        behavior_scroll_area = QScrollArea()
        behavior_scroll_area.setWidgetResizable(True)
        behavior_scroll_area.setStyleSheet("border: none;")  # 移除滚动条区域的边框
        behavior_content = QWidget()
        behavior_content.setStyleSheet("background-color: white;")  # 移除内容区域的背景
        behavior_layout = QVBoxLayout(behavior_content)
        behavior_layout.setContentsMargins(0, 0, 0, 0)
        behavior_layout.setSpacing(5)
        self.behavior_table = QTableWidget(10, 2)
        self.behavior_table.setHorizontalHeaderLabels(["属性", "范围"])
        self.apply_three_line_table_style(self.behavior_table)  # 应用统一的表格样式
        self.force_refresh_table_headers(self.behavior_table)
        self.behavior_table.horizontalHeader().setStretchLastSection(True)
        self.behavior_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.behavior_table.verticalHeader().setVisible(False)
        self.behavior_table.setAlternatingRowColors(True)  # 使用交替行颜色区分

        self.behavior_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用默认编辑功能
        self.behavior_table.setShowGrid(False)  # 移除默认的网格线

        behavior_layout.addWidget(self.behavior_table)
        behavior_scroll_area.setWidget(behavior_content)
        behavior_group_box_layout = QVBoxLayout()
        behavior_group_box_layout.setContentsMargins(15, 15, 15, 10)  # 设置内边距（左、上、右、下）
        behavior_group_box_layout.setSpacing(10)  # 设置内部控件之间的间距
        behavior_group_box_layout.addWidget(behavior_scroll_area)
        behavior_group_box.setLayout(behavior_group_box_layout)

        # 组合右侧布局
        right_layout.addWidget(class_group_box, 1)
        right_layout.addWidget(attribute_group_box, 1)
        right_layout.addWidget(behavior_group_box, 1)

        # 将左侧和右侧添加到上部布局
        top_layout.addLayout(right_layout, 2)  # 右侧减少比例

        # 下部区域 - 生成按钮
        self.generate_button = QPushButton("生成推演模型")
        self.generate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.generate_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px;
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QPushButton:pressed {
                background-color: #003f7f;
            }
        """)  # 按钮样式优化

        # 添加布局到主布局
        main_layout.addLayout(top_layout, 5)  # 上部区域占5/6
        main_layout.addWidget(self.generate_button, 1)  # 按钮区域占1/6

        # 设置主布局
        self.setLayout(main_layout)

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
            }
            QTableWidget::item {
                border: none; /* 中间行无边框 */
                padding: 5px;
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
            }
        """)
        table.horizontalHeader().repaint()  # 使用 repaint() 确保样式应用

    def handle_save(self):
        """模拟保存操作"""
        # 收集所有被勾选的要素数据
        saved_data = []
        # 假设有多个要素类别，这里简化为示例
        # 您需要根据实际情况修改此部分
        QMessageBox.information(self, "保存成功", "已成功保存推演模型。")

    def handle_ontology_selection(self, index):
        """处理本体模型下拉框的选择"""
        if index == 0:
            # 用户选择了占位符，提示用户选择有效选项
            QMessageBox.warning(self, "提示", "请选择一个有效的本体。")
            # 重新设置为占位符
            self.ontology_combo.setCurrentIndex(0)
            # 设置图像加载区为占位符
            self.ontology_image_label.setText("图形加载区")
            self.ontology_image_label.image_loaded = False
            # 禁用缩放按钮
            self.zoom_in_button.setEnabled(False)
            self.zoom_out_button.setEnabled(False)
        else:
            # 加载相应的图像
            option = self.ontology_combo.currentText()
            # 根据选择的选项加载不同的图像
            # 这里以Option 1为例，实际应用中需要根据选项加载不同的文件
            current_dir = os.path.dirname(os.path.abspath(__file__))

            if option == "整体":
                svg_path =os.path.join(current_dir, 'temp.svg')
            elif option == "突发事件本体":
                svg_path = ""
            elif option == "情景本体":
                svg_path = ""
            elif option == "情景要素本体":
                svg_path = ""
            else:
                svg_path = ""

            if not os.path.isabs(svg_path):
                svg_path = os.path.join(os.getcwd(), svg_path)

            if not os.path.exists(svg_path):
                self.ontology_image_label.setText("无法找到 SVG 文件")
                self.ontology_image_label.image_loaded = False
                # 禁用缩放按钮
                self.zoom_in_button.setEnabled(False)
                self.zoom_out_button.setEnabled(False)
                QMessageBox.warning(self, "提示", "无法找到对应的图形文件。")
            else:
                self.ontology_image_label.set_svg(svg_path)
                self.ontology_image_label.image_loaded = True
                # 启用缩放按钮
                self.zoom_in_button.setEnabled(True)
                self.zoom_out_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModelGenerationTab()
    window.resize(1200, 800)  # 设置窗口大小
    window.show()
    sys.exit(app.exec())
