# -*- coding: utf-8 -*-
import re

def update_year_in_file(input_file, output_file, target_year):
    """更新文件中的年份到目标年份"""
    # 读取原文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 计算当前年份（假设从2024开始）
    current_year = 2024
    next_year = current_year + 1
    
    # 计算目标年份
    target_next_year = target_year + 1
    
    # 年份替换规则
    # 先替换跨年格式
    content = re.sub(rf'\b{current_year}-{next_year}\b', f'{target_year}-{target_next_year}', content)
    content = re.sub(rf'\b{current_year-1}-{current_year}\b', f'{target_year-1}-{target_year}', content)
    # 再替换单年格式
    content = re.sub(rf'\b{current_year}\b', str(target_year), content)
    
    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已生成 {output_file}，年份已更新为 {target_year}")

if __name__ == "__main__":
    # 用户选择年份
    target_year = int(input("请输入目标年份: "))
    output_file = f"inp_{str(target_year)[-2:]}.txt"
    
    update_year_in_file('inp.txt', output_file, target_year)