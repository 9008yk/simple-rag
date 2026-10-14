# 前端交互规格

## 1. 文档职责

本文档定义 MVP 前端的用户流程、页面、组件、状态、交互反馈、响应式和无障碍要求。

- 功能范围以 `docs/product/MVP.md` 为准。
- 接口字段和错误格式以 `docs/contracts/API_CONTRACT.md` 为准。
- 技术栈和系统架构以 `docs/architecture/TECH_DESIGN.md` 为准。

当前阶段只有一个主页面，不引入 Vue Router，也不引入 Pinia。

## 2. MVP 目标

前端第一版需要完成：

- 显示后端连接状态。
- 上传 TXT、MD 和 MARKDOWN 文件。
- 显示上传进度状态。
- 显示上传错误。
- 加载并显示文档列表。
- 在页面刷新后重新读取持久化文档。

暂不实现：

- 登录和权限。
- 搜索、筛选和分页。
- 删除和重新处理。
- 文档预览。
- 问答聊天。

## 3. 页面清单

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| DocumentPage | `/` | 上传文档并查看文档列表 |

页面区域：

```text
DocumentPage
├── PageHeader
│   ├── 应用标题
│   └── BackendStatus
├── DocumentUpload
│   ├── 文件选择
│   ├── 上传按钮
│   └── 错误信息
└── DocumentList
    ├── 数量摘要
    ├── EmptyState
    └── DocumentListItem[]
```

## 4. 用户流程

### 4.1 页面初始化

```text
打开页面
-> 显示 BackendStatus=checking
-> 请求 GET /health
-> 请求 GET /api/documents
-> 显示后端状态和文档列表
```

### 4.2 上传文档

```text
选择文件
-> 前端检查扩展名和大小
-> 点击上传
-> 按钮进入 uploading
-> 请求 POST /api/documents
-> 201 后清空选择并刷新列表
-> 显示上传成功
```

前端检查只用于快速反馈，后端仍然是最终校验方。

### 4.3 错误流程

```text
未选择文件 -> 本地提示
扩展名不支持 -> 本地提示，后端仍返回 400 时以 detail 为准
文件超过 10 MiB -> 本地提示，后端仍返回 413 时以 detail 为准
缺少 file -> 显示后端 422 错误
文件存储不可用 -> 显示后端 507 错误
网络失败 -> 显示无法连接后端
列表加载失败 -> 列表区域显示失败状态，不覆盖整个页面
```

## 5. 组件职责

| 组件 | 职责 |
| --- | --- |
| `App` | 页面组合和跨区域状态协调 |
| `PageHeader` | 标题和后端连接状态 |
| `DocumentUpload` | 文件选择、上传和上传反馈 |
| `DocumentList` | loading、empty、loaded、failed 状态 |
| `DocumentListItem` | 文件名、状态、chunk 数量和创建时间 |

组件可以暂时保留在 `App.vue` 中，但不得让组件承担 API 字段转换之外的业务规则。

## 6. 状态矩阵

| 区域 | 状态 | 页面表现 |
| --- | --- | --- |
| BackendStatus | `checking` | 显示检查中 |
| BackendStatus | `ok` | 显示后端正常 |
| BackendStatus | `failed` | 显示后端不可用 |
| DocumentUpload | `idle` | 可以选择文件 |
| DocumentUpload | `uploading` | 禁用重复上传 |
| DocumentUpload | `success` | 显示成功并刷新列表 |
| DocumentUpload | `failed` | 显示可理解错误 |
| DocumentList | `loading` | 显示加载中 |
| DocumentList | `empty` | 显示暂无文档 |
| DocumentList | `loaded` | 显示文档记录 |
| DocumentList | `failed` | 显示加载失败 |

## 7. API 映射

| 页面动作 | API | 契约来源 |
| --- | --- | --- |
| 初始化检查 | `GET /health` | `docs/contracts/API_CONTRACT.md` |
| 加载文档 | `GET /api/documents` | `docs/contracts/API_CONTRACT.md` |
| 上传文档 | `POST /api/documents` | `docs/contracts/API_CONTRACT.md` |

前端类型必须与 `Document` 模型一致，不得额外依赖内部字段 `file_path`。

## 8. 交互和视觉要求

- 页面是工作型界面，不使用营销落地页结构。
- 上传、错误和列表区域保持稳定尺寸，加载状态不得造成明显布局跳动。
- 所有按钮使用清晰的动作名称，不使用含糊的“确定”。
- 错误信息显示在对应区域附近，不能只写入浏览器控制台。
- 文档状态需要以文本显示，不仅依赖颜色表达。
- 移动端不得出现横向滚动，按钮和文件名不能溢出容器。
- 交互控件必须有可见焦点。
- 文件输入需要明确 label。

## 9. 前端验收标准

- `AC-UI-01`：页面初始化后显示后端连接状态。
- `AC-UI-02`：可以选择 `.txt`、`.md` 或 `.markdown` 文件。
- `AC-UI-03`：未选择文件时点击上传，显示明确提示。
- `AC-UI-04`：上传成功后刷新文档列表并显示新记录。
- `AC-UI-05`：400、413、422、507 和网络错误显示给用户。
- `AC-UI-06`：文档列表为空时显示“暂无文档”。
- `AC-UI-07`：刷新页面后可以重新加载已有文档。
- `AC-UI-08`：后端不可用时，前端仍能显示错误状态。
- `AC-UI-09`：前端生产构建通过。
- `AC-UI-10`：移动端和桌面端均无内容重叠或横向滚动。

## 10. 验证方式

```powershell
cd frontend
pnpm build
pnpm dev
```

联调时同时启动 FastAPI，并按照 `docs/engineering/TESTING.md` 执行手动端到端检查。
