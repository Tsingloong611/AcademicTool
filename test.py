import re
from typing import List, Dict


def parse_hazard_vehicle(code: str) -> List[Dict[str, List[Dict[str, str]]]]:
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


# 示例代码1：带类型的 perform action
hazard_vehicle_code_with_type = """
package ResponsePlanElement{
    part def ResponsePlanElement{
        ref part Action : ResponseAction;
        ref part Resource : ResponseResource;
    }
    part def ResponseAction{
        attribute implementationCondition : Boolean;
        attribute startTime : String;
        attribute endTime : String;
    }
    part def ResponseResource{
        attribute utilizedCondition : Boolean;
        attribute usageAmount : Real;
    }


    part aid : ResponseAction{
        attribute redefines implementationCondition = true;
        attribute redefines startTime = "2022:01:17:00:28";
        attribute redefines endTime = "2022:01:17:00:39";
        ref part ambulance;
        exhibit state aidStates;
    }
    part firefighting : ResponseAction{
        attribute redefines implementationCondition = true;
        attribute redefines startTime = "2022:01:17:00:34";
        attribute redefines endTime = "2022:01:17:00:47";
        ref part fireFightingTruck;
        exhibit state firefightingStates;
    }
    part tow : ResponseAction{
        attribute redefines implementationCondition = true;
        attribute redefines startTime = "2022:01:17:00:37";
        attribute redefines endTime = "2022:01:17:01:20";
        ref part tractor;
        exhibit state towStates;
    }
    part rescue : ResponseAction{
        attribute redefines implementationCondition = true;
        attribute redefines startTime = "2022:01:17:01:03";
        attribute redefines endTime = "2022:01:17:01:31";
        ref part emergencyVehicle;
        exhibit state rescueStates;
    }


    part ambulance : ResponseResource{
        attribute redefines utilizedCondition = true;
        attribute redefines usageAmount = 1.0;
        perform action aid : Action;
    }
    part fireFightingTruck : ResponseResource{
        attribute redefines utilizedCondition =true;
        attribute redefines usageAmount = 1.0;
        perform action firefighting : Action;
    }
    part tractor : ResponseResource{
        attribute redefines utilizedCondition = true;
        attribute redefines usageAmount = 1.0;
        perform action rescue : Action;
    }
    part emergencyVehicle : ResponseResource{
        attribute redefines utilizedCondition = true;
        attribute redefines usageAmount = 1.0;
        perform action rescue : Action;
    }

    action def Action{
        out implementationCondition;
        out startTime;
        out endTime;
    }

    state def aidStates{
        entry; then idleState;
        state idleState;
        accept Aid:Action
            then implementState;
        state implementState;
    }
    state def firefightingStates{
        entry; then idleState;
        state idleState;
        accept FireFighting:Action
            then implementState;
        state implementState;
    }
    state def towStates{
        entry; then idleState;
        state idleState;
        accept Tow:Action
            then implementState;
        state implementState;
    }
    state def rescueStates{
        entry; then idleState;
        state idleState;
        accept Rescue:Action
            then implementState;
        state implementState;
    }
}
"""

# 示例代码2：不带类型的 perform action
hazard_vehicle_code_without_type = """
package HazardElement{
    part def HazardElement{}

    item def People{
         attribute Casualty : Boolean;
    }
    item def Cargo{
         attribute DetachedCondition : Boolean;
    }

    action def Collide{
        in CollideCondition = true;
        out DamageCondition = true;
        out Casualty = true;
    }
    action def Spill{
        out SpillCondition = true;
        out PullotedCondition = true;
        out DetachedCondition = true;
    }
    action def Explode{
        out ExplodeCondition = true;
    }
    state def HazardStates{
        entry; then DriveState;
        state DriveState;
        accept Collide
            then CollideState;
        state CollideState;
        accept Spill
            then SpillState;
        state SpillState;
    }
    part HazardVehicle : HazardElement{
        attribute position : String = "ND569";
        attribute drivingDirection : String = "forward";
        attribute vehicleType : String = "truck";
        attribute CollideCondition : Boolean = true;
        attribute SpillCondition : Boolean = true;
        attribute ExplodeCondition : Boolean = false;

        item passenger : People;
        item cargo : Cargo;
        ref part Road;

        perform action Collide;
        perform action Spill;
        exhibit state HazardStates;

    }

}
"""

# 选择要测试的代码样例
test_sample = hazard_vehicle_code_without_type  # 更换为 hazard_vehicle_code_without_type 以测试另一种情况

# 解析并打印结果
parsed_result = parse_hazard_vehicle(test_sample)
import pprint

print("\n最终解析结果：")
pprint.pprint(parsed_result)
