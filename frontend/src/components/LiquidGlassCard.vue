<template>
  <section
    class="liquid-card"
    :class="{
      'liquid-card--hoverable': hoverable,
      [`liquid-card--${variant}`]: variant !== 'default',
    }"
  >
    <slot />
  </section>
</template>

<script setup>
defineProps({
  hoverable: {
    type: Boolean,
    default: false,
  },
  /**
   * variant:
   *  'default'  — شفاف سبز روشن
   *  'dark'     — تیره‌تر (برای پنل‌های summary)
   *  'frosted'  — مات‌تر
   */
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'dark', 'frosted'].includes(v),
  },
})
</script>

<style scoped>
/* ─────────────────────────────────────────────
   توکن‌های محلی – fallback برای حالت روشن سبز
───────────────────────────────────────────── */
.liquid-card {
  --glass-bg:          rgba(255, 255, 255, 0.58);
  --glass-border:      rgba(255, 255, 255, 0.80);
  --glass-shadow:      0 24px 56px rgb(var(--palette-deep-sapphire-rgb) / 0.14),
                       0  4px 12px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  --glass-shadow-deep: 0 32px 72px rgb(var(--palette-deep-sapphire-rgb) / 0.22),
                       0  8px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  --glass-bg-strong:   rgba(255, 255, 255, 0.78);
  --blur:              blur(22px) saturate(180%) brightness(1.03);
  --blur-strong:       blur(36px) saturate(200%) brightness(1.05);
  --radius-lg:         32px;
}

/* ─────────────────────────────────────────────
   پایه کارت
───────────────────────────────────────────── */
.liquid-card {
  position: relative;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}

/* درخشش سفید بالای کارت */
.liquid-card::before {
  content: none;
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  z-index: 0;
}

/* خط نور سبز پایین کارت */
.liquid-card::after {
  content: none;
  position: absolute;
  bottom: 0;
  left: 12%;
  width: 76%;
  height: 1px;
  pointer-events: none;
  z-index: 0;
}

/* محتوای slot روی pseudo-elementها */
.liquid-card > :deep(*) {
  position: relative;
  z-index: 1;
}

/* ─────────────────────────────────────────────
   variant: dark – تیره‌تر برای پنل summary
───────────────────────────────────────────── */
.liquid-card--dark {
  background: #fff;
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  box-shadow:
    0 20px 44px rgb(15 23 42 / 0.1),
    0 4px 12px rgb(15 23 42 / 0.06);
  color: var(--text-primary);
}

/* درخشش سبز بسیار کم‌رنگ برای variant dark */
.liquid-card--dark::before {
  background: none;
}

.liquid-card--dark::after {
  background: none;
}

/* ─────────────────────────────────────────────
   variant: frosted – مات‌تر
───────────────────────────────────────────── */
.liquid-card--frosted {
  background: #fff;
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow:
    0 0 0 1px rgb(var(--palette-deep-sapphire-rgb) / 0.08) inset,
    0 16px 36px rgb(15 23 42 / 0.08);
}

/* ─────────────────────────────────────────────
   hoverable
───────────────────────────────────────────── */
.liquid-card--hoverable {
  cursor: pointer;
}

.liquid-card--hoverable:hover {
  transform: translateY(-4px);
  box-shadow: var(--glass-shadow-deep);
}

/* برای variant dark در حالت hover */
.liquid-card--dark.liquid-card--hoverable:hover {
  box-shadow:
    0 40px 88px rgba(0, 20, 8, 0.48),
    0 10px 24px rgba(0, 20, 8, 0.28);
}
</style>
