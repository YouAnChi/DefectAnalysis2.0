import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import numpy as np

# 数据可视化模块 - 用于智能缺陷分析系统

def load_analysis_results(excel_file):
    """加载分析结果Excel文件"""
    try:
        df = pd.read_excel(excel_file)
        return df
    except Exception as e:
        st.error(f"加载分析结果文件失败: {str(e)}")
        return None

def create_category_chart(df):
    """创建评分分类分布图表"""
    if '评分分类' not in df.columns:
        return None
    
    # 计算各分类的数量
    category_counts = df['评分分类'].value_counts().reset_index()
    category_counts.columns = ['分类', '数量']
    
    # 创建饼图
    fig = px.pie(
        category_counts, 
        values='数量', 
        names='分类',
        title='缺陷评分分类分布',
        color_discrete_sequence=px.colors.sequential.Blues_r,
        hole=0.4
    )
    
    fig.update_layout(
        legend_title_text='评分分类',
        font=dict(size=12),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    return fig

def create_similarity_histogram(df):
    """创建相似度分布直方图"""
    if '最高相似度' not in df.columns:
        return None
    
    # 创建直方图
    fig = px.histogram(
        df, 
        x='最高相似度',
        nbins=20,
        title='缺陷相似度分布',
        color_discrete_sequence=['#3498DB']
    )
    
    fig.update_layout(
        xaxis_title='相似度',
        yaxis_title='数量',
        font=dict(size=12),
        margin=dict(t=50, b=50, l=50, r=20)
    )
    
    return fig

def create_analysis_time_chart(df):
    """创建分析时间分布图"""
    if '分析时间(秒)' not in df.columns:
        return None
    
    # 创建箱形图
    fig = px.box(
        df, 
        y='分析时间(秒)',
        title='缺陷分析时间分布',
        color_discrete_sequence=['#2ECC71']
    )
    
    fig.update_layout(
        yaxis_title='分析时间(秒)',
        font=dict(size=12),
        margin=dict(t=50, b=20, l=50, r=20)
    )
    
    return fig

def create_summary_metrics(df):
    """创建摘要指标"""
    metrics = {}
    
    # 总缺陷数
    metrics['total_defects'] = len(df)
    
    # 平均分析时间
    if '分析时间(秒)' in df.columns:
        metrics['avg_analysis_time'] = df['分析时间(秒)'].mean()
    
    # 平均相似度
    if '最高相似度' in df.columns:
        metrics['avg_similarity'] = df['最高相似度'].mean()
    
    # 各分类数量
    if '评分分类' in df.columns:
        metrics['category_counts'] = df['评分分类'].value_counts().to_dict()
    
    return metrics

def display_analysis_dashboard(excel_data):
    """显示分析结果仪表板"""
    st.markdown('<div class="css-card dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 分析结果仪表板")
    
    df = load_analysis_results(excel_data)
    if df is None:
        st.warning("无法加载分析结果数据")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # 计算摘要指标
    metrics = create_summary_metrics(df)
    
    # 显示摘要指标
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("总缺陷数", f"{metrics.get('total_defects', 0)}")
    
    if 'avg_analysis_time' in metrics:
        with metric_cols[1]:
            st.metric("平均分析时间", f"{metrics.get('avg_analysis_time', 0):.2f}秒")
    
    if 'avg_similarity' in metrics:
        with metric_cols[2]:
            st.metric("平均相似度", f"{metrics.get('avg_similarity', 0):.2f}")
    
    # 创建图表
    st.markdown("### 数据可视化")
    
    # 创建两列布局用于图表
    chart_col1, chart_col2 = st.columns(2)
    
    # 评分分类分布图
    category_chart = create_category_chart(df)
    if category_chart:
        with chart_col1:
            st.plotly_chart(category_chart, use_container_width=True)
    
    # 相似度分布直方图
    similarity_chart = create_similarity_histogram(df)
    if similarity_chart:
        with chart_col2:
            st.plotly_chart(similarity_chart, use_container_width=True)
    
    # 分析时间分布图
    time_chart = create_analysis_time_chart(df)
    if time_chart:
        st.plotly_chart(time_chart, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)