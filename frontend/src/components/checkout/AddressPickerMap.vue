<template>
  <div class="map-wrap">
    <div ref="mapRef" class="map-surface" role="region" aria-label="نقشه انتخاب محل تحویل؛ با لمس نقشه یا جابه‌جایی نشانگر محل را انتخاب کنید"></div>
    <div class="map-caption">
      <MapPin :size="17" aria-hidden="true" />
      <span v-if="hasPoint">محل تحویل انتخاب شد؛ برای تغییر، روی نقشه بزنید.</span>
      <span v-else>نقطه دقیق تحویل را روی نقشه انتخاب کنید.</span>
    </div>
    <button v-if="ready" class="map-center-action" type="button" @click="chooseCenter">انتخاب مرکز نقشه</button>
    <p v-if="statusText" class="map-status" role="status">{{ statusText }}</p>
    <button v-if="status === 'error'" class="map-center-action" type="button" @click="initMap">تلاش دوباره برای نقشه</button>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { MapPin } from 'lucide-vue-next'
import * as Leaflet from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { coordinateNumber, hasDeliveryCoordinates } from '@/utils/customerOrderValidation'

const props = defineProps({ modelValue: { type: Object, default: () => ({ lat: '', lng: '' }) }, config: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue', 'status'])
const mapRef = ref(null)
const ready = ref(false)
const status = ref('loading')
const hasPoint = computed(() => hasDeliveryCoordinates(props.modelValue))
const statusText = computed(() => ({ loading: 'در حال دریافت نقشه…', error: 'نقشه در دسترس نیست. دوباره تلاش کنید یا از موقعیت من و مختصات دستی استفاده کنید.', tiles_error: 'بخشی از نقشه دریافت نشد؛ اتصال اینترنت را بررسی کنید.' }[status.value] || ''))
let map, marker, sdk = Leaflet, observer, generation = 0, mounted = false
const pin = Leaflet.icon({ iconUrl: markerIcon, iconRetinaUrl: markerIconRetina, shadowUrl: markerShadow, iconSize: [25, 41], iconAnchor: [12, 41], shadowSize: [41, 41] })

function setStatus(value) { status.value = value; emit('status', value) }
function point() {
  return [coordinateNumber(props.modelValue?.lat, -90, 90) ?? coordinateNumber(props.config.default_lat, -90, 90) ?? 35.6997,
    coordinateNumber(props.modelValue?.lng, -180, 180) ?? coordinateNumber(props.config.default_lng, -180, 180) ?? 51.3381]
}
function choose(lat, lng) {
  const next = { lat: Number(lat.toFixed(6)), lng: Number(lng.toFixed(6)) }
  if (!hasDeliveryCoordinates(next)) return
  updateMarker(next.lat, next.lng)
  emit('update:modelValue', { ...props.modelValue, ...next })
}
function chooseCenter() { if (map) { const center = map.getCenter(); choose(center.lat, center.lng) } }
function updateMarker(lat, lng) {
  if (!map) return
  if (!marker) {
    marker = sdk.marker([lat, lng], { draggable: true, icon: pin, title: 'محل تحویل', alt: 'محل تحویل انتخاب‌شده' }).addTo(map)
    marker.on('dragend', () => { const p = marker.getLatLng(); choose(p.lat, p.lng) })
  } else marker.setLatLng([lat, lng])
}
async function loadNeshan() {
  if (window.L?.Map && window.L !== Leaflet && window.__restaurantNeshanReady) return window.L
  if (!window.__restaurantNeshanLoader) {
    window.__restaurantNeshanLoader = new Promise((resolve, reject) => {
      const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = props.config.style_url; document.head.appendChild(css)
      const script = document.createElement('script'); script.src = props.config.script_url; script.async = true
      const timer = setTimeout(() => reject(new Error('map_timeout')), 12000)
      script.onload = () => { clearTimeout(timer); window.__restaurantNeshanReady = true; resolve(window.L) }
      script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error('map_failed')) }
      document.head.appendChild(script)
    }).catch((error) => { window.__restaurantNeshanLoader = null; throw error })
  }
  return window.__restaurantNeshanLoader
}
function destroyMap() { observer?.disconnect(); map?.remove(); map = null; marker = null; ready.value = false }
async function initMap() {
  if (!mounted) return
  const id = ++generation
  destroyMap(); setStatus('loading')
  try {
    const useNeshan = Boolean(String(props.config.api_key || '').trim())
    const selectedSdk = useNeshan ? await loadNeshan() : Leaflet
    await nextTick()
    if (id !== generation || !mounted) return
    sdk = selectedSdk
    const options = { center: point(), zoom: Number(props.config.default_zoom || 14), scrollWheelZoom: false }
    map = useNeshan
      ? new sdk.Map(mapRef.value, { ...options, key: props.config.api_key, maptype: 'dreamy', poi: true, traffic: false })
      : Leaflet.map(mapRef.value, options)
    if (!useNeshan) {
      Leaflet.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).on('tileerror', () => setStatus('tiles_error')).on('tileload', () => { if (status.value === 'loading') setStatus('') }).addTo(map)
    }
    map.on('click', (event) => choose(event.latlng.lat, event.latlng.lng))
    if (hasPoint.value) updateMarker(...point())
    if (typeof ResizeObserver !== 'undefined') { observer = new ResizeObserver(() => map?.invalidateSize()); observer.observe(mapRef.value) }
    ready.value = true; setStatus('')
  } catch { if (id === generation && mounted) { destroyMap(); setStatus('error') } }
}
watch(() => [props.config.api_key, props.config.script_url, props.config.provider], initMap)
watch(() => [props.config.default_lat, props.config.default_lng], () => { if (map && !hasPoint.value) map.setView(point(), map.getZoom()) })
watch(() => [props.modelValue?.lat, props.modelValue?.lng], () => {
  if (!map) return
  if (!hasPoint.value) { marker?.remove(); marker = null; return }
  updateMarker(...point()); map.panTo(point(), { animate: false })
})
onMounted(() => { mounted = true; initMap() })
onUnmounted(() => { mounted = false; generation++; destroyMap() })
</script>

<style scoped>
.map-wrap { display: grid; gap: .7rem; }
.map-surface { min-height: 300px; height: clamp(300px, 45vh, 410px); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); overflow: hidden; z-index: 0; background: var(--ds-color-surface-muted); }
.map-caption { display: flex; gap: .4rem; align-items: center; font-size: .82rem; color: var(--ds-color-action-primary); }
.map-status { margin: 0; color: var(--ds-color-text-secondary); font-size: .8rem; }
.map-center-action { justify-self: start; min-height: 44px; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); border-radius: var(--ds-radius-sm); padding: .5rem .8rem; color: var(--ds-color-action-primary); font: inherit; cursor: pointer; }
.map-wrap :deep(.leaflet-control-zoom a) { width: 44px; height: 44px; line-height: 44px; }
.map-wrap :deep(.leaflet-control-attribution) { direction: ltr; }
</style>
