# 简单 RAG 技术设计

## 1. 文档职责

本文档是项目技术选型和系统架构的唯一来源。

- 功能范围以 `docs/product/MVP.md` 为准。
- API 定义以 `docs/contracts/API_CONTRACT.md` 为准。
- 数据库结构以 `docs/contracts/DATABASE_CONTRACT.md` 为准。
- 开发规则以根目录 `AGENTS.md` 为准。
- 本文档只描述如何实现，不扩展 MVP 功能范围。

## 2. 技术栈

- 前端：Vue 3 + Vite
- 后端：FastAPI + Uvicorn
- RAG：LangChain
- 向量存储：Chroma
- 关系数据库：SQLite
- 流式回答：SSE

## 3. 技术约束

- 使用 Vite 构建前端，不引入 Webpack。
- 第一版不使用 Pinia。出现真实的跨页面共享状态后再评估。
- 前后端保持为同一仓库中的两个独立应用，不拆微服务。
- 不引入 Redis、Celery、MySQL、PostgreSQL、Kafka。
- 不引入 Agent、工具调用、LangGraph 或多步规划。
- 不为尚未出现的需求增加抽象和配置项。

## 4. 系统架构

```text
浏览器
  -> Vue 3 + Vite
  -> FastAPI
  -> LangChain
  -> Chroma
  -> SQLite
  -> LLM 和 Embedding 服务
```

API 密钥通过环境变量读取，不写入仓库。具体存储位置、数据结构、约束和一致性要求见 [`DATABASE_CONTRACT.md`](../contracts/DATABASE_CONTRACT.md)。

## 5. 接口契约

后端对外接口由 REST API 和 SSE 流式接口组成。

- `/health` 用于服务健康检查。
- `/api/documents` 用于文档上传、查询和删除。
- `/api/chat/stream` 使用 SSE 流式返回问答结果。
- `/api/conversations/{conversation_id}` 用于查询会话记录。

文档上传使用 `multipart/form-data`，其他普通接口使用 JSON。MVP 暂不提供登录和权限认证，所有业务接口统一使用 `/api` 前缀，暂不引入 API 版本号。

开发环境中，前端通过 Vite 将 `/health` 和 `/api` 请求代理到 FastAPI。生产部署时，需要通过反向代理或后端静态托管提供相同路径。

文档上传请求只执行文件持久化和 `pending` 记录创建，不执行解析、切分、Embedding 或 LLM 调用。单个文件最大为 `10 MiB`，服务端按块读取并累计大小，超出限制时删除不完整文件并返回 `413`。

接口的详细请求、响应、状态码、错误结构和 SSE 事件以 [`API_CONTRACT.md`](../contracts/API_CONTRACT.md) 为准。

## 6. 数据存储

SQLite 表结构、字段约束、表关系、状态流转、Chroma metadata 和数据一致性要求以 [`DATABASE_CONTRACT.md`](../contracts/DATABASE_CONTRACT.md) 为准。

## 7. 接口与数据存储映射

本节说明接口与数据存储之间的关系。接口的请求和响应格式以 [`API_CONTRACT.md`](../contracts/API_CONTRACT.md) 为准，表结构、字段约束和删除规则以 [`DATABASE_CONTRACT.md`](../contracts/DATABASE_CONTRACT.md) 为准。

| 接口 | 主要操作 | 涉及存储 |
| --- | --- | --- |
| `GET /health` | 服务健康检查 | 不访问业务数据 |
| `POST /api/documents` | 保存原始文件并创建文档记录 | `data/uploads/`、`documents` |
| `GET /api/documents` | 查询文档列表 | `documents` |
| `GET /api/documents/{document_id}` | 查询单个文档 | `documents` |
| `DELETE /api/documents/{document_id}` | 删除原始文件、文档和向量数据 | `data/uploads/`、`documents`、Chroma |
| `POST /api/chat/stream` | 检索 chunk、生成回答并保存消息与来源 | `conversations`、`messages`、`message_sources`、`documents`、Chroma、LLM |
| `GET /api/conversations/{conversation_id}` | 查询会话、消息和引用来源 | `conversations`、`messages`、`message_sources`、`documents` |

关键业务过程的存储操作：

```text
上传文档
-> 原始文件写入 data/uploads/
-> documents 插入 pending 记录

文档处理
-> documents 从 pending 更新为 processing
-> 切分文本并写入 Chroma
-> documents 更新为 ready，并保存 chunk_count

文档处理失败
-> documents 更新为 failed，并保存 error_message
-> 清理本次已经写入的 Chroma chunk

删除文档
-> 删除原始文件
-> 删除 Chroma chunk
-> 删除 documents 记录
-> 级联删除 message_sources

流式问答
-> 创建或读取 conversations
-> 写入 user message
-> 从 Chroma 检索相关 chunk
-> 生成回答
-> 写入 assistant message
-> 写入 message_sources
```

跨存储操作必须遵守以下规则：

- 文件保存和 SQLite 记录创建属于同一个业务操作，SQLite 写入失败时删除已保存文件。
- 只有成功写入 Chroma 后，文档才能更新为 `ready`。
- 删除文档时，只有原始文件、Chroma 和 SQLite 数据均处理成功后，才能向前端报告删除成功。
- 聊天回答和来源记录必须同时保存，不能只保存助手回答而丢失引用关系。
