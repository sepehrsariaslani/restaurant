function getCSRFToken() {
	if (typeof window === "undefined") return "";
	if (window.csrf_token) return String(window.csrf_token);
	if (window.frappe && window.frappe.csrf_token) return String(window.frappe.csrf_token);
	try {
		const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
		if (match && match[1]) return decodeURIComponent(match[1]);
	} catch (_) {}
	return "";
}

function storeCsrfToken(token) {
	const t = String(token || "").trim();
	if (!t) return;
	window.csrf_token = t;
	if (!window.frappe) window.frappe = {};
	window.frappe.csrf_token = t;
}

export async function uploadFileToFrappe(file, options = {}) {
	if (!file) {
		throw new Error("فایلی برای آپلود انتخاب نشده است.");
	}

	const buildFormData = () => {
		const formData = new FormData();
		formData.append("file", file);
		formData.append("is_private", options.isPrivate ? "1" : "0");
		if (options.doctype) formData.append("doctype", String(options.doctype));
		if (options.docname) formData.append("docname", String(options.docname));
		if (options.fieldname) formData.append("fieldname", String(options.fieldname));
		if (options.folder) formData.append("folder", String(options.folder));
		return formData;
	};

	const doFetch = (csrfToken) =>
		fetch("/api/method/upload_file", {
			method: "POST",
			headers: {
				"X-Frappe-CSRF-Token": csrfToken,
			},
			credentials: "include",
			body: buildFormData(),
		});

	let response = await doFetch(getCSRFToken());
	if (response.status === 400 || response.status === 403) {
		const freshToken = await refreshCsrfToken();
		if (freshToken) {
			response = await doFetch(freshToken);
		}
	}

	const payload = await response.json().catch(() => ({}));
	if (!response.ok || payload.exc || payload.exception) {
		const serverMessage = unpackServerMessages(payload);
		throw new Error(
			serverMessage ||
				payload._error_message ||
				payload.message ||
				"آپلود تصویر ناموفق بود. لطفاً دوباره تلاش کنید.",
		);
	}

	const message = payload.message || {};
	return {
		...message,
		file_url: String(message.file_url || "").trim(),
	};
}

async function refreshCsrfToken() {
	try {
		const res = await fetch("/api/method/frappe.utils.get_csrf_token", {
			method: "GET",
			credentials: "include",
		});
		if (res.ok) {
			const data = await res.json().catch(() => ({}));
			const token = String(data?.message || "").trim();
			if (token && token !== "unauthorized") {
				storeCsrfToken(token);
				return token;
			}
		}
	} catch (_) {}
	return getCSRFToken();
}

function unpackServerMessages(payload) {
	if (!payload || !payload._server_messages) {
		return "";
	}

	try {
		const raw = JSON.parse(payload._server_messages);
		const parsed = Array.isArray(raw) ? raw.map((line) => JSON.parse(line).message) : [];
		return parsed.filter(Boolean).join(" | ");
	} catch (error) {
		return "";
	}
}

export async function callMethodByPath(methodPath, args = {}) {
	const doFetch = (csrfToken) =>
		fetch(`/api/method/${methodPath}`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": csrfToken,
			},
			credentials: "include",
			body: JSON.stringify(args),
		});

	let response = await doFetch(getCSRFToken());

	if (response.status === 400 || response.status === 403) {
		const freshToken = await refreshCsrfToken();
		if (freshToken) {
			response = await doFetch(freshToken);
		}
	}

	const payload = await response.json().catch(() => ({}));

	if (!response.ok || payload.exc || payload.exception) {
		const serverMessage = unpackServerMessages(payload);
		const message =
			serverMessage ||
			payload._error_message ||
			payload.message ||
			"خطا در ارتباط با سرور. لطفا دوباره تلاش کنید.";
		throw new Error(message);
	}

	return payload.message;
}

export async function callMethodByPathGET(methodPath, args = {}, opts = {}) {
	const params = new URLSearchParams();
	for (const [key, value] of Object.entries(args || {})) {
		if (value === undefined || value === null) {
			continue;
		}
		if (typeof value === "object") {
			params.set(key, JSON.stringify(value));
			continue;
		}
		params.set(key, String(value));
	}

	const query = params.toString();
	const url = query ? `/api/method/${methodPath}?${query}` : `/api/method/${methodPath}`;
	const response = await fetch(url, {
		method: "GET",
		credentials: "include",
		...opts,
	});

	const payload = await response.json().catch(() => ({}));
	if (!response.ok || payload.exc || payload.exception) {
		const serverMessage = unpackServerMessages(payload);
		const message =
			serverMessage ||
			payload._error_message ||
			payload.message ||
			"خطا در ارتباط با سرور. لطفا دوباره تلاش کنید.";
		throw new Error(message);
	}
	return payload.message;
}

function isGuestSessionOnClient() {
	if (typeof window === "undefined") {
		return false;
	}
	const sessionUser = String(
		window.frappe?.session_user ||
			window.frappe?.boot?.user?.name ||
			window.boot?.user?.name ||
			window._BOOT?.user?.name ||
			"",
	).trim();
	return !sessionUser || sessionUser === "Guest";
}

function shouldPreferPublicGET() {
	return isGuestSessionOnClient() || !String(getCSRFToken() || "").trim();
}

const unsupportedDoctypesCache = new Set();

function normalizeListRows(rows) {
	return Array.isArray(rows) ? rows : [];
}

async function safeGetList(args = {}, { fallback = [] } = {}) {
	const doctype = String(args?.doctype || "").trim();
	if (doctype && unsupportedDoctypesCache.has(doctype)) {
		return normalizeListRows(fallback);
	}

	try {
		const rows = await callMethodByPath("frappe.client.get_list", args);
		return normalizeListRows(rows);
	} catch (error) {
		const message = String(error?.message || "").toLowerCase();
		if (
			doctype &&
			(message.includes("doctype") ||
				message.includes("not found") ||
				message.includes("does not exist") ||
				message.includes("permission"))
		) {
			unsupportedDoctypesCache.add(doctype);
		}
		return normalizeListRows(fallback);
	}
}

const doctypeColumnsCache = new Map();
let coreMenuSupportCache = null;
let preferBootFallback = false;
let preferManagementProductsFallback = false;
let preferMenuItemsFallback = false;
const SCHEMA_INTROSPECTION_DISABLED = true;

const STATIC_DOCTYPE_COLUMNS = {
	Item: new Set([
		"name",
		"item_code",
		"item_name",
		"item_group",
		"standard_rate",
		"disabled",
		"custom_snapp_code",
	]),
	"Item Group": new Set([
		"name",
		"item_group_name",
		"parent_item_group",
		"is_group",
		"restaurant_is_menu_category",
		"restaurant_is_subcategory",
		"restaurant_active",
		"restaurant_slug",
		"restaurant_sort_order",
		"restaurant_description",
		"restaurant_menu_icon",
		"show_on_homepage",
		"image",
	]),
};

async function listDoctypeColumns(doctype = "") {
	const normalized = String(doctype || "").trim();
	if (!normalized) {
		return new Set();
	}
	if (SCHEMA_INTROSPECTION_DISABLED) {
		return STATIC_DOCTYPE_COLUMNS[normalized] || new Set();
	}
	if (doctypeColumnsCache.has(normalized)) {
		return doctypeColumnsCache.get(normalized);
	}

	try {
		const rows = await callMethodByPath("frappe.client.get_list", {
			doctype: "DocField",
			fields: ["fieldname"],
			filters: [["parent", "=", normalized]],
			limit_page_length: 2000,
		});
		const set = new Set(
			(rows || []).map((row) => String(row?.fieldname || "").trim()).filter(Boolean),
		);
		doctypeColumnsCache.set(normalized, set);
		return set;
	} catch (error) {
		const empty = new Set();
		doctypeColumnsCache.set(normalized, empty);
		return empty;
	}
}

async function hasDoctypeField(doctype = "", fieldname = "") {
	const normalizedField = String(fieldname || "").trim();
	if (!normalizedField) {
		return false;
	}
	const columns = await listDoctypeColumns(doctype);
	return columns.has(normalizedField);
}

function makeFallbackSlug(value = "") {
	const normalized = String(value || "")
		.trim()
		.toLowerCase()
		.replace(/\s+/g, "-")
		.replace(/[^\w\u0600-\u06FF-]+/g, "")
		.replace(/-+/g, "-")
		.replace(/^-|-$/g, "");
	return normalized;
}

async function hasCoreMenuSupportOnClient() {
	if (typeof coreMenuSupportCache === "boolean") {
		return coreMenuSupportCache;
	}

	const checks = await Promise.all([
		hasDoctypeField("Item", "restaurant_enabled"),
		hasDoctypeField("Item", "restaurant_slug"),
		hasDoctypeField("Item", "restaurant_category"),
		hasDoctypeField("Item Group", "restaurant_is_menu_category"),
		hasDoctypeField("Item Group", "restaurant_is_subcategory"),
		hasDoctypeField("Item Group", "restaurant_slug"),
	]);
	coreMenuSupportCache = checks.every(Boolean);
	return coreMenuSupportCache;
}

async function getMenuBootFallback() {
	const hasMenuCategory = await hasDoctypeField("Item Group", "restaurant_is_menu_category");
	const hasSubcategory = await hasDoctypeField("Item Group", "restaurant_is_subcategory");
	const hasSlug = await hasDoctypeField("Item Group", "restaurant_slug");
	const hasSortOrder = await hasDoctypeField("Item Group", "restaurant_sort_order");
	const hasActive = await hasDoctypeField("Item Group", "restaurant_active");

	const fields = ["name", "item_group_name", "parent_item_group", "is_group"];
	if (hasSlug) {
		fields.push("restaurant_slug");
	}
	if (hasSortOrder) {
		fields.push("restaurant_sort_order");
	}

	const filters = [];
	if (hasMenuCategory) {
		filters.push(["restaurant_is_menu_category", "=", 1]);
	}
	if (hasActive) {
		filters.push(["restaurant_active", "=", 1]);
	}

	let rows = [];
	try {
		rows = await callMethodByPath("frappe.client.get_list", {
			doctype: "Item Group",
			fields,
			filters: filters.length ? filters : undefined,
			order_by: hasSortOrder
				? "restaurant_sort_order asc, item_group_name asc"
				: "item_group_name asc",
			limit_page_length: 800,
		});
	} catch (error) {
		rows = [];
	}

	const categories = [];
	const subcategories = [];
	for (const row of Array.isArray(rows) ? rows : []) {
		const isSub = hasSubcategory
			? Number(row?.restaurant_is_subcategory || 0) === 1
			: Number(row?.is_group || 0) !== 1 &&
				Boolean(String(row?.parent_item_group || "").trim());
		const payload = {
			name: String(row?.name || "").trim(),
			title: String(row?.item_group_name || row?.name || "").trim(),
			slug: hasSlug
				? String(row?.restaurant_slug || "").trim()
				: makeFallbackSlug(row?.item_group_name || row?.name || ""),
			image: "",
			sort_order: Number(row?.restaurant_sort_order || 0) || 0,
			item_count: 0,
			parent_item_group: String(row?.parent_item_group || "").trim(),
		};
		if (!payload.name) {
			continue;
		}
		if (isSub) {
			subcategories.push(payload);
		} else {
			categories.push({
				...payload,
				subcategories: [],
			});
		}
	}

	const categoryMap = new Map(categories.map((row) => [row.name, row]));
	for (const sub of subcategories) {
		const parent = categoryMap.get(sub.parent_item_group);
		if (!parent) {
			continue;
		}
		parent.subcategories.push({
			name: sub.name,
			title: sub.title,
			slug: sub.slug,
			sort_order: sub.sort_order,
			item_count: 0,
		});
	}

	for (const row of categories) {
		row.subcategories = (row.subcategories || []).sort((left, right) =>
			String(left?.title || "").localeCompare(String(right?.title || ""), "fa"),
		);
	}

	let currency = "IRR";
	try {
		const value = await callMethodByPath("frappe.client.get_single_value", {
			doctype: "Global Defaults",
			field: "default_currency",
		});
		currency = String(value || "").trim() || currency;
	} catch (error) {
		currency = "IRR";
	}

	return {
		categories,
		subcategory_enabled: Boolean(subcategories.length),
		featured_items: [],
		menu_highlight: {
			enabled: 0,
			title: "ویژه و پرفروش",
			show_featured: 1,
			show_best_seller: 1,
			featured_limit: 10,
			best_seller_limit: 10,
			per_category_limit: 3,
			category_items: {},
			items: [],
		},
		hero_slides: [],
		about_us_sections: [],
		faq_items: [],
		currency,
		branding: {
			name: "Restaurant",
			tagline: "منوی آنلاین",
			hero_title: "منوی آنلاین",
			hero_subtitle: "",
			primary_cta_label: "ورود به منو",
		},
		checkout_map: {},
	};
}

async function listManagementProductsFallback({
	search = "",
	category = "",
	active_only = 0,
	branch = "",
	tag = "",
} = {}) {
	const itemHasRestaurantEnabled = await hasDoctypeField("Item", "restaurant_enabled");
	const itemHasRestaurantSlug = await hasDoctypeField("Item", "restaurant_slug");
	const itemHasRestaurantShortDesc = await hasDoctypeField("Item", "restaurant_short_desc");
	const itemHasRestaurantBasePrice = await hasDoctypeField("Item", "restaurant_base_price");
	const itemHasRestaurantCategory = await hasDoctypeField("Item", "restaurant_category");
	const itemHasRestaurantSubcategory = await hasDoctypeField("Item", "restaurant_subcategory");
	const itemHasRestaurantBranch = await hasDoctypeField("Item", "restaurant_branch");
	const itemHasCustomSnappCode = await hasDoctypeField("Item", "custom_snapp_code");
	const itemHasImage = await hasDoctypeField("Item", "image");
	const itemHasItemImage = await hasDoctypeField("Item", "item_image");
	const itemHasRestaurantItemTags = await hasDoctypeField("Item", "restaurant_item_tags");
	const itemGroupHasSlug = await hasDoctypeField("Item Group", "restaurant_slug");

	const fields = ["name", "item_code", "item_name", "item_group", "standard_rate", "disabled"];
	if (itemHasRestaurantEnabled) {
		fields.push("restaurant_enabled");
	}
	if (itemHasRestaurantSlug) {
		fields.push("restaurant_slug");
	}
	if (itemHasRestaurantShortDesc) {
		fields.push("restaurant_short_desc");
	}
	if (itemHasRestaurantBasePrice) {
		fields.push("restaurant_base_price");
	}
	if (itemHasRestaurantCategory) {
		fields.push("restaurant_category");
	}
	if (itemHasRestaurantSubcategory) {
		fields.push("restaurant_subcategory");
	}
	if (itemHasCustomSnappCode) {
		fields.push("custom_snapp_code");
	}
	if (itemHasImage) {
		fields.push("image");
	}
	if (itemHasItemImage && !fields.includes("item_image")) {
		fields.push("item_image");
	}
	if (itemHasRestaurantItemTags) {
		fields.push("restaurant_item_tags");
	}

	const query = String(search || "").trim();
	const normalizedCategory = String(category || "").trim();
	const normalizedBranch = String(branch || "").trim();
	const normalizedTag = String(tag || "").trim();
	const filters = [];

	if (Number(active_only || 0) === 1) {
		if (itemHasRestaurantEnabled) {
			filters.push(["restaurant_enabled", "=", 1]);
		} else {
			filters.push(["disabled", "=", 0]);
		}
	}

	if (normalizedBranch && itemHasRestaurantBranch) {
		filters.push(["restaurant_branch", "in", [normalizedBranch, ""]]);
	}

	let resolvedCategoryName = "";
	if (normalizedCategory && itemGroupHasSlug) {
		try {
			const rows = await callMethodByPath("frappe.client.get_list", {
				doctype: "Item Group",
				fields: ["name"],
				filters: [["restaurant_slug", "=", normalizedCategory]],
				limit_page_length: 1,
			});
			resolvedCategoryName = String(rows?.[0]?.name || "").trim();
		} catch (error) {
			resolvedCategoryName = "";
		}
	}

	if (normalizedCategory && !resolvedCategoryName) {
		try {
			const rows = await callMethodByPath("frappe.client.get_list", {
				doctype: "Item Group",
				fields: ["name"],
				filters: [["name", "=", normalizedCategory]],
				limit_page_length: 1,
			});
			resolvedCategoryName = String(rows?.[0]?.name || "").trim();
		} catch (error) {
			resolvedCategoryName = "";
		}
	}

	if (normalizedCategory && !resolvedCategoryName) {
		try {
			const rows = await callMethodByPath("frappe.client.get_list", {
				doctype: "Item Group",
				fields: ["name"],
				filters: [["item_group_name", "=", normalizedCategory]],
				limit_page_length: 1,
			});
			resolvedCategoryName = String(rows?.[0]?.name || "").trim();
		} catch (error) {
			resolvedCategoryName = "";
		}
	}

	if (normalizedCategory) {
		const categoryValue = resolvedCategoryName || normalizedCategory;
		const hasResolved = Boolean(resolvedCategoryName);
		if (itemHasRestaurantCategory && hasResolved) {
			filters.push(["restaurant_category", "=", categoryValue]);
		} else if (!itemHasRestaurantCategory) {
			filters.push(["item_group", "=", categoryValue]);
		}
	}

	if (normalizedTag && itemHasRestaurantItemTags) {
		filters.push(["restaurant_item_tags", "like", `%${normalizedTag}%`]);
	}

	const orFilters = [];
	if (query) {
		const like = `%${query}%`;
		orFilters.push(["item_name", "like", like], ["item_code", "like", like]);
		if (itemHasRestaurantSlug) {
			orFilters.push(["restaurant_slug", "like", like]);
		}
	}

	let rows = [];
	try {
		rows = await callMethodByPath("frappe.client.get_list", {
			doctype: "Item",
			fields,
			filters: filters.length ? filters : undefined,
			or_filters: orFilters.length ? orFilters : undefined,
			order_by: "modified desc",
			limit_page_length: 500,
		});
	} catch (error) {
		return {
			products: [],
			stock: {
				low_threshold: 5,
			},
		};
	}

	const groupNames = new Set();
	for (const row of rows || []) {
		const categoryName = String(row?.restaurant_category || row?.item_group || "").trim();
		const subcategoryName = String(row?.restaurant_subcategory || "").trim();
		if (categoryName) {
			groupNames.add(categoryName);
		}
		if (subcategoryName) {
			groupNames.add(subcategoryName);
		}
	}

	const groupMap = new Map();
	if (groupNames.size) {
		const groupFields = ["name", "item_group_name", "parent_item_group"];
		if (itemGroupHasSlug) {
			groupFields.push("restaurant_slug");
		}
		try {
			const groupRows = await callMethodByPath("frappe.client.get_list", {
				doctype: "Item Group",
				fields: groupFields,
				filters: [["name", "in", Array.from(groupNames)]],
				limit_page_length: 1000,
			});
			for (const row of groupRows || []) {
				groupMap.set(String(row?.name || "").trim(), row || {});
			}
		} catch (error) {
			// Keep fallback payload even if group metadata is unavailable.
		}
	}

	const stockMap = new Map();
	const itemCodes = Array.from(
		new Set((rows || []).map((row) => String(row?.item_code || "").trim()).filter(Boolean)),
	);
	if (itemCodes.length) {
		try {
			const stockRows = await callMethodByPath("frappe.client.get_list", {
				doctype: "Bin",
				fields: ["item_code", "actual_qty"],
				filters: [["item_code", "in", itemCodes]],
				limit_page_length: 3000,
			});
			for (const row of stockRows || []) {
				const key = String(row?.item_code || "").trim();
				if (!key) {
					continue;
				}
				stockMap.set(key, Number(stockMap.get(key) || 0) + Number(row?.actual_qty || 0));
			}
		} catch (error) {
			// Ignore stock fallback failures.
		}
	}

	const payload = (rows || []).map((row) => {
		const categoryName = String(row?.restaurant_category || row?.item_group || "").trim();
		const subcategoryName = String(row?.restaurant_subcategory || "").trim();
		const categoryMeta = groupMap.get(categoryName) || {};
		const subcategoryMeta = groupMap.get(subcategoryName) || {};
		const title = String(row?.item_name || row?.name || "").trim();
		const itemCode = String(row?.item_code || row?.name || "").trim();
		const image = String(row?.image || row?.item_image || "").trim();
		const slug =
			String(row?.restaurant_slug || "").trim() ||
			makeFallbackSlug(title) ||
			makeFallbackSlug(itemCode);
		const basePrice = Number(row?.restaurant_base_price ?? row?.standard_rate ?? 0) || 0;
		const isActive = itemHasRestaurantEnabled
			? Number(row?.restaurant_enabled || 0)
			: Number(row?.disabled || 0) === 0
				? 1
				: 0;

		return {
			name: String(row?.name || "").trim(),
			item_code: itemCode,
			custom_snapp_code: String(row?.custom_snapp_code || "").trim(),
			title,
			slug,
			short_desc: String(row?.restaurant_short_desc || "").trim(),
			base_price: basePrice,
			image,
			category: categoryName,
			category_title: String(categoryMeta?.item_group_name || categoryName || "").trim(),
			category_slug: String(categoryMeta?.restaurant_slug || "").trim(),
			subcategory: subcategoryName,
			subcategory_title: String(subcategoryMeta?.item_group_name || "").trim(),
			subcategory_slug: String(subcategoryMeta?.restaurant_slug || "").trim(),
			is_active: isActive ? 1 : 0,
			is_disabled: Number(row?.disabled || 0) ? 1 : 0,
			stock_qty: Number(stockMap.get(itemCode) || 0),
			tags: itemHasRestaurantItemTags
				? String(row?.restaurant_item_tags || "")
						.split(",")
						.map((t) => t.trim())
						.filter(Boolean)
				: [],
		};
	});

	return {
		products: payload,
		stock: {
			low_threshold: 5,
		},
	};
}

export async function callRestaurantAPI(methodName, args = {}) {
	return callMethodByPath(`restaurant.api.${methodName}`, args);
}

function isMissingMethodError(error, methodPath = "") {
	const message = String(error?.message || "").trim().toLowerCase();
	const normalizedPath = String(methodPath || "").trim().toLowerCase();
	if (!message) {
		return false;
	}
	return (
		message.includes("failed to get method for command") &&
		(!normalizedPath || message.includes(normalizedPath))
	);
}

function normalizeModifierGroupOptionFallback(row = {}) {
	const actionType = String(row?.action_type || "add_on").trim() || "add_on";
	const isActive = Number(row?.is_active ?? 1) === 1 || row?.is_active === true;
	const optionItem = String(row?.option_item || "").trim();
	const priceDelta = Number(row?.price_delta || 0) || 0;
	let priceStatus = "ok";
	if (!isActive) {
		priceStatus = "inactive";
	} else if (actionType === "add_on" && !optionItem) {
		priceStatus = "missing_item";
	}
	return {
		name: String(row?.name || "").trim(),
		option_name: String(row?.option_name || row?.name || "").trim(),
		action_type: actionType,
		option_item: optionItem,
		option_item_name: String(row?.option_item_name || "").trim(),
		option_uom: String(row?.option_uom || "").trim(),
		option_qty: Number(row?.option_qty || 1) || 1,
		base_qty: Number((row?.base_qty ?? row?.option_qty ?? 1)) || 1,
		stock_uom: String(row?.stock_uom || "").trim(),
		option_cost_rate: Number(row?.option_cost_rate || 0) || 0,
		option_cost_amount: Number(row?.option_cost_amount || 0) || 0,
		legacy_price_delta: priceDelta,
		price_delta: priceDelta,
		base_price: Number((row?.base_price ?? row?.price_delta ?? 0)) || 0,
		unit_rate: Number(row?.unit_rate || 0) || 0,
		conversion_factor: Number(row?.conversion_factor || 1) || 1,
		price_status: priceStatus,
		price_source: priceStatus === "ok" ? "legacy" : "legacy_unresolved",
		price_item_code: optionItem,
		price_list: String(row?.price_list || "").trim(),
		min_qty: Number(row?.min_qty ?? 0) || 0,
		max_qty: Number(row?.max_qty ?? 4) || 4,
		qty_step: Number(row?.qty_step || row?.option_qty || 1) || 1,
		alternative_bom: String(row?.alternative_bom || "").trim(),
		recipe_multiplier: Number(row?.recipe_multiplier || 1) || 1,
		is_default: Number(row?.is_default || 0) === 1 || row?.is_default === true ? 1 : 0,
		sort_order: Number(row?.sort_order || 0) || 0,
		is_active: isActive ? 1 : 0,
		is_selectable: isActive ? 1 : 0,
		disabled: isActive ? 0 : 1,
		unavailable_reason:
			priceStatus === "missing_item"
				? "برای این گزینه هنوز آیتم قیمت‌گذاری انتخاب نشده است."
				: priceStatus === "inactive"
					? "این گزینه غیرفعال است."
					: "",
	};
}

function normalizeModifierGroupDocFallback(doc = {}, defaultPriceList = "") {
	const options = Array.isArray(doc?.options)
		? doc.options.map((row) =>
				normalizeModifierGroupOptionFallback({
					...row,
					price_list: row?.price_list || defaultPriceList,
				}),
			)
		: [];
	const activeOptionsCount = options.filter((row) => Number(row?.is_active ?? 1) === 1).length;
	const unresolvedCount = options.filter(
		(row) =>
			Number(row?.is_active ?? 1) === 1 &&
			String(row?.price_status || "").trim() !== "ok",
	).length;
	return {
		name: String(doc?.name || "").trim(),
		title: String(doc?.title || doc?.name || "").trim(),
		selection_mode: String(doc?.selection_mode || "single").trim() || "single",
		required: Number(doc?.required || 0) === 1 || doc?.required === true ? 1 : 0,
		min_select: Number(doc?.min_select || 0) || 0,
		max_select: Number(doc?.max_select || 1) || 1,
		description: String(doc?.description || "").trim(),
		sort_order: Number(doc?.sort_order || 0) || 0,
		is_active: Number(doc?.is_active ?? 1) === 1 || doc?.is_active === true ? 1 : 0,
		default_price_list: String(defaultPriceList || "").trim(),
		options,
		options_count: options.length,
		active_options_count: activeOptionsCount,
		unresolved_options_count: unresolvedCount,
		has_pricing_issues: unresolvedCount > 0 ? 1 : 0,
	};
}

async function getModifierGroupsContextFallback() {
	let defaultPriceList = "";
	let priceLists = [];
	try {
		const priceListPayload = await callRestaurantAPI("list_management_price_lists", {});
		defaultPriceList = String(priceListPayload?.default_price_list || "").trim();
		priceLists = Array.isArray(priceListPayload?.price_lists) ? priceListPayload.price_lists : [];
	} catch (_) {
		defaultPriceList = "";
		priceLists = [];
	}

	const [itemRows, bomRows, uomRows] = await Promise.all([
		safeGetList({
			doctype: "Item",
			fields: ["name", "item_name"],
			filters: [["disabled", "=", 0]],
			order_by: "item_name asc",
			limit_page_length: 1000,
		}),
		safeGetList({
			doctype: "BOM",
			fields: ["name", "item"],
			order_by: "modified desc",
			limit_page_length: 1000,
		}),
		safeGetList({
			doctype: "UOM",
			fields: ["name", "uom_name"],
			order_by: "uom_name asc",
			limit_page_length: 500,
		}),
	]);

	return {
		default_price_list: defaultPriceList,
		price_lists: priceLists,
		item_options: itemRows.map((row) => ({
			value: String(row?.name || "").trim(),
			label: String(row?.item_name || row?.name || "").trim(),
		})),
		bom_options: bomRows.map((row) => ({
			value: String(row?.name || "").trim(),
			label: String(row?.item || row?.name || "").trim(),
		})),
		uom_options: uomRows.map((row) => ({
			value: String(row?.name || "").trim(),
			label: String(row?.uom_name || row?.name || "").trim(),
		})),
		action_type_options: [
			{ value: "add_on", label: "Add-on" },
			{ value: "bom_variant", label: "BOM Variant" },
		],
	};
}

export async function getManagementSessionProfile() {
	try {
		const user =
			String((await callMethodByPathGET("frappe.auth.get_logged_user")) || "").trim() ||
			"Guest";
		if (user === "Guest") {
			return {
				user: "Guest",
				full_name: "",
				user_image: "",
				is_guest: true,
				is_staff: false,
				is_admin: false,
				roles: [],
			};
		}

		let fullName = "";
		let userImage = "";
		try {
			const profile = await callMethodByPath("frappe.client.get_value", {
				doctype: "User",
				filters: { name: user },
				fieldname: ["full_name", "user_image"],
			});
			fullName = String(profile?.full_name || "").trim();
			userImage = String(profile?.user_image || "").trim();
		} catch (profileError) {
			fullName = "";
			userImage = "";
		}

		// Fetch role/permission info from restaurant API
		let isStaff = false;
		let isAdmin = false;
		let roles = [];
		try {
			const roleData = await callRestaurantAPI("get_session_roles");
			isStaff = Boolean(roleData?.is_staff);
			isAdmin = Boolean(roleData?.is_admin);
			roles = Array.isArray(roleData?.roles) ? roleData.roles : [];
		} catch (_) {
			// Fallback: not staff if role check fails
		}

		return {
			user,
			full_name: fullName,
			user_image: userImage,
			is_guest: false,
			is_staff: isStaff,
			is_admin: isAdmin,
			roles,
		};
	} catch (error) {
		return {
			user: "Guest",
			full_name: "",
			user_image: "",
			is_guest: true,
			is_staff: false,
			is_admin: false,
			roles: [],
		};
	}
}

export async function loginManagementUser({ usr = "", pwd = "" } = {}) {
	const username = String(usr || "").trim();
	const password = String(pwd || "");
	if (!username || !password) {
		throw new Error("نام کاربری و رمز عبور الزامی است.");
	}

	const body = new URLSearchParams();
	body.set("usr", username);
	body.set("pwd", password);

	const response = await fetch("/api/method/login", {
		method: "POST",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			"X-Frappe-CSRF-Token": getCSRFToken(),
		},
		credentials: "include",
		body: body.toString(),
	});

	const payload = await response.json().catch(() => ({}));
	if (!response.ok || payload.exc || payload.exception) {
		const serverMessage = unpackServerMessages(payload);
		const message =
			serverMessage || payload._error_message || payload.message || "ورود ناموفق بود.";
		throw new Error(message);
	}

	const msg = payload.message || payload;
	if (msg?.csrf_token) storeCsrfToken(msg.csrf_token);
	await refreshCsrfToken();

	return msg;
}

export async function logoutManagementUser() {
	try {
		return await callMethodByPath("logout", {});
	} catch (error) {
		return { status: "ok" };
	}
}

export async function getMenuBoot(branch = "") {
	const args = { branch };
	try {
		if (shouldPreferPublicGET()) {
			return await callMethodByPathGET("restaurant.api.get_menu_boot", args);
		}
		return await callRestaurantAPI("get_menu_boot", args);
	} catch (error) {
		try {
			return await callMethodByPathGET("restaurant.api.get_menu_boot", args);
		} catch (fallbackError) {
			if (preferBootFallback) {
				return getMenuBootFallback();
			}
			preferBootFallback = true;
			return getMenuBootFallback();
		}
	}
}

async function getMenuItemsFallback({
	category_slug = "",
	subcategory_slug = "",
	search = "",
	page = 1,
	page_size = 20,
	branch = "",
} = {}) {
	const currentPage = Math.max(Number(page || 1), 1);
	const currentPageSize = Math.max(Math.min(Number(page_size || 20), 200), 1);
	const normalizedSubcategory = makeFallbackSlug(subcategory_slug);

	const payload = await listManagementProductsFallback({
		search,
		category: category_slug,
		active_only: 1,
		branch,
	});

	let rows = Array.isArray(payload?.products) ? payload.products : [];

	if (normalizedSubcategory) {
		rows = rows.filter((row) => {
			const subcategorySlug = makeFallbackSlug(row?.subcategory_slug || "");
			const subcategoryNameSlug = makeFallbackSlug(
				row?.subcategory_title || row?.subcategory || "",
			);
			return (
				subcategorySlug === normalizedSubcategory ||
				subcategoryNameSlug === normalizedSubcategory
			);
		});
	}

	const normalizedRows = rows.map((row) => {
		const showInPrintValue = row?.show_in_print ?? row?.show_in_website;
		const normalizedSlug =
			String(row?.slug || "").trim() ||
			makeFallbackSlug(row?.title || row?.item_name || row?.item_code || row?.name || "");

		return {
			name: String(row?.name || "").trim(),
			item_code: String(row?.item_code || "").trim(),
			title: String(row?.title || row?.item_name || row?.name || "").trim(),
			slug: normalizedSlug,
			short_desc: String(row?.short_desc || row?.restaurant_short_desc || "").trim(),
			long_desc: String(row?.long_desc || row?.restaurant_long_desc || "").trim(),
			base_price: Number(row?.base_price || 0),
			image: String(row?.image || "").trim(),
			category: String(row?.category || "").trim(),
			category_title: String(row?.category_title || row?.category || "").trim(),
			category_slug: String(row?.category_slug || "").trim(),
			subcategory: String(row?.subcategory || "").trim(),
			subcategory_title: String(row?.subcategory_title || row?.subcategory || "").trim(),
			subcategory_slug: String(row?.subcategory_slug || "").trim(),
			prep_time_mins: Number(row?.prep_time_mins || 0),
			nutrition: row?.nutrition || {},
			allergens: Array.isArray(row?.allergens) ? row.allergens : [],
			has_bom: Number(row?.has_bom || 0) ? 1 : 0,
			has_customization: Number(row?.has_customization || 0) ? 1 : 0,
			coming_soon: Number(row?.coming_soon ?? row?.restaurant_coming_soon ?? 0) ? 1 : 0,
			is_active: Number(row?.is_active || 0) ? 1 : 0,
			show_in_print: showInPrintValue === undefined ? 1 : Number(showInPrintValue) ? 1 : 0,
			show_in_website: showInPrintValue === undefined ? 1 : Number(showInPrintValue) ? 1 : 0,
		};
	});

	const start = (currentPage - 1) * currentPageSize;
	const pagedRows = normalizedRows.slice(start, start + currentPageSize);
	const total = normalizedRows.length;
	const totalPages = total > 0 ? Math.ceil(total / currentPageSize) : 0;

	return {
		items: pagedRows,
		pagination: {
			page: currentPage,
			page_size: currentPageSize,
			total,
			total_pages: totalPages,
		},
	};
}

export async function getMenuItems({
	category_slug = "",
	subcategory_slug = "",
	search = "",
	page = 1,
	page_size = 20,
	branch = "",
} = {}) {
	const args = { category_slug, subcategory_slug, search, page, page_size, branch };
	try {
		if (shouldPreferPublicGET()) {
			return await callMethodByPathGET("restaurant.api.get_menu_items", args);
		}
		return await callRestaurantAPI("get_menu_items", args);
	} catch (error) {
		try {
			return await callMethodByPathGET("restaurant.api.get_menu_items", args);
		} catch (fallbackError) {
			if (preferMenuItemsFallback || preferBootFallback) {
				return getMenuItemsFallback(args);
			}
			preferMenuItemsFallback = true;
			return getMenuItemsFallback(args);
		}
	}
}

export async function getItemDetail(item_slug, branch = "") {
	const args = { item_slug, branch };
	if (shouldPreferPublicGET()) {
		return callMethodByPathGET("restaurant.api.get_item_detail", args);
	}

	try {
		return await callRestaurantAPI("get_item_detail", args);
	} catch (error) {
		return callMethodByPathGET("restaurant.api.get_item_detail", args);
	}
}

export async function getRelatedItems(item_slug, limit = 6) {
	try {
		const data = await callMethodByPathGET("restaurant.api.get_related_items", {
			item_slug,
			limit,
		});
		return Array.isArray(data) ? data : [];
	} catch (_) {
		return [];
	}
}

export async function getBomPreview(item_code, signal) {
	const opts = signal ? { signal } : {};
	try {
		const data = await callMethodByPathGET(
			"restaurant.api.get_bom_preview",
			{ item_code },
			opts,
		);
		return data?.data || data || {};
	} catch (error) {
		if (error.name === "AbortError") throw error;
		// Fallback to POST if GET fails
		console.warn("[BOM] GET failed, falling back to POST:", error.message);
		const data = await callMethodByPath("restaurant.api.get_bom_preview", { item_code });
		return data?.data || data || {};
	}
}

export function getCustomerCheckoutProfile({ mobile = "", customer_name = "" } = {}) {
	return callRestaurantAPI("get_customer_checkout_profile", { mobile, customer_name });
}

export function getCustomerProfile({ mobile = "" } = {}) {
	return callRestaurantAPI("get_customer_profile", mobile ? { mobile } : {});
}

export function getCustomerOrders({ mobile = "", limit = 50, start = 0 } = {}) {
	return callRestaurantAPI("get_customer_orders", { mobile, limit, start });
}

export function sendOtp({ mobile = "", customer_name = "" } = {}) {
	return callRestaurantAPI("send_otp", { mobile, customer_name });
}

export function verifyOtp({ mobile = "", otp = "", code = "", customer_name = "" } = {}) {
	return callRestaurantAPI("verify_otp", { mobile, otp, code, customer_name });
}

export function getBranches() {
	return callRestaurantAPI("get_branches", {});
}

export function getAvailableTables({
	branch = "",
	reservation_date = "",
	reservation_time = "",
	guest_count = 1,
} = {}) {
	return callRestaurantAPI("get_available_tables", {
		branch,
		reservation_date,
		reservation_time,
		guest_count,
	});
}

export function createTableReservation(payload = {}) {
	return callRestaurantAPI("create_table_reservation", { payload });
}

export function validateCoupon({
	coupon_code = "",
	items = [],
	mobile = "",
	branch = "",
	subtotal = null,
} = {}) {
	return callRestaurantAPI("validate_coupon", { coupon_code, items, mobile, branch, subtotal });
}

export function submitReview(payload = {}) {
	return callRestaurantAPI("submit_review", { payload });
}

export function getItemReviews({ item_slug = "", item = "", page = 1, page_size = 20 } = {}) {
	return callRestaurantAPI("get_item_reviews", { item_slug, item, page, page_size });
}

export function saveCustomerDeliveryAddress({ customer_info = {}, address_info = {} } = {}) {
	return callRestaurantAPI("save_customer_delivery_address", { customer_info, address_info });
}

export function getCustomerVehicles({ mobile = "", customer_name = "" } = {}) {
	return callRestaurantAPI("get_customer_vehicles", { mobile, customer_name });
}

export function saveCustomerVehicle({ customer_info = {}, vehicle_info = {} } = {}) {
	return callRestaurantAPI("save_customer_vehicle", { customer_info, vehicle_info });
}

export function placeOrder(payload) {
	return callRestaurantAPI("place_order", payload);
}

export function getOrder(order_code, mobile) {
	return callRestaurantAPI("get_order", { order_code, mobile });
}

export function getOrderProductionStatus(order_code, mobile) {
	return callRestaurantAPI("get_order_production_status", { order_code, mobile });
}

export function getManagementDashboard({ date_from = "", date_to = "", branch = "" } = {}) {
	return callRestaurantAPI("get_management_dashboard", { date_from, date_to, branch });
}

export function getManagementBIReport(
	report_key,
	{ date_from = "", date_to = "", compare_mode = "previous_window" } = {},
) {
	return callRestaurantAPI("get_management_bi_report", {
		report_key,
		date_from,
		date_to,
		compare_mode,
	});
}

export function getManagementPOSBoot({ branch = "" } = {}) {
	return callRestaurantAPI("get_management_pos_boot", { branch });
}

export function getManagementPOSConfig() {
	return callRestaurantAPI("get_management_pos_config", {});
}

export function setManagementPOSConfig(payload = {}) {
	return callRestaurantAPI("set_management_pos_config", { payload });
}

export function getManagementPOSHardwareStatus() {
	return callRestaurantAPI("get_management_pos_hardware_status");
}

export function createManagementPOSOrder(payload = {}) {
	return callRestaurantAPI("create_management_pos_order", { payload });
}

export function confirmManagementPOSPayment({
	order_name = "",
	status = "paid",
	reference_no = "",
	rrn = "",
	provider_payload = {},
} = {}) {
	return callRestaurantAPI("confirm_management_pos_payment", {
		order_name,
		status,
		reference_no,
		rrn,
		provider_payload,
	});
}


export async function createPOSOrder(payload = {}) {
	return callRestaurantAPI("create_pos_order", { payload });
}

export async function producePOSOrder(order_name = "") {
	return callRestaurantAPI("produce_pos_order", { order_name });
}

export async function settlePOSOrder(order_name, payment = {}) {
	return callRestaurantAPI("settle_pos_order", { order_name, payment });
}

export async function deliverPOSOrder(order_name = "") {
	return callRestaurantAPI("deliver_pos_order", { order_name });
}

export async function produceAndDeliverPOSOrder(order_name = "") {
	return callRestaurantAPI("produce_and_deliver_pos_order", { order_name });
}


export async function createAndSettlePOSOrder(payload = {}) {
	return callRestaurantAPI("create_and_settle_pos_order", { payload });
}

export async function markManagementOrderPaid({
	order_name = "",
	reference_no = "",
	rrn = "",
	provider_payload = {},
} = {}) {
	try {
		return await callRestaurantAPI("mark_management_order_paid", {
			order_name,
			reference_no,
			rrn,
			provider_payload,
		});
	} catch (error) {
		const message = String(error?.message || "");
		if (!message.includes("has no attribute 'mark_management_order_paid'")) {
			throw error;
		}
		return confirmManagementPOSPayment({
			order_name,
			status: "paid",
			reference_no,
			rrn,
			provider_payload,
		});
	}
}

export async function completeManagementOrder({
	order_name = "",
	reference_no = "",
	rrn = "",
	provider_payload = {},
} = {}) {
	try {
		return await callRestaurantAPI("complete_management_order", {
			order_name,
			reference_no,
			rrn,
			provider_payload,
		});
	} catch (error) {
		const message = String(error?.message || "");
		if (!message.includes("has no attribute 'complete_management_order'")) {
			throw error;
		}

		await confirmManagementPOSPayment({
			order_name,
			status: "paid",
			reference_no,
			rrn,
			provider_payload,
		});

		// Fallback for older backend code: attempt to advance automation flow.
		try {
			await runManagementOrderAutoFlow({
				order_name,
				trigger: "manual",
				payment_status: "paid",
				force: 1,
			});
		} catch (flowError) {
			// Last fallback for legacy backend: force delivery status directly.
			try {
				await callMethodByPath("frappe.client.set_value", {
					doctype: "Sales Order",
					name: order_name,
					fieldname: "restaurant_status",
					value: "delivered",
				});
			} catch (statusError) {
				// Keep payment success even if delivery status update is unavailable.
			}
		}

		return { status: "success", order_name, fallback: true };
	}
}

export function voidManagementPOSOrder(order_name, reason = "") {
	return callRestaurantAPI("void_management_pos_order", { order_name, reason });
}

export function listManagementPOSOrders({
	date_from = "",
	date_to = "",
	status = "",
	cashier = "",
} = {}) {
	return callRestaurantAPI("list_management_pos_orders", {
		date_from,
		date_to,
		status,
		cashier,
	});
}

export function listManagementPOSPaymentLogs({
	date_from = "",
	date_to = "",
	status = "",
	limit = 50,
} = {}) {
	return callRestaurantAPI("list_management_pos_payment_logs", {
		date_from,
		date_to,
		status,
		limit,
	});
}

export function reportManagementPOSHardwareEvent({
	event_type = "system",
	severity = "info",
	message = "",
	payload = {},
	related_order = "",
	source = "pos",
} = {}) {
	return callRestaurantAPI("report_management_pos_hardware_event", {
		event_type,
		severity,
		message,
		payload,
		related_order,
		source,
	});
}

export function getTableOverview() {
	return callRestaurantAPI("get_table_overview");
}

export function getTableDetail(table_name = "") {
	return callRestaurantAPI("get_table_detail", { table_name });
}

export function getTableMenu(qr_token = "") {
	return callRestaurantAPI("get_table_menu", { qr_token });
}

export function placeTableOrder({ qr_token = "", items = [], note = "" } = {}) {
	return callRestaurantAPI("place_table_order", {
		qr_token,
		items,
		note,
	});
}

export function createManagementTableOrderFromPOS({
	table_name = "",
	items = [],
	note = "",
} = {}) {
	return callRestaurantAPI("create_management_table_order_from_pos", {
		table_name,
		items: JSON.stringify(items),
		note,
	});
}

export function confirmTableOrder(order_name = "") {
	return callRestaurantAPI("confirm_table_order", { order_name });
}

export function serveTableOrder(order_name = "") {
	return callRestaurantAPI("serve_table_order", { order_name });
}

export function payTableOrder(order_name = "") {
	return callRestaurantAPI("pay_table_order", { order_name });
}

export function updateTableOrderItem({
	order_name = "",
	row_name = "",
	menu_item = "",
	quantity = null,
	quantity_delta = null,
	note = null,
} = {}) {
	return callRestaurantAPI("update_table_order_item", {
		order_name,
		row_name,
		menu_item,
		quantity,
		quantity_delta,
		note,
	});
}

export function resolveTableRequest(request_name = "") {
	return callRestaurantAPI("resolve_table_request", { request_name });
}

export function closeTableSession(session_name = "") {
	return callRestaurantAPI("close_table_session", { session_name });
}

export function assignTableSessionCustomer({
	table_name = "",
	customer_name = "",
	mobile = "",
	customer_type = "",
	guest_count = 1,
} = {}) {
	return callRestaurantAPI("assign_table_session_customer", {
		table_name,
		customer_name,
		mobile,
		customer_type,
		guest_count,
	});
}

export function moveTableSession({ session_name = "", target_table = "" } = {}) {
	return callRestaurantAPI("move_table_session", {
		session_name,
		target_table,
	});
}

export function mergeTableSessions({ source_session = "", target_table = "" } = {}) {
	return callRestaurantAPI("merge_table_sessions", {
		source_session,
		target_table,
	});
}

export function listManagementOrders({
	date_from = "",
	date_to = "",
	status = "",
	source = "",
	cashier = "",
} = {}) {
	return callRestaurantAPI("list_management_orders", {
		date_from,
		date_to,
		status,
		source,
		cashier,
	});
}

export function getManagementOrderDetail(order_name, source = "") {
	return callRestaurantAPI("get_management_order_detail", { order_name, source });
}

export function updateManagementOrder({
	order_name = "",
	payment_method,
	note,
	customer_name,
	mobile,
} = {}) {
	const args = { order_name };
	if (payment_method !== undefined) args.payment_method = payment_method;
	if (note !== undefined) args.note = note;
	if (customer_name !== undefined) args.customer_name = customer_name;
	if (mobile !== undefined) args.mobile = mobile;
	return callRestaurantAPI("update_management_order", args);
}

export function createManagementReturnOrder({ order_name = "", reason = "" } = {}) {
	return callRestaurantAPI("create_management_return_order", { order_name, reason });
}

export async function listManagementProducts({
	search = "",
	category = "",
	active_only = 0,
	branch = "",
	tag = "",
} = {}) {
	if (preferManagementProductsFallback) {
		return listManagementProductsFallback({ search, category, active_only, branch, tag });
	}

	const hasCoreSupport = await hasCoreMenuSupportOnClient();
	if (!hasCoreSupport) {
		preferManagementProductsFallback = true;
		return listManagementProductsFallback({ search, category, active_only, branch, tag });
	}

	try {
		return await callRestaurantAPI("list_management_products", {
			search,
			category,
			active_only,
			branch,
			tag,
		});
	} catch (error) {
		preferManagementProductsFallback = true;
		return listManagementProductsFallback({ search, category, active_only, branch, tag });
	}
}

export async function createManagementProduct(payload = {}) {
	const itemCode = String(payload?.item_code || payload?.name || "").trim();
	const itemName = String(payload?.item_name || "").trim();
	const stockUom = String(payload?.stock_uom || "").trim();
	if (!itemCode) {
		throw new Error("کد کالا الزامی است.");
	}
	if (!itemName) {
		throw new Error("نام کالا الزامی است.");
	}
	if (!stockUom) {
		throw new Error("واحد کالا الزامی است.");
	}

	const doc = {
		doctype: "Item",
		item_code: itemCode,
		item_name: itemName,
		stock_uom: stockUom,
		item_group: String(payload?.item_group || "All Item Groups").trim() || "All Item Groups",
		is_stock_item: Number(payload?.is_stock_item ?? 0) ? 1 : 0,
		disabled: Number(payload?.disabled ?? 0) ? 1 : 0,
	};

	if (payload?.description !== undefined) {
		doc.description = String(payload.description || "").trim();
	}
	if (payload?.custom_snapp_code !== undefined) {
		doc.custom_snapp_code = String(payload.custom_snapp_code || "").trim();
	}
	if (payload?.restaurant_enabled !== undefined) {
		doc.restaurant_enabled = Number(payload.restaurant_enabled) ? 1 : 0;
	} else {
		doc.restaurant_enabled = 1;
	}
	if (payload?.show_in_print !== undefined) {
		doc.show_in_website = Number(payload.show_in_print) ? 1 : 0;
	} else if (payload?.show_in_website !== undefined) {
		doc.show_in_website = Number(payload.show_in_website) ? 1 : 0;
	}
	if (payload?.restaurant_category !== undefined) {
		doc.restaurant_category = String(payload.restaurant_category || "").trim();
	}
	if (payload?.restaurant_subcategory !== undefined) {
		doc.restaurant_subcategory = String(payload.restaurant_subcategory || "").trim();
	}

	return callMethodByPath("frappe.client.insert", { doc });
}

export async function listRestaurantItemTags({ limit = 500 } = {}) {
	const rows = await safeGetList({
		doctype: "Restaurant Item Tag",
		fields: ["name", "title"],
		order_by: "title asc, modified desc",
		limit_page_length: Math.max(1, Math.min(Number(limit || 500), 1000)),
	});
	return rows.map((row) => ({
		value: row.name,
		label: row.title || row.name,
	}));
}

export async function uploadManagementItemImage({
	item_name = "",
	file = null,
	is_private = 0,
} = {}) {
	const itemName = String(item_name || "").trim();
	if (!itemName) {
		throw new Error("شناسه محصول معتبر نیست.");
	}
	if (!file) {
		throw new Error("فایلی برای آپلود انتخاب نشده است.");
	}

	const formData = new FormData();
	formData.append("file", file);
	formData.append("doctype", "Item");
	formData.append("docname", itemName);
	formData.append("is_private", is_private ? "1" : "0");

	const response = await fetch("/api/method/upload_file", {
		method: "POST",
		headers: {
			"X-Frappe-CSRF-Token": getCSRFToken(),
		},
		credentials: "include",
		body: formData,
	});

	const payload = await response.json().catch(() => ({}));
	if (!response.ok || payload.exc || payload.exception) {
		const serverMessage = unpackServerMessages(payload);
		const message =
			serverMessage ||
			payload._error_message ||
			payload.message ||
			"آپلود تصویر ناموفق بود.";
		throw new Error(message);
	}

	return payload.message || payload;
}

export async function deleteManagementItemImageByUrl({ item_name = "", file_url = "" } = {}) {
	const itemName = String(item_name || "").trim();
	const fileUrl = String(file_url || "").trim();
	if (!itemName || !fileUrl) {
		return { deleted: false };
	}

	const rows = await safeGetList({
		doctype: "File",
		filters: [
			["attached_to_doctype", "=", "Item"],
			["attached_to_name", "=", itemName],
			["file_url", "=", fileUrl],
		],
		fields: ["name", "file_url"],
		limit_page_length: 1,
	});

	const fileRow = Array.isArray(rows) ? rows[0] : null;
	if (!fileRow?.name) {
		return { deleted: false };
	}

	await callMethodByPath("frappe.client.delete", {
		doctype: "File",
		name: fileRow.name,
	});

	return { deleted: true, name: fileRow.name, file_url: fileRow.file_url || fileUrl };
}

export async function getManagementBomContext() {
	const payload = await callRestaurantAPI("get_management_bom_context", {});
	return payload || { companies: [], default_company: "", default_currency: "" };
}

export async function listManagementBomItems({ search = "", limit = 200 } = {}) {
	const rows = await callRestaurantAPI("list_management_bom_items", { search, limit });
	return Array.isArray(rows) ? rows : [];
}

export async function listManagementModifierGroups({ search = "", limit = 300 } = {}) {
	const query = String(search || "").trim();
	const args = {
		doctype: "Restaurant Modifier Group",
		fields: [
			"name",
			"title",
			"selection_mode",
			"required",
			"min_select",
			"max_select",
			"is_active",
			"sort_order",
		],
		filters: [["is_active", "=", 1]],
		order_by: "sort_order asc, modified desc",
		limit_page_length: Math.max(1, Math.min(Number(limit || 300), 500)),
	};

	if (query) {
		const like = `%${query}%`;
		args.or_filters = [
			["name", "like", like],
			["title", "like", like],
		];
	}

	const rows = await safeGetList(args);
	return rows;
}

export async function getManagementModifierGroupDoc(group_name = "") {
	const groupName = String(group_name || "").trim();
	if (!groupName) {
		throw new Error("گروه مودیفایر نامعتبر است.");
	}
	return callMethodByPath("frappe.client.get", {
		doctype: "Restaurant Modifier Group",
		name: groupName,
	});
}

export async function listManagementModifierGroupsOverview({
	search = "",
	include_inactive = 1,
} = {}) {
	try {
		const payload = await callRestaurantAPI("list_management_modifier_groups", {
			search,
			include_inactive: Number(include_inactive) ? 1 : 0,
		});
		return payload || { groups: [], default_price_list: "" };
	} catch (error) {
		if (!isMissingMethodError(error, "restaurant.api.list_management_modifier_groups")) {
			throw error;
		}
		const fallbackContext = await getModifierGroupsContextFallback();
		const rows = await safeGetList({
			doctype: "Restaurant Modifier Group",
			fields: [
				"name",
				"title",
				"selection_mode",
				"required",
				"min_select",
				"max_select",
				"description",
				"sort_order",
				"is_active",
				"modified",
			],
			filters: Number(include_inactive) ? undefined : [["is_active", "=", 1]],
			or_filters: String(search || "").trim()
				? [
						["name", "like", `%${String(search || "").trim()}%`],
						["title", "like", `%${String(search || "").trim()}%`],
					]
				: undefined,
			order_by: "sort_order asc, modified desc",
			limit_page_length: 500,
		});
		return {
			groups: rows.map((row) => ({
				...normalizeModifierGroupDocFallback(row, fallbackContext.default_price_list),
				modified: row?.modified || "",
				options: undefined,
			})),
			default_price_list: fallbackContext.default_price_list || "",
		};
	}
}

export async function getManagementModifierGroupsContext() {
	try {
		const payload = await callRestaurantAPI("get_management_modifier_groups_context", {});
		return payload || { default_price_list: "", price_lists: [], item_options: [], bom_options: [], uom_options: [] };
	} catch (error) {
		if (!isMissingMethodError(error, "restaurant.api.get_management_modifier_groups_context")) {
			throw error;
		}
		return getModifierGroupsContextFallback();
	}
}

export async function getManagementModifierGroupDetail(group_name = "") {
	const groupName = String(group_name || "").trim();
	if (!groupName) {
		throw new Error("گروه مودیفایر نامعتبر است.");
	}
	try {
		return await callRestaurantAPI("get_management_modifier_group_detail", { group_name: groupName });
	} catch (error) {
		if (!isMissingMethodError(error, "restaurant.api.get_management_modifier_group_detail")) {
			throw error;
		}
		const [doc, context] = await Promise.all([
			getManagementModifierGroupDoc(groupName),
			getModifierGroupsContextFallback(),
		]);
		return normalizeModifierGroupDocFallback(doc, context.default_price_list);
	}
}

export async function saveManagementModifierGroup(payload = {}) {
	try {
		return await callRestaurantAPI("save_management_modifier_group", { payload });
	} catch (error) {
		if (!isMissingMethodError(error, "restaurant.api.save_management_modifier_group")) {
			throw error;
		}
		const normalizedPayload = payload && typeof payload === "object" ? payload : {};
		const doc = {
			doctype: "Restaurant Modifier Group",
			name: String(normalizedPayload?.name || "").trim() || undefined,
			title: String(normalizedPayload?.title || "").trim(),
			selection_mode: String(normalizedPayload?.selection_mode || "single").trim() || "single",
			required:
				Number(normalizedPayload?.required || 0) === 1 || normalizedPayload?.required === true ? 1 : 0,
			min_select: Number(normalizedPayload?.min_select || 0) || 0,
			max_select: Number(normalizedPayload?.max_select || 1) || 1,
			description: String(normalizedPayload?.description || "").trim(),
			sort_order: Number(normalizedPayload?.sort_order || 0) || 0,
			is_active:
				Number(normalizedPayload?.is_active ?? 1) === 1 || normalizedPayload?.is_active === true ? 1 : 0,
			options: Array.isArray(normalizedPayload?.options)
				? normalizedPayload.options.map((row) => ({
						doctype: "Restaurant Modifier Option",
						name: String(row?.name || "").trim() || undefined,
						option_name: String(row?.option_name || "").trim(),
						action_type: String(row?.action_type || "add_on").trim() || "add_on",
						option_item: String(row?.option_item || "").trim(),
						alternative_bom: String(row?.alternative_bom || "").trim(),
						option_qty: Number(row?.option_qty || 1) || 1,
						min_qty: Number(row?.min_qty ?? 1) || 1,
						max_qty: Number(row?.max_qty ?? 9) || 9,
						qty_step: Number(row?.qty_step || 1) || 1,
						recipe_multiplier: Number(row?.recipe_multiplier || 1) || 1,
						is_default: Number(row?.is_default || 0) === 1 || row?.is_default === true ? 1 : 0,
						sort_order: Number(row?.sort_order || 0) || 0,
						is_active: Number(row?.is_active ?? 1) === 1 || row?.is_active === true ? 1 : 0,
						price_delta: Number(row?.price_delta || 0) || 0,
					}))
				: [],
		};
		const method = doc.name ? "frappe.client.save" : "frappe.client.insert";
		const saved = await callMethodByPath(method, { doc });
		return getManagementModifierGroupDetail(saved?.name || doc.name || doc.title || "");
	}
}

export async function deleteManagementModifierGroup(group_name = "") {
	const groupName = String(group_name || "").trim();
	if (!groupName) {
		throw new Error("گروه مودیفایر نامعتبر است.");
	}
	return callMethodByPath("frappe.client.delete", {
		doctype: "Restaurant Modifier Group",
		name: groupName,
	});
}

export async function listManagementBoms({ item_code = "", search = "", limit = 50 } = {}) {
	const rows = await callRestaurantAPI("list_management_boms", { item_code, search, limit });
	return Array.isArray(rows) ? rows : [];
}

export async function getManagementBomDoc(bom_name = "") {
	const bomName = String(bom_name || "").trim();
	if (!bomName) {
		throw new Error("شناسه BOM معتبر نیست.");
	}
	return callRestaurantAPI("get_management_bom_doc", { bom_name: bomName });
}

function normalizeBomItems(items = []) {
	const normalizeCheck = (value, defaultValue = 0) => {
		if (value === "" || value === null || value === undefined) {
			return defaultValue ? 1 : 0;
		}
		return Number(value) ? 1 : 0;
	};

	return (Array.isArray(items) ? items : [])
		.map((row) => ({
			item_code: String(row?.item_code || "").trim(),
			qty: Number(row?.qty || 0),
			uom: String(row?.uom || "").trim(),
			rate: Number(row?.rate || 0),
			source_warehouse: String(row?.source_warehouse || "").trim(),
			show_in_website: normalizeCheck(row?.show_in_website ?? row?.show_in_print, 1),
			restaurant_customer_label: String(row?.restaurant_customer_label || "").trim(),
			restaurant_is_included_by_default: normalizeCheck(
				row?.restaurant_is_included_by_default,
				1,
			),
			restaurant_can_remove: normalizeCheck(row?.restaurant_can_remove, 0),
			restaurant_is_required: normalizeCheck(row?.restaurant_is_required),
			restaurant_is_editable_qty: normalizeCheck(row?.restaurant_is_editable_qty, 0),
			restaurant_min_multiplier: Number(row?.restaurant_min_multiplier || 0),
			restaurant_max_multiplier: Number(row?.restaurant_max_multiplier || 3),
			restaurant_step_multiplier: Number(row?.restaurant_step_multiplier || 0.5),
			restaurant_multiplier_qty: Number(row?.restaurant_multiplier_qty || 0),
			restaurant_extra_when_added: Number(row?.restaurant_extra_when_added || 0),
			restaurant_nutrition_kcal: Number(row?.restaurant_nutrition_kcal || 0),
			restaurant_nutrition_protein_g: Number(row?.restaurant_nutrition_protein_g || 0),
			restaurant_nutrition_carb_g: Number(row?.restaurant_nutrition_carb_g || 0),
			restaurant_nutrition_sugar_g: Number(row?.restaurant_nutrition_sugar_g || 0),
			restaurant_nutrition_fat_g: Number(row?.restaurant_nutrition_fat_g || 0),
			include_item_in_manufacturing: normalizeCheck(row?.include_item_in_manufacturing, 1),
			allow_alternative_item: normalizeCheck(row?.allow_alternative_item),
		}))
		.filter((row) => row.item_code && row.qty > 0 && row.uom);
}

function normalizeBomModifierRows(rows = []) {
	const normalizeCheck = (value, defaultValue = 0) => {
		if (value === "" || value === null || value === undefined) {
			return defaultValue ? 1 : 0;
		}
		return Number(value) ? 1 : 0;
	};

	return (Array.isArray(rows) ? rows : [])
		.map((row, index) => ({
			modifier_group: String(row?.modifier_group || "").trim(),
			group_key: String(row?.group_key || row?.modifier_group || "").trim(),
			group_title: String(row?.group_title || "").trim(),
			selection_mode: String(row?.selection_mode || "single").trim() || "single",
			required: normalizeCheck(row?.required),
			min_select: Number(row?.min_select || 0),
			max_select: Number(row?.max_select || 1),
			modifier_type: String(row?.modifier_type || "add_on").trim() || "add_on",
			option_key: String(row?.option_key || "").trim(),
			option_label: String(row?.option_label || "").trim(),
			option_item: String(row?.option_item || "").trim(),
			replacement_for_item: String(row?.replacement_for_item || "").trim(),
			alternative_bom: String(row?.alternative_bom || "").trim(),
			option_qty: Number(row?.option_qty || 1),
			price_delta: Number(row?.price_delta || 0),
			recipe_multiplier: Number(row?.recipe_multiplier || 1),
			is_default: normalizeCheck(row?.is_default),
			sort_order: Number(row?.sort_order ?? index ?? 0) || 0,
			is_active: normalizeCheck(row?.is_active, 1),
		}))
		.filter((row) => row.modifier_group);
}

export async function createManagementBom(payload = {}) {
	const itemCode = String(payload?.item || payload?.item_code || "").trim();
	if (!itemCode) {
		throw new Error("محصول BOM مشخص نشده است.");
	}

	const items = normalizeBomItems(payload.items || []);
	if (!items.length) {
		throw new Error("حداقل یک قلم مواد اولیه برای BOM لازم است.");
	}

	const bomDoc = {
		doctype: "BOM",
		item: itemCode,
		quantity: Number(payload?.quantity || 1) || 1,
		company: String(payload?.company || "").trim(),
		currency: String(payload?.currency || "").trim(),
		conversion_rate: 1,
		with_operations: 0,
		rm_cost_as_per:
			String(payload?.rm_cost_as_per || "Valuation Rate").trim() || "Valuation Rate",
		is_active: payload?.is_active === false ? 0 : 1,
		is_default: payload?.is_default ? 1 : 0,
		restaurant_recipe_instruction: String(payload?.restaurant_recipe_instruction || "").trim(),
		restaurant_nutrition_kcal: Number(payload?.restaurant_nutrition_kcal || 0),
		restaurant_nutrition_protein_g: Number(payload?.restaurant_nutrition_protein_g || 0),
		restaurant_nutrition_carb_g: Number(payload?.restaurant_nutrition_carb_g || 0),
		restaurant_nutrition_sugar_g: Number(payload?.restaurant_nutrition_sugar_g || 0),
		restaurant_nutrition_fat_g: Number(payload?.restaurant_nutrition_fat_g || 0),
		items,
		restaurant_modifier_rows: normalizeBomModifierRows(
			payload?.restaurant_modifier_rows || [],
		),
	};

	const created = await callMethodByPath("frappe.client.insert", {
		doc: bomDoc,
	});

	if (payload?.submit) {
		return callMethodByPath("frappe.client.submit", {
			doc: created,
		});
	}

	return created;
}

export async function updateManagementBom(payload = {}) {
	const bomName = String(payload?.name || "").trim();
	if (!bomName) {
		throw new Error("شناسه BOM معتبر نیست.");
	}

	const current = await getManagementBomDoc(bomName);

	const normalizedItems = normalizeBomItems(payload.items || current?.items || []);
	if (!normalizedItems.length) {
		throw new Error("حداقل یک قلم مواد اولیه برای BOM لازم است.");
	}

	const saved = await callMethodByPath("restaurant.api.save_management_bom", {
		payload: {
			name: bomName,
			item: String(payload?.item || payload?.item_code || current?.item || "").trim(),
			rm_cost_as_per:
				String(
					payload?.rm_cost_as_per || current?.rm_cost_as_per || "Valuation Rate",
				).trim() || "Valuation Rate",
			quantity: Number(payload?.quantity || current?.quantity || 1) || 1,
			company: String(payload?.company || current?.company || "").trim(),
			currency: String(payload?.currency || current?.currency || "").trim(),
			is_active: payload?.is_active === false ? 0 : 1,
			is_default: payload?.is_default ? 1 : 0,
			restaurant_recipe_instruction: String(
				payload?.restaurant_recipe_instruction ||
					current?.restaurant_recipe_instruction ||
					"",
			).trim(),
			restaurant_nutrition_kcal: Number(
				payload?.restaurant_nutrition_kcal || current?.restaurant_nutrition_kcal || 0,
			),
			restaurant_nutrition_protein_g: Number(
				payload?.restaurant_nutrition_protein_g ||
					current?.restaurant_nutrition_protein_g ||
					0,
			),
			restaurant_nutrition_carb_g: Number(
				payload?.restaurant_nutrition_carb_g || current?.restaurant_nutrition_carb_g || 0,
			),
			restaurant_nutrition_sugar_g: Number(
				payload?.restaurant_nutrition_sugar_g ||
					current?.restaurant_nutrition_sugar_g ||
					0,
			),
			restaurant_nutrition_fat_g: Number(
				payload?.restaurant_nutrition_fat_g || current?.restaurant_nutrition_fat_g || 0,
			),
			items: normalizedItems,
			restaurant_modifier_rows: normalizeBomModifierRows(
				payload?.restaurant_modifier_rows || current?.restaurant_modifier_rows || [],
			),
		},
	});

	if (payload?.submit && Number(saved?.docstatus || 0) === 0) {
		return callMethodByPath("frappe.client.submit", {
			doc: saved,
		});
	}
	return saved;
}

export async function submitManagementBom(bom_name = "") {
	const doc = await getManagementBomDoc(bom_name);
	if (Number(doc?.docstatus || 0) === 1) {
		return doc;
	}
	return callMethodByPath("frappe.client.submit", { doc });
}

export async function cancelManagementBom(bom_name = "") {
	const doc = await getManagementBomDoc(bom_name);
	if (Number(doc?.docstatus || 0) === 2) {
		return doc;
	}
	return callMethodByPath("frappe.client.cancel", { doc });
}

export async function duplicateManagementBomDraft(bom_name = "") {
	const source = await getManagementBomDoc(bom_name);
	const nextItems = normalizeBomItems(source?.items || []);
	const nextModifierRows = normalizeBomModifierRows(source?.restaurant_modifier_rows || []);
	if (!nextItems.length) {
		throw new Error("این BOM مواد اولیه ندارد.");
	}

	const payload = {
		doctype: "BOM",
		item: source.item,
		quantity: Number(source.quantity || 1) || 1,
		company: source.company,
		currency: source.currency,
		conversion_rate: Number(source.conversion_rate || 1) || 1,
		with_operations: 0,
		rm_cost_as_per: source.rm_cost_as_per || "Valuation Rate",
		is_active: 1,
		is_default: 0,
		restaurant_nutrition_kcal: Number(source.restaurant_nutrition_kcal || 0),
		restaurant_nutrition_protein_g: Number(source.restaurant_nutrition_protein_g || 0),
		restaurant_nutrition_carb_g: Number(source.restaurant_nutrition_carb_g || 0),
		restaurant_nutrition_sugar_g: Number(source.restaurant_nutrition_sugar_g || 0),
		restaurant_nutrition_fat_g: Number(source.restaurant_nutrition_fat_g || 0),
		amended_from: source.name || "",
		items: nextItems,
		restaurant_modifier_rows: nextModifierRows,
	};

	return callMethodByPath("frappe.client.insert", {
		doc: payload,
	});
}

export async function updateManagementBomCost({ bom_name = "", rm_cost_as_per = "" } = {}) {
	const bomName = String(bom_name || "").trim();
	if (!bomName) {
		throw new Error("شناسه BOM معتبر نیست.");
	}

	return callMethodByPath("restaurant.api.update_management_bom_cost", {
		payload: {
			bom_name: bomName,
			rm_cost_as_per: String(rm_cost_as_per || "").trim(),
		},
	});
}

export async function setManagementBomDefault({ bom_name = "", item_code = "" } = {}) {
	const bomName = String(bom_name || "").trim();
	const itemCode = String(item_code || "").trim();
	if (!bomName || !itemCode) {
		throw new Error("BOM یا محصول مشخص نیست.");
	}

	const rows = await safeGetList({
		doctype: "BOM",
		fields: ["name", "is_default"],
		filters: [
			["item", "=", itemCode],
			["docstatus", "in", [0, 1]],
		],
		limit_page_length: 500,
	});

	for (const row of rows || []) {
		if (!row?.name || row.name === bomName || !Number(row?.is_default || 0)) {
			continue;
		}
		await callMethodByPath("frappe.client.set_value", {
			doctype: "BOM",
			name: row.name,
			fieldname: "is_default",
			value: 0,
		});
	}

	await callMethodByPath("frappe.client.set_value", {
		doctype: "BOM",
		name: bomName,
		fieldname: "is_default",
		value: 1,
	});
	await callMethodByPath("frappe.client.set_value", {
		doctype: "BOM",
		name: bomName,
		fieldname: "is_active",
		value: 1,
	});

	try {
		await callMethodByPath("frappe.client.set_value", {
			doctype: "Item",
			name: itemCode,
			fieldname: "default_bom",
			value: bomName,
		});
	} catch (error) {
		// Some setups may not expose default_bom for write; keep BOM default update even then.
	}

	return getManagementBomDoc(bomName);
}

export function setManagementProductActive(item_name, active) {
	return callRestaurantAPI("set_management_product_active", { item_name, active });
}

export async function deleteManagementProduct(
	item_name,
	{ allow_archive_on_link = 1, force_delete = 0 } = {},
) {
	const itemName = String(item_name || "").trim();
	if (!itemName) {
		throw new Error("شناسه محصول معتبر نیست.");
	}

	try {
		return await callRestaurantAPI("delete_management_product", {
			item_name: itemName,
			allow_archive_on_link: allow_archive_on_link ? 1 : 0,
			force_delete: force_delete ? 1 : 0,
		});
	} catch (apiError) {
		const message = String(apiError?.message || "");
		const isMissingMethod =
			message.includes("has no attribute 'delete_management_product'") ||
			message.includes(
				"Failed to get method for command restaurant.api.delete_management_product",
			);

		if (!isMissingMethod) {
			throw apiError;
		}

		try {
			await callMethodByPath("frappe.client.delete", {
				doctype: "Item",
				name: itemName,
			});
			return {
				status: "deleted",
				item_name: itemName,
			};
		} catch (deleteError) {
			const deleteMessage = String(deleteError?.message || "");
			const canArchive =
				Boolean(allow_archive_on_link) &&
				/(linked|link exists|cannot delete|وابسته|مرتبط|reference|dependent)/i.test(
					deleteMessage,
				);
			if (!canArchive) {
				throw deleteError;
			}

			await callMethodByPath("frappe.client.set_value", {
				doctype: "Item",
				name: itemName,
				fieldname: "disabled",
				value: 1,
			});

			try {
				await callMethodByPath("frappe.client.set_value", {
					doctype: "Item",
					name: itemName,
					fieldname: "restaurant_enabled",
					value: 0,
				});
			} catch (archiveError) {
				// Optional field on some setups.
			}

			try {
				await callMethodByPath("frappe.client.set_value", {
					doctype: "Item",
					name: itemName,
					fieldname: "show_in_website",
					value: 0,
				});
			} catch (archiveError) {
				// Optional field on some setups.
			}

			return {
				status: "archived",
				item_name: itemName,
			};
		}
	}
}

function normalizeManagementMenuGroupPayload(payload = {}, currentDoc = null) {
	const source = payload && typeof payload === "object" ? payload : {};
	const fromDoc = currentDoc && typeof currentDoc === "object" ? currentDoc : {};

	const hasSubcategoryFlag = source?.restaurant_is_subcategory !== undefined;
	const hasMenuCategoryFlag = source?.restaurant_is_menu_category !== undefined;
	const requestedSubcategory = hasSubcategoryFlag
		? Number(source.restaurant_is_subcategory) === 1
		: Number(fromDoc.restaurant_is_subcategory || 0) === 1;
	const requestedMenuCategory = hasMenuCategoryFlag
		? Number(source.restaurant_is_menu_category) === 1
		: Number(fromDoc.restaurant_is_menu_category || 0) === 1;

	const restaurant_is_subcategory = requestedSubcategory ? 1 : 0;
	const restaurant_is_menu_category = requestedSubcategory ? 1 : requestedMenuCategory ? 1 : 0;

	let is_group = Number(source?.is_group ?? fromDoc?.is_group ?? 0) ? 1 : 0;
	if (restaurant_is_menu_category === 1 && restaurant_is_subcategory === 0) {
		is_group = 1;
	}
	if (restaurant_is_subcategory === 1) {
		is_group = 0;
	}

	const normalized = {
		item_group_name: String(source?.item_group_name ?? fromDoc?.item_group_name ?? "").trim(),
		parent_item_group: String(
			source?.parent_item_group ?? fromDoc?.parent_item_group ?? "",
		).trim(),
		is_group,
		restaurant_is_menu_category,
		restaurant_is_subcategory,
		restaurant_active:
			source?.restaurant_active !== undefined
				? Number(source.restaurant_active) === 1
					? 1
					: 0
				: Number(fromDoc?.restaurant_active ?? 1)
					? 1
					: 0,
		restaurant_slug: String(source?.restaurant_slug ?? fromDoc?.restaurant_slug ?? "").trim(),
		restaurant_sort_order:
			Number(source?.restaurant_sort_order ?? fromDoc?.restaurant_sort_order ?? 0) || 0,
		restaurant_description: String(
			source?.restaurant_description ?? fromDoc?.restaurant_description ?? "",
		).trim(),
		restaurant_menu_icon: String(
			source?.restaurant_menu_icon ?? fromDoc?.restaurant_menu_icon ?? "",
		).trim(),
		show_on_homepage:
			source?.show_on_homepage !== undefined
				? Number(source.show_on_homepage) === 1
					? 1
					: 0
				: Number(fromDoc?.show_on_homepage ?? 1)
					? 1
					: 0,
		image: String(source?.image ?? fromDoc?.image ?? "").trim(),
	};

	return normalized;
}

let managementMenuGroupIconFieldReady = null;

function ensureManagementMenuGroupIconField() {
	if (!managementMenuGroupIconFieldReady) {
		managementMenuGroupIconFieldReady = callRestaurantAPI("setup_menu_group_icon_field").catch(
			() => null,
		);
	}
	return managementMenuGroupIconFieldReady;
}

export async function listManagementMenuGroups({ search = "" } = {}) {
	await ensureManagementMenuGroupIconField();
	const rows = await callRestaurantAPI("list_management_menu_groups", { search });
	return (Array.isArray(rows) ? rows : []).map((row) => ({
		...row,
		restaurant_is_menu_category: Number(row?.restaurant_is_menu_category ?? 1) ? 1 : 0,
		restaurant_is_subcategory: Number(
			row?.restaurant_is_subcategory ?? (Number(row?.is_group || 0) ? 0 : 1),
		)
			? 1
			: 0,
		restaurant_active: Number(row?.restaurant_active ?? 1) ? 1 : 0,
		restaurant_slug: String(row?.restaurant_slug || "").trim(),
		restaurant_sort_order: Number(row?.restaurant_sort_order || 0) || 0,
		restaurant_description: String(row?.restaurant_description || "").trim(),
		restaurant_menu_icon: String(row?.restaurant_menu_icon || "").trim(),
		show_on_homepage: Number(row?.show_on_homepage ?? 1) ? 1 : 0,
		image: String(row?.image || "").trim(),
		modified: String(row?.modified || "").trim(),
	}));
}

export async function reorderManagementMenuGroups(items = []) {
	const normalized = (items || [])
		.filter((item) => String(item?.name || "").trim())
		.map((item, idx) => ({
			name: String(item.name).trim(),
			sort_order: Number(item.sort_order ?? idx) || idx,
		}));

	try {
		return await callRestaurantAPI("reorder_management_menu_groups", { items: normalized });
	} catch {
		await Promise.all(
			normalized.map(({ name, sort_order }) =>
				callMethodByPath("frappe.client.set_value", {
					doctype: "Item Group",
					name,
					fieldname: "restaurant_sort_order",
					value: sort_order,
				}).catch(() => null),
			),
		);
		return { ok: true, count: normalized.length };
	}
}

export function saveManagementMenuDesign(payload = {}) {
	return callRestaurantAPI("save_management_menu_design", { payload });
}

export async function listManagementItemGroupParents({ search = "" } = {}) {
	const query = String(search || "").trim();
	let rows = await callRestaurantAPI("list_management_item_group_parents", {
		search: query,
	}).catch(() => []);
	if (rows.length) {
		return rows;
	}

	const fallbackRows = await listManagementMenuGroups({ search: query }).catch(() => []);
	return (fallbackRows || [])
		.filter(
			(row) =>
				Number(row?.is_group || 0) === 1 ||
				Number(row?.restaurant_is_subcategory || 0) !== 1,
		)
		.map((row) => ({
			name: row.name,
			item_group_name: row.item_group_name || row.name,
			parent_item_group: row.parent_item_group || "",
			is_group: Number(row.is_group || 0) ? 1 : 0,
		}));
}

export async function getManagementMenuGroup(name = "") {
	const normalizedName = String(name || "").trim();
	if (!normalizedName) {
		throw new Error("شناسه گروه معتبر نیست.");
	}

	await ensureManagementMenuGroupIconField();
	return callMethodByPath("frappe.client.get", {
		doctype: "Item Group",
		name: normalizedName,
	});
}

export async function createManagementMenuGroup(payload = {}) {
	await ensureManagementMenuGroupIconField();
	const normalized = normalizeManagementMenuGroupPayload(payload);
	if (!normalized.item_group_name) {
		throw new Error("عنوان گروه الزامی است.");
	}
	if (!normalized.parent_item_group) {
		throw new Error("گروه والد الزامی است.");
	}

	const doc = {
		doctype: "Item Group",
		item_group_name: normalized.item_group_name,
		parent_item_group: normalized.parent_item_group,
		is_group: normalized.is_group,
		restaurant_is_menu_category: normalized.restaurant_is_menu_category,
		restaurant_is_subcategory: normalized.restaurant_is_subcategory,
		restaurant_active: normalized.restaurant_active,
		restaurant_slug: normalized.restaurant_slug,
		restaurant_sort_order: normalized.restaurant_sort_order,
		restaurant_description: normalized.restaurant_description,
		restaurant_menu_icon: normalized.restaurant_menu_icon,
		show_on_homepage: normalized.show_on_homepage,
		image: normalized.image,
	};
	return callMethodByPath("frappe.client.insert", { doc });
}

export async function updateManagementMenuGroup(payload = {}) {
	await ensureManagementMenuGroupIconField();
	const name = String(payload?.name || "").trim();
	if (!name) {
		throw new Error("شناسه گروه معتبر نیست.");
	}

	const current = await getManagementMenuGroup(name);

	const normalized = normalizeManagementMenuGroupPayload(payload, current);
	current.item_group_name = normalized.item_group_name;
	current.parent_item_group = normalized.parent_item_group;
	current.is_group = normalized.is_group;
	current.restaurant_is_menu_category = normalized.restaurant_is_menu_category;
	current.restaurant_is_subcategory = normalized.restaurant_is_subcategory;
	current.restaurant_active = normalized.restaurant_active;
	current.restaurant_slug = normalized.restaurant_slug;
	current.restaurant_sort_order = normalized.restaurant_sort_order;
	current.restaurant_description = normalized.restaurant_description;
	current.restaurant_menu_icon = normalized.restaurant_menu_icon;
	current.show_on_homepage = normalized.show_on_homepage;
	current.image = normalized.image;
	return callMethodByPath("frappe.client.save", { doc: current });
}

export function listManagementPriceLists({ currency = "" } = {}) {
	return callRestaurantAPI("list_management_price_lists", { currency });
}

export function setManagementDefaultPriceList(price_list_name) {
	return callRestaurantAPI("set_management_default_price_list", { price_list_name });
}

export function getManagementProductDetail({ item_name = "", date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_product_detail", { item_name, date_from, date_to });
}

export function updateManagementProductSettings(payload = {}) {
	return callRestaurantAPI("update_management_product_settings", { payload });
}

export function setManagementProductPrice(payload = {}) {
	return callRestaurantAPI("set_management_product_price", { payload });
}

export function getManagementProductVariantBuilder({ item_name = "" } = {}) {
	const normalized = String(item_name || "").trim();
	if (!normalized) {
		return callRestaurantAPI("get_management_product_variant_builder", {});
	}
	return callRestaurantAPI("get_management_product_variant_builder", { item_name: normalized });
}

export function listManagementItemAttributes({ search = "", include_values = 0 } = {}) {
	return callRestaurantAPI("list_management_item_attributes", {
		search,
		include_values: Number(include_values) ? 1 : 0,
	});
}

export function getManagementItemAttribute({ attribute_name = "" } = {}) {
	const normalized = String(attribute_name || "").trim();
	if (!normalized) {
		throw new Error("نام صفت الزامی است.");
	}
	return callRestaurantAPI("get_management_item_attribute", { attribute_name: normalized });
}

export function saveManagementItemAttribute(payload = {}) {
	return callRestaurantAPI("save_management_item_attribute", { payload });
}

export function saveManagementProductVariantBuilder(payload = {}) {
	return callRestaurantAPI("save_management_product_variant_builder", { payload });
}

export function generateManagementProductVariants(payload = {}) {
	return callRestaurantAPI("generate_management_product_variants", { payload });
}

export function runManagementOrderAutoFlow({
	order_name = "",
	trigger = "manual",
	payment_status = "",
	force = 1,
} = {}) {
	return callRestaurantAPI("run_management_order_auto_flow", {
		order_name,
		trigger,
		payment_status,
		force,
	});
}

export function getManagementProductionAutoSettings() {
	return callRestaurantAPI("get_management_production_auto_settings");
}

export function setManagementProductionAutoSettings(payload = {}) {
	return callRestaurantAPI("set_management_production_auto_settings", { payload });
}

export function getManagementPOSShiftSettings() {
	return callRestaurantAPI("get_management_pos_shift_settings");
}

export function setManagementPOSShiftSettings(payload = {}) {
	return callRestaurantAPI("set_management_pos_shift_settings", { payload });
}

export function getManagementPOSProfile({ profile_name = "" } = {}) {
	return callRestaurantAPI("get_management_pos_profile", { profile_name });
}

export function setManagementPOSProfile(payload = {}) {
	return callRestaurantAPI("set_management_pos_profile", { payload });
}

export function setManagementPOSProfileSettings(payload = {}) {
	return callRestaurantAPI("set_management_pos_profile_settings", { payload });
}

export function getManagementThemeSettings() {
	return callRestaurantAPI("get_management_theme_settings");
}

export function setManagementThemeSettings(payload = {}) {
	return callRestaurantAPI("set_management_theme_settings", { payload });
}

const SITE_SETTINGS_STORAGE_KEY = "restaurant_site_settings_local_v1";

const DEFAULT_SITE_SETTINGS = {
	web_settings: {},
	hero_slides: [],
	about_sections: [],
	faq_items: [],
};

export async function getManagementSiteSettings() {
	try {
		const result = await callRestaurantAPI("get_management_site_settings");
		if (result) {
			try {
				localStorage.setItem(SITE_SETTINGS_STORAGE_KEY, JSON.stringify(result));
			} catch (_) {}
		}
		return result;
	} catch (_apiError) {
		try {
			const stored = localStorage.getItem(SITE_SETTINGS_STORAGE_KEY);
			if (stored) {
				const parsed = JSON.parse(stored);
				if (parsed && typeof parsed === "object") return parsed;
			}
		} catch (_) {}
		return { ...DEFAULT_SITE_SETTINGS };
	}
}

export async function setManagementSiteSettings(payload = {}) {
	const result = await callRestaurantAPI("set_management_site_settings", { payload });
	try {
		localStorage.setItem(SITE_SETTINGS_STORAGE_KEY, JSON.stringify(result));
	} catch (_) {}
	return result;
}

export function listManagementCustomers({ search = "", date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("list_management_customers", { search, date_from, date_to });
}

export function getManagementTables() {
	return callRestaurantAPI("get_management_tables");
}

export function updateManagementTable(payload = {}) {
	return callRestaurantAPI("update_management_table", { payload });
}

export function updateManagementTableReservation(payload = {}) {
	return callRestaurantAPI("update_management_table_reservation", { payload });
}

export function updateManagementTableSession(payload = {}) {
	return callRestaurantAPI("update_management_table_session", { payload });
}

export function getManagementTablesOverview({
	branch = "",
	reservation_date = "",
	reservation_time = "",
} = {}) {
	return callRestaurantAPI("get_management_tables_overview", {
		branch,
		reservation_date,
		reservation_time,
	});
}

function isMissingCustomerDetailMethodError(error) {
	const message = String(error?.message || "").toLowerCase();
	if (!message) {
		return false;
	}
	if (!message.includes("get_management_customer_detail")) {
		return false;
	}
	return (
		message.includes("failed to get method for command") ||
		message.includes("has no attribute 'get_management_customer_detail'") ||
		message.includes("no attribute") ||
		message.includes("not found")
	);
}

function normalizeCustomerLabel(order = {}) {
	return String(order?.customer_name || "").trim() || "POS Customer";
}

function normalizeCustomerMobile(order = {}) {
	return String(order?.mobile || "").trim();
}

function isLegacyRevenueOrder(order = {}) {
	const source = String(order?.source || "")
		.trim()
		.toLowerCase();
	const status = String(order?.status || "")
		.trim()
		.toLowerCase();
	const webRevenueStatuses = new Set(["new", "confirmed", "preparing", "ready", "delivered"]);
	const tableRevenueStatuses = new Set(["confirmed", "served", "paid"]);
	if (source === "table") {
		return tableRevenueStatuses.has(status);
	}
	return webRevenueStatuses.has(status);
}

function isLegacyCustomerMatch(order = {}, mobile = "", customerName = "") {
	const normalizedMobile = String(mobile || "").trim();
	const normalizedName = String(customerName || "")
		.trim()
		.toLowerCase();
	const orderMobile = normalizeCustomerMobile(order);
	const orderName = normalizeCustomerLabel(order).toLowerCase();

	if (normalizedMobile && orderMobile !== normalizedMobile) {
		return false;
	}
	if (normalizedName && !normalizedMobile && orderName !== normalizedName) {
		return false;
	}
	return Boolean(normalizedMobile || normalizedName);
}

function getOrderTimestamp(order = {}) {
	const createdAt = String(order?.created_at || "").trim();
	if (!createdAt) {
		return 0;
	}
	const timestamp = Date.parse(createdAt);
	return Number.isFinite(timestamp) ? timestamp : 0;
}

function buildLegacyCustomerReport(orders = [], { date_from = "", date_to = "" } = {}) {
	const totalSpent = orders.reduce((sum, row) => sum + Number(row?.grand_total || 0), 0);
	const ordersCount = orders.length;
	const paidOrdersCount = orders.filter(
		(row) =>
			String(row?.payment_status || "")
				.trim()
				.toLowerCase() === "paid",
	).length;
	const unpaidOrdersCount = Math.max(ordersCount - paidOrdersCount, 0);
	const avgTicket = ordersCount ? totalSpent / ordersCount : 0;
	const paidRate = ordersCount ? (paidOrdersCount * 100) / ordersCount : 0;

	const productGrouped = new Map();
	const channelGrouped = new Map();
	for (const order of orders) {
		const channel = String(order?.channel || "").trim() || "unknown";
		const channelBucket = channelGrouped.get(channel) || { channel, orders: 0, sales: 0 };
		channelBucket.orders += 1;
		channelBucket.sales += Number(order?.grand_total || 0);
		channelGrouped.set(channel, channelBucket);

		for (const item of Array.isArray(order?.items) ? order.items : []) {
			const title = String(item?.title || "").trim() || "بدون نام";
			const bucket = productGrouped.get(title) || {
				product_title: title,
				qty: 0,
				amount: 0,
			};
			bucket.qty += Number(item?.qty || 0);
			bucket.amount += Number(item?.line_total || 0);
			productGrouped.set(title, bucket);
		}
	}

	const topProducts = Array.from(productGrouped.values())
		.sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
		.slice(0, 20);
	const channelRows = Array.from(channelGrouped.values()).sort(
		(a, b) => Number(b.sales || 0) - Number(a.sales || 0),
	);
	const recentOrders = orders.slice(0, 40).map((row) => ({
		order_code: row?.order_code || row?.name || "",
		status: row?.status || "",
		payment_status: row?.payment_status || "",
		channel: row?.channel || "",
		grand_total: Number(row?.grand_total || 0),
		created_at: row?.created_at || "",
	}));

	return {
		meta: {
			date_from,
			date_to,
			compare_mode: "none",
		},
		kpis: [
			{
				key: "customer_sales",
				label: "کل خرید",
				value: totalSpent,
				unit: "money",
				trend: "flat",
				change_pct: 0,
			},
			{
				key: "customer_orders",
				label: "تعداد سفارش",
				value: ordersCount,
				unit: "count",
				trend: "flat",
				change_pct: 0,
			},
			{
				key: "customer_avg_ticket",
				label: "میانگین فاکتور",
				value: avgTicket,
				unit: "money",
				trend: "flat",
				change_pct: 0,
			},
			{
				key: "customer_paid_rate",
				label: "نرخ سفارش پرداخت شده",
				value: Number(paidRate.toFixed(2)),
				unit: "percent",
				trend: "flat",
				change_pct: 0,
			},
		],
		charts: [],
		tables: [
			{
				key: "recent-orders",
				title: "آخرین سفارش‌ها",
				columns: [
					{ key: "order_code", label: "کد سفارش" },
					{ key: "status", label: "وضعیت" },
					{ key: "payment_status", label: "پرداخت" },
					{ key: "channel", label: "کانال" },
					{ key: "grand_total", label: "مبلغ", type: "money" },
					{ key: "created_at", label: "تاریخ" },
				],
				rows: recentOrders,
			},
			{
				key: "top-products",
				title: "محصولات پرتکرار",
				columns: [
					{ key: "product_title", label: "محصول" },
					{ key: "qty", label: "تعداد" },
					{ key: "amount", label: "مبلغ", type: "money" },
				],
				rows: topProducts,
			},
			{
				key: "channels",
				title: "خلاصه کانال‌ها",
				columns: [
					{ key: "channel", label: "کانال" },
					{ key: "orders", label: "تعداد سفارش" },
					{ key: "sales", label: "فروش", type: "money" },
				],
				rows: channelRows,
			},
		],
		insights: [
			{
				type: "info",
				text: `سفارش پرداخت شده: ${paidOrdersCount} | پرداخت نشده: ${unpaidOrdersCount}`,
			},
			{ type: "info", text: `بازه گزارش: ${date_from || "-"} تا ${date_to || "-"}` },
		],
	};
}

async function getManagementCustomerDetailFallback({
	mobile = "",
	customer_name = "",
	date_from = "",
	date_to = "",
} = {}) {
	const normalizedMobile = String(mobile || "").trim();
	const normalizedCustomerName = String(customer_name || "").trim();
	const payload = await callRestaurantAPI("list_management_orders", {
		date_from,
		date_to,
		source: "all",
	});
	const rows = Array.isArray(payload?.orders) ? payload.orders : [];
	const matchedOrders = rows
		.filter((row) => isLegacyCustomerMatch(row, normalizedMobile, normalizedCustomerName))
		.filter((row) => isLegacyRevenueOrder(row))
		.sort((left, right) => getOrderTimestamp(right) - getOrderTimestamp(left));

	const firstOrder = matchedOrders.length ? matchedOrders[matchedOrders.length - 1] : null;
	const lastOrder = matchedOrders.length ? matchedOrders[0] : null;
	const resolvedName =
		normalizedCustomerName || normalizeCustomerLabel(lastOrder || firstOrder || {});
	const resolvedMobile =
		normalizedMobile || normalizeCustomerMobile(lastOrder || firstOrder || {});
	const totalSpent = matchedOrders.reduce((sum, row) => sum + Number(row?.grand_total || 0), 0);
	const ordersCount = matchedOrders.length;
	const avgTicket = ordersCount ? totalSpent / ordersCount : 0;
	const paidOrdersCount = matchedOrders.filter(
		(row) =>
			String(row?.payment_status || "")
				.trim()
				.toLowerCase() === "paid",
	).length;
	const unpaidOrdersCount = Math.max(ordersCount - paidOrdersCount, 0);
	const daysSinceLastOrder = lastOrder
		? Math.max(0, Math.floor((Date.now() - getOrderTimestamp(lastOrder)) / 86400000))
		: 0;

	return {
		customer: {
			customer_name: resolvedName || "مشتری",
			mobile: resolvedMobile,
			orders_count: ordersCount,
			total_spent: totalSpent,
			avg_ticket: avgTicket,
			paid_orders_count: paidOrdersCount,
			unpaid_orders_count: unpaidOrdersCount,
			first_order_at: firstOrder?.created_at || "",
			last_order_at: lastOrder?.created_at || "",
			days_since_last_order: daysSinceLastOrder,
		},
		orders: matchedOrders,
		report: buildLegacyCustomerReport(matchedOrders, { date_from, date_to }),
	};
}

export async function getManagementCustomerDetail({
	mobile = "",
	customer_name = "",
	date_from = "",
	date_to = "",
} = {}) {
	const args = { mobile, customer_name, date_from, date_to };
	try {
		return await callRestaurantAPI("get_management_customer_detail", args);
	} catch (error) {
		if (!isMissingCustomerDetailMethodError(error)) {
			throw error;
		}
		return getManagementCustomerDetailFallback(args);
	}
}

export function getManagementReportSalesSummary({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_sales_summary", { date_from, date_to });
}

export function getManagementReportSalesTrend({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_sales_trend", { date_from, date_to });
}

export function getManagementReportSalesHourly({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_sales_hourly", { date_from, date_to });
}

export function getManagementReportTopProducts({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_top_products", { date_from, date_to });
}

export function getManagementReportProductMix({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_product_mix", { date_from, date_to });
}

export function getManagementReportOrderStatus({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_order_status", { date_from, date_to });
}

export function getManagementReportChannelSplit({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_channel_split", { date_from, date_to });
}

export function getManagementReportCashierPerformance({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_cashier_performance", { date_from, date_to });
}

export function getManagementReportCancellations({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_cancellations", { date_from, date_to });
}

export function getManagementReportModifierUsage({ date_from = "", date_to = "" } = {}) {
	return callRestaurantAPI("get_management_report_modifier_usage", { date_from, date_to });
}

export function listManagementPrintFormats({ search = "", doc_type = "", blank_only = 0 } = {}) {
	return callRestaurantAPI("list_management_print_formats", { search, doc_type, blank_only });
}

export function getManagementPrintFormatPreview({ print_format_name = "", doc_type = "" } = {}) {
	return callRestaurantAPI("get_management_print_format_preview", {
		print_format_name,
		doc_type,
	});
}

// ─── Product Builder API helpers ──────────────────────────────────────

export async function getBuilderTemplate(itemCode) {
	return callMethodByPathGET("restaurant.api.get_builder_template", { item_code: itemCode });
}

export async function computeBuilderPrice(itemCode, selections) {
	return callMethodByPath("restaurant.api.compute_builder_price", {
		item_code: itemCode,
		selections: typeof selections === "string" ? selections : JSON.stringify(selections),
	});
}

export async function saveBuilderSelection(payload) {
	return callMethodByPath("restaurant.api.save_builder_selection", payload);
}

// ─── Customer Login API helpers ───────────────────────────────────────

export async function customerSendOTP(mobile) {
	return callRestaurantAPI("customer_send_otp", { mobile });
}

export async function customerVerifyOTP(mobile, code) {
	return callRestaurantAPI("customer_verify_otp", { mobile, code });
}

export async function customerLoginPassword(mobile, password) {
	return callMethodByPath("restaurant.api.customer_login_password", { mobile, password });
}

export async function customerLogout() {
	return callMethodByPath("restaurant.api.customer_logout", {});
}

export async function customerSession() {
	return callMethodByPathGET("restaurant.api.customer_session", {});
}

// ── Zarinpal Settings API ──────────────────────────────────

export async function getZarinpalSettings() {
	return callRestaurantAPI("get_zarinpal_settings");
}

export async function saveZarinpalSettings(payload = {}) {
	return callRestaurantAPI("save_zarinpal_settings", { payload });
}

export async function testZarinpalConnection(payload = {}) {
	return callRestaurantAPI("test_zarinpal_connection", { payload });
}
