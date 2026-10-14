# 可观测性规范

## 1. 当前状态

当前只有 FastAPI 和 Uvicorn 默认日志，没有结构化日志、指标、追踪或告警系统。

## 2. 目标

能够回答：

- 上传接口是否变慢或开始失败。
- 文档摄取卡在哪个阶段。
- Embedding 或 LLM 哪一步失败。
- 检索是否返回了结果。
- 单个请求的失败原因是什么。

## 3. 日志

日志必须使用结构化字段：

```text
timestamp
level
request_id
event
method
path
status_code
duration_ms
document_id
conversation_id
error_type
```

禁止记录：

- API Key。
- Authorization Header。
- 用户完整文档内容。
- 完整 Prompt 和模型原始响应，除非经过脱敏和明确开关控制。

## 4. 指标

上传：

- 请求总数。
- 成功和失败数量。
- 按状态码分布。
- 文件大小分布。
- 上传耗时。

文档处理：

- pending、processing、ready、failed 数量。
- 解析、切分、Embedding、Chroma 写入耗时。
- 处理失败率。

检索和问答：

- 检索耗时。
- Top-K 命中数量。
- 无结果比例。
- LLM 首 token 延迟。
- LLM 总延迟。
- Token 使用量。
- 回答失败率。

## 5. 追踪

未来应为一次请求生成 `request_id`，并贯穿：

```text
FastAPI 请求
-> 文档读取
-> Chroma 检索
-> LLM 调用
-> SSE 返回
```

如果后续引入 OpenTelemetry，应优先追踪上传、摄取和问答链路。

## 6. 健康检查

当前：

```text
GET /health
```

未来可以增加更细粒度检查：

```text
数据目录可写
SQLite 可查询
Chroma 可访问
LLM Provider 配置存在
```

健康检查不应直接调用真实 LLM，以免产生费用和外部依赖抖动。

## 7. 告警

至少关注：

- 上传错误率持续升高。
- 文档处理大量进入 `failed`。
- SQLite 或磁盘写入失败。
- Chroma 不可用。
- LLM API 超时率或限流率升高。
- 问答响应时间明显上升。
- 磁盘使用率达到阈值。

## 8. 验收

- 每个请求有可关联的 `request_id`。
- 上传、摄取、检索和生成阶段均有耗时和结果。
- 日志中不存在密钥和完整敏感文档。
- 关键错误能够触发告警。
- 可以从一次失败请求定位到具体阶段。
