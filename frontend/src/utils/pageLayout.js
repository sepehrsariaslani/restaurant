// Page Layout resolver
//
// Turns raw boot data into an ordered array of block instances that the
// HomePageRenderer can iterate over.
//
// Resolution order:
//   1. If boot.page_layout.home.blocks exists -> use it (new system).
//   2. Otherwise derive a sensible default layout from the legacy flat
//      web_settings (hero_section_variant, footer_variant, ...), so
//      existing restaurants keep working with zero migration.

import { getBlockType, createBlock, makeBlockId } from "@/utils/blockRegistry";
import { resolveBranding, resolveSiteComponents } from "@/utils/siteComponents";

function asArray(value) {
	return Array.isArray(value) ? value : [];
}

// Normalize a stored block so it always has the fields the renderer needs.
function normalizeBlock(raw, index) {
	const def = getBlockType(raw && raw.type);
	if (!def) return null;
	return {
		id: String(raw.id || makeBlockId(def.type)),
		type: def.type,
		variant: String(raw.variant || def.defaultVariant).trim() || def.defaultVariant,
		enabled: raw.enabled === undefined ? true : Boolean(raw.enabled),
		order: Number.isFinite(Number(raw.order)) ? Number(raw.order) : index,
		props: raw.props && typeof raw.props === "object" ? { ...raw.props } : {},
	};
}

export function resolveHomeLayout(boot = {}) {
	const stored = boot && boot.page_layout && boot.page_layout.home;
	const storedBlocks = stored && asArray(stored.blocks);

	if (storedBlocks && storedBlocks.length) {
		return storedBlocks
			.map((block, index) => normalizeBlock(block, index))
			.filter(Boolean)
			.filter((block) => block.enabled)
			.sort((a, b) => a.order - b.order);
	}

	return buildLegacyLayout(boot);
}

// Derive a default block layout from the old flat settings.
export function buildLegacyLayout(boot = {}) {
	const branding = resolveBranding(boot);
	const components = resolveSiteComponents(boot);
	const web = (boot && boot.web_settings) || {};
	const blocks = [];

	// Hero (map legacy hero_section_variant to a block variant).
	const heroVariant = components.hero_section_variant;
	if (heroVariant && heroVariant !== "off") {
		const variantMap = {
			cover: "cover",
			fullscreen: "cover",
			banner: "minimal",
			slider: "slider",
			foodbar: "split",
		};
		blocks.push(
			createBlock("hero", {
				variant: variantMap[heroVariant] || "cover",
				props: {
					eyebrow: "",
					title: branding.hero_section_title || branding.hero_title,
					description: branding.hero_section_description || branding.hero_subtitle,
					image: branding.hero_image,
					ctaLabel:
						branding.hero_section_cta || branding.primary_cta_label || "\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648",
					ctaHref: "/menu",
					secondaryLabel: "",
					secondaryHref: "",
					slidesSource: heroVariant === "slider" ? "hero_slides" : "featured",
				},
			}),
		);
	}

	// Categories
	blocks.push(
		createBlock("categories", {
			variant: components.category_rail_variant === "image" ? "circles" : "grid",
		}),
	);

	// Featured products (respect legacy highlight toggle when present).
	const highlightEnabled = Number(web.restaurant_menu_highlight_enabled ?? 1) !== 0;
	if (highlightEnabled) {
		blocks.push(
			createBlock("products", {
				variant: "grid",
				props: {
					title:
						String(web.restaurant_menu_highlight_title || "\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646 \u0627\u0646\u062a\u062e\u0627\u0628\u200c\u0647\u0627").trim() ||
						"\u0645\u062d\u0628\u0648\u0628\u200c\u062a\u0631\u06cc\u0646 \u0627\u0646\u062a\u062e\u0627\u0628\u200c\u0647\u0627",
					source: "featured",
					limit: Number(web.restaurant_menu_highlight_featured_limit || 8) || 8,
					cardVariant: components.card_variant || "classic",
				},
			}),
		);
	}

	// Features
	blocks.push(createBlock("features", { variant: "cards" }));

	// About
	if (asArray(boot.about_us_sections).length) {
		blocks.push(createBlock("about", { variant: "cards" }));
	}

	// FAQ
	if (asArray(boot.faq_items).length) {
		blocks.push(createBlock("faq", { variant: "accordion" }));
	}

	return blocks.map((block, index) => ({ ...block, order: index }));
}
