import types

from owlready2 import *
import json
from openpyxl import Workbook

'''本体生成'''
def create_ontology(file_path,filename):
    # 加载json文件
    with open(file_path, "r") as file:
        data = json.load(file)

    desired_order = ['part', 'partSub', 'partAssociate', 'item', 'state']

    sorted_data = sorted(data, key=lambda x: desired_order.index(x['@type']) if x['@type'] in desired_order else len(
        desired_order))

    # 创建一个新的本体
    onto = get_ontology("http://example.org/scenario_3.owl")

    elements = sorted_data

    # 用于存储创建的类，以便后续引用
    classes = {}

    with onto:
        # 创建ScenarioElement class
        # subclass为AffectedElement、HazardElement、EnvironmentElement、ResponsePlanElement
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

        # 创建ElementState class
        # subclass为AffectedStates、HazardStates、ResponseStates
        class ElementState(Thing):
            pass

        class AffectedStates(ElementState):
            pass

        class HazardStates(ElementState):
            pass

        #
        class ResponsePlanElement(Thing):
            pass

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

                print(f"DEBUG cls : {cls}")

            elif element['@type'] == 'partSub':

                # 创建一个子类
                parent_cls = classes.get(element['parent'].strip())
                print(f"DEBUG parent_cls : {parent_cls}")
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
                # 处理 partAssociate 类型，创建一个新的类
                cls = types.new_class(element['@name'].strip(), (ElementCompositions,))
                classes[element['@name'].strip()] = cls

            elif element['@type'] == 'state':  # Class + ObjectProperty
                # 对于状态元素，首先创建一个顶级状态类
                state_cls = types.new_class(element['@name'].strip(), (Thing,))
                classes[element['@name'].strip()] = state_cls

                transition_class = list(set([transition['source'] for transition in element['transitions']] +
                                            [transition['target'] for transition in element['transitions']]))

                for i in transition_class:
                    if i not in classes:
                        tran_cls = types.new_class(i, (state_cls,))
                        classes[i] = tran_cls
                    else:
                        tran_cls = classes[i]

                for i in element['transitions']:
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
                    if element['datatype'] == 'Integer':
                        type_name = int
                    elif element['datatype'] == 'Boolean':
                        type_name = bool
                    elif element['datatype'] == 'String':
                        type_name = str
                    elif element['datatype'] == 'Float' or 'Double':
                        type_name = float
                    elif type_name == 'DateTime':
                        type_name = datetime.datetime
                    elif type_name == 'Date':
                        type_name = datetime.date
                    elif type_name == 'Time':
                        type_name = datetime.time

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

            elif element['@type'] == 'partAssociate':
                pA_name = 'associate' + (element['@name'].strip())
                prop = types.new_class(pA_name, (aW_prop,))
                prop.domain = [classes.get(element['owner'].strip())]
                prop.range = [classes.get(element['@name'].strip())]
                classes[pA_name] = prop

            elif element['@type'] == 'itemComposition':
                iC_name = 'consist' + (element['@name'].strip())
                prop = types.new_class(iC_name, (cC_prop,))
                prop.domain = [classes.get(element['owner'].strip())]
                prop.range = [classes.get(element['parent'].strip())]
                classes[iC_name] = prop

            elif element['@type'] == 'action':
                aC_name = 'has' + (element['@name'].strip()) + 'EffectOn'
                prop = types.new_class(aC_name, (hE_prop,))

                for i in element['outparams']:
                    for j in elements:
                        if j['@type'] == 'attribute':
                            if i == j['@name']:
                                print(f"DEBUG 2031934 : {j['owner']}")
                                if j['owner'] != 'none' and j['owner'] != '':
                                    prop.range = [classes.get(j['owner'].strip())]
                                    classes[aC_name] = prop

                for i in element['inparams']:
                    for j in elements:
                        if j['@type'] == 'attribute':
                            if i == j['@name']:
                                print(f"DEBUG 2031934 : {j['owner']}")
                                if j['owner'] != 'none' and j['owner'] != '':
                                    prop.domain = [classes.get(j['owner'].strip())]
                                    classes[aC_name] = prop

                for i in elements:
                    # print(i)
                    if i['@type'] == 'actionSub':
                        if 'parent' in i:
                            if i['parent'] is not None:
                                if i['parent'] == element['@name']:
                                    prop.domain = [classes.get(i['owner'].strip())]
                                    classes[aC_name] = prop




    #filename = "Integrated_Scenario_3.owl" #保存的文件名
    onto.save(file=filename+".owl", format="rdfxml")
    #onto.save(file="Integrated_Scenario_1.owl", format="rdfxml")

    # onto.save(file="Integrated_Scenario.owl", format="rdfxml")

def Scenario_owl_creator():
    onto = get_ontology("http://example.org/scenario_3.owl")
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

        class actionType(DataProperty):
            namespace = onto
            domain = [EconomicFactors]
            range = [str]

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

    onto.save(file="Scenario.owl", format="rdfxml")

def Emergency_owl_creator():
    onto = get_ontology("http://example.org/scenario_3.owl")
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
    onto.save(file="Emergency.owl", format="rdfxml")

'''整理为excel'''
def owl_excel_creator(filename):
    # 加载OWL文件
    onto = get_ontology(filename + ".owl").load()

    # 创建一个新的Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = filename + "_Prop"

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
    excel_file = filename + "_Prop.xlsx"
    wb.save(excel_file)
    print("Excel文件已保存为:", excel_file)

# 文件路径
file_paths = ["AffectedElement.json", "EnvironmentElement.json", "HazardElement.json", "ResponsePlanElement.json"]

for file_path in file_paths:
    #filename = file_path.split(".")[0]
    filename = "ScenarioElement"
    create_ontology(file_path,filename)

# 加载OWL文件
onto = get_ontology(filename + ".owl").load()
# 删除Action和Resource类及其子类
if onto.Action is not None:
    with onto:
        destroy_entity(onto.Action)

if onto.Resource is not None:
    with onto:
        destroy_entity(onto.Resource)

# 保存修改后的OWL文件
onto.save(file=filename + ".owl", format="rdfxml")

owl_excel_creator(filename)

Scenario_owl_creator()
owl_excel_creator("Scenario")
Emergency_owl_creator()
owl_excel_creator("Emergency")

