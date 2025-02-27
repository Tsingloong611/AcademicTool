import types
from owlready2 import *
import json
from openpyxl import Workbook
import datetime
import os
from rdflib import URIRef, RDF, OWL


import types
from owlready2 import *
import json
from openpyxl import Workbook
import datetime
import os

def create_ontology(input_path, output_path):
    """
    创建本体并保存到指定的位置，并在 ABox 层面带上数据属性的具体值。
    当遇到 @type = attribute 时，会给对应的“owner”个体赋值。
    同时，对于一些对象属性类(partAssociate、exhibitState、itemComposition等)，
    在 ABox 里建立对应的实例之间的关联，从而使得对象属性的值可以真正指向对应实例。
    """

    # 加载 json 文件
    with open(input_path, "r", encoding='utf-8') as file:
        data = json.load(file)

    # 设定创建顺序，防止处理 attribute / 对象属性 时，对应的类还没创建
    desired_order = [
        'part', 'partSub', 'partAssociate', 'item',
        'state', 'action', 'attribute',
        'exhibitState', 'itemComposition'
    ]

    # 根据 desired_order 对数据进行排序
    sorted_data = sorted(
        data,
        key=lambda x: desired_order.index(x['@type']) if x['@type'] in desired_order else len(desired_order)
    )

    # 清除之前的本体(避免多次运行时叠加)
    default_world.ontologies.clear()

    # 使用特定的 IRI 创建新的本体
    onto = get_ontology("http://example.org/scenario_element.owl")

    # 用于存储创建的类、数据属性、对象属性，以及个体
    classes = {}
    data_props = {}
    obj_props = {}
    instances = {}

    with onto:
        # ============ 1. 先创建顶层/公用类 =============
        class ScenarioElement(Thing):
            pass

        class AffectedElement(ScenarioElement):
            pass

        class HazardElement(ScenarioElement):
            pass

        class EnvironmentElement(ScenarioElement):
            pass

        class ResponsePlanElement(ScenarioElement):
            pass

        # Item 转换
        class ElementCompositions(Thing):
            pass

        # 创建 ElementState class 及其子类
        class ElementState(Thing):
            pass

        class AffectedStates(ElementState):
            pass

        class HazardStates(ElementState):
            pass

        class ResponseStates(ElementState):
            pass  # 示例中预留

        # ResponsePlanElement 的子类
        class ResponseResource(ResponsePlanElement):
            pass

        class ResponseAction(ResponsePlanElement):
            pass

        # ============ 2. 预先创建一些常用对象属性 (若需要) ============
        associateWith_prop = types.new_class('associateWith', (ObjectProperty,))
        classes['associateWith'] = associateWith_prop

        cC_prop = types.new_class('consistComposition', (ObjectProperty,))
        classes['consistComposition'] = cC_prop

        eS_prop = types.new_class('exhibitState', (ObjectProperty,))
        classes['exhibitState'] = eS_prop

        hE_prop = types.new_class('hasEffectOn', (ObjectProperty,))
        classes['hasEffectOn'] = hE_prop

        sT_prop = types.new_class('stateTransform', (ObjectProperty,))
        classes['stateTransform'] = sT_prop

        # ============ 3. 遍历 sorted_data，根据 @type 做不同处理 ============
        for element in sorted_data:
            etype = element['@type'].strip()
            ename = element['@name'].strip()

            # --------- part: 创建一个新的类，并创建一个同名实例 -------------
            if etype == 'part':
                cls = types.new_class(ename, (Thing,))
                classes[ename] = cls
                # 同时创建一个个体(若有需要)
                instances[ename] = cls(f"{ename}_inst")

            # --------- partSub: 创建一个子类 -------------
            # 在创建类时规范化名称
            def normalize_class_name(name):
                # 如果是纯数字，加上前缀
                if name.isdigit():
                    return f"Element_{name}"
                return name

            # 然后在创建类时使用：
            if etype == 'partSub':
                parent_name = element.get('parent', '').strip()
                parent_cls = classes.get(parent_name)
                if parent_cls:
                    normalized_name = normalize_class_name(ename)
                    sub_cls = types.new_class(normalized_name, (parent_cls,))
                    classes[ename] = sub_cls  # 注意：仍用原始名称作为键
                    instances[ename] = sub_cls(f"{normalized_name}_inst")

            # --------- partAssociate: 创建一个新的类 + 一个对象属性 -------------
            elif etype == 'partAssociate':
                # 先创建类
                cls = types.new_class(ename, (Thing,))
                classes[ename] = cls
                instances[ename] = cls(f"{ename}_inst")

                # 创建一个对象属性 associate{ename}, 继承自 associateWith_prop
                pA_name = 'associate' + ename
                prop = types.new_class(pA_name, (associateWith_prop,))
                obj_props[pA_name] = prop

                # 设置 domain / range (若可获取)
                owner_name = element.get('owner', '').strip()
                if owner_name and owner_name != 'none':
                    owner_cls = classes.get(owner_name)
                    if owner_cls:
                        prop.domain = [owner_cls]
                prop.range = [cls]

                # 关键：如果存在 owner 实例 和 ename 实例，都已创建完毕，则在 ABox 建立对象属性的断言
                if owner_name in instances and ename in instances:
                    owner_inst = instances[owner_name]
                    target_inst = instances[ename]
                    # 给 owner_inst 的属性 pA_name 赋值 -> 指向 target_inst
                    setattr(owner_inst, pA_name, [target_inst])

            # --------- item: 创建一个新的类(ElementCompositions子类) -------------
            elif etype == 'item':
                cls = types.new_class(ename, (ElementCompositions,))
                classes[ename] = cls
                instances[ename] = cls(f"{ename}_inst")

            # --------- state: 创建一个顶级状态类 + transitions -------------
            # elif etype == 'state':
            #     state_cls = types.new_class(ename, (ElementState,))
            #     classes[ename] = state_cls
            #     instances[ename] = state_cls(f"{ename}_inst")
            #
            #     # 处理 transitions
            #     transitions = element.get('transitions', [])
            #     # 收集 source、target 中出现的子状态名
            #     transition_class_names = set()
            #     for tr in transitions:
            #         transition_class_names.add(tr['source'])
            #         transition_class_names.add(tr['target'])
            #
            #     for tcn in transition_class_names:
            #         if tcn not in classes:
            #             # 创建子类
            #             sub_state_cls = types.new_class(tcn, (state_cls,))
            #             classes[tcn] = sub_state_cls
            #             instances[tcn] = sub_state_cls(f"{tcn}_inst")
            #
            #     # 再创建 stateTransform 属性
            #     for tr in transitions:
            #         source_name = tr['source'].strip()
            #         transit_name = tr['transit'].strip()
            #         target_name = tr['target'].strip()
            #
            #         sT_name = transit_name + 'Transform'
            #         prop = types.new_class(sT_name, (sT_prop,))
            #         obj_props[sT_name] = prop
            #
            #         source_cls = classes.get(source_name)
            #         target_cls = classes.get(target_name)
            #         if source_cls and target_cls:
            #             prop.domain = [source_cls]
            #             prop.range = [target_cls]

            # --------- action: 创建动作类 + 处理 inparams/outparams (若需要) -------------
            # elif etype == 'action':
            #     cls = types.new_class(ename, (Thing,))
            #     classes[ename] = cls
            #     instances[ename] = cls(f"{ename}_inst")
            #
            #     # 下面的逻辑是原始代码，用于创建对象属性 hasXXXEffectOn
            #     aC_name = 'has' + ename + 'EffectOn'
            #     prop = types.new_class(aC_name, (hE_prop,))
            #     obj_props[aC_name] = prop
            #
            #     # inparams
            #     for ip in element.get('inparams', []):
            #         for j in sorted_data:
            #             if j['@type'] == 'attribute' and j['@name'] == ip:
            #                 owner_j = j.get('owner', '').strip()
            #                 if owner_j not in ['', 'none'] and owner_j in classes:
            #                     prop.domain = [classes[owner_j]]
            #
            #     # outparams
            #     for op in element.get('outparams', []):
            #         for j in sorted_data:
            #             if j['@type'] == 'attribute' and j['@name'] == op:
            #                 owner_j = j.get('owner', '').strip()
            #                 if owner_j not in ['', 'none'] and owner_j in classes:
            #                     prop.range = [classes[owner_j]]
            #
            #     # actionSub 的处理(参考原始逻辑)
            #     for i in sorted_data:
            #         if i['@type'] == 'actionSub' and i.get('parent') == ename:
            #             if 'owner' in i and i['owner'] not in ['', 'none']:
            #                 if i['owner'].strip() in classes:
            #                     prop.domain = [classes[i['owner'].strip()]]

            # --------- attribute: 创建数据属性 + 给对应个体赋值 -------------
            elif etype == 'attribute':
                attr_name = ename
                owner = element.get('owner', '').strip()
                if not owner:
                    continue

                # 解析 data type
                datatype_str = element.get('datatype', 'String')
                data_value = element.get('datavalue', None)

                # 判断 Python 类型
                if datatype_str in ['Integer', 'int']:
                    dtype = int
                elif datatype_str in ['Real', 'Float', 'Double']:
                    dtype = float
                elif datatype_str in ['Boolean', 'Bool']:
                    dtype = bool
                elif datatype_str == 'Date':
                    dtype = datetime.date
                elif datatype_str == 'DateTime':
                    dtype = datetime.datetime
                elif datatype_str == 'Time':
                    dtype = datetime.time
                else:
                    # 其他情况(含 Enum, String等)，此处简单地当字符串处理
                    dtype = str

                # 如果 owner 类还没创建，跳过
                if owner not in classes:
                    continue
                owner_cls = classes[owner]

                # 创建数据属性(如果不存在)
                if attr_name not in data_props:
                    attr_prop = types.new_class(attr_name, (DataProperty,))
                    attr_prop.domain = [owner_cls]
                    attr_prop.range = [dtype]
                    data_props[attr_name] = attr_prop
                else:
                    attr_prop = data_props[attr_name]

                # 给个体赋值 (ABox)
                if owner in instances:
                    owner_inst = instances[owner]
                    if data_value and data_value.lower() != "null":
                        tmp = data_value.strip('"')
                        real_value = None
                        try:
                            if dtype == bool:
                                real_value = (tmp.lower() in ['1', 'true'])
                            elif dtype == int:
                                real_value = int(tmp)
                            elif dtype == float:
                                real_value = float(tmp)
                            else:
                                # 其他类型或字符串
                                real_value = tmp
                        except:
                            real_value = None

                        if real_value is not None:
                            setattr(owner_inst, attr_name, [real_value])

            # --------- exhibitState: 创建对象属性并在 ABox 建立关联 -------------
            elif etype == 'exhibitState':
                eS_name = 'exhibit' + ename
                prop = types.new_class(eS_name, (eS_prop,))
                obj_props[eS_name] = prop

                owner_name = element.get('owner', '').strip()
                if owner_name in classes:
                    prop.domain = [classes[owner_name]]
                if ename in classes:
                    prop.range = [classes[ename]]

                # ABox 关联：如果有对应实例，则设置对象属性
                if owner_name in instances and ename in instances:
                    owner_inst = instances[owner_name]
                    target_inst = instances[ename]
                    setattr(owner_inst, eS_name, [target_inst])

            # --------- itemComposition: 创建对象属性并在 ABox 建立关联 -------------
            elif etype == 'itemComposition':
                iC_name = 'consist' + ename
                prop = types.new_class(iC_name, (cC_prop,))
                obj_props[iC_name] = prop

                owner_name = element.get('owner', '').strip()
                parent_name = element.get('parent', '').strip()
                if owner_name in classes:
                    prop.domain = [classes[owner_name]]
                if parent_name in classes:
                    prop.range = [classes[parent_name]]

                # ABox 关联：如果有对应实例，则设置对象属性
                if owner_name in instances and parent_name in instances:
                    owner_inst = instances[owner_name]
                    target_inst = instances[parent_name]
                    setattr(owner_inst, iC_name, [target_inst])

            # --------- actionSub: (原代码中在 action 里处理 domain) -------------
            elif etype == 'actionSub':
                pass
            # 其他情况省略

    # ============ 4. 最后保存到指定位置 =============
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    onto.save(file=output_path, format="rdfxml")
    print(f"本体已保存到: {output_path}")

def Scenario_owl_creator(output_path):
    """
    创建Scenario本体并保存到指定的位置。
    """
    # 清除之前的本体
    default_world.ontologies.clear()

    # 使用特定的 IRI
    onto = get_ontology("http://example.org/scenario.owl")

    with onto:
        # Classes
        class ResilienceInfluentialFactors(Thing):
            namespace = onto

        class Scenario(Thing):
            namespace = onto

        class ScenarioResilience(Thing):
            namespace = onto

        class InvolvedScenarioElement(Thing):
            namespace = onto

        # Subclasses
        class AdaptionScenario(Scenario):
            namespace = onto

        class AbsorptionScenario(Scenario):
            namespace = onto

        class RecoveryScenario(Scenario):
            namespace = onto

        class SafetyFactors(ResilienceInfluentialFactors):
            namespace = onto

        class FunctionFactors(ResilienceInfluentialFactors):
            namespace = onto

        class EconomicFactors(ResilienceInfluentialFactors):
            namespace = onto

        class TimeFactors(ResilienceInfluentialFactors):
            namespace = onto

        # Data properties
        class casualties(DataProperty):
            namespace = onto
            domain = [SafetyFactors]
            range = [bool]

        class emergencyType(DataProperty):
            namespace = onto
            domain = [SafetyFactors]
            range = [str]

        class roadPassibility(DataProperty):
            namespace = onto
            domain = [FunctionFactors]
            range = [bool]

        class resourceType(DataProperty):
            namespace = onto
            domain = [EconomicFactors]
            range = [str]

        class roadLoss(DataProperty):
            namespace = onto
            domain = [EconomicFactors]
            range = [bool]

        class disposalDuration(DataProperty):
            namespace = onto
            domain = [TimeFactors]
            range = [str]

        class emergencyPeriod(DataProperty):
            namespace = onto
            domain = [TimeFactors]
            range = [str]

        class responseDuration(DataProperty):
            namespace = onto
            domain = [TimeFactors]
            range = [str]

        # Object properties
        class hasResilience(ObjectProperty):
            namespace = onto
            domain = [Scenario]
            range = [ScenarioResilience]

        class involvesElement(ObjectProperty):
            namespace = onto
            domain = [Scenario]
            range = [InvolvedScenarioElement]

        class influencedBy(ObjectProperty):
            namespace = onto
            domain = [Scenario]
            range = [ResilienceInfluentialFactors]

    # 保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    onto.save(file=output_path, format="rdfxml")
    print(f"Scenario本体已保存到: {output_path}")


def Emergency_owl_creator(output_path):
    """
    创建Emergency本体并保存到指定的位置。
    """
    # 清除之前的本体
    default_world.ontologies.clear()

    # 使用特定的 IRI
    onto = get_ontology("http://example.org/emergency.owl")
    with onto:
        # Classes
        class Emergency(Thing):
            namespace = onto

        class EmergencyPhase(Thing):
            namespace = onto

        class InvolvedScenario(Thing):
            namespace = onto

        # Object properties
        class inPhase(ObjectProperty):
            namespace = onto
            domain = [Emergency]
            range = [EmergencyPhase]

        class involvesScenario(ObjectProperty):
            namespace = onto
            domain = [Emergency]
            range = [InvolvedScenario]

    # 保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    onto.save(file=output_path, format="rdfxml")
    print(f"Emergency本体已保存到: {output_path}")


def owl_excel_creator(input_owl_path, output_excel_path):
    """
    将OWL文件中的属性信息整理为Excel文件。
    包括所有的数据属性和对象属性，分别写到同一个Sheet里。
    """
    # 加载OWL文件
    onto = get_ontology(input_owl_path).load()

    # 创建一个新的Excel工作簿
    wb = Workbook()
    ws = wb.active
    # 以输出 Excel 的名字作为 sheet 名(去掉扩展名 + "_Prop")
    ws.title = os.path.splitext(os.path.basename(output_excel_path))[0] + "_Prop"

    # 初始化空列表
    data_properties_list = []
    object_properties_list = []

    # 收集数据属性信息
    for dp in onto.data_properties():
        dp_dict = {
            "label": "DataProperty",
            "name": dp.name,
            "domain": dp.domain[0].name if dp.domain else "",
            "range": str(dp.range[0]) if dp.range else ""
        }
        data_properties_list.append(dp_dict)

    # 收集对象属性信息
    for op in onto.object_properties():
        op_dict = {
            "label": "ObjectProperty",
            "name": op.label[0] if op.label else op.name,
            "domain": op.domain[0].name if op.domain else "",
            "range": op.range[0].name if op.range else ""
        }
        object_properties_list.append(op_dict)

    # 写表头
    ws.append(["label", "name", "domain", "range"])

    # 先写数据属性
    for prop in data_properties_list:
        ws.append([prop["label"], prop["name"], prop["domain"], prop["range"]])

    # 再写对象属性
    for prop in object_properties_list:
        ws.append([prop["label"], prop["name"], prop["domain"], prop["range"]])

    # 保存 Excel 文件
    wb.save(output_excel_path)
    print(f"Excel文件已保存为: {output_excel_path}")


if __name__ == '__main__':
    """
    主程序示例：
    1) 从 ../data/sysml2/result 目录获取所有 json 文件
    2) 生成 ScenarioElement.owl
    3) 加载后删除 Action / Resource 类及其子类
    4) 另存再导出属性到Excel
    5) 创建 Scenario.owl 并导出
    6) 创建 Emergency.owl 并导出
    """
    # 假设你的工程目录结构和原先一致
    input_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/result')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/owl')

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 清理旧的 .owl 文件
    for f in os.listdir(output_dir):
        if f.endswith('.owl'):
            os.remove(os.path.join(output_dir, f))

    # 获取所有 JSON 文件
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

    # ========== 1) 创建 ScenarioElement 本体文件 ==========
    scenario_element_owl = os.path.join(output_dir, "ScenarioElement.owl")
    for input_file in json_files:
        input_path = os.path.join(input_dir, input_file)
        create_ontology(input_path, scenario_element_owl)

    # ========== 2) 加载 ScenarioElement.owl 文件并删除 Action / Resource 类(如果存在) ==========
    onto = get_ontology(scenario_element_owl).load()
    with onto:
        if 'Action' in onto.classes():
            destroy_entity(onto.Action)
            print("已删除类 Action 及其子类")
        if 'Resource' in onto.classes():
            destroy_entity(onto.Resource)
            print("已删除类 Resource 及其子类")

    # 保存修改后的 ScenarioElement.owl
    onto.save(file=scenario_element_owl, format="rdfxml")
    print(f"修改后的 ScenarioElement.owl 文件已保存到: {scenario_element_owl}")

    # 导出到 Excel
    owl_excel_creator(scenario_element_owl, os.path.join(output_dir, "ScenarioElement_Prop.xlsx"))

    # ========== 3) 创建 Scenario 本体并导出 ==========
    scenario_output_path = os.path.join(output_dir, "Scenario.owl")
    Scenario_owl_creator(scenario_output_path)
    owl_excel_creator(scenario_output_path, os.path.join(output_dir, "Scenario_Prop.xlsx"))

    # ========== 4) 创建 Emergency 本体并导出 ==========
    emergency_output_path = os.path.join(output_dir, "Emergency.owl")
    Emergency_owl_creator(emergency_output_path)
    owl_excel_creator(emergency_output_path, os.path.join(output_dir, "Emergency_Prop.xlsx"))
