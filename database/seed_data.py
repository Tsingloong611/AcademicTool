# -*- coding: utf-8 -*-
# @Time    : 01/21/2025
# @FileName: seed_data.py
# @Software: PyCharm

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 修改为你实际的模型导入路径
from models.models import (
    Base,
    # 以下所有类在你的 models.py 里需定义：
    AttributeAspect,
    AttributeCode,
    AttributeCodeName,
    AttributeDefinition,
    AttributeType,
    BehaviorCode,
    BehaviorDefinition,
    BehaviorNameCode,
    Category,
    Emergency,
    EntityType,
    EnumValue,
    OwlType,
    Scenario,
    Template,
    # 如果有 Entity、BehaviorValue、PosterioriData、Bayes 等模型需要插入，可一并导入
)


########################################################################
# 各表的种子数据插入函数
########################################################################

def seed_attribute_aspect(session):
    """
    INSERT INTO `attribute_aspect` VALUES (1, 'Hazard', '致灾', ...), ...
    """
    data = [
        AttributeAspect(
            attribute_aspect_id=1,
            attribute_aspect_name='Hazard',
            description='致灾',
            create_time='2025-01-14 11:56:36',
            update_time='2025-01-15 11:24:48'
        ),
        AttributeAspect(
            attribute_aspect_id=2,
            attribute_aspect_name='Environment',
            description='环境',
            create_time='2025-01-14 11:56:45',
            update_time='2025-01-14 11:56:45'
        ),
        AttributeAspect(
            attribute_aspect_id=3,
            attribute_aspect_name='Affected',
            description='承灾',
            create_time='2025-01-15 11:24:24',
            update_time='2025-01-15 11:24:24'
        ),
        AttributeAspect(
            attribute_aspect_id=4,
            attribute_aspect_name='Common',
            description='共有',
            create_time='2025-01-15 11:24:41',
            update_time='2025-01-15 11:24:41'
        ),
    ]
    session.bulk_save_objects(data)
    session.commit()


def seed_attribute_code(session):
    """
    INSERT INTO `attribute_code` VALUES (1, 'VehicleType', '车辆类型', ...), ..., (74, 'HasAction', '包含行动', ...);
    """
    raw_data = [
        (1, 'VehicleType', '车辆类型', '2025-01-15 10:41:42', '2025-01-15 10:41:42'),
        (2, 'CollisionCondition', '碰撞情况', '2025-01-15 10:43:06', '2025-01-15 10:46:42'),
        (3, 'CombustionCondition', '燃爆情况', '2025-01-15 10:43:53', '2025-01-15 10:46:52'),
        (4, 'SpillCondition', '抛洒情况', '2025-01-15 10:46:14', '2025-01-15 10:48:12'),
        (5, 'BreakdownCondition', '抛锚情况', '2025-01-15 10:48:25', '2025-01-15 10:48:25'),
        (6, 'RollOverCondition', '侧翻情况', '2025-01-15 10:48:37', '2025-01-15 10:48:37'),
        (7, 'AbnormalSpeedCondition', '速度异常情况', '2025-01-15 10:48:53', '2025-01-15 10:48:53'),
        (8, 'IIIegalLaneOccupationCondition', '违规占道情况', '2025-01-15 10:49:20', '2025-01-15 10:49:20'),
        (9, 'DrivingDirection', '行驶方向', '2025-01-15 10:49:35', '2025-01-15 10:49:35'),
        (10, 'VehiclePosition', '车辆位置', '2025-01-15 10:49:48', '2025-01-15 10:49:48'),
        (11, 'VehicleSpeed', '车辆速度', '2025-01-15 10:49:58', '2025-01-15 10:49:58'),
        (12, 'VehicleCargo', '车辆货物', '2025-01-15 10:50:13', '2025-01-15 10:50:13'),
        (13, 'VehiclePassengers', '车辆乘客', '2025-01-15 10:50:28', '2025-01-15 10:50:28'),
        (14, 'VehicleComponents', '车辆部件', '2025-01-15 10:50:39', '2025-01-15 10:50:39'),
        (15, 'DrivingRoadSegment', '所行驶路段', '2025-01-15 10:50:53', '2025-01-15 10:50:53'),
        (16, 'DamageCondition', '受损情况', '2025-01-15 10:51:02', '2025-01-15 10:51:02'),
        (17, 'CasualtyCondition', '伤亡情况', '2025-01-15 10:51:18', '2025-01-15 10:51:18'),
        (18, 'AffiliatedVehicle', '所属车辆', '2025-01-15 10:51:37', '2025-01-15 10:51:37'),
        (19, 'RoadName', '道路名称', '2025-01-15 10:51:49', '2025-01-15 10:51:49'),
        (20, 'RoadType', '道路类型', '2025-01-15 10:51:59', '2025-01-15 10:51:59'),
        (21, 'NumberOfLanes', '行车道数', '2025-01-15 10:52:18', '2025-01-15 10:52:18'),
        (22, 'TrafficVolume', '交通量', '2025-01-15 10:52:27', '2025-01-15 10:52:27'),
        (23, 'SegmentStartStakeNumber', '段起点桩号', '2025-01-15 10:52:34', '2025-01-15 10:52:53'),
        (24, 'SegmentEndStakeNumber', '段终点桩号', '2025-01-15 10:53:09', '2025-01-15 10:53:09'),
        (25, 'DesignSpeed', '设计车速', '2025-01-15 10:53:20', '2025-01-15 10:53:20'),
        (26, 'ClosureCondition', '封闭情况', '2025-01-15 10:53:43', '2025-01-15 10:53:43'),
        (27, 'RoadDamageCondition', '受损情况', '2025-01-15 10:53:54', '2025-01-15 10:53:54'),
        (28, 'PollutionCondition', '污染情况', '2025-01-15 10:54:09', '2025-01-15 10:54:09'),
        (29, 'IncludedFacilities', '所含设施', '2025-01-15 10:54:19', '2025-01-15 10:54:19'),
        (30, 'IncludedVehicles', '所含车辆', '2025-01-15 10:54:30', '2025-01-15 10:54:30'),
        (31, 'RoadMaintenanceConditon', '道路养护情况', '2025-01-15 10:54:44', '2025-01-15 10:54:44'),
        (32, 'RoadConstrucetionCondition', '道路施工情况', '2025-01-15 10:54:58', '2025-01-15 10:54:58'),
        (33, 'WeatherType', '气象类型', '2025-01-15 10:55:08', '2025-01-15 10:55:08'),
        (34, 'Rainfall', '降雨量', '2025-01-15 10:55:16', '2025-01-15 10:55:16'),
        (35, 'Visibility', '能见度', '2025-01-15 10:55:25', '2025-01-15 10:55:25'),
        (36, 'WindSpeed', '风速', '2025-01-15 10:55:43', '2025-01-15 10:55:43'),
        (37, 'WindForce', '风力', '2025-01-15 10:55:51', '2025-01-15 10:55:51'),
        (38, 'SnowfallIntensity', '降雪强度', '2025-01-15 10:56:03', '2025-01-15 10:56:03'),
        (39, 'AffectedArea', '作用区域', '2025-01-15 10:56:19', '2025-01-15 10:56:19'),
        (40, 'IncludedLanes', '所含车道', '2025-01-15 10:57:23', '2025-01-15 10:57:23'),
        (41, 'TravelTime', '通行时间', '2025-01-15 10:57:39', '2025-01-15 10:57:39'),
        (42, 'SpeedLimit', '限速值', '2025-01-15 10:57:48', '2025-01-15 10:57:48'),
        (43, 'ResourceType', '资源类型', '2025-01-15 10:58:00', '2025-01-15 10:58:00'),
        (44, 'ResourceUsageCondition', '资源使用情况', '2025-01-15 10:58:10', '2025-01-15 10:58:10'),
        (45, 'ResourceQuantityOrQuality', '资源数（质）量', '2025-01-15 10:58:34', '2025-01-15 10:58:34'),
        (46, 'AssociatedBehavior', '关联行为', '2025-01-15 10:58:48', '2025-01-15 10:58:48'),
        (47, 'BehaviorType', '行为类型', '2025-01-15 10:59:01', '2025-01-15 10:59:01'),
        (48, 'ImplementationCondition', '实施情况', '2025-01-15 10:59:14', '2025-01-15 10:59:14'),
        (49, 'TrafficCapacity', '通行能力', '2025-01-15 11:00:20', '2025-01-15 11:00:20'),
        (50, 'Duration', '持续时间', '2025-01-15 11:08:15', '2025-01-15 11:08:15'),
        (51, 'InvolvedMaterials', '涉及物资', '2025-01-15 11:08:28', '2025-01-15 11:08:28'),
        (52, 'ImplementingPersonnel', '实施人员', '2025-01-15 11:08:41', '2025-01-15 11:08:41'),
        (53, 'EmergencyVehicles', '应急车辆', '2025-01-15 11:08:51', '2025-01-15 11:08:51'),
        (54, 'TargetOfImplementation', '实施对象', '2025-01-15 11:09:12', '2025-01-15 11:09:12'),
        (55, 'FacilityType', '设施类型', '2025-01-16 23:06:00', '2025-01-16 23:06:03'),
        (56, 'FacilityLocation', '设施位置', '2025-01-16 23:06:19', '2025-01-16 23:06:21'),
        (57, 'FacilityDamageStatus', '受损情况', '2025-01-16 23:07:45', '2025-01-16 23:07:47'),
        (58, 'RoadFacilityOf', '所属路段', '2025-01-16 23:08:17', '2025-01-16 23:08:19'),
        (59, 'LaneType', '车道类型', '2025-01-20 19:07:40', '2025-01-20 19:07:42'),
        (60, 'LaneWidth', '车道宽度', '2025-01-20 19:08:14', '2025-01-20 19:08:17'),
        (61, 'DesignedSpeed', '车行道设计车速', '2025-01-20 19:08:41', '2025-01-20 19:08:43'),
        (62, 'VehicleTypeRestriction', '车行道车型限制', '2025-01-20 19:09:13', '2025-01-20 19:09:15'),
        (63, 'RoadClosureStatus', '封闭情况', '2025-01-20 19:09:42', '2025-01-20 19:09:44'),
        (64, 'PollutionStatus', '污染情况', '2025-01-20 19:10:09', '2025-01-20 19:10:11'),
        (65, 'RoadSection', '所属路段', '2025-01-20 19:10:32', '2025-01-20 19:10:34'),
        (66, 'HasVehicles', '所含车辆', '2025-01-20 19:11:06', '2025-01-20 19:11:08'),
        (67, 'VehiclePartType', '部件类型', '2025-01-20 19:25:31', '2025-01-20 19:25:35'),
        (68, 'IsDetached', '是否脱落', '2025-01-20 19:25:56', '2025-01-20 19:25:59'),
        (69, 'VehiclePartsOf', '所属车辆', '2025-01-20 19:26:31', '2025-01-20 19:26:33'),
        (70, 'VehicleLoadTyoe', '承载物类型', '2025-01-20 19:27:06', '2025-01-20 19:27:08'),
        (71, 'LoadedOn', '所属车辆', '2025-01-20 19:27:23', '2025-01-20 19:27:25'),
        (72, 'PlanName', '预案名称', '2025-01-20 19:33:41', '2025-01-20 19:33:42'),
        (73, 'HasResource', '包含资源', '2025-01-20 19:34:16', '2025-01-20 19:34:18'),
        (74, 'HasAction', '包含行动', '2025-01-20 19:34:29', '2025-01-20 19:34:31'),
        (75, 'Location', '资源位置', '2025-01-20 19:34:42', '2025-01-20 19:34:44'),
        (76, 'EmergencyPeriod', '致灾时段', '2025-02-07 13:13:35', '2025-02-07 13:13:35'),
    ]
    # 该部分实际上和 seed_attribute_code 里有重叠, 注意不要重复插入。
    # 如果只想一次性插入 attribute_code，可放到同一个函数里；本处保留示例，可能需要手动调整。
    objs = []
    for r in raw_data:
        objs.append(AttributeCode(
            attribute_code_id=r[0],
            attribute_code_name=r[1],
            description=r[2],
            create_time=r[3],
            update_time=r[4]
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_attribute_code_name(session):
    """
    INSERT INTO `attribute_code_name` VALUES
      (1, 'ExplodeCondition'), (1, 'VehicleType'), ..., (74, 'HasAction');
    """
    raw_data = [
        (1, 'VehicleType'),
        (2, 'CollideCondition'), (2, 'CollisionCondition'),
        (3, 'CombustionCondition'), (4, 'SpillCondition'),
        (5, 'BreakdownCondition'), (6, 'RollOverCondition'),
        (7, 'AbnormalSpeedCondition'), (8, 'IIIegalLaneOccupationCondition'),
        (9, 'DrivingDirection'), (10, 'position'), (10, 'VehiclePosition'),
        (11, 'VehicleSpeed'), (12, 'VehicleCargo'), (13, 'VehiclePassengers'),
        (14, 'VehicleComponents'), (15, 'DrivingRoadSegment'),
        (16, 'DamageCondition'), (17, 'CasualtyCondition'),
        (18, 'AffiliatedVehicle'), (19, 'RoadName'), (20, 'RoadType'),
        (21, 'NumberOfLanes'), (22, 'TrafficVolume'),
        (23, 'SegmentStartStakeNumber'), (24, 'SegmentEndStakeNumber'),
        (25, 'DesignSpeed'), (26, 'ClosureCondition'),
        (27, 'RoadDamageCondition'), (28, 'PollutionCondition'),
        (29, 'IncludedFacilities'), (30, 'IncludedVehicles'),
        (31, 'RoadMaintenanceConditon'), (32, 'RoadConstrucetionCondition'),
        (33, 'WeatherType'), (34, 'Rainfall'), (35, 'Visibility'),
        (36, 'WindSpeed'), (37, 'WindForce'), (38, 'SnowfallIntensity'),
        (39, 'AffectedArea'), (40, 'IncludedLanes'), (41, 'TravelTime'),
        (42, 'SpeedLimit'), (43, 'ResourceType'),
        (44, 'ResourceUsageCondition'), (45, 'ResourceQuantityOrQuality'),
        (46, 'AssociatedBehavior'), (47, 'BehaviorType'),
        (48, 'ImplementationCondition'), (49, 'TrafficCapacity'),
        (50, 'Duration'), (51, 'InvolvedMaterials'),
        (52, 'ImplementingPersonnel'), (53, 'EmergencyVehicles'),
        (54, 'TargetOfImplementation'), (55, 'FacilityType'),
        (56, 'FacilityLocation'), (57, 'FacilityDamageStatus'),
        (58, 'RoadFacilityOf'), (59, 'LaneType'), (60, 'LaneWidth'),
        (61, 'DesignedSpeed'), (62, 'VehicleTypeRestriction'),
        (63, 'RoadClosureStatus'), (64, 'PollutionStatus'),
        (65, 'RoadSection'), (66, 'HasVehicles'), (67, 'VehiclePartType'),
        (68, 'IsDetached'), (69, 'VehiclePartsOf'),
        (70, 'VehicleLoadType'), (71, 'LoadedOn'),
        (72, 'PlanName'), (73, 'HasPlan'), (74, 'HasAction'),(75,'Location'),(76,'EmergencyPeriod')
    ]
    objs = []
    for (code_id, name) in raw_data:
        objs.append(AttributeCodeName(
            attribute_code_id=code_id,
            attribute_name=name
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_category(session):
    """
    INSERT INTO `category` VALUES (1, 'AffectedElement', ...), ..., (6, 'Common', ...);
    """
    data = [
        Category(category_id=1, category_name='AffectedElement', description='承灾要素',
                 create_time='2025-01-15 10:37:25', update_time='2025-01-15 10:37:25'),
        Category(category_id=2, category_name='EnvironmentElement', description='环境要素',
                 create_time='2025-01-15 10:37:25', update_time='2025-01-15 10:37:25'),
        Category(category_id=3, category_name='HazardElement', description='致灾要素',
                 create_time='2025-01-15 10:37:25', update_time='2025-01-15 10:37:25'),
        Category(category_id=4, category_name='ResponsePlanElement', description='应急预案要素',
                 create_time='2025-01-15 10:37:25', update_time='2025-01-15 10:37:25'),
        Category(category_id=5, category_name='Item', description=None,
                 create_time='2025-01-15 10:37:25', update_time='2025-01-15 10:37:25'),
        Category(category_id=6, category_name='Common', description=None,
                 create_time='2025-01-15 10:37:38', update_time='2025-01-15 10:37:38'),
    ]
    session.bulk_save_objects(data)
    session.commit()


def seed_emergency(session):
    """
    INSERT INTO `emergency` VALUES (1, '测试', NULL, '2025-01-15 11:11:07', '2025-01-15 11:11:07');
    """
    e = Emergency(
        emergency_id=1,
        emergency_name='测试',
        emergency_description=None,
        emergency_create_time='2025-01-15 11:11:07',
        emergency_update_time='2025-01-15 11:11:07'
    )
    session.add(e)
    session.commit()


def seed_scenario(session):
    """
    你的SQL dump并没有INSERT记录到 scenario 表, 可以留空或自行插入:
    INSERT INTO `scenario` VALUES (1, '测试场景', NULL, '2025-01-15 11:11:19','2025-01-15 11:11:19',1);
    """
    pass


def seed_owl_type(session):
    """
    INSERT INTO `owl_type` VALUES
      (1, 'Unify', '整体', '2025-01-20 11:37:03', '2025-01-20 11:37:05'),
      ...
      (4, 'Scenario', '情景本体', '2025-01-20 11:38:39', '2025-01-20 11:38:41');
    """
    raw_data = [
        (1, 'Unify', '整体', '2025-01-20 11:37:03', '2025-01-20 11:37:05'),
        (2, 'Emergency', '突发事件本体', '2025-01-20 11:38:01', '2025-01-20 11:38:05'),
        (3, 'ScenarioElement', '情景要素本体', '2025-01-20 11:38:27', '2025-01-20 11:38:30'),
        (4, 'Scenario', '情景本体', '2025-01-20 11:38:39', '2025-01-20 11:38:41'),
    ]
    objs = []
    for (ot_id, ot_name, ot_desc, ctime, utime) in raw_data:
        objs.append(OwlType(
            owl_type_id=ot_id,
            owl_type_name=ot_name,
            description=ot_desc,
            create_time=ctime,
            update_time=utime
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_enum_value(session):
    """
    INSERT INTO `enum_value` VALUES
      (1, '正向', '行驶方向', 9, '2025-01-16 13:51:19', '2025-01-16 13:51:21'),
      ...
      (30, '易碎品', '承载物类型', 70, '2025-01-20 19:44:01', '2025-01-20 19:44:01');
    """
    raw_data = [
        (1, '正向', '行驶方向', 9, '2025-01-16 13:51:19', '2025-01-16 13:51:21'),
        (2, '反向', '行驶方向', 9, '2025-01-16 13:53:06', '2025-01-16 13:53:06'),
        (3, '主路', '道路类型', 20, '2025-01-16 13:53:44', '2025-01-16 13:55:10'),
        (4, '辅路', '道路类型', 20, '2025-01-16 13:55:16', '2025-01-16 13:55:16'),
        (5, '匝道', '道路类型', 20, '2025-01-16 13:55:30', '2025-01-16 13:55:30'),
        (6, '晴天', '气象类型', 34, '2025-01-16 13:56:28', '2025-01-16 13:56:28'),
        (7, '阴天', '气象类型', 34, '2025-01-16 13:56:35', '2025-01-16 13:56:35'),
        (8, '小雪', '降雪强度', 39, '2025-01-16 13:56:56', '2025-01-16 13:56:56'),
        (9, '中雪', '降雪强度', 39, '2025-01-16 13:57:02', '2025-01-16 13:57:02'),
        (10, '大雪', '降雪强度', 39, '2025-01-16 13:57:10', '2025-01-16 13:57:10'),
        (11, '牵引车', '资源类型', 44, '2025-01-16 13:57:46', '2025-01-16 13:57:46'),
        (12, '消防车', '资源类型', 44, '2025-01-16 13:57:52', '2025-01-16 13:57:52'),
        (13, '救护车', '资源类型', 44, '2025-01-16 13:57:59', '2025-01-16 13:57:59'),
        (14, '融雪车辆', '资源类型', 44, '2025-01-16 13:58:07', '2025-01-16 13:58:07'),
        (15, '交警', '资源类型', 44, '2025-01-16 13:58:19', '2025-01-16 13:58:19'),
        (16, '医生', '资源类型', 44, '2025-01-16 13:58:26', '2025-01-16 13:58:26'),
        (17, '抢险人员', '资源类型', 44, '2025-01-16 13:58:35', '2025-01-16 13:58:35'),
        (18, '灭火器', '资源类型', 44, '2025-01-16 13:58:47', '2025-01-16 13:58:47'),
        (19, '钢丝绳', '资源类型', 44, '2025-01-16 13:58:56', '2025-01-16 13:58:56'),
        (20, '融雪剂', '资源类型', 44, '2025-01-16 13:59:04', '2025-01-16 13:59:04'),
        (21, '救助', '行为类型', 48, '2025-01-20 19:41:54', '2025-01-20 19:41:54'),
        (22, '牵引', '行为类型', 48, '2025-01-20 19:42:01', '2025-01-20 19:42:01'),
        (23, '抢修', '行为类型', 48, '2025-01-20 19:42:08', '2025-01-20 19:42:08'),
        (24, '消防', '行为类型', 48, '2025-01-20 19:42:16', '2025-01-20 19:42:16'),
        (25, '发动机', '部件类型', 67, '2025-01-20 19:43:01', '2025-01-20 19:43:01'),
        (26, '轮胎', '部件类型', 67, '2025-01-20 19:43:08', '2025-01-20 19:43:08'),
        (27, '车门', '部件类型', 67, '2025-01-20 19:43:16', '2025-01-20 19:43:16'),
        (28, '易燃品', '承载物类型', 70, '2025-01-20 19:43:46', '2025-01-20 19:43:46'),
        (29, '易爆品', '承载物类型', 70, '2025-01-20 19:43:52', '2025-01-20 19:43:52'),
        (30, '易碎品', '承载物类型', 70, '2025-01-20 19:44:01', '2025-01-20 19:44:01'),
        (31, "立柱", "设施类型", 55, "2025-01-22 14:52:17", "2025-01-22 14:52:17"),
        (32, "路名牌", "设施类型", 55, "2025-01-22 14:54:31", "2025-01-22 14:54:31"),
        (33, "护栏", "设施类型", 55, "2025-01-22 14:54:40", "2025-01-22 14:54:40"),
        (34, "声屏障", "设施类型", 55, "2025-01-22 14:54:56", "2025-01-22 14:54:56"),
        (35, "水泥防撞墙", "设施类型", 55, "2025-01-22 14:55:16", "2025-01-22 14:55:16"),
        (36, "防撞隔离墩", "设施类型", 55, "2025-01-22 14:55:39", "2025-01-22 14:55:39"),
        (37, "防撞护栏", "设施类型", 55, "2025-01-22 15:02:53", "2025-01-22 15:02:53"),
        (38, "防撞墙", "设施类型", 55, "2025-01-22 15:03:05", "2025-01-22 15:03:05"),
        (39, "道路绿化", "设施类型", 55, "2025-01-22 15:03:16", "2025-01-22 15:03:16"),
        (40, "防眩屏", "设施类型", 55, "2025-01-22 15:03:49", "2025-01-22 15:03:49"),
        (41, "照明设施", "设施类型", 55, "2025-01-22 15:03:59", "2025-01-22 15:03:59"),
        (42, "交通标志", "设施类型", 55, "2025-01-22 15:04:13", "2025-01-22 15:04:13"),
        (43, "交通标线", "设施类型", 55, "2025-01-22 15:04:28", "2025-01-22 15:04:28"),
        (44, "凌晨", "致灾时段", 76, "2025-02-07 13:21:51", "2025-02-07 13:21:51"),
        (45, "上午", "致灾时段", 76, "2025-02-07 13:22:06", "2025-02-07 13:22:06"),
        (46, "下午", "致灾时段", 76, "2025-02-07 13:22:13", "2025-02-07 13:22:13"),
        (47, "晚上", "致灾时段", 76, "2025-02-07 13:22:29", "2025-02-07 13:22:29"),
        (48, '防汛车辆', '资源类型', 44, '2025-01-16 14:00:10', '2025-01-16 14:00:10'),
        (49, '封道抢险车', '资源类型', 44, '2025-01-16 14:00:18', '2025-01-16 14:00:18'),
        (50, '警车', '资源类型', 44, '2025-01-16 14:00:25', '2025-01-16 14:00:25'),
        (51, '消防员', '资源类型', 44, '2025-01-16 14:00:32', '2025-01-16 14:00:32'),
        (52, '牵引人员', '资源类型', 44, '2025-01-16 14:00:40', '2025-01-16 14:00:40'),
        (53, '安全锥', '资源类型', 44, '2025-01-16 14:00:47', '2025-01-16 14:00:47'),
        (54, '抽水泵', '资源类型', 44, '2025-01-16 14:00:54', '2025-01-16 14:00:54'),
        (55, '医疗物资', '资源类型', 44, '2025-01-16 14:01:01', '2025-01-16 14:01:01'),
        (56, '发电机', '物资', 44, '2025-01-16 14:01:08', '2025-01-16 14:01:08'),
        (57, '草包', '资源类型', 44, '2025-01-16 14:01:15', '2025-01-16 14:01:15'),
        (58, '蛇皮袋', '资源类型', 44, '2025-01-16 14:01:22', '2025-01-16 14:01:22'),
        (59, '扫帚', '资源类型', 44, '2025-01-16 14:01:29', '2025-01-16 14:01:29'),
        (60, '撬棒', '资源类型', 44, '2025-01-16 14:01:36', '2025-01-16 14:01:36'),
        (61, '千斤顶', '资源类型', 44, '2025-01-16 14:01:43', '2025-01-16 14:01:43'),
        (62, '随车修理工具', '资源类型', 44, '2025-01-16 14:01:50', '2025-01-16 14:01:50'),
        (63, '辅助轮', '资源类型', 44, '2025-01-16 14:01:57', '2025-01-16 14:01:57'),
        (64, '黄沙', '资源类型', 44, '2025-01-16 14:02:05', '2025-01-16 14:02:05'),
    ]
    objs = []
    for row in raw_data:
        (enum_id, val, desc_txt, ad_id, ctime, utime) = row
        objs.append(EnumValue(
            enum_value_id=enum_id,
            enum_value=val,
            description=desc_txt,
            attribute_definition_id=ad_id,
            create_time=ctime,
            update_time=utime
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_template(session):
    """
    INSERT INTO `template` VALUES (1, 1, 1, '车辆承灾要素', ...),
    ..., (14, 13, 4, '应急预案', ...);
    """
    raw_data = [
        (1, 1, 1, '车辆承灾要素', '{"show": [{}], "create": {"entity_type": "Vehicle", "category_type": ["AffectedElement"]}, "select": {"entity_type": "Vehicle", "category_type": "AffectedElement"}}',
         None, '2025-01-15 11:46:12', '2025-01-15 11:46:12'),
        (2, 2, 1, '道路承灾要素', '{"show": [{"aspect_type": "Affected"}], "create": {"entity_type": "Road", "category_type": ["AffectedElement"]}, "select": {"entity_type": "Road", "category_type": "AffectedElement"}}',
         None, '2025-01-15 12:44:15', '2025-01-15 12:44:15'),
        (3, 12, 5, '人类承灾要素', '{"show": [{}], "create": {"attribute": [{"CasualtyCondition": "1"}], "entity_type": "People", "category_type": ["Item"]}, "select": {"attribute": [{"CasualtyCondition": "1"}], "entity_type": "People", "category_type": "Item"}}',
         '展示时仅展示受伤的', '2025-01-15 12:44:42', '2025-01-15 12:44:42'),
        (4, 1, 3, '车辆致灾要素', '{"show": [{}], "create": {"entity_type": "Vehicle", "category_type": "HazardElement"}, "select": {"entity_type": "Vehicle", "category_type": "HazardElement"}}',
         None, '2025-01-15 12:46:02', '2025-01-15 12:46:02'),
        (5, 2, 2, '道路环境要素', '{"show": [{"aspect_type": "Environment"}], "create": {"entity_type": "Road", "category_type": ["EnvironmentElement"]}, "select": {"entity_type": "Road", "category_type": "EnvironmentElement"}}',
         None, '2025-01-15 12:47:00', '2025-01-15 12:47:00'),
        (6, 3, 2, '气象环境要素', '{"show": [{}], "create": {"entity_type": "Meteorology", "category_type": "EnvironmentElement"}, "select": {"entity_type": "Meteorology", "category_type": "EnvironmentElement"}}',
         None, '2025-01-15 12:55:22', '2025-01-15 12:55:22'),
        (7, 4, 4, '应急资源要素', '{"show": [{}], "create": {"entity_type": "ResponseResource", "category_type": "ResponsePlanElement"}, "select": {"entity_type": "ResponseResource", "category_type": "ResponsePlanElement"}}',
         None, '2025-01-15 12:55:23', '2025-01-15 12:55:23'),
        (8, 5, 4, '应急行为要素', '{"show": [{}], "create": {"entity_type": "ResponseAction", "category_type": "ResponsePlanElement"}, "select": {"entity_type": "ResponseAction", "category_type": "ResponsePlanElement"}}',
         None, '2025-01-15 12:55:23', '2025-01-15 12:55:23'),
        (9, 8, 5, '基础设施', '{"show": [{}], "create": {"entity_type": "Facility", "category_type": "Item"}, "select": {"entity_type": "Facility", "category_type": "Item"}}',
         None, '2025-01-15 12:56:36', '2025-01-15 13:02:10'),
        (10, 11, 5, '车道', '{"show": [{}], "create": {"entity_type": "Lane", "category_type": "Item"}, "select": {"entity_type": "Lane", "category_type": "Item"}}',
         None, '2025-01-16 22:59:16', '2025-01-16 22:59:19'),
        (11, 12, 5, '人类', '{"show": [{}], "create": {"entity_type": "People", "category_type": "Item"}, "select": {"entity_type": "People", "category_type": "Item"}}',
         None, '2025-01-16 23:00:07', '2025-01-16 23:00:09'),
        (12, 6, 5, '车辆部件', '{"show": [{}], "create": {"entity_type": "VehiclePart", "category_type": "Item"}, "select": {"entity_type": "VehiclePart", "category_type": "Item"}}',
         None, '2025-01-16 23:01:15', '2025-01-16 23:01:18'),
        (13, 7, 5, '承载物', '{"show": [{}], "create": {"entity_type\": \"VehicleLoad\", \"category_type\": \"Item\"}, \"select\": {\"entity_type\": \"VehicleLoad\", \"category_type\": \"Item\"}}',
         None, '2025-01-16 23:02:15', '2025-01-16 23:02:17'),
        (14, 13, 4, '应急预案', '{"show": [{}], "create": {"entity_type\": \"ResponsePlan\", \"category_type\": \"ResponsePlanElement\"}, \"select\": {\"entity_type\": \"ResponsePlan\", \"category_type\": \"ResponsePlanElement\"}}',
         None, '2025-01-16 23:03:20', '2025-01-16 23:03:23'),
    ]
    objs = []
    for row in raw_data:
        (
            tmpl_id,
            et_id,
            cat_id,
            tmpl_name,
            tmpl_json,
            desc_txt,
            ctime,
            utime
        ) = row
        objs.append(Template(
            template_id=tmpl_id,
            entity_type_id=et_id,
            category_id=cat_id,
            template_name=tmpl_name,
            template_restrict=json.loads(tmpl_json),
            description=desc_txt,
            create_time=ctime,
            update_time=utime
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_template_attribute_definition(session):
    """
    INSERT INTO `template_attribute_definition` VALUES
      (1,1),(4,1),(4,2),(1,3),...,(14,73),(14,74);
    """
    raw_data = [
        (1, 1), (4, 1), (4, 2), (1, 3), (4, 3), (1, 4), (4, 4), (4, 5),
        (4, 6), (4, 7), (4, 8), (1, 9), (4, 9), (1, 10), (4, 10), (1, 11),
        (4, 11), (1, 12), (4, 12), (1, 13), (4, 13), (1, 14), (4, 14),
        (1, 15), (4, 15), (1, 16), (3, 17), (11, 17), (3, 18), (11, 18),
        (2, 19), (5, 19), (2, 20), (5, 20), (2, 21), (5, 21), (2, 22), (5, 22),
        (2, 23), (5, 23), (2, 24), (5, 24), (2, 25), (5, 25), (2, 26), (5, 26),
        (2, 27), (2, 28), (2, 29), (5, 29), (2, 30), (5, 30), (2, 31), (5, 31),
        (5, 32), (5, 33), (6, 34), (6, 35), (6, 36), (6, 37), (6, 38), (6, 39),
        (6, 40), (5, 41), (5, 42), (5, 43), (7, 44), (7, 45), (7, 46), (7, 47),
        (8, 48), (8, 49), (8, 50), (8, 51), (8, 52), (8, 53), (8, 54),
        (9, 55), (9, 56), (9, 57), (9, 58), (10, 59), (10, 60), (10, 61), (10, 62),
        (10, 63), (10, 64), (10, 65), (10, 66), (12, 67), (12, 68), (13, 68),
        (12, 69), (13, 70), (13, 71), (14, 72), (14, 73), (14, 74), (7, 75),
        (4, 76), (5,27),(5,28),(2,32),(2,33)
    ]
    for (template_id, attr_def_id) in raw_data:
        tmpl = session.query(Template).filter_by(template_id=template_id).one()
        ad = session.query(AttributeDefinition).filter_by(attribute_definition_id=attr_def_id).one()
        tmpl.attribute_definitions.append(ad)
    session.commit()


def seed_template_behavior_definition(session):
    """
    INSERT INTO `template_behavior_definition` VALUES
      (1,1),(4,1),(1,2),(4,2),...,(8,17);
    """
    raw_data = [
        (1, 1), (4, 1), (1, 2), (4, 2), (1, 3), (4, 3), (1, 4), (4, 4),
        (1, 5), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (1, 11),
        (4, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16), (8, 17),(8,18)
    ]
    for (template_id, behavior_def_id) in raw_data:
        tmpl = session.query(Template).filter_by(template_id=template_id).one()
        bd = session.query(BehaviorDefinition).filter_by(behavior_definition_id=behavior_def_id).one()
        tmpl.behavior_definitions.append(bd)
    session.commit()

def seed_attribute_type(session):
    """
    对应:
      INSERT INTO `attribute_type` VALUES (1, 'String', '字符串', NULL, 1, '2025-01-15...', ... ), ...
    """
    data = [
        AttributeType(
            attribute_type_id=1,
            attribute_type_code='String',
            attribute_type_name='字符串',
            description=None,
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
        AttributeType(
            attribute_type_id=2,
            attribute_type_code='Real',
            attribute_type_name='数值型',
            description=None,
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
        AttributeType(
            attribute_type_id=3,
            attribute_type_code='Bool',
            attribute_type_name='布尔型',
            description=None,
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
        AttributeType(
            attribute_type_id=4,
            attribute_type_code='Enum',
            attribute_type_name='枚举型',
            description=None,
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
        AttributeType(
            attribute_type_id=5,
            attribute_type_code='Item',
            attribute_type_name='Item',
            description='实体-Item级',
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
        AttributeType(
            attribute_type_id=6,
            attribute_type_code='Entity',
            attribute_type_name='Entity',
            description='实体-非Item级',
            status=True,
            create_time='2025-01-15 11:10:14',
            update_time='2025-01-15 11:10:14'
        ),
    ]
    session.bulk_save_objects(data)
    session.commit()


def seed_entity_type(session):
    """
    对应:
      INSERT INTO `entity_type` VALUES (1, '车辆', 'Vehicle', 0, ..., 1, '2025-01-15...', ... ), ...
    """
    data = [
        EntityType(entity_type_id=1, entity_type_name='车辆', entity_type_code='Vehicle',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=2, entity_type_name='路段', entity_type_code='Road',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=3, entity_type_name='自然环境', entity_type_code='Meteorology',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=4, entity_type_name='应急资源', entity_type_code='ResponseResource',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=5, entity_type_name='应急行为', entity_type_code='ResponseAction',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=6, entity_type_name='车辆部件', entity_type_code='VehiclePart',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=7, entity_type_name='承载物', entity_type_code='VehicleLoad',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=8, entity_type_name='基础设施', entity_type_code='Facility',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=11, entity_type_name='车道', entity_type_code='Lane',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:38'),
        EntityType(entity_type_id=12, entity_type_name='人类', entity_type_code='People',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:35'),
        EntityType(entity_type_id=13, entity_type_name='应急预案', entity_type_code='ResponsePlan',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:32'),
    ]
    session.bulk_save_objects(data)
    session.commit()


def seed_attribute_definition(session):
    """
    INSERT INTO `attribute_definition` VALUES
      (1, '车辆类型', '车辆类型', 1, 1, 4, 1, 0, 0, NULL, NULL, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
      ...
      (74, '包含行动', '包含行动', 74, 6, 4, 0, 1, 1, 5, NULL, '应急预案', '2025-01-20 19:38:08', '2025-01-20 19:38:10');
    """
    raw_data = [
        (1, '车辆类型', 'VehicleType', 1, 1, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (2, '碰撞情况', 'CollisionStatus', 2, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (3, '燃爆情况', 'ExplosionCondition', 3, 3, 4, 1, 0, 0, None, '0', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (4, '抛洒情况', 'SpillageCondition', 4, 3, 4, 1, 0, 0, None, '0', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (5, '抛锚情况', 'BreakdownCondition', 5, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (6, '侧翻情况', 'RolloverCondition', 6, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (7, '速度异常情况', 'SpeedAnomalyCondition', 7, 3, 1, 0, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (8, '违规占道情况', 'ILLegalLaneOccupationCondition', 8, 3, 1, 0, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (9, '行驶方向', 'DrivingDirection', 9, 4, 4, 0, 0, 0, None, '正向', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (10, '车辆位置', 'VehicleLocation', 10, 1, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (11, '车辆速度', 'VehicleSpeed', 11, 2, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (12, '车辆货物', 'VehicleCargo', 12, 5, 4, 0, 1, 1, 7, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (13, '车辆乘客', 'VehiclePassengers', 13, 5, 4, 0, 1, 1, 12, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (14, '车辆部件', 'VehicleComponents', 14, 5, 4, 0, 1, 1, 6, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (15, '所行驶路段', 'DrivenRoad', 15, 6, 4, 1, 0, 1, 2, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (16, '受损情况', 'DamageCondition', 16, 3, 3, 1, 0, 0, None, '0', '车辆-承灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (17, '伤亡情况', 'CasualtyCondition', 17, 3, 4, 1, 0, 0, None, '0', '人类', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (18, '所属车辆', 'AffiliatedVehicle', 18, 6, 4, 1, 0, 1, 1, None, '人类', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (19, '道路名称', 'RoadName', 19, 1, 4, 0, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (20, '道路类型', 'RoadType', 20, 4, 4, 1, 0, 0, None, '主路', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (21, '行车道数', 'NumberOfLanes', 21, 2, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (22, '交通量', 'TrafficVolume', 22, 2, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (23, '段起点桩号', 'RoadStartStake', 23, 1, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (24, '段终点桩号', 'RoadEndStake', 24, 1, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (25, '设计车速', 'DesignSpeed', 25, 2, 4, 0, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (26, '封闭情况', 'ClosureCondition', 26, 3, 4, 1, 0, 0, None, '0', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (27, '受损情况', 'DamageCondition', 27, 3, 4, 1, 0, 0, None, '0', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (28, '污染情况', 'PollutionCondition', 28, 3, 4, 1, 0, 0, None, '0', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (29, '所含车道', 'ContainedLanes', 40, 5, 4, 1, 1, 1, 11, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (30, '所含设施', 'ContainedFacilities', 29, 5, 4, 0, 1, 1, 8, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (31, '所含车辆', 'ContainedVehicles', 30, 6, 4, 1, 1, 1, 1, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (32, '道路养护情况', 'RoadMaintenanceCondition', 31, 3, 2, 0, 0, 0, None, '0', '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (33, '道路施工情况', 'RoadConstructionCondition', 32, 3, 2, 0, 0, 0, None, '0', '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (34, '气象类型', 'WeatherType', 33, 4, 4, 1, 0, 0, None, '晴天', '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (35, '降雨量', 'RainfallAmount', 34, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (36, '能见度', 'Visibility', 35, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (37, '风速', 'WindSpeed', 36, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (38, '风力', 'WindForce', 37, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (39, '降雪强度', 'SnowfallIntensity', 38, 4, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (40, '作用区域', 'AffectedArea', 39, 6, 4, 1, 1, 1, 2, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (41, '通行时间', 'PassageTime', 41, 2, 2, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (42, '通行能力', 'TrafficCapacity', 49, 2, 2, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (43, '限速值', 'SpeedLimit', 42, 2, 2, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (44, '资源类型', 'ResourceType', 43, 4, 4, 1, 0, 0, None, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (45, '资源使用情况', 'ResourceUsageCondition', 44, 3, 4, 0, 0, 0, None, '0', '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (46, '资源数（质）量', 'ResourceQuantity', 45, 2, 4, 0, 0, 0, None, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (47, '关联行为', 'AssociatedBehavior', 46, 6, 4, 1, 0, 1, 5, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (48, '行为类型', 'BehaviorType', 47, 4, 4, 1, 0, 0, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (49, '实施情况', 'ImplementationCondition', 48, 3, 4, 1, 0, 0, None, '0', '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (50, '持续时间', 'Duration', 50, 2, 4, 1, 0, 0, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (51, '涉及物资', 'InvolvedMaterials', 51, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (52, '实施人员', 'ImplementationPersonnel', 52, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (53, '应急车辆', 'EmergencyVehicles', 53, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (54, '实施对象', 'ImplementationTarget', 54, 6, 4, 1, 1, 1, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (55, '设施类型', 'FacilityType', 55, 4, 4, 1, 0, 0, None, '立柱', '基础设施', '2025-01-16 23:10:21', '2025-01-16 23:10:23'),
        (56, '设施位置', 'FacilityLocation', 56, 1, 4, 1, 0, 0, None, None, '基础设施', '2025-01-16 23:11:21', '2025-01-16 23:11:25'),
        (57, '受损情况', 'DamageStatus', 57, 3, 4, 1, 0, 0, None, '0', '基础设施', '2025-03-01 23:12:06', '2025-01-16 23:12:09'),
        (58, '所属路段', 'AffiliatedRoad', 58, 6, 4, 1, 0, 1, 2, None, '基础设施', '2025-01-16 23:12:48', '2025-01-16 23:12:51'),
        (59, '车道类型', 'LaneType', 59, 1, 4, 1, 0, 0, None, None, '车道', '2025-01-20 19:14:23', '2025-01-20 19:14:25'),
        (60, '车道宽度', 'LaneWidth', 60, 2, 4, 0, 0, 0, None, None, '车道', '2025-01-20 19:15:17', '2025-01-20 19:15:18'),
        (61, '车行道设计车速', 'CarriagewayDesignSpeed', 61, 2, 4, 0, 0, 0, None, None, '车道', '2025-01-20 19:16:08', '2025-01-20 19:16:10'),
        (62, '车行道车型限制', 'CarriagewayVehicleRestrictions', 62, 3, 4, 1, 0, 0, None, '0', '车道', '2025-01-20 19:17:27', '2025-01-20 19:17:29'),
        (63, '封闭情况', 'ClosureCondition', 63, 3, 4, 1, 0, 0, None, '0', '车道', '2025-01-20 19:18:11', '2025-01-20 19:18:14'),
        (64, '污染情况', 'PollutionCondition', 64, 3, 4, 1, 0, 0, None, '0', '车道', '2025-01-20 19:18:48', '2025-01-20 19:18:50'),
        (65, '所属路段', 'AffiliatedRoad', 65, 6, 4, 1, 0, 1, 2, None, '车道', '2025-01-20 19:19:34', '2025-01-20 19:19:36'),
        (66, '所含车辆', 'ContainedVehicles', 66, 5, 4, 1, 1, 1, 1, None, '车道', '2025-01-20 19:20:08', '2025-01-20 19:20:11'),
        (67, '部件类型', 'ComponentType', 67, 4, 4, 1, 0, 0, None, None, '车辆部件', '2025-01-20 19:29:10', '2025-01-20 19:29:13'),
        (68, '是否脱落', 'ComponentType', 68, 3, 4, 1, 0, 0, None, '0', '车辆部件/承载物', '2025-01-20 19:29:58', '2025-01-20 19:30:00'),
        (69, '所属车辆', 'ComponentType', 69, 6, 4, 1, 0, 1, 1, None, '车辆部件', '2025-01-20 19:30:41', '2025-01-20 19:30:44'),
        (70, '承载物类型', 'CarriedObjectType', 70, 4, 4, 1, 0, 0, None, None, '承载物', '2025-01-20 19:31:29', '2025-01-20 19:31:31'),
        (71, '所属车辆', 'AffiliatedVehicle', 71, 6, 4, 1, 0, 1, 1, None, '承载物', '2025-01-20 19:32:02', '2025-01-20 19:32:05'),
        (72, '预案名称', 'EmergencyPlanName', 72, 1, 4, 1, 0, 0, None, '默认预案', '应急预案', '2025-01-20 19:36:24', '2025-01-20 19:36:26'),
        (73, '包含资源', 'ContainedResources', 73, 6, 4, 0, 1, 1, 4, None, '应急预案', '2025-01-20 19:37:37', '2025-01-20 19:37:39'),
        (74, '包含行动', 'ContainedActions', 74, 6, 4, 0, 1, 1, 5, None, '应急预案', '2025-01-20 19:38:08', '2025-01-20 19:38:10'),
        (75, '资源位置', 'ResourceLocation', 75, 1, 4, 0, 0, 0, None, '未知', '应急资源', '2025-01-25 15:37:03', '2025-01-25 15:37:03'),
        (76, '致灾时段', 'DisasterPeriod', 76, 4, 1, 1, 0, 0,None, '上午', '车辆 - 致灾体专有', '2025-02-07 13:14:52', '2025-02-07 13:14:52'),
    ]
    objs = []
    for d in raw_data:
        (
            def_id,
            cn_name,
            en_name,
            code_id,
            type_id,
            aspect_id,
            req_flag,
            multi_flag,
            ref_flag,
            ref_target,
            default_val,
            desc_txt,
            ctime,
            utime
        ) = d
        objs.append(AttributeDefinition(
            attribute_definition_id=def_id,
            china_default_name=cn_name,
            english_default_name=en_name,
            attribute_code_id=code_id,
            attribute_type_id=type_id,
            attribute_aspect_id=aspect_id,
            is_required=bool(req_flag),
            is_multi_valued=bool(multi_flag),
            is_reference=bool(ref_flag),
            reference_target_type_id=ref_target,
            default_value=default_val,
            description=desc_txt,
            create_time=ctime,
            update_time=utime
        ))
    session.bulk_save_objects(objs)
    session.commit()



def seed_behavior_code(session):
    """
    INSERT INTO behavior_code VALUES (1, 'VehicleMotion', '车辆行驶', ...), ...
    """
    data = [
        BehaviorCode(
            behavior_code_id=1,
            behavior_code_name='VehicleMotion',
            description='车辆行驶',
            create_time='2025-01-16 21:10:53',
            update_time='2025-01-16 21:10:53'
        ),
        BehaviorCode(
            behavior_code_id=2,
            behavior_code_name='VehicleTransport',
            description='车辆运载',
            create_time='2025-01-16 21:11:43',
            update_time='2025-01-16 21:11:43'
        ),
        BehaviorCode(
            behavior_code_id=3,
            behavior_code_name='VehicleDeparture',
            description='车辆离开',
            create_time='2025-01-16 21:11:53',
            update_time='2025-01-16 21:11:53'
        ),
        BehaviorCode(
            behavior_code_id=4,
            behavior_code_name='VehicleExplosion',
            description='车辆燃爆',
            create_time='2025-01-16 21:12:04',
            update_time='2025-01-16 21:12:04'
        ),
        BehaviorCode(
            behavior_code_id=5,
            behavior_code_name='VehicleSpillage',
            description='车辆抛洒',
            create_time='2025-01-16 21:12:15',
            update_time='2025-01-16 21:12:15'
        ),
        BehaviorCode(
            behavior_code_id=6,
            behavior_code_name='VehicleOverturn',
            description='车辆侧翻',
            create_time='2025-01-16 21:12:28',
            update_time='2025-01-16 21:12:28'
        ),
        BehaviorCode(
            behavior_code_id=7,
            behavior_code_name='VehicleBreakdown',
            description='车辆抛锚',
            create_time='2025-01-16 21:12:49',
            update_time='2025-01-16 21:12:49'
        ),
        BehaviorCode(
            behavior_code_id=8,
            behavior_code_name='VehicleCollision',
            description='车辆撞击',
            create_time='2025-01-16 21:13:05',
            update_time='2025-01-16 21:13:05'
        ),
        BehaviorCode(
            behavior_code_id=9,
            behavior_code_name='VehicleTurning',
            description='车辆转向',
            create_time='2025-01-16 21:13:22',
            update_time='2025-01-16 21:13:22'
        ),
        BehaviorCode(
            behavior_code_id=10,
            behavior_code_name='VehicleLaneChange',
            description='车辆变道',
            create_time='2025-01-16 21:13:40',
            update_time='2025-01-16 21:13:40'
        ),
        BehaviorCode(
            behavior_code_id=11,
            behavior_code_name='VehicleSpeedChange',
            description='车辆变速',
            create_time='2025-01-16 21:14:02',
            update_time='2025-01-16 21:14:02'
        ),
        BehaviorCode(
            behavior_code_id=12,
            behavior_code_name='Firefighting',
            description='消防',
            create_time='2025-01-16 21:14:13',
            update_time='2025-01-16 21:14:13'
        ),
        BehaviorCode(
            behavior_code_id=13,
            behavior_code_name='PersonnalRescue',
            description='人员救护',
            create_time='2025-01-16 21:14:30',
            update_time='2025-01-16 21:14:30'
        ),
        BehaviorCode(
            behavior_code_id=14,
            behavior_code_name='VehicleTowing',
            description='车辆牵引',
            create_time='2025-01-16 21:14:42',
            update_time='2025-01-16 21:14:42'
        ),
        BehaviorCode(
            behavior_code_id=15,
            behavior_code_name='RoadCleaning',
            description='路面清扫',
            create_time='2025-01-16 21:14:54',
            update_time='2025-01-16 21:14:54'
        ),
        BehaviorCode(
            behavior_code_id=16,
            behavior_code_name='RoadRepair',
            description='道路抢修',
            create_time='2025-01-16 21:15:05',
            update_time='2025-01-16 21:15:05'
        ),
        BehaviorCode(
            behavior_code_id=17,
            behavior_code_name='RoadControl',
            description='道路管制',
            create_time='2025-01-16 21:15:17',
            update_time='2025-01-16 21:15:17'
        ),
        BehaviorCode(
            behavior_code_id=18,
            behavior_code_name='HazardousMaterialDisposal',
            description='危化品处置',
            create_time='2025-01-16 21:15:35',
            update_time='2025-01-16 21:15:35'
        )
    ]

    session.bulk_save_objects(data)
    session.commit()

def seed_behavior_definition(session):
    """
    INSERT INTO `behavior_definition` VALUES (1, '车辆行驶', '车辆行驶', 1, 1, 2, 0, '车辆-共有', ...), ...
    """
    raw_data = [
        (1, '车辆行驶', 'VehicleMovement', 1, 1, 2, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (2, '车辆运载', 'VehicleTransport', 2, 0, 7, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (3, '车辆离开', 'VehicleDeparture', 3, 1, 2, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (4, '车辆燃爆', 'VehicleExplosion', 4, 1, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (5, '车辆抛洒', 'VehicleSpillage', 5, 1, 7, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (6, '车辆侧翻', 'VehicleRollover', 6, 1, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (7, '车辆抛锚', 'VehicleBreakdown', 7, 1, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (8, '车辆撞击', 'VehicleCollision', 8, 1, None, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (9, '车辆转向', 'VehicleSteering', 9, 1, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (10, '车辆变道', 'VehicleLaneChange', 10, 1, 11, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (11, '车辆变速', 'VehicleSpeedChange', 11, 1, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (12, '消防', 'Firefighting', 12, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (13, '人员救护', 'PersonnelRescue', 13, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (14, '车辆牵引', 'VehicleTowing', 14, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (15, '路面清扫', 'RoadCleaning', 15, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (16, '道路抢修', 'RoadRepair', 16, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (17, '道路管制', 'RoadControl', 17, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (18, '危化品处置', 'HazardousMaterialDisposal', 18, 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
    ]
    objs = []
    for row in raw_data:
        (def_id, zh_name, en_name, b_code_id,
         required, obj_et_id, multi, desc_txt,
         ctime, utime) = row
        objs.append(BehaviorDefinition(
            behavior_definition_id=def_id,
            china_default_name=zh_name,
            english_default_name=en_name,
            behavior_code_id=b_code_id,
            is_required=bool(required),
            object_entity_type_id=obj_et_id,
            is_multi_valued=bool(multi),
            description=desc_txt,
            create_time=ctime,
            update_time=utime
        ))
    session.bulk_save_objects(objs)
    session.commit()


def seed_behavior_name_code(session):
    """
    注意：behavior_name_code 表的主键应该是 (behavior_code_id, behavior_name) 的组合
    """
    raw_data = [
        (1, 'VehicleMotion'),
        (2, 'VehicleTransport'),
        (3, 'VehicleDeparture'),
        (4, 'VehicleExplosion'),
        (5, 'VehicleSpillage'),
        (5, 'Spill'),  # 这条记录和上面的记录有相同的 behavior_code_id，但 behavior_name 不同
        (6, 'VehicleOverturn'),
        (7, 'VehicleBreakdown'),
        (8, 'VehicleCollision'),
        (8, 'Collide'),
        (9, 'VehicleTurning'),
        (10, 'VehicleLaneChange'),
        (11, 'VehicleSpeedChange'),
        (12, 'Firefighting'),
        (13, 'PersonnalRescue'),
        (14, 'VehicleTowing'),
        (15, 'RoadCleaning'),
        (16, 'RoadRepair'),
        (17, 'RoadControl'),
        (18, 'HazardousMaterialDisposal'),
    ]

    # 一次插入一条记录，这样如果有某条记录出错，其他记录还能继续
    for code_id, name in raw_data:
        try:
            obj = BehaviorNameCode(
                behavior_code_id=code_id,
                behavior_name=name
            )
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting behavior_name_code: {code_id}, {name}")
            print(f"Error: {str(e)}")
            # 继续处理下一条记录

    print("behavior_name_code 表插入完成")
########################################################################
#  seed_all: 统一调用
########################################################################

def has_records(session, model):
    """检查表是否已有数据"""
    return session.query(model).first() is not None


def seed_all(session):
    """
    依照外键依赖顺序执行所有插入函数，如果表中已有数据则跳过
    """
    try:
        print("开始数据初始化...")

        # 1. 无外键依赖的基础表
        print("正在检查和插入基础数据...")

        if not has_records(session, AttributeAspect):
            print("插入 AttributeAspect 数据...")
            seed_attribute_aspect(session)
        else:
            print("AttributeAspect 表已有数据，跳过")

        if not has_records(session, AttributeType):
            print("插入 AttributeType 数据...")
            seed_attribute_type(session)
        else:
            print("AttributeType 表已有数据，跳过")

        if not has_records(session, EntityType):
            print("插入 EntityType 数据...")
            seed_entity_type(session)
        else:
            print("EntityType 表已有数据，跳过")

        if not has_records(session, Category):
            print("插入 Category 数据...")
            seed_category(session)
        else:
            print("Category 表已有数据，跳过")

        if not has_records(session, Emergency):
            print("插入 Emergency 数据...")
            seed_emergency(session)
        else:
            print("Emergency 表已有数据，跳过")

        if not has_records(session, OwlType):
            print("插入 OwlType 数据...")
            seed_owl_type(session)
        else:
            print("OwlType 表已有数据，跳过")

        # 2. 第一层依赖的表
        print("正在检查和插入第一层依赖表...")
        if not has_records(session, AttributeCode):
            print("插入 AttributeCode 数据...")
            seed_attribute_code(session)
        else:
            print("AttributeCode 表已有数据，跳过")

        if not has_records(session, AttributeCodeName):
            print("插入 AttributeCodeName 数据...")
            seed_attribute_code_name(session)
        else:
            print("AttributeCodeName 表已有数据，跳过")

        if not has_records(session, BehaviorCode):
            print("插入 BehaviorCode 数据...")
            seed_behavior_code(session)
        else:
            print("BehaviorCode 表已有数据，跳过")

        if not has_records(session, BehaviorNameCode):
            print("插入 BehaviorNameCode 数据...")
            seed_behavior_name_code(session)
        else:
            print("BehaviorNameCode 表已有数据，跳过")

        # 3. 第二层依赖的表
        print("正在检查和插入第二层依赖表...")
        if not has_records(session, AttributeDefinition):
            print("插入 AttributeDefinition 数据...")
            seed_attribute_definition(session)
        else:
            print("AttributeDefinition 表已有数据，跳过")

        if not has_records(session, BehaviorDefinition):
            print("插入 BehaviorDefinition 数据...")
            seed_behavior_definition(session)
        else:
            print("BehaviorDefinition 表已有数据，跳过")

        # 4. 第三层依赖的表
        print("正在检查和插入第三层依赖表...")
        if not has_records(session, EnumValue):
            print("插入 EnumValue 数据...")
            seed_enum_value(session)
        else:
            print("EnumValue 表已有数据，跳过")

        if not has_records(session, Scenario):
            print("插入 Scenario 数据...")
            seed_scenario(session)
        else:
            print("Scenario 表已有数据，跳过")

        # 5. template 及其关联
        print("正在检查和插入模板数据...")
        if not has_records(session, Template):
            print("插入 Template 数据...")
            seed_template(session)
            seed_template_attribute_definition(session)
            seed_template_behavior_definition(session)
        else:
            print("Template 相关表已有数据，跳过")

        print("数据初始化完成！")

    except Exception as e:
        session.rollback()
        print(f"插入失败: {str(e)}")
        raise
    finally:
        session.close()

########################################################################
#  主入口
########################################################################

if __name__ == '__main__':
    # 请将下面的连接信息替换为你自己的数据库URI
    engine = create_engine("mysql+pymysql://root:password@127.0.0.1:3306/test?charset=utf8mb4")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # 如果需要先建表（前提是 models.py 的定义与数据库结构完全对应），可取消下行注释
    # Base.metadata.create_all(engine)

    # 一键插入所有数据
    seed_all(session)
