<template>
  <div ref="el" class="scroll-reveal" :class="[directionClass, { revealed }]">
    <slot />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  threshold: { type: Number, default: 0.15 },
  delay: { type: Number, default: 0 },
  direction: { type: String, default: 'up' },
})

const el = ref(null)
const revealed = ref(false)
let observer = null
const directionClass = `from-${String(props.direction || 'up').toLowerCase()}`

onMounted(() => {
  if (!el.value) return
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        setTimeout(() => { revealed.value = true }, props.delay)
        observer?.disconnect()
      }
    },
    { threshold: props.threshold }
  )
  observer.observe(el.value)
})

onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.scroll-reveal {
  opacity: 0;
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}

.scroll-reveal.from-up:not(.revealed) {
  transform: translateY(32px);
}

.scroll-reveal.from-down:not(.revealed) {
  transform: translateY(-32px);
}

.scroll-reveal.from-left:not(.revealed) {
  transform: translateX(32px);
}

.scroll-reveal.from-right:not(.revealed) {
  transform: translateX(-32px);
}

.scroll-reveal.revealed {
  opacity: 1;
  transform: translate(0, 0);
}

@media (prefers-reduced-motion: reduce) {
  .scroll-reveal {
    opacity: 1;
    transform: none !important;
    transition: none;
  }
}
</style>
