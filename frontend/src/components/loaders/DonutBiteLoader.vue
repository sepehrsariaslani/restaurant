<template>
  <div class="food-stage donut-stage" aria-hidden="true">
    <div class="donut-ring">
      <span
        v-for="sprinkle in donutSprinkles"
        :key="sprinkle.id"
        class="sprinkle"
        :style="sprinkle.style"
      />
      <span class="bite-mark" />
    </div>
  </div>
</template>

<script setup>
const donutSprinkles = [
  { id: 'dn-0', style: { '--x': '26%', '--y': '29%', '--r': '-16deg' } },
  { id: 'dn-1', style: { '--x': '40%', '--y': '23%', '--r': '9deg' } },
  { id: 'dn-2', style: { '--x': '57%', '--y': '28%', '--r': '-8deg' } },
  { id: 'dn-3', style: { '--x': '67%', '--y': '39%', '--r': '14deg' } },
  { id: 'dn-4', style: { '--x': '35%', '--y': '47%', '--r': '6deg' } },
  { id: 'dn-5', style: { '--x': '51%', '--y': '52%', '--r': '-12deg' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 190px;
  position: relative;
}

.donut-stage {
  display: grid;
  place-items: center;
}

.donut-ring {
  width: 136px;
  height: 136px;
  border-radius: 50%;
  background: radial-gradient(circle at 48% 48%, #0000 28px, #c7854f 28px, #be7842 46px, #ac6537 100%);
  position: relative;
  animation: donut-spin 4.2s linear infinite;
}

.donut-ring::before {
  content: '';
  position: absolute;
  inset: 16px;
  border-radius: 50%;
  background: radial-gradient(circle at 48% 38%, rgb(var(--loader-accent-rgb) / 0.96), rgb(var(--loader-accent-rgb) / 0.68) 78%);
}

.sprinkle {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: 11px;
  height: 3px;
  border-radius: 999px;
  background: rgb(var(--loader-accent-rgb) / 0.92);
  transform: rotate(var(--r));
  z-index: 1;
}

.bite-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--loader-overlay-color);
  box-shadow: -18px 10px 0 var(--loader-overlay-color), -8px 24px 0 var(--loader-overlay-color);
  z-index: 2;
}

@keyframes donut-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
