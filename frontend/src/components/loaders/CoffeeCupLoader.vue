<template>
  <div class="food-stage coffee-stage" aria-hidden="true">
    <div class="steam-wrap steam-wrap--coffee">
      <span
        v-for="steam in steamLines"
        :key="`coffee-${steam.id}`"
        class="steam-line"
        :style="steam.style"
      />
    </div>
    <div class="coffee-cup">
      <span class="coffee-liquid" />
      <span class="coffee-ripple" />
      <span
        v-for="bean in coffeeBeans"
        :key="bean.id"
        class="coffee-bean"
        :style="bean.style"
      />
    </div>
    <span class="coffee-handle" />
    <span class="coffee-saucer" />
  </div>
</template>

<script setup>
const steamLines = [
  { id: 'st-0', style: { '--left': '24%', '--delay': '0s', '--dur': '2.4s' } },
  { id: 'st-1', style: { '--left': '38%', '--delay': '0.35s', '--dur': '2.1s' } },
  { id: 'st-2', style: { '--left': '52%', '--delay': '0.15s', '--dur': '2.2s' } },
  { id: 'st-3', style: { '--left': '66%', '--delay': '0.45s', '--dur': '2.5s' } },
]

const coffeeBeans = [
  { id: 'cf-0', style: { '--x': '26%', '--y': '44%', '--delay': '0.1s' } },
  { id: 'cf-1', style: { '--x': '41%', '--y': '38%', '--delay': '0.28s' } },
  { id: 'cf-2', style: { '--x': '56%', '--y': '45%', '--delay': '0.17s' } },
  { id: 'cf-3', style: { '--x': '67%', '--y': '36%', '--delay': '0.34s' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 190px;
  position: relative;
}

.coffee-stage {
  display: grid;
  place-items: end center;
}

.steam-wrap {
  position: absolute;
  inset: 6px 38px auto;
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

.coffee-cup {
  position: absolute;
  bottom: 26px;
  width: 146px;
  height: 92px;
  border-radius: 18px 18px 44px 44px;
  background: linear-gradient(180deg, #f8f6f1, #ebe6dc);
  box-shadow: inset 0 -7px 0 rgb(175 165 151 / 0.4);
  overflow: hidden;
}

.coffee-liquid {
  position: absolute;
  left: 12px;
  right: 12px;
  top: 14px;
  height: 52px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgb(var(--loader-accent-rgb) / 0.96), rgb(var(--loader-accent-rgb) / 0.72));
}

.coffee-ripple {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 24px;
  height: 20px;
  border-radius: 999px;
  border: 2px solid rgb(255 255 255 / 0.34);
  border-color: rgb(255 255 255 / 0.34) transparent transparent transparent;
  animation: coffee-wave 1.8s ease-in-out infinite;
}

.coffee-bean {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: 10px;
  height: 14px;
  border-radius: 50%;
  background: #5d3a25;
  box-shadow: inset -1px 0 0 rgb(39 24 14 / 0.45);
  animation: coffee-bean-bob 1.5s ease-in-out infinite;
  animation-delay: var(--delay);
}

.coffee-handle {
  position: absolute;
  right: 39px;
  bottom: 56px;
  width: 30px;
  height: 38px;
  border-radius: 0 24px 24px 0;
  border: 6px solid #e6e1d8;
  border-left: 0;
}

.coffee-saucer {
  position: absolute;
  bottom: 16px;
  width: 180px;
  height: 20px;
  border-radius: 50%;
  background: rgb(29 27 22 / 0.14);
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

@keyframes coffee-wave {
  0%,
  100% {
    transform: scaleX(0.92);
    opacity: 0.52;
  }
  50% {
    transform: scaleX(1.05);
    opacity: 0.92;
  }
}

@keyframes coffee-bean-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}
</style>
