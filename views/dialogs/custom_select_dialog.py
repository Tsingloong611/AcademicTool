# -*- coding: utf-8 -*-
# @Time    : 1/16/2025 11:27 AM
# @FileName: custom_select_dialog.py
# @Software: PyCharm
import json
import re
import typing
from typing import Dict, List

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QDialog, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QWidget, QStackedLayout, QFileDialog, QDialogButtonBox,
    QComboBox, QCheckBox
)
from PySide6.QtGui import QIcon, QColor, QPalette
import os

from openpyxl.styles.builtins import title

from utils import json2sysml

from sqlalchemy import text

from utils.get_config import get_cfg
from utils.json2sysml import json_to_sysml2_txt
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog


class CreateDefinitionDialog(QDialog):
    def __init__(self, parent, code_id, file_attr_name):
        super().__init__(parent)
        self.setWindowTitle("新建属性定义")
        self.code_id = code_id
        self.file_attr_name = file_attr_name
        self.created_definition_id = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"为 code_id={code_id}, 文件属性名={file_attr_name} 创建新 attribute_definition：", self))

        # 中文名
        hl_cn = QHBoxLayout()
        hl_cn.addWidget(QLabel("中文名:", self))
        self.cn_edit = QLineEdit(self)
        hl_cn.addWidget(self.cn_edit)
        layout.addLayout(hl_cn)

        # 英文名
        hl_en = QHBoxLayout()
        hl_en.addWidget(QLabel("英文名:", self))
        self.en_edit = QLineEdit(self)
        hl_en.addWidget(self.en_edit)
        layout.addLayout(hl_en)

        # 是否必需
        self.req_checkbox = QCheckBox("is_required", self)
        layout.addWidget(self.req_checkbox)

        # 类型(假设用户可选择 attribute_type)
        # 这里仅示例: 下拉列出 attribute_type 表中所有
        self.type_combo = QComboBox(self)
        layout.addWidget(QLabel("选择属性类型:", self))
        layout.addWidget(self.type_combo)

        # 先加载数据库的 attribute_type
        session = parent.get_session() if parent else None
        if session:
            type_rows = session.execute("""
                SELECT attribute_type_id, attribute_type_code
                FROM attribute_type
            """).fetchall()
            for (tid, tcode) in type_rows:
                self.type_combo.addItem(f"{tcode} (ID={tid})", userData=tid)

        # OK / Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.on_ok)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_ok(self):
        cn_name = self.cn_edit.text().strip()
        en_name = self.en_edit.text().strip()
        is_req = self.req_checkbox.isChecked()
        idx = self.type_combo.currentIndex()
        if idx < 0:
            CustomWarningDialog(self.tr("错误"), self.tr("请选择属性类型")).exec_()
            return
        sel_type_id = self.type_combo.itemData(idx)

        if not cn_name or not en_name:
            CustomWarningDialog(self.tr("错误"), self.tr("中文名与英文名不能为空")).exec_()
            return

        # 插入 attribute_definition
        session = self.parent().get_session()  # parent is MyEntityImporter
        # 仅示例, 先固定 aspect_id=4, is_multi_valued=0, is_reference=0, reference_target_type_id=NULL
        # 也可让用户更多输入
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql_insert = """
            INSERT INTO attribute_definition(
              china_default_name, english_default_name,
              attribute_code_id, attribute_type_id, attribute_aspect_id,
              is_required, is_multi_valued, is_reference,
              reference_target_type_id, default_value, description,
              create_time, update_time
            ) VALUES(
              :cn, :en,
              :code_id, :type_id, 4,
              :req, 0, 0,
              NULL, NULL, NULL,
              :now, :now
            )
        """
        session.execute(sql_insert, {
            "cn": cn_name,
            "en": en_name,
            "code_id": self.code_id,
            "type_id": sel_type_id,
            "req": 1 if is_req else 0,
            "now": now
        })
        session.commit()

        # 查新建 definition_id
        sql_get = """
            SELECT attribute_definition_id 
            FROM attribute_definition
            WHERE china_default_name=:cn
              AND english_default_name=:en
              AND attribute_code_id=:code_id
            ORDER BY attribute_definition_id DESC 
            LIMIT 1
        """
        row = session.execute(sql_get, {"cn": cn_name, "en":en_name, "code_id": self.code_id}).fetchone()
        if not row:
            CustomWarningDialog(self.tr("错误"), self.tr("新建 definition 失败")).exec_()
            self.reject()
            return
        self.created_definition_id = row[0]
        self.accept()

    def get_created_definition_id(self):
        return self.created_definition_id


def ask_user_create_definition_for_code(self, code_id: int, file_attr_name: str) -> typing.Optional[int]:
    """
    弹出对话框让用户填写中文名、英文名、是否必需、attribute_type等信息，
    插入数据库 attribute_definition, 返回新建 definition_id。
    如果用户取消或失败 => 返回 None
    """
    dlg = CreateDefinitionDialog(self, code_id=code_id, file_attr_name=file_attr_name)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.get_created_definition_id()
    else:
        return None
class SelectCodeDialog(QDialog):
    def __init__(self, parent, codes, file_attr_name, type='attribute'):
        """
        codes: List of tuple (code_id, code_name)
        file_attr_name: 当前文件属性名称，用于在对话框中提示用户
        """
        super().__init__(parent)
        if type == 'attribute':
            title_name = self.tr("选择 attribute_code")
            label_str = self.tr("文件中出现属性名: '{0}'\n请选择对应的 attribute_code:").format(file_attr_name)
        else:
            title_name = self.tr("选择 behavior_code")
            label_str = self.tr("文件中出现行为名: '{0}'\n请选择对应的 behavior_code:").format(file_attr_name)
        self.setWindowTitle(title_name)

        self.selected_code_id = None
        self.codes = codes

        layout = QVBoxLayout(self)

        label = QLabel(label_str, self)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        for cid, cname in self.codes:
            self.combo.addItem(f"{cname} (ID={cid})", userData=cid)
        layout.addWidget(self.combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_accept(self):
        idx = self.combo.currentIndex()
        if idx >= 0:
            self.selected_code_id = self.combo.itemData(idx)
        self.accept()

    def get_selected_code_id(self):
        return self.selected_code_id


    def ask_user_to_select_code_for_name(self, file_attr_name: str) -> int:
        """
        使用一个QDialog列出 attribute_code 列表，用户选一个 code_id.
        若用户取消 => 返回 None
        若用户确认 => 返回 code_id
        """
        session = self.get_session()
        # 1. 查询数据库所有 code
        code_sql = """
            SELECT attribute_code_id, attribute_code_name
            FROM attribute_code
            ORDER BY attribute_code_id
        """
        codes = session.execute(code_sql).fetchall()  # List[(id, name)]

        if not codes:
            CustomWarningDialog(self.tr("无可用Code"), self.tr("数据库中无任何 attribute_code 记录。")).exec_()
            return None

        dlg = SelectCodeDialog(parent=None, codes=codes, file_attr_name=file_attr_name)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_selected_code_id()  # 可能是 int, or None
        else:
            return None

class CustomSelectDialog(QDialog):
    # 信号，用于向外部传递操作结果
    entity_created = Signal(dict)
    entity_deleted = Signal(int)
    entity_read = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.element = self.parent.current_selected_element
        if get_cfg()["i18n"]["language"] == "en_US":
            self.element = self.parent.reverse_element_name_mapping[self.element]
        self.update_match_entities()
        self.setWindowTitle(self.tr("实体管理"))
        self.resize(400, 300)
        self.setStyleSheet("""
            background : #f0f0f0;
            color: black;

            QPushButton {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
QListWidget {
        border: 1px solid #ccc;
        border-radius: 8px;
        background-color: white;
    }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 按钮布局
        button_layout = QHBoxLayout()

        self.new_button = QPushButton(self.tr("新建"))
        self.new_button.clicked.connect(self.handle_new)
        button_layout.addWidget(self.new_button)
        self.new_button.setFixedWidth(110)

        self.delete_button = QPushButton(self.tr("删除"))
        self.delete_button.clicked.connect(self.handle_delete)
        button_layout.addWidget(self.delete_button)
        self.delete_button.setFixedWidth(110)

        self.read_button = QPushButton(self.tr("读取"))
        self.read_button.clicked.connect(self.handle_read)
        button_layout.addWidget(self.read_button)
        self.read_button.setFixedWidth(110)

        main_layout.addLayout(button_layout)

        # 使用 QStackedLayout 来切换列表和占位符
        self.stacked_layout = QStackedLayout()

        # 列表视图
        self.list_widget = QListWidget()
        # 开启交错行背景
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setAlternatingRowColors(True)
        self.populate_list()
        self.stacked_layout.addWidget(self.list_widget)

        # 占位符视图
        self.placeholder_label = QLabel(self.tr("请新建实体"))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setObjectName("placeholder")
        # 字体设置为灰色
        self.placeholder_label.setStyleSheet("""
                    color: gray;
                    font-size: 20pt;
                    border-radius: 10px;
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                """)

        self.stacked_layout.addWidget(self.placeholder_label)


        main_layout.addLayout(self.stacked_layout)




        self.update_view()


    def update_match_entities(self):


        self.rule = self.parent.get_result_by_sql(
            f"SELECT template_restrict FROM template WHERE template_name = '{self.element}'"
        )
        self.rule = json.loads(self.rule[0][0])
        filtered_data = self.parent.filter_entities_by_select_rule(self.parent.element_data, self.rule)
        # 键在filtered_data中的实体
        self.match_entities = {k: v for k, v in self.parent.element_data.items() if k in filtered_data}

    def populate_list(self):
        """填充实体列表，仅显示entity_name"""
        self.list_widget.clear()
        self.list_widget.setObjectName("entitylist")

        self.list_widget.setStyleSheet("""
            #entitylist {
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: white;
            }
            /* 自定义 QListWidgetItem 的样式 */
            QListWidget#entitylist::item {
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }

            /* 鼠标悬停时的背景色 */
            QListWidget#entitylist::item:hover {
                background-color: #cce5ff;
            }

            /* 选中项的背景色 */
            QListWidget#entitylist::item:selected {
                background-color: #5dade2;
                color: white;
            }
        """)

        # 获得实体数据
        self.update_match_entities()

        for entity_id, entity in self.match_entities.items():
            item = QListWidgetItem(entity['entity_name'])
            item.setData(Qt.UserRole, entity_id)  # 存储entity_id
            self.list_widget.addItem(item)

    def update_view(self):
        """根据实体数量切换视图"""
        if not self.match_entities:
            self.stacked_layout.setCurrentWidget(self.placeholder_label)
        else:
            self.stacked_layout.setCurrentWidget(self.list_widget)

    def handle_new(self):
        """处理新建按钮点击"""
        # 创建一个子对话框，包含“从文件新建”和“从模板新建”按钮
        new_dialog = QDialog(self)
        new_dialog.setWindowTitle(self.tr("新建实体"))
        if get_cfg()["i18n"]["language"] == "en_US":
            new_dialog.setFixedSize(180,100)
        else:
            new_dialog.setFixedSize(130, 100)
        layout = QVBoxLayout(new_dialog)

        from_file_button = QPushButton(self.tr("从文件新建"))
        from_file_button.clicked.connect(lambda: self.create_entity_from_file(new_dialog))
        layout.addWidget(from_file_button)
        if get_cfg()["i18n"]["language"] == "en_US":
            from_file_button.setFixedWidth(160)
        else:
            from_file_button.setFixedWidth(110)

        from_template_button = QPushButton(self.tr("从模板新建"))
        if get_cfg()["i18n"]["language"] == "en_US":
            from_template_button.setFixedWidth(160)
        else:
            from_template_button.setFixedWidth(110)
        from_template_button.clicked.connect(lambda: self.create_entity_from_template(new_dialog))
        layout.addWidget(from_template_button)

        new_dialog.exec()

    def parse_sysml2(self, code: str) -> List[Dict[str, List[Dict[str, str]]]]:
        """
        解析提供的代码，提取所有 part 定义的名称、属性 (attribute)、item 和 ref。
        同时解析 action 定义，记录 perform action 的 in 和 out 变量。

        :param code: 包含 part 和 action 定义的代码字符串
        :return: 包含多个 part 名称、属性、item、ref 和 perform actions 的列表
        """
        parts = []
        actions = {}

        # 正则表达式匹配所有 action 定义
        action_pattern = re.compile(r"action\s+def\s+(\w+)\s*{([^}]*)}", re.DOTALL)
        for action_match in action_pattern.finditer(code):
            action_name = action_match.group(1)
            action_body = action_match.group(2)

            in_vars = []
            out_vars = []

            # 匹配 in 变量，支持 'in var;' 和 'in var = value;'
            in_pattern = re.compile(r"in\s+(\w+)\s*(?:=\s*[^;]+)?;")
            # 匹配 out 变量，支持 'out var;' 和 'out var = value;'
            out_pattern = re.compile(r"out\s+(\w+)\s*(?:=\s*[^;]+)?;")

            in_matches = in_pattern.findall(action_body)
            out_matches = out_pattern.findall(action_body)

            in_vars.extend(in_matches)
            out_vars.extend(out_matches)

            actions[action_name] = {
                'in': in_vars,
                'out': out_vars
            }

            # 调试输出
            print(f"解析 action: {action_name}")
            print(f"  in: {in_vars}")
            print(f"  out: {out_vars}\n")

        # 正则表达式匹配所有 part 定义
        part_pattern = re.compile(r"part\s+(\w+)\s*:\s*\w+\s*{([^}]*)}", re.DOTALL)
        for part_match in part_pattern.finditer(code):
            part_name = part_match.group(1)
            part_body = part_match.group(2)

            part_dict = {
                "name": part_name,
                "attributes": [],
                "items": [],
                "refs": [],
                "performs": []
            }

            # 调试输出
            print(f"解析 part: {part_name}")
            print(f"part 内容:\n{part_body}\n")

            # 匹配 attribute 定义（支持 redefines）
            attribute_pattern = re.compile(
                r"attribute\s+(?:redefines\s+)?(\w+)\s*(?::\s*(\w+))?\s*(?:=\s*([^;]+))?;",
                re.MULTILINE
            )
            for attr_match in attribute_pattern.finditer(part_body):
                attr_name = attr_match.group(1)
                attr_type = attr_match.group(2) if attr_match.group(2) else "normal"
                attr_value = attr_match.group(3).strip() if attr_match.group(3) else "None"
                part_dict["attributes"].append({
                    "attribute_name": attr_name,
                    "type": attr_type,
                    "value": attr_value
                })
                # 调试输出
                print(f"  解析 attribute: {attr_name}, 类型: {attr_type}, 值: {attr_value}")

            # 匹配 item 定义
            item_pattern = re.compile(r"item\s+(\w+)\s*:\s*(\w+);", re.MULTILINE)
            for item_match in item_pattern.finditer(part_body):
                item_name = item_match.group(1)
                item_type = item_match.group(2)
                part_dict["items"].append({
                    "item_name": item_name,
                    "type": item_type
                })
                # 调试输出
                print(f"  解析 item: {item_name}, 类型: {item_type}")

            # 匹配 ref 定义
            ref_pattern = re.compile(r"ref\s+part\s+(\w+);", re.MULTILINE)
            for ref_match in ref_pattern.finditer(part_body):
                ref_name = ref_match.group(1)
                part_dict["refs"].append({
                    "ref_name": ref_name,
                    "type": "part"
                })
                # 调试输出
                print(f"  解析 ref: {ref_name}, 类型: part")

            # 匹配 perform action 定义，捕获 perform_name 和可选的 action_type
            perform_pattern = re.compile(r"perform\s+action\s+(\w+)(?:\s*:\s*(\w+))?;", re.MULTILINE)
            for perform_match in perform_pattern.finditer(part_body):
                perform_name = perform_match.group(1)
                action_type = perform_match.group(2)

                if action_type:
                    # 如果指定了 action_type，则使用它
                    associated_action = actions.get(action_type, {})
                else:
                    # 如果未指定 action_type，则假设 action_type 与 perform_name 相同
                    associated_action = actions.get(perform_name, {})

                perform_in = associated_action.get('in', [])
                perform_out = associated_action.get('out', [])

                part_dict["performs"].append({
                    "perform_name": perform_name,
                    "in": perform_in,
                    "out": perform_out
                })
                # 调试输出
                print(f"  解析 perform: {perform_name}, in: {perform_in}, out: {perform_out}")

            parts.append(part_dict)

        return parts

    def create_entity_from_file(self, parent_dialog):
        """从文件新建实体，不需要用户输入名称"""
        parent_dialog.close()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "All Files (*)")
        if file_path:
            # 使用文件名（不含扩展名）作为实体名称
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # 解析文件内容
            parts = self.parse_sysml2(code)
            # 从parts中提取实体名称
            print(f"提取到的结果: {parts}")
            name = parts[0]['name']

            new_entity = self.parent.create_entities_with_negative_ids(self.element, name)
            print(f"new_entity: {new_entity}")
            print(f"element_data: {self.parent.element_data}")
            # 提取parts中的数据覆盖new_entity
            self.fill_new_entity_with_parts_and_code_map(new_entity, parts)



            # 将new_entity添加到element_data中
            self.parent.element_data.update(new_entity)
            print(f"updated_element_data: {self.parent.element_data}")
            self.populate_list()
            self.update_view()

            # 弹出成功消息
            CustomInformationDialog(self, self.tr("成功"), self.tr("已成功从文件新建实体 '{0}'。").format(name))


            # 发射信号
            self.entity_created.emit(new_entity)

    def fill_new_entity_with_parts_and_code_map(self, new_entity: dict, parts: list):
        """
        处理解析好的 SysML2 part，给 new_entity 填充属性 attribute_value，
        同时按需求处理 items、refs、performs：
          - items: 若无对应 entity_type 或现有实体，就自动 create_entity_from_template(...) 。
          - refs: 同理，可以让用户选已有或自动创建；若用户放弃则跳过。
          - performs: 若 out code 未映射，就让用户指定；若用户不选则跳过。若无实体则自动 create; 若有则直接使用。
        """

        session = self.get_session()
        if not parts:
            print("parts 为空，无法填充。")
            return

        if not new_entity:
            print("new_entity 为空。")
            return

        # 只处理 parts[0]
        part_data = parts[0]

        # new_entity 只有一个键(负数ID)
        neg_entity_id = list(new_entity.keys())[0]
        entity_dict = new_entity[neg_entity_id]

        # 1) 覆盖当前实体名称
        if "name" in part_data:
            entity_dict["entity_name"] = part_data["name"]

        # 2) 处理 attributes（与之前一样）
        file_attrs = part_data.get("attributes", [])
        for fa in file_attrs:
            file_attr_name = fa.get("attribute_name")
            file_attr_value = fa.get("value")
            if isinstance(file_attr_value, str):
                file_attr_value = file_attr_value.strip('"')

            # （1）先查 attribute_code
            code_map_sql = text("""
                SELECT acn.attribute_code_id, c.attribute_code_name
                FROM attribute_code_name AS acn
                JOIN attribute_code AS c ON acn.attribute_code_id = c.attribute_code_id
                WHERE acn.attribute_name = :fname
            """)
            result = session.execute(code_map_sql, {"fname": file_attr_name}).fetchone()
            if not result:
                # => 用户手动选择 code_id
                code_id = self.ask_user_to_select_code_for_name(file_attr_name)
                if code_id is None:
                    CustomWarningDialog(self.tr("无法新建属性"), self.tr("文件属性 '{0}' 无法与任一 attribute_code 映射,已跳过.").format(file_attr_name)).exec_()
                    continue
                # 插入 attribute_code_name
                insert_sql = text("""
                    INSERT IGNORE INTO attribute_code_name (attribute_code_id, attribute_name)
                    VALUES(:cid, :aname)
                """)
                session.execute(insert_sql, {"cid": code_id, "aname": file_attr_name})
                session.commit()

                # 再查
                code_name_sql = text("SELECT attribute_code_name FROM attribute_code WHERE attribute_code_id=:cid")
                row2 = session.execute(code_name_sql, {"cid": code_id}).fetchone()
                if row2:
                    attribute_code_name = row2[0]
                else:
                    attribute_code_name = "UnknownCode"
            else:
                code_id = result[0]
                attribute_code_name = result[1]

            # （2）查 attribute_definition
            def_sql = text("""
                SELECT attribute_definition_id,
                       china_default_name, english_default_name,
                       attribute_type_id, attribute_aspect_id,
                       is_required, is_multi_valued, is_reference,
                       reference_target_type_id, default_value, description
                FROM attribute_definition
                WHERE attribute_code_id=:cid
                LIMIT 1
            """)
            def_row = session.execute(def_sql, {"cid": code_id}).fetchone()
            if not def_row:
                # => 用户手动创建 definition
                definition_id = self.ask_user_create_definition_for_code(code_id, file_attr_name)
                if not definition_id:
                    CustomWarningDialog(self.tr("无法新建属性"), self.tr("属性 '{0}' 无法在 code_id={code_id} 下创建 definition, 跳过.").format(file_attr_name)).exec_()
                    continue
                # 再查
                def_row = session.execute(def_sql, {"cid": code_id}).fetchone()
                if not def_row:
                    continue
            (def_id,
             cn_name, en_name, type_id, aspect_id,
             is_req, is_multi, is_ref, ref_tgt_id,
             def_val, desc) = def_row

            # （3）看看当前 entity 的 attributes 是否已存在 code
            match_attr = None
            for a in entity_dict["attributes"]:
                print(f"{a}")
                print(attribute_code_name)
                if a.get("attribute_code_name") == attribute_code_name:
                    match_attr = a
                    break
            if match_attr:
                # 覆盖 attribute_value
                match_attr["attribute_value"] = file_attr_value
                match_attr["attribute_name"] = file_attr_name
            else:
                # 新建
                new_attr_neg_id = self.parent.neg_id_gen.next_id()
                new_attr = {
                    "attribute_value_id": new_attr_neg_id,
                    "attribute_definition_id": def_id,
                    "attribute_name": file_attr_name,
                    "china_default_name": cn_name,
                    "english_default_name": en_name,
                    "attribute_code_name": attribute_code_name,
                    "attribute_type_code": self.get_type_code_by_id(type_id),
                    "is_required": bool(is_req),
                    "is_multi_valued": bool(is_multi),
                    "is_reference": bool(is_ref),
                    "reference_target_type_id": ref_tgt_id,
                    "default_value": def_val,
                    "description": desc,
                    "attribute_value": file_attr_value,
                    "referenced_entities": []
                }
                entity_dict["attributes"].append(new_attr)

        # 3) 处理 items
        map_dict = {'People': '人类', 'Road': '道路承灾要素','Lane':'车道','Facility':'基础设施'}
        part_items = part_data.get("items", [])
        for item_obj in part_items:
            item_name = item_obj.get("item_name")
            item_type_str = item_obj.get("type")



            # 查 entity_type
            type_sql = text("""
                    SELECT entity_type_id
                    FROM entity_type
                    WHERE entity_type_code = :tname
                    LIMIT 1
                """)
            type_row = session.execute(type_sql, {"tname": item_type_str}).fetchone()
            if not type_row:
                print(f"[item] entity_type_code='{item_type_str}' 不存在，尝试自动从模板创建...")
                CustomWarningDialog("实体类型不存在", f"实体类型 '{item_type_str}' 不存在，跳过").exec_()
                continue

            item_type_id = type_row[0]
            # 在 attributes 中找对应的引用属性
            ref_attr = next((a for a in entity_dict["attributes"]
                             if a["is_reference"] and a["reference_target_type_id"] == item_type_id), None)

            if not ref_attr:
                print(f"[item] 当前实体里无属性引用 item_type_id={item_type_id}, 跳过 item={item_name}")
                continue

            # 使用 create_entity_from_template 创建新实体

            print(f"[item] 创建 item={item_name} 类型={map_dict[item_type_str]}")
            item_entity = self.create_entity_from_template(template_name=map_dict[item_type_str], name=item_name)
            print(f"[item] 创建结果: {item_entity}")
            # 取第一个键
            item_entity_id = list(item_entity.keys())[0]

            ref_attr["referenced_entities"].append(item_entity_id)


        # 4) 处理 refs
        part_refs = part_data.get("refs", [])
        for ref_obj in part_refs:
            ref_name = ref_obj.get("ref_name")
            ref_type_str = ref_obj.get("type")

            # 查 entity_type
            type_sql = text("""
                    SELECT entity_type_id
                    FROM entity_type
                    WHERE entity_type_code = :tname
                    LIMIT 1
                """)
            type_row = session.execute(type_sql, {"tname": ref_name}).fetchone()
            if not type_row:
                print(f"[ref] 未找到 entity_type_code='{ref_name}'，跳过")
                CustomWarningDialog("实体类型不存在",f"[ref] 未找到 entity_type_code='{ref_name}'，跳过").exec_()
                continue

            ref_type_id = type_row[0]
            # 查找对应的引用属性
            ref_attr = next((a for a in entity_dict["attributes"]
                             if a["is_reference"] and a["reference_target_type_id"] == ref_type_id), None)

            if not ref_attr:
                print(f"[ref] 当前实体无可引用 ref_type_id={ref_type_id} 的属性，跳过")
                continue

            # 使用 create_entity_from_template 创建新实体

            ref_entity = self.create_entity_from_template(template_name=map_dict[ref_name], name=ref_name)
            if ref_entity:
                # 获取新创建实体的ID
                ref_entity_id = list(ref_entity.keys())[0]
                # 更新引用
                ref_attr["referenced_entities"].append(ref_entity_id)


        # 5) performs
        performs = part_data.get("performs", [])
        for pfm in performs:
            perform_name = pfm.get("perform_name")
            in_list = pfm.get("in", [])
            out_list = pfm.get("out", [])

            # (a) 若当前 project 中 behavior_code_name (或 behavior_name_code) 里没有 perform_name => 让用户指定
            #     user may skip => then we do not handle
            #     else => get or create code
            code_sql = text("""
                SELECT bc.behavior_code_id
                FROM behavior_name_code bnc
                JOIN behavior_code bc ON bc.behavior_code_id = bnc.behavior_code_id
                WHERE bnc.behavior_name = :bname
            """)
            code_row = session.execute(code_sql, {"bname": perform_name}).fetchone()
            if not code_row:
                # => 让用户指定 / 跳过
                user_selected_code_id = self.ask_user_select_behavior_code_for_name(perform_name)
                if user_selected_code_id is None:
                    print(f"[perform] 用户跳过 action={perform_name}")
                    continue
                # => 插入 behavior_name_code
                ins_sql = text("""
                    INSERT INTO behavior_name_code (behavior_code_id, behavior_name)
                    VALUES(:cid, :bname)
                """)
                session.execute(ins_sql, {"cid": user_selected_code_id, "bname": perform_name})
                session.commit()
                code_id_for_perform = user_selected_code_id
            else:
                code_id_for_perform = code_row[0]

            # (b) out_list => attribute_code_name
            #     在 self.parent.element_data 中找具备这些 out 属性的实体; 若无 => create
            matched_entity_id = None
            for out_code in out_list:
                found = False
                for e_id, e_data in self.parent.element_data.items():
                    for attr in e_data.get("attributes", []):
                        if attr.get("attribute_code_name") == out_code:
                            # 给它赋 "true"
                            attr["attribute_value"] = "true"
                            matched_entity_id = e_id
                            found = True
                            break
                    if found:
                        break

                if not found:
                    # => 没找到 => 根据模板再建？
                    #    需要知道哪张 template 里有此 out_code => 也可让用户选
                    print(f"[perform] out_code={out_code} 未在已有实体找到, 自动创建 or user select skip.")
                    # pseudo:
                    # self.create_entity_from_template(template_name=..., name=out_code)
                    # 这里仅跳过

                # 如果成功 matched_entity_id => 把它加到 当前实体 behaviors => object_entities
                if matched_entity_id is not None:
                    for b_json in entity_dict["behaviors"]:
                        if b_json.get("behavior_name") == perform_name:
                            # object_entities
                            b_json.setdefault("object_entities", [])
                            b_json["object_entities"].append({"object_entity_id": matched_entity_id})
                else:
                    print(f"[perform] out_code={out_code} 未能创建or找到可用实体, skip out.")

        print("[DONE] fill_new_entity_with_parts_and_code_map, new_entity=", new_entity)

    def create_entity_from_template(self, parent_dialog = None, template_name=None, name= None):
        """从模板新建实体，需要用户输入名称"""
        if parent_dialog:
            parent_dialog.close()
        # 弹出输入对话框获取实体名称
        if not template_name:
            template_name = self.element
        if not name:
            ask_name = CustomInputDialog(
                self.tr("新建实体"),
                self.tr("请输入新建实体的名称"),
                parent=self
            )
            ask_name.exec()
            name = ask_name.get_input()
        # 如果是空的，不创建
        if not name:
            CustomWarningDialog(self.tr("警告"), self.tr("实体名称不能为空"), parent=self).exec()
            return

        new_entity = self.parent.create_entities_with_negative_ids(template_name,name)
        print(f"new_entity: {new_entity}")
        print(f"element_data: {self.parent.element_data}")
        # 提取parts中的数据覆盖new_entity

        # 将new_entity添加到element_data中
        self.parent.element_data.update(new_entity)
        print(f"updated_element_data: {self.parent.element_data}")


        self.populate_list()
        self.update_view()

        # 弹出成功消息
        CustomInformationDialog(self.tr("成功"), self.tr("已成功从模板新建实体 '{0}'。").format(name)).exec_()
        # 发射信号
        self.entity_created.emit(new_entity)
        return new_entity

    def handle_delete(self):
        """处理删除按钮点击"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            CustomWarningDialog(self.tr("警告"), self.tr("请先选择要删除的实体。"), parent=self).exec()
            return

        item = selected_items[0]
        entity_id = item.data(Qt.UserRole)
        entity_name = item.text()

        # 删除实体
        confirm = CustomQuestionDialog(
            self.tr("确认删除"),
            self.tr('确定要删除实体 "{entity_name}" 吗？').format(entity_name=entity_name),
            parent=self
        ).ask()

        if confirm:
            del self.parent.element_data[entity_id]
            self.populate_list()
            self.update_view()
            CustomInformationDialog(self.tr("成功"), self.tr('已删除实体 "{0}"').format(entity_name), parent=self).exec()
            print(f"after_delete_element_data: {self.parent.element_data}")

            # 发射信号
            self.entity_deleted.emit(entity_id)

    def handle_read(self):
        """处理读取按钮点击"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            CustomWarningDialog(self.tr("警告"), self.tr("请先选择要读取的实体。"), parent=self).exec()
            return

        item = selected_items[0]
        entity_id = item.data(Qt.UserRole)
        entity_name = item.text()

        # 创建一个子对话框，包含“读取至sysml2文件”和“读取至界面”按钮
        read_dialog = QDialog(self)
        read_dialog.setWindowTitle(self.tr("读取实体"))
        read_dialog.setFixedSize(180, 100)
        layout = QVBoxLayout(read_dialog)

        to_sysml_button = QPushButton(self.tr("读取至sysml2文件"))
        to_sysml_button.setFixedWidth(160)
        to_sysml_button.clicked.connect(lambda: self.read_entity(entity_id, self.tr("sysml2文件")))
        layout.addWidget(to_sysml_button)

        to_interface_button = QPushButton(self.tr("读取至界面"))
        to_interface_button.setFixedWidth(160)
        to_interface_button.clicked.connect(lambda: self.read_entity(entity_id, self.tr("界面")))
        layout.addWidget(to_interface_button)

        read_dialog.exec()

    def read_entity(self, entity_id, destination):
        """读取实体的具体逻辑"""



        # 实现具体的读取逻辑，这里仅模拟
        # 例如，将实体数据写入sysml2文件或展示在界面上
        # 先打印数据
        print(f"读取实体 '{self.parent.element_data[entity_id]}' 至{destination}。")
        if destination == "sysml2文件":
            # 调用写入文件的方法
            json_input_str = json.dumps(self.parent.element_data[entity_id], ensure_ascii=False)

            content = json_to_sysml2_txt(json_input_str,self.parent.element_data)
            print(content)
        else:
            self.parent.current_selected_entity = entity_id

        CustomInformationDialog(self.tr("成功"), self.tr("已读取实体 '{entity_name}' 至{destination}。").format(entity_name = self.parent.element_data[entity_id]['entity_name'], destination = destination), parent=self).exec()


        # 发射信号
        self.entity_read.emit(entity_id, destination)

    def get_session(self):
        return self.parent.session

    def ask_user_to_select_code_for_name(self, file_attr_name: str) -> typing.Optional[int]:
        """
        使用一个QDialog列出 attribute_code 列表, 让用户选一个 code_id.
        若用户取消 => 返回 None
        若用户确认 => 返回 code_id
        """
        session = self.get_session()
        code_sql = text("""
            SELECT attribute_code_id, attribute_code_name
            FROM attribute_code
            ORDER BY attribute_code_id
        """)
        codes = session.execute(code_sql).fetchall()

        if not codes:
            CustomWarningDialog(self.tr("无可用Code"), self.tr("数据库中无任何 attribute_code 记录。"), parent=self).exec_()
            return None

        dlg = SelectCodeDialog(parent=self, codes=codes, file_attr_name=file_attr_name)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_selected_code_id()
        else:
            return None

    def ask_user_create_definition_for_code(self, code_id: int, file_attr_name: str) -> typing.Optional[int]:
        """
        弹出对话框让用户填写信息, 新建 definition, 返回新建的 attribute_definition_id.
        如果用户取消 => 返回 None
        """
        dlg = CreateDefinitionDialog(parent=self, code_id=code_id, file_attr_name=file_attr_name)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_created_definition_id()
        else:
            return None

    def ask_user_select_behavior_code_for_name(self, perform_name):
        """
        弹出对话框让用户选择 behavior_code_id.
        若用户取消 => 返回 None
        若用户确认 => 返回 behavior_code_id
        """
        session = self.get_session()
        code_sql = text("""
            SELECT behavior_code_id, behavior_name
            FROM behavior_name_code
            ORDER BY behavior_code_id
        """)
        codes = session.execute(code_sql).fetchall()

        if not codes:
            CustomWarningDialog(self.tr("无可用Code"), self.tr("数据库中无任何 behavior_code 记录。"), parent=self).exec_()
            return None

        dlg = SelectCodeDialog(parent=self, codes=codes, file_attr_name=perform_name,type='behavior')
        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_selected_code_id()
        else:
            return None

    def get_type_code_by_id(self, type_id):
        session = self.get_session()
        print(f"443{type_id}")
        type_sql = text("""
            SELECT entity_type_code
            FROM entity_type
            WHERE entity_type_id = :tid
            LIMIT 1
        """)
        type_row = session.execute(type_sql, {"tid": type_id}).fetchone()
        if not type_row:
            return "UnknownType"
        return type_row[0]


# 示例使用
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # 示例原始数据
    entities_data = {
        -15: {
            'entity_id': -15,
            'entity_name': '434',
            'entity_type_id': 2,
            'entity_parent_id': None,
            'scenario_id': 8,
            'create_time': '2025-01-15 15:04:45',
            'update_time': '2025-01-15 15:04:45',
            'categories': [
                {'category_id': 1, 'category_name': 'AffectedElement', 'description': '承灾要素'},
                {'category_id': 2, 'category_name': 'EnvironmentElement', 'description': '环境要素'}
            ],
            'attributes': [
                # 属性数据...
            ],
            'behaviors': []
        },
        # 其他实体...
    }

    app = QApplication(sys.argv)
    dialog = CustomSelectDialog(entities_data)

    # 连接信号以进行进一步处理
    dialog.entity_created.connect(lambda entity: print(f"实体已创建: {entity}"))
    dialog.entity_deleted.connect(lambda entity_id: print(f"实体已删除: {entity_id}"))
    dialog.entity_read.connect(lambda eid, dest: print(f"实体 {eid} 已读取至 {dest}"))

    dialog.show()
    sys.exit(app.exec())