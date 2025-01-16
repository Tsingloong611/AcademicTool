# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: scenario_controller.py
# @Software: PyCharm
import json
from datetime import datetime

from PySide6.QtCore import QObject, Slot, Qt, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.sync import update
from sqlalchemy.sql.base import elements

from models.models import Scenario, BehaviorValue, AttributeValue, Category, Entity, Template, BehaviorValueReference, \
    AttributeValueReference, entity_category
# 假设您已经在 models/scenario.py 中定义了 Scenario 类，
# 其中字段为 scenario_id, scenario_name, scenario_description, ...
from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.login_dialog import LoginDialog
from views.scenario_manager import ScenarioDialog
import logging
import json
from sqlalchemy.orm import Session
from typing import Dict, Any, Union, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class ScenarioController(QObject):
    # 发出查询结果信号
    send_sql_result = Signal(list)
    def __init__(self, scenario_manager, status_bar, tab_widget, db_manager):
        super().__init__()
        self.scenario_id = 1
        self.scenario_manager = scenario_manager
        self.status_bar = status_bar
        self.tab_widget = tab_widget
        self.db_manager = db_manager  # 使用传入的 DatabaseManager 实例
        self.current_scenario = None
        self.session = self.db_manager.get_session()

        # 连接信号
        self.scenario_manager.scenario_selected.connect(self.handle_scenario_selected)
        self.scenario_manager.add_requested.connect(self.handle_add_requested)
        self.scenario_manager.edit_requested.connect(self.handle_edit_requested)
        self.scenario_manager.delete_requested.connect(self.handle_delete_requested)

        self.tab_widget.ElementSettingTab.request_sql_query.connect(self.execute_sql_query)
        self.send_sql_result.connect(self.tab_widget.ElementSettingTab.receive_sql_result)
        self.tab_widget.ElementSettingTab.save_to_database_signal.connect(self.apply_changes_from_json)
        # 加载初始数据
        self.load_scenarios()

        # 从数据库管理器获取连接信息并更新状态栏
        connection_info = self.db_manager.get_connection_info()
        username = connection_info.get('username', '未知用户')
        database = connection_info.get('database', '未知数据库')
        self.status_bar.update_user_info(username, database)

    def load_scenarios(self,selected_scenario_id=None):
        """加载并在界面上显示所有情景"""
        scenarios = self.get_all_scenarios()
        self.scenario_manager.populate_scenarios(scenarios,selected_scenario_id)
        # 初始时保持标签页锁定和占位页面显示
        if scenarios:
            self.tab_widget.show_placeholder(True)
        else:
            self.tab_widget.show_placeholder(True, "请添加情景")

    def get_all_scenarios(self):
        try:
            # 这里注意：Scenario 主键改为 scenario_id
            scenarios = self.session.query(Scenario).all()
            return scenarios
        except SQLAlchemyError as e:
            print(f"Error fetching scenarios: {e}")
            QMessageBox.critical(None, "错误", f"获取情景列表失败: {e}")
            return []

    @Slot(int, str, str)
    def handle_scenario_selected(self, scenario_id, scenario_name, scenario_description):
        """当用户在列表中选择了一个情景时触发"""
        scenario = self.get_scenario_by_id(scenario_id)
        self.scenario_id = scenario_id
        if scenario:
            self.current_scenario = scenario
            # 从数据库管理器获取连接信息
            connection_info = self.db_manager.get_connection_info()
            username = connection_info.get('username', '未知用户')
            database = connection_info.get('database', '未知数据库')

            # 如果 Scenario 中还有 owl_status, bayes_status, updated_at 之类字段，
            # 也要相应做修改与获取；以下仅作示例
            owl_state = getattr(scenario, 'owl_status', "未知")
            bayes_state = getattr(scenario, 'bayes_status', "未知")
            update_time = getattr(scenario, 'scenario_update_time', None)
            if update_time is not None:
                update_time = update_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                update_time = "无"

            self.status_bar.update_status(
                username=username,
                database=database,
                scenario_name=scenario.scenario_name,  # 新字段名
                owl_status=owl_state,
                bayes_status=bayes_state,
                scenario_description=scenario.scenario_description,  # 新字段名
                update_time=update_time
            )

            # 解锁标签页并显示功能区
            self.tab_widget.show_placeholder(False)

            self.tab_widget.ElementSettingTab.session = self.session

            self.static_data = self.get_scenario_data(self.session, scenario_id)
            # 缩进
            self.static_data = json.dumps(self.static_data, indent=4, ensure_ascii=False)

            print(f"得到了{self.static_data}")
            self.static_data = json.loads(self.static_data)

            self.tab_widget.ElementSettingTab.scenario_data = self.static_data
            if not self.static_data["entities"]:
                print("No entities found for the selected scenario.")
                self.tab_widget.ElementSettingTab.element_data = {}
            else:
                entity_data = {
                    entity["entity_id"]: entity for entity in self.static_data["entities"]
                }
                print(f"读取到entity_data: {entity_data}")
                self.tab_widget.ElementSettingTab.element_data = entity_data



        else:
            self.reset_status_bar()

    from typing import Dict, Any
    from sqlalchemy.orm import Session

    def get_scenario_data(self,session: Session, scenario_id: int) -> Dict[str, Any]:
        """
        根据 scenario_id，获取该场景下所有的实体(Entity)、
        以及与实体相关的属性(AttributeValue) / 行为(BehaviorValue) / 类别(Category) 等信息，
        组织成一个包含 scenario + entities + attributes + behaviors 等的字典。
        """
        # 1. 先查询场景自身
        scenario = session.query(Scenario).filter_by(scenario_id=scenario_id).one()

        # 构建最外层 scenario 数据结构
        scenario_data = {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.scenario_name,
            "scenario_description": scenario.scenario_description,
            "scenario_create_time": str(scenario.scenario_create_time),
            "scenario_update_time": str(scenario.scenario_update_time),
            "emergency_id": scenario.emergency_id,
            "entities": []
        }

        # 2. 遍历该 scenario 下的所有 entity
        for entity in scenario.entities:
            # entity 自身信息
            entity_dict = {
                "entity_id": entity.entity_id,
                "entity_name": entity.entity_name,
                "entity_type_id": entity.entity_type_id,
                "entity_parent_id": entity.entity_parent_id,
                "scenario_id": entity.scenario_id,
                "create_time": str(entity.create_time),
                "update_time": str(entity.update_time),
                "categories": [],
                "attributes": [],
                "behaviors": []
            }

            # 3. 收集多对多关联的 category
            for cat in entity.categories:
                entity_dict["categories"].append({
                    "category_id": cat.category_id,
                    "category_name": cat.category_name,
                    "description": cat.description
                })

            # 4. 收集该 entity 的所有 attribute_value
            for av in entity.attribute_values:
                attr_def = av.attribute_definition

                attribute_item = {
                    "attribute_value_id": av.attribute_value_id,
                    "attribute_definition_id": attr_def.attribute_definition_id,
                    "attribute_name": av.attribute_name,
                    "china_default_name": attr_def.china_default_name,
                    "english_default_name": attr_def.english_default_name,
                    "attribute_code_name": attr_def.attribute_code.attribute_code_name,  # 对应 attribute_code
                    "attribute_aspect_name": attr_def.attribute_aspect.attribute_aspect_name,  # 对应 attribute_aspect
                    "attribute_type_code": attr_def.attribute_type.attribute_type_code,  # 对应 attribute_type
                    "is_required": bool(attr_def.is_required),
                    "is_multi_valued": bool(attr_def.is_multi_valued),
                    "is_reference": bool(attr_def.is_reference),
                    "reference_target_type_id": attr_def.reference_target_type_id,
                    "default_value": attr_def.default_value,
                    "description": attr_def.description,
                    # 存储在 attribute_value 表里的值
                    "attribute_value": av.attribute_value,
                    # 若是引用型属性，可收集其 references
                    "referenced_entities": []
                }

                # 如果是引用型 (attr_def.is_reference = True)，检查 attribute_value_reference
                if attr_def.is_reference:
                    for ref in av.references:
                        attribute_item["referenced_entities"].append({
                            "referenced_entity_id": ref.referenced_entity_id
                        })

                entity_dict["attributes"].append(attribute_item)

            # 5. 收集该 entity 的所有行为(behavior_value)
            #    由于 model 中定义: entity.behavior_values => BehaviorValue
            for bv in entity.behavior_values:
                bh_def = bv.behavior_definition
                # 提取 BehaviorDefinition 的中文、英文名、行为代码等信息
                # 如需还原旧字段 "behavior_name"，可以用 bh_def.china_default_name
                # 也可以添加 "english_behavior_name": bh_def.english_default_name

                # 获取 behavior_code 表中的代码名称
                #   bh_def.behavior_code_ref 是 BehaviorCode 对象
                #   bh_def.behavior_code_ref.behavior_code_name 即数据库 behavior_code.behavior_code_name
                behavior_item = {
                    "behavior_value_id": bv.behavior_value_id,
                    "behavior_definition_id": bh_def.behavior_definition_id,

                    # 原先的 "behavior_name" 用中文名替代
                    "behavior_name": bh_def.behavior_code_ref.behavior_code_name,
                    "china_default_name": bh_def.china_default_name,
                    "english_behavior_name": bh_def.english_default_name,

                    # 代码名称(如果需要)
                    "behavior_code_name": bh_def.behavior_code_ref.behavior_code_name if bh_def.behavior_code_ref else None,

                    "object_entity_type_id": bh_def.object_entity_type_id,
                    "is_required": bool(bh_def.is_required),
                    "is_multi_valued": bool(bh_def.is_multi_valued),
                    "description": bh_def.description,
                    "create_time": str(bv.create_time),
                    "update_time": str(bv.update_time),
                    # 如果该行为还引用其他对象实体(behavior_value_reference)，可在此收集
                    "object_entities": []
                }

                # bv.references => BehaviorValueReference
                for ref in bv.references:
                    behavior_item["object_entities"].append({
                        "object_entity_id": ref.object_entity_id
                    })

                entity_dict["behaviors"].append(behavior_item)

            # 将完整的 entity_dict 加入 scenario_data
            scenario_data["entities"].append(entity_dict)

        return scenario_data

    def apply_changes_from_json(session: Session, scenario_data: Dict[str, Any]) -> None:
        """
        回写逻辑:
        1. 若 scenario_id 存在且>0 => 更新; 若没有 => 新建
        2. entity_id>0 => UPDATE; entity_id<=0 => INSERT
        3. attribute_value_id>0 => UPDATE; 否则 => INSERT
        4. behavior_value_id>0 => UPDATE; 否则 => INSERT
        5. 处理引用 (attribute_value_reference, behavior_value_reference):
           - 若 refer id>0 => 直接指向已有实体
           - 若 refer id<0 => 需先新建对应实体, flush 出其id后再指向
        """

        # 0. 建立 "临时ID -> 实际ID" 的映射缓存，用来处理新建对象之间的引用
        temp_id_map: Dict[int, int] = {}  # 存储 {负数ID: 数据库生成的正数ID}

        # ----------------------------------------------------------------
        # 1. 处理 scenario 本身
        # ----------------------------------------------------------------
        sc_id = scenario_data.get("scenario_id", None)
        if sc_id and sc_id > 0:
            # 已存在 => 查找并更新
            scenario_obj = session.query(Scenario).get(sc_id)
            if not scenario_obj:
                raise ValueError(f"Scenario with ID={sc_id} not found in DB.")
            # 可以更新 scenario_name / scenario_description 等, 这里只示范 name
            if "scenario_name" in scenario_data:
                scenario_obj.scenario_name = scenario_data["scenario_name"]
            if "scenario_description" in scenario_data:
                scenario_obj.scenario_description = scenario_data["scenario_description"]
            # 不需要 manually add, 因为 scenario_obj 已是持久化对象
        else:
            # 没 ID 或 ID<=0 => 新建一个 scenario
            scenario_obj = Scenario(
                scenario_name=scenario_data.get("scenario_name", "新场景"),
                scenario_description=scenario_data.get("scenario_description", None),
                # 其余字段(如 emergency_id) 按需补充
            )
            session.add(scenario_obj)
            session.flush()  # 以便获得新的 scenario_id

        # ----------------------------------------------------------------
        # 2. 处理 entities
        # ----------------------------------------------------------------
        entities_data: List[Dict[str, Any]] = scenario_data.get("entities", [])

        # 函数内部：存储从 JSON -> 数据库 Entity对象 的映射, 以便后续引用
        entity_map: Dict[Union[int, None], Entity] = {}

        for ent_data in entities_data:
            e_id = ent_data.get("entity_id", None)
            if e_id and e_id > 0:
                # 已存在 => UPDATE
                entity_obj = session.query(Entity).get(e_id)
                if not entity_obj:
                    raise ValueError(f"Entity with ID={e_id} not found.")
                # 更新字段
                entity_obj.entity_name = ent_data.get("entity_name", entity_obj.entity_name)
                entity_obj.entity_type_id = ent_data.get("entity_type_id", entity_obj.entity_type_id)
                # 也可更新 entity_parent_id, scenario_id 等
            else:
                # 新建
                entity_obj = Entity(
                    entity_name=ent_data.get("entity_name", "新Entity"),
                    entity_type_id=ent_data.get("entity_type_id", 1),  # 默认1 => Vehicle
                    scenario_id=scenario_obj.scenario_id,
                )
                session.add(entity_obj)
                session.flush()  # 让数据库自动生成 entity_id

                # 若 JSON 中是一个负数, 则记录到 temp_id_map
                if e_id and e_id < 0:
                    temp_id_map[e_id] = entity_obj.entity_id

            # 无论新建还是更新，都放到 entity_map
            # 注意: 这里 e_id 若为 None, 也可以作为key
            entity_map[e_id] = entity_obj

            # ----------------------------------------------------------------
            # 2.1. 处理 categories (多对多)
            # ----------------------------------------------------------------
            entity_obj.categories.clear()  # 简化处理：先清空，再根据 JSON 重新添加
            for cat_data in ent_data.get("categories", []):
                # cat_data 可能同时有 "category_id" / "category_name"
                c_id = cat_data.get("category_id")
                if c_id:
                    category_obj = session.query(Category).get(c_id)
                    # 若找不到, 也可自行决定报错 或者 新建 Category
                    if not category_obj:
                        raise ValueError(f"Category ID={c_id} not found.")
                    entity_obj.categories.append(category_obj)
                else:
                    # 没有 category_id => 根据 name 查或者新建
                    cat_name = cat_data.get("category_name", None)
                    if not cat_name:
                        continue
                    category_obj = session.query(Category).filter_by(category_name=cat_name).first()
                    if not category_obj:
                        # 新建 Category, 仅示例
                        category_obj = Category(category_name=cat_name)
                        session.add(category_obj)
                        session.flush()
                    entity_obj.categories.append(category_obj)

            # ----------------------------------------------------------------
            # 2.2. 处理 attributes (AttributeValue)
            # ----------------------------------------------------------------
            for attr_data in ent_data.get("attributes", []):
                av_id = attr_data.get("attribute_value_id", None)
                if av_id and av_id > 0:
                    # 更新
                    av_obj = session.query(AttributeValue).get(av_id)
                    if not av_obj:
                        raise ValueError(f"AttributeValue ID={av_id} not found.")
                    av_obj.attribute_value = attr_data.get("attribute_value", av_obj.attribute_value)
                else:
                    # 新建
                    definition_id = attr_data["attribute_definition_id"]
                    av_obj = AttributeValue(
                        entity_id=entity_obj.entity_id,
                        attribute_definition_id=definition_id,
                        attribute_value=attr_data.get("attribute_value", None)
                    )
                    session.add(av_obj)
                    session.flush()

                # 处理引用 (attribute_value_reference)
                # 先清空原有引用 (若要保留原引用，则需做差异更新; 此处简单做覆盖)
                av_obj.references.clear()
                for ref_data in attr_data.get("referenced_entities", []):
                    ref_id = ref_data["referenced_entity_id"]  # 可能是正数, 也可能是负数
                    real_ref_id = None
                    if ref_id > 0:
                        real_ref_id = ref_id  # 已存在实体
                    else:
                        # 负数 => 新建(或已新建)对应实体, 要到 temp_id_map 找
                        if ref_id in temp_id_map:
                            real_ref_id = temp_id_map[ref_id]
                        else:
                            raise ValueError(f"Referenced entity with temp ID={ref_id} not created yet.")
                    # 添加关系
                    avr = AttributeValueReference(
                        attribute_value_id=av_obj.attribute_value_id,
                        referenced_entity_id=real_ref_id
                    )
                    session.add(avr)
                # end of attribute_value

            # ----------------------------------------------------------------
            # 2.3. 处理 behaviors (BehaviorValue)
            # ----------------------------------------------------------------
            for bhv_data in ent_data.get("behaviors", []):
                bv_id = bhv_data.get("behavior_value_id", None)
                if bv_id and bv_id > 0:
                    # 更新
                    bv_obj = session.query(BehaviorValue).get(bv_id)
                    if not bv_obj:
                        raise ValueError(f"BehaviorValue ID={bv_id} not found.")
                    # 也可以更新 behavior_definition_id, ...
                else:
                    # 新建
                    def_id = bhv_data["behavior_definition_id"]
                    bv_obj = BehaviorValue(
                        behavior_definition_id=def_id,
                        subject_entity_id=entity_obj.entity_id
                    )
                    session.add(bv_obj)
                    session.flush()

                    if bv_id and bv_id < 0:
                        temp_id_map[bv_id] = bv_obj.behavior_value_id

                # 清空引用(behavior_value_reference)
                bv_obj.references.clear()
                for ref_data in bhv_data.get("object_entities", []):
                    obj_eid = ref_data["object_entity_id"]
                    if obj_eid > 0:
                        real_eid = obj_eid
                    else:
                        # 在 temp_id_map中找
                        if obj_eid in temp_id_map:
                            real_eid = temp_id_map[obj_eid]
                        else:
                            raise ValueError(f"Referenced entity with temp ID={obj_eid} not created yet.")
                    bvr = BehaviorValueReference(
                        behavior_value_id=bv_obj.behavior_value_id,
                        object_entity_id=real_eid
                    )
                    session.add(bvr)
        # end for ent_data in entities

        # ----------------------------------------------------------------
        # 最后, commit 提交所有改动
        # ----------------------------------------------------------------
        session.commit()
        print("JSON回写数据库成功。")

    def reset_status_bar(self):
        """重置状态栏的内容"""
        connection_info = self.db_manager.get_connection_info()
        username = connection_info.get('username', '未知用户')
        database = connection_info.get('database', '未知数据库')
        self.status_bar.update_status(
            username,
            database,
            scenario_name="等待情景加载",
            owl_status="等待情景加载",
            bayes_status="等待情景加载",
            scenario_description="等待情景加载",
            update_time = "等待情景加载"
        )
        self.tab_widget.show_placeholder()

    @Slot()
    def handle_add_requested(self):
        """用户点击“添加情景”按钮时执行"""
        dialog = ScenarioDialog(self.scenario_manager)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                CustomWarningDialog("添加失败", "情景名称不能为空。").exec()
                return
            new_scenario = self.add_scenario(name, description)
            if new_scenario:
                self.load_scenarios(new_scenario.scenario_id)
                # 自动加载
                self.handle_scenario_selected(new_scenario.scenario_id,new_scenario.scenario_name,new_scenario.scenario_description)


    @Slot()
    def handle_edit_requested(self):
        """用户点击“编辑情景”按钮时执行"""
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            CustomWarningDialog("警告", "请选择要修改的情景。").exec()
            return
        scenario_id = current_item.data(Qt.UserRole)
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            CustomWarningDialog("警告", "未找到选中的情景。").exec()
            return

        dialog = ScenarioDialog(self.scenario_manager, scenario=scenario)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                CustomWarningDialog("修改失败", "情景名称不能为空。").exec()
                return
            updated = self.update_scenario(scenario_id, name, description)
            if updated:
                self.load_scenarios()
                if self.current_scenario and self.current_scenario.scenario_id == scenario_id:
                    # 也可以更新状态栏 (如果有需要)
                    pass

    @Slot()
    def handle_delete_requested(self, scenario_id):
        """用户点击“删除情景”按钮时执行"""
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            CustomWarningDialog("警告", "请选择要删除的情景。").exec()
            return
        scenario_id = current_item.data(Qt.UserRole)


        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            CustomWarningDialog("警告", "未找到选中的情景。").exec()
            return
        self.scenario_manager.list_widget.setCurrentItem(None)

        self.get_result_by_sql(f"DELETE FROM scenario WHERE scenario_id = {scenario_id}")
        self.load_scenarios()
        if self.current_scenario and self.current_scenario.scenario_id == scenario_id:
            self.current_scenario = None
            self.reset_status_bar()

    def add_scenario(self, scenario_name, scenario_description=''):
        """在数据库中插入新情景"""
        try:
            # 创建新的 Scenario 实例
            new_scenario = Scenario(
                scenario_name=scenario_name,
                scenario_description=scenario_description,
                scenario_create_time=datetime.utcnow(),  # Set to current UTC time
                scenario_update_time=datetime.utcnow(),  # Optionally set update time
                emergency_id=1  # 根据实际需求调整
            )
            self.session.add(new_scenario)
            self.session.commit()  # 提交以获取 new_scenario 的 ID

#            self.replicate_all_for_scenario(new_scenario.scenario_id) TO DO 暂时废除

            # 提交所有新的 Element 实例
            self.session.commit()
            self.session.refresh(new_scenario)
            return new_scenario
            # 查找新添加的情景并选中

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding scenario: {e}")
            CustomErrorDialog("错误", f"新增情景失败: {e}").exec()
            return None


    def update_scenario(self, scenario_id, scenario_name=None, scenario_description=None):
        """更新情景信息"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            if not scenario:
                return None
            if scenario_name:
                scenario.scenario_name = scenario_name
            if scenario_description:
                scenario.scenario_description = scenario_description
            self.session.commit()
            self.session.refresh(scenario)
            return scenario
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error updating scenario: {e}")
            CustomErrorDialog("错误", f"修改情景失败: {e}").exec()
            return None

    def delete_scenario(self, scenario_id):
        """删除指定情景"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            if not scenario:
                return False
            self.session.delete(scenario)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error deleting scenario: {e}")
            CustomErrorDialog("错误", f"删除情景失败: {e}").exec()
            return False

    def get_scenario_by_id(self, scenario_id):
        """根据ID获取情景"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            return scenario
        except SQLAlchemyError as e:
            print(f"Error fetching scenario by id: {e}")
            return None

    # 废弃方法
    # @Slot()
    # def open_database_login_dialog(self):
    #     """打开数据库登录对话框"""
    #     dialog = LoginDialog(self.session, self.scenario_manager)
    #     dialog.login_success.connect(self.handle_database_connected)
    #     if dialog.exec() == QDialog.Accepted:
    #         CustomInformationDialog("成功", "已成功连接到数据库。").exec()
    #         self.load_scenarios()
    #     else:
    #         CustomInformationDialog("错误", "无法连接到数据库。").exec()
    #
    # @Slot()
    # def handle_database_connected(self):
    #     """数据库登录成功后刷新情景列表"""
    #     CustomInformationDialog("成功", "已成功连接到数据库。").exec()
    #     self.load_scenarios()

    def get_element_by_scenario_id(self,scenario_id):
        pass

    def execute_sql_query(self, sql_query):
        print("执行查询")
        # 执行 SQL 查询
        result = self.get_result_by_sql(sql_query)
        # 发出查询结果信号
        self.send_sql_result.emit(result)

    def get_result_by_sql(self, sql_query):
        try:
            # 执行查询
            result = self.session.execute(text(sql_query)).fetchall()
            print(f"查询结果: {result}")
            return result
        except Exception as e:
            print(f"执行 SQL 查询时出错: {e}")
            return []

    def __del__(self):
        if self.session:
            self.session.close()
            print("Session closed.")


    def replicate_all_for_scenario(self, scenario_id: int):
        """
        1) 根据 scenario_id 获取该场景。
        2) 遍历数据库中所有(或特定) Template，为每个 Template 在该场景下新建一个 Entity。
        3) 为该新 Entity:
           - 附加模板所指定的 category
           - 不管 is_required 与否，对 template.attribute_definitions 中的每个属性都建一条 AttributeValue
           - 同理，对 template.behavior_definitions 中的每个行为都建一条 BehaviorValue
        4) 最后 commit。
        """

        # 0. 找到目标场景
        scenario_obj = self.session.query(Scenario).get(scenario_id)
        if not scenario_obj:
            raise ValueError(f"Scenario(id={scenario_id}) not found.")

        # 1. 获取要复制的所有模板 (可根据业务需求，添加 filter)
        all_templates = self.session.query(Template).all()

        # 2. 遍历模板，新建实体
        for tpl in all_templates:
            # 2.1 创建一个 entity 对象
            new_entity = Entity(
                entity_name=f"{tpl.template_name}_复制品",
                entity_type_id=tpl.entity_type_id,
                scenario_id=scenario_obj.scenario_id,
                create_time=datetime.utcnow(),
                update_time=datetime.utcnow()
            )
            self.session.add(new_entity)
            self.session.flush()  # 拿到 new_entity.entity_id

            # 2.2 附加模板的 category 到新实体上
            #     template.category_id -> 找到 Category 后 append
            cat_obj = self.session.query(Category).get(tpl.category_id)
            if cat_obj:
                new_entity.categories.append(cat_obj)

            # 2.3 遍历 template.attribute_definitions，对每条都创建 AttributeValue
            for attr_def in tpl.attribute_definitions:
                av = AttributeValue(
                    entity_id=new_entity.entity_id,
                    attribute_definition_id=attr_def.attribute_definition_id,
                    attribute_value=attr_def.default_value,  # 可以用默认值，也可设为 None
                    create_time=datetime.utcnow(),
                    update_time=datetime.utcnow()
                )
                self.session.add(av)
                # 不一定要 flush()，可留到 commit 一并提交

            # 2.4 遍历 template.behavior_definitions，对每条都创建 BehaviorValue
            for bhv_def in tpl.behavior_definitions:
                bv = BehaviorValue(
                    behavior_definition_id=bhv_def.behavior_definition_id,
                    subject_entity_id=new_entity.entity_id,
                    create_time=datetime.utcnow(),
                    update_time=datetime.utcnow()
                )
                self.session.add(bv)

        # 3. 一次性 commit
        self.session.commit()
        print(f"复制完成: scenario_id={scenario_id} 已新增 {len(all_templates)} 个entity。")