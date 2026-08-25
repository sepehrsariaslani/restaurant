<template>
  <div class="food-stage burger-stage" aria-hidden="true">
    <span
      v-for="layer in burgerLayers"
      :key="layer.id"
      class="burger-layer"
      :class="layer.className"
      :style="layer.style"
    />
  </div>
</template>

<script setup>
const burgerLayers = [
  { id: 'bg-0', className: 'bun-top', style: { '--delay': '0.78s', '--top': '20px' } },
  { id: 'bg-1', className: 'lettuce', style: { '--delay': '0.54s', '--top': '68px' } },
  { id: 'bg-2', className: 'cheese', style: { '--delay': '0.36s', '--top': '81px' } },
  { id: 'bg-3', className: 'patty', style: { '--delay': '0.18s', '--top': '92px' } },
  { id: 'bg-4', className: 'bun-bottom', style: { '--delay': '0s', '--top': '122px' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 190px;
  position: relative;
}

.burger-stage {
  display: block;
  padding-bottom: 16px;
}

.burger-layer {
  position: absolute;
  left: 50%;
  top: var(--top);
  transform: translate(-50%, -86px);
  opacity: 0;
  animation: burger-stack-build 3.4s cubic-bezier(0.22, 0.7, 0.19, 1) infinite;
  animation-delay: var(--delay);
  animation-fill-mode: both;
}

.bun-top {
  width: 154px;
  height: 52px;
  border-radius: 95px 95px 32px 32px;
  background: linear-gradient(180deg, rgb(245 183 111 / 0.96), rgb(212 133 60 / 0.96));
  box-shadow: inset 0 -6px 0 rgb(150 86 31 / 0.33), 0 2px 0 rgb(86 58 27 / 0.12);
}

.lettuce {
  width: 160px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgb(var(--loader-accent-rgb) / 0.78), rgb(var(--loader-accent-rgb) / 0.95), rgb(var(--loader-accent-rgb) / 0.78));
}

.cheese {
  width: 144px;
  height: 10px;
  border-radius: 999px;
  background: #f5d064;
}

.patty {
  width: 150px;
  height: 28px;
  border-radius: 18px;
  background: linear-gradient(180deg, #6b3d21, #4d2a16);
}

.bun-bottom {
  width: 142px;
  height: 24px;
  border-radius: 16px 16px 30px 30px;
  background: linear-gradient(180deg, #d89656, #b66d32);
}

.burger-stage::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 12px;
  width: 170px;
  height: 18px;
  transform: translateX(-50%);
  border-radius: 50%;
  background: rgb(26 24 20 / 0.16);
  filter: blur(2px);
}

@keyframes burger-stack-build {
  0% {
    transform: translate(-50%, -88px) scale(0.9);
    opacity: 0;
  }
  16% {
    transform: translate(-50%, 0) scale(1);
    opacity: 1;
  }
  72% {
    transform: translate(-50%, 0) scale(1);
    opacity: 1;
  }
  84% {
    transform: translate(-50%, -2px) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, 0) scale(1);
    opacity: 1;
  }
}
</style>
