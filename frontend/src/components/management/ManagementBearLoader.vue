<template>
  <div class="bear-loader" :style="{ '--loader-size': `${size}px` }" role="status" aria-live="polite">
    <svg class="bear-svg" viewBox="0 0 340 320" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      <g class="bear-shape">
        <polygon
          v-for="(piece, idx) in pieces"
          :key="`piece-${idx}`"
          class="piece"
          :class="`enter-${piece.e}`"
          :points="piece.p"
          :style="{ '--delay': `${piece.d}s`, '--piece': piece.c }"
        />
      </g>

      <g class="nose-layer">
        <polygon class="nose-top" points="149,222 191,222 170,236" />
        <polygon class="nose-left" points="149,222 170,236 158,254" />
        <polygon class="nose-right" points="191,222 170,236 182,254" />
        <polygon class="nose-bottom" points="158,254 182,254 170,270" />
      </g>

      <g class="eyes-layer">
        <ellipse class="eye-socket" cx="131" cy="167" rx="20" ry="13" />
        <ellipse class="eye-socket" cx="209" cy="167" rx="20" ry="13" />
        <circle class="eye-iris" cx="131" cy="168" r="8.3" />
        <circle class="eye-iris" cx="209" cy="168" r="8.3" />
        <circle class="eye-pupil" cx="131" cy="168" r="4.3" />
        <circle class="eye-pupil" cx="209" cy="168" r="4.3" />
        <circle class="eye-glint" cx="134" cy="165" r="1.55" />
        <circle class="eye-glint" cx="212" cy="165" r="1.55" />
      </g>
    </svg>
    <p v-if="label" class="loader-label">{{ label }}</p>
  </div>
</template>

<script setup>
const props = defineProps({
  label: {
    type: String,
    default: 'در حال بارگذاری مدیریت...',
  },
  size: {
    type: Number,
    default: 236,
  },
})

const rawPieces = [
  { p: '52,88 90,34 112,108', c: '#7D5534', e: 'tl' },
  { p: '112,108 90,34 142,72', c: '#A5754A', e: 'top' },
  { p: '289,88 250,34 228,108', c: '#7D5534', e: 'tr' },
  { p: '228,108 250,34 198,72', c: '#A5754A', e: 'top' },
  { p: '74,98 90,58 104,104', c: '#C9A57E', e: 'tl' },
  { p: '266,98 250,58 236,104', c: '#C9A57E', e: 'tr' },

  { p: '112,108 142,72 170,108', c: '#9B6D43', e: 'top' },
  { p: '228,108 198,72 170,108', c: '#8F633C', e: 'top' },
  { p: '142,72 170,61 170,108', c: '#B4885D', e: 'top' },
  { p: '198,72 170,61 170,108', c: '#A8774C', e: 'top' },

  { p: '62,138 112,108 126,146', c: '#9C6D44', e: 'left' },
  { p: '278,138 228,108 214,146', c: '#8F603A', e: 'right' },
  { p: '62,138 126,146 95,188', c: '#7E5434', e: 'left' },
  { p: '278,138 214,146 245,188', c: '#6F482E', e: 'right' },

  { p: '112,108 126,146 145,142', c: '#C8A178', e: 'center' },
  { p: '228,108 214,146 195,142', c: '#C19A72', e: 'center' },
  { p: '145,142 170,108 195,142', c: '#D7B58C', e: 'center' },
  { p: '126,146 145,142 141,182', c: '#AE7F55', e: 'center' },
  { p: '214,146 195,142 199,182', c: '#A5734C', e: 'center' },

  { p: '145,142 141,182 170,198', c: '#D7BC98', e: 'bottom' },
  { p: '195,142 199,182 170,198', c: '#CCAE89', e: 'bottom' },
  { p: '141,182 170,198 149,222', c: '#E0C6A3', e: 'bottom' },
  { p: '199,182 170,198 191,222', c: '#D5B693', e: 'bottom' },

  { p: '95,188 126,146 141,182', c: '#7A5133', e: 'bl' },
  { p: '245,188 214,146 199,182', c: '#6B442C', e: 'br' },
  { p: '95,188 141,182 138,236', c: '#664127', e: 'bl' },
  { p: '245,188 199,182 202,236', c: '#5B3924', e: 'br' },

  { p: '138,236 149,222 170,270', c: '#90643F', e: 'bottom' },
  { p: '202,236 191,222 170,270', c: '#83593A', e: 'bottom' },
  { p: '138,236 170,270 170,305', c: '#6C472D', e: 'bottom' },
  { p: '202,236 170,270 170,305', c: '#5E3D27', e: 'bottom' },

  { p: '102,232 138,236 170,305', c: '#5A3A26', e: 'bl' },
  { p: '238,232 202,236 170,305', c: '#4E3322', e: 'br' },
  { p: '112,108 62,138 52,88', c: '#6D492E', e: 'left' },
  { p: '228,108 278,138 289,88', c: '#654329', e: 'right' },
]

const pieces = rawPieces.map((piece, index) => ({
  ...piece,
  d: Number(index * 0.045 + 0.08).toFixed(3),
}))
</script>

<style scoped>
.bear-loader {
  --loader-size: 236px;
  display: grid;
  justify-items: center;
  gap: 0.45rem;
}

.bear-svg {
  width: var(--loader-size);
  height: var(--loader-size);
  overflow: visible;
  filter: drop-shadow(0 20px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.24));
}

.bear-shape {
  animation: bob 2.6s ease-in-out infinite;
  transform-origin: 50% 54%;
}

.piece {
  fill: var(--piece);
  opacity: 0;
  transform-box: fill-box;
  transform-origin: center;
  animation:
    piece-in 1.05s cubic-bezier(0.24, 0.96, 0.38, 1.15) var(--delay) both,
    piece-glow 3.6s ease-in-out calc(var(--delay) + 1.1s) infinite;
}

.enter-tl {
  transform: translate(-34px, -34px) rotate(-18deg) scale(0.88);
}

.enter-tr {
  transform: translate(34px, -34px) rotate(18deg) scale(0.88);
}

.enter-top {
  transform: translateY(-42px) rotate(10deg) scale(0.9);
}

.enter-left {
  transform: translateX(-40px) rotate(-14deg) scale(0.9);
}

.enter-right {
  transform: translateX(40px) rotate(14deg) scale(0.9);
}

.enter-bl {
  transform: translate(-30px, 30px) rotate(-12deg) scale(0.88);
}

.enter-br {
  transform: translate(30px, 30px) rotate(12deg) scale(0.88);
}

.enter-bottom {
  transform: translateY(40px) rotate(-6deg) scale(0.9);
}

.enter-center {
  transform: scale(0.8) rotate(8deg);
}

.nose-layer {
  animation: nose-breathe 2.6s ease-in-out infinite;
  transform-origin: 50% 75%;
}

.nose-top {
  fill: #3c342f;
}

.nose-left,
.nose-right {
  fill: #201c1a;
}

.nose-bottom {
  fill: #111010;
}

.eyes-layer {
  animation: blink 4.4s linear infinite;
}

.eye-socket {
  fill: #2c211c;
  opacity: 0.8;
}

.eye-iris {
  fill: #6b4628;
}

.eye-pupil {
  fill: #14100f;
}

.eye-glint {
  fill: #f9f4ee;
  opacity: 0.9;
}

.loader-label {
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-muted);
  font-weight: 600;
}

@keyframes piece-in {
  to {
    opacity: 1;
    transform: translate(0, 0) rotate(0) scale(1);
  }
}

@keyframes piece-glow {
  0%,
  100% {
    filter: brightness(1);
  }
  50% {
    filter: brightness(1.06);
  }
}

@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

@keyframes nose-breathe {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}

@keyframes blink {
  0%,
  45%,
  48%,
  100% {
    transform: scaleY(1);
    transform-origin: center;
  }
  46.5% {
    transform: scaleY(0.22);
    transform-origin: center;
  }
}
</style>
