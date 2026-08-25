<template>
  <section class="notfound-page" dir="rtl" aria-labelledby="not-found-title">
    <div class="nf-bg" aria-hidden="true">
      <span class="nf-orb nf-orb--one"></span>
      <span class="nf-orb nf-orb--two"></span>
      <span class="nf-orb nf-orb--three"></span>
    </div>

    <article class="nf-card">
      <div class="nf-kitchen-scene" aria-hidden="true">
        <div class="nf-steam nf-steam--one"></div>
        <div class="nf-steam nf-steam--two"></div>
        <div class="nf-steam nf-steam--three"></div>

        <svg class="nf-pan" viewBox="0 0 260 180" role="img" aria-label="تابه خالی">
          <defs>
            <linearGradient id="panSurface" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#3F2A1D" />
              <stop offset="100%" stop-color="#6F4A31" />
            </linearGradient>
            <linearGradient id="sauceGlow" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#F4B45F" />
              <stop offset="100%" stop-color="#C98D42" />
            </linearGradient>
          </defs>
          <path class="nf-pan-handle" d="M174 107 C204 101 229 96 245 92 C252 91 258 96 259 103 C260 110 255 116 248 117 C228 119 204 120 177 121 Z" />
          <ellipse class="nf-pan-shadow" cx="115" cy="143" rx="88" ry="15" />
          <path class="nf-pan-body" d="M31 78 C47 46 85 33 129 38 C174 43 204 66 202 99 C200 131 162 151 113 148 C64 145 21 119 31 78 Z" />
          <path class="nf-pan-lip" d="M44 82 C59 57 88 47 126 50 C163 53 190 71 190 96 C190 121 157 136 114 134 C72 132 35 108 44 82 Z" />
          <path class="nf-sauce" d="M82 86 C91 72 115 71 128 83 C142 96 163 89 169 105 C175 121 147 126 126 121 C107 116 88 125 76 112 C66 101 73 93 82 86 Z" />
          <circle class="nf-dot nf-dot--one" cx="107" cy="96" r="5" />
          <circle class="nf-dot nf-dot--two" cx="140" cy="105" r="4" />
          <circle class="nf-dot nf-dot--three" cx="122" cy="112" r="3" />
        </svg>

        <div class="nf-code">۴۰۴</div>
      </div>

      <p class="nf-eyebrow">آشپزخانه این مسیر را پیدا نکرد</p>
      <h1 id="not-found-title" class="nf-title">این صفحه از منو حذف شده!</h1>
      <p class="nf-subtitle">
        آدرسی که وارد کردید پیدا نشد. می‌توانید به منو برگردید، سفارش جدید شروع کنید یا مسیر درست را جستجو کنید.
      </p>

      <div class="nf-actions" aria-label="مسیرهای پیشنهادی">
        <a class="nf-btn nf-btn--primary" href="/order/type">
          <span>شروع سفارش جدید</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </a>
        <a class="nf-btn nf-btn--secondary" href="/menu">مشاهده منو</a>
      </div>

      <nav class="nf-quick" aria-label="لینک‌های سریع">
        <a href="/">خانه</a>
        <a href="/cart">سبد سفارش</a>
        <a href="/customer/orders">پیگیری سفارش</a>
        <a href="/customer/dashboard">داشبورد مشتری</a>
      </nav>

      <p class="nf-note">اگر از لینک QR یا پیامک وارد شده‌اید، ممکن است لینک قدیمی شده باشد.</p>
    </article>
  </section>
</template>

<script setup>
</script>

<style scoped>
.notfound-page {
  position: relative;
  min-height: 100dvh;
  overflow: hidden;
  display: grid;
  place-items: center;
  padding: max(1rem, env(safe-area-inset-top)) 1rem max(5rem, env(safe-area-inset-bottom));
  background:
    radial-gradient(circle at 18% 18%, rgba(201, 141, 66, 0.26), transparent 30%),
    radial-gradient(circle at 84% 76%, rgba(47, 143, 91, 0.18), transparent 32%),
    linear-gradient(135deg, #fbf8f4 0%, #f1e7db 48%, #e9dccd 100%);
  color: #3f2a1d;
}

.nf-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.nf-orb {
  position: absolute;
  width: 12rem;
  height: 12rem;
  border-radius: 999px;
  filter: blur(18px);
  opacity: 0.32;
}

.nf-orb--one {
  top: 8%;
  right: 8%;
  background: #c98d42;
}

.nf-orb--two {
  bottom: 10%;
  left: 6%;
  background: #2f8f5b;
}

.nf-orb--three {
  top: 48%;
  left: 28%;
  background: #d5c3af;
}

.nf-card {
  position: relative;
  z-index: 1;
  width: min(100%, 620px);
  border: 1px solid rgba(111, 74, 49, 0.16);
  border-radius: 32px;
  padding: clamp(1.25rem, 4vw, 2.25rem);
  text-align: center;
  background: rgba(255, 252, 248, 0.86);
  box-shadow: 0 24px 70px rgba(63, 42, 29, 0.16);
  backdrop-filter: blur(18px);
}

.nf-kitchen-scene {
  position: relative;
  width: min(100%, 320px);
  height: 225px;
  margin: 0 auto 0.75rem;
  display: grid;
  place-items: end center;
}

.nf-pan {
  width: 100%;
  max-width: 300px;
  filter: drop-shadow(0 18px 22px rgba(63, 42, 29, 0.22));
  animation: pan-float 4.8s ease-in-out infinite;
}

.nf-pan-handle {
  fill: #5b3924;
}

.nf-pan-shadow {
  fill: rgba(63, 42, 29, 0.16);
}

.nf-pan-body {
  fill: url(#panSurface);
}

.nf-pan-lip {
  fill: #f7efe4;
  opacity: 0.92;
}

.nf-sauce {
  fill: url(#sauceGlow);
}

.nf-dot {
  fill: #7d5534;
  opacity: 0.72;
}

.nf-steam {
  position: absolute;
  bottom: 128px;
  width: 12px;
  height: 72px;
  border-radius: 999px;
  background: linear-gradient(to top, rgba(111, 74, 49, 0), rgba(111, 74, 49, 0.22), rgba(111, 74, 49, 0));
  transform-origin: bottom center;
  animation: steam-rise 2.8s ease-in-out infinite;
}

.nf-steam--one {
  right: 39%;
  animation-delay: 0s;
}

.nf-steam--two {
  right: 49%;
  height: 88px;
  animation-delay: 0.45s;
}

.nf-steam--three {
  right: 58%;
  animation-delay: 0.9s;
}

.nf-code {
  position: absolute;
  top: 18px;
  right: 50%;
  transform: translateX(50%) rotate(-4deg);
  display: inline-grid;
  place-items: center;
  min-width: 104px;
  min-height: 54px;
  padding: 0.25rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 999px;
  color: #fffaf2;
  background: linear-gradient(135deg, #6f4a31, #3f2a1d);
  box-shadow: 0 14px 30px rgba(63, 42, 29, 0.22);
  font-size: clamp(1.55rem, 7vw, 2.7rem);
  font-weight: 1000;
  letter-spacing: 0.05em;
}

.nf-eyebrow {
  margin: 0;
  color: #2f8f5b;
  font-size: 0.92rem;
  font-weight: 900;
}

.nf-title {
  margin: 0.45rem 0 0;
  color: #3f2a1d;
  font-size: clamp(1.85rem, 7vw, 3.25rem);
  line-height: 1.15;
  font-weight: 1000;
  letter-spacing: -0.04em;
}

.nf-subtitle {
  max-width: 48ch;
  margin: 0.85rem auto 0;
  color: #654a38;
  font-size: clamp(0.98rem, 2.5vw, 1.08rem);
  line-height: 1.9;
}

.nf-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  margin: 1.4rem auto 0;
  width: min(100%, 430px);
}

.nf-btn {
  min-height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border-radius: 18px;
  text-decoration: none;
  font-weight: 900;
  transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
  touch-action: manipulation;
}

.nf-btn:focus-visible,
.nf-quick a:focus-visible {
  outline: 3px solid rgba(47, 143, 91, 0.42);
  outline-offset: 3px;
}

.nf-btn:hover {
  transform: translateY(-2px);
}

.nf-btn--primary {
  color: #fffaf2;
  background: linear-gradient(135deg, #6f4a31, #8a5d38);
  box-shadow: 0 14px 28px rgba(111, 74, 49, 0.22);
}

.nf-btn--primary svg {
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
  transform: scaleX(-1);
}

.nf-btn--secondary {
  color: #5b3924;
  background: #fffaf2;
  border: 1px solid rgba(111, 74, 49, 0.18);
}

.nf-quick {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1.25rem;
}

.nf-quick a {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.9rem;
  border: 1px solid rgba(111, 74, 49, 0.12);
  border-radius: 999px;
  color: #654a38;
  background: rgba(255, 255, 255, 0.62);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 800;
}

.nf-quick a:hover {
  background: #fffaf2;
}

.nf-note {
  margin: 1rem 0 0;
  color: #846b58;
  font-size: 0.88rem;
  line-height: 1.8;
}

@keyframes steam-rise {
  0% {
    opacity: 0;
    transform: translateY(18px) scaleX(0.7) rotate(7deg);
  }
  35% {
    opacity: 0.72;
  }
  100% {
    opacity: 0;
    transform: translateY(-34px) scaleX(1.35) rotate(-8deg);
  }
}

@keyframes pan-float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-6px) rotate(-1.2deg);
  }
}

@media (min-width: 620px) {
  .nf-actions {
    grid-template-columns: 1.2fr 0.8fr;
  }
}

@media (max-width: 420px) {
  .nf-card {
    border-radius: 26px;
  }

  .nf-kitchen-scene {
    height: 195px;
  }

  .nf-steam {
    bottom: 112px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .nf-pan,
  .nf-steam,
  .nf-btn {
    animation: none;
    transition: none;
  }

  .nf-btn:hover {
    transform: none;
  }
}
</style>
