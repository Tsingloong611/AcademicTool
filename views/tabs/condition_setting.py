import json
import os
import sys
from datetime import datetime
from functools import partial
from typing import Dict, Any, List

import requests
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QDialog, QHeaderView, QStackedLayout, QSpinBox, QComboBox, QLineEdit,
    QListWidget, QTextBrowser, QStyleOptionViewItem, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QEvent, QObject, Slot, QUrl
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QIcon
from sqlalchemy.orm import Session

# 假设你的 models / utils / views 路径与本示例一致，这里仅示例。
from models.models import Template, Category
from utils.bn_svg_update import update_with_evidence
from utils.get_config import get_cfg
from utils.plan import PlanData, PlanDataCollector, convert_to_evidence
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.dialogs.llm_dialog import AskLLM

ZH_TO_EN = {
    # Behaviors
    "救助": "Rescue",
    "牵引": "Towing",
    "抢修": "Repair",
    "消防": "Firefighting",

    # Resource types
    "人员": "Personnel",
    "物资": "Materials",
    "车辆": "Vehicles",

    # Personnel categories
    "牵引人员": "Towing Staff",
    "交警": "Traffic Police",
    "医生": "Doctors",
    "消防员": "Firefighters",
    "抢险人员": "Emergency Staff",

    # Vehicle categories
    "牵引车": "Tow Truck",
    "警车": "Police Car",
    "救护车": "Ambulance",
    "消防车": "Fire Truck",
    "融雪车辆": "Snow Removal Vehicle",
    "防汛车辆": "Flood Control Vehicle",
    "封道抢险车": "Road Closure Emergency Vehicle",

    # Material categories
    "随车修理工具": "Vehicle Repair Tools",
    "钢丝绳": "Steel Cable",
    "安全锥": "Safety Cone",
    "撬棒": "Crowbar",
    "黄沙": "Sand",
    "扫帚": "Broom",
    "辅助轮": "Auxiliary Wheel",
    "千斤顶": "Jack",
    "灭火器": "Fire Extinguisher",
    "草包": "Straw Bag",
    "蛇皮袋": "Tarpaulin Bag",
    "融雪剂": "Snow Melting Agent",
    "发电机": "Generator",
    "抽水泵": "Water Pump",
    "医疗物资": "Medical Supplies",

    # UI elements
    "行为": "Action",
    "资源": "Resource",
    "类型": "Type",
    "数量": "Quantity",
    "位置": "Location",
    "应急行为设置": "Emergency Action Settings",
    "应急资源设置": "Emergency Resource Settings",
    "添加": "Add",
    "修改": "Edit",
    "删除": "Delete",
    "执行推演": "Run Simulation",
    "证据更新": "Evidence Updates",
    "推演结果": "Simulation Results",
    # Add more UI text translations as needed
}

TYPE_MAPPING_EN = {
    "Personnel": ["Towing Staff", "Traffic Police", "Doctors", "Firefighters", "Emergency Staff"],
    "Vehicles": ["Tow Truck", "Police Car", "Ambulance", "Fire Truck", "Snow Removal Vehicle", "Flood Control Vehicle", "Road Closure Emergency Vehicle"],
    "Materials": ["Vehicle Repair Tools", "Steel Cable", "Safety Cone", "Crowbar", "Sand", "Broom", "Auxiliary Wheel", "Jack",
                 "Fire Extinguisher", "Straw Bag", "Tarpaulin Bag", "Snow Melting Agent", "Generator", "Water Pump", "Medical Supplies"]
}

# Dictionary for internal processing (English to Chinese)
EN_TO_ZH = {v: k for k, v in ZH_TO_EN.items()}

# ================== 一些通用小组件 ===================

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
    用于 simulation_table 的前两行, 如:
        - row=0 col=1/4 ("推演前/推演后")去掉下边线
        - row=1 col=1..6 ("较好/较差")去掉上边线
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
                painter.drawText(topRect, Qt.AlignCenter, self.tr("韧性"))
                painter.drawText(bottomRect, Qt.AlignCenter, self.tr("预案"))

            elif r == 0 and c == 1:
                # “推演前”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, self.tr("推演前"))

            elif r == 0 and c == 3:
                # “推演后”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, self.tr("推演后"))

            elif r == 0:
                painter.fillRect(option.rect, QColor("#f0f0f0"))

            elif r == 1 and c in [1,2,3,4]:
                # 第二行“较好/较差”，去掉上边线
                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
                text_map = {
                    1:self.tr("较好"), 2:self.tr("较差"),
                    3:self.tr("较好"), 4:self.tr("较差")
                }
                painter.drawText(option.rect, Qt.AlignCenter, text_map[c])

            painter.restore()
        else:
            # row>=2 => 数据行
            super().paint(painter, option, index)

class CustomTableWidget(QTableWidget):
    """自定义表格Widget，用于控制一些 resizeEvent & 样式。"""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        content_width = self.horizontalHeader().length()
        if content_width < 550:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class ClickableLabel(QLabel):
    """可点击的 QLabel，用于联动 CheckBox 等。"""
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()

class CustomCheckBoxWithLabel(QWidget):
    """
    左侧是CheckBox，中间是可点击的Label，右侧有一个时长SpinBox。
    当CheckBox选中时，文字高亮/变蓝，SpinBox可用；否则置灰。
    """
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
        if get_cfg()["i18n"]["language"] == "en_US":
            displayed_text = to_display_text(label_text)
            self.label = ClickableLabel(displayed_text)
        else:
            self.label = ClickableLabel(label_text)
        self.label.setStyleSheet("cursor: pointer;color: black;font-weight: normal;")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 10000)
        self.duration_spin.setSuffix(self.tr(" 分钟"))
        self.duration_spin.setEnabled(False)
        self.duration_spin.setStyleSheet("background-color: #eee;")
        self.duration_spin.setAlignment(Qt.AlignCenter)
        self.duration_spin.valueChanged.connect(self.emit_duration_changed)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(QLabel(self.tr("处置时长:")))
        layout.addWidget(self.duration_spin)

    def emit_duration_changed(self):
        self.duration_changed.emit()

    def set_selected(self, selected):
        """
        选中时(复选框打勾)，高亮文字+启用SpinBox；否则灰色。
        """
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


# ================== 地图对话框 (与原逻辑保持) ===================

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
        self.setWindowTitle(self.tr("高德地图选择"))
        self.resize(800, 600)

        self.selected_lat = 0.0
        self.selected_lng = 0.0

        layout = QVBoxLayout(self)

        self.webview = QWebEngineView(self)
        layout.addWidget(self.webview, stretch=1)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("确定"))
        self.cancel_btn = QPushButton(self.tr("取消"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.channel = QWebChannel(self.webview.page())
        self.bridge = LocationBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        self.bridge.locationSelected.connect(self.on_location_selected)
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)

        center_lat, center_lng = self.get_current_location()

        js_api_key = get_config().get("gaode-map", {}).get("javascript_api_key", "")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{self.tr("高德地图选择")}</title>
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
                        position: lnglat,
                        icon: new AMap.Icon({{
                            // 使用高德地图内置图标
                            image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
                            size: new AMap.Size(25, 34),
                            imageSize: new AMap.Size(25, 34)
                        }}),
                        offset: new AMap.Pixel(-13, -34)
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
            CustomWarningDialog(self.tr("未选择位置"), self.tr("请在地图上点击选择位置。"), self).exec()
            return
        self.accept()

    def get_selected_coordinates(self):
        return self.selected_lat, self.selected_lng

    def get_current_location(self, default_lat=31.0, default_lng=121.0):
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
            print(f"{self.tr('获取当前位置失败')}: {e}")
        return default_lat, default_lng

    def closeEvent(self, event):
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

# ----------------- 读取全局 config.json 的函数 ------------------
def get_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../../config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    database_config = config.get("database", {})
    i18n_config = config.get("i18n", {})
    gaode_map_config = config.get("gaode-map", {})

    print(f"Database username: {database_config.get('username')}")
    print(f"Database host: {database_config.get('host')}")
    print(f"Language: {i18n_config.get('language')}")
    print(f"Gaode Map enabled: {gaode_map_config.get('enable')}")
    return config

def to_display_text(chinese_text):
    """将中文转换为显示用的英文"""
    if isinstance(chinese_text, str):
        return ZH_TO_EN.get(chinese_text, chinese_text)
    return chinese_text

def to_storage_text(english_text):
    """将英文转换为存储用的中文"""
    if isinstance(english_text, str):
        return EN_TO_ZH.get(english_text, english_text)
    return english_text


# ================== 新增/修改资源的对话框：多一个“行为”下拉框 ===================

class SingleResourceDialog(QDialog):
    """
    当点击“确定”时，触发 QDialog.accepted 信号，由父级回调获取资源信息。
    """
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("资源信息"))
        self.resource = resource
        self.online_map_mode = get_config().get("gaode-map", {}).get("enable", False)
        self.init_ui()
        self.resize(600, 360)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # “行为” 的选择下拉
        self.behavior_label = QLabel(self.tr("行为:"))
        if get_cfg()["i18n"]["language"] == "en_US":
            self.behavior_input = create_centered_combobox(["Rescue", "Towing", "Repair", "Firefighting"], "Rescue")
        else:
            self.behavior_input = create_centered_combobox(["救助", "牵引", "抢修", "消防"], "救助")
        layout.addWidget(self.behavior_label)
        layout.addWidget(self.behavior_input)

        self.resource_label = QLabel(self.tr("资源:"))
        if get_cfg()["i18n"]["language"] == "en_US":
            self.resource_input = create_centered_combobox(["Personnel", "Materials", "Vehicles"], "Personnel")
        else:
            self.resource_input = create_centered_combobox(["人员", "物资", "车辆"], "人员")
        self.resource_input.currentTextChanged.connect(self.update_type_options)  # 新增信号连接
        layout.addWidget(self.resource_label)
        layout.addWidget(self.resource_input)

        self.type_label = QLabel(self.tr("类型:"))
        if get_cfg()["i18n"]["language"] == "en_US":
            self.type_input = create_centered_combobox(TYPE_MAPPING_EN["Personnel"], TYPE_MAPPING_EN["Personnel"][0])
        else:
            self.type_input = create_centered_combobox(["类型A", "类型B", "类型C"], "类型A")
        self.update_type_options()  # 初始化类型选项
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_input)

        self.quantity_label = QLabel(self.tr("数量:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setAlignment(Qt.AlignCenter)
        self.quantity_spin.setRange(1, 1000)
        layout.addWidget(self.quantity_label)
        layout.addWidget(self.quantity_spin)

        self.location_label = QLabel(self.tr("位置:"))
        loc_h_layout = QHBoxLayout()
        self.location_input = QLineEdit()
        loc_h_layout.addWidget(self.location_input)

        self.map_button = QPushButton()
        self.map_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/location.png")))
        self.map_button.setStyleSheet("")
        if self.online_map_mode:
            self.map_button.setToolTip(self.tr("点击选择位置"))
            self.map_button.clicked.connect(self.open_map_dialog)
        else:
            self.map_button.setToolTip(self.tr("地图选取功能未启用"))
            self.map_button.setDisabled(True)

        loc_h_layout.addWidget(self.map_button)
        layout.addWidget(self.location_label)
        layout.addLayout(loc_h_layout)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("确定"))
        self.cancel_btn = QPushButton(self.tr("取消"))
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # 如果是修改已有资源，则回填数据
        if self.resource:
            # 获取资源的基本信息（都是中文）
            behavior = self.resource.get("行为", "救助")
            resource_type = self.resource["资源"]
            resource_category = self.resource["类型"]

            if get_cfg()["i18n"]["language"] == "en_US":
                # 英文界面：设置英文显示
                self.behavior_input.setCurrentText(to_display_text(behavior))
                self.resource_input.setCurrentText(to_display_text(resource_type))
                # 类型选项会在update_type_options中更新
            else:
                # 中文界面：直接设置中文
                self.behavior_input.setCurrentText(behavior)
                self.resource_input.setCurrentText(resource_type)
                # 类型选项会在update_type_options中更新

            # 设置数量和位置（不需要翻译）
            self.quantity_spin.setValue(self.resource["数量"])
            self.location_input.setText(self.resource["位置"])

        for i in range(btn_layout.count()):
            btn_layout.itemAt(i).widget().setFixedWidth(50)

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

    def update_type_options(self):
        """根据资源类型更新类型选项"""
        current_resource = self.resource_input.currentText()
        self.type_input.clear()

        # 确保获取中文资源类型
        resource_zh = current_resource
        if get_cfg()["i18n"]["language"] == "en_US":
            resource_zh = to_storage_text(current_resource)

        # 类型映射（中文）
        type_mapping = {
            "人员": ["牵引人员", "交警", "医生", "消防员", "抢险人员"],
            "车辆": ["牵引车", "警车", "救护车", "消防车", "融雪车辆", "防汛车辆", "封道抢险车"],
            "物资": ["随车修理工具", "钢丝绳", "安全锥", "撬棒", "黄沙", "扫帚", "辅助轮", "千斤顶",
                     "灭火器", "草包", "蛇皮袋", "融雪剂", "发电机", "抽水泵", "医疗物资"]
        }

        # 获取中文类型列表
        zh_types = type_mapping.get(resource_zh, [])

        # 根据界面语言填充类型选项
        if get_cfg()["i18n"]["language"] == "en_US":
            # 英文界面：添加英文选项
            for zh_type in zh_types:
                en_type = to_display_text(zh_type)
                self.type_input.addItem(en_type)
        else:
            # 中文界面：添加中文选项
            self.type_input.addItems(zh_types)

        # 如果没有选项，添加一个空选项
        if self.type_input.count() == 0:
            self.type_input.addItem("")

        # 默认选择第一项
        self.type_input.setCurrentIndex(0)

        # 如果是编辑已有资源，尝试找到并选中对应的类型
        if self.resource and "类型" in self.resource:
            zh_type = self.resource["类型"]  # 原始中文类型

            # 检查此中文类型是否在当前资源的有效选项中
            if zh_type in zh_types:
                if get_cfg()["i18n"]["language"] == "en_US":
                    # 英文界面：查找并选中对应的英文类型
                    en_type = to_display_text(zh_type)
                    for i in range(self.type_input.count()):
                        if self.type_input.itemText(i) == en_type:
                            self.type_input.setCurrentIndex(i)
                            break
                else:
                    # 中文界面：查找并选中对应的中文类型
                    for i in range(self.type_input.count()):
                        if self.type_input.itemText(i) == zh_type:
                            self.type_input.setCurrentIndex(i)
                            break

    def open_map_dialog(self):
        map_dlg = MapDialog(self)
        map_dlg.accepted.connect(lambda: self.on_map_accepted(map_dlg))
        map_dlg.open()

    def on_map_accepted(self, map_dlg):
        lat, lng = map_dlg.get_selected_coordinates()
        addr = self.reverse_geocode(lat, lng)
        self.location_input.setText(f"{addr} ({lat},{lng})")

    def reverse_geocode(self, lat, lng):
        web_service_key = get_config().get("gaode-map", {}).get("web_service_key", "")
        url = f"https://restapi.amap.com/v3/geocode/regeo?location={lng},{lat}&key={web_service_key}&radius=1000&extensions=all"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "regeocode" in data:
                return data["regeocode"]["formatted_address"]
        return self.tr("未知地址")

    def get_resource(self):
        """
        返回对话框最终填入的资源信息字典：
          { "行为", "资源", "类型", "数量", "位置" }
        """
        if get_cfg()["i18n"]["language"] == "en_US":
            return {
                "行为": to_storage_text(self.behavior_input.currentText()),
                "资源": to_storage_text(self.resource_input.currentText()),
                "类型": to_storage_text(self.type_input.currentText()),
                "数量": self.quantity_spin.value(),
                "位置": self.location_input.text() or self.tr("未知")
            }
        else:
            return {
            "行为": self.behavior_input.currentText(),
            "资源": self.resource_input.currentText(),
            "类型": self.type_input.currentText(),
            "数量": self.quantity_spin.value(),
            "位置": self.location_input.text() or self.tr("未知")
            }


# ================== 其它辅助对话框 ===================

class DetailsDialog(QDialog):
    def __init__(self, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("详细信息"))
        self.setModal(True)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setHtml(info_html)
        layout.addWidget(self.browser)
        close_btn = QPushButton(self.tr("确定"))
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(110)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(close_btn)
        h.addStretch()
        layout.addLayout(h)
        self.setLayout(layout)
        # 设置滚动条样式
        self.setStyleSheet("""
        QScrollBar:horizontal {
            border: none;
            background: #f1f1f1;
            height: 8px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #c1c1c1;
            min-width: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
                QScrollBar:vertical {
            border: none;
            background: #f1f1f1;
            width: 8px;
            margin: 0px;
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
    """)

class SaveResultDialog(QDialog):
    """
    “已实施的应急行为” + “查看详情”对话框
    """
    def __init__(self, saved_categories, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("实施结果"))
        self.setModal(True)
        self.resize(300, 250)
        main_layout = QVBoxLayout(self)
        lab = QLabel(self.tr("已实施的应急行为:"))
        lab.setFont(QFont("SimSun", 14, QFont.Bold))
        main_layout.addWidget(lab)

        self.listwidget = QListWidget()
        for sc in saved_categories:
            if get_cfg()["i18n"]["language"] == "en_US":
                self.listwidget.addItem(to_display_text(sc["category"]))
            else:
                self.listwidget.addItem(sc["category"])
        main_layout.addWidget(self.listwidget)

        btn_h = QHBoxLayout()
        self.btn_detail = QPushButton(self.tr("查看详情"))
        self.btn_detail.setFixedWidth(85)
        if get_cfg()["i18n"]["language"] == "en_US":
            self.btn_detail.setFixedWidth(120)
        self.btn_detail.clicked.connect(lambda: self.open_detail_dialog(info_html))
        self.btn_ok = QPushButton(self.tr("确定"))
        self.btn_ok.setFixedWidth(85)
        self.btn_ok.clicked.connect(self.accept)
        btn_h.addWidget(self.btn_detail)
        btn_h.addWidget(self.btn_ok)
        main_layout.addLayout(btn_h)
        self.setLayout(main_layout)

    def open_detail_dialog(self, info_html):
        dlg = DetailsDialog(info_html, parent=self)
        dlg.open()


class NegativeIdGenerator:
    """全局负数 ID 生成器，从 -1 开始，每次 -1。"""
    def __init__(self, start: int = -1):
        self.current = start

    def next_id(self) -> int:
        nid = self.current
        self.current -= 1
        return nid


# ============== 主体：ConditionSettingTab(含左右布局 & 行为点击高亮 & 资源表) ==============

class ConditionSettingTab(QWidget):
    """
    包含：
     - 左侧：应急行为设置（checkbox + label + 时长）
     - 右侧：应急资源设置（单个 QTableWidget，首列为“行为”）
     - 下方：证据更新 / 推演结果 表格
     - “执行推演”按钮
    """
    save_requested = Signal()
    save_plan_to_database_signal = Signal(list, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_plan_generator = None  # 外部注入
        self.posterior_probabilities = []
        self.scenario_id = None
        self.session = None
        self.analyzer = None
        self.change_path = None
        self.neg_id_gen = NegativeIdGenerator()

        self.setWindowTitle(self.tr("应急预案设置"))

        # 行为列表+对应UI
        self.behaviors = ["救助", "牵引", "抢修", "消防"]
        self.behavior_settings = {}

        # 资源数据统一在一个表格管理
        self.plans_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency_plans.json")

        self.init_ui()
        self.init_simulation_table()

    def init_ui(self):
        self.set_stylesheet()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)
        self.setLayout(main_layout)

        # =============== 第一层: 应急行为设置(左) + 应急资源设置(右) ===============
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)
        middle_layout.setContentsMargins(0, 0, 0, 10)

        # --- 左侧：应急行为设置 ---
        behavior_group = QGroupBox(self.tr("应急行为设置"))
        behavior_group_layout = QVBoxLayout()
        behavior_group_layout.setContentsMargins(10, 10, 10, 10)
        behavior_group.setMinimumWidth(200)

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
        middle_layout.addWidget(behavior_group, stretch=1)

        # --- 右侧：应急资源设置 ---
        resource_group = QGroupBox(self.tr("应急资源设置"))
        resource_layout = QVBoxLayout()
        resource_layout.setContentsMargins(10, 10, 10, 10)

        # 表格(5列：行为 / 资源 / 类型 / 数量 / 位置)
        self.resource_table = QTableWidget(0, 5)
        self.resource_table.setHorizontalHeaderLabels([
            self.tr("行为"),
            self.tr("资源"),
            self.tr("类型"),
            self.tr("数量"),
            self.tr("位置")
        ])
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.setShowGrid(False)
        self.resource_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_table_style(self.resource_table)

        # 按钮区
        btn_hbox = QHBoxLayout()
        self.add_resource_btn = QPushButton(self.tr("添加"))
        self.edit_resource_btn = QPushButton(self.tr("修改"))
        self.delete_resource_btn = QPushButton(self.tr("删除"))
        self.execute_btn = QPushButton(self.tr("执行推演"))
        self.ask_ai_btn = QPushButton(self.tr("智能问答"))

        self.add_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/add.png")))
        self.edit_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/edit.png")))
        self.delete_resource_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/delete.png")))

        self.add_resource_btn.setFixedWidth(110)
        self.edit_resource_btn.setFixedWidth(110)
        self.delete_resource_btn.setFixedWidth(110)
        self.execute_btn.setFixedWidth(110)
        self.ask_ai_btn.setFixedWidth(110)
        if get_cfg()["i18n"]["language"] == "en_US":
            self.execute_btn.setFixedWidth(160)


        self.execute_btn.setEnabled(False)
        self.execute_btn.setToolTip(self.tr("请配置应急行为"))
        self.execute_btn.clicked.connect(self.handle_save)
        self.execute_btn.setStyleSheet("""
            QPushButton:disabled {
                background-color: #d3d3d3;
            }
        """)

        btn_hbox.addWidget(self.add_resource_btn)
        btn_hbox.addWidget(self.edit_resource_btn)
        btn_hbox.addWidget(self.delete_resource_btn)
        btn_hbox.addWidget(self.execute_btn)
        btn_hbox.addWidget(self.ask_ai_btn)
        self.ask_ai_btn.setToolTip(self.tr("智能问答功能"))
        self.setStyleSheet("""
            QPushButton:disabled {
                background-color: #d3d3d3;
            }
        """)

        resource_layout.addLayout(btn_hbox)
        resource_layout.addWidget(self.resource_table)
        resource_group.setLayout(resource_layout)

        middle_layout.addWidget(resource_group, stretch=3)
        main_layout.addLayout(middle_layout, stretch=1)

        # =============== 第二层: 下方的“证据更新”和“推演结果” ===============
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)

        evidence_group = QGroupBox(self.tr("证据更新"))
        evidence_group.setMinimumWidth(200)
        evidence_layout = QVBoxLayout()
        evidence_layout.setContentsMargins(10, 20, 10, 10)

        self.evidence_table = CustomTableWidget(0, 3)
        self.evidence_table.setHorizontalHeaderLabels([self.tr("要素节点"), self.tr("状态"), self.tr("概率")])
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

        simulation_group = QGroupBox(self.tr("推演结果"))
        simulation_layout = QVBoxLayout()
        simulation_layout.setContentsMargins(10, 20, 10, 10)

        self.simulation_table = CustomTableWidget(2, 5)
        self.simulation_table.setShowGrid(False)
        self.simulation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.simulation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.simulation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.simulation_table.horizontalHeader().setVisible(False)
        self.simulation_table.verticalHeader().setVisible(False)
        self.simulation_table.setSpan(0, 0, 2, 1)
        self.simulation_table.setSpan(0, 1, 1, 2)
        self.simulation_table.setSpan(0, 3, 1, 2)

        header_delegate = FullHeaderDelegate(self.simulation_table)
        for row in range(2):
            for col in range(self.simulation_table.columnCount()):
                self.simulation_table.setItemDelegateForRow(row, header_delegate)

        self.apply_table_style(self.simulation_table)
        self.simulation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        simulation_layout.addWidget(self.simulation_table)
        simulation_group.setLayout(simulation_layout)

        lower_layout.addWidget(evidence_group, stretch=1)
        lower_layout.addWidget(simulation_group, stretch=3)
        main_layout.addLayout(lower_layout, stretch=1)

        # 资源按钮事件
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)
        self.ask_ai_btn.clicked.connect(self.ask_ai)
        self.simulation_table.itemDoubleClicked.connect(self.show_plan_details)
        self.simulation_table.itemClicked.connect(self.on_plan_selected)  # 新增单击事件

        if not get_cfg()['llm']['enable']:
            self.ask_ai_btn.setDisabled(True)
            # 设置悬浮提示
            self.ask_ai_btn.setToolTip(self.tr("智能问答功能未启用"))

    # 新增方法：处理预案选择事件
    def on_plan_selected(self, item):
        """当用户在预案列表单击时触发"""
        row = item.row()
        plan_name_item = self.simulation_table.item(row, 0)
        if not plan_name_item:
            return

        plan_name = plan_name_item.text()
        plan_data = self.plans_data.get(plan_name)
        if not plan_data:
            return

        # 临时阻断信号防止误触发
        for b in self.behaviors:
            self.behavior_settings[b].checkbox.blockSignals(True)

        self.clear_all_inputs()
        self.load_plan_to_ui(plan_data, plan_name)

        # 恢复信号连接并检查按钮状态
        for b in self.behaviors:
            self.behavior_settings[b].checkbox.blockSignals(False)
        self.check_execute_button()

    def clear_all_inputs(self):
        """清空所有输入"""
        # 清空应急行为设置
        for b in self.behaviors:
            self.behavior_settings[b].checkbox.setChecked(False)
            self.behavior_settings[b].duration_spin.setValue(0)
            self.behavior_settings[b].set_selected(False)

        # 清空资源表格
        self.resource_table.setRowCount(0)
        # 清空证据更新表格
        self.evidence_table.setRowCount(0)

    def load_plan_to_ui(self, plan_data, plan_name):
        """将预案数据加载到UI"""
        # 处理应急行为
        print(f"[DEBUG] load plan to ui : {plan_data}")
        for action in plan_data.get("emergency_actions", []):
            action_type = action.get("action_type", "")
            duration_str = action.get("duration", "0 minutes")

            # 先分割获取原始行为名称（中文）
            if "-" in action_type:
                behavior_name = action_type.split("-", 1)[1]  # 只分割一次
            else:
                behavior_name = action_type

            # 检查是否存在对应的行为设置
            if behavior_name not in self.behavior_settings:
                continue

            # 设置行为时长
            try:
                duration = int(duration_str.split()[0])
            except:
                duration = 0

            if action.get("implementation_status", False) == "True":
                self.behavior_settings[behavior_name].checkbox.setChecked(True)
            self.behavior_settings[behavior_name].duration_spin.setValue(duration)
            self.behavior_settings[behavior_name].duration_spin.setEnabled(True)
            self.behavior_settings[behavior_name].duration_spin.setStyleSheet("background-color: white;")

            # 处理关联资源
            for resource in action.get("resources", []):
                resource_type = resource.get("resource_type", "").split("-", 1)[-1]  # 先获取基本资源名称（中文）
                resource_category = resource.get("resource_category", "")

                if get_cfg()['i18n']['language'] == 'en_US':
                    # 界面显示时转换为英文
                    displayed_behavior = to_display_text(behavior_name)
                    displayed_resource = to_display_text(resource_type)
                    displayed_res_type = to_display_text(resource_category)

                    self.add_resource_to_table(
                        behavior=displayed_behavior,
                        resource=displayed_resource,
                        res_type=displayed_res_type,
                        quantity=resource.get("quantity", 0),
                        location=resource.get("location", "")
                    )
                else:
                    self.add_resource_to_table(
                        behavior=behavior_name,
                        resource=resource_type,
                        res_type=resource_category,
                        quantity=resource.get("quantity", 0),
                        location=resource.get("location", "")
                    )

        collector = PlanDataCollector(self.session, scenario_id=self.scenario_id)

        print(f"[DEBUG] Collecting data for plan: {plan_name}")
        plan_data = collector.collect_all_data(plan_name=plan_name)
        print(f"[DEBUG] Plan data: {plan_data}")

        evidence = convert_to_evidence(plan_data)
        print(f"[DEBUG] Evidence: {evidence}")

        output_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"../../data/bn/{self.scenario_id}/plans/{plan_name}"
        ))
        print(f"[DEBUG] Output directory: {output_dir}")
        update_with_evidence(self.analyzer, evidence, output_dir)

        posteriors_file = os.path.join(output_dir, "posterior_probabilities.json")
        posterior_probabilities = {}
        if os.path.exists(posteriors_file):
            with open(posteriors_file, 'r', encoding='utf-8') as f:
                posterior_probabilities = json.load(f)
        print(f"[DEBUG] Posterior probabilities: {posterior_probabilities}")

        self.new_plan_generator.upsert_posterior_probability(plan_name, posterior_probabilities)
        self.posterior_probabilities = self.convert_json_to_posterior_probabilities(posterior_probabilities)
        print(f"[DEBUG] Posterior probabilities: {self.posterior_probabilities}")

        self.update_evidence_table()


    def add_resource_to_table(self, behavior, resource, res_type, quantity, location):
        """向资源表格添加条目"""
        row_pos = self.resource_table.rowCount()
        self.resource_table.insertRow(row_pos)

        items = [
            QTableWidgetItem(behavior),
            QTableWidgetItem(resource),
            QTableWidgetItem(res_type),
            QTableWidgetItem(str(quantity)),
            QTableWidgetItem(location)
        ]

        for col, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            self.resource_table.setItem(row_pos, col, item)

    # ============= 行为勾选/点击：高亮 & 开启时长设置 =============

    def handle_label_clicked(self, behavior):
        """
        用户点击行为文本时，如果没有勾选就勾选它（以使文字变蓝、时长可设置），否则不取消勾选。
        """
        cbox = self.behavior_settings[behavior].checkbox
        if not cbox.isChecked():
            cbox.setChecked(True)
        self.check_execute_button()

    def handle_checkbox_state_changed(self, state, behavior):
        """
        当行为复选框改变时，设置高亮、刷新可执行状态。
        """
        print(f"行为 {behavior} 的复选框状态改变为 {state}")
        is_checked = (state == 2)
        self.behavior_settings[behavior].set_selected(is_checked)
        self.check_execute_button()

    # ============= 资源表格(统一管理) =============

    def add_resource(self):
        dlg = SingleResourceDialog(parent=self)
        dlg.accepted.connect(lambda: self.on_add_resource_ok(dlg))
        dlg.open()

    def on_add_resource_ok(self, dlg):
        r = dlg.get_resource()  # dict: { "行为", "资源", "类型", "数量", "位置" }
        rowpos = self.resource_table.rowCount()
        self.resource_table.insertRow(rowpos)
        if get_cfg()["i18n"]["language"] == "en_US":
            self.resource_table.setItem(rowpos, 0, QTableWidgetItem(to_display_text(r["行为"])))
            self.resource_table.setItem(rowpos, 1, QTableWidgetItem(to_display_text(r["资源"])))
            self.resource_table.setItem(rowpos, 2, QTableWidgetItem(to_display_text(r["类型"])))
        else:
            self.resource_table.setItem(rowpos, 0, QTableWidgetItem(r["行为"]))
            self.resource_table.setItem(rowpos, 1, QTableWidgetItem(r["资源"]))
            self.resource_table.setItem(rowpos, 2, QTableWidgetItem(r["类型"]))
        self.resource_table.setItem(rowpos, 3, QTableWidgetItem(str(r["数量"])))
        self.resource_table.setItem(rowpos, 4, QTableWidgetItem(r["位置"]))
        for col in range(5):
            self.resource_table.item(rowpos, col).setTextAlignment(Qt.AlignCenter)
        self.check_execute_button()

    def edit_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            CustomWarningDialog(self.tr("提示"), self.tr("请选择要修改的资源。")).open()
            return

        row = sel[0].row()

        # 构建资源字典
        if get_cfg()["i18n"]["language"] == "en_US":
            # 英文界面：需要将表格中的英文转换为中文存储
            resource = {
                "行为": to_storage_text(self.resource_table.item(row, 0).text()),
                "资源": to_storage_text(self.resource_table.item(row, 1).text()),
                "类型": to_storage_text(self.resource_table.item(row, 2).text()),
                "数量": int(self.resource_table.item(row, 3).text()),
                "位置": self.resource_table.item(row, 4).text()
            }
        else:
            # 中文界面：直接使用表格中的中文
            resource = {
                "行为": self.resource_table.item(row, 0).text(),
                "资源": self.resource_table.item(row, 1).text(),
                "类型": self.resource_table.item(row, 2).text(),
                "数量": int(self.resource_table.item(row, 3).text()),
                "位置": self.resource_table.item(row, 4).text()
            }

        dlg = SingleResourceDialog(resource, parent=self)
        dlg.accepted.connect(lambda: self.on_edit_resource_ok(dlg, row))
        dlg.open()

    def on_edit_resource_ok(self, dlg, row):
        updated = dlg.get_resource()  # 获取资源（中文格式）

        if get_cfg()["i18n"]["language"] == "en_US":
            # 英文界面：设置英文显示
            self.resource_table.setItem(row, 0, QTableWidgetItem(to_display_text(updated["行为"])))
            self.resource_table.setItem(row, 1, QTableWidgetItem(to_display_text(updated["资源"])))
            self.resource_table.setItem(row, 2, QTableWidgetItem(to_display_text(updated["类型"])))
        else:
            # 中文界面：直接设置中文
            self.resource_table.setItem(row, 0, QTableWidgetItem(updated["行为"]))
            self.resource_table.setItem(row, 1, QTableWidgetItem(updated["资源"]))
            self.resource_table.setItem(row, 2, QTableWidgetItem(updated["类型"]))

        # 数量和位置不需要翻译
        self.resource_table.setItem(row, 3, QTableWidgetItem(str(updated["数量"])))
        self.resource_table.setItem(row, 4, QTableWidgetItem(updated["位置"]))

        # 设置文本对齐
        for col in range(5):
            self.resource_table.item(row, col).setTextAlignment(Qt.AlignCenter)

        self.check_execute_button()

    def delete_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            CustomWarningDialog(self.tr("提示"), self.tr("请选择要删除的资源。")).open()
            return
        row = sel[0].row()
        resource_behavior = self.resource_table.item(row, 0).text()
        resource_name = self.resource_table.item(row, 1).text()

        qdlg = CustomQuestionDialog(
            self.tr("确认删除"),
            self.tr("确定要删除【") + resource_behavior + self.tr("】行为下的资源：") + resource_name + "？",
            parent=self
        )
        qdlg.accepted.connect(lambda: self.on_delete_confirmed(True, row))
        qdlg.open()

    def on_delete_confirmed(self, is_ok, row):
        if is_ok:
            self.resource_table.removeRow(row)
            self.check_execute_button()

    # ============= 推演按钮可用性检查 =============

    def check_execute_button(self):
        """
        只有当用户至少勾选了一个行为，且勾选的行为都设置了时长>0，并且每个勾选行为在表格里至少有1条资源，才可执行推演。
        """
        selected_behaviors = [
            b for b in self.behaviors
            if self.behavior_settings[b].checkbox.isChecked()
        ]
        if not selected_behaviors:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip(self.tr("请配置应急行为"))
            return

        # 检查时长 > 0
        all_have_duration = all(self.behavior_settings[b].get_duration() > 0 for b in selected_behaviors)
        if not all_have_duration:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip(self.tr("请给已勾选的行为设置时长"))
            return

        # 检查表格资源
        behaviors_in_table = []
        for row in range(self.resource_table.rowCount()):
            bh = self.resource_table.item(row, 0).text()
            # 如果是英文界面，需要将表格中的英文行为名称转换为中文进行比较
            if get_cfg()["i18n"]["language"] == "en_US":
                bh = to_storage_text(bh)  # 将英文转为中文

            if bh not in behaviors_in_table:
                behaviors_in_table.append(bh)

        # 要求每个选中的行为都在表格里至少有1行
        all_have_resources = all(b in behaviors_in_table for b in selected_behaviors)
        if not all_have_resources:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip(self.tr("勾选行为需在表格中添加资源"))
            return

        # 满足即可
        self.execute_btn.setEnabled(True)
        self.execute_btn.setToolTip("")

    # ============= 执行推演：保存 & 弹窗 & 输入预案名 & BN分析 =============

    def handle_save(self):
        selected_behaviors = [
            b for b in self.behaviors
            if self.behavior_settings[b].checkbox.isChecked()
        ]
        if not selected_behaviors:
            CustomInformationDialog(self.tr("保存结果"), self.tr("没有要保存的应急行为。"), parent=self).open()
            return

        # 整理在弹窗中显示的概览信息
        saved_categories = []
        for b in selected_behaviors:
            duration = self.behavior_settings[b].get_duration()
            b_resources = []
            # 收集表格里本行为对应的资源
            for row in range(self.resource_table.rowCount()):
                for row in range(self.resource_table.rowCount()):
                    table_behavior = self.resource_table.item(row, 0).text()

                    # 如果是英文界面，将表格中的行为名称转换为中文进行比较
                    if get_cfg()["i18n"]["language"] == "en_US":
                        if to_storage_text(table_behavior) == b:
                            r = {
                                "资源": self.resource_table.item(row, 1).text(),
                                "类型": self.resource_table.item(row, 2).text(),
                                "数量": int(self.resource_table.item(row, 3).text()),
                                "位置": self.resource_table.item(row, 4).text()
                            }
                            b_resources.append(r)
                    else:
                        if table_behavior == b:
                            r = {
                                "资源": self.resource_table.item(row, 1).text(),
                                "类型": self.resource_table.item(row, 2).text(),
                                "数量": int(self.resource_table.item(row, 3).text()),
                                "位置": self.resource_table.item(row, 4).text()
                            }
                            b_resources.append(r)

            saved_categories.append({
                "category": b,
                "attributes": {self.tr("时长"): f"{duration} {self.tr('分钟')}"},
                "behaviors": b_resources
            })

        info_html = """
        <html><head><style>
         body{font-family:"Microsoft YaHei";font-size:14px;color:#333}
         h2{text-align:center;color:#0078d7;margin-bottom:20px}
         h3{color:#005a9e;margin-top:30px;margin-bottom:10px}
         table{width:100%;border-collapse:collapse;margin-bottom:20px}
         th,td{border:1px solid #ccc;padding:10px;text-align:center}
         th{background-color:#f0f0f0}
         .no-behavior{color:red;font-style:italic;text-align:center}
        </style></head><body><h2>""" + self.tr("保存结果详情") + """</h2>
        """
        print(f"[DEBUG] Saved categories: {saved_categories}")
        for item in saved_categories:
            if get_cfg()["i18n"]["language"] == "en_US":
                info_html += self.tr("<h3>类别: ")+f"{to_display_text(item['category'])}</h3>"
            else:
                info_html += self.tr("<h3>类别: ")+f"{item['category']}</h3>"
            info_html += """<b>""" + self.tr("属性") + """:</b>
            <table><tr><th>""" + self.tr("属性名称") + """</th><th>""" + self.tr("属性值") + """</th></tr>"""
            for k,v in item["attributes"].items():
                info_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
            info_html += "</table><b>" + self.tr("资源列表") + ":</b>"
            if item["behaviors"]:
                info_html += """
                <table>
                <tr><th>""" + self.tr("资源名称") + """</th><th>""" + self.tr("类型") + """</th><th>""" + self.tr("数量") + """</th><th>""" + self.tr("位置") + """</th></tr>
                """
                for r in item["behaviors"]:
                    info_html += f"<tr><td>{r['资源']}</td><td>{r['类型']}</td><td>{r['数量']}</td><td>{r['位置']}</td></tr>"
                info_html += "</table>"
            else:
                info_html += "<p class='no-behavior'>" + self.tr("无资源") + "</p>"
        info_html += "</body></html>"

        dlg = SaveResultDialog(saved_categories, info_html, parent=self)
        dlg.accepted.connect(lambda: self.on_save_result_confirmed(info_html))
        dlg.open()

    def on_save_result_confirmed(self, info_html):
        """
        用户在“实施结果”对话框点确定后，再让他输入预案名称。
        """
        input_dlg = CustomInputDialog(self.tr("预案名称设置"), self.tr("请输入预案名字:"), parent=self)
        input_dlg.accepted_text.connect(lambda name: self.on_plan_name_input(name))
        input_dlg.open()

    def on_plan_name_input(self, plan_name):
        plan_name = plan_name.strip()
        if not plan_name:
            CustomWarningDialog(self.tr("提示"), self.tr("预案名字不能为空。"), parent=self).open()
            return

        plan_data = self.format_plan_as_json(plan_name)
        print(f"[DEBUG] Plan data: {plan_data}")
        self.create_plan(plan_name, plan_data)

        # 收集并执行 BN 推演
        collector = PlanDataCollector(self.session, scenario_id=self.scenario_id)
        print(f"[DEBUG] Collecting data for plan: {plan_name}")
        collected_data = collector.collect_all_data(plan_name=plan_name)
        print(f"[DEBUG] Collected plan data: {collected_data}")

        evidence = convert_to_evidence(collected_data)
        print(f"[DEBUG] Evidence: {evidence}")

        output_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"../../data/bn/{self.scenario_id}/plans/{plan_name}"
        ))
        print(f"[DEBUG] Output directory: {output_dir}")
        update_with_evidence(self.analyzer, evidence, output_dir)

        posteriors_file = os.path.join(output_dir, "posterior_probabilities.json")
        posterior_probabilities = {}
        if os.path.exists(posteriors_file):
            with open(posteriors_file, 'r', encoding='utf-8') as f:
                posterior_probabilities = json.load(f)
        print(f"[DEBUG] Posterior probabilities: {posterior_probabilities}")

        # 存数据库 (后验概率)
        self.new_plan_generator.upsert_posterior_probability(plan_name, posterior_probabilities)
        self.posterior_probabilities = self.convert_json_to_posterior_probabilities(posterior_probabilities)
        print(f"[DEBUG] Posterior probabilities: {self.posterior_probabilities}")
        self.update_evidence_table()

        if self.load_saved_plans():
            CustomInformationDialog(
                self.tr("成功"),
                self.tr("预案 '") + plan_name + self.tr("' 已保存并推演。"),
                parent=self
            ).open()
        else:
            CustomWarningDialog(
                self.tr("错误"),
                self.tr("保存预案时出现错误。"),
                parent=self
            ).open()

    def format_plan_as_json(self, plan_name):
        """
        将当前勾选的行为和表格资源整理成最终 plan_data。
        在“行为”与“资源”名称前都加上 {plan_name}- 前缀。
        """
        selected_behaviors = [
            b for b in self.behaviors
            if self.behavior_settings[b].checkbox.isChecked()
        ]
        plan_data = {
            "plan_name": plan_name,
            "emergency_actions": [],
            "simulation_results": {
                "推演前-较好": "30%",
                "推演前-较差": "20%",
                "推演后-较好": "60%",
                "推演后-较差": "10%"
            }
        }

        for b in self.behaviors:
            duration = self.behavior_settings[b].get_duration()
            b_resources = []
            # 找到表格中属于 b 的资源
            for row in range(self.resource_table.rowCount()):
                if get_cfg()["i18n"]["language"] == "en_US":
                    if to_storage_text(self.resource_table.item(row, 0).text()) == b:
                        res_name = to_storage_text(self.resource_table.item(row, 1).text())
                        res_type = to_storage_text(self.resource_table.item(row, 2).text())
                        quantity = int(self.resource_table.item(row, 3).text())
                        location = self.resource_table.item(row, 4).text()
                        resource_data = {
                            "resource_type": f"{plan_name}-{res_name}",
                            "resource_category": res_type,
                            "quantity": quantity,
                            "location": location
                        }
                        b_resources.append(resource_data)
                else:
                    if self.resource_table.item(row, 0).text() == b:
                        res_name = self.resource_table.item(row, 1).text()
                        res_type = self.resource_table.item(row, 2).text()
                        quantity = int(self.resource_table.item(row, 3).text())
                        location = self.resource_table.item(row, 4).text()
                        resource_data = {
                            "resource_type": f"{plan_name}-{res_name}",
                            "resource_category": res_type,
                            "quantity": quantity,
                            "location": location
                        }
                        b_resources.append(resource_data)

            if b_resources:
                action_data = {
                    "action_type": f"{plan_name}-{b}",
                    "duration": f"{duration} minutes",
                    "implementation_status": "True" if b in selected_behaviors else "False",
                    "resources": b_resources
                }
                plan_data["emergency_actions"].append(action_data)

        return plan_data

    def create_plan(self, name, plan_data) -> Dict[int, Any]:
        """
        将 plan_data 发射信号给外部存DB，或由self.new_plan_generator逻辑处理。
        """
        new_plan_data = self.new_plan_generator.build_plan_structure(plan_data)
        print(f"[DEBUG] New plan data: {new_plan_data}")
        saved_plan = []
        for entity_id, entity in new_plan_data.items():
            saved_plan.append(entity)
        self.save_plan_to_database_signal.emit(saved_plan, False)
        return new_plan_data

    # ============= simulation_table 相关 =============

    def init_simulation_table(self):
        self.simulation_table_clear_header()

    def simulation_table_clear_header(self):
        """
        初始化 simulation_table 的两行多级表头
        """
        self.simulation_table.clearContents()
        self.simulation_table.setRowCount(2)

        self.simulation_table.setSpan(0, 0, 2, 1)  # "韧性/预案"
        self.simulation_table.setSpan(0, 1, 1, 2)  # "推演前"
        self.simulation_table.setSpan(0, 3, 1, 2)  # "推演后"

        # 创建空item占位
        for col in range(5):
            if self.simulation_table.item(0, col) is None:
                self.simulation_table.setItem(0, col, QTableWidgetItem(""))
            if self.simulation_table.item(1, col) is None:
                self.simulation_table.setItem(1, col, QTableWidgetItem(""))

        header_delegate = FullHeaderDelegate(self.simulation_table)
        for row in range(2):
            for col in range(self.simulation_table.columnCount()):
                self.simulation_table.setItemDelegateForRow(row, header_delegate)

    def load_saved_plans(self):
        """
        读取已保存的所有预案, 并更新 simulation_table
        """
        try:
            self.simulation_table_clear_header()
            print(f"[DEBUG] Loading plans from file: {self.change_path}")
            self.plans_data = self.new_plan_generator.get_all_plans(change_path=self.change_path)
            print(f"[DEBUG] Loaded plans: {self.plans_data}")

            for plan_name, plan_data in self.plans_data.items():
                self.add_plan_to_simulation_table(plan_name, plan_data)
            return True
        except Exception as e:
            print(f"Error loading plans: {str(e)}")
            CustomWarningDialog(
                self.tr("错误"),
                self.tr("加载预案数据时出现错误：") + str(e),
                parent=self
            ).open()

    def add_plan_to_simulation_table(self, plan_name, plan_data):
        """
        将单个预案显示在 simulation_table(追加到末尾)
        """
        current_data_rows = self.simulation_table.rowCount() - 2
        new_row = current_data_rows + 2
        self.simulation_table.insertRow(new_row)

        self.simulation_table.setItem(new_row, 0, QTableWidgetItem(plan_name))
        self.simulation_table.item(new_row, 0).setTextAlignment(Qt.AlignCenter)

        sim_res = plan_data.get("simulation_results", {
            "推演前-较好": "30%",
            "推演前-较差": "20%",
            "推演后-较好": "60%",
            "推演后-较差": "10%"
        })
        print(f"[DEBUG] Simulation results: {sim_res}")
        columns = [
            sim_res["推演前-较好"],
            sim_res["推演前-较差"],
            sim_res["推演后-较好"],
            sim_res["推演后-较差"]
        ]
        for col, val in enumerate(columns, start=1):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            self.simulation_table.setItem(new_row, col, item)

    def show_plan_details(self, item):
        """
        双击 simulation_table 某行 => 显示预案详情对话框 & 计算后验概率
        """
        row = item.row()
        plan_name = self.simulation_table.item(row, 0).text()
        collector = PlanDataCollector(self.session, scenario_id=self.scenario_id)

        print(f"[DEBUG] Collecting data for plan: {plan_name}")
        plan_data = collector.collect_all_data(plan_name=plan_name)
        print(f"[DEBUG] Plan data: {plan_data}")

        evidence = convert_to_evidence(plan_data)
        print(f"[DEBUG] Evidence: {evidence}")

        output_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"../../data/bn/{self.scenario_id}/plans/{plan_name}"
        ))
        print(f"[DEBUG] Output directory: {output_dir}")
        update_with_evidence(self.analyzer, evidence, output_dir)

        posteriors_file = os.path.join(output_dir, "posterior_probabilities.json")
        posterior_probabilities = {}
        if os.path.exists(posteriors_file):
            with open(posteriors_file, 'r', encoding='utf-8') as f:
                posterior_probabilities = json.load(f)
        print(f"[DEBUG] Posterior probabilities: {posterior_probabilities}")

        self.new_plan_generator.upsert_posterior_probability(plan_name, posterior_probabilities)
        self.posterior_probabilities = self.convert_json_to_posterior_probabilities(posterior_probabilities)
        print(f"[DEBUG] Posterior probabilities: {self.posterior_probabilities}")

        self.update_evidence_table()

        if plan_name in self.plans_data:
            plan_data = self.plans_data[plan_name]
            info_html = self.generate_plan_details_html(plan_data)
            details_dialog = DetailsDialog(info_html, self)
            details_dialog.setWindowTitle(self.tr("预案详情 - ") + plan_name)
            details_dialog.open()

    def generate_plan_details_html(self, plan_data):
        info_html = """
        <html><head><style>
         body{font-family:"Microsoft YaHei";font-size:14px;color:#333}
         h2{text-align:center;color:#0078d7;margin-bottom:20px}
         h3{color:#005a9e;margin-top:30px;margin-bottom:10px}
         .timestamp{color:#666;font-size:12px;text-align:right;margin-bottom:20px}
         table{width:100%;border-collapse:collapse;margin-bottom:20px}
         th,td{border:1px solid #ccc;padding:10px;text-align:center}
         th{background-color:#f0f0f0}
         .no-resource{color:red;font-style:italic;text-align:center}
        </style></head><body>
        """
        info_html += f"<h2> {plan_data.get('plan_name','')}</h2>"
        create_time_str = self.tr('创建时间') + ": " + plan_data.get('timestamp', '')
        info_html += f"<div class='timestamp'>{create_time_str}</div>"

        for action in plan_data.get('emergency_actions', []):
            if action.get('implementation_status') == 'True':
                if get_cfg()['i18n']['language'] == 'en_US':
                    title_str_raw = self.tr('应急行为') + ": " + to_display_text(action.get('action_type', '')) + " (" + self.tr('已实施') + ")"
                    title_str = f"<h3>{title_str_raw}</h3>"
                else:
                    title_str_raw = self.tr('应急行为') + ": " + action.get('action_type', '') + " (" + self.tr('已实施') + ")"
                    title_str = f"<h3>{title_str_raw}</h3>"
            else:
                if get_cfg()['i18n']['language'] == 'en_US':
                    title_str_raw = self.tr('应急行为') + ": " + to_display_text(action.get('action_type', '')) + " (" + self.tr('未实施') + ")"
                    title_str = f"<h3>{title_str_raw}</h3>"
                else:
                    title_str_raw = self.tr('应急行为') + ": " + action.get('action_type', '') + " (" + self.tr('未实施') + ")"
                    title_str = f"<h3>{title_str_raw}</h3>"

            info_html += f"{title_str}"
            info_html += f"<p><b>{self.tr('时长')}:</b> {action.get('duration','')}</p>"

            info_html += f"<b>{self.tr('资源列表')}:</b>"
            if action.get('resources'):
                info_html += """
                <table>
                <tr>
                    <th>""" + self.tr('资源名称') + """</th>
                    <th>""" + self.tr('类型') + """</th>
                    <th>""" + self.tr('数量') + """</th>
                    <th>""" + self.tr('位置') + """</th>
                </tr>
                """
                for resource in action['resources']:
                    if get_cfg()['i18n']['language'] == 'en_US':
                        displayed_resource = to_display_text(resource.get('resource_type',''))
                        displayed_res_type = to_display_text(resource.get('resource_category',''))
                        info_html += f"""
                        <tr>
                            <td>{displayed_resource}</td>
                            <td>{displayed_res_type}</td>
                            <td>{resource.get('quantity','')}</td>
                            <td>{resource.get('location','')}</td>
                        </tr>
                        """
                    else:
                        info_html += f"""
                        <tr>
                            <td>{resource.get('resource_type','')}</td>
                            <td>{resource.get('resource_category','')}</td>
                            <td>{resource.get('quantity','')}</td>
                            <td>{resource.get('location','')}</td>
                        </tr>
                        """
                info_html += "</table>"
            else:
                info_html += f"<p class='no-resource'>{self.tr('无资源')}</p>"


        info_html += "</body></html>"
        return info_html

    def convert_json_to_posterior_probabilities(self, json_data):
        """
        将 posterior_probabilities.json 的 dict 转成 [ {要素节点, 状态, 概率}, ... ] 便于表格显示
        """
        posterior_probabilities = []
        for element_node, states in json_data.items():
            for state, probability in states.items():
                probability_percentage = f"{probability*100:.2f}%"
                entry = {
                    "要素节点": element_node,
                    "状态": state,
                    "概率": probability_percentage
                }
                posterior_probabilities.append(entry)
        return posterior_probabilities

    def update_evidence_table(self):
        self.evidence_table.clearContents()
        self.evidence_table.setRowCount(0)
        self.evidence_table.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
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
        """)

        # 水平滚动条样式（如果有的话）
        self.evidence_table.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: #f1f1f1;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        for d in self.posterior_probabilities:
            if d.get("要素节点") not in ["ScenarioResilience"]:
                if get_cfg()["i18n"]["language"] == "en_US":
                    rowpos = self.evidence_table.rowCount()
                    self.evidence_table.insertRow(rowpos)
                    self.evidence_table.setItem(rowpos, 0, QTableWidgetItem(to_display_text(d.get("要素节点",""))))
                    self.evidence_table.setItem(rowpos, 1, QTableWidgetItem(to_display_text(d.get("状态",""))))
                    self.evidence_table.setItem(rowpos, 2, QTableWidgetItem(d.get("概率","")))
                    for col in range(3):
                        self.evidence_table.item(rowpos, col).setTextAlignment(Qt.AlignCenter)
                        self.evidence_table.item(rowpos, col).setToolTip(self.evidence_table.item(rowpos, col).text())
                else:
                    rowpos = self.evidence_table.rowCount()
                    self.evidence_table.insertRow(rowpos)
                    self.evidence_table.setItem(rowpos, 0, QTableWidgetItem(d.get("要素节点","")))
                    self.evidence_table.setItem(rowpos, 1, QTableWidgetItem(d.get("状态","")))
                    self.evidence_table.setItem(rowpos, 2, QTableWidgetItem(d.get("概率","")))
                    for col in range(3):
                        self.evidence_table.item(rowpos, col).setTextAlignment(Qt.AlignCenter)
                        self.evidence_table.item(rowpos, col).setToolTip(self.evidence_table.item(rowpos, col).text())


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
            border: 2px solid #0078d7;
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

    def ask_ai(self):
        if self.plans_data:
            ask_ai_dialog = AskLLM(self,self.plans_data)
            ask_ai_dialog.exec_()
        else:
            ask_ai_dialog = AskLLM(self)
            ask_ai_dialog.exec_()


# ===== 测试入口，仅供本地运行时参考 =====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionSettingTab()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
