export const PRODUCT_DETAIL_TABS = [
	{ value: "overview", label: "کارت محصول" },
	{ value: "settings", label: "فروش و نمایش" },
	{ value: "formula", label: "فرمول و رسپی" },
	{ value: "variants", label: "مدل‌ها" },
	{ value: "builder", label: "سفارشی‌سازی" },
	{ value: "reports", label: "گزارش فروش" },
	{ value: "changes", label: "تغییرات" },
];

export const KITCHEN_PRINT_MODE_OPTIONS = [
	{ value: "parent_only", label: "فقط محصول اصلی" },
	{ value: "parent_with_components", label: "محصول اصلی + انتخاب‌های مشتری" },
	{ value: "components_grouped_by_step", label: "انتخاب‌ها به تفکیک مرحله" },
];

export const STOCK_CONSUMPTION_MODE_OPTIONS = [
	{ value: "no_stock_deduction", label: "بدون کسر موجودی" },
	{ value: "consume_selected_components", label: "کسر اقلام انتخاب‌شده" },
	{ value: "create_dynamic_bom", label: "پیش‌نمایش BOM پویا" },
	{
		value: "use_sales_order_exploded_components",
		label: "استفاده از اقلام بازشده سفارش فروش",
	},
	{ value: "manual_kitchen_consumption", label: "مصرف دستی توسط آشپزخانه" },
];

const KITCHEN_PRINT_MODE_ALIAS_MAP = {
	full_selections: "parent_with_components",
	"full detail": "parent_with_components",
	"step only": "components_grouped_by_step",
	"option only": "parent_with_components",
};

const STOCK_CONSUMPTION_MODE_ALIAS_MAP = {
	from_builder: "consume_selected_components",
	"per option": "consume_selected_components",
	"per step": "create_dynamic_bom",
	fixed: "no_stock_deduction",
};

function normalizeSelectValue(value, options, aliasMap, fallback = "") {
	const rawValue = String(value || "").trim();
	if (!rawValue) return fallback;

	const canonical = rawValue.toLowerCase();
	if (aliasMap[canonical]) {
		return aliasMap[canonical];
	}

	return options.some((option) => option.value === rawValue) ? rawValue : fallback;
}

export function normalizeKitchenPrintMode(value) {
	return normalizeSelectValue(
		value,
		KITCHEN_PRINT_MODE_OPTIONS,
		KITCHEN_PRINT_MODE_ALIAS_MAP,
		"parent_with_components",
	);
}

export function normalizeStockConsumptionMode(value) {
	return normalizeSelectValue(
		value,
		STOCK_CONSUMPTION_MODE_OPTIONS,
		STOCK_CONSUMPTION_MODE_ALIAS_MAP,
		"consume_selected_components",
	);
}

export function createInitialProductSettingsForm() {
	return {
		item_code: "",
		item_name: "",
		item_group: "",
		stock_uom: "",
		description: "",
		restaurant_slug: "",
		restaurant_short_desc: "",
		restaurant_long_desc: "",
		restaurant_category: "",
		restaurant_subcategory: "",
		restaurant_branch: "",
		image: "",
		website_image: "",
		restaurant_prep_time_mins: 0,
		restaurant_sort_order: 0,
		restaurant_auto_add_qty: 0,
		restaurant_item_tag_table: [],
		restaurant_nutrition_kcal: 0,
		restaurant_nutrition_protein_g: 0,
		restaurant_nutrition_carb_g: 0,
		restaurant_nutrition_sugar_g: 0,
		restaurant_nutrition_fat_g: 0,
		show_in_print: false,
		restaurant_enabled: false,
		restaurant_is_featured: false,
		restaurant_is_best_seller: false,
		restaurant_requires_bom: false,
		restaurant_auto_add_to_order: false,
		restaurant_coming_soon: false,
		restaurant_out_of_stock: false,
		out_of_stock_until: "",
		restaurant_restock_date: "",
		disabled: false,
		restaurant_is_customizable: false,
		restaurant_customize_button_label: "سفارشی‌سازی",
		restaurant_custom_product_type: "",
		restaurant_builder_template: "",
		restaurant_builder_active: true,
		restaurant_allow_direct_add: false,
		restaurant_show_nutrition_summary: false,
		restaurant_show_allergen_warnings: false,
		restaurant_kitchen_print_mode: "",
		restaurant_stock_consumption_mode: "",
		restaurant_kitchen_ticket: true,
	};
}

export function hydrateProductSettingsForm(form, payload = {}, tagOptions = []) {
	const item = payload?.item || {};
	form.item_code = item.item_code || "";
	form.item_name = item.item_name || "";
	form.item_group = item.item_group || "";
	form.stock_uom = item.stock_uom || "";
	form.description = item.description || "";
	form.restaurant_slug = item.restaurant_slug || "";
	form.restaurant_short_desc = item.short_description || "";
	form.restaurant_long_desc = item.long_description || "";
	form.restaurant_category = item.restaurant_category || "";
	form.restaurant_subcategory = item.restaurant_subcategory || "";
	form.restaurant_branch = item.restaurant_branch || "";
	form.image = item.image || "";
	form.website_image = item.website_image || "";
	form.restaurant_prep_time_mins = Number(item.restaurant_prep_time_mins || 0);
	form.restaurant_sort_order = Number(item.restaurant_sort_order || 0);
	form.restaurant_auto_add_qty = Number(item.restaurant_auto_add_qty || 0);
	form.restaurant_item_tag_table = Array.isArray(item.restaurant_item_tag_table)
		? item.restaurant_item_tag_table
		: splitTagTitles(item.restaurant_item_tags || item.tags).map((tag) => ({
				tag,
				_tag_title: tag,
			}));

	if (form.restaurant_item_tag_table.length) {
		for (const link of form.restaurant_item_tag_table) {
			if (link.tag && !link._tag_title) {
				const tagOption = tagOptions.find((option) => option.value === link.tag);
				link._tag_title = tagOption ? tagOption.label : link.tag;
			}
		}
	}

	form.restaurant_nutrition_kcal = Number(
		item.restaurant_nutrition_kcal || item.nutrition?.kcal || 0,
	);
	form.restaurant_nutrition_protein_g = Number(
		item.restaurant_nutrition_protein_g || item.nutrition?.protein_g || 0,
	);
	form.restaurant_nutrition_carb_g = Number(
		item.restaurant_nutrition_carb_g || item.nutrition?.carb_g || 0,
	);
	form.restaurant_nutrition_sugar_g = Number(
		item.restaurant_nutrition_sugar_g || item.nutrition?.sugar_g || 0,
	);
	form.restaurant_nutrition_fat_g = Number(
		item.restaurant_nutrition_fat_g || item.nutrition?.fat_g || 0,
	);
	form.show_in_print = Number(item.show_in_print ?? item.show_in_website ?? 0) === 1;
	form.restaurant_enabled = Number(item.restaurant_enabled || 0) === 1;
	form.restaurant_is_featured = Number(item.restaurant_is_featured || 0) === 1;
	form.restaurant_is_best_seller = Number(item.restaurant_is_best_seller || 0) === 1;
	form.restaurant_requires_bom = Number(item.restaurant_requires_bom || 0) === 1;
	form.restaurant_auto_add_to_order = Number(item.restaurant_auto_add_to_order || 0) === 1;
	form.restaurant_coming_soon = Number(item.restaurant_coming_soon || 0) === 1;
	form.restaurant_out_of_stock = Number(item.restaurant_out_of_stock || 0) === 1;
	form.out_of_stock_until = item.out_of_stock_until || item.restaurant_out_of_stock_until || "";
	form.restaurant_restock_date = item.restock_date || item.restaurant_restock_date || "";
	form.disabled = Number(item.disabled || 0) === 1;
	form.restaurant_is_customizable = Number(item.restaurant_is_customizable || 0) === 1;
	form.restaurant_customize_button_label =
		item.restaurant_customize_button_label || "سفارشی‌سازی";
	form.restaurant_custom_product_type = item.restaurant_custom_product_type || "";
	form.restaurant_builder_template = item.restaurant_builder_template || "";
	form.restaurant_builder_active = Number(item.restaurant_builder_active ?? 1) === 1;
	form.restaurant_allow_direct_add = Number(item.restaurant_allow_direct_add || 0) === 1;
	form.restaurant_show_nutrition_summary =
		Number(item.restaurant_show_nutrition_summary || 0) === 1;
	form.restaurant_show_allergen_warnings =
		Number(item.restaurant_show_allergen_warnings || 0) === 1;
	form.restaurant_kitchen_print_mode = normalizeKitchenPrintMode(
		item.restaurant_kitchen_print_mode,
	);
	form.restaurant_stock_consumption_mode = normalizeStockConsumptionMode(
		item.restaurant_stock_consumption_mode,
	);
	form.restaurant_kitchen_ticket = Number(item.kitchen_ticket ?? 1) === 1;
}

export function serializeProductSettingsState(form, builderConfig = null) {
	return JSON.stringify({
		item_code: String(form.item_code || "").trim(),
		item_name: String(form.item_name || "").trim(),
		item_group: String(form.item_group || "").trim(),
		stock_uom: String(form.stock_uom || "").trim(),
		description: String(form.description || "").trim(),
		restaurant_slug: String(form.restaurant_slug || "").trim(),
		restaurant_short_desc: String(form.restaurant_short_desc || "").trim(),
		restaurant_long_desc: String(form.restaurant_long_desc || "").trim(),
		restaurant_category: String(form.restaurant_category || "").trim(),
		restaurant_subcategory: String(form.restaurant_subcategory || "").trim(),
		restaurant_branch: String(form.restaurant_branch || "").trim(),
		image: String(form.image || "").trim(),
		website_image: String(form.website_image || "").trim(),
		restaurant_prep_time_mins: Number(form.restaurant_prep_time_mins || 0),
		restaurant_sort_order: Number(form.restaurant_sort_order || 0),
		restaurant_auto_add_qty: Number(form.restaurant_auto_add_qty || 0),
		restaurant_item_tag_table: (form.restaurant_item_tag_table || []).map((link) => ({
			tag: link.tag,
			_tag_title: link._tag_title || "",
		})),
		restaurant_item_tags: (form.restaurant_item_tag_table || [])
			.map((link) => link._tag_title || link.tag_title || link.tag || "")
			.map((tag) => String(tag || "").trim())
			.filter(Boolean)
			.join(", "),
		restaurant_nutrition_kcal: Number(form.restaurant_nutrition_kcal || 0),
		restaurant_nutrition_protein_g: Number(form.restaurant_nutrition_protein_g || 0),
		restaurant_nutrition_carb_g: Number(form.restaurant_nutrition_carb_g || 0),
		restaurant_nutrition_sugar_g: Number(form.restaurant_nutrition_sugar_g || 0),
		restaurant_nutrition_fat_g: Number(form.restaurant_nutrition_fat_g || 0),
		show_in_print: form.show_in_print ? 1 : 0,
		restaurant_enabled: form.restaurant_enabled ? 1 : 0,
		restaurant_is_featured: form.restaurant_is_featured ? 1 : 0,
		restaurant_is_best_seller: form.restaurant_is_best_seller ? 1 : 0,
		restaurant_requires_bom: form.restaurant_requires_bom ? 1 : 0,
		restaurant_auto_add_to_order: form.restaurant_auto_add_to_order ? 1 : 0,
		restaurant_coming_soon: form.restaurant_coming_soon ? 1 : 0,
		restaurant_out_of_stock: form.restaurant_out_of_stock ? 1 : 0,
		restaurant_out_of_stock_until: String(form.out_of_stock_until || "").trim(),
		restaurant_restock_date: String(form.restaurant_restock_date || "").trim(),
		disabled: form.disabled ? 1 : 0,
		restaurant_is_customizable: form.restaurant_is_customizable ? 1 : 0,
		restaurant_customize_button_label: String(
			form.restaurant_customize_button_label || "",
		).trim(),
		restaurant_custom_product_type: String(form.restaurant_custom_product_type || "").trim(),
		restaurant_builder_template: String(form.restaurant_builder_template || "").trim(),
		restaurant_builder_active: form.restaurant_builder_active ? 1 : 0,
		restaurant_allow_direct_add: form.restaurant_allow_direct_add ? 1 : 0,
		restaurant_show_nutrition_summary: form.restaurant_show_nutrition_summary ? 1 : 0,
		restaurant_show_allergen_warnings: form.restaurant_show_allergen_warnings ? 1 : 0,
		restaurant_kitchen_print_mode: normalizeKitchenPrintMode(
			form.restaurant_kitchen_print_mode,
		),
		restaurant_stock_consumption_mode: normalizeStockConsumptionMode(
			form.restaurant_stock_consumption_mode,
		),
		restaurant_kitchen_ticket: form.restaurant_kitchen_ticket ? 1 : 0,
		restaurant_kitchen_ticket: form.restaurant_kitchen_ticket ? 1 : 0,
		product_builder_config: clonePlainObject(builderConfig),
	});
}

export function buildProductSettingsPayload({ itemName = "", form, builderConfig = null } = {}) {
	const parsed = JSON.parse(serializeProductSettingsState(form, builderConfig));
	const keepCustomizationEnabled = Number(parsed.restaurant_is_customizable || 0) === 1;
	const hasProductBuilderConfig = Boolean(builderConfig && keepCustomizationEnabled);
	const shouldKeepBuilderEnabled = Boolean(
		keepCustomizationEnabled || hasProductBuilderConfig,
	);
	const shouldForceBuilderFlow =
		shouldKeepBuilderEnabled && Number(parsed.restaurant_builder_active || 0) === 1;

	return {
		name: itemName,
		...parsed,
		restaurant_is_customizable: shouldKeepBuilderEnabled ? 1 : 0,
		restaurant_builder_active: shouldKeepBuilderEnabled
			? Number(parsed.restaurant_builder_active || 0)
			: 0,
		restaurant_allow_direct_add: shouldForceBuilderFlow
			? 0
			: Number(parsed.restaurant_allow_direct_add || 0),
		product_builder_config: clonePlainObject(builderConfig),
		show_in_website: Number(parsed.show_in_print || 0) ? 1 : 0,
	};
}

export function clonePlainObject(value = null) {
	if (!value || typeof value !== "object") return null;
	if (typeof structuredClone === "function") {
		try {
			return structuredClone(value);
		} catch (error) {
			// Fall back to JSON cloning for plain API payloads.
		}
	}
	return JSON.parse(JSON.stringify(value));
}

function splitTagTitles(rawValue) {
	if (!rawValue) return [];
	const rows = Array.isArray(rawValue) ? rawValue : String(rawValue).replace(/\n/g, ",").split(",");
	return rows
		.map((row) => {
			if (row && typeof row === "object") {
				return row._tag_title || row.tag_title || row.title || row.tag || "";
			}
			return row;
		})
		.map((tag) => String(tag || "").trim())
		.filter(Boolean);
}

export function createEmptyBuilderStep(index) {
	return {
		step_title: `مرحله ${index + 1}`,
		step_key: `step-${Date.now()}-${index}`,
		step_description: "",
		sort_order: index,
		selection_mode: "multiple",
		min_select: 1,
		max_select: 1,
		is_required: true,
		show_step_price: true,
		step_icon: "",
		options: [],
		conditional_logic: {},
	};
}

export function normalizeVariantAttributesDraft(attributes = []) {
	const rows = [];
	for (const row of attributes || []) {
		const name = String(row?.name || "").trim();
		if (!name) continue;

		const values = Array.isArray(row?.values)
			? row.values.map((valueRow) => ({
					value: String(valueRow?.value || "").trim(),
					abbr: String(valueRow?.abbr || "").trim(),
					sort_order: Number(valueRow?.sort_order || 0),
					is_default: Number(valueRow?.is_default || 0) ? 1 : 0,
				}))
			: [];

		rows.push({
			name,
			label: String(row?.label || name).trim(),
			selected_on_template: Number(row?.selected_on_template || 0) ? 1 : 0,
			show_in_website:
				row?.show_in_website === undefined ? 1 : Number(row?.show_in_website || 0),
			selection_only: Number(row?.selection_only || 0),
			disabled: Number(row?.disabled || 0),
			values,
		});
	}
	return rows;
}

export function resolveTemplateAttributeSelection(attributes = [], templateAttributes = []) {
	const availableNames = new Set(attributes.map((row) => row.name));
	const fromPayload = Array.isArray(templateAttributes)
		? templateAttributes
				.map((value) => String(value || "").trim())
				.filter((value) => value && availableNames.has(value))
		: [];
	const fromRows = attributes
		.filter((row) => Number(row?.selected_on_template || 0) === 1)
		.map((row) => row.name);

	return Array.from(new Set((fromPayload.length ? fromPayload : fromRows).filter(Boolean)));
}

export function normalizeDateRaw(raw) {
	let value = String(raw || "").trim();
	if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(value)) {
		value = value.replace(" ", "T");
	}
	if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{4,}$/.test(value)) {
		value = value.replace(/^(.+\.\d{3})\d+$/, "$1");
	}
	return value;
}

export function formatPersianDate(value, withTime = false) {
	const raw = String(value || "").trim();
	if (!raw) return "-";
	const normalizedRaw = normalizeDateRaw(raw);
	try {
		const parsedDate = new Date(normalizedRaw);
		if (Number.isNaN(parsedDate.getTime())) return raw;
		return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
			year: "numeric",
			month: "long",
			day: "numeric",
			...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
		}).format(parsedDate);
	} catch (dateErr) {
		return raw;
	}
}

export function localizeAxisLabel(value) {
	const raw = String(value || "").trim();
	if (!raw) return raw;
	if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return formatPersianDate(raw, false);
	if (/^\d{1,2}:\d{2}/.test(raw)) return raw;
	if (/^\d+(\.\d+)?$/.test(raw)) return Number(raw).toLocaleString("fa-IR");
	return localizeText(raw);
}

const REPORT_REGEX_REPLACEMENTS = [
	[/\bCompared to previous window\b/gi, "نسبت به بازه قبلی"],
	[/\bProduct sales\b/gi, "فروش محصول"],
	[/\bSold Quantity\b/gi, "مقدار فروش"],
	[/\bUnique Customers\b/gi, "مشتریان یکتا"],
	[/\bAverage Order Value\b/gi, "میانگین مبلغ سفارش"],
	[/\bSales Contribution\b/gi, "سهم از فروش"],
	[/\bDaily Sales\b/gi, "فروش روزانه"],
	[/\bDaily Quantity\b/gi, "تعداد روزانه"],
	[/\bHourly Sales Trend\b/gi, "روند فروش ساعتی"],
	[/\bRecent Orders\b/gi, "سفارش‌های اخیر"],
	[/\bTop Customers\b/gi, "برترین مشتریان"],
	[/\bOrder Code\b/gi, "کد سفارش"],
	[/\bCustomer Name\b/gi, "نام مشتری"],
	[/\bPrice List Rate\b/gi, "نرخ لیست قیمت"],
	[/\bLine Total\b/gi, "جمع ردیف"],
	[/\bIn window\b/gi, "در این بازه"],
	[/\bWith\b/gi, "با"],
	[/\bSnapp Guest\b/gi, "مهمان اسنپ"],
	[/\bdine_in\b/gi, "سالن"],
];

const REPORT_PHRASE_MAP = {
	"price history": "تاریخچه قیمت",
	"sales summary": "خلاصه فروش",
	"sales trend": "روند فروش",
	"sales hourly": "فروش ساعتی",
	"top products": "محصولات پرفروش",
	"product mix": "ترکیب محصولات",
	"order status": "وضعیت سفارش",
	"channel split": "تفکیک کانال فروش",
	"cashier performance": "عملکرد صندوقدار",
	cancellations: "لغو سفارش‌ها",
	"modifier usage": "استفاده از افزودنی‌ها",
	"average ticket": "میانگین سبد خرید",
	"line total": "جمع ردیف",
	"order code": "کد سفارش",
	"customer name": "نام مشتری",
	"price list rate": "نرخ لیست قیمت",
	"daily sales": "فروش روزانه",
	"daily quantity": "تعداد روزانه",
	"hourly sales trend": "روند فروش ساعتی",
	"recent orders": "سفارش‌های اخیر",
	"top customers": "برترین مشتریان",
	"product sales": "فروش محصول",
	"sold quantity": "مقدار فروش",
	"unique customers": "مشتریان یکتا",
	"average order value": "میانگین مبلغ سفارش",
	"sales contribution": "سهم از فروش",
	"compared to previous window": "نسبت به بازه قبلی",
	"valid from": "تاریخ اعتبار",
	"effective at": "زمان اثرگذاری",
	"created at": "زمان ایجاد",
	"updated at": "زمان بروزرسانی",
	"price list": "لیست قیمت",
	amount: "مبلغ",
	sales: "فروش",
	revenue: "درآمد",
	total: "جمع کل",
	orders: "تعداد سفارش",
	order: "سفارش",
	customer: "مشتری",
	customers: "مشتریان",
	name: "نام",
	product: "محصول",
	products: "محصولات",
	item: "آیتم",
	items: "آیتم‌ها",
	category: "دسته",
	subcategory: "زیردسته",
	date: "تاریخ",
	hour: "ساعت",
	status: "وضعیت",
	channel: "کانال",
	code: "کد",
	count: "تعداد",
	value: "مقدار",
	price: "قیمت",
	rate: "نرخ",
	qty: "تعداد",
	quantity: "تعداد",
	currency: "ارز",
	uom: "واحد",
	modified: "آخرین بروزرسانی",
	cost: "هزینه",
	profit: "سود",
	margin: "حاشیه سود",
	discount: "تخفیف",
	tax: "مالیات",
	tip: "انعام",
	service: "حق سرویس",
	wallet: "کیف پول",
	pending: "در انتظار",
	confirmed: "تایید شده",
	preparing: "در حال آماده‌سازی",
	ready: "آماده تحویل",
	delivered: "تحویل شده",
	cancelled: "لغو شده",
};

export function localizeText(value) {
	const raw = String(value || "").trim();
	if (!raw) return "";

	if (/^peak day for this item:/i.test(raw)) {
		const datePart = raw.split(":").slice(1).join(":").trim().replace(/\.$/, "");
		return `روز اوج فروش این محصول: ${localizeAxisLabel(datePart)}.`;
	}

	if (/^cancelled amount in window:/i.test(raw)) {
		const amountPart = raw.split(":").slice(1).join(":").trim().replace(/\.$/, "");
		return `مبلغ لغو شده در این بازه: ${amountPart}.`;
	}

	let replaced = raw;
	for (const [pattern, replacement] of REPORT_REGEX_REPLACEMENTS) {
		replaced = replaced.replace(pattern, replacement);
	}
	if (replaced !== raw) return replaced;

	const normalized = raw
		.replace(/([a-z])([A-Z])/g, "$1 $2")
		.toLowerCase()
		.replace(/[_-]+/g, " ")
		.replace(/\s+/g, " ")
		.trim();

	if (REPORT_PHRASE_MAP[normalized]) return REPORT_PHRASE_MAP[normalized];

	const translatedWords = normalized.split(" ").map((word) => REPORT_PHRASE_MAP[word] || word);
	const translated = translatedWords.join(" ");
	return translated !== normalized ? translated : raw;
}
