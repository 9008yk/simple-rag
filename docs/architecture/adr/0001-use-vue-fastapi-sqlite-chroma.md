# ADR-0001：使用 Vue、FastAPI、SQLite 和 Chroma

## 状态

已接受。

## 背景

项目目标是实现一个简单的本地 RAG 知识库问答应用，优先验证上传、检索和引用流程，而不是构建分布式生产平台。

## 决策

采用：

```text
前端：Vue 3 + Vite
后端：FastAPI
RAG：LangChain
关系数据：SQLite
向量数据：Chroma
流式协议：SSE
```

## 原因

- Vue 3 和 Vite 适合快速构建单页应用。
- FastAPI 对异步接口、文件上传和 SSE 支持良好。
- SQLite 无需独立服务，适合单机 MVP。
- Chroma 支持本地持久化向量检索。
- LangChain 可以提供文档加载、切分和检索能力，但 MVP 不引入 Agent。

## 影响

正面影响：

- 本地启动简单。
- 基础设施依赖少。
- 可以快速完成端到端 RAG 验证。

限制：

- SQLite 不适合高并发分布式写入。
- Chroma 本地部署不适合大规模多租户。
- 未来扩展需要显式迁移关系数据库和向量存储。

## 被拒绝的方案

- MySQL + 独立向量数据库：对当前 MVP 运维成本过高。
- PostgreSQL + pgvector：可以在未来重新评估。
- 微服务和消息队列：当前没有规模和并发依据。
