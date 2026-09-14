<template>
  <section class="image-manager">
    <label class="upload-drop">
      <input ref="fileInputRef" class="hidden-input" type="file" accept="image/*" multiple @change="onFileChange" />
      <span class="upload-icon" aria-hidden="true">
        <UploadCloudIcon :size="22" />
      </span>
      <div class="upload-copy">
        <strong>{{ uploading ? 'در حال آپلود...' : 'افزودن تصویر جدید' }}</strong>
        <small>عکس محصول را انتخاب کنید؛ می‌توانید چند تصویر را با هم بفرستید.</small>
      </div>
      <button type="button" class="secondary-btn upload-action" :disabled="uploading" @click.prevent="openFilePicker">
        {{ uploading ? 'در حال ارسال...' : 'انتخاب فایل' }}
      </button>
    </label>

    <div class="image-grid" v-if="items.length">
      <article v-for="item in items" :key="item.url" class="image-card">
        <button type="button" class="thumb-btn" aria-label="نمایش تصویر" @click="$emit('select', item.url)">
          <img :src="item.url" alt="تصویر محصول" class="thumb" loading="lazy" />
        </button>

        <div class="badge-row">
          <span class="badge cover" v-if="item.isCover">
            <StarIcon :size="13" />
            کاور
          </span>
          <span class="badge secondary" v-if="item.isSecondary">
            <ImageIcon :size="13" />
            عکس دوم
          </span>
          <span class="badge muted" v-if="!item.isCover && !item.isSecondary">گالری</span>
        </div>

        <div class="action-row">
          <button type="button" class="secondary-btn mini" :disabled="item.isCover || busy" @click="$emit('set-cover', item.url)">
            <StarIcon :size="14" />
            کاور
          </button>
          <button
            type="button"
            class="secondary-btn mini"
            :disabled="item.isSecondary || busy"
            @click="$emit('set-secondary', item.url)"
          >
            <ImageIcon :size="14" />
            عکس دوم
          </button>
          <button type="button" class="secondary-btn mini danger" :disabled="busy" @click="confirmRemove(item.url)">
            <TrashIcon :size="14" />
            حذف
          </button>
        </div>
      </article>
    </div>

    <p class="muted" v-else>هنوز تصویری ثبت نشده است.</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import {
  Image as ImageIcon,
  Star as StarIcon,
  Trash2 as TrashIcon,
  UploadCloud as UploadCloudIcon,
} from 'lucide-vue-next'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  uploading: {
    type: Boolean,
    default: false,
  },
  busy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['upload', 'set-cover', 'set-secondary', 'remove', 'select'])
const fileInputRef = ref(null)

function openFilePicker() {
  fileInputRef.value?.click?.()
}

function onFileChange(event) {
  const files = Array.from(event?.target?.files || [])
  if (!files.length) {
    return
  }
  emit('upload', files)
  event.target.value = ''
}

function confirmRemove(url) {
  if (!url) {
    return
  }
  const confirmed = window.confirm('این تصویر حذف شود؟')
  if (!confirmed) {
    return
  }
  emit('remove', url)
}
</script>

<style scoped>
.image-manager {
  display: grid;
  gap: 0.75rem;
}

.upload-drop {
  min-height: 5rem;
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.28);
  border-radius: 12px;
  background: var(--bg-soft, var(--mg-bg-page));
  padding: 0.75rem;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.7rem;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
  touch-action: manipulation;
}

.upload-drop:hover,
.upload-drop:focus-within {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.45);
  background: var(--module-50, rgb(139 94 52 / 0.075));
  box-shadow: 0 10px 22px rgb(15 23 42 / 0.06);
}

.upload-icon {
  width: 2.55rem;
  height: 2.55rem;
  border-radius: 12px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, var(--mg-border-light));
  color: var(--module-500, var(--mg-primary));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hidden-input {
  display: none;
}

.upload-copy {
  display: grid;
  gap: 0.15rem;
  min-width: 0;
}

.upload-copy strong {
  color: var(--text-primary, var(--mg-text-main));
  font-size: 0.9rem;
}

.upload-copy small {
  font-size: 0.78rem;
  color: var(--text-muted, var(--mg-text-muted));
  line-height: 1.65;
}

.upload-action {
  min-height: 2.45rem;
  white-space: nowrap;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.6rem;
}

.image-card {
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 12px;
  background: var(--bg-card, #fff);
  padding: 0.5rem;
  display: grid;
  gap: 0.45rem;
  min-width: 0;
}

.thumb-btn {
  border: 1px solid var(--border, var(--mg-border-light));
  padding: 0;
  background: var(--bg-soft, var(--mg-bg-page));
  border-radius: 10px;
  overflow: hidden;
  aspect-ratio: 4 / 3;
  cursor: pointer;
  transition: border-color 0.18s ease, transform 0.18s ease;
}

.thumb-btn:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.32);
  transform: translateY(-1px);
}

.thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  background: #fff;
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.24rem;
  min-height: 1.55rem;
}

.badge {
  border-radius: 999px;
  font-size: 0.72rem;
  padding: 0.14rem 0.45rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
}

.badge.cover {
  background: var(--module-50, rgb(139 94 52 / 0.075));
  color: var(--module-title-light, var(--mg-text-main));
}

.badge.secondary {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.15);
  color: var(--module-600, var(--mg-primary));
}

.badge.muted {
  background: var(--bg-soft, var(--mg-bg-page));
  color: var(--text-muted, var(--mg-text-muted));
}

.action-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.24rem;
}

.mini {
  min-height: 2.25rem;
  padding: 0.35rem 0.36rem;
  font-size: 0.74rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.22rem;
}

.mini.danger {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.35);
  color: var(--danger);
}

@media (max-width: 980px) {
  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .upload-drop {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .upload-action {
    grid-column: 1 / -1;
    width: 100%;
  }
}
</style>
