import types
from owlready2 import *
import json
from openpyxl import Workbook
import datetime
import os

from rdflib import URIRef, RDF, OWL

'''本体生成'''


def create_ontology(input_path, output_path):
    """
    创建本体并保存到指定的位置。

    :param input_path: 输入的JSON文件的完整路径。
    :param output_path: 输出的OWL文件的完整路径（包含文件名，但不需要添加扩展名）。
    """
    # 加载json文件
    with open(input_path, "r", encoding='utf-8') as file:
        data = json.load(file)

    desired_order = ['part', 'partSub', 'partAssociate', 'item', 'state']

    sorted_data = sorted(data, key=lambda x: desired_order.index(x['@type']) if x['@type'] in desired_order else len(
        desired_order))

    # 清除之前的本体
    default_world.ontologies.clear()
    # 使用特定的 IRI
    onto = get_ontology("http://example.org/scenario_element.owl")

    elements = sorted_data

    # 用于存储创建的类，以便后续引用
    classes = {}

    with onto:
        # 创建ScenarioElement class及其子类
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

        # Item转换
        class ElementCompositions(Thing):
            pass

        # 创建ElementState class及其子类
        class ElementState(Thing):
            pass

        class AffectedStates(ElementState):
            pass

        class HazardStates(ElementState):
            pass

        class ResponseStates(ElementState):
            pass  # 假设需要添加ResponseStates

        # ResponsePlanElement 的子类
        class ResponseResource(ResponsePlanElement):
            pass

        class ResponseAction(ResponsePlanElement):
            pass

        # Object property
        aW_prop = types.new_class('associateWith', (ObjectProperty,))
        classes['associateWith'] = aW_prop

        cC_prop = types.new_class('consistComposition', (ObjectProperty,))
        classes['consistComposition'] = cC_prop

        eS_prop = types.new_class('exhibitState', (ObjectProperty,))
        classes['exhibitState'] = eS_prop

        hE_prop = types.new_class('hasEffectOn', (ObjectProperty,))
        classes['hasEffectOn'] = hE_prop

        sT_prop = types.new_class('stateTransform', (ObjectProperty,))
        classes['stateTransform'] = sT_prop

        # Class DataProperty ObjectiveProperty
        for element in elements:
            # Class
            if element['@type'] == 'part':
                # 创建一个新的类
                cls = types.new_class(element['@name'].strip(), (Thing,))
                classes[element['@name'].strip()] = cls

            elif element['@type'] == 'partSub':
                # 创建一个子类
                parent_cls = classes.get(element['parent'].strip())
                if parent_cls is not None:
                    sub_cls = types.new_class(element['@name'].strip(), (parent_cls,))
                    classes[element['@name'].strip()] = sub_cls

            elif element['@type'] == 'partAssociate':
                # 处理 partAssociate 类型，创建一个新的类
                cls = types.new_class(element['@name'].strip(), (Thing,))
                classes[element['@name'].strip()] = cls

                # 处理 partAssociate 类型，创建一个新的objetiveProperty
                pA_name = 'associate' + (element['@name'].strip())
                prop = types.new_class(pA_name, (aW_prop,))
                prop.range = [classes.get(element['@name'].strip())]
                if element['owner'] != '' and element['owner'] != 'none':
                    prop.domain = [classes.get(element['owner'].strip())]
                classes[pA_name] = prop

            elif element['@type'] == 'item':
                # 处理 item 类型，创建一个新的类
                cls = types.new_class(element['@name'].strip(), (ElementCompositions,))
                classes[element['@name'].strip()] = cls

            elif element['@type'] == 'state':  # Class + ObjectProperty
                # 对于状态元素，首先创建一个顶级状态类
                state_cls = types.new_class(element['@name'].strip(), (Thing,))
                classes[element['@name'].strip()] = state_cls

                transition_class = list(set([transition['source'] for transition in element.get('transitions', [])] +
                                            [transition['target'] for transition in element.get('transitions', [])]))

                for i in transition_class:
                    if i not in classes:
                        tran_cls = types.new_class(i, (state_cls,))
                        classes[i] = tran_cls
                    else:
                        tran_cls = classes[i]

                for i in element.get('transitions', []):
                    sT_name = i['transit'].strip() + 'Transform'
                    prop = types.new_class(sT_name, (sT_prop,))
                    prop.domain = [classes.get(i['source'].strip())]
                    prop.range = [classes.get(i['target'].strip())]
                    classes[sT_name] = prop

            # DataProperty
            elif element['@type'] == 'attribute':
                attr_name = element['@name'].strip()
                owner = classes.get(element['owner'].strip())
                if owner is not None:
                    if element['datatype'] == 'Integer' or "Real":
                        type_name = int
                    elif element['datatype'] == 'Boolean' or "Bool":
                        type_name = bool
                    elif element['datatype'] == 'String':
                        type_name = str
                    elif element['datatype'] in ['Float', 'Double']:
                        type_name = float
                    elif element['datatype'] == 'DateTime':
                        type_name = datetime.datetime
                    elif element['datatype'] == 'Date':
                        type_name = datetime.date
                    elif element['datatype'] == 'Time':
                        type_name = datetime.time
                    else:
                        type_name = str  # 默认类型

                    # 创建数据属性
                    attr_prop = types.new_class(attr_name, (DataProperty,))
                    attr_prop.domain = [owner]
                    attr_prop.range = [type_name]
                    classes[attr_name] = attr_prop

            # ObjectiveProperty
            elif element['@type'] == 'exhibitState':
                eS_name = 'exhibit' + (element['@name'].strip())
                prop = types.new_class(eS_name, (eS_prop,))
                prop.domain = [classes.get(element['owner'].strip())]
                prop.range = [classes.get(element['@name'].strip())]
                classes[eS_name] = prop

            elif element['@type'] == 'itemComposition':
                iC_name = 'consist' + (element['@name'].strip())
                prop = types.new_class(iC_name, (cC_prop,))
                prop.domain = [classes.get(element['owner'].strip())]
                prop.range = [classes.get(element['parent'].strip())]
                classes[iC_name] = prop

            elif element['@type'] == 'action':
                aC_name = 'has' + (element['@name'].strip()) + 'EffectOn'
                prop = types.new_class(aC_name, (hE_prop,))

                for i in element.get('outparams', []):
                    for j in elements:
                        if j['@type'] == 'attribute' and i == j['@name']:
                            if j['owner'] not in ['', 'none']:
                                prop.range = [classes.get(j['owner'].strip())]

                for i in element.get('inparams', []):
                    for j in elements:
                        if j['@type'] == 'attribute' and i == j['@name']:
                            if j['owner'] not in ['', 'none']:
                                prop.domain = [classes.get(j['owner'].strip())]

                for i in elements:
                    if i['@type'] == 'actionSub' and i.get('parent') == element['@name']:
                        if 'owner' in i and i['owner'] not in ['', 'none']:
                            prop.domain = [classes.get(i['owner'].strip())]

                classes[aC_name] = prop

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存本体到指定的位置
    onto.save(file=output_path, format="rdfxml")
    print(f"本体已保存到: {output_path}")


def Scenario_owl_creator(output_path):
    """
    创建Scenario本体并保存到指定的位置。

    :param output_path: 输出的Scenario.owl文件的完整路径。
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

        # class aidResource(DataProperty):
        #     namespace = onto
        #     domain = [EconomicFactors]
        #     range = [str]
        #
        # class towResource(DataProperty):
        #     namespace = onto
        #     domain = [EconomicFactors]
        #     range = [str]
        #
        # class firefightingResource(DataProperty):
        #     namespace = onto
        #     domain = [EconomicFactors]
        #     range = [str]
        #
        # class rescueResource(DataProperty):
        #     namespace = onto
        #     domain = [EconomicFactors]
        #     range = [str]

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

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    onto.save(file=output_path, format="rdfxml")
    print(f"Scenario本体已保存到: {output_path}")


def Emergency_owl_creator(output_path):
    """
    创建Emergency本体并保存到指定的位置。

    :param output_path: 输出的Emergency.owl文件的完整路径。
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

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    onto.save(file=output_path, format="rdfxml")
    print(f"Emergency本体已保存到: {output_path}")


'''整理为excel'''


def owl_excel_creator(input_owl_path, output_excel_path):
    """
    将OWL文件中的属性信息整理为Excel文件。

    :param input_owl_path: 输入的OWL文件的完整路径（包含文件名和扩展名）。
    :param output_excel_path: 输出的Excel文件的完整路径。
    """
    # 加载OWL文件
    onto = get_ontology(input_owl_path).load()

    # 创建一个新的Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = os.path.splitext(os.path.basename(output_excel_path))[0] + "_Prop"

    # 初始化一个空列表来存储属性信息的字典
    data_properties_list = []
    object_properties_list = []

    # 获取数据属性信息并整理为字典格式加入列表
    for dp in onto.data_properties():
        dp_dict = {
            "label": "DataProperty",
            "name": dp.name,
            "domain": dp.domain[0].name if dp.domain else "",
            "range": str(dp.range[0]) if dp.range else ""
        }
        data_properties_list.append(dp_dict)

    # 获取对象属性信息并整理为字典格式加入列表
    for op in onto.object_properties():
        op_dict = {
            "label": "ObjectProperty",
            "name": op.label[0] if op.label else op.name,
            "domain": op.domain[0].name if op.domain else "",
            "range": op.range[0].name if op.range else ""
        }
        object_properties_list.append(op_dict)

    # 写入表头
    ws.append(["label", "name", "domain", "range"])

    # 遍历属性信息列表，将信息写入Excel文件
    for prop in data_properties_list:
        ws.append([prop["label"], prop["name"], prop["domain"], prop["range"]])

    for prop in object_properties_list:
        ws.append([prop["label"], prop["name"], prop["domain"], prop["range"]])

    # 保存Excel文件
    wb.save(output_excel_path)
    print(f"Excel文件已保存为: {output_excel_path}")



if __name__ == '__main__':
    # 定义输入和输出目录
    input_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/result')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/sysml2/owl')

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 清理旧的 owl 文件
    for f in os.listdir(output_dir):
        if f.endswith('.owl'):
            os.remove(os.path.join(output_dir, f))

    # 获取所有JSON文件
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

    # 创建ScenarioElement本体文件
    scenario_element_owl = os.path.join(output_dir, "ScenarioElement.owl")
    for input_file in json_files:
        input_path = os.path.join(input_dir, input_file)
        create_ontology(input_path, scenario_element_owl)

    # 加载ScenarioElement.owl文件并进行后续操作
    onto = get_ontology(scenario_element_owl).load()
    # 删除Action和Resource类及其子类
    with onto:
        if 'Action' in onto.classes():
            destroy_entity(onto.Action)
            print("已删除类 Action 及其子类")
        if 'Resource' in onto.classes():
            destroy_entity(onto.Resource)
            print("已删除类 Resource 及其子类")

    # 保存修改后的ScenarioElement.owl文件
    onto.save(file=scenario_element_owl, format="rdfxml")
    print(f"修改后的ScenarioElement.owl文件已保存到: {scenario_element_owl}")

    # 创建对应的Excel文件
    owl_excel_creator(scenario_element_owl, os.path.join(output_dir, "ScenarioElement_Prop.xlsx"))

    # 创建Scenario本体
    scenario_output_path = os.path.join(output_dir, "Scenario.owl")
    Scenario_owl_creator(scenario_output_path)
    owl_excel_creator(scenario_output_path, os.path.join(output_dir, "Scenario_Prop.xlsx"))

    # 创建Emergency本体
    emergency_output_path = os.path.join(output_dir, "Emergency.owl")
    Emergency_owl_creator(emergency_output_path)
    owl_excel_creator(emergency_output_path, os.path.join(output_dir, "Emergency_Prop.xlsx"))
