# 简单 RAG 技术设计

## 1. 文档职责

本文档是项目技术选型、系统架构、接口契约和数据模型的唯一来源。

- 功能范围以 `docs/MVP.md` 为准。
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

数据存储位置：

- 原始文件保存在 `data/uploads/`。
- Chroma 数据保存在 `data/chroma/`。
- SQLite 数据库保存在 `data/app.db`。
- API 密钥通过环境变量读取，不写入仓库。

## 5. 接口草案

```text
GET    /health
POST   /api/documents
GET    /api/documents
GET    /api/documents/{document_id}
DELETE /api/documents/{document_id}
POST   /api/chat/stream
GET    /api/conversations/{conversation_id}
```

`POST /api/chat/stream` 请求示例：

```json
{
  "question": "项目的目标是什么？",
  "conversation_id": null
}
```

SSE 至少包含以下事件：

```text
message       回答文本片段
sources       来源列表
done          流式回答结束
error         错误信息
```

## 6. 数据模型

### 6.1 SQLite

`documents`

```text
id
filename
file_path
status
chunk_count
error_message
created_at
updated_at
```

`conversations`

```text
id
title
created_at
updated_at
```

`messages`

```text
id
conversation_id
role
content
created_at
```

`message_sources`

```text
id
message_id
document_id
chunk_id
source
chunk_index
score
```

### 6.2 Chroma

每个 chunk 至少保存：

```text
文本内容
embedding
document_id
chunk_id
source
chunk_index
```
