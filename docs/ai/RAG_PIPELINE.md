# RAG Pipeline

## 1. 文档职责

本文档定义知识库文档从上传到问答引用的完整 RAG 流程。

上传、列表、解析、切分、Embedding 和 Chroma 摄取已经实现；向量检索和问答仍待实现。本文档中的实现参数已经决策，后续代码必须按照这些参数实现。

## 2. 总体流程

```text
原始文件
-> 解析文本
-> 清洗和规范化
-> 文本切分
-> Embedding
-> 写入 Chroma
-> 文档状态 ready
-> 用户提问
-> 查询向量化
-> 相似度检索
-> 构造 Prompt
-> LLM 生成
-> 保存消息与来源
-> 流式返回答案和引用
```

## 3. 文档摄取

### 3.1 当前支持格式

```text
.txt
.md
.markdown
```

PDF、DOCX、HTML 和 OCR 不属于当前 MVP。

### 3.2 处理状态

```text
pending -> processing -> ready
pending -> processing -> failed
```

失败时写入 `error_message`。MVP 不实现失败重试，用户可以删除后重新上传。

### 3.3 一致性要求

- 写入 Chroma 成功后才能更新为 `ready`。
- 处理失败时必须清理本次写入的部分 chunk。
- 原始文件、SQLite 记录和 Chroma chunk 必须能够通过 `document_id` 关联。

### 3.4 处理触发与恢复

`POST /api/documents` 返回 `201` 后，通过 FastAPI 进程内 BackgroundTasks 调度文档处理，不在上传请求内同步执行解析和 Embedding。

这是单机 MVP 的非持久化后台任务方案，不引入 Redis 或 Celery。后续如果任务可靠性成为问题，再通过 ADR 迁移到独立任务队列。

如果服务在处理过程中重启，之前停留在 `processing` 的文档在下次启动时更新为 `failed`，错误信息为处理被服务重启中断。MVP 不自动重试。

## 4. 文本解析和切分

解析规则：

- TXT 按文本读取。
- Markdown 保留标题、段落和列表的语义边界。
- 不使用图片、表格和扫描件 OCR。

切分要求：

- 每个 chunk 必须保留 `document_id`、`chunk_id`、`source` 和 `chunk_index`。
- chunk 不能跨越来源文档。
- 切分前必须清理无法解析的字符。
- 空文档或解析后无语义内容的文档必须进入 `failed`。

已决策：

| 项目 | 决策 |
| --- | --- |
| 文件编码 | 使用 UTF-8，允许 BOM；解码失败进入 `failed` |
| 切分单位 | 按字符长度切分，不引入 tokenizer 依赖 |
| 切分策略 | Markdown 先按标题结构分段，再按段落、换行、中文句末标点和字符递归切分 |
| chunk size | 800 字符 |
| chunk overlap | 120 字符 |
| 标题层级 | 保留，并将当前标题路径放入 chunk 文本供检索和回答使用 |
| 最小 chunk 条件 | 去除空白后必须包含可见文本；纯空白 chunk 丢弃 |
| chunk_index | 从 `0` 开始，在同一文档内连续递增 |

切分不得跨越源代码块和 Markdown 标题边界，除非单个代码块或段落本身超过 800 字符。

## 5. Embedding 和 Chroma

每个 chunk 写入 Chroma：

```text
Chroma ID: chunk_id
document: chunk 原文
embedding: 向量
metadata:
  document_id
  chunk_id
  source
  chunk_index
```

已决策：

| 项目 | 决策 |
| --- | --- |
| 运行方式 | 本地模型 |
| Provider | `sentence-transformers` |
| Model | `BAAI/bge-small-zh-v1.5` |
| 向量维度 | `512` |
| 向量归一化 | 启用 |
| Chroma 距离 | cosine |

Chroma collection 使用：

```text
collection: document_chunks
metadata: {"hnsw:space": "cosine"}
```

模型首次使用需要下载并缓存。生产部署必须在启动前预下载模型，不能依赖运行期临时下载。

同一个 Chroma collection 中必须使用相同模型和相同向量维度。

## 6. 检索

检索流程：

```text
用户问题
-> 使用相同 Embedding 模型生成查询向量
-> 在 Chroma 中执行相似度检索
-> 返回相关 chunk 和 metadata
-> 过滤不可用文档
-> 将命中结果交给 Prompt
```

已决策：

| 项目 | 决策 |
| --- | --- |
| Top-K | `4` |
| 相似度阈值 | MVP 不设置硬阈值，保留原始分数并在无可靠上下文时由 Prompt 拒答 |
| 按文档过滤 | MVP 不支持，检索全部 `ready` 文档 |
| Rerank | MVP 不引入 |
| 混合检索 | MVP 不引入 |
| 查询改写 | MVP 不引入，直接使用当前问题生成查询向量 |

检索结果少于 4 条时返回实际数量。collection 为空时返回 0 条，不调用 LLM。

## 7. Prompt 和回答

Prompt 必须包含：

- 用户问题。
- 检索得到的 chunk 原文。
- 来源标识。
- 无相关上下文时的拒答规则。
- 不得编造来源的约束。

助手回答必须满足：

- 回答内容基于检索上下文。
- 有引用时返回至少一个 `MessageSource`。
- 没有可靠上下文时明确说明无法从当前知识库回答。
- 不允许把内部文件路径返回给用户。

已决策 Prompt 结构：

```text
System:
你是知识库问答助手。只能依据用户消息中提供的知识库资料回答。
如果资料不足以回答，请明确说明无法从当前知识库确认。
不得编造资料、来源或引用编号。

User:
知识库资料：
[1] 来源：{source}，片段：{chunk_index}
{chunk_text}

[2] ...

问题：{question}
```

回答约束：

- 使用与用户问题相同的语言回答。
- 引用编号使用 `[1]`、`[2]`，必须与本次 `sources` 数组顺序一致。
- 没有引用依据时不得生成伪引用。
- LLM 使用 OpenAI-compatible Chat Completions 接口。
- Provider、Base URL、模型名称和密钥通过环境变量配置。
- MVP 固定 `temperature=0.1`，最大输出 token 为 `1024`。
- Prompt 模板版本为 `rag-answer-v1`。

## 8. 会话与来源

```text
conversations 1 -> N messages
messages 1 -> N message_sources
documents 1 -> N message_sources
```

来源记录至少包含：

```text
document_id
chunk_id
source
chunk_index
score
```

MVP 检索和回答只使用当前问题。`conversation_id` 用于保存和展示聊天记录，不把历史消息加入检索查询或 Prompt。历史上下文增强必须另行决策。

## 9. 质量和可观测性

后续需要记录：

- 文档解析耗时。
- chunk 数量。
- Embedding 耗时和失败率。
- Chroma 写入和删除结果。
- 检索 Top-K 和分数分布。
- LLM 首 token 延迟和总耗时。
- 无上下文拒答比例。

评估指标：

- `Recall@4`：标准答案所在 chunk 是否进入前 4 条。
- 引用正确率：回答中的引用是否对应实际使用的 chunk。
- 回答忠实度：回答是否得到检索上下文支持。
- 拒答正确率：知识库无依据时是否明确拒答。
- 首 token 延迟和完整回答延迟。

实现问答后建立至少 20 个固定问题作为首版评估集，覆盖可回答问题、无答案问题和相似文档问题。

## 10. 验收方向

- 上传后文档最终进入 `ready` 或明确进入 `failed`。
- `ready` 文档的 `chunk_count` 大于 0。
- 重新启动服务后仍能检索已有 chunk。
- 提问只使用知识库中的相关上下文。
- 回答可以定位到具体文档和 chunk。
- 删除文档时原始文件、SQLite 和 Chroma 保持一致。
