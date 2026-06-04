<template>
  <ManagementPageScaffold title="گالری فرمت چاپ" subtitle="پیش نمایش و چاپ سریع فرمت های چاپ برای همه داکیومنت ها">
    <template #actions>
      <button class="secondary-btn" type="button" @click="loadGallery" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی لیست' }}
      </button>
    </template>

    <ManagementSurfaceCard tone="accent" title="فیلترها" subtitle="جستجو در نام فرمت، داکیومنت و ماژول">
      <div class="filter-grid">
        <label>
          جستجو
          <input v-model.trim="filters.search" class="input" type="text" placeholder="مثال: حواله، فرمول ساخت، افتتاحیه صندوق" @keyup.enter="loadGallery" />
        </label>

        <label>
          نوع داکیومنت
          <SearchableDropdown
            v-model="filters.doc_type"
            :options="docTypeOptions"
            placeholder="همه داکیومنت‌ها"
            search-placeholder="جستجوی داکیومنت..."
            @update:model-value="onDocTypeChange"
          />
        </label>

        <label class="check-label">
          <input v-model="filters.blank_only" type="checkbox" @change="loadGallery" />
          فقط فرمت های خالی
        </label>

        <button class="primary-btn" type="button" @click="loadGallery" :disabled="loading">اعمال فیلتر</button>
      </div>

      <p class="muted stats-line">{{ totalCount }} فرمت چاپ در دسترس است.</p>
    </ManagementSurfaceCard>

    <p class="error" v-if="error">{{ error }}</p>

    <section class="workspace-grid">
      <ManagementSurfaceCard title="لیست فرمت ها" subtitle="نمای گالری بر اساس نوع داکیومنت">
        <p class="muted" v-if="loading">در حال دریافت فرمت های چاپ...</p>

        <template v-else-if="groupedFormats.length">
          <div class="format-groups">
            <section v-for="group in groupedFormats" :key="group.doc_type" class="doc-group">
              <header class="group-head">
                <strong>{{ group.doc_type_label }}</strong>
                <small class="muted">{{ group.items.length }} فرمت</small>
              </header>

              <div class="format-grid">
                <button
                  v-for="item in group.items"
                  :key="item.name"
                  type="button"
                  class="format-card"
                  :class="{ active: item.name === activeFormatName }"
                  @click="openPreview(item)"
                >
                  <div class="card-top">
                    <span class="badge" v-if="item.is_blank">خالی</span>
                    <small>{{ item.doc_type_label || item.doc_type }}</small>
                  </div>
                  <strong>{{ item.title }}</strong>
                </button>
              </div>
            </section>
          </div>
        </template>

        <p v-else class="muted">فرمتی با این فیلتر پیدا نشد.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        class="preview-card"
        :title="previewTitle || 'پیش نمایش چاپ'"
        :subtitle="activeFormat ? `${activeFormat.doc_type_label || activeFormat.doc_type} | ${activeFormat.title}` : 'یک فرمت را انتخاب کنید'"
      >
        <template #head>
          <button class="primary-btn" type="button" :disabled="!previewHtml || previewLoading" @click="printPreview">
            چاپ همین فرمت
          </button>
        </template>

        <p class="muted" v-if="previewLoading">در حال ساخت پیش نمایش...</p>
        <p class="error" v-else-if="previewError">{{ previewError }}</p>
        <p class="muted" v-else-if="!previewHtml">برای مشاهده، یک فرمت چاپ را انتخاب کنید.</p>

        <iframe
          v-else
          ref="previewFrame"
          class="preview-frame"
          :srcdoc="previewHtml"
          title="پیش نمایش چاپ"
        />
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementPrintFormatPreview, listManagementPrintFormats } from '@/utils/api'

const loading = ref(false)
const error = ref('')
const totalCount = ref(0)

const formats = ref([])
const docTypes = ref([])
const activeFormatName = ref('')
const previewTitle = ref('')
const previewHtml = ref('')
const previewError = ref('')
const previewLoading = ref(false)
const previewFrame = ref(null)

const filters = reactive({
  search: '',
  doc_type: '',
  blank_only: 0,
})

const activeFormat = computed(() => formats.value.find((row) => row.name === activeFormatName.value) || null)

const groupedFormats = computed(() => {
  const grouped = {}
  for (const row of formats.value) {
    const key = row.doc_type || 'سایر'
    if (!grouped[key]) {
      grouped[key] = []
    }
    grouped[key].push(row)
  }
  return Object.keys(grouped)
    .sort((a, b) => a.localeCompare(b, 'fa'))
    .map((docType) => ({
      doc_type: docType,
      doc_type_label: grouped[docType][0]?.doc_type_label || docType,
      items: grouped[docType].slice().sort((a, b) => {
        if (a.is_blank !== b.is_blank) {
          return a.is_blank ? -1 : 1
        }
        return String(a.title || a.name).localeCompare(String(b.title || b.name), 'fa')
      }),
    }))
})

const docTypeOptions = computed(() => [
  { value: '', label: 'همه داکیومنت ها' },
  ...(docTypes.value || []).map((item) => ({
    value: item.doc_type,
    label: `${item.doc_type_label || item.doc_type} (${Number(item.count || 0).toLocaleString('fa-IR')})`,
  })),
])

async function loadGallery() {
  loading.value = true
  error.value = ''
  try {
    const payload = await listManagementPrintFormats({
      search: filters.search,
      doc_type: filters.doc_type,
      blank_only: filters.blank_only ? 1 : 0,
    })

    formats.value = Array.isArray(payload?.formats) ? payload.formats : []
    docTypes.value = Array.isArray(payload?.doc_types) ? payload.doc_types : []
    totalCount.value = Number(payload?.total || formats.value.length || 0)

    if (!formats.value.length) {
      activeFormatName.value = ''
      previewTitle.value = ''
      previewHtml.value = ''
      previewError.value = ''
      return
    }

    const stillExists = formats.value.find((row) => row.name === activeFormatName.value)
    if (!stillExists) {
      await openPreview(formats.value[0])
    }
  } catch (loadErr) {
    error.value = loadErr.message || 'دریافت لیست فرمت های چاپ ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function openPreview(item) {
  if (!item?.name) {
    return
  }

  activeFormatName.value = item.name
  previewLoading.value = true
  previewError.value = ''
  try {
    const payload = await getManagementPrintFormatPreview({
      print_format_name: item.name,
      doc_type: item.doc_type,
    })
    previewTitle.value = payload?.title || item.title || item.name
    previewHtml.value = payload?.html || ''
  } catch (previewErr) {
    previewHtml.value = ''
    previewError.value = previewErr.message || 'پیش نمایش قابل تولید نیست.'
  } finally {
    previewLoading.value = false
  }
}

function printPreview() {
  if (!previewHtml.value) {
    return
  }

  const iframe = previewFrame.value
  const frameWindow = iframe?.contentWindow
  if (frameWindow) {
    frameWindow.focus()
    frameWindow.print()
    return
  }

  const popup = window.open('', '_blank')
  if (!popup) {
    return
  }
  popup.document.write(previewHtml.value)
  popup.document.close()
  popup.focus()
  popup.print()
}

function onDocTypeChange() {
  loadGallery()
}

loadGallery()
</script>

<style scoped>
.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;
  align-items: end;
}

.filter-grid label {
  display: grid;
  gap: 0.24rem;
  font-size: 0.79rem;
}

.check-label {
  display: inline-flex !important;
  align-items: center;
  gap: 0.35rem;
  padding-bottom: 0.55rem;
}

.stats-line {
  margin: 0.65rem 0 0;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 0.7rem;
}

.format-groups {
  display: grid;
  gap: 0.9rem;
  max-height: 72vh;
  overflow: auto;
  padding-inline-end: 0.2rem;
}

.doc-group {
  display: grid;
  gap: 0.45rem;
}

.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.group-head strong {
  font-size: 0.88rem;
}

.format-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
}

.format-card {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.65);
  text-align: right;
  padding: 0.58rem;
  display: grid;
  gap: 0.32rem;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.format-card:hover {
  transform: translateY(-2px);
}

.format-card.active {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.9);
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
}

.format-card strong {
  font-size: 0.84rem;
  line-height: 1.5;
}

.preview-card {
  min-height: 76vh;
  display: grid;
  gap: 0.5rem;
}

.preview-frame {
  width: 100%;
  min-height: 66vh;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 16px;
  background: #fff;
}

.error {
  margin: 0;
  color: var(--danger);
}

@media (max-width: 1080px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .format-groups {
    max-height: none;
  }

  .preview-card {
    min-height: auto;
  }

  .preview-frame {
    min-height: 62vh;
  }
}

@media (max-width: 640px) {
  .filter-grid,
  .format-grid {
    grid-template-columns: 1fr;
  }
}
</style>
