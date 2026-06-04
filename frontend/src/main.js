import { createApp } from 'vue'
import App from './App.vue'
import './theme.css'
import { applySavedThemeSettings, hydrateThemeSettingsFromServer } from './utils/themeSettings'

function bootstrapDocument() {
  document.documentElement.setAttribute('lang', 'fa')
  document.documentElement.setAttribute('dir', 'rtl')
}

bootstrapDocument()
applySavedThemeSettings(window._BOOT?.theme_settings || null)

const initialPage = String(window._PAGE || '')
if (initialPage.startsWith('management-')) {
  hydrateThemeSettingsFromServer()
}
createApp(App).mount('#app')
