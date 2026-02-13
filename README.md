# 企业内部知识库问答机器人（RAG）

基于 **RAG（检索增强生成）** 的企业内部知识库问答系统：将企业文档（制度、流程、手册等）导入知识库，通过自然语言提问即可获得基于文档的准确回答，并支持引用来源，符合企业合规与可追溯需求。

---

## 📋 目录

- [功能特点](#功能特点)
- [快速开始](#快速开始)
- [系统架构](#系统架构)
- [RAG 原理](#rag-原理)
- [大模型集成](#大模型集成)
- [核心模块详解](#核心模块详解)
- [配置说明](#配置说明)
- [API 说明](#api-说明)
- [性能优化](#性能优化)
- [扩展与定制](#扩展与定制)
- [常见问题](#常见问题)
- [企业部署建议](#企业部署建议)

---

## ✨ 功能特点

- **多格式文档**：支持 PDF、Word（.docx）、TXT、Markdown，从指定目录递归加载
- **本地向量化**：使用 HuggingFace 多语言句向量模型，无需嵌入 API Key，数据不出内网
- **可配置 LLM**：可选接入 OpenAI 或任意 OpenAI 兼容 API（含国产大模型），未配置时仅返回检索片段
- **企业向设计**：回答仅依据文档、可展示参考来源、无法回答时明确提示，便于审计与合规
- **API + Web**：提供 FastAPI 接口与现代化问答页面，便于集成到 OA、钉钉、企业微信等

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

首次运行会下载嵌入模型（约 400MB），需网络畅通。

### 2. 配置环境（可选）

复制 `.env.example` 为 `.env`，按需修改：

- **不配置 LLM**：仅使用检索结果作为回答（适合内网无外网 API 场景）。
- **配置 LLM**：设置 `LLM_API_BASE`、`LLM_API_KEY`、`LLM_MODEL`，可使用 OpenAI 或国内兼容接口（如 DeepSeek、通义、智谱等）。

**示例配置（DeepSeek）**：
```bash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
```

### 3. 放入知识库文档

将企业文档放入 `knowledge_docs/` 目录（支持子目录），支持格式：`.pdf`、`.docx`、`.txt`、`.md`。项目内已包含一份示例制度 `示例制度-请假与考勤.txt`。

### 4. 启动服务

```bash
python run.py
```

或：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

浏览器访问 **http://localhost:8000** 即可使用问答页面；接口文档见 **http://localhost:8000/docs**。

### 5. 重建索引（更新文档后）

文档增删改后需重建向量索引：

```bash
python scripts/build_index.py
```

或在服务运行中调用 `POST /api/rebuild`，或在 Web 界面点击「重建索引」按钮。

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                     用户界面层                           │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Web 前端    │  │  REST API     │                    │
│  └──────┬───────┘  └──────┬───────┘                    │
└─────────┼──────────────────┼────────────────────────────┘
          │                  │
          └──────────┬───────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  业务逻辑层                              │
│  ┌──────────────────────────────────────────────┐      │
│  │         RAG 问答链（rag/chain.py）            │      │
│  │  - 问题向量化                                  │      │
│  │  - 检索相关文档                                │      │
│  │  - 构建 Prompt                                │      │
│  │  - 调用 LLM 生成回答                           │      │
│  └──────────────────────────────────────────────┘      │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  数据层                                 │
│  ┌──────────────────┐  ┌──────────────────────────┐     │
│  │  文档加载模块    │  │   向量存储模块            │     │
│  │ (knowledge/     │  │  (knowledge/            │     │
│  │  loader.py)     │  │   vector_store.py)      │     │
│  │                 │  │                         │     │
│  │ - PDF 解析      │  │ - Chroma 向量库         │     │
│  │ - Word 解析     │  │ - 嵌入模型管理           │     │
│  │ - TXT/MD 解析   │  │ - 索引构建与检索          │     │
│  └──────────────────┘  └──────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  存储层                                  │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │  知识库文档      │  │   Chroma 向量库           │    │
│  │ (knowledge_docs/)│  │   (chroma_db/)           │    │
│  └──────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 项目结构

```
├── api/
│   └── main.py          # FastAPI 服务与 /api/ask、/api/rebuild
├── knowledge/
│   ├── loader.py        # 文档加载（PDF/Word/TXT/MD）
│   └── vector_store.py  # Chroma 向量库与索引构建
├── rag/
│   └── chain.py        # RAG 检索 + LLM 问答链
├── static/
│   └── index.html      # 问答前端页面
├── scripts/
│   └── build_index.py  # 重建索引脚本
├── knowledge_docs/      # 知识库文档目录（放入你的企业文档）
├── config.py            # 配置（环境变量 / .env）
├── logger_config.py    # 日志配置
├── run.py               # 启动服务
├── requirements.txt
└── .env.example
```

---

## 🔬 RAG 原理

### 什么是 RAG？

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合**信息检索**和**生成式 AI** 的技术范式，解决了大语言模型（LLM）的以下问题：

- **知识更新滞后**：模型训练数据有截止日期，无法获取最新信息
- **幻觉问题**：模型可能生成看似合理但实际错误的信息
- **领域知识不足**：通用模型缺乏企业特定的制度、流程等知识

### RAG 工作流程

```
用户问题
    ↓
向量化查询（Embedding）
    ↓
向量数据库检索（Similarity Search）
    ↓
获取 Top-K 相关文档片段
    ↓
构建 Prompt（问题 + 检索到的上下文）
    ↓
LLM 生成回答
    ↓
返回答案 + 来源引用
```

### 关键技术点

#### 1. 文档切分（Chunking）

**为什么需要切分？**
- 向量数据库对单个文档的检索效率低
- 长文档包含多个主题，切分后能更精准定位
- 减少 LLM 的上下文长度，提高效率

**切分策略**：
- **大小**：默认 500 字符（可配置）
- **重叠**：默认 80 字符，避免关键信息被切分边界截断
- **分隔符**：优先按段落（`\n\n`）、句子（`。`、`！`、`？`）切分

#### 2. 向量化（Embedding）

**原理**：
- 将文本转换为固定维度的数值向量（如 384 维）
- 语义相似的文本，其向量在向量空间中的距离更近
- 使用余弦相似度或欧氏距离衡量相似性

**本系统使用的模型**：
- `paraphrase-multilingual-MiniLM-L12-v2`
- 多语言支持（中英文）
- 本地运行，无需 API Key

#### 3. 向量检索（Retrieval）

**相似度检索**：
- 将用户问题向量化
- 在向量数据库中查找最相似的 K 个文档片段（Top-K）
- 默认返回 Top-8（可配置）

**检索算法**：
- Chroma 使用 `similarity` 搜索
- 可设置相似度阈值（`score_threshold`）过滤低质量结果

#### 4. 上下文增强生成（Augmented Generation）

**Prompt 构建**：
```
系统提示：你是企业内部知识库问答助手...
参考文档：[检索到的文档片段]
用户问题：[用户的实际问题]
```

**生成策略**：
- LLM 基于参考文档生成回答
- 要求仅依据文档内容，不编造信息
- 若文档不足以回答，明确说明

---

## 🤖 大模型集成

### DeepSeek API 集成状态

系统**已完整集成大语言模型（LLM）**，当前配置使用 **DeepSeek API**：

```bash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
```

### RAG 完整流程（含 LLM）

```
用户问题
    ↓
【步骤1】向量检索（本地）
    ├─ 问题向量化（HuggingFace Embedding）
    ├─ 在 Chroma 向量库中检索 Top-K 相关文档片段
    └─ 获取参考文档上下文
    ↓
【步骤2】构建 Prompt
    ├─ 系统提示词（角色定义、回答规则）
    ├─ 参考文档（检索到的文档片段）
    └─ 用户问题
    ↓
【步骤3】调用 DeepSeek API（云端）
    ├─ 发送 HTTP 请求到 https://api.deepseek.com/v1/chat/completions
    ├─ 使用配置的 API Key 认证
    └─ 模型：deepseek-chat
    ↓
【步骤4】生成回答
    ├─ DeepSeek 基于参考文档生成回答
    ├─ 解析响应
    └─ 返回答案 + 来源引用
```

### 两种工作模式

#### 模式 1：完整 RAG（已启用）✅

**条件**：已配置 `LLM_API_BASE` 和 `LLM_API_KEY`

**流程**：
1. 向量检索 → 获取相关文档
2. 构建 Prompt → 包含参考文档和问题
3. **调用 DeepSeek API** → 生成回答
4. 返回生成的回答 + 来源引用

**优势**：
- ✅ 回答更自然、流畅
- ✅ 能归纳总结多个文档片段
- ✅ 符合企业文档的表述风格

#### 模式 2：仅检索模式（降级）

**条件**：未配置 LLM API 或初始化失败

**流程**：
1. 向量检索 → 获取相关文档
2. 直接返回检索到的文档片段（未经过 LLM 处理）

**使用场景**：
- 内网环境，无法访问外网 API
- 测试阶段，仅验证检索功能
- 成本控制，避免 API 调用费用

### 切换不同的 LLM 提供商

#### 使用 OpenAI

```bash
# .env
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o-mini
```

#### 使用通义千问

```bash
# .env
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=qwen-turbo
```

#### 使用智谱 AI

```bash
# .env
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=xxx
LLM_MODEL=glm-4
```

**注意**：所有配置都使用 OpenAI 兼容的 API 格式，只需修改 `base_url`、`api_key` 和 `model` 即可。

### 安全与隐私

**数据流向**：
```
企业文档（本地）
    ↓
向量化（本地，HuggingFace）
    ↓
向量库（本地，Chroma）
    ↓
检索（本地）
    ↓
参考文档片段（本地）
    ↓
【仅发送】→ DeepSeek API（云端）
    ├─ 参考文档片段（已切分，不包含完整文档）
    ├─ 用户问题
    └─ 系统提示词
    ↓
生成的回答（云端 → 本地）
```

**安全措施**：
- ✅ 完整文档不离开本地
- ✅ 仅发送检索到的相关片段（Top-K）
- ✅ API Key 存储在 `.env`，不提交到代码仓库
- ✅ 可配置为完全本地模式（不调用 API）

---

## 🔧 核心模块详解

### 1. 文档加载模块 (`knowledge/loader.py`)

#### 支持格式

| 格式 | 加载方式 | 说明 |
|------|---------|------|
| `.pdf` | `PyPDFLoader` | LangChain 标准 PDF 加载器 |
| `.txt` | `path.read_text(encoding="utf-8")` | 直接读取，支持 UTF-8/GBK |
| `.md` | 同上 | Markdown 文件 |
| `.docx` | `python-docx` | 新版 Word 格式 |
| `.doc` | `unstructured.partition_doc` | 旧版 Word（需额外依赖） |

#### 实现细节

**文本文件加载**：
```python
def _load_txt_or_md(path: Path) -> list[Document]:
    try:
        text = path.read_text(encoding="utf-8")
        return [Document(page_content=text, metadata={...})]
    except UnicodeDecodeError:
        # 回退到 GBK 编码
        text = path.read_text(encoding="gbk")
        ...
```

**Word 文件加载**：
- `.docx`：使用 `python-docx` 提取段落文本
- `.doc`：使用 `unstructured` 库（需要安装 `unstructured[local]`）

### 2. 向量存储模块 (`knowledge/vector_store.py`)

#### 嵌入模型管理（单例模式）

```python
_embeddings_instance = None

def _get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is not None:
        return _embeddings_instance
    # 首次加载
    _embeddings_instance = HuggingFaceEmbeddings(...)
    return _embeddings_instance
```

**优势**：
- 进程内只加载一次模型（约 400MB）
- 后续请求复用，避免重复加载

#### 文档切分

**RecursiveCharacterTextSplitter**：
- 按分隔符优先级切分：`\n\n` → `\n` → `。` → `！` → `？` → `；` → ` ` → ``
- 保证块大小不超过 `chunk_size`
- 相邻块重叠 `chunk_overlap` 字符

#### 向量库构建

```python
vector_store = Chroma.from_documents(
    documents=splits,           # 切分后的文档列表
    embedding=embeddings,       # 嵌入模型
    collection_name="enterprise_knowledge",
    persist_directory=str(persist_dir),  # 持久化目录
)
```

### 3. RAG 问答链 (`rag/chain.py`)

#### 问答流程

```python
def answer_question(question: str, top_k: int = None):
    # 1. 获取向量库
    vector_store = get_vector_store()
    
    # 2. 检索相关文档
    retriever = vector_store.as_retriever(...)
    docs = retriever.invoke(question)
    
    # 3. 格式化上下文
    context = _format_docs(docs)
    
    # 4. 构建 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", f"参考文档：\n{context}\n\n用户问题：{question}"),
    ])
    
    # 5. 调用 LLM
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(question)
    
    # 6. 返回结果
    return {"answer": answer, "sources": [...], ...}
```

#### 系统提示词设计

**核心原则**：
1. **优先依据文档**：只要文档中有相关内容，必须作答
2. **明确无法回答的条件**：仅当文档为空或完全无关时才说无法回答
3. **引用原文**：制度、流程、数字等按原文表述
4. **不编造信息**：文档中不存在的内容不能编造

### 4. API 服务层 (`api/main.py`)

#### FastAPI 路由

**问答接口**：
```python
@app.post("/api/ask", response_model=QuestionResponse)
def api_ask(req: QuestionRequest):
    result = answer_question(req.question, top_k=req.top_k)
    return QuestionResponse(...)
```

**重建索引接口**：
```python
@app.post("/api/rebuild")
def api_rebuild():
    rebuild_index()
    return {"status": "ok", "message": "知识库索引已重建"}
```

#### 启动预热

**目的**：在服务启动时预加载嵌入模型和向量库，避免首条请求卡顿

```python
@app.on_event("startup")
def startup_warmup():
    get_vector_store()  # 触发模型加载
```

---

## ⚙️ 配置说明

### 环境变量配置（`.env`）

#### 知识库路径
```bash
KNOWLEDGE_BASE_PATH=knowledge_docs      # 文档目录
PERSIST_DIRECTORY=chroma_db              # 向量库持久化目录
```

#### 嵌入模型
```bash
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
# 本地模型，无需 API Key
```

#### LLM 配置（可选）
```bash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
```

#### RAG 参数
```bash
CHUNK_SIZE=500          # 文本块大小
CHUNK_OVERLAP=80        # 块重叠长度
TOP_K=8                 # 检索返回数量
```

#### 服务配置
```bash
HOST=0.0.0.0
PORT=8000
```

### 配置优先级

1. 环境变量（`.env` 文件）
2. 系统环境变量
3. 代码默认值

---

## 📡 API 说明

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ask` | POST | 提交问题，返回 RAG 答案与参考来源 |
| `/api/rebuild` | POST | 从知识库目录重建向量索引 |
| `/health` | GET | 健康检查 |

**请求示例（/api/ask）**：

```json
{"question": "请假流程是怎样的？", "top_k": 5}
```

**响应示例**：

```json
{
  "answer": "根据制度，员工在 OA 或钉钉提交请假申请…",
  "sources": [{"filename": "示例制度-请假与考勤.txt", "source": "...", "content": "…"}],
  "retrieved_only": false
}
```

---

## ⚡ 性能优化

### 1. 单例模式

**嵌入模型**：
- 进程内只加载一次（约 400MB）
- 后续请求复用，避免重复加载

**向量库**：
- 全局单例，避免重复连接

**LLM 客户端**：
- 单例管理，复用连接

### 2. 启动预热

- 服务启动时预加载模型和向量库
- 首条请求无需等待加载

### 3. 向量库持久化

- Chroma 将向量数据持久化到磁盘
- 重启服务无需重新构建索引

### 4. 检索优化

- 使用 Top-K 检索，避免全量扫描
- 可设置相似度阈值过滤低质量结果

### 5. 日志管理

- 按天轮转，避免日志文件过大
- 保留 7 天历史日志

---

## 🔨 扩展与定制

### 1. 添加新的文档格式

在 `knowledge/loader.py` 中添加：

```python
def _load_custom_format(path: Path) -> list[Document]:
    # 实现加载逻辑
    text = extract_text_from_custom_format(path)
    return [Document(page_content=text, metadata={...})]

LOADER_MAP[".custom"] = _load_custom_format
```

### 2. 更换嵌入模型

在 `.env` 中修改：
```bash
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

**注意**：更换模型后需重建索引。

### 3. 自定义 Prompt

修改 `rag/chain.py` 中的 `SYSTEM_PROMPT`：
```python
SYSTEM_PROMPT = """你的自定义提示词..."""
```

### 4. 添加认证

在 `api/main.py` 中添加：
```python
from fastapi import Depends, HTTPException, Header

async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401)
    return x_api_key

@app.post("/api/ask", dependencies=[Depends(verify_token)])
def api_ask(...):
    ...
```

### 5. 集成到企业系统

**钉钉/企业微信**：
- 将 `/api/ask` 封装为 HTTP 接口
- 在机器人回调中调用

**OA 系统**：
- 提供 iframe 嵌入
- 或通过 SSO 集成

---

## ❓ 常见问题

### Q1: 为什么回答总是说"无法完整回答"？

**可能原因**：
1. 向量库未重建，索引中没有相关文档
2. 检索到的文档片段与问题不匹配
3. LLM 过于保守

**解决方案**：
1. 点击「重建索引」或运行 `python scripts/build_index.py`
2. 检查 `knowledge_docs/` 下是否有相关文档
3. 调整 `TOP_K` 增加检索数量
4. 检查系统提示词是否过于严格

### Q2: 如何提高检索准确度？

1. **优化文档切分**：调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP`
2. **增加检索数量**：提高 `TOP_K`（如 10-15）
3. **更换嵌入模型**：使用更强大的模型（如 `all-mpnet-base-v2`）
4. **文档质量**：确保文档结构清晰、内容完整

### Q3: 支持哪些 LLM？

- OpenAI（GPT-4、GPT-3.5）
- DeepSeek（推荐，性价比高）
- 通义千问、智谱、Moonshot 等 OpenAI 兼容 API

### Q4: 如何更新知识库？

1. 将新文档放入 `knowledge_docs/`
2. 调用 `POST /api/rebuild` 或运行 `python scripts/build_index.py`
3. 等待索引重建完成

### Q5: 向量库占用多少空间？

- 取决于文档数量和切分后的块数
- 每个向量约 1.5KB（384 维 × 4 字节）
- 1000 个文档块约占用 1.5MB（不含元数据）

### Q6: 如何验证 DeepSeek API 是否工作？

**方法 1：查看日志**
- 启动服务时，如果看到 LLM 初始化成功的日志，说明已连接

**方法 2：测试问答**
- 如果回答自然流畅、有归纳总结，说明 DeepSeek 在工作
- 检查 API 返回的 `retrieved_only: false` 表示使用了 LLM

**方法 3：检查网络请求**
- 打开浏览器开发者工具（F12）→ Network 标签
- 提交问题时查看响应时间（> 2 秒说明调用了 API）

---

## 🏢 企业部署建议

1. **权限与审计**：在网关或 API 层增加认证（如 JWT、API Key），并对 `/api/ask`、`/api/rebuild` 做访问日志与审计。
2. **定时重建索引**：用计划任务定期执行 `scripts/build_index.py` 或调用 `POST /api/rebuild`，使新文档及时生效。
3. **内网部署**：嵌入与向量检索均在本地完成；仅在使用云端 LLM 时需访问外网，也可改用内网部署的开源或国产大模型 API。
4. **日志**：日志写入 `logs/` 目录，按天轮转，便于排查与合规留痕。

---

## 📦 依赖与版本

- Python 3.10+
- LangChain、Chroma、sentence-transformers、FastAPI 等见 `requirements.txt`

嵌入模型默认：`paraphrase-multilingual-MiniLM-L12-v2`（多语言），可在 `.env` 中通过 `EMBEDDING_MODEL` 更换。

---

## 📄 许可证

本项目仅供学习与企业内部使用，请遵守各依赖组件的许可协议。

---

**文档版本**：v2.0  
**最后更新**：2026-02-13
