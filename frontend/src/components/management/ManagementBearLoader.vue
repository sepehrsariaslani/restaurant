<template>
  <div class="bear-loader" :style="{ '--loader-size': `${size}px` }" role="status" aria-live="polite">
    <div class="bear-stage">
      <span class="bear-halo" aria-hidden="true"></span>
      <span class="bear-ground" aria-hidden="true"></span>
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

        <g class="cheek-layer" aria-hidden="true">
          <ellipse class="cheek" cx="102" cy="196" rx="14" ry="9" />
          <ellipse class="cheek" cx="238" cy="196" rx="14" ry="9" />
        </g>
      </svg>
    </div>

    <p v-if="brand" class="loader-brand">{{ brand }}</p>
    <p v-if="label" class="loader-label">{{ label }}</p>
  </div>
</template>

<script setup>
const props = defineProps({
  label: {
    type: String,
    default: 'در حال بارگذاری مدیریت...',
  },
  brand: {
    type: String,
    default: '',
  },
  size: {
    type: Number,
    default: 236,
  },
})

// پالت رنگ‌های اصلی سیستم: سبز موفقیت، زیتونی، نارنجی + سایه‌ها
const PALETTE = [
  '#6F7B56', '#8A8B63', '#C97852',
  '#7F8B60', '#9A9B74', '#D4885F',
  '#5F6B4C', '#7A7B58', '#B46845',
]

const rawPieces = [
  { p: '52,88 90,34 112,108', e: 'tl' },
  { p: '112,108 90,34 142,72', e: 'top' },
  { p: '289,88 250,34 228,108', e: 'tr' },
  { p: '228,108 250,34 198,72', e: 'top' },
  { p: '74,98 90,58 104,104', e: 'tl' },
  { p: '266,98 250,58 236,104', e: 'tr' },

  { p: '112,108 142,72 170,108', e: 'top' },
  { p: '228,108 198,72 170,108', e: 'top' },
  { p: '142,72 170,61 170,108', e: 'top' },
  { p: '198,72 170,61 170,108', e: 'top' },

  { p: '62,138 112,108 126,146', e: 'left' },
  { p: '278,138 228,108 214,146', e: 'right' },
  { p: '62,138 126,146 95,188', e: 'left' },
  { p: '278,138 214,146 245,188', e: 'right' },

  { p: '112,108 126,146 145,142', e: 'center' },
  { p: '228,108 214,146 195,142', e: 'center' },
  { p: '145,142 170,108 195,142', e: 'center' },
  { p: '126,146 145,142 141,182', e: 'center' },
  { p: '214,146 195,142 199,182', e: 'center' },

  { p: '145,142 141,182 170,198', e: 'bottom' },
  { p: '195,142 199,182 170,198', e: 'bottom' },
  { p: '141,182 170,198 149,222', e: 'bottom' },
  { p: '199,182 170,198 191,222', e: 'bottom' },

  { p: '95,188 126,146 141,182', e: 'bl' },
  { p: '245,188 214,146 199,182', e: 'br' },
  { p: '95,188 141,182 138,236', e: 'bl' },
  { p: '245,188 199,182 202,236', e: 'br' },

  { p: '138,236 149,222 170,270', e: 'bottom' },
  { p: '202,236 191,222 170,270', e: 'bottom' },
  { p: '138,236 170,270 170,305', e: 'bottom' },
  { p: '202,236 170,270 170,305', e: 'bottom' },

  { p: '102,232 138,236 170,305', e: 'bl' },
  { p: '238,232 202,236 170,305', e: 'br' },
  { p: '112,108 62,138 52,88', e: 'left' },
  { p: '228,108 278,138 289,88', e: 'right' },
]

const pieces = rawPieces.map((piece, index) => ({
  ...piece,
  c: PALETTE[index % PALETTE.length],
  d: Number(index * 0.045 + 0.08).toFixed(3),
}))
</script>

<style scoped>
.bear-loader {
  --loader-size: 236px;
  display: grid;
  justify-items: center;
  gap: 0.35rem;
  text-align: center;
}

.bear-stage {
  position: relative;
  width: var(--loader-size);
  height: var(--loader-size);
  display: grid;
  place-items: center;
}

/* هاله نرم رنگی پشت خرس */
.bear-halo {
  position: absolute;
  inset: 6%;
  border-radius: 50%;
  background: radial-gradient(
    circle at 50% 45%,
    color-mix(in srgb, var(--mg-primary, #c97852) 20%, transparent) 0%,
    color-mix(in srgb, var(--mg-success, #6f7b56) 14%, transparent) 48%,
    color-mix(in srgb, var(--mg-olive, #8a8b63) 8%, transparent) 72%,
    transparent 100%
  );
  animation: halo-pulse 3.2s ease-in-out infinite;
}

/* سایه زمین زیر خرس */
.bear-ground {
  position: absolute;
  bottom: 4%;
  left: 50%;
  width: 52%;
  height: 11px;
  transform: translateX(-50%);
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgb(52 38 31 / 0.22) 0%, transparent 70%);
  animation: ground-breathe 2.6s ease-in-out infinite;
}

.bear-svg {
  width: 86%;
  height: 86%;
  overflow: visible;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 16px 22px rgb(52 38 31 / 0.2));
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
  fill: var(--mg-primary, #c97852);
}

.eye-pupil {
  fill: #14100f;
}

.eye-glint {
  fill: #f9f4ee;
  opacity: 0.9;
}

.cheek-layer {
  animation: blush 3.2s ease-in-out infinite;
}

.cheek {
  fill: color-mix(in srgb, var(--mg-primary, #c97852) 34%, transparent);
  opacity: 0.55;
}

.loader-brand {
  margin: 0.3rem 0 0;
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  background: linear-gradient(
    120deg,
    var(--mg-primary, #c97852) 0%,
    var(--mg-olive, #8a8b63) 55%,
    var(--mg-success, #6f7b56) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.loader-label {
  margin: 0;
  font-size: 0.8rem;
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
    filter: brightness(1.07);
  }
}

@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

@keyframes halo-pulse {
  0%,
  100% {
    opacity: 0.75;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.045);
  }
}

@keyframes ground-breathe {
  0%,
  100% {
    opacity: 0.55;
    transform: translateX(-50%) scale(1);
  }
  50% {
    opacity: 0.8;
    transform: translateX(-50%) scale(1.08);
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

@keyframes blush {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.75;
  }
}
</style>
