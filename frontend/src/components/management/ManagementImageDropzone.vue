<template>
  <section class="image-dropzone" :class="{ dragging: isDragging, busy: uploading }">
    <input ref="fileInputRef" class="hidden-input" type="file" accept="image/*" @change="onFileChange" />

    <div class="preview-panel" :class="{ empty: !modelValue }">
      <img v-if="modelValue" :src="modelValue" :alt="altText || 'تصویر انتخاب‌شده'" class="preview-image" @error="onImageError" />
      <div v-else class="empty-preview">
        <ImageIcon :size="30" />
        <strong>تصویر دسته هنوز انتخاب نشده</strong>
        <small>برای نمایش حرفه‌ای در لیست و منوی مشتری، یک تصویر واضح اضافه کنید.</small>
      </div>
    </div>

    <div
      class="drop-panel"
      role="button"
      tabindex="0"
      :aria-busy="uploading ? 'true' : 'false'"
      @click="openFilePicker"
      @keydown.enter.prevent="openFilePicker"
      @keydown.space.prevent="openFilePicker"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDropFiles"
    >
      <span class="upload-icon" aria-hidden="true">
        <LoaderIcon v-if="uploading" :size="22" class="spin" />
        <UploadCloudIcon v-else :size="24" />
      </span>
      <div class="drop-copy">
        <strong>{{ uploading ? 'در حال آپلود تصویر...' : 'عکس را اینجا رها کنید یا کلیک کنید' }}</strong>
        <small>JPG, PNG, WebP — حداکثر {{ maxSizeMb }} مگابایت</small>
      </div>
    </div>

    <label class="url-field">
      <span>یا آدرس تصویر را دستی وارد کنید</span>
      <input class="input" :value="modelValue" placeholder="/files/category.jpg" @input="updateValue($event.target.value)" />
    </label>

    <div class="drop-actions" v-if="modelValue">
      <button type="button" class="secondary-btn mini" @click="openFilePicker" :disabled="uploading">تعویض تصویر</button>
      <button type="button" class="secondary-btn mini danger" @click="clearImage" :disabled="uploading">حذف تصویر</button>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { Image as ImageIcon, Loader2 as LoaderIcon, UploadCloud as UploadCloudIcon } from 'lucide-vue-next'
import { uploadFileToFrappe } from '@/utils/api'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  altText: {
    type: String,
    default: '',
  },
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: String,
    default: '',
  },
  fieldname: {
    type: String,
    default: '',
  },
  maxSizeMb: {
    type: Number,
    default: 5,
  },
})

const emit = defineEmits(['update:modelValue', 'error', 'uploaded'])

const fileInputRef = ref(null)
const isDragging = ref(false)
const uploading = ref(false)

function openFilePicker() {
  if (uploading.value) return
  fileInputRef.value?.click?.()
}

function updateValue(value = '') {
  emit('update:modelValue', String(value || '').trim())
}

function clearImage() {
  updateValue('')
}

function onImageError(event) {
  event.target.style.display = 'none'
}

function onFileChange(event) {
  const file = event?.target?.files?.[0]
  event.target.value = ''
  if (file) uploadImage(file)
}

function onDropFiles(event) {
  isDragging.value = false
  const file = event?.dataTransfer?.files?.[0]
  if (file) uploadImage(file)
}

async function uploadImage(file) {
  if (!String(file?.type || '').startsWith('image/')) {
    emit('error', 'لطفاً فقط فایل تصویر انتخاب کنید.')
    return
  }

  const maxBytes = Number(props.maxSizeMb || 5) * 1024 * 1024
  if (file.size > maxBytes) {
    emit('error', `حجم تصویر نباید بیشتر از ${props.maxSizeMb} مگابایت باشد.`)
    return
  }

  uploading.value = true
  try {
    const uploaded = await uploadFileToFrappe(file, {
      doctype: props.doctype,
      docname: props.docname,
      fieldname: props.fieldname,
      isPrivate: false,
    })
    if (!uploaded.file_url) {
      throw new Error('آدرس فایل آپلودشده از سرور دریافت نشد.')
    }
    updateValue(uploaded.file_url)
    emit('uploaded', uploaded)
  } catch (error) {
    emit('error', error.message || 'آپلود تصویر ناموفق بود.')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.image-dropzone {
  display: grid;
  grid-template-columns: minmax(240px, 0.9fr) minmax(260px, 1.1fr);
  gap: 0.85rem;
  align-items: stretch;
}

.hidden-input {
  display: none;
}

.preview-panel,
.drop-panel,
.url-field {
  border: 1px solid var(--border, #e2e8f0);
  background: color-mix(in srgb, var(--bg-card, #fff) 88%, var(--bg-soft, #f8fafc));
  border-radius: 20px;
}

.preview-panel {
  min-height: 220px;
  overflow: hidden;
  display: grid;
  place-items: center;
  box-shadow: 0 16px 34px rgb(15 23 42 / 0.06);
}

.preview-image {
  width: 100%;
  height: 100%;
  min-height: 220px;
  object-fit: cover;
}

.empty-preview {
  padding: 1.25rem;
  display: grid;
  justify-items: center;
  gap: 0.45rem;
  text-align: center;
  color: var(--text-muted, #64748b);
}

.empty-preview strong {
  color: var(--text-primary, #0f172a);
  font-size: 0.98rem;
}

.empty-preview small {
  line-height: 1.7;
}

.drop-panel {
  min-height: 150px;
  border-style: dashed;
  border-width: 2px;
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.2);
  cursor: pointer;
  padding: 1rem;
  display: grid;
  place-items: center;
  gap: 0.55rem;
  text-align: center;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  touch-action: manipulation;
}

.drop-panel:hover,
.drop-panel:focus-visible,
.image-dropzone.dragging .drop-panel {
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.45);
  background: color-mix(in srgb, var(--bg-card, #fff) 76%, var(--module-50, #f5eee5));
  box-shadow: 0 18px 34px rgb(15 23 42 / 0.08);
  transform: translateY(-1px);
  outline: none;
}

.upload-icon {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 18px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e2e8f0);
  color: var(--module-500, #8b5e34);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.drop-copy {
  display: grid;
  gap: 0.2rem;
}

.drop-copy strong {
  color: var(--text-primary, #0f172a);
  font-size: 0.95rem;
}

.drop-copy small,
.url-field span {
  color: var(--text-muted, #64748b);
  font-size: 0.78rem;
}

.url-field {
  grid-column: 2;
  padding: 0.75rem;
  display: grid;
  gap: 0.35rem;
}

.drop-actions {
  grid-column: 2;
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.mini {
  min-height: 2.5rem;
  padding: 0.38rem 0.7rem;
  font-size: 0.78rem;
}

.danger {
  color: var(--danger, #dc2626);
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .drop-panel,
  .spin {
    transition-duration: 0.01ms;
    animation: none;
  }
}

@media (max-width: 760px) {
  .image-dropzone {
    grid-template-columns: minmax(0, 1fr);
  }

  .url-field,
  .drop-actions {
    grid-column: auto;
  }

  .preview-panel,
  .preview-image {
    min-height: 190px;
  }
}
</style>
