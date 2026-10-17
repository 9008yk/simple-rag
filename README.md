# Simple RAG

一个本地运行的简单 RAG 知识库问答项目。

当前仓库已完成前端文档上传和列表界面，并通过 FastAPI 提供 `/health` 健康检查、`POST /api/documents` 文档上传和 `GET /api/documents` 文档列表接口。文档解析、向量检索和流式问答尚未实现。

## 项目结构

```text
backend/              FastAPI 服务
frontend/             Vue 3 + Vite 应用
docs/                 需求和项目文档
data/uploads/         上传的原始文件
data/chroma/          Chroma 持久化数据
data/app.db           SQLite 数据库
```

## 环境要求

- Python 3.12
- Node.js 22
- pnpm

## 启动后端

在 PowerShell 中执行：

```powershell
cd backend
py -V:Astral/CPython3.12.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

## 运行后端测试

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

## 启动前端

另开一个 PowerShell 终端：

```powershell
cd frontend
pnpm install
pnpm dev
```

浏览器访问：

```text
http://localhost:5173
```

开发服务器会将 `/health` 和 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 构建前端

```powershell
cd frontend
pnpm build
```

## 文档

- `docs/README.md`：完整文档索引和阅读顺序。
- `docs/product/MVP.md`：功能范围、验收标准和实施顺序。
- `docs/engineering/FRONTEND_SPEC.md`：页面、组件、交互状态和前端验收标准。
- `docs/architecture/TECH_DESIGN.md`：技术栈、系统架构和接口与存储映射。
- `docs/contracts/API_CONTRACT.md`：接口契约、错误格式和 SSE 事件。
- `docs/contracts/DATABASE_CONTRACT.md`：数据表、字段约束、关系和一致性要求。
- `docs/ai/RAG_PIPELINE.md`：解析、切分、Embedding、检索和回答流程。
- `docs/engineering/CONFIGURATION.md`：环境变量和密钥管理。
- `docs/engineering/TESTING.md`：测试层级、命令和合并门槛。
- `docs/operations/SECURITY.md`：文件、数据、模型和密钥安全要求。
- `docs/operations/DEPLOYMENT.md`：构建、部署、升级和回滚。
- `docs/operations/RUNBOOK.md`：常见故障处理步骤。
- `docs/operations/OBSERVABILITY.md`：日志、指标、追踪和告警。
- `CONTRIBUTING.md`：人类协作和 PR 流程。
- `CHANGELOG.md`：项目变更记录。
- `AGENTS.md`：编码规则和验证要求。
