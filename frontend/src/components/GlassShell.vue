<template>
  <section class="page-shell glass-card shell">

    <div class="shell-content">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.shell {
  padding: 1.15rem;
}

.shell-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.95rem;
}

.shell-head h1 {
  margin: 0.18rem 0 0;
  font-size: 1.6rem;
}

.shell-head p {
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
