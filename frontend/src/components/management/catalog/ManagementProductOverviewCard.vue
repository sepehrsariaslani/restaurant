<template>
  <ManagementSurfaceCard class="product-general-card product-general-card--compact" title="اطلاعات کلی" subtitle="تصویر و تنظیمات سریع محصول">
    <div class="product-general-layout">
      <aside class="product-general-media" aria-label="عکس محصول">
        <div class="general-image-shell is-clickable" @click="$emit('open-media')">
          <img v-if="mainImage" :src="mainImage" :alt="form.item_name || 'عکس محصول'" class="general-product-image" />
          <div v-else class="general-image-empty">
            <span aria-hidden="true">+</span>
            <p>افزودن تصویر</p>
          </div>
          <button type="button" class="pg-image-edit-btn" title="مدیریت تصاویر" aria-label="مدیریت تصاویر" @click.stop="$emit('open-media')">
            <Camera :size="15" />
          </button>
        </div>
      </aside>

      <div class="product-general-main">
        <div class="product-general-fields">
          <label class="pg-name-field">
            نام کالا
            <input class="input" v-model="form.item_name" placeholder="نام نمایشی محصول" />
          </label>

          <div class="pg-status-row" aria-label="وضعیت محصول">
            <span class="pg-status-pill" :class="form.restaurant_enabled ? 'is-on' : 'is-off'">
              {{ form.restaurant_enabled ? 'فعال در منو' : 'غیرفعال در منو' }}
            </span>
            <span v-if="form.restaurant_coming_soon" class="pg-status-pill is-soon">به‌زودی</span>
            <span v-if="outOfStock" class="pg-status-pill is-warn">ناموجود</span>
            <span v-if="form.disabled" class="pg-status-pill is-off">غیرفعال در سیستم</span>
            <button
              type="button"
              class="pg-status-pill pg-status-pill--btn"
              :class="form.restaurant_kitchen_ticket ? 'is-kitchen-on' : 'is-kitchen-off'"
              title="فیش آشپزخانه را روشن یا خاموش کنید"
              @click="form.restaurant_kitchen_ticket = !form.restaurant_kitchen_ticket"
            >
              فیش آشپزخانه
            </button>
            <span class="pg-status-pill is-code" :title="form.item_code">{{ form.item_code }}</span>
          </div>

          <div class="pg-meta-row">
            <span v-if="selectedItemGroupPath" class="pg-meta-chip">
              <strong>گروه کالا</strong>
              {{ selectedItemGroupPath }}
            </span>
            <span v-if="readinessChecks.length" class="pg-readiness" :class="readinessScore === readinessChecks.length ? 'is-ready' : ''">
              آمادگی: {{ readinessScore.toLocaleString('fa-IR') }} / {{ readinessChecks.length.toLocaleString('fa-IR') }}
            </span>
          </div>
        </div>

        <label class="price-inline-field">
          قیمت کالا
          <span class="price-inline-control">
            <PersianNumberInput v-model="priceForm.price_list_rate" :min="0" suffix="ریال" />
            <button class="secondary-btn quick-price-save" type="button" @click="$emit('save-price')" :disabled="savingPrice">
              {{ savingPrice ? 'در حال ثبت...' : 'ثبت قیمت' }}
            </button>
          </span>
        </label>

        <div class="pg-quick-toggles">
          <ManagementToggleSwitch v-model="form.restaurant_enabled" label="فعال در منو" />
          <ManagementToggleSwitch v-model="form.restaurant_coming_soon" label="به‌زودی" />
        </div>
      </div>
    </div>
  </ManagementSurfaceCard>
</template>

<script setup>
import { Camera } from 'lucide-vue-next'
import PersianNumberInput from '@/components/PersianNumberInput.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementToggleSwitch from '@/components/management/ManagementToggleSwitch.vue'

defineProps({
  form: { type: Object, required: true },
  priceForm: { type: Object, required: true },
  mainImage: { type: String, default: '' },
  outOfStock: { type: Boolean, default: false },
  selectedItemGroupPath: { type: String, default: '' },
  readinessChecks: { type: Array, default: () => [] },
  readinessScore: { type: Number, default: 0 },
  savingPrice: { type: Boolean, default: false },
})

defineEmits(['open-media', 'save-price'])
</script>

<style scoped>
.product-general-card { overflow: hidden; }
.product-general-layout { display: grid; grid-template-columns: minmax(230px, .72fr) minmax(0, 1.28fr); gap: .85rem; align-items: stretch; }
.product-general-media { min-width: 0; display: grid; align-content: stretch; }
.general-image-shell { position: relative; min-height: 220px; height: clamp(220px, 23vw, 330px); aspect-ratio: 1 / 1; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-md); background: radial-gradient(circle at 18% 18%, var(--mg-bg-soft), transparent 34%), var(--mg-bg-surface); display: grid; place-items: center; overflow: hidden; box-shadow: var(--mg-shadow-sm); }
.general-image-shell.is-clickable { cursor: pointer; }
.general-product-image { width: 100%; height: 100%; object-fit: contain; object-position: center; background: var(--bg-card, #fff); }
.general-image-empty { display: grid; justify-items: center; gap: .4rem; color: var(--mg-text-muted); text-align: center; }
.general-image-empty span { width: 3.4rem; height: 3.4rem; border-radius: 999px; display: grid; place-items: center; background: var(--bg-card, #fff); border: 1px solid var(--mg-border); color: var(--mg-primary); font-size: 1.55rem; font-weight: 900; }
.general-image-empty p { margin: 0; font-size: .82rem; font-weight: 800; }
.pg-image-edit-btn { position: absolute; bottom: .55rem; inset-inline-end: .55rem; width: 32px; height: 32px; border-radius: 999px; border: 1px solid rgb(255 255 255 / .7); background: rgb(30 22 17 / .62); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; }
.product-general-main { min-width: 0; display: grid; align-content: center; gap: .8rem; }
.product-general-fields { display: grid; gap: .55rem; min-width: 0; }
.pg-name-field { display: grid; gap: .28rem; color: var(--mg-text-muted); font-size: .78rem; font-weight: 800; }
.pg-name-field input { min-height: 2.5rem; }
.pg-status-row { display: flex; align-items: center; flex-wrap: wrap; gap: .42rem; min-width: 0; }
.pg-status-pill { display: inline-flex; align-items: center; min-height: 1.8rem; border-radius: 999px; padding: .2rem .6rem; font-size: .7rem; font-weight: 800; white-space: nowrap; }
.pg-status-pill.is-on { color: var(--mg-success); background: var(--mg-success-bg); }
.pg-status-pill.is-off { color: var(--mg-text-muted); background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent); }
.pg-status-pill.is-soon { color: var(--mg-primary); background: color-mix(in srgb, var(--mg-primary) 12%, transparent); }
.pg-status-pill.is-warn { color: #92400e; background: rgb(254 243 199 / .95); }
.pg-status-pill.is-code { direction: ltr; color: var(--mg-text-muted); background: var(--mg-bg-soft); font-weight: 600; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.pg-status-pill--btn { border: 1px solid var(--mg-border-light); cursor: pointer; font-family: inherit; }
.pg-status-pill.is-kitchen-on { color: var(--mg-success); background: var(--mg-success-bg); }
.pg-status-pill.is-kitchen-off { color: var(--mg-text-muted); background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent); }
.pg-meta-row { display: flex; align-items: center; flex-wrap: wrap; gap: .42rem; }
.pg-meta-chip, .pg-readiness { display: inline-flex; align-items: center; gap: .3rem; min-height: 1.8rem; padding: .2rem .6rem; border-radius: 999px; font-size: .7rem; font-weight: 800; }
.pg-meta-chip { color: var(--mg-text-muted); background: var(--mg-bg-soft); border: 1px solid var(--mg-border-light); }
.pg-meta-chip strong { color: var(--mg-text-main); }
.pg-readiness { color: var(--mg-primary); background: color-mix(in srgb, var(--mg-primary) 9%, transparent); }
.pg-readiness.is-ready { color: var(--mg-success); background: var(--mg-success-bg); }
.price-inline-field { display: grid; gap: .3rem; color: var(--mg-text-muted); font-size: .78rem; font-weight: 800; }
.price-inline-control { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: .45rem; min-width: 0; }
.quick-price-save { min-width: 108px; min-height: 2.65rem; white-space: nowrap; }
.pg-quick-toggles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem; }
.pg-quick-toggles :deep(.toggle-switch) { min-height: 4.2rem; }
@media (max-width: 860px) {
  .product-general-layout { grid-template-columns: minmax(170px, .55fr) minmax(0, 1fr); gap: .6rem; }
  .general-image-shell { min-height: 220px; height: clamp(220px, 30vw, 280px); }
  .pg-status-pill { white-space: normal; text-align: center; }
}
@media (max-width: 560px) {
  .product-general-layout { grid-template-columns: 1fr; }
  .general-image-shell { width: 100%; height: min(76vw, 300px); min-height: 220px; aspect-ratio: 16 / 10; }
  .product-general-main { gap: .65rem; }
  .pg-status-row { align-items: stretch; }
  .pg-status-pill { flex: 1 1 auto; justify-content: center; }
  .price-inline-control { grid-template-columns: 1fr; }
  .quick-price-save { width: 100%; }
}
</style>
