# -*- coding: utf-8 -*-
"""
批量导入页面 - 提供 Task 模型的批量数据导入界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from datetime import datetime

from .base_page import BasePage
from models import Task


class BatchImportPage(BasePage):
    """批量导入页面 - 任务批量导入功能"""
    
    def setup_ui(self):
        """设置批量导入页面的用户界面"""
        # 页面标题
        title_label = ttk.Label(
            self.frame, 
            text="批量导入", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 样例下载区域
        self.setup_sample_download_area()
        
        # 文件选择区域
        self.setup_file_selection_area()
        
        # 数据预览区域
        self.setup_preview_area()
        
        # 导入执行区域
        self.setup_import_area()
        
        # 初始化变量
        self.current_data = None
        self.validation_results = []
    
    def setup_sample_download_area(self):
        """设置样例下载区域"""
        sample_frame = ttk.LabelFrame(self.frame, text="样例文件下载", padding=15)
        sample_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 说明文本
        desc_label = ttk.Label(
            sample_frame, 
            text="下载样例文件来了解正确的导入格式：",
            font=('Arial', 10)
        )
        desc_label.pack(anchor='w', pady=(0, 10))
        
        # 按钮区域
        btn_frame = ttk.Frame(sample_frame)
        btn_frame.pack(fill=tk.X)
        
        # Excel样例下载按钮
        excel_btn = ttk.Button(
            btn_frame,
            text="下载 Excel 样例",
            command=self.download_excel_sample,
            width=20
        )
        excel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # TXT样例下载按钮
        txt_csv_btn = ttk.Button(
            btn_frame,
            text="下载 CSV 样例",
            command=self.download_csv_sample,
            width=20
        )
        txt_csv_btn.pack(side=tk.LEFT, padx=10)
        
        # TAB分隔符样例下载按钮
        txt_tab_btn = ttk.Button(
            btn_frame,
            text="下载 TAB 样例",
            command=self.download_tab_sample,
            width=20
        )
        txt_tab_btn.pack(side=tk.LEFT, padx=10)
        
        # 格式说明
        format_info = ttk.Label(
            sample_frame,
            text="必填字段：赛事级别*, 赛事名称*, 国家/地区*, 联赛名称*, 赛事类型*, 赛事年份*",
            font=('Arial', 9),
            foreground='blue'
        )
        format_info.pack(anchor='w', pady=(10, 0))
    
    def setup_file_selection_area(self):
        """设置文件选择区域"""
        file_frame = ttk.LabelFrame(self.frame, text="选择导入文件", padding=15)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 文件路径显示
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="文件路径:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            path_frame, 
            textvariable=self.file_path_var,
            state='readonly',
            width=50
        )
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 浏览按钮
        browse_btn = ttk.Button(
            path_frame,
            text="浏览文件",
            command=self.browse_file,
            width=12
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # 解析按钮
        parse_btn = ttk.Button(
            file_frame,
            text="解析文件",
            command=self.parse_file,
            width=15
        )
        parse_btn.pack(pady=(0, 0))
    
    def setup_preview_area(self):
        """设置数据预览区域"""
        preview_frame = ttk.LabelFrame(self.frame, text="数据预览", padding=15)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建Treeview表格
        columns = ['level', 'event', 'country', 'league', 'type', 'year', 'group', 'link', 'link_second']
        column_names = ['级别', '赛事名称', '国家/地区', '联赛名称', '类型', '年份', '分组', '主链接', '备用链接']
        
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        # 设置列标题和宽度
        for col, name in zip(columns, column_names):
            self.preview_tree.heading(col, text=name)
            self.preview_tree.column(col, width=80, minwidth=50)
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        
        self.preview_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.preview_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # 验证结果显示
        self.validation_text = tk.Text(preview_frame, height=4, state='disabled')
        self.validation_text.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))
    
    def setup_import_area(self):
        """设置导入执行区域"""
        import_frame = ttk.Frame(self.frame)
        import_frame.pack(fill=tk.X, pady=10)
        
        # 导入按钮
        self.import_btn = ttk.Button(
            import_frame,
            text="执行批量导入",
            command=self.execute_import,
            width=15,
            state='disabled'
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态显示
        self.status_label = ttk.Label(import_frame, text="请先选择并解析文件")
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def download_excel_sample(self):
        """下载Excel样例文件"""
        try:
            # 创建样例数据
            sample_data = {
                'level': [1, 2],
                'event': ['欧洲冠军联赛', '英格兰足球超级联赛'],
                'country': ['欧洲', '英格兰'],
                'league': ['欧冠', '英超'],
                'type': ['常规', '常规'],
                'year': ['2024', '2024'],
                'group': ['A组', '默认组'],
                'link': ['https://example.com/ucl', 'https://example.com/epl'],
                'link_second': ['', '']
            }
            
            df = pd.DataFrame(sample_data)
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="保存Excel样例文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx")]
            )
            
            if file_path:
                df.to_excel(file_path, index=False)
                self.show_message("成功", f"Excel样例文件已保存到：{file_path}", "info")
                self.log_action("下载样例", f"Excel样例: {file_path}")
                
        except Exception as e:
            self.logger.error(f"下载Excel样例失败: {e}")
            self.show_message("错误", f"下载失败: {str(e)}", "error")
    
    def download_csv_sample(self):
        """下载CSV样例文件"""
        try:
            # CSV样例内容（逗号分隔）
            sample_content = """level,event,country,league,type,year,group,link,link_second
1,欧洲冠军联赛,欧洲,欧冠,常规,2024,A组,https://example.com/ucl,
2,英格兰足球超级联赛,英格兰,英超,常规,2024,默认组,https://example.com/epl,"""
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="保存CSV样例文件",
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sample_content)
                self.show_message("成功", f"CSV样例文件已保存到：{file_path}", "info")
                self.log_action("下载样例", f"CSV样例: {file_path}")
                
        except Exception as e:
            self.logger.error(f"下载CSV样例失败: {e}")
            self.show_message("错误", f"下载失败: {str(e)}", "error")
    
    def download_tab_sample(self):
        """下载TAB分隔符样例文件"""
        try:
            # TAB样例内容（制表符分隔）
            sample_content = """level\tevent\tcountry\tleague\ttype\tyear\tgroup\tlink\tlink_second
1\t欧洲冠军联赛\t欧洲\t欧冠\t常规\t2024\tA组\thttps://example.com/ucl\t
2\t英格兰足球超级联赛\t英格兰\t英超\t常规\t2024\t默认组\thttps://example.com/epl\t"""
            
            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="保存TAB分隔符样例文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("制表符文件", "*.tsv")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sample_content)
                self.show_message("成功", f"TAB样例文件已保存到：{file_path}", "info")
                self.log_action("下载样例", f"TAB样例: {file_path}")
                
        except Exception as e:
            self.logger.error(f"下载TAB样例失败: {e}")
            self.show_message("错误", f"下载失败: {str(e)}", "error")
    
    def browse_file(self):
        """浏览选择导入文件"""
        file_path = filedialog.askopenfilename(
            title="选择导入文件",
            filetypes=[
                ("支持的文件", "*.xlsx;*.xls;*.txt;*.csv"),
                ("Excel文件", "*.xlsx;*.xls"),
                ("文本文件", "*.txt;*.csv"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.log_action("选择文件", f"文件路径: {file_path}")
    
    def parse_file(self):
        """解析导入文件"""
        file_path = self.file_path_var.get()
        if not file_path:
            self.show_message("提示", "请先选择要导入的文件", "warning")
            return
        
        if not os.path.exists(file_path):
            self.show_message("错误", "文件不存在", "error")
            return
        
        try:
            # 根据文件扩展名选择解析方式
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                separator_used = "Excel格式"
            elif file_ext in ['.txt', '.csv']:
                # 智能检测分隔符
                df, separator_used = self.detect_separator_and_parse(file_path)
            else:
                self.show_message("错误", "不支持的文件格式", "error")
                return
            
            # 标准化列名
            df = self.normalize_column_names(df)
            
            # 验证数据
            self.current_data = df
            validation_results = self.validate_data(df)
            
            # 显示预览
            self.display_preview(df)
            self.display_validation_results(validation_results)
            
            # 启用导入按钮
            if all(result['valid'] for result in validation_results):
                self.import_btn.config(state='normal')
                self.status_label.config(text=f"数据验证通过，共 {len(df)} 条记录 ({separator_used})")
            else:
                self.import_btn.config(state='disabled')
                self.status_label.config(text="数据验证失败，请检查错误信息")
            
            self.log_action("解析文件", f"成功解析 {len(df)} 条记录，使用{separator_used}")
            
        except Exception as e:
            self.logger.error(f"解析文件失败: {e}")
            self.show_message("错误", f"解析失败: {str(e)}", "error")
            self.status_label.config(text="文件解析失败")
    
    def validate_data(self, df):
        """验证导入数据"""
        results = []
        required_fields = ['level', 'event', 'country', 'league', 'type', 'year']
        
        # 检查必需列是否存在（已经过列名标准化处理）
        missing_columns = [col for col in required_fields if col not in df.columns]
        if missing_columns:
            results.append({
                'valid': False,
                'message': f"缺少必需列: {', '.join(missing_columns)}"
            })
            return results
        
        # 逐行验证数据
        for index, row in df.iterrows():
            row_errors = []
            
            # 检查必填字段
            for field in required_fields:
                if pd.isna(row[field]) or str(row[field]).strip() == '':
                    row_errors.append(f"{field}为空")
            
            # 验证级别为数字
            try:
                if not pd.isna(row['level']):
                    int(row['level'])
            except (ValueError, TypeError):
                row_errors.append("level必须为数字")
            
            # 验证类型是否在允许范围内
            valid_types = ["常规", "联二合并", "春秋合并", "东西拆分"]
            if not pd.isna(row['type']) and str(row['type']) not in valid_types:
                row_errors.append(f"type必须为: {', '.join(valid_types)}")
            
            # 记录验证结果
            if row_errors:
                results.append({
                    'valid': False,
                    'row': index + 1,
                    'message': f"第{index + 1}行错误: {'; '.join(row_errors)}"
                })
            else:
                results.append({
                    'valid': True,
                    'row': index + 1,
                    'message': f"第{index + 1}行验证通过"
                })
        
        return results
    
    def display_preview(self, df):
        """显示数据预览"""
        # 清空现有数据
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 插入数据行（最多显示前50行）
        display_rows = min(50, len(df))
        for index in range(display_rows):
            row = df.iloc[index]
            values = []
            for col in self.preview_tree['columns']:
                if col in df.columns:
                    val = row[col]
                    if pd.isna(val):
                        values.append('')
                    else:
                        values.append(str(val))
                else:
                    values.append('')
            
            self.preview_tree.insert('', 'end', values=values)
        
        if len(df) > 50:
            # 添加提示信息
            note_values = ['...', f'共{len(df)}条记录', '仅显示前50条', '...', '...', '...', '...', '...', '...']
            self.preview_tree.insert('', 'end', values=note_values)
    
    def display_validation_results(self, results):
        """显示验证结果"""
        self.validation_text.config(state='normal')
        self.validation_text.delete(1.0, tk.END)
        
        # 统计
        total_rows = len(results)
        valid_rows = len([r for r in results if r['valid']])
        invalid_rows = total_rows - valid_rows
        
        # 显示统计信息
        summary = f"验证结果: 总计 {total_rows} 行，通过 {valid_rows} 行，失败 {invalid_rows} 行\n\n"
        self.validation_text.insert(tk.END, summary)
        
        # 显示错误信息（仅显示前20个错误）
        error_results = [r for r in results if not r['valid']][:20]
        for result in error_results:
            self.validation_text.insert(tk.END, result['message'] + '\n')
        
        if len(error_results) < invalid_rows:
            self.validation_text.insert(tk.END, f"... 还有 {invalid_rows - len(error_results)} 个错误未显示\n")
        
        self.validation_text.config(state='disabled')
        self.validation_results = results
    
    def execute_import(self):
        """执行批量导入"""
        if self.current_data is None:
            self.show_message("提示", "请先选择并解析文件", "warning")
            return
        
        # 再次验证
        if not all(result['valid'] for result in self.validation_results):
            self.show_message("错误", "数据验证失败，无法导入", "error")
            return
        
        try:
            success_count = 0
            error_count = 0
            duplicate_count = 0
            
            with self.get_db_session() as session:
                for index, row in self.current_data.iterrows():
                    try:
                        # 处理 group 字段默认值
                        group = row.get('group', '默认组')
                        if pd.isna(group) or str(group).strip() == '':
                            group = '默认组'
                        
                        # 创建任务对象
                        task = Task(
                            level=int(row['level']),
                            event=str(row['event']),
                            country=str(row['country']),
                            league=str(row['league']),
                            type=str(row['type']),
                            year=str(row['year']),
                            group=str(group),
                            link=str(row.get('link', '')) if not pd.isna(row.get('link')) else None,
                            link_second=str(row.get('link_second', '')) if not pd.isna(row.get('link_second')) else None
                        )
                        
                        session.add(task)
                        session.flush()  # 刷新以获取可能的约束冲突
                        success_count += 1
                        
                    except Exception as e:
                        error_msg = str(e)
                        if 'UNIQUE constraint failed' in error_msg:
                            duplicate_count += 1
                            self.logger.warning(f"第{index + 1}行重复数据跳过: {row['league']}-{row['year']}-{group}")
                        else:
                            error_count += 1
                            self.logger.error(f"第{index + 1}行导入失败: {e}")
                
                # 提交事务
                session.commit()
            
            # 显示导入结果
            result_msg = f"导入完成！成功: {success_count}, 重复跳过: {duplicate_count}, 错误: {error_count}"
            self.show_message("导入结果", result_msg, "info" if error_count == 0 else "warning")
            self.status_label.config(text=result_msg)
            
            # 记录日志
            self.log_action("批量导入", f"成功{success_count}条，重复{duplicate_count}条，错误{error_count}条")
            
            # 清空数据
            if success_count > 0:
                self.clear_import_data()
            
        except Exception as e:
            self.logger.error(f"批量导入失败: {e}")
            self.show_message("错误", f"导入失败: {str(e)}", "error")
    
    def clear_import_data(self):
        """清空导入数据"""
        self.file_path_var.set("")
        self.current_data = None
        self.validation_results = []
        
        # 清空预览
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 清空验证结果
        self.validation_text.config(state='normal')
        self.validation_text.delete(1.0, tk.END)
        self.validation_text.config(state='disabled')
        
        # 禁用导入按钮
        self.import_btn.config(state='disabled')
        self.status_label.config(text="请先选择并解析文件")
        
        self.log_action("清空导入数据")
    
    def detect_separator_and_parse(self, file_path):
        """智能检测分隔符并解析文件"""
        separators = [
            ('\t', 'TAB分隔符'),
            (',', '逗号分隔符'),
            (';', '分号分隔符')
        ]
        
        for sep, sep_name in separators:
            try:
                # 尝试解析文件
                df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                
                # 检查是否成功解析（至少要有必需的列）
                required_columns = ['level', 'event', 'country', 'league', 'type', 'year']
                
                # 将列名转换为小写进行比较（容错处理）
                df_columns_lower = [col.lower().strip() for col in df.columns]
                
                # 检查必需列是否存在
                missing_required = []
                for req_col in required_columns:
                    if req_col.lower() not in df_columns_lower:
                        missing_required.append(req_col)
                
                # 如果缺少必需列太多，尝试下一个分隔符
                if len(missing_required) > 2:  # 允许最多缺少2个必需列
                    continue
                    
                # 检查数据行数是否合理（至少1行数据）
                if len(df) < 1:
                    continue
                    
                # 成功解析，返回结果
                self.logger.info(f"检测到文件格式：{sep_name}，列数：{len(df.columns)}，行数：{len(df)}")
                return df, sep_name
                
            except Exception as e:
                # 当前分隔符解析失败，尝试下一个
                self.logger.debug(f"使用{sep_name}解析失败：{e}")
                continue
        
        # 所有分隔符都失败，抛出异常
        raise ValueError("无法检测文件格式，请检查文件内容是否符合要求")
    
    def normalize_column_names(self, df):
        """标准化列名，支持多种列名变体"""
        column_mapping = {
            # 标准列名：可能的变体列名
            'level': ['level', '级别', '赛事级别', 'Level'],
            'event': ['event', '赛事名称', '赛事', 'Event'],
            'country': ['country', '国家', '地区', '国家/地区', 'Country'],
            'league': ['league', '联赛', '联赛名称', 'League'],
            'type': ['type', '类型', '赛事类型', 'Type'],
            'year': ['year', '年份', '赛事年份', 'Year'],
            'group': ['group', '分组', '组别', '分组信息', 'Group'],
            'link': ['link', '链接', '主链接', '主要链接', 'Link'],
            'link_second': ['link_second', '备用链接', '第二链接', '次要链接', 'Link_Second', 'link2']
        }
        
        # 创建重命名字典
        rename_dict = {}
        df_columns_lower = {col: col.lower().strip() for col in df.columns}
        
        for standard_name, variants in column_mapping.items():
            for variant in variants:
                for original_col, lower_col in df_columns_lower.items():
                    if lower_col == variant.lower():
                        rename_dict[original_col] = standard_name
                        break
                if standard_name in rename_dict.values():
                    break
        
        # 重命名列
        df_renamed = df.rename(columns=rename_dict)
        
        # 记录列名映射
        if rename_dict:
            mapping_info = ", ".join([f"{old}->{new}" for old, new in rename_dict.items()])
            self.logger.info(f"列名映射：{mapping_info}")
        
        return df_renamed