import { createApp } from "vue";
import App from "./App.vue";
import "./theme.css";
import { applySavedThemeSettings, hydrateThemeSettingsFromServer } from "./utils/themeSettings";

function bootstrapDocument() {
	document.documentElement.setAttribute("lang", "fa");
	document.documentElement.setAttribute("dir", "rtl");
}

bootstrapDocument();
applySavedThemeSettings(window._BOOT?.theme_settings || null);

const initialPage = String(window._PAGE || "");
if (initialPage.startsWith("management-")) {
	hydrateThemeSettingsFromServer();
}

if ("serviceWorker" in navigator) {
	window.addEventListener("load", () => {
		navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch((error) => {
			console.info("[PWA] Service worker registration skipped:", error);
		});
	});
}

createApp(App).mount("#app");
