<template>
  <span ref="el" class="counter">{{ display }}</span>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  target: { type: Number, required: true },
  suffix: { type: String, default: '' },
  duration: { type: Number, default: 1800 },
})

const el = ref(null)
const display = ref('0' + props.suffix)
let observer = null
let rafId = null

function animate() {
  const start = performance.now()
  const from = 0
  const to = props.target

  function tick(now) {
    const elapsed = now - start
    const progress = Math.min(elapsed / props.duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = Math.round(from + (to - from) * eased)
    display.value = current.toLocaleString('fa-IR') + props.suffix
    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    }
  }

  rafId = requestAnimationFrame(tick)
}

watch(
  () => props.target,
  (nextValue) => {
    if (!Number.isFinite(Number(nextValue))) {
      display.value = '0' + props.suffix
      return
    }
    display.value = Number(nextValue).toLocaleString('fa-IR') + props.suffix
  },
)

onMounted(() => {
  if (!el.value) return
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        animate()
        observer?.disconnect()
      }
    },
    { threshold: 0.3 }
  )
  observer.observe(el.value)
})

onUnmounted(() => {
  observer?.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.counter {
  font-variant-numeric: tabular-nums;
}
</style>
