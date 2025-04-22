import pandas as pd
import re
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_defect_data.log"),
        logging.StreamHandler()
    ]
)

def extract_data_from_column(input_file, output_file):
    """
    从Excel表格的E列提取数据，并将其分解到F-M列
    """
    try:
        logging.info(f"正在读取Excel文件: {input_file}")
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            logging.error(f"输入文件不存在: {input_file}")
            return
            
        # 读取Excel文件
        df = pd.read_excel(input_file)
        
        # 检查是否有E列
        if len(df.columns) < 5:
            logging.error("Excel文件列数不足，无法处理E列数据")
            return
            
        # 获取E列的名称
        e_column_name = df.columns[4]  # 索引4对应E列
        logging.info(f"E列名称: {e_column_name}")
        
        # 创建新列
        new_columns = [
            '评分分类', '严重等级', '缺陷类型', '缺陷子类型', '缺陷引入阶段', '缺陷场景', 
            '根因分析', '改进主体', '改善策略'
        ]
        
        for col in new_columns:
            df[col] = ''
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                # 获取E列数据
                e_data = str(row[e_column_name])
                if pd.isna(e_data) or e_data.strip() == '':
                    continue
                    
                # 提取各个字段的数据
                # 评分分类
                match = re.search(r'评分分类[：:](\s*)([^\n]*)', e_data)
                if match:
                    df.at[index, '评分分类'] = match.group(2).strip()
                
                # 严重等级
                match = re.search(r'严重等级[：:](\s*)([^\n]*)', e_data)
                if match:
                    df.at[index, '严重等级'] = match.group(2).strip()
                
                # 缺陷类型
                match = re.search(r'缺陷类型[：:](\s*)([^\n]*)', e_data)
                if match:
                    defect_type_full = match.group(2).strip()
                    # 按照"-"符号拆分
                    if '-' in defect_type_full:
                        defect_parts = defect_type_full.split('-', 1)
                        df.at[index, '缺陷类型'] = defect_parts[0].strip()
                        df.at[index, '缺陷子类型'] = defect_parts[1].strip()
                    else:
                        df.at[index, '缺陷类型'] = defect_type_full
                        df.at[index, '缺陷子类型'] = ''
                
                # 缺陷场景
                match = re.search(r'缺陷场景[：:](\s*)([^\n]*)', e_data)
                if match:
                    scene_full = match.group(2).strip()
                    df.at[index, '缺陷场景'] = scene_full
                
                # 缺陷引入阶段
                match = re.search(r'缺陷引入阶段[：:](\s*)([^\n]*)', e_data)
                if match:
                    df.at[index, '缺陷引入阶段'] = match.group(2).strip()
                
                # 根因分析
                match = re.search(r'根因分析[：:](\s*)([^\n]*)', e_data)
                if match:
                    cause_full = match.group(2).strip()
                    df.at[index, '根因分析'] = cause_full
                
                # 改进主体
                match = re.search(r'改进主体[：:](\s*)([^\n]*)', e_data)
                if match:
                    df.at[index, '改进主体'] = match.group(2).strip()
                
                # 改善策略
                match = re.search(r'改善策略[：:](\s*)([^\n]*)', e_data)
                if match:
                    df.at[index, '改善策略'] = match.group(2).strip()
                
            except Exception as e:
                logging.warning(f"处理第 {index + 1} 行时出错: {str(e)}")
                continue
        
        # 保存到新的Excel文件
        logging.info(f"正在保存结果到: {output_file}")
        
        # 重新排列列的顺序
        column_order = [
            # 保留原有的前5列
            df.columns[0], df.columns[1], df.columns[2], df.columns[3], df.columns[4],
            # 新的列顺序
            '评分分类', '严重等级', '缺陷类型', '缺陷子类型', '缺陷引入阶段', 
            '缺陷场景', '根因分析', '改进主体', '改善策略'
        ]
        
        # 确保所有列都存在
        final_columns = [col for col in column_order if col in df.columns]
        
        # 按新顺序排列列
        df = df[final_columns]
        df.to_excel(output_file, index=False)
        logging.info(f"数据提取完成！结果已保存到 {output_file}")
        logging.info(f"列已按照新的顺序排列，并拆分了缺陷类型、缺陷场景和根因分析列")
        
    except Exception as e:
        logging.error(f"处理过程中出现错误: {str(e)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='从Excel表格E列提取数据到多个列')
    parser.add_argument('--input', '-i', type=str, default='缺陷分析结果.xlsx', help='输入Excel文件路径')
    parser.add_argument('--output', '-o', type=str, default='缺陷数据提取结果.xlsx', help='输出Excel文件路径')
    
    args = parser.parse_args()
    
    # 运行主函数
    extract_data_from_column(args.input, args.output)