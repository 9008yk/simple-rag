# 贡献指南

## 1. 开始开发前

先阅读：

```text
docs/README.md
docs/product/MVP.md
docs/engineering/FRONTEND_SPEC.md
docs/contracts/API_CONTRACT.md
docs/contracts/DATABASE_CONTRACT.md
docs/architecture/TECH_DESIGN.md
```

修改 RAG、配置、安全或部署时，继续阅读对应专题文档。

## 2. 分支规则

默认使用 `codex/` 前缀：

```text
codex/document-ui
codex/document-delete
codex/rag-ingestion
```

一个分支只处理一个功能、修复或文档主题。开始前从最新 `main` 创建：

```powershell
git switch main
git pull --ff-only
git switch -c codex/feature-name
```

## 3. 开发流程

```text
确认需求和契约
-> 创建功能分支
-> 先补或更新测试
-> 实现最小切片
-> 运行验证
-> 审查 diff
-> 提交并推送
-> 创建 PR
```

不得把未提交的多个无关功能混在同一个 PR 中。

## 4. Commit Message

使用 Conventional Commits：

```text
feat(api): add document list
fix(api): clean partial uploads
docs: define frontend interaction
test(api): cover database migration
chore: update dependencies
```

提交应保持可理解、可回滚，不提交调试代码和临时文件。

## 5. 验证命令

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

前端：

```powershell
cd frontend
pnpm build
```

测试要求以 `docs/engineering/TESTING.md` 为准。

## 6. Pull Request

PR 必须包含：

- 变更目的。
- 涉及的文档契约。
- 测试证据。
- 风险和未覆盖内容。
- 手动验证方式。

PR 合并前必须满足：

- 变更范围单一。
- 相关测试通过。
- 前端构建通过。
- 契约和代码一致。
- 没有密钥、运行数据或数据库文件。
- 没有未解决的 P0/P1 问题。

## 7. Review 重点

Review 优先检查：

- 行为和业务语义。
- API、数据库和前端状态一致性。
- 失败路径和资源清理。
- 安全和权限。
- 数据一致性。
- 测试是否检查真实副作用。

格式和自动检查不能代替人工语义审查。

## 8. 文档规则

- 每类信息只有一个权威来源。
- 接口修改先更新 `docs/contracts/API_CONTRACT.md`。
- 数据库修改先更新 `docs/contracts/DATABASE_CONTRACT.md`。
- 前端页面和交互修改先更新 `docs/engineering/FRONTEND_SPEC.md`。
- RAG 行为修改先更新 `docs/ai/RAG_PIPELINE.md`。
- 文档只写当前决策、明确待决策项和约束，不复制整段其他文档。

## 9. 禁止提交

```text
.env
API Key
data/app.db
data/uploads/ 中的用户文件
data/chroma/ 中的运行数据
backend/.venv/
frontend/node_modules/
```
