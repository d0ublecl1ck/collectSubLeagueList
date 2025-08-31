# -*- coding: utf-8 -*-
import re
import pandas as pd

def update_year_in_csv_file(input_file, output_file, target_year):
    """更新CSV文件中的年份到目标年份"""
    # 尝试多种编码读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'cp936', 'iso-8859-1']
    df = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, na_filter=False, encoding=encoding)
            used_encoding = encoding
            print(f"成功使用 {encoding} 编码读取CSV文件")
            break
        except UnicodeDecodeError as e:
            print(f"尝试 {encoding} 编码失败: {e}")
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码读取失败: {e}")
            continue
    
    if df is None:
        raise Exception(f"无法读取CSV文件，已尝试编码: {', '.join(encodings)}")
    
    
    # 计算当前年份（假设从2024开始）
    current_year = 2024
    next_year = current_year + 1
    
    # 计算目标年份
    target_next_year = target_year + 1
    
    # 更新year列中的年份
    # 先替换跨年格式
    df['year'] = df['year'].astype(str).str.replace(
        f'{current_year}-{next_year}', f'{target_year}-{target_next_year}', regex=False
    )
    df['year'] = df['year'].str.replace(
        f'{current_year-1}-{current_year}', f'{target_year-1}-{target_year}', regex=False
    )
    # 再替换单年格式（使用正则表达式确保完整匹配）
    df['year'] = df['year'].str.replace(
        rf'\b{current_year}\b', str(target_year), regex=True
    )
    
    # 更新link和link_second列中的年份（如果存在）
    for col in ['link', 'link_second']:
        if col in df.columns:
            # 只处理非空值，避免将空字符串转换为'nan'
            mask = df[col] != ''
            if mask.any():
                # 先替换跨年格式
                df.loc[mask, col] = df.loc[mask, col].str.replace(
                    f'{current_year}-{next_year}', f'{target_year}-{target_next_year}', regex=False
                )
                df.loc[mask, col] = df.loc[mask, col].str.replace(
                    f'{current_year-1}-{current_year}', f'{target_year-1}-{target_year}', regex=False
                )
                # 再替换单年格式
                df.loc[mask, col] = df.loc[mask, col].str.replace(
                    rf'\b{current_year}\b', str(target_year), regex=True
                )
    
    # 保存为CSV文件
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"已生成 {output_file}，年份已更新为 {target_year}")

if __name__ == "__main__":
    # 用户选择年份
    target_year = int(input("请输入目标年份: "))
    output_file = f"inp_{str(target_year)[-2:]}.csv"
    
    update_year_in_csv_file('inp.csv', output_file, target_year)