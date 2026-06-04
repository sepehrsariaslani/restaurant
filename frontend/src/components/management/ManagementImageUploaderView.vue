<template>
  <section class="image-manager">
    <label class="upload-drop">
      <input ref="fileInputRef" class="hidden-input" type="file" accept="image/*" multiple @change="onFileChange" />
      <div class="upload-copy">
        <strong>{{ uploading ? 'در حال آپلود...' : 'افزودن تصویر جدید' }}</strong>
        <small>فایل تصویر را انتخاب کنید یا روی این بخش بزنید.</small>
      </div>
      <button type="button" class="secondary-btn" :disabled="uploading" @click.prevent="openFilePicker">
        {{ uploading ? 'در حال ارسال...' : 'انتخاب فایل' }}
      </button>
    </label>

    <div class="image-grid" v-if="items.length">
      <article v-for="item in items" :key="item.url" class="image-card">
        <button type="button" class="thumb-btn" @click="$emit('select', item.url)">
          <img :src="item.url" alt="gallery image" class="thumb" />
        </button>

        <div class="badge-row">
          <span class="badge cover" v-if="item.isCover">کاور</span>
          <span class="badge secondary" v-if="item.isSecondary">عکس دوم</span>
        </div>

        <div class="action-row">
          <button type="button" class="secondary-btn mini" :disabled="item.isCover || busy" @click="$emit('set-cover', item.url)">
            کاور
          </button>
          <button
            type="button"
            class="secondary-btn mini"
            :disabled="item.isSecondary || busy"
            @click="$emit('set-secondary', item.url)"
          >
            عکس دوم
          </button>
          <button type="button" class="secondary-btn mini danger" :disabled="busy" @click="confirmRemove(item.url)">
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
  gap: 0.6rem;
}

.upload-drop {
  border: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.35);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.62);
  padding: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  cursor: pointer;
}

.hidden-input {
  display: none;
}

.upload-copy {
  display: grid;
  gap: 0.15rem;
}

.upload-copy strong {
  font-size: 0.88rem;
}

.upload-copy small {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
}

.image-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 12px;
  background: rgb(var(--palette-eggshell-rgb) / 0.7);
  padding: 0.45rem;
  display: grid;
  gap: 0.35rem;
}

.thumb-btn {
  border: none;
  padding: 0;
  background: transparent;
  border-radius: 10px;
  overflow: hidden;
  aspect-ratio: 4 / 3;
  cursor: pointer;
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
  min-height: 1.42rem;
}

.badge {
  border-radius: 999px;
  font-size: 0.74rem;
  padding: 0.12rem 0.45rem;
  font-weight: 700;
}

.badge.cover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

.badge.secondary {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.17);
  color: rgb(var(--palette-deep-saffron-rgb) / 1);
}

.action-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.24rem;
}

.mini {
  padding: 0.35rem 0.4rem;
  font-size: 0.76rem;
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
    flex-direction: column;
    align-items: flex-start;
  }

  .image-grid {
    grid-template-columns: 1fr;
  }
}
</style>
