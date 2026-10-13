# Database Contract

## 1. 文档职责

本文档是项目 SQLite 表结构和 Chroma 数据组织的唯一契约来源。

- 功能范围以 `docs/MVP.md` 为准。
- 接口定义以 `docs/API_CONTRACT.md` 为准。
- 技术栈和系统架构以 `docs/TECH_DESIGN.md` 为准。
- 数据库结构变更时先更新本文档，再修改代码。
- `backend/app/db.py` 必须实现本文档定义的约束。

## 2. 存储职责

| 数据 | 存储位置 | 说明 |
| --- | --- | --- |
| 原始文档 | `data/uploads/` | 用户上传的 TXT、MD 和 MARKDOWN 文件 |
| 业务数据 | `data/app.db` | SQLite 数据库 |
| chunk 和向量 | `data/chroma/` | Chroma 持久化数据 |

SQLite 保存业务记录、会话和来源关系。Chroma 保存 chunk 文本、embedding 和检索元数据。

## 3. 通用约定

- 主键使用不透明字符串。
- `document_id` 使用 UUID hex 字符串。
- `chunk_id` 使用 `{document_id}:{chunk_index}`。
- 时间使用 ISO 8601 UTC 字符串，例如 `2026-10-03T12:00:00+00:00`。
- 文件路径相对于 `data/` 保存，例如 `uploads/{document_id}.md`。
- 每次建立 SQLite 连接后必须启用外键：`PRAGMA foreign_keys = ON`。
- 每次建立 SQLite 连接后设置写入等待时间：`PRAGMA busy_timeout = 5000`。
- 数据库字段不直接等同于 API 字段。例如 `file_path` 仅供内部使用，不通过 API 返回。

文档状态：

| 状态 | 含义 |
| --- | --- |
| `pending` | 文件已保存，等待处理 |
| `processing` | 正在解析、切分和写入向量库 |
| `ready` | 已可以检索 |
| `failed` | 处理失败，可以查看 `error_message` |

## 4. SQLite 数据表

### 4.1 documents

保存上传文档的元数据和处理状态。

| 字段 | SQLite 类型 | 可空 | 默认值 | 约束和说明 |
| --- | --- | --- | --- | --- |
| `id` | TEXT | 否 | 无 | 主键 |
| `filename` | TEXT | 否 | 无 | 用户上传时的原始文件名 |
| `file_path` | TEXT | 否 | 无 | 相对于 `data/` 的文件路径，必须唯一 |
| `status` | TEXT | 否 | 无 | `pending`、`processing`、`ready`、`failed` |
| `chunk_count` | INTEGER | 否 | `0` | 必须大于等于 `0` |
| `error_message` | TEXT | 是 | `NULL` | 处理失败原因 |
| `created_at` | TEXT | 否 | 无 | 创建时间 |
| `updated_at` | TEXT | 否 | 无 | 最后更新时间 |

目标表结构：

```sql
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'processing', 'ready', 'failed')
    ),
    chunk_count INTEGER NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_created_at
ON documents (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_status
ON documents (status);
```

不变量：

- `filename` 不唯一，相同文件名可以对应多个不同 `document_id`。
- `file_path` 必须唯一，磁盘文件不能被其他文档记录复用。
- `ready` 状态的 `chunk_count` 必须大于 `0`。
- `failed` 状态的 `error_message` 不得为空。
- 非 `failed` 状态的 `error_message` 必须为 `null`。

### 4.2 conversations

保存一次问答会话。

| 字段 | SQLite 类型 | 可空 | 默认值 | 约束和说明 |
| --- | --- | --- | --- | --- |
| `id` | TEXT | 否 | 无 | 主键 |
| `title` | TEXT | 否 | 无 | 会话标题 |
| `created_at` | TEXT | 否 | 无 | 创建时间 |
| `updated_at` | TEXT | 否 | 无 | 最后更新时间 |

目标表结构：

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
ON conversations (updated_at DESC);
```

### 4.3 messages

保存会话中的用户消息和助手消息。

| 字段 | SQLite 类型 | 可空 | 默认值 | 约束和说明 |
| --- | --- | --- | --- | --- |
| `id` | TEXT | 否 | 无 | 主键 |
| `conversation_id` | TEXT | 否 | 无 | 外键，指向 `conversations.id` |
| `role` | TEXT | 否 | 无 | `user` 或 `assistant` |
| `content` | TEXT | 否 | 无 | 消息正文 |
| `created_at` | TEXT | 否 | 无 | 创建时间 |

目标表结构：

```sql
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
ON messages (conversation_id, created_at, id);
```

删除会话时，其消息一并删除。

### 4.4 message_sources

保存助手消息引用的文档 chunk。

| 字段 | SQLite 类型 | 可空 | 默认值 | 约束和说明 |
| --- | --- | --- | --- | --- |
| `id` | TEXT | 否 | 无 | 主键 |
| `message_id` | TEXT | 否 | 无 | 外键，指向 `messages.id` |
| `document_id` | TEXT | 否 | 无 | 外键，指向 `documents.id` |
| `chunk_id` | TEXT | 否 | 无 | Chroma 中的 chunk ID |
| `source` | TEXT | 否 | 无 | 回答生成时保存的来源名称快照 |
| `chunk_index` | INTEGER | 否 | 无 | 原文档中的 chunk 顺序，从 `0` 开始 |
| `score` | REAL | 否 | 无 | 检索分数 |

目标表结构：

```sql
CREATE TABLE IF NOT EXISTS message_sources (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    score REAL NOT NULL,
    FOREIGN KEY (message_id)
        REFERENCES messages (id)
        ON DELETE CASCADE,
    FOREIGN KEY (document_id)
        REFERENCES documents (id)
        ON DELETE CASCADE,
    UNIQUE (message_id, chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_message_sources_message
ON message_sources (message_id);

CREATE INDEX IF NOT EXISTS idx_message_sources_document
ON message_sources (document_id);
```

删除消息或文档时，相关来源记录一并删除。

## 5. 表关系

```text
conversations 1
    |
    +-- N messages
              |
              +-- N message_sources
                          |
                          +-- 1 documents
```

规则：

- 一个会话包含多条消息。
- 一个用户问题对应一条 `user` 消息。
- 一个助手回答对应一条 `assistant` 消息。
- 一条助手消息可以引用多个文档 chunk。
- Chroma chunk 通过 `chunk_id` 与 `message_sources` 关联。

## 6. 状态流转

```text
pending
  -> processing
  -> ready

pending
  -> processing
  -> failed

任何状态
  -> 删除文档
```

处理过程中：

- 上传成功时创建 `pending` 记录。
- 开始解析前更新为 `processing`。
- 成功写入全部 chunk 后更新为 `ready`，并写入 `chunk_count`。
- 处理失败时更新为 `failed`，并写入 `error_message`。

MVP 暂不实现失败重试。失败文档可以直接删除后重新上传。

## 7. Chroma Contract

Chroma 使用一个 collection：

```text
document_chunks
```

每条记录表示一个文档 chunk：

| 数据 | 说明 |
| --- | --- |
| Chroma ID | `chunk_id` |
| document | chunk 原文 |
| embedding | 由统一 Embedding 模型生成 |
| `document_id` | 所属文档 ID |
| `chunk_id` | chunk 唯一标识 |
| `source` | 来源文件名 |
| `chunk_index` | chunk 在原文档中的顺序 |

约束：

- 只有 `ready` 文档的 chunk 可以进入检索流程。
- 同一 collection 中的 embedding 必须来自相同模型和相同维度。
- 写入 Chroma 后再将文档状态更新为 `ready`。
- 文档处理失败时，必须删除本次已经写入的 Chroma chunk。
- 删除文档时，先按 `document_id` 删除 Chroma chunk，再删除 SQLite 数据。

## 8. 数据一致性

- 文件写入成功和 SQLite 记录创建必须作为同一个业务操作处理。
- 如果 SQLite 写入失败，必须删除已经保存的原始文件。
- 并发上传使用独立 SQLite 连接，写入锁等待最多 5 秒，不使用应用级全局锁。
- 删除文档时，依次处理原始文件、Chroma chunk 和 SQLite 记录。
- 如果 Chroma 删除失败，不应将数据库记录报告为删除成功。

## 9. 备份和迁移

备份时必须同时保留：

```text
data/app.db
data/chroma/
data/uploads/
```

数据库结构发生变化时：

1. 更新本文档中的表结构和不变量。
2. 增加对应的迁移步骤。
3. 修改 `backend/app/db.py`。
4. 增加或更新数据库测试。

MVP 使用 `CREATE TABLE IF NOT EXISTS` 初始化新数据库，不自动修改已有表结构。后续字段变更需要显式迁移。

当前仓库提供一次性迁移函数，用于把早期没有 `UNIQUE` 和 `CHECK` 约束的 `documents` 表转换为当前结构：

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.db import migrate_documents_constraints; migrate_documents_constraints()"
```
