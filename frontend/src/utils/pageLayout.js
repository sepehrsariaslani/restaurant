// Page Layout resolver
//
// Turns raw boot data into an ordered array of block instances for a
// specific public page. Stored page layouts win; otherwise we derive a
// sensible fallback from the existing public page data so legacy pages
// keep rendering without migration.

import {
	createBlock,
	getBlockType,
	isBlockAllowedOnPage,
	makeBlockId,
	normalizePageBuilderKey,
} from "@/utils/blockRegistry";
import { resolveBranding, resolveSiteComponents } from "@/utils/siteComponents";

function asArray(value) {
	return Array.isArray(value) ? value : [];
}

function safeNumber(value, fallback = 0) {
	const out = Number(value);
	return Number.isFinite(out) ? out : fallback;
}

function text(value, fallback = "") {
	const out = String(value ?? "").trim();
	return out || fallback;
}

function firstActive(rows = []) {
	return asArray(rows).find((row) => Number(row?.is_active ?? 1) !== 0) || rows[0] || {};
}

function normalizeBlock(raw, index, page = "home") {
	const def = getBlockType(raw && raw.type);
	if (!def || !isBlockAllowedOnPage(page, def.type)) return null;
	return {
		id: String(raw.id || makeBlockId(def.type)),
		type: def.type,
		variant: String(raw.variant || def.defaultVariant).trim() || def.defaultVariant,
		enabled: raw.enabled === undefined ? true : Boolean(raw.enabled),
		order: Number.isFinite(Number(raw.order)) ? Number(raw.order) : index,
		props: raw.props && typeof raw.props === "object" ? { ...raw.props } : {},
	};
}

export function hasStoredPageLayout(boot = {}, page = "home") {
	const pageKey = normalizePageBuilderKey(page);
	const stored = boot?.page_layout?.[pageKey];
	return Array.isArray(stored?.blocks) && stored.blocks.length > 0;
}

export function resolvePageLayout(boot = {}, page = "home") {
	const pageKey = normalizePageBuilderKey(page);
	const stored = boot?.page_layout?.[pageKey];
	const storedBlocks = asArray(stored?.blocks);

	if (storedBlocks.length) {
		return storedBlocks
			.map((block, index) => normalizeBlock(block, index, pageKey))
			.filter(Boolean)
			.filter((block) => block.enabled)
			.sort((a, b) => a.order - b.order);
	}

	return buildLegacyPageLayout(boot, pageKey);
}

export function resolveHomeLayout(boot = {}) {
	return resolvePageLayout(boot, "home");
}

export function buildLegacyPageLayout(boot = {}, page = "home") {
	const pageKey = normalizePageBuilderKey(page);
	const builders = {
		home: buildLegacyHomeLayout,
		homev2: buildLegacyHomeV2Layout,
		about: buildLegacyAboutLayout,
		faq: buildLegacyFaqLayout,
		product_groups: buildLegacyProductGroupsLayout,
	};
	const build = builders[pageKey] || buildLegacyHomeLayout;
	return build(boot).map((block, index) => ({ ...block, order: index }));
}

function buildLegacyHomeV2Layout(boot = {}) {
	const blocks = [
		createBlock("healthy_hero", {
			variant: "club",
			props: {
				eyebrow: "غذای سالم، با حال خوب",
				title: "هر روز، یک انتخاب",
				highlight: "خوش‌طعم‌تر از همیشه",
				description: "طعم‌های تازه و ترکیب‌های متعادل، برای وقتی که می‌خواهی هم خوشمزه بخوری هم انتخاب خوبی داشته باشی.",
				ctaLabel: "دیدن منوی سالم",
				ctaHref: "/menu",
			},
		}),
		createBlock("categories", {
			variant: "grid",
			props: {
				eyebrow: "منوی تازه و متنوع",
				title: "از کجا شروع کنیم؟",
			},
		}),
		createBlock("products", {
			variant: "grid",
			props: {
				eyebrow: "پیشنهادهای خوش‌طعم",
				title: "انتخاب‌های محبوب",
				source: "featured",
				limit: 6,
			},
		}),
		createBlock("features", {
			variant: "cards",
			props: {
				eyebrow: "ویدرخت، با نگاه سالم‌تر",
				title: "ساده انتخاب کن، خوب بخور",
				items: [
					{ icon: "leaf", title: "ترکیب‌های تازه", description: "مواد و مزه‌ها را با دقت کنار هم می‌چینیم." },
					{ icon: "sliders", title: "انتخاب‌های متنوع", description: "برای سلیقه‌ها و حال‌وهوای مختلف." },
					{ icon: "heart", title: "غذای سالم و خوش‌طعم", description: "تعادل خوب، بدون کنار گذاشتن لذت غذا." },
				],
			},
		}),
		createBlock("banner", {
			variant: "solid",
			props: {
				title: "برای انتخاب بعدی آماده‌ای؟",
				description: "منوی روز را ببین و ترکیب مورد علاقه‌ات را پیدا کن.",
				ctaLabel: "رفتن به منو",
				ctaHref: "/menu",
			},
		}),
	];

	return blocks.filter(Boolean);
}

function buildLegacyHomeLayout(boot = {}) {
	const branding = resolveBranding(boot);
	const components = resolveSiteComponents(boot);
	const web = boot?.web_settings || {};
	const blocks = [];

	const heroVariant = components.hero_section_variant;
	if (heroVariant && heroVariant !== "off") {
		const variantMap = {
			cover: "cover",
			fullscreen: "fullscreen",
			banner: "banner",
			slider: "slider",
			foodbar: "foodbar",
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
						branding.hero_section_cta || branding.primary_cta_label || "مشاهده منو",
					ctaHref: "/menu",
					secondaryLabel: "",
					secondaryHref: "",
					slidesSource: heroVariant === "slider" ? "hero_slides" : "featured",
				},
			}),
		);
	}

	blocks.push(
		createBlock("categories", {
			variant: components.category_rail_variant === "image" ? "circles" : "grid",
		}),
	);

	const highlightEnabled = Number(web.restaurant_menu_highlight_enabled ?? 1) !== 0;
	if (highlightEnabled) {
		blocks.push(
			createBlock("products", {
				variant: "grid",
				props: {
					title:
						text(web.restaurant_menu_highlight_title, "محبوب‌ترین انتخاب‌ها"),
					source: "featured",
					limit: safeNumber(web.restaurant_menu_highlight_featured_limit, 8) || 8,
					cardVariant: components.card_variant || "classic",
				},
			}),
		);
	}

	const hasPopular =
		asArray(boot.featured_items).length ||
		(boot.menu_highlight && asArray(boot.menu_highlight.items).length);
	if (hasPopular) {
		blocks.push(createBlock("popular", { variant: "showcase" }));
	}

	blocks.push(createBlock("features", { variant: "cards" }));

	if (asArray(boot.about_us_sections).length) {
		blocks.push(createBlock("about", { variant: "cards" }));
	}

	if (asArray(boot.faq_items).length) {
		blocks.push(createBlock("faq", { variant: "accordion" }));
	}

	return blocks;
}

function buildLegacyAboutLayout(boot = {}) {
	const branding = resolveBranding(boot);
	const sections = asArray(boot.about_us_sections).filter((row) => Number(row?.is_active ?? 1) !== 0);
	const heroSection = firstActive(
		sections.filter((row) => {
			const type = text(row?.section_type).toLowerCase();
			return type === "hero" || type === "story" || type === "history";
		}),
	);

	const title = text(heroSection?.title, text(branding.name, "درباره ما"));
	const description =
		text(heroSection?.subtitle) ||
		text(heroSection?.body_text).slice(0, 180) ||
		"داستان مجموعه، ارزش‌ها و تجربه‌ای که برای مشتری می‌سازیم.";

	const blocks = [
		createBlock("hero", {
			variant: "minimal",
			props: {
				eyebrow: "درباره ما",
				title,
				description,
				ctaLabel: "مشاهده منو",
				ctaHref: "/menu",
				secondaryLabel: "سوالات متداول",
				secondaryHref: "/faq",
			},
		}),
	];

	if (sections.length) {
		blocks.push(
			createBlock("about", {
				variant: "cards",
				props: {
					eyebrow: "درباره ما",
					title: "داستان رستوران ما",
					subtitle: text(heroSection?.subtitle),
					moreLabel: "مشاهده کامل",
					moreHref: "/about-us",
					limit: 4,
				},
			}),
		);
	}

	blocks.push(
		createBlock("banner", {
			variant: "solid",
			props: {
				title: "برای تجربه کامل، منو را ببینید",
				description: "از همین‌جا می‌توانید وارد منو شوید و سفارش خود را ثبت کنید.",
				ctaLabel: "مشاهده منو",
				ctaHref: "/menu",
			},
		}),
	);

	return blocks;
}

function buildLegacyFaqLayout(boot = {}) {
	const branding = resolveBranding(boot);
	const faqCount = asArray(boot.faq_items).filter((row) => Number(row?.is_active ?? 1) !== 0).length;

	const blocks = [
		createBlock("hero", {
			variant: "minimal",
			props: {
				eyebrow: "سوالات متداول",
				title: "هر سوالی درباره سفارش، آماده پاسخ هستیم",
				description:
					faqCount > 0
						? `${faqCount.toLocaleString("fa-IR")} سوال ثبت شده برای پاسخ سریع‌تر به مشتری‌ها.`
						: `سوالات پرتکرار ${text(branding.name, "رستوران")} را اینجا جمع‌آوری کرده‌ایم.`,
				ctaLabel: "شروع سفارش",
				ctaHref: "/menu",
			},
		}),
		createBlock("faq", {
			variant: "accordion",
			props: {
				eyebrow: "سوالات متداول",
				title: "پاسخ پرسش‌های پرتکرار",
				moreLabel: "مشاهده همه سوالات",
				moreHref: "/faq",
				limit: 12,
			},
		}),
		createBlock("banner", {
			variant: "solid",
			props: {
				title: "هنوز سوالی باقی مانده؟",
				description: "منو را ببینید یا از تیم فروش برای ثبت سفارش کمک بگیرید.",
				ctaLabel: "مشاهده منو",
				ctaHref: "/menu",
			},
		}),
	];

	return blocks;
}

function buildLegacyProductGroupsLayout(boot = {}) {
	const branding = resolveBranding(boot);
	const components = resolveSiteComponents(boot);

	return [
		createBlock("hero", {
			variant: "minimal",
			props: {
				eyebrow: "منوی دسته‌بندی‌شده",
				title: text(branding.hero_title, "گروه محصولات را انتخاب کنید"),
				description:
					text(branding.hero_subtitle) ||
					"مشتری روی هر گروه بزند و مستقیم وارد منوی همان گروه شود.",
				ctaLabel: "مشاهده همه منو",
				ctaHref: "/menu",
			},
		}),
		createBlock("categories", {
			variant: components.category_rail_variant === "image" ? "circles" : "grid",
			props: {
				eyebrow: "گروه‌های منو",
				title: "از کدام گروه شروع می‌کنید؟",
				subtitle: "نمایش دسته‌ها و زیرگروه‌ها بر اساس تنظیمات فعلی منو",
				limit: 0,
			},
		}),
		createBlock("banner", {
			variant: "solid",
			props: {
				title: "همه آیتم‌ها را یکجا ببینید",
				description: "اگر دسته‌بندی نمی‌خواهید، مستقیم وارد منوی کامل شوید.",
				ctaLabel: "رفتن به منو",
				ctaHref: "/menu",
			},
		}),
	];
}
