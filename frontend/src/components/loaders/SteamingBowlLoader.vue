<template>
  <div class="food-stage bowl-stage" aria-hidden="true">
    <div class="steam-wrap">
      <span
        v-for="steam in steamLines"
        :key="steam.id"
        class="steam-line"
        :style="steam.style"
      />
    </div>
    <span class="bowl-lip" />
    <span class="bowl-body" />
    <span class="bowl-shadow" />
  </div>
</template>

<script setup>
const steamLines = [
  { id: 'st-0', style: { '--left': '24%', '--delay': '0s', '--dur': '2.4s' } },
  { id: 'st-1', style: { '--left': '38%', '--delay': '0.35s', '--dur': '2.1s' } },
  { id: 'st-2', style: { '--left': '52%', '--delay': '0.15s', '--dur': '2.2s' } },
  { id: 'st-3', style: { '--left': '66%', '--delay': '0.45s', '--dur': '2.5s' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 190px;
  position: relative;
}

.bowl-stage {
  display: grid;
  place-items: end center;
}

.steam-wrap {
  position: absolute;
  inset: 12px 20px auto;
  height: 96px;
}

.steam-line {
  position: absolute;
  left: var(--left);
  bottom: 0;
  width: 10px;
  height: 52px;
  border-radius: 999px;
  border: 2.2px solid rgb(var(--loader-accent-rgb) / 0.36);
  border-color: rgb(var(--loader-accent-rgb) / 0.38) transparent transparent transparent;
  animation: steam-rise var(--dur) ease-in-out infinite;
  animation-delay: var(--delay);
}

.bowl-lip {
  position: absolute;
  bottom: 58px;
  width: 162px;
  height: 28px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgb(var(--loader-accent-rgb) / 0.2), rgb(var(--loader-accent-rgb) / 0.08));
  box-shadow: inset 0 -4px 0 rgb(var(--loader-accent-rgb) / 0.35);
}

.bowl-body {
  position: absolute;
  bottom: 18px;
  width: 146px;
  height: 78px;
  border-radius: 0 0 80px 80px;
  background: linear-gradient(180deg, rgb(var(--loader-accent-rgb) / 0.94), rgb(var(--loader-accent-rgb) / 0.66));
  box-shadow: inset 0 -10px 16px rgb(21 20 15 / 0.18);
}

.bowl-shadow {
  position: absolute;
  bottom: 8px;
  width: 176px;
  height: 20px;
  border-radius: 50%;
  background: rgb(35 33 28 / 0.16);
  filter: blur(2px);
}

@keyframes steam-rise {
  0% {
    transform: translateY(6px) scale(0.82);
    opacity: 0;
  }
  35% {
    opacity: 0.7;
  }
  100% {
    transform: translateY(-36px) scale(1.08);
    opacity: 0;
  }
}
</style>
