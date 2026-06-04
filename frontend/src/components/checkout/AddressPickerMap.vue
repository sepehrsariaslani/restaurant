<template>
  <div class="map-wrap">
    <div ref="mapRef" class="map-surface" :class="{ hidden: !isMapVisible }"></div>
    <p class="muted" v-if="statusText">{{ statusText }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ lat: '', lng: '' }),
  },
  config: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue', 'status'])

const mapRef = ref(null)
const mapInstance = ref(null)
const markerInstance = ref(null)
const status = ref('')
const mapReady = ref(false)

const statusText = computed(() => {
  if (status.value === 'loading') {
    return 'در حال بارگذاری نقشه...'
  }
  if (status.value === 'missing_api_key') {
    return 'کلید نقشه تنظیم نشده است. مختصات را دستی وارد کنید.'
  }
  if (status.value === 'error') {
    return 'نقشه بارگذاری نشد. لطفا مختصات را دستی ثبت کنید.'
  }
  return ''
})

const isMapVisible = computed(() => mapReady.value && !statusText.value)

function toNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function currentLatLng() {
  const lat = toNumber(props.modelValue?.lat)
  const lng = toNumber(props.modelValue?.lng)
  const defaultLat = toNumber(props.config?.default_lat) || 35.6997
  const defaultLng = toNumber(props.config?.default_lng) || 51.3381
  return {
    lat: lat ?? defaultLat,
    lng: lng ?? defaultLng,
  }
}

function emitLatLng(lat, lng) {
  emit('update:modelValue', {
    ...(props.modelValue || {}),
    lat,
    lng,
  })
}

function setStatus(nextStatus) {
  status.value = nextStatus
  emit('status', nextStatus)
}

async function ensureNeshanLoaded(config = {}) {
  if (window.L && window.L.Map) {
    return window.L
  }

  if (window.__restaurantNeshanLoader) {
    return window.__restaurantNeshanLoader
  }

  const scriptUrl = String(config.script_url || '').trim()
  const styleUrl = String(config.style_url || '').trim()
  if (!scriptUrl) {
    throw new Error('missing_script_url')
  }

  window.__restaurantNeshanLoader = new Promise((resolve, reject) => {
    if (styleUrl && !document.querySelector(`link[data-neshan-style="${styleUrl}"]`)) {
      const style = document.createElement('link')
      style.rel = 'stylesheet'
      style.href = styleUrl
      style.dataset.neshanStyle = styleUrl
      document.head.appendChild(style)
    }

    if (document.querySelector(`script[data-neshan-script="${scriptUrl}"]`)) {
      const intervalId = window.setInterval(() => {
        if (window.L && window.L.Map) {
          window.clearInterval(intervalId)
          resolve(window.L)
        }
      }, 40)
      window.setTimeout(() => {
        window.clearInterval(intervalId)
        reject(new Error('script_timeout'))
      }, 10000)
      return
    }

    const script = document.createElement('script')
    script.src = scriptUrl
    script.async = true
    script.dataset.neshanScript = scriptUrl
    script.onload = () => resolve(window.L)
    script.onerror = () => reject(new Error('script_load_failed'))
    document.head.appendChild(script)
  })

  return window.__restaurantNeshanLoader
}

function destroyMap() {
  if (mapInstance.value && typeof mapInstance.value.remove === 'function') {
    mapInstance.value.remove()
  }
  mapInstance.value = null
  markerInstance.value = null
  mapReady.value = false
}

function updateMarker(lat, lng) {
  if (!mapInstance.value || !window.L) {
    return
  }

  if (!markerInstance.value) {
    markerInstance.value = window.L.marker([lat, lng], { draggable: true }).addTo(mapInstance.value)
    markerInstance.value.on('dragend', (event) => {
      const point = event.target.getLatLng()
      emitLatLng(Number(point.lat.toFixed(6)), Number(point.lng.toFixed(6)))
    })
    return
  }
  markerInstance.value.setLatLng([lat, lng])
}

async function initMap() {
  const apiKey = String(props.config?.api_key || '').trim()
  if (!apiKey) {
    setStatus('missing_api_key')
    return
  }

  setStatus('loading')
  try {
    await ensureNeshanLoaded(props.config || {})
    if (!mapRef.value || !window.L) {
      throw new Error('map_container_missing')
    }

    const { lat, lng } = currentLatLng()
    const zoom = Number(props.config?.default_zoom || 13)
    mapInstance.value = new window.L.Map(mapRef.value, {
      key: apiKey,
      maptype: 'dreamy',
      poi: true,
      traffic: false,
      center: [lat, lng],
      zoom,
    })
    mapInstance.value.on('click', (event) => {
      const point = event.latlng || {}
      const nextLat = Number((point.lat || lat).toFixed(6))
      const nextLng = Number((point.lng || lng).toFixed(6))
      updateMarker(nextLat, nextLng)
      emitLatLng(nextLat, nextLng)
    })
    updateMarker(lat, lng)
    mapReady.value = true
    setStatus('')
  } catch (error) {
    destroyMap()
    setStatus('error')
  }
}

watch(
  () => [props.modelValue?.lat, props.modelValue?.lng],
  ([nextLat, nextLng]) => {
    if (!mapReady.value || !mapInstance.value) {
      return
    }
    const lat = toNumber(nextLat)
    const lng = toNumber(nextLng)
    if (lat == null || lng == null) {
      return
    }
    updateMarker(lat, lng)
    mapInstance.value.panTo([lat, lng], { animate: false })
  },
)

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  destroyMap()
})
</script>

<style scoped>
.map-wrap {
  display: grid;
  gap: 0.4rem;
}

.map-surface {
  min-height: 240px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
}

.map-surface.hidden {
  display: none;
}

.muted {
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-muted);
}
</style>
