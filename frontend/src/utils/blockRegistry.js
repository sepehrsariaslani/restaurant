// Block Registry
//
// Single source of truth for the block-based home page.
// Both the public renderer (HomePageRenderer.vue) and the management
// builder read from this file, so a block type only needs to be
// described once.
//
// Each block "type" describes:
//   - label:       human label (fa) shown in the builder
//   - icon:        lucide icon name for the builder list
//   - component:   the Vue component that renders it
//   - variants:    array of { value, label, desc } design options
//   - defaultVariant
//   - props:       schema of editable, per-instance content fields
//   - toProps:     (block, boot) => object of props passed to the component
//   - single:      if true, only one instance of this block is allowed
//
// The `props` schema is intentionally declarative so the builder can
// auto-generate its form. Each field is:
//   { key, label, type, default, options?, help? }
// type is one of: text | textarea | image | number | boolean | select | link | features

import { defineAsyncComponent, markRaw } from "vue";

// Lazy component imports keep the public bundle small.
const HeroBlock = defineAsyncComponent(() => import("@/components/blocks/HeroBlock.vue"));
const AboutBlock = defineAsyncComponent(() => import("@/components/blocks/AboutBlock.vue"));
const ProductsBlock = defineAsyncComponent(() => import("@/components/blocks/ProductsBlock.vue"));
const CategoriesBlock = defineAsyncComponent(() => import("@/components/blocks/CategoriesBlock.vue"));
const FeaturesBlock = defineAsyncComponent(() => import("@/components/blocks/FeaturesBlock.vue"));
const FaqBlock = defineAsyncComponent(() => import("@/components/blocks/FaqBlock.vue"));
const BannerBlock = defineAsyncComponent(() => import("@/components/blocks/BannerBlock.vue"));
const PopularBlock = defineAsyncComponent(() => import("@/components/blocks/PopularBlock.vue"));
const HealthyHeroBlock = defineAsyncComponent(() => import("@/components/blocks/HealthyHeroBlock.vue"));

let _uid = 0;
export function makeBlockId(type = "blk") {
	_uid += 1;
	return `${type}_${Date.now().toString(36)}_${_uid}`;
}

function str(value, fallback = "") {
	const out = String(value ?? "").trim();
	return out || fallback;
}

function num(value, fallback = 0) {
	const out = Number(value);
	return Number.isFinite(out) ? out : fallback;
}

function bool(value, fallback = false) {
	if (value === undefined || value === null || value === "") return fallback;
	return Number(value) ? true : Boolean(value);
}

function productKey(item = {}) {
	return str(item?.slug || item?.item_code || item?.item || item?.name || item?.title).toLowerCase();
}

function firstNonEmptyArray(...values) {
	return values.find((value) => Array.isArray(value) && value.length) || [];
}

// ---------------------------------------------------------------------------
// Block type definitions
// ---------------------------------------------------------------------------

export const BLOCK_TYPES = {
	hero: {
		type: "hero",
		label: "\u0647\u06cc\u0631\u0648",
		icon: "image",
		component: markRaw(HeroBlock),
		single: false,
		variants: [
			{ value: "slider", label: "\u0627\u0633\u0644\u0627\u06cc\u062f\u0631", desc: "\u0686\u0646\u062f \u0627\u0633\u0644\u0627\u06cc\u062f \u062a\u0635\u0648\u06cc\u0631\u06cc \u0628\u0627 CTA \u0645\u0633\u062a\u0642\u0644" },
			{ value: "fullscreen", label: "\u062a\u0645\u0627\u0645\u200c\u0635\u0641\u062d\u0647", desc: "\u0628\u0646\u0631 \u0628\u0632\u0631\u06af \u062a\u0645\u0627\u0645 \u0635\u0641\u062d\u0647 \u0628\u0627 \u062a\u0635\u0648\u06cc\u0631 \u067e\u0633\u200c\u0632\u0645\u06cc\u0646\u0647 \u0648 \u0647\u062f\u0631 \u0634\u0641\u0627\u0641" },
			{ value: "banner", label: "\u0628\u0646\u0631 \u06a9\u0648\u062a\u0627\u0647", desc: "\u0628\u0646\u0631 \u0627\u0641\u0642\u06cc \u062c\u0645\u0639\u200c\u0648\u062c\u0648\u0631 \u0628\u0627 \u0627\u0631\u062a\u0641\u0627\u0639 \u06a9\u0645\u062a\u0631\u060c \u0645\u0646\u0627\u0633\u0628 \u0628\u0631\u0627\u06cc \u0635\u0641\u062d\u0627\u062a \u0645\u06cc\u0646\u06cc\u0645\u0627\u0644" },
			{ value: "cover", label: "\u06a9\u0627\u0648\u0631 \u0633\u0627\u0644\u0645", desc: "\u0647\u06cc\u0631\u0648 \u0631\u0648\u0634\u0646 \u0634\u0628\u06cc\u0647 \u062a\u0635\u0648\u06cc\u0631 \u0646\u0645\u0648\u0646\u0647\u061b \u0639\u06a9\u0633 \u063a\u0630\u0627\u060c \u0645\u062a\u0646 \u0628\u0632\u0631\u06af\u060c \u062f\u06a9\u0645\u0647\u200c\u0647\u0627 \u0648 \u0645\u0632\u06cc\u062a\u200c\u0647\u0627" },
			{ value: "foodbar", label: "\u0641\u0648\u062f\u0628\u0627\u0631 \u0645\u062d\u0635\u0648\u0644\u06cc", desc: "\u0647\u06cc\u0631\u0648 \u0645\u062d\u0635\u0648\u0644\u200c\u0645\u062d\u0648\u0631 \u0628\u0627 \u062a\u0635\u0648\u06cc\u0631 \u0628\u0632\u0631\u06af \u0648 \u062a\u0645\u0631\u06a9\u0632 \u0631\u0648\u06cc \u0622\u06cc\u062a\u0645\u200c\u0647\u0627\u06cc \u067e\u0631\u0641\u0631\u0648\u0634" },
			{ value: "minimal", label: "\u0645\u06cc\u0646\u06cc\u0645\u0627\u0644", desc: "\u0641\u0642\u0637 \u0639\u0646\u0648\u0627\u0646\u060c \u062a\u0648\u0636\u06cc\u062d \u06a9\u0648\u062a\u0627\u0647 \u0648 \u062f\u06a9\u0645\u0647" },
			{ value: "split", label: "\u062f\u0648\u0633\u062a\u0648\u0646\u0647", desc: "\u0645\u062a\u0646 \u062f\u0631 \u06cc\u06a9 \u0633\u0645\u062a\u060c \u062a\u0635\u0648\u06cc\u0631 \u062f\u0631 \u0633\u0645\u062a \u062f\u06cc\u06af\u0631" },
		],
		defaultVariant: "fullscreen",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646 \u0627\u0635\u0644\u06cc", type: "text", default: "" },
			{ key: "description", label: "\u062a\u0648\u0636\u06cc\u062d", type: "textarea", default: "" },
			{ key: "image", label: "\u062a\u0635\u0648\u06cc\u0631", type: "image", default: "" },
			{ key: "ctaLabel", label: "\u0645\u062a\u0646 \u062f\u06a9\u0645\u0647 \u0627\u0635\u0644\u06cc", type: "text", default: "\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648" },
			{ key: "ctaHref", label: "\u0644\u06cc\u0646\u06a9 \u062f\u06a9\u0645\u0647 \u0627\u0635\u0644\u06cc", type: "link", default: "/menu" },
			{ key: "secondaryLabel", label: "\u0645\u062a\u0646 \u062f\u06a9\u0645\u0647 \u062f\u0648\u0645", type: "text", default: "" },
			{ key: "secondaryHref", label: "\u0644\u06cc\u0646\u06a9 \u062f\u06a9\u0645\u0647 \u062f\u0648\u0645", type: "link", default: "" },
			{
				key: "slidesSource",
				label: "\u0645\u0646\u0628\u0639 \u0627\u0633\u0644\u0627\u06cc\u062f\u0647\u0627",
				type: "select",
				default: "hero_slides",
				options: [
					{ value: "hero_slides", label: "\u0627\u0633\u0644\u0627\u06cc\u062f\u0647\u0627\u06cc \u062a\u0639\u0631\u06cc\u0641\u200c\u0634\u062f\u0647" },
					{ value: "featured", label: "\u0645\u062d\u0635\u0648\u0644\u0627\u062a \u0648\u06cc\u0698\u0647" },
				],
				help: "\u0641\u0642\u0637 \u0628\u0631\u0627\u06cc \u0648\u0627\u0631\u06cc\u0627\u0646\u062a \u0627\u0633\u0644\u0627\u06cc\u062f\u0631",
			},
		],
		toProps(block, boot) {
			const p = block.props || {};
			const slidesSource = str(p.slidesSource, "hero_slides");
			const slides =
				slidesSource === "featured" ? boot.featured_items || [] : boot.hero_slides || [];
			return {
				variant: str(block.variant, "cover"),
				eyebrow: str(p.eyebrow),
				title: str(p.title),
				description: str(p.description),
				image: str(p.image),
				ctaLabel: str(p.ctaLabel, "\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648"),
				ctaHref: str(p.ctaHref, "/menu"),
				secondaryLabel: str(p.secondaryLabel),
				secondaryHref: str(p.secondaryHref),
				slides,
				currency: str(boot.currency, "IRR"),
			};
		},
	},

	about: {
		type: "about",
		label: "\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627",
		icon: "info",
		component: markRaw(AboutBlock),
		single: false,
		variants: [
			{ value: "cards", label: "\u06a9\u0627\u0631\u062a\u06cc", desc: "\u0686\u0646\u062f \u06a9\u0627\u0631\u062a \u062a\u0635\u0648\u06cc\u0631 + \u0645\u062a\u0646" },
			{ value: "story", label: "\u062f\u0627\u0633\u062a\u0627\u0646", desc: "\u06cc\u06a9 \u0628\u0644\u0648\u06a9 \u0645\u062a\u0646\u06cc \u062a\u0645\u06cc\u0632 \u0628\u0627 \u062a\u0635\u0648\u06cc\u0631" },
			{ value: "stats", label: "\u0622\u0645\u0627\u0631\u06cc", desc: "\u062a\u0645\u0631\u06a9\u0632 \u0631\u0648\u06cc \u0627\u0639\u062f\u0627\u062f \u0648 \u062f\u0633\u062a\u0627\u0648\u0631\u062f\u0647\u0627" },
		],
		defaultVariant: "cards",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{ key: "moreLabel", label: "\u0645\u062a\u0646 \u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "text", default: "\u0645\u0634\u0627\u0647\u062f\u0647 \u06a9\u0627\u0645\u0644" },
			{ key: "moreHref", label: "\u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "link", default: "/about-us" },
			{ key: "limit", label: "\u062a\u0639\u062f\u0627\u062f \u0628\u062e\u0634 \u0646\u0645\u0627\u06cc\u0634\u06cc", type: "number", default: 3 },
		],
		toProps(block, boot) {
			const p = block.props || {};
			return {
				variant: str(block.variant, "cards"),
				eyebrow: str(p.eyebrow, "\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627"),
				title: str(p.title, "\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627"),
				subtitle: str(p.subtitle),
				moreLabel: str(p.moreLabel, "\u0645\u0634\u0627\u0647\u062f\u0647 \u06a9\u0627\u0645\u0644"),
				moreHref: str(p.moreHref, "/about-us"),
				sections: boot.about_us_sections || [],
				limit: num(p.limit, 3),
			};
		},
	},

	products: {
		type: "products",
		label: "\u0645\u062d\u0635\u0648\u0644\u0627\u062a",
		icon: "utensils",
		component: markRaw(ProductsBlock),
		single: false,
		variants: [
			{ value: "grid", label: "\u0634\u0628\u06a9\u0647\u200c\u0627\u06cc", desc: "\u06a9\u0627\u0631\u062a\u200c\u0647\u0627\u06cc \u0645\u062d\u0635\u0648\u0644 \u062f\u0631 \u06af\u0631\u06cc\u062f" },
			{ value: "rail", label: "\u0631\u06cc\u0644 \u0627\u0641\u0642\u06cc", desc: "\u0627\u0633\u06a9\u0631\u0648\u0644 \u0627\u0641\u0642\u06cc \u0645\u062d\u0635\u0648\u0644\u0627\u062a" },
			{ value: "spotlight", label: "\u0648\u06cc\u0698\u0647", desc: "\u06cc\u06a9 \u0645\u062d\u0635\u0648\u0644 \u0628\u0632\u0631\u06af + \u0686\u0646\u062f \u06a9\u0648\u0686\u06a9" },
		],
		defaultVariant: "grid",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u067e\u0631\u0641\u0631\u0648\u0634\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646 \u0627\u0646\u062a\u062e\u0627\u0628\u200c\u0647\u0627" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{
				key: "source",
				label: "\u0645\u0646\u0628\u0639 \u0645\u062d\u0635\u0648\u0644\u0627\u062a",
				type: "select",
				default: "featured",
				options: [
					{ value: "featured", label: "\u0648\u06cc\u0698\u0647" },
					{ value: "best_seller", label: "\u067e\u0631\u0641\u0631\u0648\u0634" },
					{ value: "category", label: "\u06cc\u06a9 \u062f\u0633\u062a\u0647 \u0645\u0634\u062e\u0635" },
				],
			},
			{ key: "category", label: "\u0634\u0646\u0627\u0633\u0647 \u062f\u0633\u062a\u0647", type: "text", default: "", help: "\u0641\u0642\u0637 \u0627\u06af\u0631 \u0645\u0646\u0628\u0639 \u062f\u0633\u062a\u0647 \u0628\u0627\u0634\u062f" },
			{ key: "limit", label: "\u062a\u0639\u062f\u0627\u062f \u0622\u06cc\u062a\u0645", type: "number", default: 8 },
			{
				key: "cardVariant",
				label: "\u0646\u0648\u0639 \u06a9\u0627\u0631\u062a",
				type: "select",
				default: "classic",
				options: [
					{ value: "classic", label: "\u06a9\u0644\u0627\u0633\u06cc\u06a9" },
					{ value: "dark", label: "\u062a\u0627\u0631\u06cc\u06a9" },
					{ value: "navy", label: "\u0646\u06cc\u0648\u06cc" },
				],
			},
		],
		toProps(block, boot) {
			const p = block.props || {};
			const source = str(p.source, "featured");
			let items = [];
			if (source === "best_seller") {
				items = firstNonEmptyArray(boot.best_seller_items, boot.featured_items);
			} else if (source === "category") {
				const cat = str(p.category);
				const all = boot.categories || [];
				const match = all.find(
					(c) => str(c.slug) === cat || str(c.name) === cat || str(c.title) === cat,
				);
				items = (match && (match.items || match.products)) || [];
			} else {
				items = boot.featured_items || [];
			}
			const limit = num(p.limit, 8);
			return {
				variant: str(block.variant, "grid"),
				eyebrow: str(p.eyebrow, "\u067e\u0631\u0641\u0631\u0648\u0634\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627"),
				title: str(p.title, "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646 \u0627\u0646\u062a\u062e\u0627\u0628\u200c\u0647\u0627"),
				subtitle: str(p.subtitle),
				items: limit > 0 ? items.slice(0, limit) : items,
				cardVariant: str(p.cardVariant, "classic"),
				currency: str(boot.currency, "IRR"),
			};
		},
	},

	categories: {
		type: "categories",
		label: "\u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc\u200c\u0647\u0627",
		icon: "grid",
		component: markRaw(CategoriesBlock),
		single: false,
		variants: [
			{ value: "grid", label: "\u0634\u0628\u06a9\u0647\u200c\u0627\u06cc", desc: "\u06a9\u0627\u0631\u062a\u200c\u0647\u0627\u06cc \u062f\u0633\u062a\u0647 \u0628\u0627 \u062a\u0635\u0648\u06cc\u0631" },
			{ value: "pills", label: "\u0686\u06cc\u067e \u0645\u062a\u0646\u06cc", desc: "\u062f\u06a9\u0645\u0647\u200c\u0647\u0627\u06cc \u0633\u0627\u062f\u0647 \u0648 \u062e\u0648\u0627\u0646\u0627" },
			{ value: "circles", label: "\u062f\u0627\u06cc\u0631\u0647\u200c\u0627\u06cc", desc: "\u0622\u06cc\u06a9\u0648\u0646\u200c\u0647\u0627\u06cc \u062f\u0627\u06cc\u0631\u0647\u200c\u0627\u06cc \u0628\u0627 \u0628\u0631\u0686\u0633\u0628" },
		],
		defaultVariant: "grid",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u0627\u0632 \u06a9\u062f\u0627\u0645 \u062f\u0633\u062a\u0647 \u0634\u0631\u0648\u0639 \u0645\u06cc\u200c\u06a9\u0646\u06cc\u062f\u061f" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{ key: "limit", label: "\u062a\u0639\u062f\u0627\u062f \u062f\u0633\u062a\u0647", type: "number", default: 0, help: "0 \u06cc\u0639\u0646\u06cc \u0647\u0645\u0647" },
		],
		toProps(block, boot) {
			const p = block.props || {};
			const limit = num(p.limit, 0);
			const categories = boot.categories || [];
			return {
				variant: str(block.variant, "grid"),
				eyebrow: str(p.eyebrow, "\u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc"),
				title: str(p.title, "\u0627\u0632 \u06a9\u062f\u0627\u0645 \u062f\u0633\u062a\u0647 \u0634\u0631\u0648\u0639 \u0645\u06cc\u200c\u06a9\u0646\u06cc\u062f\u061f"),
				subtitle: str(p.subtitle),
				categories: limit > 0 ? categories.slice(0, limit) : categories,
				currency: str(boot.currency, "IRR"),
			};
		},
	},

	features: {
		type: "features",
		label: "\u0645\u0632\u06cc\u062a\u200c\u0647\u0627",
		icon: "sparkles",
		component: markRaw(FeaturesBlock),
		single: false,
		variants: [
			{ value: "cards", label: "\u06a9\u0627\u0631\u062a\u06cc", desc: "\u0633\u0647 \u06a9\u0627\u0631\u062a \u0622\u06cc\u06a9\u0648\u0646 + \u0645\u062a\u0646" },
			{ value: "inline", label: "\u0631\u062f\u06cc\u0641\u06cc", desc: "\u0646\u0648\u0627\u0631 \u0627\u0641\u0642\u06cc \u0641\u0634\u0631\u062f\u0647" },
		],
		defaultVariant: "cards",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u0686\u0631\u0627 \u0645\u0627\u061f" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u0686\u0646\u062f \u062f\u0644\u06cc\u0644 \u0628\u0631\u0627\u06cc \u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u0627" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{ key: "items", label: "\u0622\u06cc\u062a\u0645\u200c\u0647\u0627", type: "features", default: [] },
		],
		toProps(block) {
			const p = block.props || {};
			const items =
				Array.isArray(p.items) && p.items.length
					? p.items
					: [
							{ icon: "zap", title: "\u062a\u062d\u0648\u06cc\u0644 \u0633\u0631\u06cc\u0639", description: "\u0645\u0633\u06cc\u0631 \u062e\u0631\u06cc\u062f \u06a9\u0648\u062a\u0627\u0647 \u0648 \u0631\u0648\u0634\u0646." },
							{ icon: "sliders", title: "\u0634\u062e\u0635\u06cc\u200c\u0633\u0627\u0632\u06cc", description: "\u0645\u0648\u0627\u062f \u0631\u0627 \u0645\u0637\u0627\u0628\u0642 \u0633\u0644\u06cc\u0642\u0647 \u062a\u0646\u0638\u06cc\u0645 \u06a9\u0646\u06cc\u062f." },
							{ icon: "leaf", title: "\u0645\u0648\u0627\u062f \u062a\u0627\u0632\u0647", description: "\u062a\u0645\u0631\u06a9\u0632 \u0631\u0648\u06cc \u062a\u0627\u0632\u06af\u06cc \u0648 \u06a9\u06cc\u0641\u06cc\u062a." },
					  ];
			return {
				variant: str(block.variant, "cards"),
				eyebrow: str(p.eyebrow, "\u0686\u0631\u0627 \u0645\u0627\u061f"),
				title: str(p.title, "\u0686\u0646\u062f \u062f\u0644\u06cc\u0644 \u0628\u0631\u0627\u06cc \u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u0627"),
				subtitle: str(p.subtitle),
				items,
			};
		},
	},

	faq: {
		type: "faq",
		label: "\u0633\u0648\u0627\u0644\u0627\u062a \u0645\u062a\u062f\u0627\u0648\u0644",
		icon: "help-circle",
		component: markRaw(FaqBlock),
		single: false,
		variants: [
			{ value: "accordion", label: "\u0622\u06a9\u0627\u0631\u062f\u0626\u0648\u0646", desc: "\u0644\u06cc\u0633\u062a \u0628\u0627\u0632/\u0628\u0633\u062a\u0647\u200c\u0634\u0648\u0646\u062f\u0647" },
			{ value: "grid", label: "\u0634\u0628\u06a9\u0647\u200c\u0627\u06cc", desc: "\u062f\u0648 \u0633\u062a\u0648\u0646 \u0633\u0648\u0627\u0644 \u0648 \u062c\u0648\u0627\u0628" },
		],
		defaultVariant: "accordion",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u0633\u0648\u0627\u0644\u0627\u062a \u0645\u062a\u062f\u0627\u0648\u0644" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u0633\u0648\u0627\u0644\u0627\u062a \u0645\u062a\u062f\u0627\u0648\u0644" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{ key: "moreLabel", label: "\u0645\u062a\u0646 \u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "text", default: "\u0647\u0645\u0647 \u0633\u0648\u0627\u0644\u0627\u062a" },
			{ key: "moreHref", label: "\u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "link", default: "/faq" },
			{ key: "limit", label: "\u062a\u0639\u062f\u0627\u062f \u0633\u0648\u0627\u0644", type: "number", default: 6 },
		],
		toProps(block, boot) {
			const p = block.props || {};
			const limit = num(p.limit, 6);
			const faqs = boot.faq_items || [];
			return {
				variant: str(block.variant, "accordion"),
				eyebrow: str(p.eyebrow, "\u0633\u0648\u0627\u0644\u0627\u062a \u0645\u062a\u062f\u0627\u0648\u0644"),
				title: str(p.title, "\u0633\u0648\u0627\u0644\u0627\u062a \u0645\u062a\u062f\u0627\u0648\u0644"),
				subtitle: str(p.subtitle),
				moreLabel: str(p.moreLabel, "\u0647\u0645\u0647 \u0633\u0648\u0627\u0644\u0627\u062a"),
				moreHref: str(p.moreHref, "/faq"),
				faqs: limit > 0 ? faqs.slice(0, limit) : faqs,
			};
		},
	},

	popular: {
		type: "popular",
		label: "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627",
		icon: "flame",
		component: markRaw(PopularBlock),
		single: false,
		variants: [
			{ value: "showcase", label: "\u0648\u06cc\u062a\u0631\u06cc\u0646", desc: "\u06cc\u06a9 \u0645\u062d\u0635\u0648\u0644 \u0628\u0632\u0631\u06af + \u0644\u06cc\u0633\u062a \u0631\u062a\u0628\u0647\u200c\u0628\u0646\u062f\u06cc" },
			{ value: "ranked", label: "\u06af\u0631\u06cc\u062f \u0631\u062a\u0628\u0647\u200c\u062f\u0627\u0631", desc: "\u06a9\u0627\u0631\u062a\u200c\u0647\u0627 \u0628\u0627 \u0634\u0645\u0627\u0631\u0647 \u0645\u062d\u0628\u0648\u0628\u06cc\u062a" },
		],
		defaultVariant: "showcase",
		props: [
			{ key: "eyebrow", label: "\u0628\u0631\u0686\u0633\u0628 \u0628\u0627\u0644\u0627", type: "text", default: "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627" },
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u0645\u062d\u0628\u0648\u0628 \u0645\u0634\u062a\u0631\u06cc\u200c\u0647\u0627" },
			{ key: "subtitle", label: "\u0632\u06cc\u0631\u0639\u0646\u0648\u0627\u0646", type: "text", default: "" },
			{ key: "moreLabel", label: "\u0645\u062a\u0646 \u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "text", default: "\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648" },
			{ key: "moreHref", label: "\u0644\u06cc\u0646\u06a9 \u0628\u06cc\u0634\u062a\u0631", type: "link", default: "/menu" },
			{ key: "excludeFeatured", label: "\u067e\u0646\u0647\u0627\u0646 \u06a9\u0631\u062f\u0646 \u0645\u062d\u0635\u0648\u0644\u0627\u062a \u062a\u06a9\u0631\u0627\u0631\u06cc", type: "boolean", default: false },
			{
				key: "source",
				label: "\u0645\u0646\u0628\u0639",
				type: "select",
				default: "best_seller",
				options: [
					{ value: "best_seller", label: "\u067e\u0631\u0641\u0631\u0648\u0634" },
					{ value: "featured", label: "\u0648\u06cc\u0698\u0647" },
				],
			},
			{ key: "limit", label: "\u062a\u0639\u062f\u0627\u062f \u0622\u06cc\u062a\u0645", type: "number", default: 5 },
		],
		toProps(block, boot) {
			const p = block.props || {};
			const source = str(p.source, "best_seller");
			const highlight = boot.menu_highlight?.items;
			let items;
			if (source === "featured") {
				items = Array.isArray(boot.featured_items) ? boot.featured_items : [];
			} else {
				items = firstNonEmptyArray(boot.best_seller_items, highlight, boot.featured_items);
				if (bool(p.excludeFeatured, false)) {
					const web = boot.web_settings || {};
					const featuredLimit = num(web.restaurant_menu_highlight_featured_limit, 8) || 8;
					const excluded = new Set(
						(Array.isArray(boot.featured_items) ? boot.featured_items : [])
							.slice(0, featuredLimit)
							.map(productKey)
							.filter(Boolean),
					);
					items = items.filter((item) => !excluded.has(productKey(item)));
				}
			}
			const limit = num(p.limit, 5);
			return {
				variant: str(block.variant, "showcase"),
				eyebrow: str(p.eyebrow, "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646\u200c\u0647\u0627"),
				title: str(p.title, "\u0645\u062d\u0628\u0648\u0628 \u0645\u0634\u062a\u0631\u06cc\u200c\u0647\u0627"),
				subtitle: str(p.subtitle),
				moreLabel: str(p.moreLabel, "\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648"),
				moreHref: str(p.moreHref, "/menu"),
				items: limit > 0 ? items.slice(0, limit) : items,
				currency: str(boot.currency, "IRR"),
			};
		},
	},

	banner: {
		type: "banner",
		label: "\u0628\u0646\u0631 / \u06a9\u0627\u0644\u200c\u062a\u0648\u0627\u06a9\u0634\u0646",
		icon: "megaphone",
		component: markRaw(BannerBlock),
		single: false,
		variants: [
			{ value: "solid", label: "\u0631\u0646\u06af\u06cc", desc: "\u067e\u0633\u200c\u0632\u0645\u06cc\u0646\u0647 \u0631\u0646\u06af\u06cc \u06cc\u06a9\u062f\u0633\u062a" },
			{ value: "image", label: "\u062a\u0635\u0648\u06cc\u0631\u06cc", desc: "\u067e\u0633\u200c\u0632\u0645\u06cc\u0646\u0647 \u0639\u06a9\u0633 \u0628\u0627 \u0645\u062a\u0646 \u0631\u0648\u06cc \u0622\u0646" },
		],
		defaultVariant: "solid",
		props: [
			{ key: "title", label: "\u0639\u0646\u0648\u0627\u0646", type: "text", default: "\u067e\u06cc\u0634\u0646\u0647\u0627\u062f \u0627\u0645\u0631\u0648\u0632" },
			{ key: "description", label: "\u062a\u0648\u0636\u06cc\u062d", type: "textarea", default: "" },
			{ key: "image", label: "\u062a\u0635\u0648\u06cc\u0631", type: "image", default: "" },
			{ key: "ctaLabel", label: "\u0645\u062a\u0646 \u062f\u06a9\u0645\u0647", type: "text", default: "\u0634\u0631\u0648\u0639 \u0633\u0641\u0627\u0631\u0634" },
			{ key: "ctaHref", label: "\u0644\u06cc\u0646\u06a9 \u062f\u06a9\u0645\u0647", type: "link", default: "/menu" },
		],
		toProps(block) {
			const p = block.props || {};
			return {
				variant: str(block.variant, "solid"),
				title: str(p.title, "\u067e\u06cc\u0634\u0646\u0647\u0627\u062f \u0627\u0645\u0631\u0648\u0632"),
				description: str(p.description),
				image: str(p.image),
				ctaLabel: str(p.ctaLabel, "\u0634\u0631\u0648\u0639 \u0633\u0641\u0627\u0631\u0634"),
				ctaHref: str(p.ctaHref, "/menu"),
			};
		},
	},

	healthy_hero: {
		type: "healthy_hero",
		label: "هیرو سبز و سه‌بعدی",
		icon: "leaf",
		component: markRaw(HealthyHeroBlock),
		single: true,
		variants: [
			{ value: "club", label: "ساندویچ باشگاهی", desc: "نمایش ساندویچ لایه‌ای با بازشدن تعاملی ترکیبات" },
		],
		defaultVariant: "club",
		props: [
			{ key: "eyebrow", label: "برچسب بالا", type: "text", default: "غذای سالم، با حال خوب" },
			{ key: "title", label: "عنوان اصلی", type: "text", default: "هر روز، یک انتخاب" },
			{ key: "highlight", label: "ادامه عنوان", type: "text", default: "خوش‌طعم‌تر از همیشه" },
			{ key: "description", label: "توضیح", type: "textarea", default: "طعم‌های تازه و ترکیب‌های متعادل، برای وقتی که می‌خواهی هم خوشمزه بخوری هم انتخاب خوبی داشته باشی." },
			{ key: "ctaLabel", label: "متن دکمه اصلی", type: "text", default: "دیدن منوی سالم" },
			{ key: "ctaHref", label: "لینک دکمه اصلی", type: "link", default: "/menu" },
			{ key: "ingredients", label: "ترکیبات ساندویچ", type: "features", default: [
				{ icon: "wheat", title: "نان تست جو", description: "دو برش برشته و خوش‌عطر" },
				{ icon: "leaf", title: "کاهوی تازه", description: "ترد و سبز" },
				{ icon: "utensils", title: "سینه مرغ گریل‌شده", description: "همراه سس سبک سبزیجات" },
				{ icon: "sparkles", title: "پیاز کاراملی", description: "با طعمی ملایم و شیرین" },
				{ icon: "sparkles", title: "کمی ذرت شیرین", description: "برای یک طعم دلنشین" },
			] },
		],
		toProps(block) {
			const p = block.props || {};
			return {
				eyebrow: str(p.eyebrow, "غذای سالم، با حال خوب"),
				title: str(p.title, "هر روز، یک انتخاب"),
				highlight: str(p.highlight, "خوش‌طعم‌تر از همیشه"),
				description: str(p.description, "طعم‌های تازه و ترکیب‌های متعادل، برای وقتی که می‌خواهی هم خوشمزه بخوری هم انتخاب خوبی داشته باشی."),
				ctaLabel: str(p.ctaLabel, "دیدن منوی سالم"),
				ctaHref: str(p.ctaHref, "/menu"),
				ingredients: Array.isArray(p.ingredients) ? p.ingredients : [],
			};
		},
	},
};

const SiteElementBlock = markRaw(defineAsyncComponent(() => import("@/components/blocks/SiteElementBlock.vue")));
const elementField = (key, label, type = "text", value = "", extra = {}) => ({ key, label, type, default: value, ...extra });
Object.assign(BLOCK_TYPES, {
  section: { type: "section", label: "بخش و گروه", variants: [{ value: "stack", label: "عمودی" }, { value: "grid", label: "شبکه" }, { value: "row", label: "ردیفی" }], defaultVariant: "stack", props: [] },
  text: { type: "text", label: "عنوان و متن", variants: [{ value: "default", label: "متن" }], props: [elementField("title", "عنوان", "text", "عنوان تازه"), elementField("body", "متن", "textarea", "متن خود را بنویسید."), elementField("level", "نوع عنوان", "select", "h2", { options: ["h1", "h2", "h3", "h4"].map((value, i) => ({ value, label: `عنوان سطح ${i + 1}` })) })] },
  image: { type: "image", label: "تصویر", variants: [{ value: "default", label: "تصویر" }], props: [elementField("image", "تصویر", "image"), elementField("alt", "توضیح دسترس‌پذیر تصویر"), elementField("caption", "زیرنویس")] },
  button: { type: "button", label: "دکمه و پیوند", variants: [{ value: "solid", label: "رنگی" }, { value: "outline", label: "خطی" }, { value: "text", label: "متنی" }], props: [elementField("label", "متن دکمه", "text", "مشاهده بیشتر"), elementField("href", "نشانی مقصد", "link", "/menu")] },
  spacer: { type: "spacer", label: "فاصله", variants: [{ value: "default", label: "فاصله" }], props: [elementField("height", "ارتفاع", "number", 32)] },
  divider: { type: "divider", label: "جداکننده", variants: [{ value: "default", label: "خط" }], props: [] },
});
for (const kind of ["text", "image", "button", "spacer", "divider"]) {
  Object.assign(BLOCK_TYPES[kind], { component: SiteElementBlock, defaultVariant: BLOCK_TYPES[kind].variants[0].value, toProps: block => ({ ...block.props, kind, variant: block.variant }) });
}

export const BLOCK_TYPE_LIST = Object.values(BLOCK_TYPES);

const PAGE_ALIASES = {
	home: "home",
	homev2: "homev2",
	home_v2: "homev2",
	"home-v2": "homev2",
	about: "about",
	faq: "faq",
	product_groups: "product_groups",
	"product-groups": "product_groups",
};

const PUBLIC_PAGE_LAYOUT_KEYS = [
	"blog", "blog-post", "menu", "item", "cart", "customize", "bom-preview",
	"payment", "payment-callback", "order-success", "order-start", "order-type",
	"order-dine-in", "order-pickup", "order-delivery", "customer-login", "survey",
	"customer-dashboard", "customer-referrals", "customer-collaboration",
	"customer-recurring-orders", "customer-nutrition", "customer-profile",
	"customer-vehicles", "customer-wallet", "customer-addresses", "customer-branches",
	"customer-orders", "customer-order-detail", "customer-delivery",
	"customer-table-reservation", "customer-table-select", "checkout", "payment-fail",
];
PUBLIC_PAGE_LAYOUT_KEYS.forEach((page) => { PAGE_ALIASES[page] = page; });

export function normalizePageBuilderKey(page = "home") {
	const key = String(page || "").trim();
	return /^custom:[a-z0-9][a-z0-9-]{0,79}$/.test(key) ? key : PAGE_ALIASES[key] || "home";
}

const editorialPageBlocks = ["hero", "features", "banner"];
const workflowPageBlocks = ["banner"];
const editorialPageKeys = new Set(["blog", "blog-post", "menu", "item"]);

export const PAGE_BLOCK_CATALOGS = {
	home: ["hero", "categories", "products", "popular", "features", "about", "faq", "banner"],
	homev2: ["healthy_hero", "categories", "products", "popular", "features", "about", "faq", "banner"],
	about: ["hero", "about", "banner"],
	faq: ["hero", "faq", "banner"],
	product_groups: ["hero", "categories", "banner"],
	...Object.fromEntries(PUBLIC_PAGE_LAYOUT_KEYS.map((page) => [
		page,
		editorialPageKeys.has(page) ? editorialPageBlocks : workflowPageBlocks,
	])),
};

export function getPageBlockCatalog(page = "home") {
	return Object.keys(BLOCK_TYPES);
}

export function getPageBlockPalette(page = "home") {
	return getPageBlockCatalog(page)
		.map((type) => getBlockType(type))
		.filter(Boolean);
}

export function isBlockAllowedOnPage(page = "home", type = "") {
	return getPageBlockCatalog(page).includes(String(type || "").trim());
}

export function getBlockType(type) {
	return BLOCK_TYPES[String(type || "").trim()] || null;
}

function clone(value) {
	try {
		return JSON.parse(JSON.stringify(value));
	} catch (_) {
		return value;
	}
}

// Build a fresh block instance with sane defaults from the schema.
export function createBlock(type, overrides = {}) {
	const def = getBlockType(type);
	if (!def) return null;
	const props = {};
	for (const field of def.props || []) {
		props[field.key] = field.default !== undefined ? clone(field.default) : "";
	}
	return {
		id: makeBlockId(type),
		type: def.type,
		variant: def.defaultVariant,
		enabled: true,
		props,
		...overrides,
	};
}

export { bool, num, str };
