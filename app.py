import json
import os
import logging
import pandas as pd
import openai 
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("defect_analysis.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 初始化LLM模型
def init_llm():
    try:
        logging.info("正在初始化LLM模型 (使用 OpenAI 库)...")
        client = openai.OpenAI(
            api_key="1VyZ5+sL@n+YL7%F",
            base_url="http://192.168.36.188:10040/v1"
        )
        # 测试API连接
        logging.info("测试LLM API连接...")
        client.chat.completions.create(
            model="DeepSeek-Llama-70B", # 确保模型名称与你的本地服务匹配
            messages=[{"role": "user", "content": "测试连接"}],
            max_tokens=10 # 限制测试调用的 token 数量
        )
        logging.info("LLM模型初始化成功")
        return client
    except Exception as e:
        logging.error(f"初始化LLM模型失败: {str(e)}")
        return None

# 初始化向量化模型
def init_embeddings():
    try:
        logging.info("正在初始化向量化模型...")
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 定义模型名称和本地存储路径
        model_name = 'shibing624/text2vec-base-chinese'
        model_package_dir = os.path.join(current_dir, 'model_package')
        
        # 确保模型存储目录存在
        os.makedirs(model_package_dir, exist_ok=True)
        
        # 设置HuggingFace环境变量，强制使用本地目录
        os.environ['TRANSFORMERS_CACHE'] = model_package_dir
        os.environ['HF_HOME'] = model_package_dir
        os.environ['HF_DATASETS_CACHE'] = os.path.join(model_package_dir, 'datasets')
        # 禁用网络下载，如果本地模型不完整则会报错
        # os.environ['HF_HUB_OFFLINE'] = '1' # 部署时可以考虑启用
        
        logging.info(f"设置模型缓存/下载目录为: {model_package_dir}")
        
        # 尝试加载模型，HuggingFaceEmbeddings会自动处理缓存和下载
        logging.info(f"尝试从 {model_package_dir} 加载或下载模型 {model_name}...")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                cache_folder=model_package_dir
            )
            logging.info(f"HuggingFaceEmbeddings 对象创建成功: {model_name}")
        except Exception as emb_e:
            logging.error(f"创建 HuggingFaceEmbeddings 对象时出错: {str(emb_e)}", exc_info=True)
            raise emb_e # 重新抛出异常，以便上层捕获
        logging.info("向量化模型初始化成功")
        logging.info("向量化模型初始化成功")
        return embeddings
        
    except Exception as e:
        logging.error(f"初始化向量化模型失败: {str(e)}")
        logging.error("请检查网络连接或本地模型文件是否完整。")
        # 在部署环境中，如果模型加载失败，应该直接退出或抛出异常
        # return None # 或者 raise e
        # 为了本地开发方便，暂时返回None
        return None


# 加载知识库
def load_knowledge_base(file_path):
    try:
        logging.info(f"正在加载知识库文件: {file_path}")
        if not os.path.exists(file_path):
            logging.error(f"知识库文件不存在: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
            logging.info(f"知识库加载成功，包含 {len(knowledge_base.get('defects', []))} 条缺陷记录")
            return knowledge_base
    except json.JSONDecodeError as e:
        logging.error(f"知识库文件JSON格式错误: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"读取知识库文件失败: {str(e)}")
        return None

# 构建向量存储
def build_vector_store(_knowledge_base):
    try:
        logging.info("开始构建向量存储...")
        defects = _knowledge_base['defects']
        total_defects = len(defects)
        logging.info(f"共有 {total_defects} 条缺陷记录需要处理")
        
        texts = []
        metadatas = []
        
        # 使用tqdm添加进度条
        for defect in tqdm(defects, desc="处理缺陷记录", unit="条"):
            try:
                text = defect['defect_description']
                if not text or pd.isna(text) or text.strip() == "":
                    continue
                    
                metadata = {
                    'id': defect['id'],
                    'defect_number': defect['defect_number'],
                    'product_name': defect['product_name'],
                    'title': defect['title'],
                    'work_order': defect.get('work_order', ''),
                    'occurrence_probability': defect.get('occurrence_probability', ''),
                    'score_category': defect.get('score_category', ''),
                    'severity_level': defect.get('severity_level', ''),
                    'defect_type': defect.get('defect_type', ''),
                    'defect_scenario': defect.get('defect_scenario', ''),
                    'introduction_phase': defect.get('introduction_phase', ''),
                    'source': defect['metadata']['source']
                }
                texts.append(text)
                metadatas.append(metadata)
            except KeyError as e:
                logging.warning(f"缺陷记录缺少必要字段: {str(e)}，跳过该记录")
                continue
            except Exception as e:
                logging.warning(f"处理缺陷记录时出错: {str(e)}，跳过该记录")
                continue
        
        logging.info(f"成功处理 {len(texts)} 条有效缺陷记录，开始构建向量索引...")
        embeddings = init_embeddings()
        if not embeddings:
            logging.error("无法获取向量化模型，向量存储构建中止")
            return None
        logging.info(f"开始调用 FAISS.from_texts 构建向量存储，共 {len(texts)} 个文本...")
        try:
            vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
            logging.info("FAISS.from_texts 调用完成")
        except Exception as faiss_e:
            logging.error(f"调用 FAISS.from_texts 时出错: {str(faiss_e)}", exc_info=True)
            return None
        logging.info("向量存储构建完成")
        return vector_store
    except Exception as e:
        logging.error(f"构建向量存储失败: {str(e)}")
        return None

# 读取系统提示文件
def load_system_prompt(file_path):
    try:
        # 处理相对路径
        if not os.path.isabs(file_path):
            # 获取当前脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, file_path)
            
        logging.info(f"正在加载系统提示文件: {file_path}")
        if not os.path.exists(file_path):
            logging.warning(f"系统提示文件不存在: {file_path}，将使用默认提示词")
            # 返回默认提示词而不是None
            return "你是一个专业的缺陷分析专家，请分析给定缺陷的可能原因和解决方案。"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            logging.info(f"系统提示文件加载成功: {file_path}")
            return content
    except Exception as e:
        logging.error(f"读取系统提示文件失败: {file_path}, 错误: {str(e)}")
        # 返回默认提示词而不是None
        return "你是一个专业的缺陷分析专家，请分析给定缺陷的可能原因和解决方案。"

# 缓存机制已移除

# 分析缺陷
def analyze_defect(defect_description, defect_title, score_category, vector_store, llm, similarity_threshold=0.3):
    try:
        logging.info(f"开始分析缺陷: {defect_title if defect_title else '无标题'}")
        
        # 根据评分分类选择不同的系统提示词文件和筛选条件
        system_prompt_file = 'sys.md'  # 默认系统提示词文件
        
        # 根据评分分类设置筛选条件
        if score_category == '功能使用':
            system_prompt_file = 'sys.md'
            logging.info("使用功能使用评分分类")
        elif score_category == '体验良好':
            system_prompt_file = 'sys2.md'
            logging.info("使用体验良好评分分类")
        elif score_category == '性能效率':
            system_prompt_file = 'sys3.md'
            logging.info("使用性能效率评分分类")
        else:
            logging.info(f"未知评分分类: {score_category}，使用默认系统提示词文件")
        
        # 检索相似案例
        logging.info("开始检索相似案例...")
        similar_docs = []
        # 用于存储相似案例的详细信息，供后续导出使用
        similar_cases_info = []
        
        # 执行检索
        if not similar_docs:
            try:
                # 先根据评分分类筛选知识库中的文档
                from langchain_core.documents import Document
                filtered_docs = []
                
                # 获取向量存储中的所有文档
                all_docs = vector_store.docstore._dict.values()
                
                # 根据评分分类筛选文档
                for doc in all_docs:
                    if isinstance(doc, Document) and doc.metadata.get('score_category') == score_category:
                        filtered_docs.append(doc)
                
                logging.info(f"根据评分分类'{score_category}'筛选出 {len(filtered_docs)} 个文档")
                
                # 如果筛选后的文档数量太少，则使用原始检索
                if len(filtered_docs) < 5:
                    logging.info(f"筛选后文档数量不足，使用原始检索")
                    logging.info(f"在原始向量存储中执行 similarity_search_with_score (k=8)...")
                    similar_docs = vector_store.similarity_search_with_score(
                        defect_description,
                        k=8
                    )
                    logging.info(f"原始向量存储检索完成，找到 {len(similar_docs)} 个结果。")
                else:
                    # 创建临时向量存储用于检索
                    logging.info("开始创建临时向量存储...")
                    from langchain_community.vectorstores import FAISS
                    embeddings = init_embeddings()
                    texts = [doc.page_content for doc in filtered_docs]
                    metadatas = [doc.metadata for doc in filtered_docs]
                    logging.info(f"准备使用 {len(texts)} 个文本和 {len(metadatas)} 个元数据创建临时 FAISS 索引")
                    try:
                        temp_vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
                        logging.info("临时向量存储创建成功")
                    except Exception as temp_faiss_e:
                        logging.error(f"创建临时 FAISS 索引时出错: {str(temp_faiss_e)}", exc_info=True)
                        # 如果临时索引创建失败，可以考虑回退到原始检索或直接报错
                        logging.warning("临时索引创建失败，将尝试在原始向量存储中检索")
                        similar_docs = vector_store.similarity_search_with_score(defect_description, k=8)
                        logging.info(f"回退到原始向量存储检索完成，找到 {len(similar_docs)} 个结果。")
                        temp_vector_store = None # 标记临时存储不可用

                    # 在筛选后的文档中进行相似度检索
                    if temp_vector_store:
                     logging.info("开始在临时向量存储中进行相似度检索...")
                    logging.info(f"在临时向量存储中执行 similarity_search_with_score (k=8)...")
                    similar_docs = temp_vector_store.similarity_search_with_score(
                        defect_description,
                        k=8
                    )
                    logging.info(f"临时向量存储检索完成，找到 {len(similar_docs)} 个结果。")
                    logging.info("临时向量存储检索完成")
                
                logging.info(f"检索到 {len(similar_docs)} 个候选案例")
                
                # 缓存机制已移除
            except Exception as e:
                logging.error(f"检索相似案例失败: {str(e)}")
                similar_docs = []
        
        # 取前3个最相似的案例
        similar_docs = similar_docs[:3] if similar_docs else []
        
        context = "历史相似案例：\n"
        if not similar_docs:
            context += "未找到相似案例，将基于缺陷描述直接进行分析。\n\n"
            logging.warning("未找到相似案例，将基于缺陷描述直接进行分析")
        else:
            for i, (doc, score) in enumerate(similar_docs, 1):
                similarity = 100 / (1 + score)
                logging.info(f"案例{i}相似度: {similarity:.2f}%")
                context += f"案例{i}（相似度: {similarity:.2f}%）：\n{doc.page_content}\n"
                
                # 创建相似案例信息字典
                case_info = {
                    '案例序号': i,
                    '相似度': f"{similarity:.2f}%",
                    '缺陷描述': doc.page_content
                }
                
                if hasattr(doc, 'metadata') and doc.metadata:
                    context += "元数据信息:\n"
                    for key, value in doc.metadata.items():
                        if value and str(value).lower() != 'nan' and key != 'source':
                            context += f"{key}: {value}\n"
                            case_info[key] = value
                    context += "\n"
                
                similar_cases_info.append(case_info)
        
        # 加载系统提示文件，load_system_prompt函数已修改为在文件不存在时返回默认提示词
        system_prompt = load_system_prompt(system_prompt_file)
        logging.info(f"使用系统提示词: {system_prompt_file}")
        
        # 构造 OpenAI 格式的消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请基于以下历史案例分析当前缺陷：\n\n{context}\n当前缺陷标题：\n{defect_title}\n\n当前缺陷描述：\n{defect_description}\n\n评分分类：{score_category}"}
        ]
        
        logging.info("开始调用LLM进行分析...")
        reasoning_content = "" # OpenAI 标准 API 不直接支持 reasoning_content
        answer_content = ""
        
        try:
            # 使用 OpenAI 客户端进行流式调用 (llm 变量现在是 OpenAI client)
            stream = llm.chat.completions.create(
                model="DeepSeek-Llama-70B", # 确保模型名称正确
                messages=messages,
                stream=True
            )
            for chunk in stream:
                # 检查 OpenAI stream chunk 结构并提取内容
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    answer_content += chunk.choices[0].delta.content
            logging.info("LLM分析完成")
        except Exception as e:
            logging.error(f"LLM调用失败: {str(e)}")
            # 返回错误信息，保持三个返回值的结构，即使 reasoning 为空
            return f"LLM调用失败: {str(e)}", f"分析过程出错: {str(e)}", similar_cases_info
        
        # OpenAI API 不返回 reasoning_content，因此返回空字符串
        return "", answer_content, similar_cases_info
    except Exception as e:
        logging.error(f"缺陷分析过程出错: {str(e)}")
        return f"分析过程出错: {str(e)}", f"分析过程出错: {str(e)}", []

def main(input_file='缺陷1.xlsx', output_file='缺陷分析结果.xlsx', knowledge_base_file='defects_knowledge_base.json', similarity_threshold=0.3):
    # 确保输入文件路径是绝对路径
    input_file = os.path.abspath(input_file)
    output_file = os.path.abspath(output_file)
    
    # 处理知识库文件路径
    # 如果知识库文件路径不是绝对路径，则尝试在当前脚本目录下查找
    if not os.path.isabs(knowledge_base_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_knowledge_path = os.path.join(script_dir, knowledge_base_file)
        if os.path.exists(default_knowledge_path):
            knowledge_base_file = default_knowledge_path
        else:
            # 如果当前目录下没有找到，则使用绝对路径
            knowledge_base_file = os.path.abspath(knowledge_base_file)
    
    logging.info("=== 智能缺陷分析系统启动 ===")
    logging.info(f"输入文件: {input_file}")
    logging.info(f"输出文件: {output_file}")
    logging.info(f"知识库文件: {knowledge_base_file}")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        logging.error(f"输入文件不存在: {input_file}")
        return
        
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"已创建输出目录: {output_dir}")
        except Exception as e:
            logging.error(f"创建输出目录失败: {str(e)}")
            return
    
    # 加载知识库
    # 如果指定的知识库文件不存在，尝试使用默认知识库
    if not os.path.exists(knowledge_base_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_knowledge_file = os.path.join(script_dir, 'defects_knowledge_base.json')
        logging.warning(f"指定的知识库文件不存在: {knowledge_base_file}，尝试使用默认知识库: {default_knowledge_file}")
        knowledge_base_file = default_knowledge_file
    
    knowledge_base = load_knowledge_base(knowledge_base_file)
    if knowledge_base is None:
        logging.error("加载知识库失败，程序退出")
        return
    
    # 构建向量存储
    vector_store = build_vector_store(knowledge_base)
    if vector_store is None:
        logging.error("构建向量存储失败，程序退出")
        return
    
    # 初始化LLM模型
    llm = init_llm()
    if llm is None:
        logging.error("LLM模型初始化失败，程序退出")
        return
    
    try:
        # 读取Excel文件
        logging.info(f"正在读取Excel文件: {input_file}")
        try:
            df = pd.read_excel(input_file)
        except Exception as e:
            logging.error(f"读取Excel文件失败: {str(e)}")
            return
            
        if '缺陷描述' not in df.columns:
            logging.error("错误：Excel文件中没有'缺陷描述'列")
            return
        
        # 检查是否有缺陷标题列，如果没有则使用空字符串
        has_title = '缺陷标题' in df.columns
        logging.info(f"Excel文件{'包含' if has_title else '不包含'}缺陷标题列")
        
        # 检查是否有评分分类列，如果没有则使用默认值
        has_score_category = '评分分类' in df.columns
        logging.info(f"Excel文件{'包含' if has_score_category else '不包含'}评分分类列")
        
        # 创建结果DataFrame
        results_df = pd.DataFrame()
        results_df['缺陷描述'] = df['缺陷描述']
        if has_title:
            results_df['缺陷标题'] = df['缺陷标题']
        if has_score_category:
            results_df['评分分类'] = df['评分分类']
        results_df['推理过程'] = ''
        results_df['分析结果'] = ''
        
        # 创建相似案例DataFrame，用于存储每条缺陷的相似案例
        similar_cases_df = pd.DataFrame(columns=['缺陷索引', '缺陷描述', '缺陷标题', '评分分类', '案例序号', '相似度', '相似案例描述', '相似案例标题', 'defect_number', 'product_name', 'severity_level', 'defect_type', 'defect_scenario', 'introduction_phase'])
        
        # 逐行处理缺陷描述
        total_rows = len(df)
        logging.info(f"共有 {total_rows} 条缺陷描述需要处理")
        
        # 使用tqdm添加进度条
        for index, row in tqdm(df.iterrows(), total=total_rows, desc="处理缺陷", unit="条"):
            logging.info(f"\n正在处理第 {index + 1}/{total_rows} 条缺陷描述...")
            defect_description = row['缺陷描述']
            if pd.isna(defect_description) or not str(defect_description).strip():
                logging.warning(f"跳过第 {index + 1} 行：缺陷描述为空")
                continue
            
            # 获取缺陷标题，如果没有则使用空字符串
            defect_title = row['缺陷标题'] if has_title else ''
            if pd.isna(defect_title):
                defect_title = ''
            
            # 获取评分分类，如果没有则使用默认值'功能使用'
            score_category = row['评分分类'] if has_score_category else '功能使用'
            if pd.isna(score_category) or not str(score_category).strip():
                score_category = '功能使用'
            
            try:
                # 分析缺陷
                reasoning, analysis, similar_cases = analyze_defect(
                    str(defect_description), 
                    str(defect_title), 
                    str(score_category), 
                    vector_store, 
                    llm,
                    similarity_threshold=similarity_threshold
                )
                results_df.at[index, '推理过程'] = reasoning
                results_df.at[index, '分析结果'] = analysis
                logging.info(f"第 {index + 1} 条处理完成")
                
                # 将相似案例添加到相似案例DataFrame
                for case in similar_cases:
                    case_row = {
                        '缺陷索引': index,
                        '缺陷描述': defect_description,
                        '缺陷标题': defect_title,
                        '评分分类': score_category,
                        '案例序号': case.get('案例序号', ''),
                        '相似度': case.get('相似度', ''),
                        '相似案例描述': case.get('缺陷描述', ''),
                        '相似案例标题': case.get('title', ''),
                    }
                    
                    # 添加其他可能的元数据字段
                    for key in ['defect_number', 'product_name', 'severity_level', 'defect_type', 'defect_scenario', 'introduction_phase']:
                        case_row[key] = case.get(key, '')
                    
                    similar_cases_df = pd.concat([similar_cases_df, pd.DataFrame([case_row])], ignore_index=True)
            except Exception as e:
                error_msg = f"处理第 {index + 1} 条时出错: {str(e)}"
                logging.error(error_msg)
                results_df.at[index, '推理过程'] = f"处理出错: {str(e)}"
                results_df.at[index, '分析结果'] = f"处理出错: {str(e)}"
        
        # 保存结果到新的Excel文件
        logging.info(f"正在保存结果到: {output_file}")
        try:
            results_df.to_excel(output_file, index=False)
            logging.info(f"分析完成！结果已保存到 {output_file}")
            
            # 保存相似案例到新的Excel文件
            similar_cases_output = os.path.splitext(output_file)[0] + '_相似案例.xlsx'
            similar_cases_df.to_excel(similar_cases_output, index=False)
            logging.info(f"相似案例已保存到: {similar_cases_output}")
        except Exception as e:
            logging.error(f"保存结果文件失败: {str(e)}")
        
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")

# 添加命令行参数支持
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能缺陷分析系统')
    parser.add_argument('--input', '-i', type=str, default='缺陷1.xlsx', help='输入Excel文件路径')
    parser.add_argument('--output', '-o', type=str, default='缺陷分析结果.xlsx', help='输出Excel文件路径')
    parser.add_argument('--knowledge', '-k', type=str, default='defects_knowledge_base.json', help='知识库文件路径')
    parser.add_argument('--threshold', '-t', type=float, default=0.3, help='相似度阈值(0-1之间)')
    # 缓存相关参数已移除
    
    args = parser.parse_args()
    
    # 验证相似度阈值范围
    if args.threshold < 0 or args.threshold > 1:
        logging.error(f"相似度阈值必须在0-1之间，当前值: {args.threshold}")
        args.threshold = 0.3
        logging.info(f"已重置相似度阈值为默认值: {args.threshold}")
    
    # 运行主函数
    main(args.input, args.output, args.knowledge, args.threshold)