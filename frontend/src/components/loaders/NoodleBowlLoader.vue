<template>
  <div class="food-stage">
    <!-- steam -->
    <div class="steam">
      <span v-for="s in steam" :key="s.id" class="steam-line" :style="s.style"/>
    </div>

    <!-- chopsticks -->
    <div class="chopsticks">
      <span class="stick a"/>
      <span class="stick b"/>

      <div class="lifted">
        <span v-for="n in lifted" :key="n.id" class="lift-noodle" :style="n.style"/>
      </div>
    </div>

    <!-- soup -->
    <div class="soup">
      <span class="oil o1"/>
      <span class="oil o2"/>
      <span class="bubble b1"/>
      <span class="bubble b2"/>
    </div>

    <!-- noodle surface -->
    <div class="noodle-surface">
      <span v-for="n in noodles" :key="n.id" class="noodle" :style="n.style"/>
      <div class="toppings">
        <div class="egg">
          <span class="yolk"/>
        </div>

        <span class="corn c1"/>
        <span class="corn c2"/>
        <span class="corn c3"/>
        <span class="corn c4"/>

        <span class="green g1"/>
        <span class="green g2"/>
        <span class="green g3"/>
        <span class="green g4"/>
        <span class="green g5"/>
        <span class="green g6"/>
        <span class="green g7"/>
        <span class="green g8"/>

        <span class="meat"/>
      </div>
    </div>

    <!-- bowl -->
    <div class="bowl-lip"/>
    <div class="bowl"/>
    <div class="shadow"/>
  </div>
</template>

<script setup>
const steam = [
  { id:1, style:{'--x':'25%','--d':'0s'}},
  { id:2, style:{'--x':'40%','--d':'0.4s'}},
  { id:3, style:{'--x':'55%','--d':'0.2s'}},
  { id:4, style:{'--x':'70%','--d':'0.6s'}}
]

function generateBowlNoodles() {
  const rows = []
  for (let index = 0; index < 96; index += 1) {
    rows.push({
      id: `bowl-${index}`,
      style: {
        '--x': `${Math.random() * 80 + 5}%`,
        '--y': `${Math.random() * 42 + 12}%`,
        '--w': `${Math.random() * 22 + 26}px`,
        '--h': `${Math.random() * 42 + 64}px`,
        '--rot': `${Math.random() * 60 - 30}deg`,
        '--d': `${Math.random() * 1.6}s`,
      },
    })
  }
  return rows
}

function generateLiftedNoodles() {
  const rows = []
  for (let index = 0; index < 32; index += 1) {
    rows.push({
      id: `lift-${index}`,
      style: {
        '--x': `${Math.random() * 40 - 20}px`,
        '--y': `${Math.random() * 48 + 18}px`,
        '--w': `${Math.random() * 20 + 24}px`,
        '--h': `${Math.random() * 40 + 56}px`,
        '--rot': `${Math.random() * 60 - 30}deg`,
        '--d': `${Math.random() * 1.1}s`,
      },
    })
  }
  return rows
}

const noodles = generateBowlNoodles()
const lifted = generateLiftedNoodles()
</script>

<style scoped>
.food-stage {
  width: 240px;
  height: 190px;
  position: relative;
  margin: auto;
  --accent-rgb: var(--loader-accent-rgb, 106 154 107);
  --overlay-color: var(--loader-overlay-color, #f6f4ed);
}

/* steam */
.steam {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 90px;
}

.steam-line {
  position: absolute;
  left: var(--x);
  bottom: 0;
  width: 10px;
  height: 60px;
  border-radius: 100px;
  border: 2px solid rgb(var(--accent-rgb) / 0.34);
  border-color: rgb(var(--accent-rgb) / 0.42) transparent transparent transparent;
  animation: steam 3s ease-in-out infinite;
  animation-delay: var(--d);
  filter: blur(.3px);
}

@keyframes steam {
  0% { transform: translateY(10px) scale(.7); opacity: 0 }
  40% { opacity: .7 }
  100% { transform: translateY(-40px) scale(1.1); opacity: 0 }
}

/* bowl */
.bowl-lip {
  position: absolute;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%);
  width: 170px;
  height: 30px;
  border-radius: 50px;
  background: linear-gradient(
    180deg,
    rgb(255 255 255 / 0.98),
    color-mix(in srgb, rgb(var(--accent-rgb) / 0.26), var(--overlay-color) 74%)
  );
  box-shadow: inset 0 -4px 0 rgb(var(--accent-rgb) / 0.2);
  z-index: 5;
}

.bowl {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 90px;
  border-radius: 0 0 90px 90px;
  background: linear-gradient(
    180deg,
    rgb(var(--accent-rgb) / 0.98),
    rgb(var(--accent-rgb) / 0.74)
  );
  box-shadow:
    inset 0 -10px 20px rgb(0 0 0 / 0.24),
    inset 0 8px 10px rgb(255 255 255 / 0.16);
  z-index: 4;
}

.shadow {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 170px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0,0,0,.25);
  filter: blur(6px);
}

/* soup */
.soup {
  position: absolute;
  bottom: 72px;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 55px;
  border-radius: 50%;
  background: radial-gradient(
    circle at 40% 40%,
    color-mix(in srgb, #ffd58a 78%, rgb(var(--accent-rgb) / 0.4) 22%),
    color-mix(in srgb, #d28b33 58%, rgb(var(--accent-rgb) / 0.62) 42%)
  );
  overflow: hidden;
  z-index: 1;
}

.oil {
  position: absolute;
  width: 14px;
  height: 8px;
  background: color-mix(in srgb, #ffd56d 74%, rgb(var(--accent-rgb) / 0.5) 26%);
  border-radius: 50%;
  animation: oil 4s infinite ease-in-out;
}

.o1 { left: 40%; top: 20% }
.o2 { left: 60%; top: 35% }

@keyframes oil {
  50% { transform: translateY(-3px) }
}

.bubble {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
  opacity: .7;
  animation: bubble 3s infinite;
}

.b1 { left: 45%; bottom: 5px }
.b2 { left: 55%; bottom: 8px }

@keyframes bubble {
  0% { transform: translateY(0); opacity: .2 }
  70% { opacity: .7 }
  100% { transform: translateY(-20px); opacity: 0 }
}

/* noodles */
.noodle-surface {
  position: absolute;
  bottom: 74px;
  left: 50%;
  transform: translateX(-50%);
  width: 146px;
  height: 76px;
  border-radius: 999px;
  overflow: hidden;
  z-index: 2;
}

.noodle {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--w);
  height: var(--h);
  border: 2.5px solid #ffcc33;
  border-bottom: 0;
  border-radius: 999px 999px 0 0;
  transform: rotate(var(--rot));
  animation: noodle-jiggle 1.6s ease-in-out infinite;
  animation-delay: var(--d);
  filter: drop-shadow(1px 1px 1px rgba(0,0,0,.2));
}

@keyframes noodle-jiggle {
  50% { transform: rotate(var(--rot)) translateY(-2px) }
}

/* toppings */
.toppings {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 5;
  pointer-events: none;
}

.egg {
  position: absolute;
  left: 29%;
  top: 24%;
  width: 36px;
  height: 25px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 3px 5px rgba(0,0,0,.2);
  transform: rotate(-8deg);
}

.yolk {
  position: absolute;
  width: 16px;
  height: 16px;
  background: #ffb300;
  border-radius: 50%;
  top: 3px;
  left: 8px;
  box-shadow: inset 0 -2px 4px rgba(0,0,0,.2);
}

.corn {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #ffd84c;
  border-radius: 3px;
  box-shadow: 0 1px 2px rgba(0,0,0,.2);
}

.c1 { left: 70%; top: 34% }
.c2 { left: 63%; top: 44% }
.c3 { left: 75%; top: 53% }
.c4 { left: 68%; top: 58% }

.green {
  position: absolute;
  width: 12px;
  height: 6px;
  background: rgb(var(--accent-rgb) / 0.9);
  border-radius: 3px;
  box-shadow: 0 1px 2px rgba(0,0,0,.2);
}

.g1 { left: 18%; top: 24%; transform: rotate(12deg); }
.g2 { left: 28%; top: 18%; transform: rotate(-8deg); }
.g3 { left: 39%; top: 30%; transform: rotate(28deg); }
.g4 { left: 49%; top: 21%; transform: rotate(-14deg); }
.g5 { left: 58%; top: 33%; transform: rotate(22deg); }
.g6 { left: 67%; top: 25%; transform: rotate(-10deg); }
.g7 { left: 74%; top: 38%; transform: rotate(16deg); }
.g8 { left: 44%; top: 41%; transform: rotate(-24deg); }

.meat {
  position: absolute;
  left: 40%;
  top: 45%;
  width: 35px;
  height: 18px;
  background: linear-gradient(#b55, #7a2a2a);
  border-radius: 8px;
  box-shadow: inset 0 2px 4px rgba(255,255,255,.2), 0 2px 4px rgba(0,0,0,.3);
  transform: rotate(-15deg);
}

/* chopsticks */
.chopsticks {
  position: absolute;
  right: 35px;
  bottom: 142px;
  width: 80px;
  height: 90px;
  transform-origin: bottom right;
  animation: stick 2.5s ease-in-out infinite;
  z-index: 4;
}

@keyframes stick {
  50% { transform: rotate(-4deg) }
}

.stick {
  position: absolute;
  bottom: 0;
  width: 7px;
  height: 110px;
  border-radius: 4px;
  background: linear-gradient(#e8cdab, #b88656);
  box-shadow: -1px 0 3px rgba(0,0,0,.2);
}

.stick.a { left: 28px; transform: rotate(18deg) }
.stick.b { left: 40px; transform: rotate(12deg) }

.lifted {
  position: absolute;
  left: 4px;
  bottom: -12px;
  width: 84px;
  height: 98px;
}

.lift-noodle {
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--w);
  height: var(--h);
  border: 2.5px solid #ffcc33;
  border-bottom: 0;
  border-radius: 999px 999px 0 0;
  transform: rotate(var(--rot));
  animation: noodle-jiggle 1.4s infinite;
  animation-delay: var(--d);
  filter: drop-shadow(1px 1px 1px rgba(0,0,0,.2));
}
</style>
