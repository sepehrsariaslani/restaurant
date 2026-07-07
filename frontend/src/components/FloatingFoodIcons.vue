<template>
  <div class="floating-icons" aria-hidden="true">
    <span
      v-for="icon in icons"
      :key="icon.id"
      class="float-icon"
      :style="{
        '--x': icon.x + '%',
        '--y': icon.y + '%',
        '--size': icon.size + 'rem',
        '--duration': icon.duration + 's',
        '--delay': icon.delay + 's',
        '--opacity': icon.opacity,
      }"
    >{{ icon.emoji }}</span>
  </div>
</template>

<script setup>
const emojis = ['🍕', '🍔', '🥗', '🍜', '🌮', '🍳', '🥘', '🍰', '☕', '🫒', '🥑', '🍋']

function rand(min, max) {
  return Math.random() * (max - min) + min
}

const icons = emojis.map((emoji, idx) => ({
  id: idx,
  emoji,
  x: rand(2, 95),
  y: rand(5, 90),
  size: rand(1.2, 2.4),
  duration: rand(12, 22),
  delay: rand(0, 6),
  opacity: rand(0.06, 0.15),
}))
</script>

<style scoped>
.floating-icons {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.float-icon {
  position: absolute;
  left: var(--x);
  top: var(--y);
  font-size: var(--size);
  opacity: var(--opacity);
  animation: floatBob var(--duration) ease-in-out var(--delay) infinite alternate;
  will-change: transform;
  user-select: none;
}

@keyframes floatBob {
  0% {
    transform: translate3d(0, 0, 0) rotate(0deg);
  }
  50% {
    transform: translate3d(-12px, -18px, 0) rotate(8deg);
  }
  100% {
    transform: translate3d(10px, 14px, 0) rotate(-6deg);
  }
}
</style>
