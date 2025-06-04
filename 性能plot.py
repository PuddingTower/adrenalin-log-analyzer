# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import os
import glob
import re
import sys
from datetime import datetime

# =============================================================================
# 1. 全局配置 (Centralized Configuration)
# =============================================================================

def setup_matplotlib_chinese():
    """设置matplotlib以支持中文显示和负号。"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        print("字体已设置为 SimHei。")
    except Exception:
        try:
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            print("SimHei 未找到，尝试设置字体为 Microsoft YaHei。")
        except Exception:
            print("警告：中文字体设置失败，图表中的中文可能无法正确显示。")

def get_data_directory():
    """获取数据文件所在的目录（支持.py和打包后的.exe）。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# --- 文件和输出配置 ---
DATA_DIRECTORY = get_data_directory()
OUTPUT_DIRECTORY = os.path.join(DATA_DIRECTORY, f"分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# --- 文件匹配模式 ---
HARDWARE_FILE_PATTERN = 'Hardware.*.CSV'
FPS_FILE_PATTERN = 'FPS.Latency.*.CSV'

# --- 绘图配置 ---
# 定义了每个图表的信息，方便修改和扩展
GPU_PLOTS = {
    'GPU 1 UTIL': {'title': 'GPU 利用率', 'ylabel': '利用率 (%)'},
    'GPU 1 SCLK': {'title': 'GPU 核心频率', 'ylabel': '频率 (MHz)'},
    'GPU 1 BRD PWR': {'title': 'GPU 功耗', 'ylabel': '功耗 (W)'},
    'GPU 1 TEMP': {'title': 'GPU 温度', 'ylabel': '温度 (°C)', 'extra_line': 'GPU 1 HOTSPOT TEMP', 'extra_label': '热点温度'},
    'GPU 1 FAN': {'title': 'GPU 风扇转速', 'ylabel': '转速 (RPM)'},
    'GPU MEM 1 UTIL': {'title': '显存使用量', 'ylabel': '显存 (MB)'}
}

CPU_MEM_PLOTS = {
    'CPU UTIL': {'title': 'CPU 利用率', 'ylabel': '利用率 (%)'},
    'CPU FREQUENCY': {'title': 'CPU 频率', 'ylabel': '频率 (GHz)'},
    'CPU TEMPERATURE': {'title': 'CPU 温度', 'ylabel': '温度 (°C)'},
    'SYSTEM MEM UTIL': {'title': '系统内存利用率', 'ylabel': '利用率 (%)'}
}

FPS_PLOTS = {
    'FPS': {'title': 'FPS', 'ylabel': 'FPS'},
    'AVG FRAME TIME': {'title': '平均帧时间', 'ylabel': '帧时间 (ms)'},
    '99th% FPS': {'title': '99th 百分位 FPS', 'ylabel': 'FPS'},
    'STUTTER': {'title': '卡顿指标', 'ylabel': '指标/率', 'lines': {'MICRO STUTTER': '微卡顿', 'HEAVY STUTTER RATE': '严重卡顿率'}}
}


# =============================================================================
# 2. 辅助函数 (Helper Functions)
# =============================================================================

def find_latest_file(directory, pattern):
    """根据模式在目录中查找最新的文件。"""
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files:
        return None
    
    # 尝试按文件名中的时间戳排序，如果失败则按文件修改时间排序
    try:
        latest_file = max(files, key=lambda f: re.search(r'(\d{8}-\d{6})', os.path.basename(f)).group(1))
    except (AttributeError, ValueError):
        print(f"警告：无法从文件名中解析时间戳，将根据文件修改时间选择最新文件。")
        latest_file = max(files, key=os.path.getmtime)
        
    return latest_file

def load_and_clean_data(file_path, file_type):
    """
    加载并清洗CSV数据。
    
    Args:
        file_path (str): CSV文件路径。
        file_type (str): 文件类型 ('Hardware' 或 'FPS') 用于定制化清洗。

    Returns:
        pd.DataFrame: 清洗后的DataFrame。
    """
    if not file_path or not os.path.exists(file_path):
        print(f"错误: {file_type} 文件路径无效或文件不存在: {file_path}")
        return pd.DataFrame()

    print(f"\n--- 正在处理 {file_type} 数据: {os.path.basename(file_path)} ---")
    try:
        df = pd.read_csv(file_path, na_values=["N/A"], skipinitialspace=True)
        
        if 'TIME STAMP' not in df.columns:
            print(f"错误: {file_type} 文件中缺少 'TIME STAMP' 列。")
            return pd.DataFrame()
            
        # AMD导出的数据有时第一行是空的，需要跳过
        if pd.isna(df.iloc[0]['TIME STAMP']):
            df = df.iloc[1:].copy()
            
        df['TIME STAMP'] = pd.to_datetime(df['TIME STAMP'], errors='coerce')
        df.dropna(subset=['TIME STAMP'], inplace=True)
        
        if df.empty:
            print(f"警告: {file_type} 文件在移除无效时间戳后为空。")
            return df
            
        for col in df.columns:
            if col != 'TIME STAMP' and col != 'PROCESS':
                df[col] = pd.to_numeric(df[col], errors='coerce')

        print(f"数据加载清洗完成。共 {len(df)} 条记录。")
        print(f"时间范围: {df['TIME STAMP'].min()} -> {df['TIME STAMP'].max()}")
        if 'PROCESS' in df.columns:
            print(f"涉及的进程: {df['PROCESS'].unique()}")
        
        return df

    except Exception as e:
        print(f"处理 {file_type} 文件时发生未知错误: {e}")
        return pd.DataFrame()

def plot_time_series(ax, df, plot_config):
    """在给定的Axes上绘制时间序列图。"""
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xlabel('时间')
    
    # 格式化X轴时间显示
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

    # 处理单线图
    if 'y_col' in plot_config:
        col = plot_config['y_col']
        if col in df.columns and not df[col].dropna().empty:
            ax.plot(df['TIME STAMP'], df[col], label=plot_config.get('label', col))
            ax.set_title(plot_config['title'])
            ax.set_ylabel(plot_config['ylabel'])
            
            # 检查是否有附加线（如热点温度）
            if 'extra_line' in plot_config and plot_config['extra_line'] in df.columns:
                extra_col = plot_config['extra_line']
                ax.plot(df['TIME STAMP'], df[extra_col], label=plot_config['extra_label'], linestyle='--')
            ax.legend()
        else:
            ax.set_title(f"{plot_config['title']} (数据缺失)")
            ax.text(0.5, 0.5, '数据缺失', ha='center', va='center', transform=ax.transAxes)
    
    # 处理多线图（如卡顿）
    elif 'lines' in plot_config:
        plotted = False
        ax.set_title(plot_config['title'])
        ax.set_ylabel(plot_config['ylabel'])
        for col, label in plot_config['lines'].items():
            if col in df.columns and not df[col].dropna().empty:
                ax.plot(df['TIME STAMP'], df[col].fillna(0), label=label, linestyle='--' if 'MICRO' in col else ':')
                plotted = True
        if plotted:
            ax.legend()
        else:
            ax.set_title(f"{plot_config['title']} (数据缺失)")
            ax.text(0.5, 0.5, '数据缺失', ha='center', va='center', transform=ax.transAxes)

# =============================================================================
# 3. 主逻辑 (Main Logic)
# =============================================================================

def main():
    """主执行函数"""
    setup_matplotlib_chinese()
    
    # --- 查找并加载数据 ---
    hardware_file = find_latest_file(DATA_DIRECTORY, HARDWARE_FILE_PATTERN)
    fps_file = find_latest_file(DATA_DIRECTORY, FPS_FILE_PATTERN)

    hw_df = load_and_clean_data(hardware_file, "Hardware")
    fps_df = load_and_clean_data(fps_file, "FPS.Latency")

    if hw_df.empty and fps_df.empty:
        print("\n错误：未能加载任何有效数据，程序即将退出。")
        return

    # 创建输出目录
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
        print(f"\n图表将保存至: {OUTPUT_DIRECTORY}")

    # --- 生成并保存Hardware图表 ---
    if not hw_df.empty:
        print("\n--- 正在生成 Hardware 图表 ---")
        # GPU图表
        fig_gpu, axs_gpu = plt.subplots(3, 2, figsize=(18, 15), constrained_layout=True)
        fig_gpu.suptitle('GPU 硬件指标随时间变化', fontsize=20)
        for ax, (col, config) in zip(axs_gpu.flat, GPU_PLOTS.items()):
            plot_time_series(ax, hw_df, {'y_col': col, **config})
        plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'GPU硬件指标.png'))
        plt.show()

        # CPU和内存图表
        fig_cpu, axs_cpu = plt.subplots(2, 2, figsize=(18, 10), constrained_layout=True)
        fig_cpu.suptitle('CPU 与内存指标随时间变化', fontsize=20)
        for ax, (col, config) in zip(axs_cpu.flat, CPU_MEM_PLOTS.items()):
            plot_time_series(ax, hw_df, {'y_col': col, **config})
        plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'CPU与内存指标.png'))
        plt.show()

    # --- 生成并保存FPS图表 ---
    if not fps_df.empty:
        print("\n--- 正在生成 FPS.Latency 图表 ---")
        fig_fps, axs_fps = plt.subplots(2, 2, figsize=(18, 10), constrained_layout=True)
        fig_fps.suptitle('游戏性能指标随时间变化', fontsize=20)
        plot_configs = [
            {'y_col': 'FPS', **FPS_PLOTS['FPS']},
            {'y_col': 'AVG FRAME TIME', **FPS_PLOTS['AVG FRAME TIME']},
            {'y_col': '99th% FPS', **FPS_PLOTS['99th% FPS']},
            FPS_PLOTS['STUTTER']
        ]
        for ax, config in zip(axs_fps.flat, plot_configs):
            plot_time_series(ax, fps_df, config)
        plt.savefig(os.path.join(OUTPUT_DIRECTORY, '游戏性能指标.png'))
        plt.show()

    # --- 合并数据并生成关联性分析图表 ---
    if not hw_df.empty and not fps_df.empty:
        print("\n--- 正在合并数据并生成关联性分析图表 ---")
        merged_df = pd.merge_asof(
            fps_df.sort_values('TIME STAMP'),
            hw_df.sort_values('TIME STAMP'),
            on='TIME STAMP',
            direction='nearest',
            tolerance=pd.Timedelta('2s')
        )
        
        # 选择用于分析的数值列
        corr_cols = [
            'FPS', '99th% FPS', 'AVG FRAME TIME',
            'GPU 1 UTIL', 'GPU 1 SCLK', 'GPU 1 BRD PWR', 'GPU 1 TEMP',
            'CPU UTIL', 'CPU FREQUENCY', 'CPU TEMPERATURE', 'SYSTEM MEM UTIL'
        ]
        # 仅保留merged_df中实际存在的列
        valid_corr_cols = [col for col in corr_cols if col in merged_df.columns]
        
        if len(valid_corr_cols) > 1:
            corr_matrix = merged_df[valid_corr_cols].corr()
            
            plt.figure(figsize=(12, 10))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
            plt.title('关键性能指标相关性热力图', fontsize=16)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIRECTORY, '性能指标相关性热力图.png'))
            print("正在显示图表: 性能指标相关性热力图")
            plt.show()
        else:
            print("合并后的有效数据列不足，无法生成相关性分析。")

    print("\n--- 分析完成 ---")

if __name__ == '__main__':
    main()
