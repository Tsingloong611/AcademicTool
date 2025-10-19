# -*- coding: utf-8 -*-
# @Time    : 1/22/2025 8:02 PM
# @FileName: plan.py
# @Software: PyCharm
import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime

import pandas as pd
import requests
from PySide6.QtCore import QTimer, QThread, QCoreApplication
from jedi.inference.gradual.typing import Tuple
from semantictools import config_path
from sqlalchemy import select, and_, create_engine, text, bindparam
from sqlalchemy.orm import Session, sessionmaker
from typing import Dict, List, Optional, Any

from models.models import AttributeValue, Entity, AttributeDefinition, AttributeCode, EntityType, Template, Category, \
    PosterioriData, BayesNode, BayesNodeState, AttributeValueReference
from utils.get_config import get_cfg
from views.dialogs.custom_warning_dialog import CustomWarningDialog


class PlanDataCollector:
    def __init__(self, session: Session, scenario_id: int):
        """
        初始化计划数据收集器

        Args:
            session: SQLAlchemy会话
            scenario_id: 场景ID
        """
        self.session = session
        self.scenario_id = scenario_id

    def get_road_passibility(self) -> List[Any]:
        """获取道路通行性数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND (ac.attribute_code_name = 'ClosureCondition'
        OR(ac.attribute_code_name = 'RoadClosureStatus' AND e.entity_parent_id IS NOT NULL))
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_road_damage(self) -> List[Any]:
        """获取道路损毁数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND (
            ac.attribute_code_name = 'RoadDamageCondition' 
            OR 
            (ac.attribute_code_name = 'FacilityDamageStatus' AND e.entity_parent_id IS NOT NULL)
        )
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_road_position(self) -> Tuple:
        # 查询满足条件的第一个实体
        first_entity = self.session.query(Entity) \
            .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
            .filter(
            Entity.scenario_id == self.scenario_id,
            EntityType.entity_type_code == 'Road'
        ) \
            .order_by(Entity.entity_id) \
            .first()

        if first_entity is None:
            # 如果没有满足条件的实体，返回空元组
            return tuple()

        # 查询第一个实体的属性值
        results = self.session.query(AttributeValue.attribute_value) \
            .join(AttributeDefinition,
                  AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
            .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
            .filter(
            AttributeValue.entity_id == first_entity.entity_id,
            AttributeCode.attribute_code_name.in_(['RoadName','SegmentStartStakeNumber', 'SegmentEndStakeNumber'])
        ).all()

        # 把查询结果打包成一个扁平的元组
        result_tuple = tuple(item[0] for item in results)
        return result_tuple

    def get_resource_positions(self,plan_name) -> List:
        # 查询所有满足条件的实体,父实体为None
        if not plan_name:
            entities = self.session.query(Entity) \
                .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
                .filter(
                Entity.scenario_id == self.scenario_id,
                EntityType.entity_type_code == 'ResponseResource',
                Entity.entity_parent_id.is_(None)
            ) \
                .all()
        else:
            # 根据plan_name找到plan的entity_id
            plan_id = self.session.query(Entity.entity_id) \
                .filter(
                Entity.entity_name == plan_name,
                Entity.scenario_id == self.scenario_id
            ).scalar()
            entities = self.session.query(Entity) \
                .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
                .filter(
                Entity.scenario_id == self.scenario_id,
                EntityType.entity_type_code == 'ResponseResource',
                Entity.entity_parent_id == plan_id
            ) \
                .all()

        # 逐个查询实体的属性值
        results = []
        for entity in entities:
            result = self.session.query(AttributeValue.attribute_value) \
                .join(AttributeDefinition,
                      AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
                .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
                .filter(
                AttributeValue.entity_id == entity.entity_id,
                AttributeCode.attribute_code_name == 'Location'
            ).all()

            # 把查询结果打包成一个扁平的元组
            result = [item[0] for item in result][0]
            results.append(result)

        return results

    def get_casualties(self) -> List[Any]:
        """获取人员伤亡数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN entity_type et ON e.entity_type_id = et.entity_type_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND et.entity_type_code = 'People'
        AND ac.attribute_code_name = 'CasualtyCondition'
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_emergency_period(self) -> List[Any]:
        """获取应急时长数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN entity_type et ON e.entity_type_id = et.entity_type_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND et.entity_type_code = 'Vehicle'
        AND ac.attribute_code_name = 'EmergencyPeriod'
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_resource_usage(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """获取资源使用情况"""
        if plan_name:
            # 先获取plan_id
            plan_sql = """
            SELECT entity_id FROM entity
            WHERE entity_name = :plan_name
            AND scenario_id = :scenario_id
            """
            plan_id = self.session.execute(text(plan_sql),
                                           {"plan_name": plan_name,
                                            "scenario_id": self.scenario_id}).scalar()

            if not plan_id:
                return {}

            sql = """
            SELECT av.*, ac.attribute_code_name FROM attribute_value av
            JOIN entity e ON av.entity_id = e.entity_id
            JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
            JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
            WHERE e.entity_parent_id = :plan_id
            AND e.scenario_id = :scenario_id
            AND ac.attribute_code_name IN ('AidResource', 'TowResource', 
                                         'FirefightingResource', 'RescueResource')
            """
            results = self.session.execute(text(sql),
                                           {"plan_id": plan_id,
                                            "scenario_id": self.scenario_id}).all()
        else:
            sql = """
            SELECT av.*, ac.attribute_code_name FROM attribute_value av
            JOIN entity e ON av.entity_id = e.entity_id
            JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
            JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
            WHERE e.entity_parent_id IS NULL
            AND e.scenario_id = :scenario_id
            AND ac.attribute_code_name IN ('AidResource', 'TowResource', 
                                         'FirefightingResource', 'RescueResource')
            """
            results = self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

        return {result.attribute_code_name: result[0] for result in results}

    def get_related_resource(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """获取处置时长数据"""

        if plan_name:
            plan_sql = """
            SELECT entity_id FROM entity
            WHERE entity_name = :plan_name
            AND scenario_id = :scenario_id
            """
            plan_id = self.session.execute(text(plan_sql),
                                           {"plan_name": plan_name,
                                            "scenario_id": self.scenario_id}).scalar()

            if not plan_id:
                return {}

            action_sql = """
            SELECT e.entity_id FROM entity e
            JOIN entity_type et ON e.entity_type_id = et.entity_type_id
            WHERE e.entity_parent_id = :plan_id
            AND e.scenario_id = :scenario_id
            AND et.entity_type_code = 'ResponseAction'
            """
            action_ids = self.session.execute(text(action_sql),
                                              {"plan_id": plan_id,
                                               "scenario_id": self.scenario_id}).scalars().all()
        else:
            action_sql = """
            SELECT e.entity_id FROM entity e
            JOIN entity_type et ON e.entity_type_id = et.entity_type_id
            WHERE e.entity_parent_id IS NULL
            AND e.scenario_id = :scenario_id
            AND et.entity_type_code = 'ResponseAction'
            """
            action_ids = self.session.execute(text(action_sql),
                                              {"scenario_id": self.scenario_id}).scalars().all()

        if not action_ids:
            return {}

        ids_str = ','.join(str(id) for id in action_ids)
        attribute_sql = f"""
        SELECT av.*, ac.attribute_code_name 
        FROM attribute_value av
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE av.entity_id IN ({ids_str})
        AND ac.attribute_code_name IN ('BehaviorType', 'ImplementationCondition', 'Duration')
        """
        results = self.session.execute(text(attribute_sql)).all()

        result_dict = defaultdict(list)
        for result in results:
            result_dict[result.attribute_code_name].append(result.attribute_value)

        return dict(result_dict)

    def get_emergency_type(self) -> int:
        """获取应急类型数据"""
        # 查看有没有vehicle且属于承灾体的entity
        sql = """
        SELECT * FROM entity e
        JOIN entity_category ec ON e.entity_id = ec.entity_id
        WHERE e.scenario_id = :scenario_id
        AND e.entity_type_id = (SELECT entity_type_id FROM entity_type WHERE entity_type_code = 'Vehicle')
        AND ec.category_id = (SELECT category_id FROM category WHERE category_name = 'AffectedElement')
        """
        # 执行查询，看是不是空，如果不是，返回Collision_Acident
        if self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all():
            return 2

        # 查看抛洒与侧翻情况
        results = self.session.query(AttributeValue.attribute_value) \
            .join(Entity, AttributeValue.entity_id == Entity.entity_id) \
            .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
            .join(AttributeDefinition,
                  AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
            .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
            .filter(
            Entity.scenario_id == self.scenario_id,
            EntityType.entity_type_code == 'Vehicle',
            AttributeCode.attribute_code_name.in_(['SpillCondition', 'RollOverCondition'])
        ).all()

        # 检查返回的每个 attribute_value
        for (value,) in results:
            # 根据数据类型做判断，可根据实际情况调整
            if value in (1, True) or str(value).lower() in ('1', 'true'):
                return 0

        return 1


    def get_all_plan_ids(self) -> List[str]:
        """获取所有计划名称"""
        sql = """
        SELECT entity_id FROM entity
        WHERE entity_type_id = (SELECT entity_type_id FROM entity_type WHERE entity_type_code = 'ResponsePlan')
        AND scenario_id = :scenario_id
        """
        return [result[0] for result in self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()]

    def collect_all_data(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """
        收集所有数据

        Args:
            plan_name: 可选的计划名称。若指定，获取该计划的资源使用和处置时长数据；
                      若不指定，获取parent_id为空的资源使用和处置时长数据

        Returns:
            包含所有收集数据的字典
        """
        data = {
            'road_passibility': self.get_road_passibility(),
            'road_damage': self.get_road_damage(),
            'casualties': self.get_casualties(),
            'related_resource': self.get_related_resource(plan_name),
            'emergency_period': self.get_emergency_period(),
            'emergency_type': self.get_emergency_type(),
            'road_position':self.get_road_position(),
            'resource_positions': self.get_resource_positions(plan_name)
        }
        print(f"data: {data}")

        return data


def get_coordinates_from_stake(road_name, stake_number, api_key):
    """
    根据道路名称和桩号查询经纬度。

    :param road_name: 道路名称，如 "山西省朔州市某高速公路"
    :param stake_number: 桩号，例如 "1"
    :param api_key: 你的高德地图 API Key
    :return: 如果查询成功返回 (经度, 纬度) 的元组，否则返回 None
    """
    # 构造查询地址，例如 "山西省朔州市某高速公路 桩号 1"
    address = f"{road_name} 桩号 {stake_number}"
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        'address': address,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        if data.get('status') == '1' and data.get('geocodes'):
            # 取第一个匹配结果
            location = data['geocodes'][0]['location']  # 格式 "经度,纬度"
            lon, lat = location.split(',')
            return lon, lat
        else:
            print("查询失败，返回数据:", data)
            return None
    except Exception as e:
        print("请求异常:", e)
        return None


def get_driving_distance(origin, destination, api_key):
    """
    根据起点和终点坐标调用高德驾车路径规划 API 获取行驶距离。

    :param origin: 起点坐标元组 (经度, 纬度)，例如 (112.4328, 39.338005)
    :param destination: 终点坐标元组 (经度, 纬度)
    :param api_key: 高德地图 API Key
    :return: 行驶距离（单位：米），如果查询失败返回 None
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "key": api_key,
        # 可以设置 extensions 参数为 "all" 以获得更详细的路径信息
        "extensions": "base"
    }

    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") == "1" and data.get("route"):
        paths = data["route"].get("paths", [])
        if paths:
            first_path = paths[0]
            distance = first_path.get("distance")  # 单位为米，返回的是字符串
            return int(distance) if distance else None
    return None

def get_driving_time(origin, destination, api_key):
    """
    根据起点和终点坐标调用高德驾车路径规划 API 获取行驶时间。

    :param origin: 起点坐标元组 (经度, 纬度)，例如 (112.4328, 39.338005)
    :param destination: 终点坐标元组 (经度, 纬度)
    :param api_key: 高德地图 API Key
    :return: 行驶时间（单位：s），如果查询失败返回 None
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "key": api_key,
        # 可以设置 extensions 参数为 "all" 以获得更详细的路径信息
        "extensions": "base"
    }

    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") != "1":
        print("请求失败，返回数据:", data)

    if data.get("status") == "1" and data.get("route"):
        paths = data["route"].get("paths", [])
        if paths:
            first_path = paths[0]
            duration = first_path.get("duration")  # 单位为秒
            if duration:
                print(f"duration: {duration}")
            else:
                print("duration is None")
                print("data: ", data)
            return int(duration) if duration else None
    return None

def get_coordinates_from_stake_by_file(stake_number):
    try:
        # 设置 Excel 文件路径
        excel_path = os.path.join(os.path.dirname(__file__), '../data/required_information/road_position_information.xlsx')

        # 读取 Excel 文件中的数据，指定需要的列（桩号、经度、纬度）
        df = pd.read_excel(excel_path, header=0)
        print(df.head())

        # 查找给定桩号的行
        stake_data = df[df['桩号名称'] == stake_number]

        if not stake_data.empty:
            # 提取经纬度
            longitude = stake_data['经度'].values[0]
            latitude = stake_data['维度'].values[0]
            print(f"桩号 {stake_number} 对应的经纬度为 ({longitude}, {latitude})")
            return (longitude, latitude)
        else:
            print(f"未找到桩号 {stake_number} 的数据")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None


def convert_to_evidence(data: Dict[str, Any], time_stage: str = "t0") -> Dict[str, Any]:
    """
    【全面改进版】
    根据明确的 T0-T3 阶段定义，全面重构 BN 证据生成逻辑，并增加健壮性和日志。

    - T0 (事故发生前): 系统正常状态，无负面证据。
    - T1 (事故发生瞬间): 引入所有事故相关的负面证据。
    - T2 (应急资源到位): 在T1基础上，引入响应时长和资源就绪的证据。
    - T3 (应急处置后): 在T2基础上，引入处置时长证据，并根据已实施的行为逆转负-面证据。
    """
    logging.info(f"--- [EVIDENCE GENERATION] STAGE: {time_stage} ---")

    evidence = {}

    # --------------------------------------------------------------------
    # 步骤 1: 提取并预处理所有可能用到的原始数据
    # --------------------------------------------------------------------

    # a) 事故负面信息
    road_passibility_data = data.get('road_passibility', [])
    impassable_values = {'1', 'true'}
    is_impassable = any(str(record[4]).strip().lower() in impassable_values for record in road_passibility_data)
    logging.debug(f"原始数据'is_impassable': {is_impassable}")

    road_damage_data = data.get('road_damage', [])
    damage_values = {'1', 'true'}
    is_damaged = any(str(record[4]).strip().lower() in damage_values for record in road_damage_data)
    logging.debug(f"原始数据'is_damaged': {is_damaged}")

    casualties_data = data.get('casualties', [])
    has_casualties = bool(casualties_data and str(casualties_data[0][-1]).lower() in ('1', 'true'))
    logging.debug(f"原始数据'has_casualties': {has_casualties}")

    # b) 环境与类型信息
    emergency_period_data = data.get('emergency_period', [])
    emergency_type = data.get('emergency_type', 0)

    # c) 应急预案信息 (即使为空也要安全处理)
    related_resource = data.get('related_resource', {})
    implemented_behaviors = set()
    durations = related_resource.get('Duration', []) or []
    behavior_types = related_resource.get('BehaviorType', []) or []
    implementation_conditions = related_resource.get('ImplementationCondition', []) or []

    for i, behavior in enumerate(behavior_types):
        if behavior and i < len(implementation_conditions):
            impl_cond = implementation_conditions[i]
            is_active = (isinstance(impl_cond, str) and impl_cond.strip().lower() in ['1', 'true']) or \
                        (not isinstance(impl_cond, str) and bool(int(impl_cond)) if impl_cond is not None else False)
            if is_active:
                implemented_behaviors.add(behavior)
    logging.debug(f"预案中已实施的行为: {implemented_behaviors or '无'}")

    # --------------------------------------------------------------------
    # 步骤 2: 根据阶段 (time_stage) 构建证据字典
    # --------------------------------------------------------------------

    # --- 基础证据 (所有阶段共有) ---
    evidence['emergencyType'] = emergency_type

    emergency_period_map_dict = {
        '凌晨': 0, '上午': 1, '下午': 2, '晚上': 3,
        'Earlymorning': 0, 'Morning': 1, 'Afternoon': 2, 'Evening': 3
    }
    if emergency_period_data:
        period_str = emergency_period_data[0][-1]
        evidence['emergencyPeriod'] = emergency_period_map_dict.get(period_str)

    # --- 阶段性证据构建 ---

    # 默认资源位为0 (未动用)
    resource_nodes = ["AidResource", "TowResource", "FirefightingResource", "RescueResource"]
    for node in resource_nodes:
        evidence[node] = 0

    if time_stage == "t0":
        # T0: 事故发生前，一切正常
        logging.info("阶段T0: 设置系统为正常状态。")
        evidence['roadPassibility'] = 1  # 1=通行
        evidence['roadLoss'] = 0  # 0=无损坏
        evidence['casualties'] = 0  # 0=无伤亡

    else:  # T1, T2, T3 均基于事故已发生
        # 步骤 2.1: 设置事故造成的初始负面状态 (这是T1, T2, T3的基线)
        logging.info("阶段T1/T2/T3基线: 引入事故初始负面证据。")
        evidence['roadPassibility'] = 0 if is_impassable else 1
        evidence['roadLoss'] = 1 if is_damaged else 0
        evidence['casualties'] = 1 if has_casualties else 0

        # T1 阶段到此结束
        if time_stage == "t1":
            logging.info("阶段T1: 仅包含事故负面证据。")

        # T2 和 T3 阶段需要进一步处理
        if time_stage in ["t2", "t3"]:
            # 步骤 2.2: 引入资源就绪标志
            logging.info(f"阶段{time_stage}: 引入资源就绪标志。")
            behavior_to_resource = {'抢修': 'RescueResource', '牵引': 'TowResource', '救助': 'AidResource',
                                    '消防': 'FirefightingResource'}
            for behavior, resource_node in behavior_to_resource.items():
                if behavior in implemented_behaviors:
                    evidence[resource_node] = 1  # 1=资源已到位/已动用
                    logging.debug(f"  - {resource_node} 设置为 1 (已动用)")

            # 步骤 2.3: 引入响应时长 (responseDuration)
            logging.info(f"阶段{time_stage}: 计算并引入响应时长。")
            road_position = data.get('road_position', [])
            resource_positions = data.get('resource_positions', [])
            if road_position and resource_positions:
                try:
                    # ---- START: 完整的 responseDuration 计算逻辑 ----
                    road_name, start_stake, end_stake = road_position
                    # (由于此部分代码不变，为简洁起见，使用占位符，请确保您的原始代码在此处)
                    # ---- 您完整的、包含API调用的 responseDuration 计算代码 ----
                    # ---- START: 原版 responseDuration 计算逻辑 ----
                    road_name, start_stake, end_stake = road_position
                    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    api_key = config.get('gaode-map', {}).get('web_service_key')
                    start_coordinates = get_coordinates_from_stake_by_file(start_stake)
                    end_coordinates = get_coordinates_from_stake_by_file(end_stake)
                    if start_coordinates and end_coordinates:
                        start_lon, start_lat = map(float, start_coordinates)
                        end_lon, end_lat = map(float, end_coordinates)
                        avg_lon = (start_lon + end_lon) / 2
                        avg_lat = (start_lat + end_lat) / 2
                        pattern = r'(.+?)\s*\(\s*([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)\s*\)'
                        worst_minutes = 0.0
                        for resource in resource_positions:
                            match = re.search(pattern, resource)
                            if not match: continue
                            latitude = float(match.group(2))
                            longitude = float(match.group(3))
                            sec = get_driving_time((avg_lon, avg_lat), (longitude, latitude), api_key)
                            if sec is not None:
                                worst_minutes = max(worst_minutes, sec / 60.0)
                            QThread.msleep(200)  # 减少延迟，加快调试
                            QCoreApplication.processEvents()
                        if worst_minutes > 0:
                            if worst_minutes <= 15:
                                evidence['responseDuration'] = 0
                            elif worst_minutes <= 40:
                                evidence['responseDuration'] = 1
                            elif worst_minutes <= 60:
                                evidence['responseDuration'] = 2
                            else:
                                evidence['responseDuration'] = 3
                            logging.debug(
                                f"  - 计算得到最差响应时间: {worst_minutes:.2f} 分钟, 对应证据 'responseDuration' = {evidence['responseDuration']}")
                    else:
                        logging.warning("  - 无法获取桩号坐标，跳过 responseDuration 计算。")
                    # ---- END: 原版 responseDuration 计算逻辑 ----
                except Exception as e:
                    logging.error(f"  - 计算 responseDuration 时发生严重错误: {e}")
            else:
                logging.warning("  - 缺少道路或资源位置信息，跳过 responseDuration 计算。")

        if time_stage == "t3":
            # 步骤 2.4: 引入处置时长 (disposalDuration)
            logging.info("阶段T3: 计算并引入处置时长。")
            max_bucket = 0
            if durations and implemented_behaviors:  # 只有实施了行为才有处置时长
                for d_str in durations:
                    if d_str is not None:
                        try:
                            duration_val = int(str(d_str).strip().split()[0])
                            if duration_val <= 15:
                                bucket = 0
                            elif duration_val <= 30:
                                bucket = 1
                            elif duration_val <= 60:
                                bucket = 2
                            else:
                                bucket = 3
                            max_bucket = max(max_bucket, bucket)
                        except (ValueError, IndexError):
                            pass
            evidence['disposalDuration'] = max_bucket
            logging.debug(f"  - 计算得到最大处置时长分档 'disposalDuration' = {max_bucket}")

            # 步骤 2.5: 【核心】根据已实施的行为，逆转负面证据
            logging.info("阶段T3: 根据已实施行为逆转负面证据。")
            if '抢修' in implemented_behaviors:
                evidence['roadLoss'] = 0  # 道路损坏被修复
                logging.debug("  - '抢修' 已实施，将 'roadLoss' 逆转为 0 (无损坏)")
            if '牵引' in implemented_behaviors:
                evidence['roadPassibility'] = 1  # 道路恢复通行
                logging.debug("  - '牵引' 已实施，将 'roadPassibility' 逆转为 1 (通行)")
            if '救助' in implemented_behaviors:
                evidence['casualties'] = 0
                logging.debug("  - '救助' 已实施，将 'casualties' 逆转为 0 (无伤亡)")

    # Final log before returning
    logging.info(f"--- [EVIDENCE GENERATION] Final Evidence for {time_stage}: ---")
    # 使用 json.dumps 格式化输出，更易读
    formatted_evidence = json.dumps(evidence, indent=2)
    for line in formatted_evidence.split('\n'):
        logging.info(line)

    return evidence

# connection_string = f"mysql+mysqlconnector://Tsing_loong:12345678@localhost:3306/test2?charset=utf8mb4"
# engine = create_engine(connection_string, echo=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# session = SessionLocal()
# # 使用示例:
#
# # 创建会话和收集器实例
# collector = PlanDataCollector(session, scenario_id=3)
#
# # 收集数据
# plan_data = collector.collect_all_data(plan_name=None)
#
# # 转换为贝叶斯网络证据
# evidence = convert_to_evidence(plan_data)


# print(evidence)

class PlanData:
    def __init__(self, session, scenario_id, neg_id_gen):
        self.session = session
        self.scenario_id = scenario_id
        self.neg_id_gen = neg_id_gen

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
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entity_json = {
                "entity_id": e_id,
                "entity_name": name,
                "entity_type_id": tpl.entity_type_id,
                "entity_parent_id": None,
                "scenario_id": self.scenario_id,  # 你上下文里的场景ID
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
            print(f"[DEBUG] 生成负数ID实体: {entity_json}")

        return replicated_data


    def _set_attribute_value(self, entity_json: Dict[str, Any], attr_code_name: str, value: Any):
        """
        小工具函数：在 entity_json["attributes"] 中找到 attribute_code_name == attr_code_name，
        然后把 attribute_value 设置为 value.
        """
        for attr in entity_json.get("attributes", []):
            # 注意，这里判断 attr["attribute_code_name"] 是否等于我们要找的 code
            if attr.get("attribute_code_name") == attr_code_name:
                attr["attribute_value"] = value
                break

    def _set_behavior_value(self, entity_json: Dict[str, Any], behavior_code_name: str, name: Optional[str] = None):
        """
        如果 entity_json["behaviors"] 中包含 behavior_code_name 对应的 behavior，可以为其设置一个自定义名称等。
        也可以在 behaviors 里新增 object_entities 引用等。演示用，不一定需要。
        """
        for b in entity_json.get("behaviors", []):
            if b.get("behavior_code_name") == behavior_code_name:
                if name is not None:
                    b["behavior_name"] = name
                break

    def _append_reference(self, entity_json: Dict[str, Any], attr_code_name: str, ref_eid: int):
        """
        小工具函数：在 entity_json["attributes"] 中找到 attr_code_name 对应的一项，
        将 ref_eid 放到 "referenced_entities" 数组里。
        适用于 is_reference=True / is_multi_valued=True 这种属性.
        """
        for attr in entity_json.get("attributes", []):
            if attr.get("attribute_code_name") == attr_code_name:
                # 说明这个属性是一个 reference，可能是多值
                attr["referenced_entities"].append(ref_eid)
                break

    def build_plan_structure(self, plan_input: Dict[str, Any]) -> Dict[int, Any]:
        """
        根据前端给定的 JSON (plan_input)，递归创建应急预案及其下属的 应急行为/应急资源等，返回一个
        { -1: { ...planEntity...}, -2: {...actionEntity...}, -3: {...resource...}, ... } 的大字典.

        plan_input 大致结构：
        {
          "plan_name": "...",
          "emergency_actions": [
            {
              "action_type": "...",
              "duration": "...",
              "implementation_status": "...",
              "resources": [
                { "resource_type": "...", "quantity": 1, ... },
                ...
              ]
            },
            ...
          ],
          "simulation_results": {...}   # 如果有，需要存就处理
        }
        """

        # 1) 创建一个“应急预案”实体
        print(f"[DEBUG] 开始创建应急预案: {plan_input}")
        plan_name_str = plan_input.get("plan_name", "未命名预案")
        plan_entities = self.create_entities_with_negative_ids("应急预案", name=plan_name_str)
        # 假设“应急预案”模板只会返回 1~N 个 entity，通常只有1个
        # 拿到第一个 key
        if not plan_entities:
            # 理论上这里不会发生，除非 DB 里找不到该 template
            return {}

        plan_eid = next(iter(plan_entities.keys()))  # 例如 -1
        plan_json = plan_entities[plan_eid]

        # 2) 在预案实体的 attributes 里，设置 "PlanName" = plan_name_str
        self._set_attribute_value(plan_json, "PlanName", plan_name_str)

        # 如果你还有其他需要存的，比如 simulation_results
        # 目前 DB 没有 "SimulationResults" 这类 attribute_code，
        # 你可以先扩展 attribute_definition 或者这里先跳过
        # 这里仅演示，假如要存成一个 JSON 字符串，放进 "description" (如果 DB 有这个字段)
        # 也可以 `_set_attribute_value(plan_json, "SomeCode", json.dumps(plan_input["simulation_results"]))`
        # 先示例存在 plan_json["description"]:
        # （注意：在真实 get_scenario_data 中 description 可能是 entity 自身字段，不是 attribute）
        plan_json["description"] = json.dumps(plan_input.get("simulation_results", {}), ensure_ascii=False)

        # 3) 处理 actions
        emergency_actions = plan_input.get("emergency_actions", [])

        for action_obj in emergency_actions:
            # 3.1 创建一个“应急行为要素”实体
            action_name = action_obj.get("action_type", "未知行为")
            action_entities = self.create_entities_with_negative_ids("应急行为要素", name=action_name)

            if not action_entities:
                continue
            # 同理，这里假设只会创建1个
            act_eid = next(iter(action_entities.keys()))
            act_json = action_entities[act_eid]

            # 3.2 设置行为自身的属性: BehaviorType, Duration, ImplementationCondition ...
            # 先举例 BehaviorType
            # behavior_type是action_type的 - 后的字符
            behavior_type = action_obj.get("action_type", "未知行为")
            behavior_type = behavior_type.split('-')[-1].strip()
            self._set_attribute_value(act_json, "BehaviorType", behavior_type)
            self._set_attribute_value(act_json, "Duration",       action_obj.get("duration"))
            self._set_attribute_value(act_json, "ImplementationCondition", action_obj.get("implementation_status"))

            # 3.3 把该 action 挂到预案的 "HasAction" 引用属性里 (如果 template_attribute_definition 映射是如此)
            self._append_reference(plan_json, "HasAction", act_eid)

            # 3.4 处理 resources
            resources = action_obj.get("resources", [])
            for res_obj in resources:
                # 创建“应急资源要素”
                res_name = res_obj.get("resource_type", "未知资源")
                resource_entities = self.create_entities_with_negative_ids("应急资源要素", name=res_name)
                if not resource_entities:
                    continue

                res_eid = next(iter(resource_entities.keys()))
                res_json = resource_entities[res_eid]

                # 设置资源属性: ResourceType, ResourceQuantityOrQuality ...
                self._set_attribute_value(res_json, "ResourceType", res_obj.get("resource_category"))
                self._set_attribute_value(res_json, "ResourceQuantityOrQuality", res_obj.get("quantity"))
                self._set_attribute_value(res_json, "Location", res_obj.get("location"))
                # 设置关联属性: AssociatedBehavior
                self._append_reference(res_json, "AssociatedBehavior", act_eid)


                res_json["description"] = f"分类: {res_obj.get('resource_category')} / 位置: {res_obj.get('location')}"


                self._append_reference(plan_json, "HasResource", res_eid)

                # 把 resource_entities 合并进整体字典
                plan_entities.update(resource_entities)

            # 把 action_entities 合并进整体字典
            plan_entities.update(action_entities)

        print(f"[DEBUG] 创建完毕，返回所有实体: {plan_entities}")
        # 最终返回包含 预案 + 所有子实体 的一个大 dict
        self.post_process_entities(plan_entities)
        return plan_entities

    def post_process_entities(self, plan_entities: Dict[int, Dict]) -> None:
        """
        对已生成的负数ID实体做二次修饰，满足以下需求：
          1) 行为的 Duration 只保留数字部分
          2) 资源的 description 只保留位置
          3) 行为/资源 的 entity_parent_id = 预案ID (假定预案ID 就是最先的 key, 或者自己找 "应急预案")
          4) 资源的 AssociatedBehavior => 指向对应行为ID; 如果资源类型=人员，则加到行为的 ImplementingPersonnel; 如果=车辆，则加到 EmergencyVehicles
        """
        # -- (A) 找到预案ID (假设只有一个预案，且key是 -1)
        #    如果实际情况更复杂，可通过 entity_type_id==13 来确定预案实体是谁
        plan_id = None
        for eid, ent in plan_entities.items():
            if ent.get("entity_type_id") == 13:  # 13 => 应急预案
                plan_id = eid
                break

        if plan_id is None:
            print("[WARN] 未找到应急预案实体，跳过后处理")
            return

        plan_json = plan_entities[plan_id]

        # -- (B) 收集所有应急行为、应急资源的 ID
        behavior_ids = []
        resource_ids = []

        for eid, ent in plan_entities.items():
            if eid == plan_id:
                continue  # 跳过预案本身
            etype = ent.get("entity_type_id")
            # 5 => "ResponseAction" (应急行为)
            # 4 => "ResponseResource" (应急资源)
            if etype == 5:  # 应急行为
                behavior_ids.append(eid)
            elif etype == 4:  # 应急资源
                resource_ids.append(eid)

        # -- (C) 给这些行为 / 资源都设置 parent_id = plan_id
        for bid in behavior_ids:
            plan_entities[bid]["entity_parent_id"] = plan_id
        for rid in resource_ids:
            plan_entities[rid]["entity_parent_id"] = plan_id

        # -- (D) 去掉 Duration 里的 " minutes"
        for bid in behavior_ids:
            beh = plan_entities[bid]
            # 找到 attributes 里的 "Duration"
            for attr in beh.get("attributes", []):
                if attr.get("attribute_code_name") == "Duration":
                    val = attr.get("attribute_value")
                    if isinstance(val, str) and "minutes" in val:
                        # 例如 "1 minutes" -> "1"
                        attr["attribute_value"] = val.replace(" minutes", "")
                    # 也可以考虑 val.replace(" ", "") if 只想保留数字
                    # 或者干脆解析成数字 int(val.split()[0]) => 1

        # -- (E) 对资源的 description 只保留 "location"
        #    假设原先 description="分类: 类型A / 位置: 435"
        #    我们要只保留 "435"
        for rid in resource_ids:
            res = plan_entities[rid]
            desc = res.get("description", "")
            # 如果你能统一保证是类似"分类: XXX / 位置: YYY"的格式，可以做字符串解析
            # 简单粗暴一点：只保留最后一部分 => "435"
            # 例如:
            if "位置:" in desc:
                # 取 "位置:" 后面的部分
                location_str = desc.split("位置:")[-1].strip()
                # 如果还包含 '/' 或别的符号可以再进一步 .split('/')
                res["description"] = location_str
            # 如果描述里本身就只有数字，就无需改

        # -- (F) 处理 “AssociatedBehavior” & 资源类型 => 写入行为的 "ImplementingPersonnel"/"EmergencyVehicles"
        #    先做一个小帮助函数来获取 attribute 对象
        def get_attr(ent, code_name: str) -> Optional[Dict]:
            """在 ent["attributes"] 中找到指定 code_name 的那一项"""
            for a in ent.get("attributes", []):
                if a.get("attribute_code_name") == code_name:
                    return a
            return None

        for rid in resource_ids:
            res_ent = plan_entities[rid]
            # 1) 在资源上读取“AssociatedBehavior” => 获取对应的 应急行为ID
            assoc_attr = get_attr(res_ent, "AssociatedBehavior")
            if assoc_attr and "referenced_entities" in assoc_attr and assoc_attr["referenced_entities"]:
                # 假设每个资源只关联一个行为
                action_eid = assoc_attr["referenced_entities"][0]
                if action_eid in behavior_ids:
                    # 2) 根据资源类型，将资源ID添加到对应行为的 ImplementingPersonnel / EmergencyVehicles
                    resource_type = None
                    rtype_attr = get_attr(res_ent, "ResourceType")
                    if rtype_attr:
                        resource_type = rtype_attr.get("attribute_value")

                    if resource_type and isinstance(resource_type, str):
                        beh_ent = plan_entities[action_eid]
                        if "人" in resource_type:  # 例如 "人员"
                            imp_attr = get_attr(beh_ent, "ImplementingPersonnel")
                            if imp_attr:
                                if "referenced_entities" not in imp_attr:
                                    imp_attr["referenced_entities"] = []
                                imp_attr["referenced_entities"].append(rid)
                        elif "车" in resource_type:  # 例如 "车辆"
                            eve_attr = get_attr(beh_ent, "EmergencyVehicles")
                            if eve_attr:
                                if "referenced_entities" not in eve_attr:
                                    eve_attr["referenced_entities"] = []
                                eve_attr["referenced_entities"].append(rid)
            else:
                # 如果资源没有关联行为，您可以选择跳过或进行其他处理
                print(f"[WARN] 资源ID {rid} 没有关联的行为，跳过关联。")

        # 修改就地，无需 return；plan_entities 本身即被改动

    def upsert_posterior_probability(
            self,
            plan_name: str,
            posterior_dict: Dict[str, Dict[str, float]],
            time_stage: str = "t0"
    ) -> None:
        """
        将后验概率写入 posteriori_data （字段名对齐当前模型）：
          - Entity.entity_name
          - BayesNode.bayes_node_name
          - BayesNodeState.bayes_node_state_name

        若数据库尚未添加 posteriori_data.time_stage 列，下面的 try/except 会自动退化为“无阶段”的 upsert。
        """
        from datetime import datetime
        from sqlalchemy import and_
        from models.models import PosterioriData, BayesNode, BayesNodeState, Entity
        session = self.session

        # 1) 定位 plan
        plan = session.query(Entity).filter(Entity.entity_name == plan_name).one_or_none()
        if plan is None:
            raise ValueError(f"Plan not found: {plan_name}")
        plan_id = plan.entity_id

        # 2) 建缓存
        node_cache: Dict[str, int] = {}
        state_cache: Dict[Tuple[int, str], int] = {}

        def _node_id(node_name: str) -> int:
            if node_name in node_cache:
                return node_cache[node_name]
            node = (session.query(BayesNode)
                    .filter(BayesNode.bayes_node_name == node_name)
                    .one())
            node_cache[node_name] = node.bayes_node_id
            return node.bayes_node_id

        def _state_id(node_name: str, state_label: str) -> int:
            nid = _node_id(node_name)
            key = (nid, state_label)
            if key in state_cache:
                return state_cache[key]
            st = (session.query(BayesNodeState)
                  .filter(BayesNodeState.bayes_node_id == nid,
                          BayesNodeState.bayes_node_state_name == state_label)
                  .one())
            state_cache[key] = st.bayes_node_state_id
            return st.bayes_node_state_id

        rows_to_add = []

        for node_name, dist in posterior_dict.items():
            # 允许节点不在库里，跳过并继续
            try:
                nid = _node_id(node_name)
            except Exception:
                # 节点没找到，跳过整个节点
                continue

            for state_label, prob in dist.items():
                try:
                    bns_id = _state_id(node_name, state_label)
                except Exception:
                    # 状态没找到，跳过该状态
                    continue

                # 3) upsert
                try:
                    # 如果存在 time_stage 列，用 (plan_id, state, time_stage) 唯一定位
                    rec = (session.query(PosterioriData)
                           .filter(and_(
                        PosterioriData.plan_id == plan_id,
                        PosterioriData.bayes_node_state_id == bns_id,
                        PosterioriData.time_stage == time_stage
                    ))
                           .one_or_none())
                    if rec:
                        rec.posterior_probability = float(prob)
                        rec.update_time = datetime.now()
                    else:
                        rows_to_add.append(PosterioriData(
                            posterior_probability=float(prob),
                            bayes_node_state_id=bns_id,
                            plan_id=plan_id,
                            time_stage=time_stage
                        ))
                except Exception:
                    # 数据库还没有 time_stage 列：退化为 (plan_id, state) upsert
                    rec = (session.query(PosterioriData)
                           .filter(PosterioriData.plan_id == plan_id,
                                   PosterioriData.bayes_node_state_id == bns_id)
                           .one_or_none())
                    if rec:
                        rec.posterior_probability = float(prob)
                        rec.update_time = datetime.now()
                    else:
                        rows_to_add.append(PosterioriData(
                            posterior_probability=float(prob),
                            bayes_node_state_id=bns_id,
                            plan_id=plan_id
                        ))

        if rows_to_add:
            session.bulk_save_objects(rows_to_add)
        session.commit()

    def get_plan_by_name(self, plan_name: str) -> Dict[str, Any]:
        """
        新增方法：
        返回指定预案的详细信息，与 get_all_plans() 中对单个预案的结构一致。
        若不存在则返回空字典。
        """
        all_plans = self.get_all_plans()
        return all_plans.get(plan_name, {})




    def get_all_plans(self, change_path=None) -> Dict[str, Any]:
        """
        【完整优化版】
        返回所有预案信息，并从 posteriori_data 表中精确读取 t0 和 t_last 的结果，
        同时保留了 emergency_actions 的完整查询逻辑。
        """
        import logging
        from .get_config import get_cfg  # 确保 get_cfg 被正确导入

        session = self.session
        results: Dict[str, Any] = {}

        # --- 步骤 1: 提前准备，提高效率 ---

        # 1.1) 获取 DBN 配置中的最后一个时间阶段
        try:
            stages = get_cfg().get("dbn", {}).get("time_stages", ["t0", "t1", "t2", "t3"])
            LAST_TIME_STAGE = stages[-1] if stages else 't3'
        except Exception:
            LAST_TIME_STAGE = 't3'

        logging.info(f"get_all_plans: 将使用 't0' 作为推演前, '{LAST_TIME_STAGE}' 作为推演后。")

        # 1.2) 提前获取 Resilience 节点和状态的 ID
        resilience_node = session.query(BayesNode).filter_by(bayes_node_name='ScenarioResilience').one_or_none()
        if not resilience_node:
            logging.warning("get_all_plans: 未在数据库中找到 'ScenarioResilience' 节点，无法获取推演结果。")
            # 仍然继续，但 simulation_results 将为空

        good_state_id, bad_state_id = None, None
        if resilience_node:
            good_state = session.query(BayesNodeState.bayes_node_state_id).filter_by(
                bayes_node_id=resilience_node.bayes_node_id, bayes_node_state_name='Good'
            ).scalar()
            bad_state = session.query(BayesNodeState.bayes_node_state_id).filter_by(
                bayes_node_id=resilience_node.bayes_node_id, bayes_node_state_name='Bad'
            ).scalar()
            if good_state and bad_state:
                good_state_id, bad_state_id = good_state, bad_state
            else:
                logging.warning("get_all_plans: 'ScenarioResilience' 节点的状态 'Good' 或 'Bad' 未找到。")

        # --- 步骤 2: 循环处理每个预案 ---

        # 2.1) 找到所有应急预案实体
        plan_entities = session.query(Entity).filter_by(
            entity_type_id=13,  # 13 = 应急预案
            scenario_id=self.scenario_id
        ).all()

        for plan_ent in plan_entities:
            plan_id = plan_ent.entity_id
            plan_name = plan_ent.entity_name
            plan_create_time = plan_ent.create_time.strftime("%Y-%m-%d %H:%M:%S")

            # ========== (A) 组装 "emergency_actions" (保留您原有的完整逻辑) ==========

            actions = session.query(Entity).filter_by(entity_parent_id=plan_id, entity_type_id=5).all()
            action_list = []
            for act in actions:
                action_dict = {
                    "action_type": "", "duration": "0 minutes",
                    "implementation_status": "False", "resources": []
                }
                attr_values = session.query(AttributeValue).filter_by(entity_id=act.entity_id).all()
                attr_map = {
                    av.attribute_definition.attribute_code.attribute_code_name: av.attribute_value
                    for av in attr_values if av.attribute_definition and av.attribute_definition.attribute_code
                }

                # 从 attr_map 填充 action_dict
                action_dict["action_type"] = attr_map.get("BehaviorType", "")
                if "Duration" in attr_map and attr_map["Duration"]:
                    action_dict["duration"] = f'{attr_map["Duration"]} minutes'
                action_dict["implementation_status"] = attr_map.get("ImplementationCondition", "False")

                # (A-1) 找到 action 下的资源
                res_subq = (
                    session.query(AttributeValue.entity_id)
                    .join(AttributeDefinition,
                          AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id)
                    .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id)
                    .join(AttributeValueReference,
                          AttributeValue.attribute_value_id == AttributeValueReference.attribute_value_id)
                    .filter(AttributeCode.attribute_code_name == "AssociatedBehavior")
                    .filter(AttributeValueReference.referenced_entity_id == act.entity_id)
                    .subquery()
                )
                res_entities = (
                    session.query(Entity).filter(
                        Entity.entity_id.in_(res_subq),
                        Entity.entity_type_id == 4,  # 应急资源
                        Entity.entity_parent_id == plan_id
                    ).all()
                )
                resource_list = []
                for res_ent in res_entities:
                    res_attr_values = session.query(AttributeValue).filter_by(entity_id=res_ent.entity_id).all()
                    res_attr_map = {
                        rav.attribute_definition.attribute_code.attribute_code_name: rav.attribute_value
                        for rav in res_attr_values if
                        rav.attribute_definition and rav.attribute_definition.attribute_code
                    }

                    # (此处保留您原有的 type_mapping 逻辑来确定 resource_type)
                    type_mapping = {
                        "人员": ["牵引人员", "交警", "医生", "消防员", "抢险人员"],
                        "车辆": ["牵引车", "警车", "救护车", "消防车", "融雪车辆", "防汛车辆", "封道抢险车"],
                        "物资": ["随车修理工具", "钢丝绳", "安全锥", "撬棒", "黄沙", "扫帚", "辅助轮", "千斤顶",
                                 "灭火器", "草包", "蛇皮袋", "融雪剂", "发电机", "抽水泵", "医疗物资"]
                    }
                    # 看category是人员还是车辆还是物资
                    for key, value in type_mapping.items():
                        if res_attr_map.get("ResourceType") in value:
                            resource_type = key
                            break
                    # 也可根据实际字段/业务设置
                    resource_item = {
                        "resource_type": resource_type,
                        "resource_category": res_attr_map.get("ResourceType", "未知资源"),
                        "quantity": res_attr_map.get("ResourceQuantityOrQuality", 0),
                        "location": res_attr_map.get("Location", "未知位置")
                    }
                    resource_list.append(resource_item)

                action_dict["resources"] = resource_list
                action_list.append(action_dict)

            # ========== (B) 组装 "simulation_results"【核心优化】 ==========

            sim_results = {
                "推演前-较好": "N/A", "推演前-较差": "N/A",
                "推演后-较好": "N/A", "推演后-较差": "N/A"
            }

            if good_state_id and bad_state_id:
                # 一次性查询出该预案 t0 和 t_last 的所有相关后验数据
                post_data_list = session.query(PosterioriData).filter(
                    PosterioriData.plan_id == plan_id,
                    PosterioriData.time_stage.in_(['t0', LAST_TIME_STAGE]),
                    PosterioriData.bayes_node_state_id.in_([good_state_id, bad_state_id])
                ).all()

                # 填充 "推演前" (t0) 的结果
                for post in post_data_list:
                    if post.time_stage == 't0':
                        if post.bayes_node_state_id == good_state_id:
                            sim_results["推演前-较好"] = f"{post.posterior_probability * 100:.2f}%"
                        elif post.bayes_node_state_id == bad_state_id:
                            sim_results["推演前-较差"] = f"{post.posterior_probability * 100:.2f}%"

                # 填充 "推演后" (t_last) 的结果
                for post in post_data_list:
                    if post.time_stage == LAST_TIME_STAGE:
                        if post.bayes_node_state_id == good_state_id:
                            sim_results["推演后-较好"] = f"{post.posterior_probability * 100:.2f}%"
                        elif post.bayes_node_state_id == bad_state_id:
                            sim_results["推演后-较差"] = f"{post.posterior_probability * 100:.2f}%"

            # ========== (C) 最终组装 plan_info (保留您的 change_path 逻辑) ==========
            if change_path:
                logging.info(f"根据路径调整推演前结果: {change_path}")
                try:
                    with open(change_path, 'r') as f:
                        change_dict = json.load(f)
                        if "ScenarioResilience" in change_dict:
                            good_prior = change_dict["ScenarioResilience"].get("Good", 0.0)
                            bad_prior = change_dict["ScenarioResilience"].get("Bad", 0.0)
                            sim_results["推演前-较好"] = f"{good_prior * 100:.2f}%"
                            sim_results["推演前-较差"] = f"{bad_prior * 100:.2f}%"
                except (IOError, json.JSONDecodeError) as e:
                    logging.error(f"读取 change_path 文件失败: {e}")

            plan_info = {
                "plan_name": plan_name,
                "emergency_actions": action_list,
                "simulation_results": sim_results,
                "timestamp": plan_create_time
            }
            results[plan_name] = plan_info

        return results