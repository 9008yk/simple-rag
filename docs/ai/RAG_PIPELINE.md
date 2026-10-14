# RAG Pipeline

## 1. 文档职责

本文档定义知识库文档从上传到问答引用的完整 RAG 流程。

当前只有上传和列表接口已经实现，解析、切分、Embedding、检索和问答仍待实现。本文档中的“待决策”项必须在对应功能编码前确认。

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

待决策：

| 决策 | 状态 |
| --- | --- |
| 切分单位使用字符、token 还是 Markdown 标题结构 | 待决策 |
| chunk size | 待决策 |
| chunk overlap | 待决策 |
| 是否保留标题层级 | 待决策 |

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

待决策：

| 决策 | 状态 |
| --- | --- |
| Embedding Provider | 待决策 |
| Embedding Model | 待决策 |
| 向量维度 | 待决策 |
| 本地模型还是云 API | 待决策 |

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

待决策：

| 决策 | 状态 |
| --- | --- |
| Top-K | 待决策 |
| 相似度阈值 | 待决策 |
| 是否支持按文档过滤 | 待决策 |
| 是否引入 Rerank | MVP 暂不引入 |
| 是否支持混合检索 | MVP 暂不引入 |

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

Prompt 模板和版本在实现问答接口前确定。

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

## 9. 质量和可观测性

后续需要记录：

- 文档解析耗时。
- chunk 数量。
- Embedding 耗时和失败率。
- Chroma 写入和删除结果。
- 检索 Top-K 和分数分布。
- LLM 首 token 延迟和总耗时。
- 无上下文拒答比例。

评估指标后续再确定，例如检索命中率、答案忠实度和引用准确率。

## 10. 验收方向

- 上传后文档最终进入 `ready` 或明确进入 `failed`。
- `ready` 文档的 `chunk_count` 大于 0。
- 重新启动服务后仍能检索已有 chunk。
- 提问只使用知识库中的相关上下文。
- 回答可以定位到具体文档和 chunk。
- 删除文档时原始文件、SQLite 和 Chroma 保持一致。
