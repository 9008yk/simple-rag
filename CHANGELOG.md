# Changelog

本文件记录用户可见的功能、契约和工程变更。

## [Unreleased]

### Added

- Vue 3 + Vite 前端骨架。
- 前端文档上传、状态反馈和文档列表界面。
- FastAPI 健康检查接口。
- `POST /api/documents` 文档上传接口。
- `GET /api/documents` 文档列表接口。
- SQLite `documents` 表约束、索引和显式迁移。
- 文件上传大小限制、分块写入和失败清理。
- 后端接口、迁移和错误路径测试。
- Markdown 结构感知切分和 800/120 字符切分参数。
- 本地 `BAAI/bge-small-zh-v1.5` Embedding 和 Chroma 持久化。
- 上传后的进程内后台文档摄取、状态流转和重启恢复。
- 基于 ready 文档的 Chroma Top-K 向量检索。

### Documentation

- 建立 MVP、技术设计、API Contract 和 Database Contract。
- 建立前端、RAG、配置、测试、安全、部署、Runbook 和可观测性文档。
- 建立 ADR、贡献指南和文档索引。
- 确定基于本地中文 Embedding 的 RAG 切分、检索和 Prompt 参数。

### Planned

- 文档详情和删除接口。
- 带引用来源的 SSE 流式问答。

目前还没有正式版本号或发布标签。
