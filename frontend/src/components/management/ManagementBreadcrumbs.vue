<template>
  <nav class="mg-breadcrumbs" aria-label="مسیر صفحه">
    <!-- دکمه بازگشت (موبایل) -->
    <a
      v-if="backHref"
      class="mg-back"
      :href="backHref"
      :aria-label="`بازگشت به ${backLabel}`"
      :title="backLabel"
    >
      <ArrowRight :size="18" :stroke-width="2.2" />
    </a>

    <div class="mg-crumbs-scroll">
      <template v-for="(item, idx) in items" :key="`${item.label}-${idx}`">
        <a
          v-if="item.href && idx < items.length - 1"
          class="mg-crumb mg-crumb--link"
          :href="item.href"
        >{{ item.label }}</a>
        <span v-else class="mg-crumb mg-crumb--current" :title="item.label">{{ item.label }}</span>
        <span v-if="idx < items.length - 1" class="mg-crumb-sep" aria-hidden="true">/</span>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { computed } from "vue";
import { ArrowRight } from "lucide-vue-next";

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

// والد قابل بازگشت = آخرین آیتم دارای لینک (برای موبایل)
const backHref = computed(() => {
  const parents = (props.items || []).filter((item) => item.href)
  return parents.length ? parents[parents.length - 1].href : ""
})

const backLabel = computed(() => {
  const parents = (props.items || []).filter((item) => item.href)
  return parents.length ? parents[parents.length - 1].label : ""
})
</script>

<style scoped>
.mg-breadcrumbs {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.74rem;
  color: var(--mg-text-muted);
  min-width: 0;
}

.mg-crumbs-scroll {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
  min-width: 0;
}

/* دکمه بازگشت — فقط موبایل نمایش داده می‌شود */
.mg-back {
  display: none;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  text-decoration: none;
  box-shadow: var(--mg-shadow-sm);
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.mg-back:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light));
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface));
}

.mg-back:active {
  transform: scale(0.95);
}

.mg-crumb {
  color: var(--mg-text-muted);
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
}

.mg-crumb--link:hover {
  color: var(--mg-primary);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.mg-crumb--current {
  color: var(--mg-text-main);
  font-weight: 800;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mg-crumb-sep {
  color: var(--mg-text-muted);
  opacity: 0.5;
  font-size: 0.7rem;
}

/* ── موبایل: نوار بزرگ و لمسی ── */
@media (max-width: 640px) {
  .mg-breadcrumbs {
    font-size: 0.8rem;
    gap: 0.4rem;
    padding: 0.4rem 0.55rem;
    border: 1px solid var(--mg-border-light);
    border-radius: 14px;
    background: var(--mg-bg-surface);
    box-shadow: var(--mg-shadow-sm);
  }

  .mg-back {
    display: inline-flex;
  }

  .mg-crumbs-scroll {
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }

  .mg-crumbs-scroll::-webkit-scrollbar {
    display: none;
  }

  .mg-crumb--current {
    font-size: 0.84rem;
    max-width: none;
  }
}
</style>
