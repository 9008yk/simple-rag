# AGENTS.md

## 项目说明

这是一个简单的 RAG 知识库问答项目，目标是完成文档上传、向量检索和带引用来源的流式问答。

修改功能前先阅读 `docs/MVP.md`，修改技术实现前同时阅读 `docs/TECH_DESIGN.md`。

## 文档优先级

1. `docs/MVP.md` 定义功能范围和验收标准。
2. `docs/TECH_DESIGN.md` 定义技术栈、架构、接口和数据模型。
3. `AGENTS.md` 定义编码过程和验证要求。

文档发生冲突时，不自行选择实现方案；先停下来说明冲突，等待需求或技术设计更新。

## 开发约束

- 只实现 `docs/MVP.md` 定义的范围。
- 技术选型不得超出 `docs/TECH_DESIGN.md`。确需调整时先更新设计文档。
- 不做与当前任务无关的重构、格式化或依赖升级。
- 优先实现最小闭环，不为尚未出现的需求增加抽象和配置项。

## 项目结构

```text
backend/              FastAPI 服务
frontend/             Vue 3 应用
docs/                 项目文档
data/uploads/         上传的原始文件
data/chroma/          Chroma 持久化数据
data/app.db           SQLite 数据库
```

## 常用命令

```text
后端目录：backend
后端启动：.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
后端测试：.\.venv\Scripts\python.exe -m pytest -q

前端目录：frontend
前端安装：pnpm install
前端启动：pnpm dev
前端构建：pnpm build
```

## 验证要求

- 修改后运行与改动直接相关的测试。
- 上传、检索、回答和来源引用主流程必须保持可用。
- 回答必须能够定位到具体文档和 chunk。
- 数据写入后，重启服务仍应能够检索。
- 错误不能静默失败，前后端都需要提供可理解的反馈。
