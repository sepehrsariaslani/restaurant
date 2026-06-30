import { Utensils } from "lucide-vue-next";
import * as AllIcons from "lucide-vue-next";

const SKIP_KEYS = new Set(["default", "icons", "createLucideIcon"]);

function normalizeIconName(name = "") {
	return String(name || "")
		.replace(/Icon$/, "")
		.trim();
}

function isLucideComponent(key, value) {
	if (SKIP_KEYS.has(key)) return false;
	if (!/^[A-Z]/.test(String(key || ""))) return false;
	return typeof value === "function";
}

function humanizeIconName(name = "") {
	return normalizeIconName(name)
		.replace(/([a-z0-9])([A-Z])/g, "$1 $2")
		.replace(/([A-Z])([A-Z][a-z])/g, "$1 $2")
		.trim();
}

const uniqueIcons = new Map();

for (const [rawName, component] of Object.entries(AllIcons)) {
	if (!isLucideComponent(rawName, component)) continue;
	const name = normalizeIconName(rawName);
	if (!name) continue;
	if (uniqueIcons.has(name)) continue;
	uniqueIcons.set(name, component);
}

export const MENU_ICON_OPTIONS = Array.from(uniqueIcons.entries())
	.map(([value, component]) => ({
		value,
		label: humanizeIconName(value),
		keywords: [value.toLowerCase(), humanizeIconName(value).toLowerCase()],
		component,
	}))
	.sort((a, b) => a.label.localeCompare(b.label));

export const MENU_ICON_COMPONENTS = MENU_ICON_OPTIONS.reduce((acc, option) => {
	acc[option.value] = option.component;
	return acc;
}, {});

export function sanitizeMenuIcon(value = "") {
	const normalized = normalizeIconName(String(value || "").trim());
	return MENU_ICON_COMPONENTS[normalized] ? normalized : "";
}

export function getMenuIconComponent(value = "", fallback = Utensils) {
	return MENU_ICON_COMPONENTS[sanitizeMenuIcon(value)] || fallback;
}

export function inferMenuIconFromText(value = "") {
	const text = String(value || "").toLowerCase();
	const matched = MENU_ICON_OPTIONS.find((option) =>
		option.keywords.some((keyword) => text.includes(String(keyword).toLowerCase())),
	);
	return matched?.component || Utensils;
}
