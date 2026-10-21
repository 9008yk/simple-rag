# ADR-0003：RAG 摄取和检索参数

## 状态

已接受。

## 背景

项目需要在不引入复杂 Agent、Redis 和 Celery 的前提下，完成中文 TXT 和 Markdown 文档的解析、切分、向量化和检索。

## 决策

文档处理和检索采用：

```text
处理触发：FastAPI BackgroundTasks
切分方式：Markdown 结构感知 + 字符递归切分
chunk size：800 字符
chunk overlap：120 字符
Embedding：BAAI/bge-small-zh-v1.5
向量维度：512
向量距离：cosine
Top-K：4
相似度硬阈值：MVP 不设置
文档过滤：MVP 不提供
Rerank：不提供
混合检索：不提供
查询改写：不提供
LLM：OpenAI-compatible Chat Completions
```

## 原因

- 字符切分不依赖额外 tokenizer，适合当前中文文档 MVP。
- Markdown 标题结构有利于保留文档层级和引用可读性。
- 本地 Embedding 避免上传文档内容到第三方 Embedding 服务。
- Top-K 4 限制 Prompt 大小，同时给模型足够上下文。
- MVP 不设置硬阈值，避免在没有评估数据时产生任意参数。
- 进程内 BackgroundTasks 不增加 Redis 和 Celery 运维成本。

## 影响

- 后台任务不是持久化队列，服务重启可能中断处理。
- 重启时处于 `processing` 的文档需要标记为 `failed`。
- 本地 Embedding 模型需要在部署前下载并缓存。
- 无硬阈值可能返回弱相关结果，Prompt 必须支持基于资料不足的拒答。
- 后续更换 Embedding 模型必须重建 Chroma collection。
