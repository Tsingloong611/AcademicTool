# -*- coding: utf-8 -*-
# @Time    : 2025/2/20 19:25
# @FileName: test.py
# @Software: PyCharm
import pandas as pd
import itertools


def generate_recovery_capacity_data():
    # 所有可能的状态
    states = {
        "disposalDuration": ["0-15min", "15-30min", "30-60min", "60min+"],
        "responseDuration": ["0-15min", "15-30min", "30-60min", "60min+"],
        "RescueResource": ["Not_Used", "Used"],
        "FirefightingResource": ["Not_Used", "Used"],
        "TowResource": ["Not_Used", "Used"],
        "AidResource": ["Not_Used", "Used"]
    }

    # 生成所有组合
    combinations = list(itertools.product(
        range(len(states["disposalDuration"])),
        range(len(states["responseDuration"])),
        range(2),  # RescueResource
        range(2),  # FirefightingResource
        range(2),  # TowResource
        range(2)  # AidResource
    ))

    # 准备Excel数据
    data = []
    for combo in combinations:
        # 对每个组合生成两行数据，状态值分别为0和1
        for state in [0, 1]:
            data.append({
                'Node': 'RecoveryCapacity',
                'Condition': str(list(combo)),
                'State': state,
                'E1': 'M'  # 所有评估值设为M
            })

    return data


def create_excel_file():
    # 生成RecoveryCapacity数据
    recovery_data = generate_recovery_capacity_data()


    # 合并所有数据
    all_data =  recovery_data

    # 创建DataFrame
    df = pd.DataFrame(all_data)

    # 写入Excel文件
    output_file = 'assessment_data.xlsx'
    df.to_excel(output_file, index=False)
    print(f"数据已写入到 {output_file}")

    # 返回生成的组合数量信息
    return {
        'total_combinations': len(recovery_data),
        'recovery_states': len(recovery_data) // 2,  # 每个组合有两个状态
        'file_path': output_file
    }


# 执行生成和写入
result = create_excel_file()

print(f"""
生成完成:
- 总行数: {result['total_combinations']}
- 恢复能力组合数: {result['recovery_states']}
- 文件保存在: {result['file_path']}
""")