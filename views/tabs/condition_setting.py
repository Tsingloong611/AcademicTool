import json
import os
import sys
from functools import partial

import requests
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QDialog, QHeaderView, QStackedLayout, QSpinBox, QComboBox, QLineEdit,
    QListWidget, QTextBrowser, QStyleOptionViewItem, QStyledItemDelegate, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent, QObject, Slot, QUrl
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QIcon

from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog


# ============== 自定义委托 / 小组件（跟原代码保持一致） ==============

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

    combobox.setEditable(True)
    combobox.lineEdit().setReadOnly(True)
    combobox.lineEdit().setAlignment(Qt.AlignCenter)

    view = combobox.view()
    delegate = CenteredItemDelegate(view)
    view.setItemDelegate(delegate)

    no_wheel_filter = NoWheelEventFilter(combobox)
    combobox.installEventFilter(no_wheel_filter)

    return combobox

class FullHeaderDelegate(QStyledItemDelegate):
    """
    自定义两行多级表头，保持原先多级表头的结构。
      - row=0 col=1/4 ("推演前/推演后")去掉下边线
      - row=1 col=1..6 ("较好/中等/较差")去掉上边线
    """
    def paint(self, painter, option, index):
        r, c = index.row(), index.column()
        if r < 2:
            painter.save()
            painter.fillRect(option.rect, QColor("#f0f0f0"))

            if r == 0 and c == 0:
                # 斜杠 “韧性/预案”
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())

                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

                # 斜线
                painter.drawLine(option.rect.topLeft(), option.rect.bottomRight())

                # 上下文字
                topRect = option.rect.adjusted(0, 0, 0, -option.rect.height()//2)
                bottomRect = option.rect.adjusted(0, option.rect.height()//2, 0, 0)
                painter.drawText(topRect, Qt.AlignCenter, "韧性")
                painter.drawText(bottomRect, Qt.AlignCenter, "预案")

            elif r == 0 and c == 1:
                # “推演前”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, "推演前")

            elif r == 0 and c == 4:
                # “推演后”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, "推演后")

            elif r == 0:
                # 其他被合并单元格
                painter.fillRect(option.rect, QColor("#f0f0f0"))

            elif r == 1 and c in [1,2,3,4,5,6]:
                # 第二行“较好/中等/较差”，去掉上边线
                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
                text_map = {
                    1:"较好", 2:"中等", 3:"较差",
                    4:"较好", 5:"中等", 6:"较差"
                }
                painter.drawText(option.rect, Qt.AlignCenter, text_map[c])

            painter.restore()
        else:
            # row>=2 => 数据行
            super().paint(painter, option, index)

class CustomTableWidget(QTableWidget):
    """
    自定义表格Widget，用于控制一些 resizeEvent & 样式
    """
    def resizeEvent(self, event):
        super().resizeEvent(event)
        content_width = self.horizontalHeader().length()
        if content_width < 550:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()

class CustomCheckBoxWithLabel(QWidget):
    duration_changed = Signal()

    def __init__(self, label_text):
        super().__init__()
        self.init_ui(label_text)

    def init_ui(self, label_text):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0,0,0,0)

        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.label = ClickableLabel(label_text)
        self.label.setStyleSheet("cursor: pointer;color: black;font-weight: normal;")
        self.label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0,10000)
        self.duration_spin.setSuffix(" 分钟")
        self.duration_spin.setEnabled(False)
        self.duration_spin.setStyleSheet("background-color: #eee;")
        self.duration_spin.setAlignment(Qt.AlignCenter)
        self.duration_spin.valueChanged.connect(self.emit_duration_changed)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(QLabel("时长:"))
        layout.addWidget(self.duration_spin)

    def emit_duration_changed(self):
        self.duration_changed.emit()

    def set_selected(self, selected):
        font = self.label.font()
        if selected:
            font.setBold(True)
            self.label.setFont(font)
            self.label.setStyleSheet("font-weight: bold; color: #5dade2; cursor: pointer;")
            self.duration_spin.setEnabled(True)
            self.duration_spin.setStyleSheet("background-color: white;")
        else:
            font.setBold(False)
            self.label.setFont(font)
            self.label.setStyleSheet("font-weight: normal; color: black; cursor: pointer;")
            self.duration_spin.setEnabled(False)
            self.duration_spin.setStyleSheet("background-color: #eee;")

    def get_duration(self):
        return self.duration_spin.value()



# ============== 地图对话框（改为 open() + 信号槽，但保持原布局 & 样式） ==============

class LocationBridge(QObject):
    locationSelected = Signal(float, float)

    @Slot(float, float)
    def sendLocationToQt(self, lat, lng):
        self.locationSelected.emit(lat, lng)

class MapDialog(QDialog):
    """
    非阻塞地图对话框 (open)，保留原布局和 closeEvent() 手动释放
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高德地图选择")
        self.resize(800, 600)

        self.selected_lat = 0.0
        self.selected_lng = 0.0

        layout = QVBoxLayout(self)

        self.webview = QWebEngineView(self)
        layout.addWidget(self.webview, stretch=1)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # WebChannel
        self.channel = QWebChannel(self.webview.page())
        self.bridge = LocationBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # 信号连接
        self.bridge.locationSelected.connect(self.on_location_selected)
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)

        center_lat, center_lng = self.get_current_location()

        # 定义 HTML 内容
        js_api_key = get_config().get("gaode-map", {}).get("javascript_api_key", "")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>高德地图选择</title>
            <style>
                html, body, #mapContainer {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
            </style>
            <script src="https://webapi.amap.com/maps?v=2.0&key={js_api_key}"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                var bridge = null;
                var map = null;
                var marker = null;

                function initMap() {{
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        bridge = channel.objects.bridge;
                    }});

                    map = new AMap.Map('mapContainer', {{
                        resizeEnable: true,
                        center: [{center_lng}, {center_lat}],
                        zoom: 13
                    }});

                    map.on('click', function(e) {{
                        var lnglat = e.lnglat;
                        var lng = lnglat.getLng();
                        var lat = lnglat.getLat();

                        if (marker) {{
                            map.remove(marker);
                        }}
                        marker = new AMap.Marker({{
                            position: lnglat
                        }});
                        marker.setMap(map);

                        if (bridge) {{
                            bridge.sendLocationToQt(lat, lng);
                        }}
                    }});
                }}
                window.onload = initMap;
            </script>
        </head>
        <body>
            <div id="mapContainer"></div>
        </body>
        </html>
        """
        self.webview.setHtml(html_content, QUrl("qrc:///"))

    @Slot(float, float)
    def on_location_selected(self, lat, lng):
        self.selected_lat = lat
        self.selected_lng = lng

    def on_ok_clicked(self):
        if self.selected_lat == 0.0 and self.selected_lng == 0.0:
            QMessageBox.warning(self, "未选择位置", "请在地图上点击选择位置。")
            return
        self.accept()

    def get_selected_coordinates(self):
        return self.selected_lat, self.selected_lng

    def get_current_location(self, default_lat=39.0, default_lng=116.0):
        web_service_key = get_config().get("gaode-map", {}).get("web_service_key", "")
        url = f"https://restapi.amap.com/v3/ip?key={web_service_key}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1" and "rectangle" in data:
                    rectangle = data["rectangle"]
                    coords = rectangle.split(';')
                    if len(coords) == 2:
                        lng_min, lat_min = map(float, coords[0].split(','))
                        lng_max, lat_max = map(float, coords[1].split(','))
                        center_lat = (lat_min + lat_max) / 2
                        center_lng = (lng_min + lng_max) / 2
                        return center_lat, center_lng
        except Exception as e:
            print(f"获取当前位置失败: {e}")
        return default_lat, default_lng

    def closeEvent(self, event):
        # 手动释放 QWebEngineView 和 QWebChannel
        if self.webview and self.webview.page():
            self.webview.page().setWebChannel(None)
        if hasattr(self, 'channel') and self.channel:
            self.channel.deleteLater()
            self.channel = None
        if self.webview:
            self.webview.setParent(None)
            self.webview.deleteLater()
            self.webview = None
        super().closeEvent(event)

# ============== 资源信息对话框（改为 open() + 信号槽，保留原布局/样式） ==============
def get_config():
    # 获取项目根目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../../config.json")

    # 确保路径有效
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # 读取并解析 config.json
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 访问配置中的各个部分
    database_config = config.get("database", {})
    i18n_config = config.get("i18n", {})
    gaode_map_config = config.get("gaode-map", {})

    # 示例：打印数据库配置
    print(f"Database username: {database_config.get('username')}")
    print(f"Database host: {database_config.get('host')}")
    print(f"Language: {i18n_config.get('language')}")
    print(f"Gaode Map enabled: {gaode_map_config.get('enable')}")
    return config

class SingleResourceDialog(QDialog):
    """
    改用 open() 显示，不用 exec()。保留原先布局和样式。
    当点击“确定”时，触发 QDialog.accepted 信号，由父级回调获取资源信息。
    """
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("资源信息")
        self.resource = resource
        self.online_map_mode = get_config().get("gaode-map", {}).get("enable", False)
        self.init_ui()
        self.resize(600, 300)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.resource_label = QLabel("资源:")
        self.resource_input = create_centered_combobox(["人员", "物资", "车辆"], "人员")
        layout.addWidget(self.resource_label)
        layout.addWidget(self.resource_input)

        self.type_label = QLabel("类型:")
        self.type_input = create_centered_combobox(["类型A", "类型B", "类型C"], "类型A")
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_input)

        self.quantity_label = QLabel("数量:")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setAlignment(Qt.AlignCenter)
        self.quantity_spin.setRange(1,1000)
        layout.addWidget(self.quantity_label)
        layout.addWidget(self.quantity_spin)

        # ------------【位置行：QLineEdit + 小地图图标按钮】-------------
        self.location_label = QLabel("位置:")
        loc_h_layout = QHBoxLayout()
        self.location_input = QLineEdit()
        loc_h_layout.addWidget(self.location_input)

        self.map_button = QPushButton()
        self.map_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/location.png")))  # 保留你的原图标
        self.map_button.setStyleSheet("""

        """)
        if self.online_map_mode:
            self.map_button.setToolTip("点击选择位置")
            self.map_button.clicked.connect(self.open_map_dialog)
        else:
            self.map_button.setToolTip("地图选取功能未启用")
            self.map_button.setDisabled(True)

        loc_h_layout.addWidget(self.map_button)
        layout.addWidget(self.location_label)
        layout.addLayout(loc_h_layout)
        # --------------------------------------------------------------

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # 如果有初始 resource，就填充
        if self.resource:
            self.resource_input.setCurrentText(self.resource["资源"])
            self.type_input.setCurrentText(self.resource["类型"])
            self.quantity_spin.setValue(self.resource["数量"])
            self.location_input.setText(self.resource["位置"])

        for i in range(btn_layout.count()):
            btn_layout.itemAt(i).widget().setFixedWidth(50)

        # 保留原先样式
        self.setStyleSheet("""
            QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """)

    def open_map_dialog(self):
        """
        弹出地图选取对话框(非阻塞方式)。
        """
        map_dlg = MapDialog(self)
        # 当 map_dlg accepted 时拿到坐标更新
        map_dlg.accepted.connect(lambda: self.on_map_accepted(map_dlg))
        map_dlg.open()

    def on_map_accepted(self, map_dlg):
        lat, lng = map_dlg.get_selected_coordinates()
        addr = self.reverse_geocode(lat, lng)
        self.location_input.setText(f"{addr} ({lat},{lng})")

    def get_resource(self):
        return {
            "资源": self.resource_input.currentText(),
            "类型": self.type_input.currentText(),
            "数量": self.quantity_spin.value(),
            "位置": self.location_input.text() or "未知"
        }

    def reverse_geocode(self, lat, lng):
        web_service_key = get_config().get("gaode-map", {}).get("web_service_key", "")
        url = f"https://restapi.amap.com/v3/geocode/regeo?location={lng},{lat}&key={web_service_key}&radius=1000&extensions=all"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "regeocode" in data:
                return data["regeocode"]["formatted_address"]
        return "未知地址"

# ============== 详情查看对话框 & 保存结果对话框（保持原布局，改成 open()） ==============

class DetailsDialog(QDialog):
    def __init__(self, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详细信息")
        self.setModal(True)
        self.resize(600,400)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setHtml(info_html)
        layout.addWidget(self.browser)
        close_btn = QPushButton("确定")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(50)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(close_btn)
        h.addStretch()
        layout.addLayout(h)
        self.setLayout(layout)

class SaveResultDialog(QDialog):
    def __init__(self, saved_categories, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存结果")
        self.setModal(True)
        self.resize(300,250)
        main_layout = QVBoxLayout(self)
        lab = QLabel("已保存的应急行为类别:")
        lab.setFont(QFont("SimSun",14,QFont.Bold))
        main_layout.addWidget(lab)

        self.listwidget = QListWidget()
        for sc in saved_categories:
            self.listwidget.addItem(sc["category"])
        main_layout.addWidget(self.listwidget)

        btn_h = QHBoxLayout()
        self.btn_detail = QPushButton("查看详情")
        self.btn_detail.setFixedWidth(85)
        self.btn_detail.clicked.connect(lambda: self.open_detail_dialog(info_html))
        self.btn_ok = QPushButton("确定")
        self.btn_ok.setFixedWidth(50)
        self.btn_ok.clicked.connect(self.accept)
        btn_h.addWidget(self.btn_detail)
        btn_h.addWidget(self.btn_ok)
        main_layout.addLayout(btn_h)
        self.setLayout(main_layout)

    def open_detail_dialog(self, info_html):
        dlg = DetailsDialog(info_html, parent=self)
        dlg.open()  # 用 open() 非阻塞


# ============== 主界面: ConditionSettingTab (保留原先布局 & 样式), 改用 open() ==============

class ConditionSettingTab(QWidget):
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应急预案设置")
        # 行为资源
        self.behavior_resources = {b:[] for b in ["救助","牵引","抢修","消防"]}
        self.current_behavior = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI components and layout with three layers:
        1. Execute Simulation Button (Top)
        2. Emergency Behavior and Resources Settings (Middle)
        3. Evidence Update and Simulation Results (Bottom)
        """
        self.set_stylesheet()

        # 主布局改为垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)
        self.setLayout(main_layout)

        # =============== 第一层布局：执行推演按钮 =================





        # =============== 第二层布局：应急行为设置和应急资源设置 =================
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)
        middle_layout.setContentsMargins(0, 0, 0, 10)

        # 左侧布局：应急行为设置
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(10)

        behavior_group = QGroupBox("应急行为设置")
        behavior_group_layout = QVBoxLayout()
        behavior_group_layout.setContentsMargins(10, 10, 10, 10)
        behavior_group.setMinimumWidth(200)

        self.behaviors = ["救助", "牵引", "抢修", "消防"]
        self.behavior_settings = {}
        for b in self.behaviors:
            cbox_with_label = CustomCheckBoxWithLabel(b)
            cbox_with_label.checkbox.stateChanged.connect(
                partial(self.handle_checkbox_state_changed, behavior=b)
            )
            cbox_with_label.label.clicked.connect(
                partial(self.handle_label_clicked, behavior=b)
            )
            cbox_with_label.duration_changed.connect(self.check_execute_button)
            behavior_group_layout.addWidget(cbox_with_label)
            self.behavior_settings[b] = cbox_with_label

        behavior_group.setLayout(behavior_group_layout)

        left_vbox.addWidget(behavior_group, stretch=1)

        # 右侧布局：应急资源设置
        resource_group = QGroupBox("应急资源设置")
        resource_layout = QVBoxLayout()
        resource_layout.setContentsMargins(10, 10, 10, 10)
        self.resource_stacked_layout = QStackedLayout()

        # Placeholder Widget
        self.placeholder_widget = QWidget()
        ph_layout = QVBoxLayout()
        ph_label = QLabel("请选择应急行为")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_label.setStyleSheet("""
                color: gray;
                font-size: 20pt;
                border-radius: 10px;
                border: 0px solid #c0c0c0;
                background-color: #ffffff;
            """)
        ph_layout.addWidget(ph_label)
        self.placeholder_widget.setLayout(ph_layout)
        self.resource_stacked_layout.addWidget(self.placeholder_widget)

        # Resource Management Widget
        self.resource_management_widget = QWidget()
        res_mgmt_layout = QVBoxLayout()
        res_mgmt_layout.setContentsMargins(0, 0, 0, 0)


        label_btn_layout = QHBoxLayout()
        label_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.current_behavior_label = QLabel("请选择应急行为")
        self.current_behavior_label.setAlignment(Qt.AlignCenter)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:gray;")

        btn_hbox = QHBoxLayout()
        btn_hbox.setContentsMargins(0, 0, 0, 0)
        self.add_resource_btn = QPushButton("添加")
        self.edit_resource_btn = QPushButton("修改")
        self.delete_resource_btn = QPushButton("删除")
        # 创建并配置“执行推演”按钮
        self.execute_btn = QPushButton("执行推演")
        self.execute_btn.setEnabled(False)
        self.execute_btn.setToolTip("请配置应急行为")
        self.execute_btn.setFixedWidth(110)
        self.execute_btn.clicked.connect(self.handle_save)
        self.execute_btn.setStyleSheet("""
            QPushButton:disabled {
                background-color: #d3d3d3;
            }
        """)

        self.add_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/add.png")))
        self.edit_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/edit.png")))
        self.delete_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/delete.png")))

        self.add_resource_btn.setFixedWidth(110)
        self.edit_resource_btn.setFixedWidth(110)
        self.delete_resource_btn.setFixedWidth(110)

        btn_hbox.addWidget(self.add_resource_btn)
        btn_hbox.addWidget(self.edit_resource_btn)
        btn_hbox.addWidget(self.delete_resource_btn)
        btn_hbox.addWidget(self.execute_btn)

        label_btn_layout.addWidget(self.current_behavior_label)
        label_btn_layout.addLayout(btn_hbox)

        res_mgmt_layout.addLayout(label_btn_layout)

        self.resource_table = QTableWidget(0, 4)
        self.resource_table.setHorizontalHeaderLabels(["资源", "类型", "数量", "位置"])
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.setShowGrid(False)
        self.resource_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_table_style(self.resource_table)

        res_mgmt_layout.addWidget(self.resource_table)
        self.resource_management_widget.setLayout(res_mgmt_layout)
        self.resource_stacked_layout.addWidget(self.resource_management_widget)

        resource_layout.addLayout(self.resource_stacked_layout)
        resource_group.setLayout(resource_layout)

        # 将应急资源设置组框添加到middle_layout
        middle_layout.addLayout(left_vbox, stretch=1)
        middle_layout.addWidget(resource_group, stretch=3)

        # 将第二层布局添加到主布局
        main_layout.addLayout(middle_layout, stretch=1)

        # =============== 第三层布局：证据更新和推演结果 =================
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)

        # 左侧布局：证据更新
        evidence_group = QGroupBox("证据更新")
        evidence_group.setMinimumWidth(200)
        evidence_layout = QVBoxLayout()
        evidence_layout.setContentsMargins(10, 20, 10, 10)
        self.evidence_table = CustomTableWidget(0, 3)
        self.evidence_table.setHorizontalHeaderLabels(["要素节点", "状态", "概率"])
        self.evidence_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.evidence_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.evidence_table.setSelectionMode(QTableWidget.SingleSelection)
        self.evidence_table.verticalHeader().setVisible(False)
        self.evidence_table.setAlternatingRowColors(True)
        self.evidence_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.evidence_table.setShowGrid(False)
        self.evidence_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_table_style(self.evidence_table)
        evidence_layout.addWidget(self.evidence_table)
        evidence_group.setLayout(evidence_layout)

        # 右侧布局：推演结果
        simulation_group = QGroupBox("推演结果")
        simulation_layout = QVBoxLayout()
        simulation_layout.setContentsMargins(10, 20, 10, 10)
        self.simulation_table = CustomTableWidget(2, 7)
        self.simulation_table.setShowGrid(False)
        self.simulation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.simulation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.simulation_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.simulation_table.horizontalHeader().setVisible(False)
        self.simulation_table.verticalHeader().setVisible(False)

        # 多级表头：两行
        self.simulation_table.setSpan(0, 0, 2, 1)  # 斜杠"韧性/预案"
        self.simulation_table.setSpan(0, 1, 1, 3)  # "推演前"
        self.simulation_table.setSpan(0, 4, 1, 3)  # "推演后"

        # 自定义表头委托
        header_delegate = FullHeaderDelegate(self.simulation_table)
        for row in range(2):
            for col in range(self.simulation_table.columnCount()):
                self.simulation_table.setItemDelegateForRow(row, header_delegate)

        self.apply_table_style(self.simulation_table)
        self.simulation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        simulation_layout.addWidget(self.simulation_table)
        simulation_group.setLayout(simulation_layout)

        # 将证据更新和推演结果添加到lower_layout
        lower_layout.addWidget(evidence_group, stretch=1)
        lower_layout.addWidget(simulation_group, stretch=3)

        # 将第三层布局添加到主布局
        main_layout.addLayout(lower_layout, stretch=1)

        # =============== 连接按钮（非阻塞模式） =================
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)

    def handle_label_clicked(self, behavior):
        self.check_execute_button()
        cbox = self.behavior_settings[behavior].checkbox
        if not cbox.isChecked():
            cbox.setChecked(True)
        else:
            self.switch_behavior(behavior)
            self.update_label_styles(behavior)

    def handle_checkbox_state_changed(self, state, behavior):
        self.switch_behavior(behavior)
        self.update_label_styles(behavior)
        self.update_resource_dependencies(behavior)
        self.check_execute_button()

    def switch_behavior(self, behavior):
        self.current_behavior = behavior

        self.current_behavior_label.setText(f"正在编辑: {behavior}")
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:#5dade2;")
        self.add_resource_btn.setToolTip(f"添加{behavior}的资源")
        self.edit_resource_btn.setToolTip(f"修改{behavior}的资源")
        self.delete_resource_btn.setToolTip(f"删除{behavior}的资源")
        self.resource_stacked_layout.setCurrentWidget(self.resource_management_widget)
        self.load_resources_for_behavior(behavior)

    def update_label_styles(self, selected_behavior):
        for b, cbl in self.behavior_settings.items():
            cbl.set_selected(b == selected_behavior)

    def update_resource_dependencies(self, behavior):
        self.resource_stacked_layout.setCurrentWidget(self.resource_management_widget)
        self.load_resources_for_behavior(behavior)

    def load_resources_for_behavior(self, behavior):
        self.resource_table.setRowCount(0)
        for r in self.behavior_resources[behavior]:
            self.add_resource_to_table(r, behavior)

    def add_resource_to_table(self, resource, behavior):
        rowpos = self.resource_table.rowCount()
        self.resource_table.insertRow(rowpos)
        self.resource_table.setItem(rowpos,0,QTableWidgetItem(resource["资源"]))
        self.resource_table.setItem(rowpos,1,QTableWidgetItem(resource["类型"]))
        self.resource_table.setItem(rowpos,2,QTableWidgetItem(str(resource["数量"])))
        self.resource_table.setItem(rowpos,3,QTableWidgetItem(resource["位置"]))
        for col in range(4):
            self.resource_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def add_resource(self):
        if not self.current_behavior:
            dlg = CustomWarningDialog("提示","请先选择应急行为")
            dlg.open()  # 非阻塞
            return
        dlg = SingleResourceDialog(parent=self)
        # 当资源对话框点击“确定”时，回调 on_add_resource_ok
        dlg.accepted.connect(lambda: self.on_add_resource_ok(dlg))
        dlg.open()  # 非阻塞

    def on_add_resource_ok(self, dlg):
        r = dlg.get_resource()
        self.behavior_resources[self.current_behavior].append(r)
        self.add_resource_to_table(r, self.current_behavior)
        self.check_execute_button()

    def edit_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            wdlg = CustomWarningDialog("提示","请选择要修改的资源。")
            wdlg.open()
            return
        row = sel[0].row()
        resource = {
            "资源": self.resource_table.item(row,0).text(),
            "类型": self.resource_table.item(row,1).text(),
            "数量": int(self.resource_table.item(row,2).text()),
            "位置": self.resource_table.item(row,3).text()
        }
        dlg = SingleResourceDialog(resource, parent=self)
        dlg.accepted.connect(lambda: self.on_edit_resource_ok(dlg, resource, row))
        dlg.open()

    def on_edit_resource_ok(self, dlg, old_res, row):
        updated = dlg.get_resource()
        try:
            idx = self.behavior_resources[self.current_behavior].index(old_res)
            self.behavior_resources[self.current_behavior][idx] = updated
        except ValueError:
            CustomWarningDialog("提示","未找到要修改的资源。").open()
            return
        self.resource_table.setItem(row,0,QTableWidgetItem(updated["资源"]))
        self.resource_table.setItem(row,1,QTableWidgetItem(updated["类型"]))
        self.resource_table.setItem(row,2,QTableWidgetItem(str(updated["数量"])))
        self.resource_table.setItem(row,3,QTableWidgetItem(updated["位置"]))
        for col in range(4):
            self.resource_table.item(row,col).setTextAlignment(Qt.AlignCenter)
        self.check_execute_button()

    def delete_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            CustomWarningDialog("提示","请选择要删除的资源。").open()
            return
        row = sel[0].row()
        resource = {
            "资源": self.resource_table.item(row,0).text(),
            "类型": self.resource_table.item(row,1).text(),
            "数量": int(self.resource_table.item(row,2).text()),
            "位置": self.resource_table.item(row,3).text()
        }

        qdlg = CustomQuestionDialog("确认删除", f"确定要删除应急行为 '{self.current_behavior}' 下的选中资源吗？", parent=self)
        qdlg.answered.connect(lambda is_ok: self.on_delete_confirmed(is_ok, resource, row))
        qdlg.open()

    def on_delete_confirmed(self, is_ok, resource, row):
        if is_ok:
            try:
                self.behavior_resources[self.current_behavior].remove(resource)
            except ValueError:
                CustomWarningDialog("提示","未找到要删除的资源。").open()
                return
            self.resource_table.removeRow(row)
            self.check_execute_button()

    def check_execute_button(self):
        selected_b = [b for b in self.behaviors if self.behavior_settings[b].checkbox.isChecked()]
        # 检查是否所有应急行为都有资源
        all_checked = any([len(self.behavior_resources[b]) > 0 for b in selected_b])
        # 检查有资源的应急行为是否都有时长
        for b in selected_b:
            if len(self.behavior_resources[b]) > 0:
                duration = self.behavior_settings[b].get_duration()
                if duration == 0:
                    all_checked = False
                    break
        if not all_checked:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip("请配置应急行为")
        else:
            self.execute_btn.setEnabled(all_checked)
            self.execute_btn.setToolTip("请配置应急行为" if not all_checked else "")

    def handle_save(self):
        saved_categories = []
        for b in self.behaviors:
            cbox = self.behavior_settings[b].checkbox
            if cbox.isChecked():
                duration = self.behavior_settings[b].get_duration()
                res_list = self.behavior_resources[b]
                saved_categories.append({
                    "category": b,
                    "attributes": {"时长": f"{duration} 分钟"},
                    "behaviors": res_list
                })
        if not saved_categories:
            dlg = CustomInformationDialog("保存结果","没有要保存的应急行为。", parent=self)
            dlg.open()
            return

        info_html = """
        <html><head><style>
         body{font-family:"Microsoft YaHei";font-size:14px;color:#333}
         h2{text-align:center;color:#0078d7;margin-bottom:20px}
         h3{color:#005a9e;margin-top:30px;margin-bottom:10px}
         table{width:100%;border-collapse:collapse;margin-bottom:20px}
         th,td{border:1px solid #ccc;padding:10px;text-align:center}
         th{background-color:#f0f0f0}
         .no-behavior{color:red;font-style:italic;text-align:center}
        </style></head><body><h2>保存结果详情</h2>
        """
        for item in saved_categories:
            info_html += f"<h3>类别: {item['category']}</h3>"
            info_html += """<b>属性:</b>
            <table><tr><th>属性名称</th><th>属性值</th></tr>"""
            for k,v in item["attributes"].items():
                info_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
            info_html += "</table><b>资源列表:</b>"
            if item["behaviors"]:
                info_html += """<table>
                <tr><th>资源名称</th><th>类型</th><th>数量</th><th>位置</th></tr>"""
                for r in item["behaviors"]:
                    info_html += f"<tr><td>{r['资源']}</td><td>{r['类型']}</td><td>{r['数量']}</td><td>{r['位置']}</td></tr>"
                info_html += "</table>"
            else:
                info_html += "<p class='no-behavior'>无资源</p>"
        info_html += "</body></html>"

        dlg = SaveResultDialog(saved_categories, info_html, parent=self)
        dlg.accepted.connect(lambda: self.on_save_result_confirmed(info_html))
        dlg.open()

    def on_save_result_confirmed(self, info_html):
        # 询问预案名
        input_dlg = CustomInputDialog("预案名称设置","请输入预案名字:",parent=self)
        input_dlg.accepted_text.connect(lambda name: self.on_plan_name_input(name))
        input_dlg.open()

    def on_plan_name_input(self, plan_name):
        plan_name = plan_name.strip()
        if plan_name:
            self.update_evidence_table()
            self.update_simulation_table(plan_name)
            CustomInformationDialog("成功", f"预案 '{plan_name}' 已保存并推演。", parent=self).open()
        else:
            CustomWarningDialog("提示","预案名字不能为空。").exec_()

    def update_evidence_table(self):
        example_data = [
            {"要素节点":"节点1","状态":"正常","概率":"80%"},
            {"要素节点":"节点2","状态":"异常","概率":"20%"},
        ]
        self.evidence_table.clearContents()
        self.evidence_table.setRowCount(0)
        for d in example_data:
            rowpos = self.evidence_table.rowCount()
            self.evidence_table.insertRow(rowpos)
            self.evidence_table.setItem(rowpos,0,QTableWidgetItem(d["要素节点"]))
            self.evidence_table.setItem(rowpos,1,QTableWidgetItem(d["状态"]))
            self.evidence_table.setItem(rowpos,2,QTableWidgetItem(d["概率"]))
            for col in range(3):
                self.evidence_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def update_simulation_table(self, plan_name):
        data = [
            {
                "预案名字": plan_name,
                "推演前-较好":"30%",
                "推演前-中等":"50%",
                "推演前-较差":"20%",
                "推演后-较好":"60%",
                "推演后-中等":"30%",
                "推演后-较差":"10%",
            }
        ]
        for d in data:
            rowpos = self.simulation_table.rowCount()
            self.simulation_table.setRowCount(rowpos+1)
            self.simulation_table.setItem(rowpos,0,QTableWidgetItem(d["预案名字"]))
            self.simulation_table.setItem(rowpos,1,QTableWidgetItem(d["推演前-较好"]))
            self.simulation_table.setItem(rowpos,2,QTableWidgetItem(d["推演前-中等"]))
            self.simulation_table.setItem(rowpos,3,QTableWidgetItem(d["推演前-较差"]))
            self.simulation_table.setItem(rowpos,4,QTableWidgetItem(d["推演后-较好"]))
            self.simulation_table.setItem(rowpos,5,QTableWidgetItem(d["推演后-中等"]))
            self.simulation_table.setItem(rowpos,6,QTableWidgetItem(d["推演后-较差"]))
            for col in range(7):
                self.simulation_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def set_stylesheet(self):
        self.setStyleSheet("""
        QGroupBox {
            border:1px solid #ccc;
            border-radius:8px;
            margin-top:10px;
            font-weight:bold;
            background-color:#fff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding:2px 10px;
            font-weight:bold;
            color:#333;
            background-color:#E8E8E8;
            border-radius:10px;
            border-bottom-left-radius:0;
        }
        QLabel{ color:#333; }
        QCheckBox{ color:#333; }

        QLineEdit, QComboBox, QSpinBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 2px solid #0078d7; /* 蓝色边框 */
        }

        QScrollBar:vertical, QScrollBar:horizontal {
            border:none; background:#f1f1f1; width:8px; height:8px; margin:0;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background:#c1c1c1; min-width:20px; min-height:20px; border-radius:4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            height:0;width:0;subcontrol-origin:margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background:none;
        }
        """)

    def apply_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border:none;
                font-size:14px;
                border-bottom:1px solid black;
                                    background-color: white;
    alternate-background-color: #e9e7e3;
            }
            QHeaderView::section {
                border-top:1px solid black;
                border-bottom:1px solid black;
                background-color:#f0f0f0;
                font-weight:bold;
                padding:4px;
                color:#333;
                text-align:center;
            }
            QTableWidget::item {
                border:none;
                padding:5px;
                text-align:center;
            }
            QTableWidget::item:selected {
                background-color:#cce5ff; color:black; border:none;
            }
            QTableWidget:focus {
                outline:none;
            }
        """)
        table.setAlternatingRowColors(True)

    def reset_inputs(self):
        pass


# ============== 主程序入口 ==============

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionSettingTab()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
