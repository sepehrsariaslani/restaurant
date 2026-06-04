<template>
  <div class="gallery-shell" v-if="rows.length">
    <article
      v-for="(row, index) in rows"
      :key="resolveRowKey(row, index)"
      class="gallery-card"
      :class="{ clickable }"
      :tabindex="clickable ? 0 : undefined"
      @click="onCardClick($event, row)"
      @keydown.enter.prevent="onCardKeydown(row)"
      @keydown.space.prevent="onCardKeydown(row)"
    >
      <div class="image-shell">
        <img v-if="resolveImage(row)" :src="resolveImage(row)" :alt="readField(row, titleField, 'image')" class="image" />
        <div v-else class="fallback">{{ fallbackText }}</div>

        <slot name="overlay" :row="row" :index="index" />
      </div>

      <div class="body">
        <strong>{{ readField(row, titleField, '-') }}</strong>
        <small v-if="subtitleField">{{ readField(row, subtitleField, '-') }}</small>

        <p class="caption" v-if="$slots.caption">
          <slot name="caption" :row="row" :index="index" />
        </p>
      </div>

      <footer class="card-actions" v-if="$slots.actions">
        <slot name="actions" :row="row" :index="index" />
      </footer>
    </article>
  </div>

  <p v-else class="muted">{{ emptyText }}</p>
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
})

const emit = defineEmits(['click-item'])

function resolveRowKey(row, index) {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row, index)
  }
  if (typeof props.rowKey === 'string' && props.rowKey) {
    return row?.[props.rowKey] ?? index
  }
  return row?.name || row?.id || index
}

function readField(row, key, fallback = '-') {
  if (!key) {
    return fallback
  }
  const value = row?.[key]
  if (value === null || value === undefined || value === '') {
    return fallback
  }
  return value
}

function resolveImage(row) {
  return String(row?.[props.imageField] || row?.[props.secondaryImageField] || '').trim()
}

function onCardClick(event, row) {
  if (!props.clickable) {
    return
  }
  const target = event?.target
  if (target?.closest?.('a, button, input, select, textarea, label, [role="button"], [data-no-card-click="1"]')) {
    return
  }
  emit('click-item', row)
}

function onCardKeydown(row) {
  if (!props.clickable) {
    return
  }
  emit('click-item', row)
}
</script>

<style scoped>
.gallery-shell {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;
}

.gallery-card {
  border-radius: 16px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  overflow: hidden;
  display: grid;
  gap: 0.45rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.gallery-card.clickable {
  cursor: pointer;
}

.gallery-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.image-shell {
  position: relative;
  aspect-ratio: 4 / 3;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  display: grid;
  place-items: center;
}

.image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fallback {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.body {
  padding: 0 0.5rem;
  display: grid;
  gap: 0.15rem;
}

.body strong {
  font-size: 0.82rem;
  line-height: 1.55;
}

.body small {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.caption {
  margin: 0;
  font-size: 0.72rem;
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.78);
}

.card-actions {
  padding: 0 0.5rem 0.55rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

@media (max-width: 1180px) {
  .gallery-shell {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .gallery-shell {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .gallery-shell {
    grid-template-columns: 1fr;
  }
}
</style>
