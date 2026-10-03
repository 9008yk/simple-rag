<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getHealth } from "./api/client";

const backendStatus = ref("checking");

onMounted(async () => {
  try {
    const data = await getHealth();
    backendStatus.value = data.status;
  } catch {
    backendStatus.value = "failed";
  }
});
</script>

<template>
  <main>
    <p>Backend: {{ backendStatus }}</p>
  </main>
</template>
