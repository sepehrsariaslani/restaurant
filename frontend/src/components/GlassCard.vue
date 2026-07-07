<template>
  <article class="glass-card" :class="{ 'glass-card-hover': hoverable }">
    <slot />
  </article>
</template>

<script setup>
defineProps({
  hoverable: {
    type: Boolean,
    default: false,
  },
})
</script>
