<template>
  <div class="liquid-backdrop">
    <div class="blob blob-a" aria-hidden="true"></div>
    <div class="blob blob-b" aria-hidden="true"></div>
    <div class="blob blob-c" aria-hidden="true"></div>
    <slot />
  </div>
</template>

<style scoped>
.liquid-backdrop {
  position: relative;
  min-height: 100dvh;
  isolation: isolate;
  overflow-x: hidden;
}

.blob {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(60px);
  will-change: transform;
}

.blob-a {
  width: 380px;
  height: 380px;
  top: -120px;
  right: -140px;
  background: var(--accent-green20);
  animation: blobDrift 10s ease-in-out infinite alternate;
}

.blob-b {
  width: 300px;
  height: 300px;
  bottom: 60px;
  left: -130px;
  background: var(--accent-green20);
  animation: blobDrift 10s ease-in-out infinite alternate-reverse;
}

.blob-c {
  width: 300px;
  height: 300px;
  top: 45%;
  left: 45%;
  /*background: var(--accent-green40);*/
  animation: blobDrift 10s ease-in-out infinite alternate;
}

@keyframes blobDrift {
  0%   { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(30px, -20px) scale(1.05); }
  66%  { transform: translate(-20px, 30px) scale(0.97); }
  100% { transform: translate(20px, 10px) scale(1.03); }
}

.liquid-backdrop > :not(.blob) {
  position: relative;
  z-index: 1;
}
</style>
