// API client for the per-company page layout endpoints.
//
// These call the whitelisted methods in restaurant/page_layout.py by full
// path, mirroring how the rest of the app calls frappe.client.* helpers.

import { callMethodByPath } from "@/utils/api";

const BASE = "restaurant.page_layout";

const LOCAL_KEY = "restaurant_page_layout_local_v1";

function cacheLocal(page, result) {
	try {
		const store = JSON.parse(localStorage.getItem(LOCAL_KEY) || "{}");
		store[page] = result;
		localStorage.setItem(LOCAL_KEY, JSON.stringify(store));
	} catch (_) {}
}

function readLocal(page) {
	try {
		const store = JSON.parse(localStorage.getItem(LOCAL_KEY) || "{}");
		return store[page] || null;
	} catch (_) {
		return null;
	}
}

export async function getManagementPageLayout(page = "home", company = "") {
	try {
		const result = await callMethodByPath(`${BASE}.get_management_page_layout`, {
			page,
			company: company || undefined,
		});
		if (result) cacheLocal(page, result);
		return result || { page, blocks: [], company };
	} catch (error) {
		const cached = readLocal(page);
		if (cached) return cached;
		throw error;
	}
}

export async function setManagementPageLayout(payload = {}, company = "") {
	const page = String(payload.page || "home").trim() || "home";
	const body = {
		payload: JSON.stringify({ page, blocks: payload.blocks || [] }),
		company: company || undefined,
	};
	const result = await callMethodByPath(`${BASE}.set_management_page_layout`, body);
	if (result) cacheLocal(page, result);
	return result;
}

export async function resetManagementPageLayout(page = "home", company = "") {
	const result = await callMethodByPath(`${BASE}.reset_management_page_layout`, {
		page,
		company: company || undefined,
	});
	cacheLocal(page, result);
	return result;
}
