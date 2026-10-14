# 文档索引

## 文档职责

本目录按“需求、前端、架构、接口、数据、RAG、质量、运维”划分文档。每类信息只保留一个权威来源，其他文档通过链接引用。

| 文档 | 职责 | 状态 |
| --- | --- | --- |
| [MVP.md](./product/MVP.md) | 功能范围、用户流程和验收标准 | 当前有效 |
| [FRONTEND_SPEC.md](./engineering/FRONTEND_SPEC.md) | 页面、组件、交互状态和前端验收标准 | 当前有效 |
| [TECH_DESIGN.md](./architecture/TECH_DESIGN.md) | 技术栈、系统架构和接口与存储映射 | 当前有效 |
| [API_CONTRACT.md](./contracts/API_CONTRACT.md) | 请求、响应、错误和 SSE 事件 | 当前有效 |
| [DATABASE_CONTRACT.md](./contracts/DATABASE_CONTRACT.md) | SQLite 表结构、约束、关系和 Chroma 数据约定 | 当前有效 |
| [RAG_PIPELINE.md](./ai/RAG_PIPELINE.md) | 解析、切分、Embedding、检索、生成和引用 | 部分待实现 |
| [CONFIGURATION.md](./engineering/CONFIGURATION.md) | 环境变量、路径、模型和密钥配置 | 部分已实现 |
| [TESTING.md](./engineering/TESTING.md) | 测试层级、命令、隔离和合并门槛 | 当前有效 |
| [SECURITY.md](./operations/SECURITY.md) | 文件、数据、模型和密钥安全要求 | 部分待实现 |
| [DEPLOYMENT.md](./operations/DEPLOYMENT.md) | 构建、部署、升级和回滚 | 尚未实现 |
| [RUNBOOK.md](./operations/RUNBOOK.md) | 常见故障处理和恢复步骤 | 尚未实现 |
| [OBSERVABILITY.md](./operations/OBSERVABILITY.md) | 日志、指标、追踪和告警 | 尚未实现 |
| [ADR-0001](./architecture/adr/0001-use-vue-fastapi-sqlite-chroma.md) | 技术栈选择记录 | 已接受 |
| [ADR-0002](./architecture/adr/0002-no-agent-in-mvp.md) | MVP 不引入 Agent 的决策 | 已接受 |

## 按任务阅读文档

添加或修改功能：

```text
docs/product/MVP.md
-> docs/engineering/FRONTEND_SPEC.md 或 docs/contracts/API_CONTRACT.md
-> 对应实现文档
```

修改接口：

```text
docs/contracts/API_CONTRACT.md
-> docs/contracts/DATABASE_CONTRACT.md
-> docs/architecture/TECH_DESIGN.md
```

修改前端：

```text
docs/engineering/FRONTEND_SPEC.md
-> docs/contracts/API_CONTRACT.md
```

修改 RAG：

```text
docs/ai/RAG_PIPELINE.md
-> docs/contracts/DATABASE_CONTRACT.md
-> docs/contracts/API_CONTRACT.md
```

准备部署：

```text
docs/engineering/CONFIGURATION.md
-> docs/operations/SECURITY.md
-> docs/operations/DEPLOYMENT.md
-> docs/operations/RUNBOOK.md
-> docs/operations/OBSERVABILITY.md
```

## 冲突处理

文档发生冲突时停止实现，并按以下规则判断：

1. 功能是否属于范围，以 `MVP.md` 为准。
2. 对外接口行为以 `API_CONTRACT.md` 为准。
3. 数据结构和一致性以 `DATABASE_CONTRACT.md` 为准。
4. 前端交互和状态以 `FRONTEND_SPEC.md` 为准。
5. RAG 处理流程以 `RAG_PIPELINE.md` 为准。
6. 技术栈和系统架构以 `TECH_DESIGN.md` 为准。

不要为了让代码通过测试而反向修改契约。先确认哪份文档需要变更，再同步代码和测试。
