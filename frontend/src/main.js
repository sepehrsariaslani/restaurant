import { createApp } from "vue";
import App from "./App.vue";
import "./theme.css";
import "./design-system/customer.css";
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

if (window.location.pathname !== "/design-preview" && "serviceWorker" in navigator) {
	window.addEventListener("load", () => {
		navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch((error) => {
			console.info("[PWA] Service worker registration skipped:", error);
		});
	});
}

const path = window.location.pathname;
const isDesignPreview = path === "/design-preview";
const isCustomPage = path.startsWith("/p/") || window._PAGE === "custom-design-page";
if (isDesignPreview || isCustomPage) {
	import("./pages/design/RestaurantDesignSurface.vue").then(({ default: Surface }) => {
		createApp(Surface, { preview: isDesignPreview }).mount("#app");
	});
} else {
	createApp(App).mount("#app");
}
