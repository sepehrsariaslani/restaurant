<template>
  <div class="branch-map-picker" :class="{ 'is-empty': !locatedBranches.length }" dir="rtl">
    <div v-if="locatedBranches.length" ref="mapElement" class="branch-map-picker__surface" role="img" aria-label="نقشه شعب قابل انتخاب"></div>
    <div v-else class="branch-map-picker__empty">
      <MapPin :size="20" aria-hidden="true" />
      <span>موقعیت شعبه‌ها هنوز روی نقشه ثبت نشده است.</span>
    </div>
    <p v-if="showDeliveryRadius && selectedBranch?.delivery_radius_km > 0" class="branch-map-picker__caption">
      محدودهٔ تقریبی ارسال شعبهٔ انتخاب‌شده با دایره نمایش داده شده است.
    </p>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { MapPin } from 'lucide-vue-next'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  branches: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  showDeliveryRadius: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const mapElement = ref(null)
const locatedBranches = computed(() => (props.branches || []).filter((row) => {
  const lat = Number(row?.lat)
  const lng = Number(row?.lng)
  return Number.isFinite(lat) && lat >= -90 && lat <= 90 && Number.isFinite(lng) && lng >= -180 && lng <= 180 && !(lat === 0 && lng === 0)
}))
const selectedBranch = computed(() => locatedBranches.value.find((row) => String(row.id || row.name || '') === props.modelValue) || null)
let map = null
let layer = null
let resizeObserver = null
let mounted = false
let generation = 0

function branchId(row) { return String(row?.id || row?.name || '') }
function branchIcon(selected) {
  return L.divIcon({
    className: 'branch-map-leaflet-icon',
    html: `<span class="branch-map-pin${selected ? ' is-selected' : ''}"></span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

function renderBranches() {
  if (!map || !layer) return
  layer.clearLayers()
  const bounds = []
  locatedBranches.value.forEach((branch) => {
    const id = branchId(branch)
    const point = [Number(branch.lat), Number(branch.lng)]
    bounds.push(point)
    if (props.showDeliveryRadius && id === props.modelValue && Number(branch.delivery_radius_km) > 0) {
      const radius = L.circle(point, { radius: Number(branch.delivery_radius_km) * 1000, interactive: false }).addTo(layer)
      const path = radius.getElement()
      if (path) {
        path.style.stroke = 'var(--ds-color-action-primary)'
        path.style.fill = 'var(--ds-color-action-primary-soft)'
        path.style.fillOpacity = '0.2'
      }
    }
    L.marker(point, { icon: branchIcon(id === props.modelValue), title: branch.title || branch.name || 'شعبه' })
      .on('click', () => emit('update:modelValue', id))
      .addTo(layer)
  })
  const selected = selectedBranch.value
  if (selected) map.setView([Number(selected.lat), Number(selected.lng)], Math.max(map.getZoom(), 12), { animate: false })
  else if (bounds.length > 1) map.fitBounds(bounds, { padding: [28, 28], maxZoom: 13 })
  else if (bounds.length === 1) map.setView(bounds[0], 12, { animate: false })
}

async function initMap() {
  if (!mounted || !locatedBranches.value.length) return
  const currentGeneration = ++generation
  await nextTick()
  if (!mounted || currentGeneration !== generation || !mapElement.value) return
  map?.remove()
  map = L.map(mapElement.value, { zoomControl: true, scrollWheelZoom: false, attributionControl: true })
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map)
  layer = L.featureGroup().addTo(map)
  renderBranches()
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => map?.invalidateSize())
    resizeObserver.observe(mapElement.value)
  }
}

watch(() => [locatedBranches.value.map((row) => `${branchId(row)}:${row.lat}:${row.lng}:${row.delivery_radius_km || ''}`).join('|'), props.modelValue, props.showDeliveryRadius], async () => {
  if (!locatedBranches.value.length) {
    resizeObserver?.disconnect()
    map?.remove()
    map = null
    layer = null
    return
  }
  if (!map) await initMap()
  else renderBranches()
})
onMounted(() => { mounted = true; initMap() })
onUnmounted(() => { mounted = false; generation++; resizeObserver?.disconnect(); map?.remove(); map = null; layer = null })
</script>

<style scoped>
.branch-map-picker { display: grid; gap: .45rem; }
.branch-map-picker__surface { height: clamp(210px, 32vh, 300px); min-height: 210px; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); overflow: hidden; z-index: 0; background: var(--ds-color-surface-muted); }
.branch-map-picker__empty { display: flex; align-items: center; gap: .55rem; min-height: 72px; padding: .8rem 1rem; border: 1px dashed var(--ds-color-border); border-radius: var(--ds-radius-md); color: var(--ds-color-text-secondary); background: var(--ds-color-surface-muted); font-size: .84rem; }
.branch-map-picker__caption { margin: 0; color: var(--ds-color-text-muted); font-size: .76rem; }
.branch-map-picker :deep(.leaflet-control-zoom a) { width: 42px; height: 42px; line-height: 42px; }
.branch-map-picker :deep(.leaflet-control-attribution) { direction: ltr; }
:global(.branch-map-leaflet-icon) { background: transparent; border: 0; }
:global(.branch-map-pin) { display: block; width: 24px; height: 24px; border: 3px solid var(--ds-color-surface-raised); border-radius: 50% 50% 50% 0; transform: rotate(-45deg); background: var(--ds-color-action-primary); box-shadow: var(--ds-shadow-sm); }
:global(.branch-map-pin.is-selected) { background: var(--ds-color-action-accent); transform: rotate(-45deg) scale(1.12); }
</style>
