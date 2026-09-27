<template>
  <div v-if="kind === 'text'" class="site-element-text">
    <component :is="heading" v-if="title" data-design-field="title">{{ title }}</component>
    <p v-if="body" data-design-field="body">{{ body }}</p>
  </div>
  <figure v-else-if="kind === 'image'" class="site-element-image">
    <img v-if="safeDesignUrl(image)" :src="safeDesignUrl(image)" :alt="alt" loading="lazy" />
    <div v-else class="site-element-empty">تصویر را از پنل ویژگی‌ها انتخاب کنید</div>
    <figcaption v-if="caption" data-design-field="caption">{{ caption }}</figcaption>
  </figure>
  <a v-else-if="kind === 'button'" class="site-element-button" :class="`site-element-button--${variant}`" :href="safeDesignUrl(href, '#')" data-design-field="label">{{ label }}</a>
  <hr v-else-if="kind === 'divider'" class="site-element-divider" />
  <div v-else-if="kind === 'spacer'" :style="{ height: `${Math.max(0, Math.min(800, Number(height) || 32))}px` }" aria-hidden="true" />
</template>
<script setup>
import { computed } from 'vue'
import { safeDesignUrl } from '@/utils/designBlockStyle'
const props = defineProps({ kind: String, title: String, body: String, image: String, alt: String, caption: String, label: String, href: String, variant: String, level: String, height: [String, Number] })
const heading = computed(() => ['h1', 'h2', 'h3', 'h4'].includes(props.level) ? props.level : 'h2')
</script>
<style scoped>
.site-element-text p { white-space: pre-line; line-height: 1.9; }
.site-element-text h1,.site-element-text h2,.site-element-text h3,.site-element-text h4 { margin: 0 0 .75rem; font-size: 1.6em; line-height: 1.5; }
.site-element-image { margin: 0; }
.site-element-image img { display: block; width: 100%; height: auto; border-radius: inherit; }
.site-element-image figcaption { padding-block: .5rem; color: var(--ds-color-text-secondary); }
.site-element-empty { padding: 3rem 1rem; text-align: center; background: var(--ds-color-surface-muted); }
.site-element-button { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: .75rem 1.5rem; border: 1px solid var(--ds-color-action-primary); border-radius: var(--ds-radius-control, 12px); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); text-decoration: none; font-weight: 700; }
.site-element-button--outline { color: var(--ds-color-action-primary); background: transparent; }
.site-element-button--text { color: var(--ds-color-action-primary); background: transparent; border-color: transparent; }
.site-element-divider { border: 0; border-top: 1px solid var(--ds-color-border); margin-block: 1rem; }
</style>
