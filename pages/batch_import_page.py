# -*- coding: utf-8 -*-
"""
批量导入页面 - 提供 Task 模型的批量数据导入界面（重新设计布局）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from datetime import datetime

from .base_page import BasePage
from models import Task, Team, JsDataRaw, Standings


class BatchImportPage(BasePage):
    """批量导入页面 - 任务批量导入功能"""
    
    def setup_scrollable_container(self):
        """设置可滚动的容器"""
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(self.frame)
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # 创建可滚动的框架
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 布局Canvas和滚动条
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        self.scrollable_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)
    
    def on_frame_configure(self, event):
        """当内部框架大小改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """当Canvas大小改变时调整内部框架宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def setup_ui(self):
        """设置批量导入页面的用户界面"""
        # 创建可滚动的主容器
        self.setup_scrollable_container()
        
        # 页面标题
        title_label = ttk.Label(
            self.scrollable_frame, 
            text="批量导入", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 15))
        
        # 文件选择和控制区域（置顶）
        self.setup_file_and_import_area()
        
        # 数据预览区域
        self.setup_preview_area()
        
        # 样例下载区域（底部，紧凑）
        self.setup_sample_download_area()
        
        # 初始化变量
        self.current_data = None
        self.validation_results = []
        self.duplicate_results = []
    
    def setup_file_and_import_area(self):
        """设置文件选择和导入控制区域（合并顶部区域）"""
        # 主控制框架
        control_frame = ttk.LabelFrame(self.scrollable_frame, text="文件导入", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建左右分栏
        main_frame = ttk.Frame(control_frame)
        main_frame.pack(fill=tk.X)
        
        # 左侧：文件路径输入
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        # 文件选择行
        file_frame = ttk.Frame(left_frame)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(file_frame, text="文件路径:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            file_frame, 
            textvariable=self.file_path_var,
            state='readonly'
        )
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 状态显示行
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame, 
            text="请选择要导入的文件",
            font=('Arial', 10),
            foreground='blue'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 右侧：按钮列
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # 浏览按钮
        browse_btn = ttk.Button(
            button_frame,
            text="浏览文件",
            command=self.browse_file,
            width=15
        )
        browse_btn.pack(pady=(0, 8))
        
        # 解析按钮
        parse_btn = ttk.Button(
            button_frame,
            text="解析文件",
            command=self.parse_file,
            width=15
        )
        parse_btn.pack(pady=(0, 8))
        
        # 导入按钮（突出显示）
        self.import_btn = ttk.Button(
            button_frame,
            text="📥 执行批量导入",
            command=self.execute_import,
            width=15,
            state='disabled'
        )
        self.import_btn.pack()
    
    
    def setup_preview_area(self):
        """设置数据预览区域"""
        preview_frame = ttk.LabelFrame(self.scrollable_frame, text="数据预览", padding=15)
        preview_frame.pack(fill=tk.X, pady=(0, 15))
        
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
        
        # 验证结果显示（自动调整高度）
        self.validation_text = tk.Text(preview_frame, height=1, state='disabled', wrap=tk.WORD)
        
        # 添加验证结果文本框的滚动条
        validation_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.validation_text.yview)
        self.validation_text.configure(yscrollcommand=validation_scrollbar.set)
        
        self.validation_text.grid(row=2, column=0, sticky='ew', pady=(10, 0))
        validation_scrollbar.grid(row=2, column=1, sticky='ns', pady=(10, 0))
    
    def setup_sample_download_area(self):
        """设置样例下载区域（底部紧凑版）"""
        sample_frame = ttk.LabelFrame(self.scrollable_frame, text="导入格式说明", padding=10)
        sample_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 格式说明
        format_info = ttk.Label(
            sample_frame,
            text="必填字段：赛事级别*, 赛事名称*, 国家/地区*, 联赛名称*, 赛事类型*, 赛事年份* | 支持格式：Excel(.xlsx), CSV(.csv), TAB分隔(.txt)",
            font=('Arial', 9),
            foreground='#666666'
        )
        format_info.pack(anchor='w', pady=(0, 10))
        
        # 样例下载按钮行
        sample_btn_frame = ttk.Frame(sample_frame)
        sample_btn_frame.pack(fill=tk.X)
        
        ttk.Label(sample_btn_frame, text="样例下载:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 10))
        
        # Excel样例按钮
        excel_btn = ttk.Button(
            sample_btn_frame,
            text="Excel样例",
            command=self.download_excel_sample,
            width=12
        )
        excel_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # CSV样例按钮
        csv_btn = ttk.Button(
            sample_btn_frame,
            text="CSV样例",
            command=self.download_csv_sample,
            width=12
        )
        csv_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # TAB样例按钮
        tab_btn = ttk.Button(
            sample_btn_frame,
            text="TAB样例",
            command=self.download_tab_sample,
            width=12
        )
        tab_btn.pack(side=tk.LEFT)
    
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
            
            # 检测重复数据
            duplicate_results = self.detect_duplicates_in_file(df)
            self.duplicate_results = duplicate_results
            
            # 显示预览
            self.display_preview(df)
            self.display_validation_results(validation_results, duplicate_results)
            
            # 启用导入按钮
            if all(result['valid'] for result in validation_results):
                self.import_btn.config(state='normal')
                self.status_label.config(
                    text=f"✅ 数据验证通过，共 {len(df)} 条记录 ({separator_used})，可以导入",
                    foreground='green'
                )
            else:
                self.import_btn.config(state='disabled')
                self.status_label.config(
                    text="❌ 数据验证失败，请检查错误信息",
                    foreground='red'
                )
            
            self.log_action("解析文件", f"成功解析 {len(df)} 条记录，使用{separator_used}")
            
        except Exception as e:
            self.logger.error(f"解析文件失败: {e}")
            self.show_message("错误", f"解析失败: {str(e)}", "error")
            self.status_label.config(text="文件解析失败")

    # 保持原有的其他方法不变
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
    
    def display_validation_results(self, results, duplicate_results=None):
        """显示验证结果和重复检测结果"""
        self.validation_text.config(state='normal')
        self.validation_text.delete(1.0, tk.END)
        
        # 统计
        total_rows = len(results)
        valid_rows = len([r for r in results if r['valid']])
        invalid_rows = total_rows - valid_rows
        
        # 显示统计信息
        summary = f"验证结果: 总计 {total_rows} 行，通过 {valid_rows} 行，失败 {invalid_rows} 行\n"
        self.validation_text.insert(tk.END, summary)
        
        # 显示重复检测结果
        if duplicate_results:
            total_duplicate_rows = sum(dup['count'] for dup in duplicate_results)
            unique_combinations = len(duplicate_results)
            
            self.validation_text.insert(tk.END, f"\n⚠️ 发现文件内重复数据:\n")
            self.validation_text.insert(tk.END, f"重复组合: {unique_combinations} 组，影响 {total_duplicate_rows} 条记录\n\n")
            
            # 显示前10组重复详情
            displayed_count = 0
            for dup in duplicate_results[:10]:
                displayed_count += 1
                row_nums_str = ', '.join(map(str, dup['row_numbers']))
                self.validation_text.insert(tk.END, 
                    f"第{displayed_count}组: {dup['league']}-{dup['year']}-{dup['group']} (行号: {row_nums_str})\n")
            
            if len(duplicate_results) > 10:
                self.validation_text.insert(tk.END, f"... 还有 {len(duplicate_results) - 10} 组重复未显示\n")
            
            self.validation_text.insert(tk.END, "\n📝 导入时将保留每组的最后一条记录，前面的记录会被覆盖。\n\n")
        else:
            self.validation_text.insert(tk.END, "\n✅ 未发现文件内重复数据\n\n")
        
        # 显示错误信息
        if invalid_rows > 0:
            self.validation_text.insert(tk.END, "验证错误详情:\n")
            error_results = [r for r in results if not r['valid']]
            for result in error_results:
                self.validation_text.insert(tk.END, result['message'] + '\n')
            
            if len(error_results) < invalid_rows:
                self.validation_text.insert(tk.END, f"... 还有 {invalid_rows - len(error_results)} 个错误未显示\n")
        
        self.validation_text.config(state='disabled')
        self.validation_results = results
        
        # 自动调整文本框高度
        self.auto_resize_validation_text()
    
    def auto_resize_validation_text(self):
        """自动调整验证结果文本框的高度"""
        # 获取文本内容的行数
        content = self.validation_text.get(1.0, tk.END)
        line_count = content.count('\n')
        
        # 设置最小和最大高度
        min_height = 3
        max_height = 15
        
        # 根据内容调整高度，但限制在最小和最大值之间
        new_height = max(min_height, min(line_count + 1, max_height))
        
        # 更新文本框高度
        self.validation_text.config(height=new_height)
        
        # 更新滚动区域（如果内容需要滚动的话）
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def has_core_field_changes(self, existing_task, new_data):
        """检测是否有核心字段变更"""
        core_fields = ['level', 'event', 'country', 'league', 'type', 'year', 'group', 'link', 'link_second']
        changes = []
        
        for field in core_fields:
            # 获取新值
            if field == 'level':
                new_value = int(new_data['level'])
            elif field in ['link', 'link_second']:
                new_value = str(new_data.get(field, '')) if not pd.isna(new_data.get(field)) else None
                # 处理空字符串
                if new_value == '':
                    new_value = None
            else:
                new_value = str(new_data[field]) if not pd.isna(new_data[field]) else None
            
            # 获取现有值
            existing_value = getattr(existing_task, field)
            
            # 比较值
            if existing_value != new_value:
                changes.append(f"{field}: '{existing_value}' -> '{new_value}'")
        
        return len(changes) > 0, changes
    
    def clear_related_data(self, session, task_id):
        """清空指定任务的关联数据"""
        try:
            # 删除 teams 数据
            session.query(Team).filter_by(task_id=task_id).delete()
            # 删除 js_data_raw 数据
            session.query(JsDataRaw).filter_by(task_id=task_id).delete()
            # 删除 standings 数据
            session.query(Standings).filter_by(task_id=task_id).delete()
            
            self.logger.info(f"已清空任务 {task_id} 的关联数据")
        except Exception as e:
            self.logger.error(f"清空任务 {task_id} 关联数据失败: {e}")
            raise
    
    def update_task_fields(self, existing_task, new_data, group):
        """更新任务字段"""
        existing_task.level = int(new_data['level'])
        existing_task.event = str(new_data['event'])
        existing_task.country = str(new_data['country'])
        existing_task.league = str(new_data['league'])
        existing_task.type = str(new_data['type'])
        existing_task.year = str(new_data['year'])
        existing_task.group = str(group)
        
        # 处理 link 字段
        link_value = str(new_data.get('link', '')) if not pd.isna(new_data.get('link')) else None
        existing_task.link = link_value if link_value != '' else None
        
        # 处理 link_second 字段
        link_second_value = str(new_data.get('link_second', '')) if not pd.isna(new_data.get('link_second')) else None
        existing_task.link_second = link_second_value if link_second_value != '' else None
        
        # updated_at 会自动更新

    def execute_import(self):
        """执行批量导入（支持更新模式）"""
        if self.current_data is None:
            self.show_message("提示", "请先选择并解析文件", "warning")
            return
        
        # 再次验证
        if not all(result['valid'] for result in self.validation_results):
            self.show_message("错误", "数据验证失败，无法导入", "error")
            return
        
        try:
            insert_count = 0  # 新增记录数
            major_update_count = 0  # 重要更新数（清空关联数据）
            minor_update_count = 0  # 一般更新数（仅更新字段）
            error_count = 0
            
            # 计算文件内重复统计
            file_duplicate_count = 0
            if self.duplicate_results:
                file_duplicate_count = sum(dup['count'] for dup in self.duplicate_results) - len(self.duplicate_results)
                # 减去每组保留的最后一条，剩下的就是被覆盖的数量
            
            with self.get_db_session() as session:
                for index, row in self.current_data.iterrows():
                    try:
                        # 处理 group 字段默认值
                        group = row.get('group', '默认组')
                        if pd.isna(group) or str(group).strip() == '':
                            group = '默认组'
                        
                        # 查找现有记录
                        existing_task = session.query(Task).filter_by(
                            league=str(row['league']),
                            year=str(row['year']),
                            group=str(group)
                        ).first()
                        
                        if existing_task:
                            # 检查是否有核心字段变更
                            has_changes, change_details = self.has_core_field_changes(existing_task, row)
                            
                            if has_changes:
                                # 清空关联数据
                                self.clear_related_data(session, existing_task.id)
                                # 更新任务字段
                                self.update_task_fields(existing_task, row, group)
                                major_update_count += 1
                                self.logger.info(f"第{index + 1}行重要更新: {row['league']}-{row['year']}-{group}, 变更: {'; '.join(change_details)}")
                            else:
                                # 只是一般更新
                                self.update_task_fields(existing_task, row, group)
                                minor_update_count += 1
                                self.logger.debug(f"第{index + 1}行一般更新: {row['league']}-{row['year']}-{group}")
                        else:
                            # 创建新任务
                            new_task = Task(
                                level=int(row['level']),
                                event=str(row['event']),
                                country=str(row['country']),
                                league=str(row['league']),
                                type=str(row['type']),
                                year=str(row['year']),
                                group=str(group),
                                link=str(row.get('link', '')) if not pd.isna(row.get('link')) and str(row.get('link', '')) != '' else None,
                                link_second=str(row.get('link_second', '')) if not pd.isna(row.get('link_second')) and str(row.get('link_second', '')) != '' else None
                            )
                            session.add(new_task)
                            insert_count += 1
                            self.logger.info(f"第{index + 1}行新增: {row['league']}-{row['year']}-{group}")
                        
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"第{index + 1}行处理失败: {e}")
                
                # 提交事务
                session.commit()
            
            # 显示导入结果
            result_parts = [f"新增: {insert_count}条", f"重要更新: {major_update_count}条", f"一般更新: {minor_update_count}条"]
            if file_duplicate_count > 0:
                result_parts.append(f"文件内重复: {file_duplicate_count}条")
            if error_count > 0:
                result_parts.append(f"错误: {error_count}条")
            
            result_msg = "导入完成！" + ", ".join(result_parts)
            self.show_message("导入结果", result_msg, "info" if error_count == 0 else "warning")
            self.status_label.config(text=result_msg, foreground='green')
            
            # 记录日志
            log_parts = [f"新增{insert_count}条", f"重要更新{major_update_count}条", f"一般更新{minor_update_count}条"]
            if file_duplicate_count > 0:
                log_parts.append(f"文件内重复{file_duplicate_count}条")
            if error_count > 0:
                log_parts.append(f"错误{error_count}条")
            
            self.log_action("批量导入", "，".join(log_parts))
            
            # 清空数据
            if insert_count > 0 or major_update_count > 0 or minor_update_count > 0:
                self.clear_import_data()
            
        except Exception as e:
            self.logger.error(f"批量导入失败: {e}")
            self.show_message("错误", f"导入失败: {str(e)}", "error")
    
    def clear_import_data(self):
        """清空导入数据"""
        self.file_path_var.set("")
        self.current_data = None
        self.validation_results = []
        self.duplicate_results = []
        
        # 清空预览
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 清空验证结果
        self.validation_text.config(state='normal')
        self.validation_text.delete(1.0, tk.END)
        self.validation_text.config(state='disabled')
        
        # 禁用导入按钮
        self.import_btn.config(state='disabled')
        self.status_label.config(text="请选择要导入的文件", foreground='blue')
        
        self.log_action("清空导入数据")
    
    def detect_separator_and_parse(self, file_path):
        """智能检测分隔符并解析文件"""
        # 读取文件前两行来判断格式
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError("文件内容不足，至少需要标题行和一行数据")
        
        header_line = lines[0].strip()
        data_line = lines[1].strip()
        
        try:
            # 使用 split() 自动分割标题行和数据行
            header_parts = header_line.split()
            data_parts = data_line.split()
            
            # 检查列数是否一致
            if len(header_parts) != len(data_parts):
                raise ValueError(f"标题行列数({len(header_parts)})与数据行列数({len(data_parts)})不一致")
            
            # 检查是否有足够的列
            if len(data_parts) < 6:  # 至少需要6列必填字段
                raise ValueError("数据列数不足，至少需要6列")
            
            # 根据标题行确定type字段的位置
            type_index = -1
            for i, col_name in enumerate(header_parts):
                if col_name.lower() == 'type':
                    type_index = i
                    break
            
            if type_index == -1:
                raise ValueError("未找到type列")
            
            # 验证type字段值
            type_field = data_parts[type_index].strip()
            valid_types = ["常规", "联二合并", "春秋合并", "东西拆分"]
            if type_field not in valid_types:
                raise ValueError(f"type字段值无效: {type_field}")
            
            # 根据列数判断是否包含link_second字段
            if len(data_parts) not in [8, 9]:
                raise ValueError(f"列数错误，应为8或9列，实际为{len(data_parts)}列")
            
            # 使用空白字符作为分隔符解析文件
            df = pd.read_csv(file_path, sep='\s+', encoding='utf-8')
            separator_used = "空白分隔符"
            
            # 记录实际的列顺序
            self.logger.info(f"检测到文件格式：{separator_used}")
            self.logger.info(f"列顺序：{list(df.columns)}")
            self.logger.info(f"数据：列数={len(df.columns)}，行数={len(df)}")
            
            return df, separator_used
            
        except Exception as e:
            self.logger.error(f"解析文件失败：{e}")
            raise ValueError(f"无法解析文件格式: {str(e)}")
    
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
    
    def detect_duplicates_in_file(self, df):
        """检测文件内重复数据"""
        duplicates = []
        
        # 标准化处理数据（模拟导入时的逻辑）
        df_processed = df.copy()
        
        # 处理 group 字段默认值
        df_processed['group_processed'] = df_processed.apply(
            lambda row: '默认组' if (pd.isna(row.get('group')) or str(row.get('group', '')).strip() == '') 
                        else str(row.get('group')), axis=1
        )
        
        # 创建唯一键
        df_processed['unique_key'] = (
            df_processed['league'].astype(str) + '-' + 
            df_processed['year'].astype(str) + '-' + 
            df_processed['group_processed'].astype(str)
        )
        
        # 查找重复项
        duplicate_keys = df_processed['unique_key'].duplicated(keep=False)
        
        if duplicate_keys.any():
            # 按唯一键分组，找出重复组合
            grouped = df_processed[duplicate_keys].groupby('unique_key')
            
            for unique_key, group in grouped:
                if len(group) > 1:
                    # 解析唯一键
                    key_parts = unique_key.split('-')
                    if len(key_parts) >= 3:
                        league = key_parts[0]
                        year = '-'.join(key_parts[1:-1])  # 处理年份中可能包含的'-'
                        group_name = key_parts[-1]
                        
                        # 记录重复信息
                        row_numbers = [idx + 1 for idx in group.index]  # 转换为1基索引
                        duplicates.append({
                            'league': league,
                            'year': year, 
                            'group': group_name,
                            'unique_key': unique_key,
                            'row_numbers': row_numbers,
                            'count': len(row_numbers),
                            'rows_data': group[['league', 'year', 'group_processed', 'event', 'country']].to_dict('records')
                        })
        
        return duplicates