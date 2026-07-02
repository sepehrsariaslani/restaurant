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

import { markRaw } from "vue";

// Lazy component imports keep the public bundle small.
const HeroBlock = () => import("@/components/blocks/HeroBlock.vue");
const AboutBlock = () => import("@/components/blocks/AboutBlock.vue");
const ProductsBlock = () => import("@/components/blocks/ProductsBlock.vue");
const CategoriesBlock = () => import("@/components/blocks/CategoriesBlock.vue");
const FeaturesBlock = () => import("@/components/blocks/FeaturesBlock.vue");
const FaqBlock = () => import("@/components/blocks/FaqBlock.vue");
const BannerBlock = () => import("@/components/blocks/BannerBlock.vue");
const PopularBlock = () => import("@/components/blocks/PopularBlock.vue");

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
			{ value: "cover", label: "\u06a9\u0627\u0648\u0631", desc: "\u0639\u06a9\u0633 \u0628\u0632\u0631\u06af\u060c \u0645\u062a\u0646\u060c \u062f\u06a9\u0645\u0647 \u0648 \u0645\u0632\u06cc\u062a\u200c\u0647\u0627" },
			{ value: "split", label: "\u062f\u0648\u0633\u062a\u0648\u0646\u0647", desc: "\u0645\u062a\u0646 \u062f\u0631 \u06cc\u06a9 \u0633\u0645\u062a\u060c \u062a\u0635\u0648\u06cc\u0631 \u062f\u0631 \u0633\u0645\u062a \u062f\u06cc\u06af\u0631" },
			{ value: "minimal", label: "\u0645\u06cc\u0646\u06cc\u0645\u0627\u0644", desc: "\u0641\u0642\u0637 \u0639\u0646\u0648\u0627\u0646\u060c \u062a\u0648\u0636\u06cc\u062d \u06a9\u0648\u062a\u0627\u0647 \u0648 \u062f\u06a9\u0645\u0647" },
			{ value: "slider", label: "\u0627\u0633\u0644\u0627\u06cc\u062f\u0631", desc: "\u0686\u0646\u062f \u0627\u0633\u0644\u0627\u06cc\u062f \u062a\u0635\u0648\u06cc\u0631\u06cc \u0628\u0627 CTA \u0645\u0633\u062a\u0642\u0644" },
		],
		defaultVariant: "cover",
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
				items = boot.best_seller_items || boot.featured_items || [];
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
			const highlight = (boot.menu_highlight && boot.menu_highlight.items) || [];
			let items = [];
			if (source === "featured") {
				items = boot.featured_items || [];
			} else {
				items = boot.best_seller_items || highlight || boot.featured_items || [];
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
};

export const BLOCK_TYPE_LIST = Object.values(BLOCK_TYPES);

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
