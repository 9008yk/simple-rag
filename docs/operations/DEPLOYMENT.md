# 部署说明

## 1. 当前状态

当前只有本地开发启动方式，没有 Docker、CI/CD 或生产部署配置。本文档定义目标部署边界，不代表这些能力已经实现。

## 2. 目标部署结构

```text
浏览器
-> HTTPS / 反向代理
-> Vue 静态资源
-> FastAPI
-> SQLite + 上传文件 + Chroma
-> LLM / Embedding Provider
```

生产环境需要分别处理：

- 前端静态构建。
- FastAPI 进程。
- 持久化数据目录。
- 环境变量和 Secret。
- 反向代理、超时和上传大小。
- 日志和健康检查。

## 3. 持久化数据

部署时必须挂载并备份：

```text
data/app.db
data/uploads/
data/chroma/
```

容器或进程重建不能删除这些目录。

## 4. 构建步骤

前端：

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm build
```

后端依赖：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. 目标发布流程

```text
确认 main 已通过 CI
-> 构建前端
-> 安装后端依赖
-> 执行数据库迁移
-> 启动后端
-> 执行健康检查
-> 切换流量
-> 观察错误率和延迟
```

## 6. 数据迁移

- 发布前先备份 SQLite 和 Chroma。
- 迁移必须可重复执行。
- 迁移失败时禁止继续启动新版本。
- 不允许依赖 `CREATE TABLE IF NOT EXISTS` 修改已有表结构。
- 数据库迁移脚本必须纳入版本控制。

## 7. 回滚

回滚前确认：

- 应用版本可以回退。
- 数据库迁移是否具备反向迁移或恢复方案。
- Chroma 和上传目录是否有对应备份。
- 新版本是否已经写入不兼容数据。

如果数据结构不兼容，不能只回滚代码，必须同时恢复数据。

## 8. 部署配置

生产环境至少需要：

```text
SIMPLE_RAG_DATA_DIR
LLM_PROVIDER
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
EMBEDDING_PROVIDER
EMBEDDING_API_KEY
EMBEDDING_BASE_URL
EMBEDDING_MODEL
```

具体变量以 `docs/engineering/CONFIGURATION.md` 为准。

## 9. 上线前检查

- 前端构建通过。
- 后端测试通过。
- 数据库迁移验证通过。
- `.env` 和密钥未进入 Git。
- 健康检查可用。
- 日志和告警已配置。
- 备份和恢复已经演练。
- 上传大小和请求超时已在反向代理中配置。

## 10. 尚未实现

- Dockerfile。
- Docker Compose。
- Nginx 或网关配置。
- GitHub Actions。
- 自动部署。
- 容器镜像签名。
- 生产监控和告警。
