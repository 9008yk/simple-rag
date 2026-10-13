# Simple RAG

一个本地运行的简单 RAG 知识库问答项目。

当前仓库已完成前后端基础骨架，并通过 FastAPI 提供 `/health` 健康检查和 `POST /api/documents` 文档上传接口。文档列表、解析、向量检索和流式问答尚未实现。

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

- `docs/MVP.md`：功能范围、验收标准和实施顺序。
- `docs/TECH_DESIGN.md`：技术栈和系统架构。
- `docs/API_CONTRACT.md`：接口契约、错误格式和 SSE 事件。
- `docs/DATABASE_CONTRACT.md`：数据表、字段约束、关系和一致性要求。
- `AGENTS.md`：编码规则和验证要求。
