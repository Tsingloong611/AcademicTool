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
    QListWidget, QTextBrowser, QStyleOptionViewItem, QStyledItemDelegate, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent, QObject, Slot, QUrl
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QIcon
from sqlalchemy.orm import Session

from models.models import Template, Category
from utils.bn_svg_update import update_with_evidence
from utils.plan import PlanData, evidence, PlanDataCollector, convert_to_evidence
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
                painter.drawText(topRect, Qt.AlignCenter, self.tr("韧性"))
                painter.drawText(bottomRect, Qt.AlignCenter, self.tr("预案"))

            elif r == 0 and c == 1:
                # “推演前”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, self.tr("推演前"))

            elif r == 0 and c == 4:
                # “推演后”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                painter.drawText(option.rect, Qt.AlignCenter, self.tr("推演后"))

            elif r == 0:
                painter.fillRect(option.rect, QColor("#f0f0f0"))

            elif r == 1 and c in [1,2,3,4,5,6]:
                # 第二行“较好/中等/较差”，去掉上边线
                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
                text_map = {
                    1:self.tr("较好"), 2:self.tr("中等"), 3:self.tr("较差"),
                    4:self.tr("较好"), 5:self.tr("中等"), 6:self.tr("较差")
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

        self.label = ClickableLabel(self.tr(label_text))
        self.label.setStyleSheet("cursor: pointer;color: black;font-weight: normal;")
        self.label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0,10000)
        self.duration_spin.setSuffix(self.tr(" 分钟"))
        self.duration_spin.setEnabled(False)
        self.duration_spin.setStyleSheet("background-color: #eee;")
        self.duration_spin.setAlignment(Qt.AlignCenter)
        self.duration_spin.valueChanged.connect(self.emit_duration_changed)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(QLabel(self.tr("时长:")))
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
            QMessageBox.warning(self, self.tr("未选择位置"), self.tr("请在地图上点击选择位置。"))
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

class SingleResourceDialog(QDialog):
    """
    改用 open() 显示，不用 exec()。保留原先布局和样式。
    当点击“确定”时，触发 QDialog.accepted 信号，由父级回调获取资源信息。
    """
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("资源信息"))
        self.resource = resource
        self.online_map_mode = get_config().get("gaode-map", {}).get("enable", False)
        self.init_ui()
        self.resize(600, 300)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.resource_label = QLabel(self.tr("资源:"))
        self.resource_input = create_centered_combobox(["人员", "物资", "车辆"], "人员")
        layout.addWidget(self.resource_label)
        layout.addWidget(self.resource_input)

        self.type_label = QLabel(self.tr("类型:"))
        self.type_input = create_centered_combobox(["类型A", "类型B", "类型C"], "类型A")
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_input)

        self.quantity_label = QLabel(self.tr("数量:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setAlignment(Qt.AlignCenter)
        self.quantity_spin.setRange(1,1000)
        layout.addWidget(self.quantity_label)
        layout.addWidget(self.quantity_spin)

        self.location_label = QLabel(self.tr("位置:"))
        loc_h_layout = QHBoxLayout()
        self.location_input = QLineEdit()
        loc_h_layout.addWidget(self.location_input)

        self.map_button = QPushButton()
        self.map_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../resources/icons/location.png")))
        self.map_button.setStyleSheet(""" """)
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

        if self.resource:
            self.resource_input.setCurrentText(self.resource["资源"])
            self.type_input.setCurrentText(self.resource["类型"])
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

    def open_map_dialog(self):
        map_dlg = MapDialog(self)
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
            "位置": self.location_input.text() or self.tr("未知")
        }

    def reverse_geocode(self, lat, lng):
        web_service_key = get_config().get("gaode-map", {}).get("web_service_key", "")
        url = f"https://restapi.amap.com/v3/geocode/regeo?location={lng},{lat}&key={web_service_key}&radius=1000&extensions=all"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "regeocode" in data:
                return data["regeocode"]["formatted_address"]
        return self.tr("未知地址")


class DetailsDialog(QDialog):
    def __init__(self, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("详细信息"))
        self.setModal(True)
        self.resize(600,400)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setHtml(info_html)
        layout.addWidget(self.browser)
        close_btn = QPushButton(self.tr("确定"))
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
        self.setWindowTitle(self.tr("实施结果"))
        self.setModal(True)
        self.resize(300,250)
        main_layout = QVBoxLayout(self)
        lab = QLabel(self.tr("已实施的应急行为:"))
        lab.setFont(QFont("SimSun",14,QFont.Bold))
        main_layout.addWidget(lab)

        self.listwidget = QListWidget()
        for sc in saved_categories:
            self.listwidget.addItem(sc["category"])
        main_layout.addWidget(self.listwidget)

        btn_h = QHBoxLayout()
        self.btn_detail = QPushButton(self.tr("查看详情"))
        self.btn_detail.setFixedWidth(85)
        self.btn_detail.clicked.connect(lambda: self.open_detail_dialog(info_html))
        self.btn_ok = QPushButton(self.tr("确定"))
        self.btn_ok.setFixedWidth(50)
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

class ConditionSettingTab(QWidget):
    save_requested = Signal()
    save_plan_to_database_signal = Signal(list,bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_plan_generator = None
        self.posterior_probabilities = []
        self.scenario_id = None
        self.session = None
        self.analyzer = None
        self.neg_id_gen = NegativeIdGenerator()
        self.setWindowTitle(self.tr("应急预案设置"))
        self.behavior_resources = {b:[] for b in ["救助","牵引","抢修","消防"]}
        self.current_behavior = None
        self.plans_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency_plans.json")
        self.init_ui()
        self.init_simulation_table()  # 初始化表格结构


    def init_ui(self):
        self.set_stylesheet()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 0, 20, 10)
        self.setLayout(main_layout)

        # =============== 第一层布局：执行推演按钮 =================
        #

        # =============== 第二层布局：应急行为设置和应急资源设置 =================
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)
        middle_layout.setContentsMargins(0, 0, 0, 10)

        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(10)

        behavior_group = QGroupBox(self.tr("应急行为设置"))
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

        resource_group = QGroupBox(self.tr("应急资源设置"))
        resource_layout = QVBoxLayout()
        resource_layout.setContentsMargins(10, 10, 10, 10)
        self.resource_stacked_layout = QStackedLayout()

        self.placeholder_widget = QWidget()
        ph_layout = QVBoxLayout()
        ph_label = QLabel(self.tr("请选择应急行为"))
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

        self.resource_management_widget = QWidget()
        res_mgmt_layout = QVBoxLayout()
        res_mgmt_layout.setContentsMargins(0, 0, 0, 0)

        label_btn_layout = QHBoxLayout()
        label_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.current_behavior_label = QLabel(self.tr("请选择应急行为"))
        self.current_behavior_label.setAlignment(Qt.AlignCenter)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:gray;")

        btn_hbox = QHBoxLayout()
        btn_hbox.setContentsMargins(0, 0, 0, 0)
        self.add_resource_btn = QPushButton(self.tr("添加"))
        self.edit_resource_btn = QPushButton(self.tr("修改"))
        self.delete_resource_btn = QPushButton(self.tr("删除"))

        self.execute_btn = QPushButton(self.tr("执行推演"))
        self.execute_btn.setEnabled(False)
        self.execute_btn.setToolTip(self.tr("请配置应急行为"))
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
        self.resource_table.setHorizontalHeaderLabels([self.tr("资源"), self.tr("类型"), self.tr("数量"), self.tr("位置")])
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

        middle_layout.addLayout(left_vbox, stretch=1)
        middle_layout.addWidget(resource_group, stretch=3)
        main_layout.addLayout(middle_layout, stretch=1)

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
        self.simulation_table = CustomTableWidget(2, 7)
        self.simulation_table.setShowGrid(False)
        self.simulation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.simulation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.simulation_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.simulation_table.horizontalHeader().setVisible(False)
        self.simulation_table.verticalHeader().setVisible(False)

        self.simulation_table.setSpan(0, 0, 2, 1)
        self.simulation_table.setSpan(0, 1, 1, 3)
        self.simulation_table.setSpan(0, 4, 1, 3)

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

        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)
        self.simulation_table.itemDoubleClicked.connect(self.show_plan_details)

    def save_plan_to_file(self, plan_data):
        """Save plan data to JSON file"""
        try:
            # Load existing plans if file exists
            if os.path.exists(self.plans_file):
                with open(self.plans_file, 'r', encoding='utf-8') as f:
                    self.plans_data = json.load(f)
            else:
                self.plans_data = {}

            # Add timestamp to plan data
            plan_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save plan with its name as key
            self.plans_data[plan_data['plan_name']] = plan_data

            # Write updated plans to file
            with open(self.plans_file, 'w', encoding='utf-8') as f:
                json.dump(self.plans_data, ensure_ascii=False, indent=2, fp=f)

            return True
        except Exception as e:
            print(f"Error saving plan: {str(e)}")
            return False

    def add_plan_to_simulation_table(self, plan_name, plan_data):
        """Add a single plan to the simulation table"""
        # Get current row count excluding header rows
        current_data_rows = self.simulation_table.rowCount() - 2
        new_row = current_data_rows + 2  # Add after headers

        self.simulation_table.insertRow(new_row)

        # Set plan name
        self.simulation_table.setItem(new_row, 0, QTableWidgetItem(plan_name))

        # Get simulation results from plan data or use defaults
        simulation_results = plan_data.get('simulation_results', {
            "推演前-较好": "30%",
            "推演前-中等": "50%",
            "推演前-较差": "20%",
            "推演后-较好": "60%",
            "推演后-中等": "30%",
            "推演后-较差": "10%"
        })

        # Set simulation results
        columns = [
            simulation_results["推演前-较好"],
            simulation_results["推演前-中等"],
            simulation_results["推演前-较差"],
            simulation_results["推演后-较好"],
            simulation_results["推演后-中等"],
            simulation_results["推演后-较差"]
        ]

        for col, value in enumerate(columns, 1):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            self.simulation_table.setItem(new_row, col, item)

    def show_plan_details(self, item):
        """Show detailed information for the selected plan"""
        row = item.row()
        plan_name = self.simulation_table.item(row, 0).text()

        collector = PlanDataCollector(self.session, scenario_id=self.scenario_id)

        # 收集数据
        print(f"[DEBUG] Collecting data for plan: {plan_name}")
        plan_data = collector.collect_all_data(plan_name=plan_name)
        print(f"[DEBUG] Plan data: {plan_data}")

        # 转换为贝叶斯网络证据
        evidence = convert_to_evidence(plan_data)
        print(f"[DEBUG] Evidence: {evidence}")

        output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  f"../../data/bn/{self.scenario_id}/plans/{plan_name}"))
        print(f"[DEBUG] Output directory: {output_dir}")
        update_with_evidence(self.analyzer, evidence, output_dir)

        # 打开posteriot_probabilities.json
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
            print(f"[DEBUG] Plan data: {plan_data}")

            # Generate HTML content for the details dialog
            info_html = self.generate_plan_details_html(plan_data)

            # Show details dialog
            details_dialog = DetailsDialog(info_html, self)
            details_dialog.setWindowTitle(self.tr("预案详情 - ") + plan_name)
            details_dialog.open()

    def generate_plan_details_html(self, plan_data):
        """Generate HTML content for plan details"""
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

        info_html += f"<h2>{plan_data['plan_name']}</h2>"
        info_html += f"<div class='timestamp'>{self.tr('创建时间')}: {plan_data['timestamp']}</div>"

        for action in plan_data['emergency_actions']:
            if action['implementation_status'] == 'True':
                info_html += f"<h3>{self.tr('应急行为')}: {action['action_type']}</h3>"
                info_html += f"<p><b>{self.tr('时长')}:</b> {action['duration']}</p>"

                # Resources table
                info_html += f"<b>{self.tr('资源列表')}:</b>"
                if action['resources']:
                    info_html += f"""
                    <table>
                    <tr>
                        <th>{self.tr('资源名称')}</th>
                        <th>{self.tr('类型')}</th>
                        <th>{self.tr('数量')}</th>
                        <th>{self.tr('位置')}</th>
                    </tr>
                    """
                    for resource in action['resources']:
                        info_html += f"""
                        <tr>
                            <td>{resource['resource_type']}</td>
                            <td>{resource['resource_category']}</td>
                            <td>{resource['quantity']}</td>
                            <td>{resource['location']}</td>
                        </tr>
                        """
                    info_html += "</table>"
                else:
                    info_html += f"<p class='no-resource'>{self.tr('无资源')}</p>"

        info_html += "</body></html>"
        return info_html

    def load_saved_plans(self):
        """Load saved plans from JSON file and update simulation table"""
        try:
            # Initialize table structure
            self.init_simulation_table()

            self.plans_data = self.new_plan_generator.get_all_plans()
            print(f"[DEBUG] Loaded plans: {self.plans_data}")

            # Add each plan to the simulation table
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
        self.current_behavior_label.setText(self.tr("正在编辑: ") + behavior)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:#5dade2;")
        self.add_resource_btn.setToolTip(self.tr("添加") + behavior + self.tr("的资源"))
        self.edit_resource_btn.setToolTip(self.tr("修改") + behavior + self.tr("的资源"))
        self.delete_resource_btn.setToolTip(self.tr("删除") + behavior + self.tr("的资源"))
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
            dlg = CustomWarningDialog(self.tr("提示"), self.tr("请先选择应急行为"))
            dlg.open()
            return
        dlg = SingleResourceDialog(parent=self)
        dlg.accepted.connect(lambda: self.on_add_resource_ok(dlg))
        dlg.open()

    def on_add_resource_ok(self, dlg):
        r = dlg.get_resource()
        self.behavior_resources[self.current_behavior].append(r)
        self.add_resource_to_table(r, self.current_behavior)
        self.check_execute_button()

    def edit_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            wdlg = CustomWarningDialog(self.tr("提示"), self.tr("请选择要修改的资源。"))
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
            CustomWarningDialog(self.tr("提示"), self.tr("未找到要修改的资源。")).open()
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
            CustomWarningDialog(self.tr("提示"), self.tr("请选择要删除的资源。")).open()
            return
        row = sel[0].row()
        resource = {
            "资源": self.resource_table.item(row,0).text(),
            "类型": self.resource_table.item(row,1).text(),
            "数量": int(self.resource_table.item(row,2).text()),
            "位置": self.resource_table.item(row,3).text()
        }

        qdlg = CustomQuestionDialog(
            self.tr("确认删除"),
            self.tr("确定要删除应急行为 '") + self.current_behavior + self.tr("' 下的选中资源吗？"),
            parent=self
        )
        qdlg.accepted.connect(lambda: self.on_delete_confirmed(True, resource, row))
        qdlg.open()

    def on_delete_confirmed(self, is_ok, resource, row):
        if is_ok:
            try:
                self.behavior_resources[self.current_behavior].remove(resource)
            except ValueError:
                CustomWarningDialog(self.tr("提示"), self.tr("未找到要删除的资源。")).open()
                return
            self.resource_table.removeRow(row)
            self.check_execute_button()

    def check_execute_button(self):
        selected_b = [b for b in self.behaviors if self.behavior_settings[b].checkbox.isChecked()]

        if not selected_b:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip(self.tr("请配置应急行为"))
            return

        # 检查所有被勾选的应急行为是否有资源
        all_have_resources = all(len(self.behavior_resources[b]) > 0 for b in selected_b)

        # 检查所有被勾选的应急行为的时长是否大于0
        all_have_duration = all(self.behavior_settings[b].get_duration() > 0 for b in selected_b)

        # 如果所有被勾选的应急行为都满足上述两个条件，则启用按钮
        if all_have_resources and all_have_duration:
            self.execute_btn.setEnabled(True)
            self.execute_btn.setToolTip("")
        else:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip(self.tr("请配置应急行为"))

    def create_plan(self,name,plan_data) -> Dict[int, Any]:

        new_plan_data = self.new_plan_generator.build_plan_structure(plan_data)
        print(f"[DEBUG] New plan data: {new_plan_data}")
        saved_plan = []
        for entity_id, entity in new_plan_data.items():
            saved_plan.append(entity)
        self.save_plan_to_database_signal.emit(saved_plan,False)
        return new_plan_data


    def handle_save(self):
        saved_categories = []
        for b in self.behaviors:
            cbox = self.behavior_settings[b].checkbox
            if cbox.isChecked():
                duration = self.behavior_settings[b].get_duration()
                res_list = self.behavior_resources[b]
                saved_categories.append({
                    "category": b,
                    "attributes": {self.tr("时长"): f"{duration} {self.tr('分钟')}"},
                    "behaviors": res_list
                })
        if not saved_categories:
            dlg = CustomInformationDialog(self.tr("保存结果"), self.tr("没有要保存的应急行为。"), parent=self)
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
        </style></head><body><h2>""" + self.tr("保存结果详情") + """</h2>
        """
        for item in saved_categories:
            info_html += f"<h3>{self.tr('类别')}: {item['category']}</h3>"
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
        input_dlg = CustomInputDialog(self.tr("预案名称设置"), self.tr("请输入预案名字:"), parent=self)
        input_dlg.accepted_text.connect(lambda name: self.on_plan_name_input(name))
        input_dlg.open()

    def format_plan_as_json(self, plan_name):
        """Format the emergency plan details as JSON."""
        plan_data = {
            "plan_name": plan_name,
            "emergency_actions": [],
            "simulation_results": {
                "推演前-较好": "30%",
                "推演前-中等": "50%",
                "推演前-较差": "20%",
                "推演后-较好": "60%",
                "推演后-中等": "30%",
                "推演后-较差": "10%"
            }
        }

        # Collect data for each checked behavior
        for behavior in self.behaviors:
            checkbox = self.behavior_settings[behavior].checkbox

            if checkbox.isChecked():
                action_data = {
                    "action_type": behavior,
                    "duration": f"{self.behavior_settings[behavior].get_duration()} minutes",
                    "implementation_status": "True",
                    "resources": []
                }

                # Add all resources for this behavior
                for resource in self.behavior_resources[behavior]:
                    resource_data = {
                        "resource_type": resource["资源"],
                        "resource_category": resource["类型"],
                        "quantity": resource["数量"],
                        "location": resource["位置"]
                    }
                    action_data["resources"].append(resource_data)

                plan_data["emergency_actions"].append(action_data)

        return plan_data

    def convert_json_to_posterior_probabilities(self,json_data):
        """
        将给定的 JSON 数据转换为 posterior_probabilities 列表格式。

        参数：
            json_data (dict): 包含要转换数据的字典。

        返回：
            list: 转换后的 posterior_probabilities 列表。
        """
        posterior_probabilities = []

        for element_node, states in json_data.items():
            # 遍历每个要素节点下的所有状态
            for state, probability in states.items():
                # 将概率转换为百分比字符串，保留两位小数
                probability_percentage = f"{probability * 100:.2f}%"

                # 创建一个字典并添加到列表中
                entry = {
                    "要素节点": element_node,
                    "状态": state,
                    "概率": probability_percentage
                }
                posterior_probabilities.append(entry)

        return posterior_probabilities

    def on_plan_name_input(self, plan_name):
        """Handle plan name input and save plan data"""
        plan_name = plan_name.strip()
        if plan_name:
            # Format the plan data as JSON
            plan_data = self.format_plan_as_json(plan_name)
            print(f"[DEBUG] Plan data: {plan_data}")
            self.create_plan(plan_name,plan_data)
            collector = PlanDataCollector(self.session, scenario_id=self.scenario_id)

            # 收集数据
            print(f"[DEBUG] Collecting data for plan: {plan_name}")
            plan_data = collector.collect_all_data(plan_name=plan_name)
            print(f"[DEBUG] Plan data: {plan_data}")

            # 转换为贝叶斯网络证据
            evidence = convert_to_evidence(plan_data)
            print(f"[DEBUG] Evidence: {evidence}")

            output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../data/bn/{self.scenario_id}/plans/{plan_name}"))
            print(f"[DEBUG] Output directory: {output_dir}")
            update_with_evidence(self.analyzer, evidence, output_dir)

            # 打开posteriot_probabilities.json
            posteriors_file = os.path.join(output_dir, "posterior_probabilities.json")
            posterior_probabilities = {}
            if os.path.exists(posteriors_file):
                with open(posteriors_file, 'r', encoding='utf-8') as f:
                    posterior_probabilities = json.load(f)
            print(f"[DEBUG] Posterior probabilities: {posterior_probabilities}")

            self.new_plan_generator.upsert_posterior_probability(plan_name,posterior_probabilities)

            self.posterior_probabilities = self.convert_json_to_posterior_probabilities(posterior_probabilities)
            print(f"[DEBUG] Posterior probabilities: {self.posterior_probabilities}")

            self.update_evidence_table()

            new_plan_data = self.new_plan_generator.get_all_plans()
            print(f"[DEBUG] New plan data: {new_plan_data}")

            if self.load_saved_plans():
                # Show success message
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
        else:
            CustomWarningDialog(
                self.tr("提示"),
                self.tr("预案名字不能为空。"),
                parent=self
            ).open()

    def init_simulation_table(self):
        """Initialize simulation table with headers and structure"""
        self.simulation_table.clearContents()
        self.simulation_table.setRowCount(2)  # Initial header rows

        # Set header structure
        self.simulation_table.setSpan(0, 0, 2, 1)  # "韧性/预案" cell
        self.simulation_table.setSpan(0, 1, 1, 3)  # "推演前" cell
        self.simulation_table.setSpan(0, 4, 1, 3)  # "推演后" cell

        # Initialize header rows with empty items
        for col in range(7):
            if self.simulation_table.item(0, col) is None:
                self.simulation_table.setItem(0, col, QTableWidgetItem(""))
            if self.simulation_table.item(1, col) is None:
                self.simulation_table.setItem(1, col, QTableWidgetItem(""))

        # Apply header delegate
        header_delegate = FullHeaderDelegate(self.simulation_table)
        for row in range(2):
            for col in range(self.simulation_table.columnCount()):
                self.simulation_table.setItemDelegateForRow(row, header_delegate)

    def update_evidence_table(self):
        self.evidence_table.clearContents()
        self.evidence_table.setRowCount(0)
        for d in self.posterior_probabilities:
            rowpos = self.evidence_table.rowCount()
            self.evidence_table.insertRow(rowpos)
            self.evidence_table.setItem(rowpos,0,QTableWidgetItem(d[self.tr("要素节点")]))
            self.evidence_table.setItem(rowpos,1,QTableWidgetItem(d[self.tr("状态")]))
            self.evidence_table.setItem(rowpos,2,QTableWidgetItem(d[self.tr("概率")]))
            for col in range(3):
                item = self.evidence_table.item(rowpos, col)
                item.setTextAlignment(Qt.AlignCenter)
                item.setToolTip(item.text())
        # 设置tooltip,显示浮标所在单元格内容


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
        self.setStyleSheet(self.tr("""
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
        """))

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionSettingTab()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
