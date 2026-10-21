# 配置说明

## 1. 文档职责

本文档定义开发、测试和未来部署环境中的配置来源、变量名称和密钥处理规则。

当前实现只直接读取 `SIMPLE_RAG_DATA_DIR`。其他变量是后续 LLM、Embedding 和部署功能的预留配置。

## 2. 配置优先级

目标优先级：

```text
显式环境变量
-> .env 文件
-> 应用默认值
```

当前 Python 代码尚未统一加载 `.env`，因此开发时优先使用 PowerShell 环境变量。实现配置加载后，应保持上述优先级。

## 3. 当前配置

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `SIMPLE_RAG_DATA_DIR` | 否 | 项目 `data/` | SQLite、上传文件和 Chroma 的数据根目录 |

示例：

```powershell
$env:SIMPLE_RAG_DATA_DIR = 'D:\vue3-program\simple-rag\data'
```

测试必须使用临时目录，不能写入真实 `data/`。

## 4. LLM 配置

以下变量已决策，待问答功能实现：

```text
LLM_PROVIDER=openai-compatible
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
LLM_TIMEOUT_SECONDS=60
```

MVP 只支持一个 OpenAI-compatible Chat Completions 服务，不在代码中固定供应商和模型。

## 5. Embedding 配置

以下变量已决策，待文档摄取功能实现：

```text
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DIMENSION=512
```

Embedding 使用本地模型，不需要 API Key 或 Base URL。未来替换为远程 Provider 时必须先更新本文档和 ADR。

Embedding 模型变更时必须同时更新向量维度、重建 Chroma collection，并记录迁移方式。

## 6. 上传和处理配置

当前上传限制：

```text
允许扩展名：.txt、.md、.markdown
最大文件大小：10 MiB
```

处理参数：

```text
CHUNK_SIZE=800
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=4
```

详细切分和检索行为以 `docs/ai/RAG_PIPELINE.md` 为准。

## 7. 密钥和安全

- `.env`、API Key 和 Token 不得提交到 Git。
- `.env.example` 只能包含变量名、说明和假值。
- 日志不得输出 API Key、完整请求头或敏感文档内容。
- 前端不得包含 LLM 或 Embedding 密钥。
- 生产环境优先使用平台 Secret 管理，而不是明文 `.env`。

## 8. 环境差异

| 环境 | 数据目录 | 模型 | 日志 |
| --- | --- | --- | --- |
| 开发 | 本地 `data/` | 可使用开发模型 | 详细日志 |
| 测试 | 临时目录 | 测试替身或低成本模型 | 测试输出 |
| 生产 | 持久化卷 | 固定模型版本 | 结构化日志 |

## 9. 配置验收

- 缺少必填配置时应用启动失败并给出明确错误。
- 配置错误不会退化为静默使用默认密钥或默认模型。
- 测试可以完全隔离数据和外部模型。
- `.env.example` 与实际支持的变量保持一致。
