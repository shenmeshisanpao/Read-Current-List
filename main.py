#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Current Record File Analyzer
# Author: ZhiCheng Zhang <zhangzhicheng@cnncmail.cn>
# Date: 2025-07-30

import sys
import os
import csv
import time
import re
from datetime import datetime
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QHBoxLayout, QGridLayout, QLineEdit, QFileDialog,
                             QMessageBox, QComboBox, QDialog, QTextBrowser, QTextEdit,
                             QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class CurrentRecordAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Current Record File Analyzer")
        self.setGeometry(100, 100, 800, 600)
        
        # 数据存储
        self.data = None
        self.file_path = ""
        self.start_utc = None
        self.end_utc = None
        self.total_runtime = None
        
        self.init_ui()
        self.create_menu_bar()
        self.statusBar().showMessage("Ready")      # 状态栏

        # 为结果文本框添加右键复制功能
        self.ch1_result_text.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.ch2_result_text.setContextMenuPolicy(Qt.ActionsContextMenu)

        # CH1复制动作
        copy_ch1_action = QtWidgets.QAction("Copy CH1 Result", self)
        copy_ch1_action.triggered.connect(lambda: self.copy_to_clipboard(self.ch1_result_text.text()))
        self.ch1_result_text.addAction(copy_ch1_action)

        # CH2复制动作
        copy_ch2_action = QtWidgets.QAction("Copy CH2 Result", self)
        copy_ch2_action.triggered.connect(lambda: self.copy_to_clipboard(self.ch2_result_text.text()))
        self.ch2_result_text.addAction(copy_ch2_action)

        
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu('File')
        
        open_action = QtWidgets.QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu('Help')
        
        tutorial_action = QtWidgets.QAction('Tutorial', self)
        tutorial_action.triggered.connect(self.show_tutorial)
        tutorial_action.setShortcut('Ctrl+H')
        help_menu.addAction(tutorial_action)
        
        about_action = QtWidgets.QAction('About', self)
        about_action.triggered.connect(self.show_about)
        about_action.setShortcut('Ctrl+A')
        help_menu.addAction(about_action)
    
    def init_ui(self):
        """初始化用户界面"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 文件打开区域
        file_group = QGroupBox("File Information")
        file_layout = QVBoxLayout()
        
        # 文件路径显示
        file_path_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("font-weight: bold; color: #666;")
        open_file_btn = QPushButton("Open File")
        open_file_btn.clicked.connect(self.open_file)
        open_file_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        file_path_layout.addWidget(QLabel("File Path:"))
        file_path_layout.addWidget(self.file_path_label, 1)
        file_path_layout.addWidget(open_file_btn)
        
        # 文件信息显示
        info_layout = QGridLayout()
        self.start_time_label = QLabel("Start Time: --")
        self.end_time_label = QLabel("End Time: --")
        self.total_runtime_label = QLabel("Total Runtime: --")
        
        info_layout.addWidget(self.start_time_label, 0, 0)
        info_layout.addWidget(self.end_time_label, 0, 1)
        info_layout.addWidget(self.total_runtime_label, 1, 0, 1, 2)
        
        file_layout.addLayout(file_path_layout)
        file_layout.addLayout(info_layout)
        file_group.setLayout(file_layout)
        
        # 时间范围选择区域
        time_range_group = QGroupBox("Time Range Selection")
        time_range_layout = QVBoxLayout()
        
        # 时间范围选项
        self.time_range_group = QButtonGroup()
        self.full_time_radio = QRadioButton("Full Time Range")
        self.custom_time_radio = QRadioButton("Custom Time Range")
        self.full_time_radio.setChecked(True)
        
        self.time_range_group.addButton(self.full_time_radio, 0)
        self.time_range_group.addButton(self.custom_time_radio, 1)
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.full_time_radio)
        radio_layout.addWidget(self.custom_time_radio)
        radio_layout.addStretch()
        
        # 自定义时间输入区域
        self.custom_time_widget = QWidget()
        custom_layout = QGridLayout()
        
        # 开始时间输入
        custom_layout.addWidget(QLabel("Start Time:"), 0, 0)
        self.start_utc_input = QLineEdit()
        self.start_utc_input.setPlaceholderText("UTC Timestamp (e.g.: 1752638106.8)")
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("Time Format (e.g.: 20250727 15:41:15.100)")
        self.start_runtime_input = QLineEdit()
        self.start_runtime_input.setPlaceholderText("Runtime (seconds)")
        
        custom_layout.addWidget(QLabel("UTC Timestamp:"), 1, 0)
        custom_layout.addWidget(self.start_utc_input, 1, 1)
        custom_layout.addWidget(QLabel("Time:"), 2, 0)
        custom_layout.addWidget(self.start_time_input, 2, 1)
        custom_layout.addWidget(QLabel("Runtime (sec):"), 3, 0)
        custom_layout.addWidget(self.start_runtime_input, 3, 1)
        
        # 结束时间输入
        custom_layout.addWidget(QLabel("End Time:"), 0, 2)
        self.end_utc_input = QLineEdit()
        self.end_utc_input.setPlaceholderText("UTC Timestamp (e.g.: 1752638121.0)")
        self.end_time_input = QLineEdit()
        self.end_time_input.setPlaceholderText("Time Format (e.g.: 20250727 15:41:30.100)")
        self.end_runtime_input = QLineEdit()
        self.end_runtime_input.setPlaceholderText("Runtime (seconds)")
        
        custom_layout.addWidget(QLabel("UTC Timestamp:"), 1, 2)
        custom_layout.addWidget(self.end_utc_input, 1, 2)
        custom_layout.addWidget(QLabel("Time:"), 2, 2)
        custom_layout.addWidget(self.end_time_input, 2, 2)
        custom_layout.addWidget(QLabel("Runtime (sec):"), 3, 2)
        custom_layout.addWidget(self.end_runtime_input, 3, 2)
        
        self.custom_time_widget.setLayout(custom_layout)
        self.custom_time_widget.setEnabled(False)
        
        # 连接信号
        self.full_time_radio.toggled.connect(self.on_time_range_changed)
        self.custom_time_radio.toggled.connect(self.on_time_range_changed)
        
        # 连接时间输入框的信号，实现自动转换
        self.start_utc_input.textChanged.connect(lambda: self.auto_convert_time('start', 'utc'))
        self.start_time_input.textChanged.connect(lambda: self.auto_convert_time('start', 'time'))
        self.start_runtime_input.textChanged.connect(lambda: self.auto_convert_time('start', 'runtime'))
        self.end_utc_input.textChanged.connect(lambda: self.auto_convert_time('end', 'utc'))
        self.end_time_input.textChanged.connect(lambda: self.auto_convert_time('end', 'time'))
        self.end_runtime_input.textChanged.connect(lambda: self.auto_convert_time('end', 'runtime'))
        
        time_range_layout.addLayout(radio_layout)
        time_range_layout.addWidget(self.custom_time_widget)
        time_range_group.setLayout(time_range_layout)
        
        # 计算按钮和结果显示区域
        calc_group = QGroupBox("Calculation Results")
        calc_layout = QVBoxLayout()

        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.clicked.connect(self.calculate_charge)
        self.calculate_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        self.calculate_btn.setEnabled(False)

        # 结果显示区域
        result_display_layout = QHBoxLayout()

        # CH1结果显示
        ch1_group = QGroupBox("Channel 1 Charge (mC)")
        ch1_layout = QVBoxLayout()
        self.ch1_result_text = QLineEdit()
        self.ch1_result_text.setReadOnly(True)
        self.ch1_result_text.setFont(QFont("Consolas", 14, QFont.Bold))
        self.ch1_result_text.setStyleSheet("""
            QLineEdit {
                background-color: #f0f8ff;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 8px;
                text-align: center;
                color: #2E86AB;
            }
        """)
        self.ch1_result_text.setAlignment(Qt.AlignCenter)
        self.ch1_result_text.setPlaceholderText("--")
        ch1_layout.addWidget(self.ch1_result_text)
        ch1_group.setLayout(ch1_layout)

        # CH2结果显示
        ch2_group = QGroupBox("Channel 2 Charge (mC)")
        ch2_layout = QVBoxLayout()
        self.ch2_result_text = QLineEdit()
        self.ch2_result_text.setReadOnly(True)
        self.ch2_result_text.setFont(QFont("Consolas", 14, QFont.Bold))
        self.ch2_result_text.setStyleSheet("""
            QLineEdit {
                background-color: #f0fff0;
                border: 2px solid #FF9800;
                border-radius: 5px;
                padding: 8px;
                text-align: center;
                color: #2E86AB;
            }
        """)
        self.ch2_result_text.setAlignment(Qt.AlignCenter)
        self.ch2_result_text.setPlaceholderText("--")
        ch2_layout.addWidget(self.ch2_result_text)
        ch2_group.setLayout(ch2_layout)

        # 添加到水平布局
        result_display_layout.addWidget(ch1_group)
        result_display_layout.addWidget(ch2_group)

        calc_layout.addWidget(self.calculate_btn)
        calc_layout.addWidget(QLabel("Charge Calculation Results:"))
        calc_layout.addLayout(result_display_layout)
        calc_group.setLayout(calc_layout)
        
        # 添加到主布局
        main_layout.addWidget(file_group)
        main_layout.addWidget(time_range_group)
        main_layout.addWidget(calc_group)
        main_layout.addStretch()
    
    def on_time_range_changed(self):
        """时间范围选择改变时的处理"""
        self.custom_time_widget.setEnabled(self.custom_time_radio.isChecked())
    
    def auto_convert_time(self, position, input_type):
        """自动转换时间格式"""
        if not self.data is not None or not hasattr(self, 'start_utc'):
            return
            
        try:
            if position == 'start':
                utc_input = self.start_utc_input
                time_input = self.start_time_input
                runtime_input = self.start_runtime_input
            else:
                utc_input = self.end_utc_input
                time_input = self.end_time_input
                runtime_input = self.end_runtime_input
            
            # 避免递归调用
            if hasattr(self, '_converting'):
                return
            self._converting = True
            
            try:
                if input_type == 'utc' and utc_input.text():
                    utc_timestamp = float(utc_input.text())
                    # 转换为时间格式
                    dt = datetime.fromtimestamp(utc_timestamp)
                    time_str = dt.strftime("%Y%m%d %H:%M:%S.%f")[:-3]  # 保留毫秒
                    time_input.setText(time_str)
                    # 计算运行时间
                    if self.start_utc:
                        runtime = utc_timestamp - self.start_utc
                        runtime_input.setText(f"{runtime:.3f}")
                
                elif input_type == 'time' and time_input.text():
                    time_str = time_input.text().strip()
                    # 解析时间格式
                    dt = self.parse_time_string(time_str)
                    if dt:
                        utc_timestamp = dt.timestamp()
                        utc_input.setText(f"{utc_timestamp:.1f}")
                        # 计算运行时间
                        if self.start_utc:
                            runtime = utc_timestamp - self.start_utc
                            runtime_input.setText(f"{runtime:.3f}")
                
                elif input_type == 'runtime' and runtime_input.text():
                    runtime = float(runtime_input.text())
                    if self.start_utc:
                        utc_timestamp = self.start_utc + runtime
                        utc_input.setText(f"{utc_timestamp:.1f}")
                        # 转换为时间格式
                        dt = datetime.fromtimestamp(utc_timestamp)
                        time_str = dt.strftime("%Y%m%d %H:%M:%S.%f")[:-3]
                        time_input.setText(time_str)
            
            except (ValueError, TypeError):
                pass  # 忽略转换错误
            
            finally:
                del self._converting
                
        except Exception:
            pass
    
    def parse_time_string(self, time_str):
        """解析时间字符串"""
        try:
            # 尝试不同的时间格式
            formats = [
                "%Y%m%d %H:%M:%S.%f",
                "%Y%m%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Current Record File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 检查文件格式和内容
            if not self.validate_file(file_path):
                return
                
            # 读取文件数据
            self.load_file_data(file_path)
            
            # 更新界面
            self.file_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.file_path_label.setToolTip(file_path)
            
            # 显示文件信息
            self.update_file_info()
            
            # 启用计算按钮
            self.calculate_btn.setEnabled(True)
            
            QMessageBox.information(self, "Success", "File loaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def validate_file(self, file_path):
        """验证文件格式和内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否为CSV文件
            if not file_path.lower().endswith('.csv'):
                QMessageBox.warning(self, "Warning", "Please select a CSV format file!")
                return False
            
            # 检查是否包含多个会话（不支持Append模式的文件）
            session_count = content.count("New dual-channel monitoring session started at")
            if session_count > 1:
                QMessageBox.warning(self, "Not Supported", 
                    "Detected file contains multiple monitoring sessions (Append mode), "
                    "this type of file is not currently supported.\n"
                    "Please select a single monitoring session file.")
                return False
            
            # 检查文件头格式
            lines = content.strip().split('\n')
            if len(lines) < 3:
                QMessageBox.warning(self, "Format Error", "File content is incomplete!")
                return False
            
            # 检查表头格式
            header = lines[0].strip()
            expected_headers = [
                "UTC Timestamp, Run Time (Seconds), Channel 1 Current (mA), Channel 2 Current (mA), Channel 1 Integral (mC), Channel 2 Integral (mC)",
                "UTC Timestamp, Run Time (Seconds), Current (mA), Integral Value (mC)"  # 兼容旧格式
            ]
            
            if not any(header == expected for expected in expected_headers):
                QMessageBox.warning(self, "Format Error", 
                    "Incorrect file header format!\n"
                    f"Current file header: {header}\n"
                    "Please ensure this is a correct current monitoring record file.")
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"File validation failed: {str(e)}")
            return False
    
    def load_file_data(self, file_path):
        """加载文件数据"""
        try:
            # 读取CSV文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 过滤掉注释行
            data_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    data_lines.append(line)
            
            # 解析数据
            if len(data_lines) < 2:
                raise ValueError("Insufficient data rows in file")
            
            # 检查是否为双通道格式
            header = data_lines[0]
            is_dual_channel = "Channel 1" in header and "Channel 2" in header
            
            # 解析数据行
            data_rows = []
            for line in data_lines[1:]:
                parts = [part.strip() for part in line.split(',')]
                if is_dual_channel and len(parts) >= 6:
                    # 双通道格式: UTC, Runtime, Ch1_Current, Ch2_Current, Ch1_Integral, Ch2_Integral
                    data_rows.append({
                        'utc_timestamp': float(parts[0]),
                        'runtime': float(parts[1]),
                        'ch1_current': float(parts[2]),
                        'ch2_current': float(parts[3]),
                        'ch1_integral': float(parts[4]),
                        'ch2_integral': float(parts[5])
                    })
                elif not is_dual_channel and len(parts) >= 4:
                    # 单通道格式: UTC, Runtime, Current, Integral
                    data_rows.append({
                        'utc_timestamp': float(parts[0]),
                        'runtime': float(parts[1]),
                        'ch1_current': float(parts[2]),
                        'ch2_current': 0.0,  # 单通道时设为0
                        'ch1_integral': float(parts[3]),
                        'ch2_integral': 0.0   # 单通道时设为0
                    })
            
            if not data_rows:
                raise ValueError("No valid data rows found in file")
            
            # 转换为DataFrame
            self.data = pd.DataFrame(data_rows)
            self.is_dual_channel = is_dual_channel
            
            # 计算文件信息
            self.start_utc = self.data['utc_timestamp'].iloc[0]
            self.end_utc = self.data['utc_timestamp'].iloc[-1]
            self.total_runtime = self.data['runtime'].iloc[-1]
            
        except Exception as e:
            raise Exception(f"Data loading failed: {str(e)}")
    
    def update_file_info(self):
        """更新文件信息显示"""
        if self.data is None:
            return
        
        # 格式化时间显示
        start_dt = datetime.fromtimestamp(self.start_utc)
        end_dt = datetime.fromtimestamp(self.end_utc)
        
        start_str = f"{start_dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {self.start_utc:.1f})"
        end_str = f"{end_dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {self.end_utc:.1f})"
        runtime_str = f"{self.total_runtime:.3f} seconds"
        
        self.start_time_label.setText(f"Start Time: {start_str}")
        self.end_time_label.setText(f"End Time: {end_str}")
        self.total_runtime_label.setText(f"Total Runtime: {runtime_str}")
    
    def calculate_charge(self):
        """计算电荷量"""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "Please open a file first!")
            return
        
        try:
            # 确定时间范围
            if self.full_time_radio.isChecked():
                start_utc = self.start_utc
                end_utc = self.end_utc
            else:
                # 自定义时间范围
                start_utc = self.get_custom_time('start')
                end_utc = self.get_custom_time('end')
                
                if start_utc is None or end_utc is None:
                    QMessageBox.warning(self, "Warning", "Please enter valid start and end times!")
                    return
                
                if start_utc >= end_utc:
                    QMessageBox.warning(self, "Warning", "Start time must be less than end time!")
                    return
            
            # 计算电荷量
            ch1_start_integral = self.interpolate_integral(start_utc, 'ch1_integral')
            ch1_end_integral = self.interpolate_integral(end_utc, 'ch1_integral')
            ch2_start_integral = self.interpolate_integral(start_utc, 'ch2_integral')
            ch2_end_integral = self.interpolate_integral(end_utc, 'ch2_integral')
            
            ch1_total_charge = ch1_end_integral - ch1_start_integral
            ch2_total_charge = ch2_end_integral - ch2_start_integral

            # 显示结果到对应的文本框
            self.ch1_result_text.setText(f"{ch1_total_charge:.6f}")
            self.ch2_result_text.setText(f"{ch2_total_charge:.6f}")

            # 可选：在状态栏显示计算完成信息（如果需要详细信息）
            start_dt = datetime.fromtimestamp(start_utc)
            end_dt = datetime.fromtimestamp(end_utc)
            duration = end_utc - start_utc

            # 如果需要，可以在状态栏显示计算信息
            status_message = (f"Calculation completed - Time range: {start_dt.strftime('%H:%M:%S')} to "
                         f"{end_dt.strftime('%H:%M:%S')} (duration {duration:.1f}s)")
            self.statusBar().showMessage(status_message, 5000)  # 显示5秒   

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")
    
    def get_custom_time(self, position):
        """获取自定义时间"""
        try:
            if position == 'start':
                utc_text = self.start_utc_input.text().strip()
                time_text = self.start_time_input.text().strip()
                runtime_text = self.start_runtime_input.text().strip()
            else:
                utc_text = self.end_utc_input.text().strip()
                time_text = self.end_time_input.text().strip()
                runtime_text = self.end_runtime_input.text().strip()
            
            # 优先使用UTC时间戳
            if utc_text:
                return float(utc_text)
            elif time_text:
                dt = self.parse_time_string(time_text)
                if dt:
                    return dt.timestamp()
            elif runtime_text:
                runtime = float(runtime_text)
                return self.start_utc + runtime
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def interpolate_integral(self, target_utc, column):
        """插值计算指定时间点的积分值"""
        # 查找最接近的两个数据点
        data_utc = self.data['utc_timestamp'].values
        data_integral = self.data[column].values
        
        # 如果目标时间在数据范围外，使用边界值
        if target_utc <= data_utc[0]:
            return data_integral[0]
        if target_utc >= data_utc[-1]:
            return data_integral[-1]
        
        # 查找插值点
        for i in range(len(data_utc) - 1):
            if data_utc[i] <= target_utc <= data_utc[i + 1]:
                # 线性插值
                t1, t2 = data_utc[i], data_utc[i + 1]
                v1, v2 = data_integral[i], data_integral[i + 1]
                
                # 避免除零
                if t2 == t1:
                    return v1
                
                # 线性插值公式
                interpolated_value = v1 + (v2 - v1) * (target_utc - t1) / (t2 - t1)
                return interpolated_value
        
        # 如果没有找到合适的区间，返回最接近的值
        idx = np.argmin(np.abs(data_utc - target_utc))
        return data_integral[idx]
    
    def show_about(self):
        """显示关于对话框"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About")
        about_dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_label = QLabel()
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignTop)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        about_text = """
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <center>
        <h2 style="color: #2E86AB;">Current Record File Analyzer</h2>
        <p><b>Version 2025.07.30</b></p>
        <p>Support "Real-Time Current Monitoring System"</p>
        <p><b>Developer:</b> Zhicheng Zhang</p>
        <p><b>Email:</b> <a href="mailto:zhangzhicheng@cnncmail.cn">zhangzhicheng@cnncmail.cn</a></p>
        <p style="color: #666; font-size: 12px;">© 2025 CIAE & IMP Nuclear Astrophysics Group. All Rights Reserved.</p>
        </center>
        
        <hr style="margin: 20px 0; border: 1px solid #ddd;">
        
        <h3 style="color: #2E86AB;">About This Software</h3>
        <p>This software is used to analyze current monitoring record files, supports single-channel and dual-channel data formats, and can calculate charge integrals within specified time ranges.</p>

        <hr style="margin: 20px 0; border: 1px solid #ddd;">
        
        <h3 style="color: #2E86AB;">Update History</h3>

        <h4 style="color: #4A90E2; margin-bottom: 5px;"> 2025-07-30</h4>
        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li>Initial Release.</li>
            <li>Open and validate CSV format current record files</li>
            <li>Display file start/end times and total runtime</li>
            <li>Support full time range and custom time period analysis</li>
            <li>Automatic time format conversion (UTC timestamp, time, runtime)</li>
            <li>Precise charge integral calculation (supports interpolation)</li>
            <li>Support single-channel and dual-channel data formats</li>
        </ul>
        </div>        
        
        <hr style="margin: 20px 0; border: 1px solid #ddd;">
        
        <center>
        <p style="font-size: 12px; color: #888;">
        For technical support or bug reports, please contact the developer.<br>
        This software is provided "as is" without warranty of any kind.
        </p>
        </center>
        </div>
        """
        
        content_label.setText(about_text)
        scroll_area.setWidget(content_label)
        
        layout.addWidget(scroll_area)
        
        # 添加确定按钮
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(about_dialog.accept)
        ok_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        about_dialog.setLayout(layout)
        about_dialog.exec_()

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.statusBar().showMessage(f"Copied: {text}", 2000)


    def show_tutorial(self):
        """显示教程对话框"""
        tutorial_dialog = QDialog(self)
        tutorial_dialog.setWindowTitle("Tutorial")
        tutorial_dialog.setFixedSize(600, 500)
        
        layout = QVBoxLayout()
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # 从外部HTML文件加载教程内容
        tutorial_html = self.load_tutorial_html()
        text_browser.setHtml(tutorial_html)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(tutorial_dialog.accept)
        close_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        layout.addWidget(text_browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        tutorial_dialog.setLayout(layout)
        tutorial_dialog.exec_()

    def load_tutorial_html(self):
        """加载教程HTML文件"""
        try:
            # 获取程序所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tutorial_path = os.path.join(current_dir, "tutorial.html")
            
            # 检查文件是否存在
            if os.path.exists(tutorial_path):
                with open(tutorial_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 如果文件不存在，返回简单的错误信息
                return """
                <html>
                <body>
                    <h2>Tutorial File Not Found</h2>
                    <p>The tutorial file tutorial.html could not be found. Please ensure that the file is located in the same directory as the program.</p>
                    <p>Program Directory: {}</p>
                </body>
                </html>
                """.format(current_dir)
        
        except Exception as e:
            # 如果读取文件出错，返回错误信息
            return f"""
            <html>
            <body>
                <h2>Failed to Load Tutorial</h2>
                <p>An error occurred while reading the tutorial file: {str(e)}</p>
            </body>
            </html>
            """
        
        text_browser.setHtml(tutorial_html)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(tutorial_dialog.accept)
        close_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        layout.addWidget(text_browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        tutorial_dialog.setLayout(layout)
        tutorial_dialog.exec_()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Current Record File Analyzer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Current Monitor Tools")
    
    # 设置应用程序图标（如果存在）
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(icon_path):
        icon = QtGui.QIcon(icon_path)
        app.setWindowIcon(icon)
    
    # 创建并显示主窗口
    window = CurrentRecordAnalyzer()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
