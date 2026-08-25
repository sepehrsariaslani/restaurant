<template>
  <div class="food-stage club-stage" aria-hidden="true">
    <span class="club-shadow" />
    <div class="club-build">
      <span
        v-for="layer in clubLayers"
        :key="layer.id"
        class="club-layer"
        :class="layer.className"
        :style="layer.style"
      />
      <span class="club-stick" />
      <span class="club-olive" />
    </div>
  </div>
</template>

<script setup>
const clubLayers = [
  { id: 'cb-0', className: 'club-toast', style: { '--delay': '0s', '--drop-y': '-132px', '--z': '0px', '--tilt': '-7deg', '--level': '1' } },
  { id: 'cb-1', className: 'club-turkey', style: { '--delay': '0.14s', '--drop-y': '-140px', '--z': '10px', '--tilt': '-6deg', '--level': '2' } },
  { id: 'cb-2', className: 'club-cheese', style: { '--delay': '0.28s', '--drop-y': '-148px', '--z': '17px', '--tilt': '-6deg', '--level': '3' } },
  { id: 'cb-3', className: 'club-bacon', style: { '--delay': '0.42s', '--drop-y': '-156px', '--z': '24px', '--tilt': '-5deg', '--level': '4' } },
  { id: 'cb-4', className: 'club-lettuce', style: { '--delay': '0.56s', '--drop-y': '-164px', '--z': '31px', '--tilt': '-5deg', '--level': '5' } },
  { id: 'cb-5', className: 'club-tomato', style: { '--delay': '0.7s', '--drop-y': '-172px', '--z': '38px', '--tilt': '-5deg', '--level': '6' } },
  { id: 'cb-6', className: 'club-toast-top', style: { '--delay': '0.84s', '--drop-y': '-180px', '--z': '46px', '--tilt': '-5deg', '--level': '7' } },
]
</script>

<style scoped>
.food-stage {
  width: min(86vw, 250px);
  height: 240px;
  position: relative;
  --accent-rgb: var(--loader-accent-rgb, 106 154 107);
}

.club-stage {
  display: grid;
  place-items: center;
}

.club-shadow {
  position: absolute;
  bottom: 16px;
  width: 190px;
  height: 24px;
  border-radius: 50%;
  background: rgb(0 0 0 / 0.22);
  filter: blur(5px);
  animation: shadow-pulse 3.2s cubic-bezier(0.24, 0.72, 0.2, 1) infinite;
}

.club-build {
  position: relative;
  width: 190px;
  height: 210px;
  transform: translateY(2px) rotateX(5deg);
  transform-style: preserve-3d;
  perspective: 880px;
  perspective-origin: 50% 68%;
}

.club-layer {
  position: absolute;
  left: 50%;
  transform: translateX(-50%) translateY(var(--drop-y)) translateZ(var(--z)) rotateX(var(--tilt));
  transform-style: preserve-3d;
  opacity: 0;
  z-index: var(--level);
  animation: club-drop 3.2s cubic-bezier(0.22, 0.74, 0.18, 1) infinite;
  animation-delay: var(--delay);
  animation-fill-mode: both;
  filter: drop-shadow(0 3px 2px rgb(0 0 0 / 0.16));
  will-change: transform, opacity;
}

.club-layer::before,
.club-layer::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.club-toast {
  bottom: 48px;
  width: 160px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f5d7a8, #e7bc84 60%, #d7a46b);
  box-shadow:
    inset 0 -4px 0 rgb(177 118 62 / 0.35),
    inset 0 2px 2px rgb(255 255 255 / 0.34);
}

.club-toast::before {
  inset: 4px 7px 6px;
  border-radius: 6px;
  background: linear-gradient(180deg, #f8e6c4, #f1d4a8);
  opacity: 0.92;
}

.club-toast::after {
  left: 10px;
  right: 10px;
  bottom: -8px;
  height: 11px;
  border-radius: 0 0 8px 8px;
  background: linear-gradient(180deg, rgb(159 103 54 / 0.52), rgb(124 80 41 / 0.2));
  transform: rotateX(76deg);
  transform-origin: top;
}

.club-toast-top {
  bottom: 132px;
  width: 152px;
  height: 23px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f6daad, #e9bf87 60%, #d9a96f);
  box-shadow:
    inset 0 -4px 0 rgb(177 118 62 / 0.33),
    inset 0 2px 2px rgb(255 255 255 / 0.34);
}

.club-toast-top::before {
  inset: 4px 7px 6px;
  border-radius: 6px;
  background: linear-gradient(180deg, #f9e8c7, #f3d8ad);
  opacity: 0.92;
}

.club-toast-top::after {
  left: 10px;
  right: 10px;
  bottom: -8px;
  height: 10px;
  border-radius: 0 0 8px 8px;
  background: linear-gradient(180deg, rgb(159 103 54 / 0.48), rgb(124 80 41 / 0.18));
  transform: rotateX(76deg);
  transform-origin: top;
}

.club-turkey {
  bottom: 70px;
  width: 154px;
  height: 15px;
  border-radius: 7px;
  background: linear-gradient(180deg, #f6d4ce, #e7b8af 64%, #d9a69f);
  box-shadow: inset 0 -2px 0 rgb(156 106 99 / 0.24);
}

.club-turkey::after {
  left: 9px;
  right: 9px;
  bottom: -6px;
  height: 8px;
  border-radius: 0 0 999px 999px;
  background: linear-gradient(180deg, rgb(150 102 94 / 0.44), rgb(150 102 94 / 0.12));
  transform: rotateX(73deg);
  transform-origin: top;
}

.club-cheese {
  bottom: 84px;
  width: 162px;
  height: 10px;
  border-radius: 3px;
  background: linear-gradient(180deg, #ffd754, #f2ba27);
}

.club-cheese::after {
  left: 10px;
  right: 10px;
  bottom: -5px;
  height: 7px;
  border-radius: 0 0 999px 999px;
  background: linear-gradient(180deg, rgb(183 127 16 / 0.42), rgb(183 127 16 / 0.12));
  transform: rotateX(73deg);
  transform-origin: top;
}

.club-bacon {
  bottom: 95px;
  width: 150px;
  height: 11px;
  border-radius: 3px;
  background: repeating-linear-gradient(90deg, #7c2616, #7c2616 10px, #b04632 10px, #b04632 20px);
}

.club-bacon::after {
  left: 8px;
  right: 8px;
  bottom: -5px;
  height: 7px;
  border-radius: 0 0 999px 999px;
  background: linear-gradient(180deg, rgb(86 28 20 / 0.46), rgb(86 28 20 / 0.14));
  transform: rotateX(74deg);
  transform-origin: top;
}

.club-lettuce {
  bottom: 106px;
  width: 165px;
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(180deg, rgb(var(--accent-rgb) / 0.96), rgb(var(--accent-rgb) / 0.74));
  clip-path: polygon(0 10%, 10% 80%, 20% 10%, 30% 90%, 40% 10%, 50% 100%, 60% 10%, 70% 90%, 80% 10%, 90% 80%, 100% 10%, 100% 100%, 0 100%);
}

.club-lettuce::after {
  left: 9px;
  right: 9px;
  bottom: -6px;
  height: 8px;
  border-radius: 0 0 999px 999px;
  background: linear-gradient(180deg, rgb(20 49 20 / 0.42), rgb(20 49 20 / 0.12));
  transform: rotateX(74deg);
  transform-origin: top;
}

.club-tomato {
  bottom: 120px;
  width: 142px;
  height: 11px;
  border-radius: 4px;
  background: linear-gradient(180deg, #eb6a61, #ce3e34);
}

.club-tomato::before {
  inset: 2px 12px 3px;
  border-radius: 999px;
  background:
    radial-gradient(circle at 20% 45%, rgb(255 220 205 / 0.45) 0 2px, transparent 2px),
    radial-gradient(circle at 40% 55%, rgb(255 220 205 / 0.45) 0 2px, transparent 2px),
    radial-gradient(circle at 58% 44%, rgb(255 220 205 / 0.45) 0 2px, transparent 2px),
    radial-gradient(circle at 78% 54%, rgb(255 220 205 / 0.45) 0 2px, transparent 2px);
}

.club-tomato::after {
  left: 8px;
  right: 8px;
  bottom: -5px;
  height: 7px;
  border-radius: 0 0 999px 999px;
  background: linear-gradient(180deg, rgb(108 31 27 / 0.45), rgb(108 31 27 / 0.14));
  transform: rotateX(73deg);
  transform-origin: top;
}

.club-stick,
.club-olive {
  position: absolute;
  left: 50%;
  opacity: 0;
  animation: pin-pop 3.2s ease-in-out infinite;
}

.club-stick {
  --pin-z: 56px;
  bottom: 62px;
  width: 5px;
  height: 128px;
  transform: translateX(-50%) translateZ(var(--pin-z));
  background: linear-gradient(90deg, #e0c79f, #bc9869);
  border-radius: 4px;
  z-index: 10;
}

.club-olive {
  --pin-z: 58px;
  bottom: 190px;
  width: 20px;
  height: 24px;
  transform: translateX(-50%) translateZ(var(--pin-z));
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #dcf5d7, rgb(var(--accent-rgb) / 0.9));
  z-index: 11;
}

@keyframes club-drop {
  0% {
    transform: translateX(-50%) translateY(var(--drop-y)) translateZ(var(--z)) rotateX(var(--tilt));
    opacity: 0;
  }
  14% {
    transform: translateX(-50%) translateY(0) translateZ(var(--z)) rotateX(var(--tilt));
    opacity: 1;
  }
  22% {
    transform: translateX(-50%) translateY(-2px) translateZ(var(--z)) rotateX(var(--tilt));
    opacity: 1;
  }
  30%,
  78% {
    transform: translateX(-50%) translateY(0) translateZ(var(--z)) rotateX(var(--tilt));
    opacity: 1;
  }
  100% {
    transform: translateX(-50%) translateY(44px) translateZ(var(--z)) rotateX(var(--tilt));
    opacity: 0;
  }
}

@keyframes pin-pop {
  0%,
  48% {
    opacity: 0;
    transform: translateX(-50%) translateY(-28px) translateZ(var(--pin-z));
  }
  58%,
  80% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) translateZ(var(--pin-z));
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(44px) translateZ(var(--pin-z));
  }
}

@keyframes shadow-pulse {
  0%,
  100% {
    transform: scale(0.78);
    opacity: 0;
  }
  30%,
  78% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
