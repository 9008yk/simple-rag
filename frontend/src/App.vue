<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  getHealth,
  listDocuments,
  uploadDocument,
  type Document,
} from "./api/client";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".txt", ".md", ".markdown"];

type BackendStatus = "checking" | "ok" | "failed";
type DocumentsStatus = "loading" | "loaded" | "empty" | "failed";
type UploadStatus = "idle" | "uploading" | "success" | "failed";

const backendStatus = ref<BackendStatus>("checking");
const documentsStatus = ref<DocumentsStatus>("loading");
const uploadStatus = ref<UploadStatus>("idle");
const documents = ref<Document[]>([]);
const selectedFile = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const documentsError = ref("");
const uploadMessage = ref("");

const selectedFileName = computed(
  () => selectedFile.value?.name ?? "尚未选择文件",
);

const canUpload = computed(
  () => selectedFile.value !== null && uploadStatus.value !== "uploading",
);

function validateFile(file: File): string {
  const filename = file.name.toLowerCase();
  const hasAllowedExtension = ALLOWED_EXTENSIONS.some((extension) =>
    filename.endsWith(extension),
  );

  if (!hasAllowedExtension) {
    return "只支持 TXT、MD 和 MARKDOWN 文件。";
  }

  if (file.size === 0) {
    return "不能上传空文件。";
  }

  if (file.size > MAX_FILE_SIZE) {
    return "文件不能超过 10 MiB。";
  }

  return "";
}

async function checkBackend() {
  try {
    const data = await getHealth();
    backendStatus.value = data.status === "ok" ? "ok" : "failed";
  } catch {
    backendStatus.value = "failed";
  }
}

async function loadDocuments() {
  documentsStatus.value = "loading";
  documentsError.value = "";

  try {
    documents.value = await listDocuments();
    documentsStatus.value = documents.value.length === 0 ? "empty" : "loaded";
  } catch (error) {
    documentsStatus.value = "failed";
    documentsError.value =
      error instanceof Error ? error.message : "文档列表加载失败。";
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  uploadMessage.value = "";
  uploadStatus.value = "idle";

  if (!file) {
    selectedFile.value = null;
    return;
  }

  const validationError = validateFile(file);
  if (validationError) {
    selectedFile.value = null;
    input.value = "";
    uploadStatus.value = "failed";
    uploadMessage.value = validationError;
    return;
  }

  selectedFile.value = file;
}

async function handleUpload() {
  if (!selectedFile.value) {
    uploadStatus.value = "failed";
    uploadMessage.value = "请先选择要上传的文件。";
    return;
  }

  uploadStatus.value = "uploading";
  uploadMessage.value = "";

  try {
    await uploadDocument(selectedFile.value);
    uploadStatus.value = "success";
    uploadMessage.value = "上传成功，文档已加入列表。";
    selectedFile.value = null;
    if (fileInput.value) {
      fileInput.value.value = "";
    }
    await loadDocuments();
  } catch (error) {
    uploadStatus.value = "failed";
    uploadMessage.value =
      error instanceof Error ? error.message : "文档上传失败。";
  }
}

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("zh-CN", { hour12: false });
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "等待处理",
    processing: "处理中",
    ready: "可检索",
    failed: "处理失败",
  };

  return labels[status] ?? status;
}

onMounted(async () => {
  await checkBackend();
  await loadDocuments();
});
</script>

<template>
  <main class="app-shell">
    <header class="page-header">
      <div>
        <p class="eyebrow">Knowledge Base</p>
        <h1>Simple RAG</h1>
        <p class="page-description">上传文档并查看当前知识库处理状态。</p>
      </div>
      <span class="status-badge" :data-state="backendStatus">
        <span class="status-dot" aria-hidden="true"></span>
        后端{{
          backendStatus === "ok"
            ? "正常"
            : backendStatus === "checking"
              ? "检查中"
              : "不可用"
        }}
      </span>
    </header>

    <section class="content-section" aria-labelledby="upload-title">
      <div class="section-heading">
        <div>
          <h2 id="upload-title">上传文档</h2>
          <p>支持 TXT、MD 和 MARKDOWN，单个文件不超过 10 MiB。</p>
        </div>
      </div>

      <form class="upload-form" @submit.prevent="handleUpload">
        <div class="file-picker">
          <label for="document-file">选择文件</label>
          <input
            id="document-file"
            ref="fileInput"
            type="file"
            accept=".txt,.md,.markdown"
            @change="handleFileChange"
          />
          <span class="selected-file">{{ selectedFileName }}</span>
        </div>

        <button class="primary-button" type="submit" :disabled="!canUpload">
          {{ uploadStatus === "uploading" ? "上传中..." : "上传文档" }}
        </button>
      </form>

      <p
        v-if="uploadMessage"
        class="feedback-message"
        :data-state="uploadStatus"
        aria-live="polite"
      >
        {{ uploadMessage }}
      </p>
    </section>

    <section class="content-section" aria-labelledby="documents-title">
      <div class="section-heading">
        <div>
          <h2 id="documents-title">文档列表</h2>
          <p>共 {{ documents.length }} 个文档</p>
        </div>
        <button
          class="secondary-button"
          type="button"
          :disabled="documentsStatus === 'loading'"
          @click="loadDocuments"
        >
          刷新
        </button>
      </div>

      <p v-if="documentsStatus === 'loading'" class="state-message">
        正在加载文档...
      </p>

      <p
        v-else-if="documentsStatus === 'failed'"
        class="state-message error-message"
        role="alert"
      >
        {{ documentsError }}
      </p>

      <p v-else-if="documentsStatus === 'empty'" class="state-message">
        暂无文档，请先上传。
      </p>

      <ul v-else class="document-list">
        <li v-for="document in documents" :key="document.id">
          <div class="document-primary">
            <strong>{{ document.filename }}</strong>
            <span>{{ formatCreatedAt(document.created_at) }}</span>
          </div>
          <div class="document-meta">
            <span class="document-status" :data-state="document.status">
              {{ getStatusLabel(document.status) }}
            </span>
            <span>{{ document.chunk_count }} chunks</span>
          </div>
        </li>
      </ul>
    </section>
  </main>
</template>
