const STATUS_LABELS = {
	new: "جدید",
	pending: "در انتظار تایید",
	confirmed: "تایید شده",
	preparing: "در حال آماده سازی",
	ready: "آماده تحویل",
	courier_handoff: "تحویل پیک شد",
	on_the_way: "در مسیر",
	served: "سرو شد",
	paid: "پرداخت شد",
	done: "انجام شد",
	delivered: "تحویل شده",
	cancelled: "لغو شده",
	occupied: "اشغال",
	empty: "خالی",
	waiting: "در انتظار",
	active: "فعال",
	closed: "بسته",
};

export function formatMoney(value, currency = "IRR") {
	const numeric = Number(value || 0);
	const normalizedCurrency = String(currency || "")
		.trim()
		.toUpperCase();
	const isToman = normalizedCurrency === "TOMAN";
	const displayValue = isToman ? numeric / 10 : numeric;
	const hasFraction = Math.abs(displayValue - Math.round(displayValue)) > 1e-8;
	const formattedRaw = new Intl.NumberFormat("fa-IR", {
		maximumFractionDigits: isToman ? (hasFraction ? 1 : 0) : 0,
	}).format(isToman ? displayValue : Math.round(displayValue));
	const formatted = formattedRaw.replace(/[٬,]/g, ".");
	const unit = isToman ? "تومان" : normalizedCurrency === "IRR" ? "ریال" : currency;
	return `${formatted} ${unit}`;
}

export function toPersianNumber(value, options = {}) {
	const numeric = Number(value || 0);
	if (!Number.isFinite(numeric)) {
		return "۰";
	}
	return numeric.toLocaleString("fa-IR", options);
}

export function formatStatus(status) {
	return STATUS_LABELS[status] || status || "-";
}

export function normalizeMobile(value) {
	return String(value || "")
		.replace(/[^\d]/g, "")
		.trim();
}

export function parseQuery() {
	const params = new URLSearchParams(window.location.search || "");
	const result = {};
	for (const [key, val] of params.entries()) {
		result[key] = val;
	}
	return result;
}
