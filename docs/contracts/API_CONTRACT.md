# API Contract

## 1. 文档职责

本文档是项目 HTTP API 的唯一契约来源，定义请求、响应、错误、状态码和 SSE 事件。

- 功能范围以 `docs/product/MVP.md` 为准。
- 技术栈、架构和数据模型以 `docs/architecture/TECH_DESIGN.md` 为准。
- API 调整时先更新本文档，再修改后端和前端。
- FastAPI 生成的 `/docs` 和 `/openapi.json` 必须与本文档一致。

MVP 接口实现状态：

| 接口 | 状态 |
| --- | --- |
| `GET /health` | 已实现 |
| `POST /api/documents` | 已实现 |
| `GET /api/documents` | 已实现 |
| `GET /api/documents/{document_id}` | 待实现 |
| `DELETE /api/documents/{document_id}` | 待实现 |
| `POST /api/chat/stream` | 待实现 |
| `GET /api/conversations/{conversation_id}` | 待实现 |

## 2. 通用约定

开发环境后端地址：

```text
http://127.0.0.1:8000
```

开发环境前端通过 Vite 代理访问后端，前端代码使用相对路径：

```text
GET /health
POST /api/documents
```

通用规则：

- 除文件上传外，请求和响应使用 `application/json; charset=utf-8`。
- ID 是不透明的字符串，前端不得解析 ID 内部结构。
- 时间使用 ISO 8601 UTC 格式，例如 `2026-10-03T12:00:00+00:00`。
- MVP 不包含登录和权限认证。
- 未找到资源返回 `404`。
- 请求字段不合法返回 `422`。

通用错误响应：

```json
{
  "detail": "Error description"
}
```

## 3. 通用模型

### Document

```json
{
  "id": "5f7d9b3f4c1e4d2ca5b1d0e8f3a7b6c9",
  "filename": "guide.md",
  "status": "pending",
  "chunk_count": 0,
  "error_message": null,
  "created_at": "2026-10-03T12:00:00+00:00",
  "updated_at": "2026-10-03T12:00:00+00:00"
}
```

字段说明：

| 字段 | 类型 | 可空 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 否 | 文档唯一标识 |
| `filename` | string | 否 | 用户上传时的原始文件名 |
| `status` | string | 否 | `pending`、`processing`、`ready` 或 `failed` |
| `chunk_count` | integer | 否 | 已生成的 chunk 数量 |
| `error_message` | string | 是 | 处理失败原因，成功时为 `null` |
| `created_at` | string | 否 | 创建时间 |
| `updated_at` | string | 否 | 最后更新时间 |

### MessageSource

```json
{
  "document_id": "5f7d9b3f4c1e4d2ca5b1d0e8f3a7b6c9",
  "chunk_id": "5f7d9b3f4c1e4d2ca5b1d0e8f3a7b6c9:3",
  "source": "guide.md",
  "chunk_index": 3,
  "score": 0.82
}
```

## 4. 健康检查

### GET /health

响应：`200 OK`

```json
{
  "status": "ok"
}
```

## 5. 文档接口

### POST /api/documents

上传并创建文档。

请求类型：

```text
multipart/form-data
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | File | 是 | `.txt`、`.md` 或 `.markdown` 文件 |

上传规则：

- 单个文件最大 `10 MiB`。
- 同名文件允许重复上传，每次创建独立文档，不覆盖已有文件。
- 接口只保存原始文件并创建 `pending` 记录，不执行解析、切分或向量化。

成功响应：`201 Created`

响应体为 `Document`：

```json
{
  "id": "5f7d9b3f4c1e4d2ca5b1d0e8f3a7b6c9",
  "filename": "guide.md",
  "status": "pending",
  "chunk_count": 0,
  "error_message": null,
  "created_at": "2026-10-03T12:00:00+00:00",
  "updated_at": "2026-10-03T12:00:00+00:00"
}
```

错误响应：

| 状态码 | 场景 |
| --- | --- |
| `400` | 文件为空或扩展名不支持 |
| `413` | 文件超过 `10 MiB` |
| `422` | 缺少 `file` 字段 |
| `507` | 文件存储不可用或磁盘空间不足 |

### GET /api/documents

获取全部文档，按创建时间倒序排列。

成功响应：`200 OK`

```json
[
  {
    "id": "5f7d9b3f4c1e4d2ca5b1d0e8f3a7b6c9",
    "filename": "guide.md",
    "status": "pending",
    "chunk_count": 0,
    "error_message": null,
    "created_at": "2026-10-03T12:00:00+00:00",
    "updated_at": "2026-10-03T12:00:00+00:00"
  }
]
```

### GET /api/documents/{document_id}

获取指定文档。

成功响应：`200 OK`，响应体为 `Document`。

错误响应：

| 状态码 | 场景 |
| --- | --- |
| `404` | 文档不存在 |

### DELETE /api/documents/{document_id}

删除指定文档及其关联的文件和向量数据。

成功响应：`204 No Content`

错误响应：

| 状态码 | 场景 |
| --- | --- |
| `404` | 文档不存在 |

## 6. 问答接口

### POST /api/chat/stream

提交问题并通过 SSE 返回流式回答。

请求类型：

```text
application/json
```

请求体：

```json
{
  "question": "项目的目标是什么？",
  "conversation_id": null
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | string | 是 | 非空问题文本 |
| `conversation_id` | string | 否 | 为空时创建新会话 |

成功响应：

```text
200 OK
Content-Type: text/event-stream
```

SSE 事件：

```text
event: message
data: {"conversation_id":"...","message_id":"...","delta":"答案片段"}

event: sources
data: {"conversation_id":"...","message_id":"...","sources":[...]}

event: done
data: {"conversation_id":"...","message_id":"..."}

event: error
data: {"detail":"错误信息"}
```

说明：

- 流开始前发生的参数错误使用普通 JSON 错误响应。
- 流开始后的错误使用 `error` 事件。
- 前端只依赖事件名和 JSON 数据，不解析记录分隔符。

### GET /api/conversations/{conversation_id}

获取会话及消息记录。

成功响应：`200 OK`

```json
{
  "id": "conversation-id",
  "title": "项目的目标是什么？",
  "created_at": "2026-10-03T12:00:00+00:00",
  "updated_at": "2026-10-03T12:00:00+00:00",
  "messages": [
    {
      "id": "message-id",
      "role": "user",
      "content": "项目的目标是什么？",
      "created_at": "2026-10-03T12:00:00+00:00",
      "sources": []
    },
    {
      "id": "assistant-message-id",
      "role": "assistant",
      "content": "项目目标是构建一个简单 RAG 应用。",
      "created_at": "2026-10-03T12:00:01+00:00",
      "sources": [
        {
          "document_id": "document-id",
          "chunk_id": "document-id:3",
          "source": "guide.md",
          "chunk_index": 3,
          "score": 0.82
        }
      ]
    }
  ]
}
```

错误响应：

| 状态码 | 场景 |
| --- | --- |
| `404` | 会话不存在 |
