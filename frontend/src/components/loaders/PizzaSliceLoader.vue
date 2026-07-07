<template>
  <div class="food-stage pizza-stage" aria-hidden="true">
    <div class="pizza-wheel">
      <span
        v-for="topping in pizzaToppings"
        :key="topping.id"
        class="pizza-topping"
        :style="topping.style"
      />
    </div>
    <div class="pizza-slice">
      <span class="cheese-drip drip-a" />
      <span class="cheese-drip drip-b" />
      <span class="olive olive-a" />
      <span class="olive olive-b" />
    </div>
  </div>
</template>

<script setup>
const pizzaToppings = [
  { id: 'pz-0', style: { '--x': '24%', '--y': '28%', '--delay': '0.1s' } },
  { id: 'pz-1', style: { '--x': '48%', '--y': '18%', '--delay': '0.3s' } },
  { id: 'pz-2', style: { '--x': '65%', '--y': '36%', '--delay': '0.17s' } },
  { id: 'pz-3', style: { '--x': '36%', '--y': '52%', '--delay': '0.4s' } },
  { id: 'pz-4', style: { '--x': '56%', '--y': '62%', '--delay': '0.22s' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 190px;
  position: relative;
}

.pizza-stage {
  display: grid;
  place-items: center;
}

.pizza-wheel {
  width: 124px;
  height: 124px;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 45%, #f7b756 0%, #e48e39 68%, #b66623 100%);
  border: 7px solid #d59149;
  position: absolute;
  left: 20px;
  bottom: 20px;
  animation: slow-spin 3.6s linear infinite;
}

.pizza-topping {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgb(var(--loader-accent-rgb) / 0.9);
  box-shadow: inset 0 -2px 0 rgb(22 31 19 / 0.35);
  animation: topping-blink 1.8s ease-in-out infinite;
  animation-delay: var(--delay);
}

.pizza-slice {
  position: absolute;
  right: 16px;
  bottom: 24px;
  width: 0;
  height: 0;
  border-left: 52px solid transparent;
  border-right: 52px solid transparent;
  border-top: 104px solid #f4ba5f;
  transform: rotate(-16deg);
  animation: slice-pop 1.6s ease-in-out infinite;
}

.pizza-slice::before {
  content: '';
  position: absolute;
  top: -106px;
  left: -58px;
  width: 116px;
  height: 15px;
  border-radius: 999px;
  background: #cf8a48;
}

.cheese-drip {
  position: absolute;
  top: -35px;
  width: 9px;
  height: 22px;
  border-radius: 999px;
  background: #f8d77d;
}

.drip-a {
  left: -9px;
}

.drip-b {
  left: 6px;
  height: 28px;
}

.olive {
  position: absolute;
  top: -70px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgb(var(--loader-accent-rgb) / 0.82);
}

.olive-a {
  left: -22px;
}

.olive-b {
  left: 8px;
}

@keyframes slow-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes topping-blink {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.85);
  }
}

@keyframes slice-pop {
  0%,
  100% {
    transform: rotate(-16deg) translateY(0);
  }
  45% {
    transform: rotate(-14deg) translateY(-5px);
  }
}
</style>
