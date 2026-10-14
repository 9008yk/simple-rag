# Changelog

本文件记录用户可见的功能、契约和工程变更。

## [Unreleased]

### Added

- Vue 3 + Vite 前端骨架。
- FastAPI 健康检查接口。
- `POST /api/documents` 文档上传接口。
- `GET /api/documents` 文档列表接口。
- SQLite `documents` 表约束、索引和显式迁移。
- 文件上传大小限制、分块写入和失败清理。
- 后端接口、迁移和错误路径测试。

### Documentation

- 建立 MVP、技术设计、API Contract 和 Database Contract。
- 建立前端、RAG、配置、测试、安全、部署、Runbook 和可观测性文档。
- 建立 ADR、贡献指南和文档索引。

### Planned

- 前端文档上传和列表界面。
- 文档详情和删除接口。
- 文档解析、切分和 Chroma 写入。
- 带引用来源的 SSE 流式问答。

目前还没有正式版本号或发布标签。
