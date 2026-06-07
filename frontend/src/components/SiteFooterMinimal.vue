<template>
  <footer class="site-footer-minimal" dir="rtl">
    <div class="sfm-inner">
      <span class="sfm-brand">{{ brandName }}</span>
      <span class="sfm-copy">{{ copyright || `© ${new Date().getFullYear()} — تمامی حقوق محفوظ است.` }}</span>
      <nav class="sfm-links">
        <a href="/" class="sfm-link">خانه</a>
        <a href="/menu" class="sfm-link">منو</a>
        <a href="/cart" class="sfm-link">سبد</a>
      </nav>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  brandName: {
    type: String,
    default: '',
  },
  copyright: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.site-footer-minimal {
  border-top: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  background: rgb(var(--palette-eggshell-rgb, 251 248 244) / 0.92);
  direction: rtl;
}

.sfm-inner {
  width: min(1200px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 1rem 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.sfm-brand {
  font-size: 0.88rem;
  font-weight: 800;
  color: var(--ink-800, #3d2e26);
}

.sfm-copy {
  font-size: 0.75rem;
  color: var(--ink-700, #7a6a60);
  flex: 1;
  text-align: center;
}

.sfm-links {
  display: flex;
  gap: 0.4rem;
}

.sfm-link {
  font-size: 0.78rem;
  color: var(--ink-700, #7a6a60);
  text-decoration: none;
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  transition: color 0.15s;
}

.sfm-link:hover {
  color: var(--ink-900, #1c1411);
}

@media (max-width: 520px) {
  .sfm-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.4rem;
  }

  .sfm-copy {
    text-align: right;
  }
}
</style>
