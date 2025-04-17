# 智能缺陷分析系统

## 项目概述

智能缺陷分析系统是一个基于大语言模型和向量检索的缺陷分析工具，能够自动分析产品缺陷描述，并提供专业的原因分析和解决方案建议。系统通过Streamlit提供友好的Web界面，支持Excel文件上传、实时日志显示和结果下载等功能。

## 功能特点

- **智能分析**：利用大语言模型（DeepSeek）对缺陷进行智能分析
- **相似案例检索**：基于向量数据库（FAISS）进行相似案例检索
- **多评分分类支持**：根据不同评分分类（功能使用、体验良好、性能效率）选择不同的分析策略
- **批量处理**：支持Excel文件批量导入和处理
- **实时日志**：提供实时处理日志显示
- **结果导出**：支持分析结果和日志导出

## 系统架构

系统由以下主要组件构成：

1. **前端界面**：基于Streamlit构建的Web界面（`streamlit_app.py`）
2. **核心分析引擎**：基于LangChain和DeepSeek的分析模块（`app.py`）
3. **知识库**：包含历史缺陷案例的JSON文件（`defects_knowledge_base.json`）
4. **系统提示词**：针对不同评分分类的提示词文件（`sys.md`, `sys2.md`, `sys3.md`）

## 环境要求

- Python 3.9+
- 网络连接（用于访问DeepSeek API）
- 至少4GB可用内存
- 约500MB磁盘空间

## 安装依赖

本项目依赖以下主要Python库：

- streamlit
- langchain
- langchain_deepseek
- pandas
- faiss-cpu
- huggingface_hub
- tqdm

可以通过以下命令安装所有依赖：

```bash
pip install streamlit langchain langchain_deepseek pandas faiss-cpu huggingface_hub tqdm
```

或者创建虚拟环境后使用requirements.txt安装（推荐）：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 部署指南

### 本地部署

#### Windows系统

1. **安装Python**：
   - 从[Python官网](https://www.python.org/downloads/windows/)下载并安装Python 3.9+
   - 安装时勾选"Add Python to PATH"

2. **下载项目**：
   
   - 下载或克隆项目到本地目录
   
3. **创建虚拟环境**：
   ```cmd
   cd 项目目录路径
   python -m venv venv
   venv\Scripts\activate
   ```

4. **安装依赖**：
   ```cmd
   pip install streamlit langchain langchain_deepseek pandas faiss-cpu huggingface_hub tqdm
   ```

5. **配置API密钥**：
   - 在`app.py`文件中更新DeepSeek API密钥

6. **启动应用**：
   ```cmd
   streamlit run streamlit_app.py
   ```

#### Linux/MacOS系统

1. **安装Python**：
   - Linux: `sudo apt-get install python3.9 python3.9-venv`
   - MacOS: `brew install python@3.9`

2. **下载项目**：
   ```bash
   git clone <项目仓库URL>
   cd <项目目录>
   ```

3. **创建虚拟环境**：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **安装依赖**：
   ```bash
   pip install streamlit langchain langchain_deepseek pandas faiss-cpu huggingface_hub tqdm
   ```

5. **配置API密钥**：
   - 在`app.py`文件中更新DeepSeek API密钥

6. **启动应用**：
   ```bash
   streamlit run streamlit_app.py
   ```

### 服务器部署

#### 使用Screen或Tmux（Linux/MacOS）

适用于需要长期运行的简单部署：

1. **安装Screen或Tmux**：
   - `sudo apt-get install screen` 或 `sudo apt-get install tmux`

2. **创建新会话**：
   - Screen: `screen -S defect_analysis`
   - Tmux: `tmux new -s defect_analysis`

3. **启动应用**：
   ```bash
   cd <项目目录>
   source venv/bin/activate
   streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
   ```

4. **分离会话**：
   - Screen: 按 `Ctrl+A` 然后按 `D`
   - Tmux: 按 `Ctrl+B` 然后按 `D`

5. **重新连接会话**：
   - Screen: `screen -r defect_analysis`
   - Tmux: `tmux attach -t defect_analysis`

#### 使用Systemd服务（Linux）

适用于需要自动启动和监控的生产环境：

1. **创建服务文件**：
   ```bash
   sudo nano /etc/systemd/system/defect-analysis.service
   ```

2. **添加以下内容**：
   ```ini
   [Unit]
   Description=Defect Analysis Streamlit App
   After=network.target
   
   [Service]
   User=<用户名>
   WorkingDirectory=/path/to/project
   ExecStart=/path/to/project/venv/bin/streamlit run /path/to/project/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
   Restart=on-failure
   RestartSec=5s
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **启用并启动服务**：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable defect-analysis
   sudo systemctl start defect-analysis
   ```

4. **检查服务状态**：
   ```bash
   sudo systemctl status defect-analysis
   ```

#### 使用Docker部署

适用于容器化部署：

1. **创建Dockerfile**：
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **创建requirements.txt**：
   ```
   streamlit
   langchain
   langchain_deepseek
   pandas
   faiss-cpu
   huggingface_hub
   tqdm
   ```

3. **构建并运行Docker镜像**：
   ```bash
   docker build -t defect-analysis .
   docker run -d -p 8501:8501 --name defect-analysis-app defect-analysis
   ```

#### 使用Nginx反向代理（生产环境）

适用于需要HTTPS和域名访问的生产环境：

1. **安装Nginx**：
   ```bash
   sudo apt-get install nginx
   ```

2. **配置Nginx**：
   ```bash
   sudo nano /etc/nginx/sites-available/defect-analysis
   ```

3. **添加以下内容**：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
   
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

4. **启用站点并重启Nginx**：
   ```bash
   sudo ln -s /etc/nginx/sites-available/defect-analysis /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **配置SSL（可选）**：
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## 配置说明

### API密钥配置

在`app.py`文件中找到以下代码段并更新API密钥：

```python
llm = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key="your-api-key-here",  # 替换为你的API密钥
    base_url="https://api.deepseek.com",
)
```

### 系统提示词配置

系统提供三个不同的提示词文件，分别对应不同的评分分类：

- `sys.md`: 功能使用类缺陷分析
- `sys2.md`: 体验良好类缺陷分析
- `sys3.md`: 性能效率类缺陷分析

可以根据需要修改这些文件中的提示词内容。

## 使用说明

1. **启动应用**：
   ```bash
   streamlit run streamlit_app.py
   ```

2. **上传Excel文件**：
   - Excel文件必须包含"缺陷描述"列
   - 可选包含"缺陷标题"和"评分分类"列
   - 评分分类可以是"功能使用"、"体验良好"或"性能效率"

3. **选择知识库**：
   - 默认使用系统自带的知识库
   - 可以上传自定义知识库文件（JSON格式）

4. **开始分析**：
   - 点击"开始分析"按钮
   - 实时查看处理日志
   - 等待分析完成

5. **下载结果**：
   - 分析完成后可下载Excel格式的分析结果
   - 可选下载完整日志文件

## 数据格式说明

### 输入Excel格式

必须包含的列：
- `缺陷描述`：缺陷的详细描述文本

可选列：
- `缺陷标题`：缺陷的简短标题
- `评分分类`：缺陷的评分分类，可以是"功能使用"、"体验良好"或"性能效率





1、打印历史缺陷

2、最好设定模版

3、实时缓存

4、改善策略优化

5、定级有一些出入，模型更严重一些，其他均可用。数值人、甘肃、

