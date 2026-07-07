<template>
  <div class="loader-renderer" :style="rendererVars">
    <template v-if="normalized.mode === 'custom' && hasCustomCode">
      <iframe
        class="custom-frame"
        :title="normalized.title || 'custom loader'"
        :srcdoc="customSrcdoc"
        sandbox="allow-scripts"
      />
    </template>

    <template v-else-if="normalized.preset === 'steaming-bowl'">
      <SteamingBowlLoader />
    </template>

    <template v-else-if="normalized.preset === 'noodle-bowl'">
      <NoodleBowlLoader />
    </template>

    <template v-else-if="normalized.preset === 'burger-stack'">
      <BurgerStackLoader />
    </template>

    <template v-else-if="normalized.preset === 'club-sandwich'">
      <ClubSandwichLoader />
    </template>

    <template v-else-if="normalized.preset === 'coffee-cup'">
      <CoffeeCupLoader />
    </template>

    <template v-else-if="normalized.preset === 'pizza-slice'">
      <PizzaSliceLoader />
    </template>

    <template v-else>
      <DonutBiteLoader />
    </template>

    <div class="loader-copy" v-if="showCopy">
      <strong>{{ normalized.title }}</strong>
      <p>{{ normalized.subtitle }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BurgerStackLoader from '@/components/loaders/BurgerStackLoader.vue'
import ClubSandwichLoader from '@/components/loaders/ClubSandwichLoader.vue'
import CoffeeCupLoader from '@/components/loaders/CoffeeCupLoader.vue'
import DonutBiteLoader from '@/components/loaders/DonutBiteLoader.vue'
import NoodleBowlLoader from '@/components/loaders/NoodleBowlLoader.vue'
import PizzaSliceLoader from '@/components/loaders/PizzaSliceLoader.vue'
import SteamingBowlLoader from '@/components/loaders/SteamingBowlLoader.vue'
import { normalizeLoaderSettings } from '@/utils/loaderSettings'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({}),
  },
  hideCopy: {
    type: Boolean,
    default: false,
  },
})

const normalized = computed(() => normalizeLoaderSettings(props.settings || {}))
const hasCustomCode = computed(() => Boolean(String(normalized.value.customCode || '').trim()))
const showCopy = computed(() => !props.hideCopy)

function hexToRgbString(hex) {
  const value = String(hex || '').replace('#', '')
  if (value.length !== 6) {
    return '106 154 107'
  }
  const red = Number.parseInt(value.slice(0, 2), 16)
  const green = Number.parseInt(value.slice(2, 4), 16)
  const blue = Number.parseInt(value.slice(4, 6), 16)
  return `${red} ${green} ${blue}`
}

const rendererVars = computed(() => ({
  '--loader-accent': normalized.value.accentColor,
  '--loader-accent-rgb': hexToRgbString(normalized.value.accentColor),
  '--loader-overlay-color': normalized.value.overlayColor,
}))

const customSrcdoc = computed(() => {
  const raw = String(normalized.value.customCode || '').trim()
  if (!raw) {
    return ''
  }
  if (/<html[\s>]/i.test(raw)) {
    return raw
  }
  return `<!doctype html>
<html lang="fa" dir="rtl">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      :root { color-scheme: light; }
      * { box-sizing: border-box; }
      html, body {
        width: 100%;
        height: 100%;
        margin: 0;
        overflow: hidden;
        background: transparent;
        font-family: Vazirmatn, sans-serif;
      }
      body {
        display: grid;
        place-items: center;
      }
      .loader-root {
        width: 100%;
        height: 100%;
        display: grid;
        place-items: center;
      }
    </style>
  </head>
  <body>
    <div class="loader-root">${raw}</div>
  </body>
</html>`
})
</script>

<style scoped>
.loader-renderer {
  width: min(92vw, 420px);
  display: grid;
  justify-items: center;
  gap: 1rem;
}

.loader-copy {
  text-align: center;
  display: grid;
  gap: 0.25rem;
}

.loader-copy strong {
  font-size: 1rem;
  color: #223429;
}

.loader-copy p {
  margin: 0;
  font-size: 0.83rem;
  color: rgb(34 52 41 / 0.72);
}

.custom-frame {
  width: min(92vw, 460px);
  height: 220px;
  border: 0;
  background: transparent;
}
</style>
