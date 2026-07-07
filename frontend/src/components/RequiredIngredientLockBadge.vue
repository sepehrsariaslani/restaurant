<template>
  <span class="lock-badge" :class="{ editable: editable }">
    {{ editable ? 'اجباری (قابل تغییر)' : 'اجباری' }}
  </span>
</template>

<script setup>
defineProps({
  editable: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.lock-badge {
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  background: rgba(204, 86, 86, 0.14);
  color: #8b3333;
  font-size: 0.67rem;
}

.editable {
  background: rgba(68, 128, 111, 0.16);
  color: #2e6455;
}
</style>
