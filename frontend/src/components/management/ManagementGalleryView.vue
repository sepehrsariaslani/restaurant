<template>
  <div class="ng-shell" v-if="rows.length">
    <article
      v-for="(row, index) in rows"
      :key="resolveRowKey(row, index)"
      class="ng-card"
      :class="{ 'ng-card--clickable': clickable, [`ng-card--${rowColor(row)}`]: rowColor(row) }"
      :tabindex="clickable ? 0 : undefined"
      @click="onCardClick($event, row)"
      @keydown.enter.prevent="onCardKeydown(row)"
      @keydown.space.prevent="onCardKeydown(row)"
    >
      <!-- تصویر -->
      <div class="ng-media">
        <img v-if="resolveImage(row)" :src="resolveImage(row)" :alt="readField(row, titleField, 'image')" class="ng-img" loading="lazy" />
        <div v-else class="ng-fallback">
          <span class="ng-fallback-text">{{ initials(readField(row, titleField, fallbackText)) }}</span>
        </div>

        <!-- وضعیت روی تصویر -->
        <div class="ng-media-top" v-if="$slots.overlay">
          <slot name="overlay" :row="row" :index="index" />
        </div>

        <!-- دکمه سریع (fixed روی کارت) -->
        <div class="ng-quick-action" v-if="$slots.quickAction">
          <slot name="quickAction" :row="row" :index="index" />
        </div>

        <!-- دسته روی تصویر -->
        <span v-if="categoryOf(row)" class="ng-cat-badge">{{ categoryOf(row) }}</span>
      </div>

      <!-- بدنه -->
      <div class="ng-body">
        <strong class="ng-title">{{ readField(row, titleField, '-') }}</strong>
        <small v-if="codeOf(row)" class="ng-code">{{ codeOf(row) }}</small>

        <!-- چیپ‌های متادیتا -->
        <div class="ng-chips" v-if="hasChips(row)">
          <template v-for="pkey in orderedProps" :key="pkey">
            <span
              v-if="isPropVisible(pkey) && chipRenderers?.[pkey]"
              class="ng-chip"
              :class="chipClassFor(row, pkey)"
            >{{ chipTextFor(row, pkey) }}</span>
          </template>
          <span v-for="t in tagsOf(row)" :key="t" class="ng-chip ng-chip--tag">{{ t }}</span>
          <span v-if="moreTagsOf(row)" class="ng-chip ng-chip--tag">+{{ moreTagsOf(row) }}</span>
        </div>

        <p class="ng-caption" v-if="$slots.caption">
          <slot name="caption" :row="row" :index="index" />
        </p>
      </div>

      <footer class="ng-actions" v-if="$slots.actions">
        <slot name="actions" :row="row" :index="index" />
      </footer>
    </article>
  </div>

  <p v-else class="ng-empty">{{ emptyText }}</p>
</template>

<script setup>
const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: [String, Function],
    default: '',
  },
  imageField: {
    type: String,
    default: 'image',
  },
  secondaryImageField: {
    type: String,
    default: 'website_image',
  },
  titleField: {
    type: String,
    default: 'title',
  },
  subtitleField: {
    type: String,
    default: '',
  },
  codeField: {
    type: String,
    default: 'item_code',
  },
  categoryField: {
    type: String,
    default: 'category_title',
  },
  emptyText: {
    type: String,
    default: 'داده‌ای برای نمایش وجود ندارد.',
  },
  fallbackText: {
    type: String,
    default: 'بدون تصویر',
  },
  clickable: {
    type: Boolean,
    default: false,
  },
  // پشتیبانی از خواص نمایشی view
  properties: {
    type: Object,
    default: null,
  },
  propertyOrder: {
    type: Array,
    default: null,
  },
  chipRenderers: {
    type: Object,
    default: null,
  },
  rowClass: {
    type: [String, Function],
    default: '',
  },
})

const emit = defineEmits(['click-item'])

const DEFAULT_ORDER = ['category_title', 'base_price', 'stock_qty', 'is_active', 'tags', 'item_code']

const orderedProps = props.propertyOrder?.length ? props.propertyOrder : DEFAULT_ORDER

function resolveRowKey(row, index) {
  if (typeof props.rowKey === 'function') return props.rowKey(row, index)
  if (typeof props.rowKey === 'string' && props.rowKey) return row?.[props.rowKey] ?? index
  return row?.name || row?.id || index
}

function readField(row, key, fallback = '-') {
  if (!key) return fallback
  const value = row?.[key]
  if (value === null || value === undefined || value === '') return fallback
  return value
}

function resolveImage(row) {
  return String(row?.[props.imageField] || row?.[props.secondaryImageField] || '').trim()
}

function initials(value) {
  const chunks = String(value || '').trim().split(/\s+/).filter(Boolean)
  return chunks.slice(0, 2).map((w) => w[0]).join('').toUpperCase() || '•'
}

function categoryOf(row) {
  return readField(row, props.categoryField, '')
}

function codeOf(row) {
  return readField(row, props.codeField, '')
}

function tagsOf(row) {
  const tags = Array.isArray(row?.tags) ? row.tags : []
  return tags.slice(0, 4)
}

function moreTagsOf(row) {
  const tags = Array.isArray(row?.tags) ? row.tags : []
  return tags.length > 4 ? tags.length - 4 : 0
}

function isPropVisible(key) {
  return props.properties?.[key] !== false
}

function chipTextFor(row, key) {
  try {
    return props.chipRenderers?.[key]?.(row)?.text ?? ''
  } catch (_) {
    return ''
  }
}

function chipClassFor(row, key) {
  try {
    return props.chipRenderers?.[key]?.(row)?.cls ?? ''
  } catch (_) {
    return ''
  }
}

function hasChips(row) {
  for (const key of orderedProps) {
    if (isPropVisible(key) && chipTextFor(row, key)) return true
  }
  return tagsOf(row).length > 0
}

function rowColor(row) {
  if (typeof props.rowClass === 'function') {
    const cls = props.rowClass(row) || ''
    const match = String(cls).match(/nrow-(\w+)/)
    return match ? match[1] : ''
  }
  return ''
}

function onCardClick(event, row) {
  if (!props.clickable) return
  const target = event?.target
  if (target?.closest?.('a, button, input, select, textarea, label, [role="button"], [data-no-card-click="1"]')) return
  emit('click-item', row)
}

function onCardKeydown(row) {
  if (!props.clickable) return
  emit('click-item', row)
}
</script>

<style scoped>
.ng-shell {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.65rem;
}

.ng-card {
  border-radius: 16px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.ng-card--clickable {
  cursor: pointer;
}

.ng-card--clickable:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  box-shadow: 0 14px 30px rgb(var(--mg-primary-rgb) / 0.14);
}

/* رنگ شرطی */
.ng-card--red { background: color-mix(in srgb, #ef4444 8%, var(--mg-bg-surface)); }
.ng-card--orange { background: color-mix(in srgb, #f97316 8%, var(--mg-bg-surface)); }
.ng-card--yellow { background: color-mix(in srgb, #eab308 9%, var(--mg-bg-surface)); }
.ng-card--green { background: color-mix(in srgb, #22c55e 8%, var(--mg-bg-surface)); }
.ng-card--blue { background: color-mix(in srgb, #3b82f6 8%, var(--mg-bg-surface)); }
.ng-card--gray { background: color-mix(in srgb, #6b7280 8%, var(--mg-bg-surface)); }

.ng-media {
  position: relative;
  aspect-ratio: 4 / 3;
  background: color-mix(in srgb, var(--mg-bg-soft) 70%, transparent);
  display: grid;
  place-items: center;
  overflow: hidden;
}

.ng-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.25s ease;
}

.ng-card--clickable:hover .ng-img {
  transform: scale(1.04);
}

.ng-fallback {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, color-mix(in srgb, var(--mg-primary) 18%, var(--mg-bg-surface)) 0%, color-mix(in srgb, var(--mg-olive) 18%, var(--mg-bg-surface)) 100%);
}

.ng-fallback-text {
  font-size: 1.6rem;
  font-weight: 800;
  color: color-mix(in srgb, var(--mg-primary) 70%, var(--mg-text-muted));
}

.ng-media-top {
  position: absolute;
  top: 0.4rem;
  right: 0.4rem;
  left: 0.4rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.3rem;
}

.ng-cat-badge {
  position: absolute;
  bottom: 0.4rem;
  right: 0.4rem;
  font-size: 0.64rem;
  font-weight: 600;
  color: var(--mg-bg-surface);
  background: rgb(52 38 31 / 0.65);
  backdrop-filter: blur(4px);
  border-radius: 999px;
  padding: 0.14rem 0.5rem;
}

.ng-body {
  padding: 0.55rem 0.6rem 0.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}

.ng-title {
  font-size: 0.84rem;
  line-height: 1.5;
  color: var(--mg-text-main);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ng-code {
  font-size: 0.64rem;
  color: var(--mg-text-muted);
  direction: ltr;
  text-align: right;
  font-family: ui-monospace, monospace;
}

.ng-chips {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.28rem;
  margin-top: 0.25rem;
}

.ng-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.64rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 70%, transparent);
  border-radius: 999px;
  padding: 0.08rem 0.45rem;
  white-space: nowrap;
}

.ng-chip--soft {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 25%, transparent);
  font-weight: 600;
}

.ng-chip--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 30%, transparent);
  font-weight: 600;
}

.ng-chip--off {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
  border-color: transparent;
}

.ng-chip--tag {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
  border-color: transparent;
}

.ng-chip--code {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-page) 80%, var(--mg-bg-soft) 20%);
  border-color: var(--mg-border-light);
  font-family: ui-monospace, monospace;
  direction: ltr;
}

.ng-caption {
  margin: 0.2rem 0 0;
  font-size: 0.7rem;
  color: var(--mg-text-muted);
}

.ng-actions {
  padding: 0.3rem 0.6rem 0.55rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.ng-empty {
  padding: 1.5rem 0.75rem;
  text-align: center;
  color: var(--mg-text-muted);
  font-size: 0.8rem;
}

/* ریسپانسیو: دسکتاپ → تبلت → موبایل */
@media (max-width: 1180px) {
  .ng-shell {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .ng-shell {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .ng-shell {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.45rem;
  }

  .ng-card {
    border-radius: 12px;
  }

  .ng-media {
    aspect-ratio: 4 / 3;
  }

  .ng-body {
    padding: 0.4rem 0.45rem 0.3rem;
    gap: 0.15rem;
  }

  .ng-title {
    font-size: 0.74rem;
    line-height: 1.4;
  }

  .ng-code {
    font-size: 0.58rem;
  }

  .ng-chips {
    gap: 0.2rem;
    margin-top: 0.18rem;
  }

  .ng-chip {
    font-size: 0.58rem;
    padding: 0.06rem 0.35rem;
  }

  .ng-cat-badge {
    font-size: 0.56rem;
    padding: 0.1rem 0.4rem;
    bottom: 0.3rem;
    right: 0.3rem;
  }

  .ng-media-top {
    top: 0.3rem;
    right: 0.3rem;
    left: 0.3rem;
  }

  .gallery-status {
    font-size: 0.56rem;
    padding: 0.1rem 0.4rem;
  }
}

@media (max-width: 360px) {
  .ng-shell {
    gap: 0.35rem;
  }

  .ng-body {
    padding: 0.35rem 0.4rem 0.25rem;
  }

  .ng-title {
    font-size: 0.68rem;
  }
}
.ng-quick-action {
  position: absolute;
  top: 0.5rem;
  inset-inline-start: 0.5rem;
  z-index: 5;
}

</style>
