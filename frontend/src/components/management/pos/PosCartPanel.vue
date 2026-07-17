<template>
	<section class="cart-panel">
		<!-- Order Mode Segmented Control -->
		<nav class="mode-seg" role="tablist">
			<button
				v-for="mode in orderModes"
				:key="mode.value"
				type="button"
				role="tab"
				:aria-selected="orderMode === mode.value"
				:class="{ active: orderMode === mode.value }"
				@click="$emit('update:orderMode', mode.value)"
			>
				{{ mode.label }}
			</button>
		</nav>

		<!-- Place Selector -->
		<div class="place-field" v-if="normalizedPlaceOptions.length > 1">
			<span class="place-label">جایگاه</span>
			<SearchableDropdown
				:model-value="place"
				:options="normalizedPlaceOptions"
				placeholder="انتخاب کنید"
				search-placeholder="جستجوی جایگاه..."
				include-empty-option
				empty-label="انتخاب کنید"
				@update:model-value="$emit('update:place', $event)"
			/>
		</div>

		<!-- Cart -->
		<div class="cart-section">
			<header class="cart-head">
				<h3>سبد خرید</h3>
				<div class="cart-head-actions">
					<button
						v-if="undoLine"
						type="button"
						class="undo-btn"
						:title="`بازگردانی: ${undoLine.title}`"
						@click="$emit('undo-last-line')"
					>↩ {{ undoLine.title }}</button>
					<button type="button" class="clear-btn" @click="$emit('clear-cart')">حذف همه</button>
				</div>
			</header>

			<div class="cart-list" v-if="cartLines.length">
				<article
					v-for="line in cartLines"
					:key="line.line_id"
					class="cart-row"
					:class="{ active: selectedLineId === line.line_id }"
					@click="$emit('update:selectedLineId', line.line_id)"
				>
					<div class="line-main">
						<div class="line-title-row">
							<strong>{{ line.title }}</strong>
							<span class="line-price">{{ formatMoney(rowTotal(line), currency) }}</span>
						</div>
						<small class="line-custom" v-if="canEditCustomization(line)">سفارشی‌سازی فعال</small>
						<ul class="line-custom-list" v-if="customizationSummary(line).length">
							<li v-for="(entry, idx) in customizationSummary(line)" :key="`${line.line_id}-custom-${idx}`">{{ entry }}</li>
						</ul>
						<small class="line-note" v-if="line.note">{{ line.note }}</small>
					</div>
					<div class="line-actions">
						<button v-if="canEditCustomization(line)" type="button" class="act-btn bom" title="ویرایش سفارشی سازی" @click.stop="$emit('edit-line-customization', line)">BOM</button>
						<button type="button" class="act-btn" title="یادداشت" @click.stop="$emit('edit-line-note', line)">Note</button>
						<div class="counter">
							<button type="button" @click.stop="$emit('decrement-line', line)">−</button>
							<span>{{ qtyText(line.qty) }}</span>
							<button type="button" @click.stop="$emit('increment-line', line)">+</button>
						</div>
						<button type="button" class="act-btn remove" title="حذف" @click.stop="$emit('remove-line', line)">×</button>
					</div>
				</article>
			</div>

			<div class="cart-empty" v-else>
				<span class="cart-empty-icon"><ShoppingCart :size="22" :stroke-width="2.1" /></span>
				<p>سبد خرید خالی است</p>
			</div>
		</div>

		<!-- Financial -->
		<div class="fin-section">
			<!-- Discount group: amount + coupon code -->
			<div class="fin-group">
				<div class="fin-row">
					<span class="fin-label">تخفیف</span>
					<div class="fin-control">
						<AmountPercentToggle
							:model-value="financial.discountType === 'percent' ? 'percent' : 'fixed'"
							aria-label="نوع تخفیف"
							@update:model-value="patchFinancial({ discountType: $event === 'percent' ? 'percent' : 'fixed' })"
						/>
						<PersianNumberInput
							:model-value="financial.discountValue"
							input-class="fin-input"
							placeholder="0"
							:min="0"
							@update:model-value="patchFinancial({ discountValue: $event })"
						/>
					</div>
				</div>
				<div class="fin-row">
					<span class="fin-label">کد تخفیف</span>
					<div class="fin-control">
						<input
							class="fin-input"
							:value="financial.couponCode"
							@input="patchFinancial({ couponCode: $event.target.value })"
							placeholder="کد / معرف"
						/>
						<button type="button" class="fin-action-btn" @click="$emit('verify-coupon')">بررسی</button>
					</div>
				</div>
			</div>

			<!-- Service + Tax group -->
			<div class="fin-group">
				<div class="fin-row">
					<span class="fin-label">حق سرویس</span>
					<div class="fin-control">
						<AmountPercentToggle
							:model-value="financial.serviceType === 'percent' ? 'percent' : 'fixed'"
							aria-label="نوع حق سرویس"
							@update:model-value="patchFinancial({ serviceType: $event === 'percent' ? 'percent' : 'fixed' })"
						/>
						<PersianNumberInput
							:model-value="financial.serviceValue"
							input-class="fin-input"
							placeholder="0"
							:min="0"
							@update:model-value="patchFinancial({ serviceValue: $event })"
						/>
					</div>
				</div>
				<div class="fin-row">
					<label class="fin-toggle-label">
						<input
							type="checkbox"
							class="fin-checkbox"
							:checked="Boolean(financial.taxExempt)"
							@change="patchFinancial({ taxExempt: $event.target.checked })"
						/>
						<span class="fin-label">معاف از مالیات</span>
					</label>
					<div class="fin-control">
						<AmountPercentToggle
							:model-value="financial.taxType === 'percent' ? 'percent' : 'fixed'"
							aria-label="نوع مالیات"
							:disabled="Boolean(financial.taxExempt)"
							@update:model-value="patchFinancial({ taxType: $event === 'percent' ? 'percent' : 'fixed' })"
						/>
						<PersianNumberInput
							:model-value="financial.taxValue"
							input-class="fin-input"
							placeholder="ارزش افزوده"
							:min="0"
							:disabled="Boolean(financial.taxExempt)"
							@update:model-value="patchFinancial({ taxValue: $event })"
						/>
					</div>
				</div>
			</div>

			<!-- Note -->
			<div class="fin-note-row">
				<input
					class="fin-note-input"
					:value="note"
					@input="$emit('update:note', $event.target.value)"
					placeholder="یادداشت سفارش..."
				/>
			</div>
		</div>

		<!-- Summary -->
		<div class="summary-box">
			<div class="sum-line">
				<span>جمع کالاها</span>
				<strong>{{ formatMoney(totals.itemsTotal || 0, currency) }}</strong>
			</div>
			<div class="sum-line" v-if="isNonZero(totals.discountAmount)">
				<span>تخفیف</span>
				<strong class="discount">- {{ formatMoney(totals.discountAmount || 0, currency) }}</strong>
			</div>
			<div class="sum-line" v-if="isNonZero(totals.taxAmount)">
				<span>مالیات</span>
				<strong>{{ formatMoney(totals.taxAmount || 0, currency) }}</strong>
			</div>
			<div class="sum-line" v-if="isNonZero(totals.tipAmount)">
				<span>انعام</span>
				<strong>{{ formatMoney(totals.tipAmount || 0, currency) }}</strong>
			</div>
			<div class="sum-line" v-if="isNonZero(totals.serviceAmount)">
				<span>حق سرویس</span>
				<strong>{{ formatMoney(totals.serviceAmount || 0, currency) }}</strong>
			</div>
			<div class="sum-line payable">
				<span>مبلغ قابل پرداخت</span>
				<strong>{{ formatMoney(totals.payableAmount || 0, currency) }}</strong>
			</div>
		</div>

		<!-- Actions -->
		<footer class="checkout-actions">
			<div class="checkout-btns">
				<button
					type="button"
					class="save-btn"
					:disabled="submitting || !cartLines.length"
					@click="$emit('submit-order')"
				>{{ submitting ? "در حال ثبت..." : orderMode === "dine_in" ? "افزودن به میز" : "ثبت سفارش" }}</button>
				<button
					type="button"
					class="pay-btn"
					:disabled="submitting || !cartLines.length || orderMode === 'dine_in'"
					@click="openPaymentPopup"
				>{{ submitting ? "در حال پرداخت..." : orderMode === "dine_in" ? "تسویه از تب میزها" : "تسویه فاکتور" }}</button>
				<button
					type="button"
					class="settle-btn-custom"
					:disabled="submitting || !cartLines.length || orderMode === 'dine_in'"
					@click="openPaymentPopup(null, 'settle')"
				>{{ submitting ? "در حال ثبت..." : "تسویه و تحویل" }}</button>
			</div>
			<button
				type="button"
				class="print-btn"
				:disabled="orderMode === 'dine_in' ? !canPrintTableOrders : !cartLines.length"
				@click="$emit('print-ticket')"
			>{{ orderMode === "dine_in" ? "چاپ تاییدشده‌ها" : "چاپ فاکتور" }}</button>
			<div class="checkout-opts">
				<label>
					<input type="checkbox" :checked="Boolean(financial.printProduction)" @change="patchFinancial({ printProduction: $event.target.checked })" />
					چاپ صورتحساب تولید
				</label>
				<label>
					<input type="checkbox" :checked="Boolean(financial.createNextInvoice)" @change="patchFinancial({ createNextInvoice: $event.target.checked })" />
					ساخت صورتحساب بعدی
				</label>
			</div>
		</footer>
	</section>

	<div v-if="showPaymentPopup" class="pay-popup-backdrop" @click.self="showPaymentPopup = false">
		<section class="pay-popup" dir="rtl">
			<header class="pay-popup-head">
				<div class="pay-popup-title">
					<CreditCard :size="18" :stroke-width="2.2" />
					<h3>تسویه فاکتور</h3>
				</div>
				<button type="button" class="pay-popup-close" @click="showPaymentPopup = false">
					<X :size="16" :stroke-width="2.4" />
				</button>
			</header>

			<div class="pay-total-banner">
				<span>مبلغ قابل پرداخت</span>
				<strong>{{ formatMoney(totals.payableAmount || 0, currency) }}</strong>
			</div>

			<div class="pay-splits">
				<div v-for="(split, idx) in paymentSplits" :key="idx" class="pay-split-row">
					<div class="pay-split-card">
						<div class="pay-split-head">
							<div class="pay-method-preview">
								<component :is="paymentMethodIcon(split.method)" :size="16" :stroke-width="2.2" />
								<span>{{ splitMethodLabel(split) }}</span>
							</div>
							<button
								v-if="paymentSplits.length > 1"
								type="button"
								class="pay-split-remove"
								@click="removeSplit(idx)"
							>
								<X :size="14" :stroke-width="2.4" />
							</button>
						</div>
						<div class="pay-split-controls">
							<select
								class="dark-input pay-method-select"
								:value="split.optionKey"
								@change="updateSplitOption(split, $event.target.value)"
							>
								<option
									v-for="option in paymentOptionList"
									:key="option.key"
									:value="option.key"
								>
									{{ option.label }}
								</option>
							</select>
							<PersianNumberInput
								:model-value="split.amount"
								input-class="pay-amount-input"
								placeholder="مبلغ"
								:min="0"
								show-words
								@update:model-value="split.amount = $event"
							/>
						</div>
						<p v-if="split.method === 'credit'" class="pay-credit-hint">
							این بخش بدون ثبت پرداخت نهایی به صورت اعتباری ذخیره می‌شود.
						</p>
					</div>
				</div>
			</div>

			<button type="button" class="pay-add-split-btn" @click="addSplit">
				<Plus :size="14" :stroke-width="2.5" />
				<span>افزودن روش پرداخت</span>
			</button>

			<div
				class="pay-remaining-row"
				:class="{ zero: isSplitBalanced, over: isSplitOver }"
			>
				<span>{{
					isSplitOver
						? "مازاد پرداختی"
						: isSplitBalanced
							? "تسویه کامل"
							: "باقیمانده"
				}}</span>
				<strong>{{ formatMoney(Math.abs(splitRemaining), currency) }}</strong>
			</div>

			<div class="pay-split-summary" v-if="paymentSplits.length > 1">
				<div
					v-for="(split, idx) in paymentSplits"
					:key="`s-${idx}`"
					class="pay-split-summary-row"
				>
					<span class="pay-split-summary-label">
						<component :is="paymentMethodIcon(split.method)" :size="14" :stroke-width="2.2" />
						<span>{{ splitMethodLabel(split) }}</span>
					</span>
					<span>{{ formatMoney(split.amount || 0, currency) }}</span>
				</div>
			</div>

			<footer class="pay-popup-footer">
				<button type="button" class="pay-cancel-btn" @click="showPaymentPopup = false">
					انصراف
				</button>
				<button
					type="button"
					class="pay-confirm-btn"
					:disabled="splitRemaining > 0.001 || submitting"
					@click="confirmPayment"
				>
					{{ submitting ? "در حال ثبت..." : "تأیید و ثبت پرداخت" }}
				</button>
			</footer>
		</section>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Banknote, CreditCard, FileClock, Plus, ShoppingCart, X, MessageSquare } from "lucide-vue-next";
import SearchableDropdown from "@/components/SearchableDropdown.vue";
import PersianNumberInput from "@/components/PersianNumberInput.vue";
import AmountPercentToggle from "@/components/AmountPercentToggle.vue";
import { formatMoney, formatStatus, toPersianNumber } from "@/utils/format";

function isNonZero(value) {
	const num = Number(value);
	return Number.isFinite(num) && Math.abs(num) > 0.0001;
}

const props = defineProps({
	cartLines: {
		type: Array,
		default: () => [],
	},
	selectedLineId: {
		type: String,
		default: "",
	},
	currency: {
		type: String,
		default: "IRR",
	},
	orderMode: {
		type: String,
		default: "dine_in",
	},
	place: {
		type: String,
		default: "",
	},
	placeOptions: {
		type: Array,
		default: () => [],
	},
	tableOrders: {
		type: Array,
		default: () => [],
	},
	tablePreviewLoading: {
		type: Boolean,
		default: false,
	},
	selectedTableLabel: {
		type: String,
		default: "",
	},
	canPrintTableOrders: {
		type: Boolean,
		default: false,
	},
	note: {
		type: String,
		default: "",
	},
	paymentMethod: {
		type: String,
		default: "cash",
	},
	paymentReference: {
		type: String,
		default: "",
	},
	paymentRrn: {
		type: String,
		default: "",
	},
	paymentBoot: {
		type: Object,
		default: () => ({}),
	},
	paymentOptions: {
		type: Array,
		default: () => [],
	},
	financial: {
		type: Object,
		default: () => ({}),
	},
	totals: {
		type: Object,
		default: () => ({}),
	},
	submitting: {
		type: Boolean,
		default: false,
	},
	undoLine: {
		type: Object,
		default: null,
	},
});

const emit = defineEmits([
	"update:selectedLineId",
	"update:orderMode",
	"update:place",
	"update:note",
	"update:paymentMethod",
	"update:paymentReference",
	"update:paymentRrn",
	"patch-financial",
	"increment-line",
	"decrement-line",
	"remove-line",
	"undo-last-line",
	"edit-line-note",
	"edit-line-customization",
	"clear-cart",
	"submit-order",
	"submit-and-settle",
	"submit-and-pay",
	"print-ticket",
	"verify-credit",
	"verify-coupon",
	"update-table-order-item",
	"print-confirmed-table",
]);

const showPaymentPopup = ref(false);
const paymentPopupIntent = ref("pay");
const paymentSplits = ref([]);
const discountInputRef = ref(null);

const splitTotal = computed(() =>
	paymentSplits.value.reduce((sum, s) => sum + Number(s.amount || 0), 0),
);
const splitRemaining = computed(() => Number(props.totals?.payableAmount || 0) - splitTotal.value);
const isSplitBalanced = computed(() => Math.abs(splitRemaining.value) <= 0.001);
const isSplitOver = computed(() => splitRemaining.value < -0.001);

const orderModes = [
	{ value: "dine_in", label: "سالن" },
	{ value: "takeaway", label: "بیرون بر (مشتری)" },
	{ value: "delivery", label: "بیرون بر (پیک)" },
];

const pendingTableOrders = computed(() =>
	(props.tableOrders || []).filter(
		(order) => String(order.status || "").toLowerCase() === "pending",
	),
);

const confirmedTableOrders = computed(() =>
	(props.tableOrders || []).filter(
		(order) => String(order.status || "").toLowerCase() !== "pending",
	),
);

const normalizedPlaceOptions = computed(() =>
	(props.placeOptions || []).map((option) => ({
		value: option,
		label: option,
	})),
);

const paymentOptionList = computed(() =>
	Array.isArray(props.paymentOptions) && props.paymentOptions.length
		? props.paymentOptions
		: [
				{
					key: "cash:نقدی",
					method: "cash",
					label: "نقدی",
					mode_of_payment: "نقدی",
				},
		  ],
);

const defaultPaymentOption = computed(() => {
	const exactMethod = paymentOptionList.value.find((option) => option.method === props.paymentMethod);
	if (exactMethod) {
		return exactMethod;
	}
	return (
		paymentOptionList.value.find((option) => Boolean(option.default)) ||
		paymentOptionList.value[0] ||
		null
	);
});

watch(
	() => paymentOptionList.value,
	() => {
		paymentSplits.value = paymentSplits.value.map((split) => syncSplitOption(split));
	},
	{ deep: true },
);

function patchFinancial(partial) {
	emit("patch-financial", partial);
}

function resolvePaymentOption(optionKey = "") {
	return paymentOptionList.value.find((option) => option.key === optionKey) || null;
}

function buildSplit(optionKey = "", amount = 0) {
	const option = resolvePaymentOption(optionKey) || defaultPaymentOption.value;
	return {
		optionKey: option?.key || "",
		method: option?.method || "cash",
		mode_of_payment: option?.mode_of_payment || option?.label || "نقدی",
		label: option?.label || "نقدی",
		amount,
	};
}

function syncSplitOption(split = {}) {
	const option = resolvePaymentOption(split.optionKey) || defaultPaymentOption.value;
	if (!option) {
		return {
			optionKey: "",
			method: "cash",
			mode_of_payment: "نقدی",
			label: "نقدی",
			amount: Number(split.amount || 0),
		};
	}
	return {
		...split,
		optionKey: option.key,
		method: option.method,
		mode_of_payment: option.mode_of_payment || option.label,
		label: option.label,
		amount: Number(split.amount || 0),
	};
}

function updateSplitOption(split, optionKey) {
	Object.assign(split, syncSplitOption({ ...split, optionKey }));
}

function openPaymentPopup(preferredMethod = null, intent = "pay") {
	const total = Number(props.totals?.payableAmount || 0);
	const preferredOption =
		paymentOptionList.value.find((option) => option.method === preferredMethod) ||
		paymentOptionList.value.find((option) => option.method === props.paymentMethod) ||
		defaultPaymentOption.value;
	paymentSplits.value = [buildSplit(preferredOption?.key || "", total)];
	paymentPopupIntent.value = intent === "settle" ? "settle" : "pay";
	showPaymentPopup.value = true;
}

function addSplit() {
	const remaining = Math.max(splitRemaining.value, 0);
	paymentSplits.value.push(buildSplit(defaultPaymentOption.value?.key || "", remaining));
}

function removeSplit(idx) {
	paymentSplits.value.splice(idx, 1);
}

function paymentMethodIcon(method) {
	if (method === "card") return CreditCard;
	if (method === "credit") return FileClock;
	return Banknote;
}

function splitMethodLabel(split = {}) {
	return String(split.label || split.mode_of_payment || "").trim() || "نقدی";
}

function confirmPayment() {
	const validSplits = paymentSplits.value
		.map((split) => syncSplitOption(split))
		.filter((s) => Number(s.amount || 0) > 0);
	const primary = validSplits.reduce(
		(a, b) => (Number(b.amount || 0) > Number(a.amount || 0) ? b : a),
		validSplits[0] || buildSplit(defaultPaymentOption.value?.key || "", 0),
	);
	emit("update:paymentMethod", primary.method);
	const payload = {
		splits: validSplits.map((split) => ({
			optionKey: split.optionKey,
			method: split.method,
			mode_of_payment: split.mode_of_payment,
			label: split.label,
			amount: Number(split.amount || 0),
		})),
	};
	if (paymentPopupIntent.value === "settle") {
		emit("submit-and-settle", payload);
	} else {
		emit("submit-and-pay", payload);
	}
	showPaymentPopup.value = false;
	paymentPopupIntent.value = "pay";
}

function rowTotal(line) {
	return Number(line.qty || 0) * Number(line.price || line.unit_price || 0);
}

function qtyText(value) {
	const numeric = Number(value || 0);
	if (!Number.isFinite(numeric)) {
		return "۰";
	}
	if (Math.abs(numeric - Math.round(numeric)) < 0.0001) {
		return toPersianNumber(Math.round(numeric));
	}
	return toPersianNumber(Number(numeric.toFixed(3)), { maximumFractionDigits: 3 });
}

function formatCompactNumber(value, decimals = 2) {
	const parsed = Number(value || 0);
	if (!Number.isFinite(parsed)) {
		return "۰";
	}
	const trimmed = parsed.toFixed(decimals).replace(/\.?0+$/, "");
	return trimmed.includes(".")
		? trimmed.replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)])
		: toPersianNumber(Number(trimmed || 0));
}

function formatDateTime(value) {
	const raw = String(value || "").trim();
	if (!raw) {
		return "-";
	}
	try {
		return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
			month: "2-digit",
			day: "2-digit",
			hour: "2-digit",
			minute: "2-digit",
		}).format(new Date(raw));
	} catch (dateErr) {
		return raw;
	}
}

function ingredientBaseMultiplier(ingredient = {}) {
	return Number(ingredient?.is_included_by_default || 0) === 1 ? 1 : 0;
}

function customizationSummary(line) {
	const customization = line?.customization || {};
	const ingredientMap = new Map(
		(line?.customization_ingredients || [])
			.map((row) => ({
				key: String(row?.key || "").trim(),
				name: String(row?.name || "").trim(),
				customer_label: String(row?.customer_label || "").trim(),
				is_included_by_default: Number(row?.is_included_by_default || 0),
			}))
			.filter((row) => row.key)
			.map((row) => [row.key, row]),
	);
	const lines = [];

	for (const row of customization.ingredient_adjustments || []) {
		const ingredientKey = String(row?.ingredient_key || "").trim();
		if (!ingredientKey) {
			continue;
		}
		const selected = Number(row?.multiplier || 0);
		if (!Number.isFinite(selected)) {
			continue;
		}

		const ingredient = ingredientMap.get(ingredientKey);
		const label = ingredient?.customer_label || ingredient?.name || ingredientKey;
		if (!ingredient) {
			if (selected > 0) {
				lines.push(`• ${label}: x${formatCompactNumber(selected)}`);
			}
			continue;
		}

		const base = ingredientBaseMultiplier(ingredient);
		if (Math.abs(selected - base) < 0.001) {
			continue;
		}
		if (base <= 0 && selected > 0) {
			lines.push(`+ افزودن ${label} x${formatCompactNumber(selected)}`);
			continue;
		}
		if (base > 0 && selected <= 0) {
			lines.push(`- حذف ${label}`);
			continue;
		}
		if (selected > base) {
			lines.push(
				`+ افزایش ${label} (${formatCompactNumber(base)} → ${formatCompactNumber(selected)})`,
			);
		} else {
			lines.push(
				`- کاهش ${label} (${formatCompactNumber(base)} → ${formatCompactNumber(selected)})`,
			);
		}
	}

	for (const row of customization.selected_modifiers || []) {
		const group = String(row?.group || row?.group_name || "").trim();
		const option = String(row?.option || row?.option_name || "").trim();
		if (!group || !option) {
			continue;
		}
		const qty = Math.max(Number(row?.qty || 1), 1);
		lines.push(`+ ${group} / ${option}${qty > 1 ? ` x${formatCompactNumber(qty)}` : ""}`);
	}

	for (const row of customization.selected_alternatives || []) {
		const ingredientKey = String(row?.ingredient_key || "").trim();
		const alternative = String(row?.alternative_item || "").trim();
		if (!ingredientKey || !alternative) {
			continue;
		}
		const ingredient = ingredientMap.get(ingredientKey);
		const label = ingredient?.customer_label || ingredient?.name || ingredientKey;
		lines.push(`↺ جایگزین ${label} با ${alternative}`);
	}

	return lines;
}

function canEditCustomization(line) {
	const customization = line?.customization || {};
	return Boolean(
		line?.has_customization ||
		line?.variant_of ||
		Number((line?.customization_ingredients || []).length || 0) > 0 ||
		Number((customization.ingredient_adjustments || []).length || 0) > 0 ||
		Number((customization.selected_modifiers || []).length || 0) > 0 ||
		Number((customization.selected_alternatives || []).length || 0) > 0,
	);
}

function focusDiscountInput() {
	discountInputRef.value?.focus();
	discountInputRef.value?.select?.();
}

defineExpose({
	focusDiscountInput,
	openPaymentPopup,
});
</script>

<style scoped>
/* ─── Panel Shell ─── */
.cart-panel {
	border-radius: 16px;
	background: var(--mg-bg-surface);
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.1);
	padding: 0;
	color: var(--mg-text-main);
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

/* ─── Segmented Control ─── */
.mode-seg {
	display: flex;
	gap: 2px;
	padding: 0.5rem 0.65rem 0;
	background: transparent;
}

.mode-seg button {
	flex: 1;
	border: none;
	background: rgb(var(--pos-primary-rgb) / 0.06);
	color: rgb(var(--pos-primary-rgb) / 0.6);
	padding: 0.5rem 0.25rem;
	font-size: 0.78rem;
	font-weight: 500;
	font-family: inherit;
	cursor: pointer;
	transition: all 0.2s ease;
	position: relative;
}

.mode-seg button:first-child {
	border-radius: 0 10px 10px 0;
}

.mode-seg button:last-child {
	border-radius: 10px 0 0 10px;
}

.mode-seg button:not(:first-child):not(:last-child) {
	border-radius: 0;
}

.mode-seg button.active {
	background: var(--pos-primary);
	color: var(--mg-bg-surface);
	font-weight: 700;
	box-shadow: 0 2px 8px rgb(var(--pos-primary-rgb) / 0.25);
}

.mode-seg button:not(.active):hover {
	background: rgb(var(--pos-primary-rgb) / 0.1);
	color: var(--pos-primary);
}

/* ─── Place Field ─── */
.place-field {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0.45rem 0.65rem;
	border-bottom: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
}

.place-label {
	font-size: 0.74rem;
	font-weight: 600;
	color: rgb(var(--pos-primary-rgb) / 0.55);
	flex-shrink: 0;
}

/* ─── Cart Section ─── */
.cart-section {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.cart-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.55rem 0.65rem 0.35rem;
}

.cart-head h3 {
	margin: 0;
	font-size: 0.82rem;
	font-weight: 700;
	color: var(--pos-primary);
}

.cart-head-actions {
	display: flex;
	align-items: center;
	gap: 0.35rem;
}

.undo-btn {
	background: none;
	border: 1px solid rgb(var(--pos-accent-rgb) / 0.3);
	color: var(--pos-accent);
	border-radius: 6px;
	font-size: 0.68rem;
	font-family: inherit;
	padding: 0.18rem 0.5rem;
	cursor: pointer;
	max-width: 9rem;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	transition: all 0.15s ease;
}

.undo-btn:hover {
	background: var(--pos-accent);
	border-color: var(--pos-accent);
	color: var(--mg-bg-surface);
}

.clear-btn {
	background: none;
	border: none;
	color: rgb(var(--pos-primary-rgb) / 0.4);
	font-size: 0.72rem;
	font-family: inherit;
	cursor: pointer;
	padding: 0.2rem 0.35rem;
	border-radius: 6px;
	transition: all 0.15s ease;
}

.clear-btn:hover {
	color: var(--pos-danger);
	background: rgb(var(--pos-danger-rgb) / 0.08);
}

/* ─── Cart List ─── */
.cart-list {
	display: flex;
	flex-direction: column;
	gap: 3px;
	overflow-y: auto;
	scrollbar-width: thin;
	padding: 0 0.45rem 0.35rem;
	flex: 1;
	min-height: 0;
}

.cart-row {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 0.4rem;
	padding: 0.5rem 0.55rem;
	border-radius: 10px;
	background: rgb(var(--pos-primary-rgb) / 0.025);
	cursor: pointer;
	transition: all 0.15s ease;
	border: 1.5px solid transparent;
}

.cart-row:hover {
	background: rgb(var(--pos-primary-rgb) / 0.05);
}

.cart-row.active {
	background: rgb(var(--pos-primary-rgb) / 0.06);
	border-color: rgb(var(--pos-primary-rgb) / 0.18);
}

.line-main {
	display: flex;
	flex-direction: column;
	gap: 2px;
	min-width: 0;
}

.line-title-row {
	display: flex;
	align-items: baseline;
	gap: 0.4rem;
}

.line-title-row strong {
	font-size: 0.78rem;
	font-weight: 600;
	color: var(--mg-text-main);
}

.line-price {
	font-size: 0.72rem;
	color: rgb(var(--pos-primary-rgb) / 0.55);
	font-weight: 500;
	flex-shrink: 0;
}

.line-custom {
	font-size: 0.66rem;
	color: rgb(var(--pos-primary-rgb) / 0.5);
	font-style: italic;
}

.line-custom-list {
	margin: 0;
	padding-right: 0.6rem;
	color: rgb(var(--pos-primary-rgb) / 0.55);
	font-size: 0.66rem;
	line-height: 1.5;
	display: flex;
	flex-direction: column;
	gap: 1px;
}

.line-custom-list li {
	list-style: none;
}

.line-note {
	font-size: 0.66rem;
	color: var(--pos-accent);
}

.line-actions {
	display: flex;
	align-items: center;
	gap: 3px;
	flex-shrink: 0;
}

.act-btn {
	width: 26px;
	height: 26px;
	border: none;
	background: rgb(var(--pos-primary-rgb) / 0.06);
	color: rgb(var(--pos-primary-rgb) / 0.6);
	border-radius: 7px;
	cursor: pointer;
	font-size: 0.78rem;
	font-family: inherit;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.12s ease;
	padding: 0;
}

.act-btn:hover {
	background: rgb(var(--pos-primary-rgb) / 0.12);
	color: var(--pos-primary);
}

.act-btn.bom {
	width: auto;
	padding: 0 0.35rem;
	font-size: 0.62rem;
	font-weight: 700;
	color: var(--pos-accent);
	background: rgb(var(--pos-accent-rgb) / 0.08);
}

.act-btn.bom:hover {
	background: rgb(var(--pos-accent-rgb) / 0.18);
}

.act-btn.remove {
	color: rgb(var(--pos-danger-rgb) / 0.5);
}

.act-btn.remove:hover {
	background: rgb(var(--pos-danger-rgb) / 0.1);
	color: var(--pos-danger);
}

.counter {
	display: inline-flex;
	align-items: center;
	background: rgb(var(--pos-primary-rgb) / 0.04);
	border-radius: 8px;
	overflow: hidden;
}

.counter button {
	width: 26px;
	height: 26px;
	border: none;
	background: transparent;
	color: var(--pos-primary);
	cursor: pointer;
	font-size: 0.88rem;
	font-weight: 600;
	font-family: inherit;
	transition: background 0.12s ease;
}

.counter button:hover {
	background: rgb(var(--pos-primary-rgb) / 0.1);
}

.counter span {
	min-width: 32px;
	text-align: center;
	font-size: 0.76rem;
	font-weight: 600;
	color: var(--mg-text-main);
}

/* ─── Empty State ─── */
.cart-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 2rem 1rem;
	flex: 1;
}

.cart-empty-icon {
	font-size: 1.6rem;
	opacity: 0.25;
	margin-bottom: 0.5rem;
}

.cart-empty p {
	margin: 0;
	font-size: 0.78rem;
	color: rgb(var(--pos-primary-rgb) / 0.35);
}

/* ─── Financial Section ─── */
.fin-section {
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
	padding: 0.5rem 0.65rem;
	display: flex;
	flex-direction: column;
	gap: 0.45rem;
}

.fin-group {
	display: flex;
	flex-direction: column;
	gap: 0;
	background: rgb(var(--pos-primary-rgb) / 0.02);
	border-radius: 10px;
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
	overflow: hidden;
}

.fin-group .fin-row + .fin-row {
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.05);
}

.fin-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	padding: 0.38rem 0.55rem;
	min-height: 36px;
}

.fin-label {
	font-size: 0.72rem;
	color: rgb(var(--pos-primary-rgb) / 0.55);
	font-weight: 600;
	white-space: nowrap;
	flex-shrink: 0;
}

.fin-toggle-label {
	display: inline-flex;
	align-items: center;
	gap: 0.35rem;
	cursor: pointer;
}

.fin-checkbox {
	width: 14px;
	height: 14px;
	accent-color: var(--pos-primary);
	cursor: pointer;
	flex-shrink: 0;
}

.fin-control {
	display: flex;
	align-items: center;
	gap: 0.3rem;
	flex-shrink: 0;
	max-width: 170px;
}

.fin-input {
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.1);
	background: rgb(var(--pos-primary-rgb) / 0.03);
	color: var(--mg-text-main);
	border-radius: 8px;
	padding: 0.32rem 0.5rem;
	font-size: 0.74rem;
	font-family: inherit;
	width: 100%;
	min-width: 0;
	height: 30px;
	outline: none;
	transition: all 0.15s ease;
}

.fin-input:focus {
	border-color: rgb(var(--pos-primary-rgb) / 0.3);
	background: var(--mg-bg-surface);
	box-shadow: 0 0 0 2px rgb(var(--pos-primary-rgb) / 0.06);
}

.fin-input:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}

.fin-action-btn {
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	background: rgb(var(--pos-primary-rgb) / 0.05);
	color: var(--pos-primary);
	font-size: 0.7rem;
	font-weight: 600;
	cursor: pointer;
	flex-shrink: 0;
	transition: all 0.15s ease;
	font-family: inherit;
	white-space: nowrap;
	border-radius: 8px;
	padding: 0.32rem 0.6rem;
	height: 30px;
}

.fin-action-btn:hover {
	background: rgb(var(--pos-primary-rgb) / 0.1);
}

.fin-note-row {
	margin-top: 0.1rem;
}

.fin-note-input {
	width: 100%;
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.08);
	background: rgb(var(--pos-primary-rgb) / 0.02);
	color: var(--mg-text-main);
	border-radius: 8px;
	padding: 0.35rem 0.55rem;
	font-size: 0.72rem;
	font-family: inherit;
	height: 30px;
	outline: none;
	transition: all 0.15s ease;
}

.fin-note-input::placeholder {
	color: rgb(var(--pos-primary-rgb) / 0.3);
}

.fin-note-input:focus {
	border-color: rgb(var(--pos-primary-rgb) / 0.25);
	background: var(--mg-bg-surface);
	box-shadow: 0 0 0 2px rgb(var(--pos-primary-rgb) / 0.05);
}

/* ─── Summary ─── */
.summary-box {
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
	padding: 0.5rem 0.65rem;
	display: flex;
	flex-direction: column;
	gap: 0.22rem;
}

.sum-line {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: 0.74rem;
	color: rgb(var(--pos-primary-rgb) / 0.55);
}

.sum-line strong {
	font-weight: 600;
	color: var(--mg-text-main);
}

.sum-line strong.discount {
	color: var(--pos-success);
}

.sum-line.payable {
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.08);
	margin-top: 0.25rem;
	padding-top: 0.4rem;
	font-size: 0.84rem;
	color: var(--mg-text-main);
	font-weight: 500;
}

.sum-line.payable strong {
	font-size: 0.92rem;
	font-weight: 800;
	color: var(--pos-primary);
}

/* ─── Checkout Actions ─── */
.checkout-actions {
	padding: 0.5rem 0.65rem 0.6rem;
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
	display: flex;
	flex-direction: column;
	gap: 0.4rem;
}

.checkout-btns {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.35rem;
}

.save-btn,
.pay-btn,
.print-btn {
	border: 0;
	border-radius: 10px;
	color: var(--mg-bg-surface);
	padding: 0.55rem 0.5rem;
	cursor: pointer;
	font-family: inherit;
	font-size: 0.78rem;
	font-weight: 700;
	transition: all 0.15s ease;
}

.save-btn {
	background: var(--pos-primary);
}

.save-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px rgb(var(--pos-primary-rgb) / 0.3);
}

.settle-btn-custom {
	background: var(--mg-success);
	color: var(--mg-bg-surface);
	border: none;
	padding: 12px 16px;
	border-radius: 10px;
	font-size: 13px;
	font-weight: 600;
	cursor: pointer;
	white-space: nowrap;
	flex: 1;
	min-width: 0;
	transition: all 0.15s;
}
.settle-btn-custom:hover:not(:disabled) {
	background: var(--mg-success);
}
.settle-btn-custom:disabled {
	background: var(--mg-success-bg);
	cursor: not-allowed;
	opacity: 0.6;
}

.pay-btn {
	background: var(--pos-accent);
}

.pay-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px rgb(var(--pos-accent-rgb) / 0.3);
}

.print-btn {
	background: transparent;
	color: rgb(var(--pos-primary-rgb) / 0.55);
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	font-weight: 600;
}

.print-btn:hover:not(:disabled) {
	background: rgb(var(--pos-primary-rgb) / 0.06);
	color: var(--pos-primary);
	border-color: rgb(var(--pos-primary-rgb) / 0.2);
}

.save-btn:disabled,
.pay-btn:disabled,
.print-btn:disabled {
	opacity: 0.35;
	cursor: not-allowed;
	box-shadow: none;
}

.checkout-opts {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.checkout-opts label {
	display: inline-flex;
	align-items: center;
	gap: 0.3rem;
	font-size: 0.68rem;
	color: rgb(var(--pos-primary-rgb) / 0.45);
	cursor: pointer;
	transition: color 0.12s;
}

.checkout-opts label:hover {
	color: rgb(var(--pos-primary-rgb) / 0.7);
}

.checkout-opts input[type="checkbox"] {
	width: 13px;
	height: 13px;
	accent-color: var(--pos-primary);
	cursor: pointer;
}

/* ─── Responsive ─── */
@media (max-width: 980px) {
	.cart-panel {
		max-height: none;
	}
}

/* ─── Payment Popup ─── */
.pay-popup-backdrop {
	position: fixed;
	inset: 0;
	z-index: 300;
	background: rgb(0 0 0 / 0.45);
	backdrop-filter: blur(4px);
	display: grid;
	place-items: center;
	padding: 1rem;
}

.pay-popup {
	background: var(--mg-bg-surface);
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	border-radius: 20px;
	width: min(520px, calc(100vw - 2rem));
	max-height: min(760px, calc(100dvh - 2rem));
	overflow: auto;
	box-shadow: 0 24px 60px rgb(15 23 42 / 0.22);
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
	padding: 1.15rem;
	color: var(--mg-text-main);
}

.pay-popup-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.pay-popup-title {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	color: var(--pos-primary);
}

.pay-popup-head h3 {
	margin: 0;
	font-size: 0.95rem;
	font-weight: 800;
	color: var(--pos-primary);
}

.pay-popup-close {
	width: 2rem;
	height: 2rem;
	border: none;
	border-radius: 8px;
	background: rgb(var(--pos-primary-rgb) / 0.06);
	color: rgb(var(--pos-primary-rgb) / 0.5);
	font-size: 1.1rem;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.12s ease;
}

.pay-popup-close:hover {
	background: rgb(var(--pos-primary-rgb) / 0.12);
	color: var(--mg-text-main);
}

.pay-total-banner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: rgb(var(--pos-primary-rgb) / 0.04);
	border-radius: 12px;
	padding: 0.7rem 0.85rem;
	font-size: 0.8rem;
	color: rgb(var(--pos-primary-rgb) / 0.6);
}

.pay-total-banner strong {
	font-size: 1.05rem;
	font-weight: 800;
	color: var(--pos-primary);
}

.pay-splits {
	display: flex;
	flex-direction: column;
	gap: 0.55rem;
}

.pay-split-row {
	display: block;
}

.pay-split-card {
	display: flex;
	flex-direction: column;
	gap: 0.65rem;
	padding: 0.8rem;
	border-radius: 14px;
	background: rgb(var(--pos-primary-rgb) / 0.03);
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.08);
}

.pay-split-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.75rem;
}

.pay-method-preview {
	display: inline-flex;
	align-items: center;
	gap: 0.45rem;
	font-size: 0.82rem;
	font-weight: 700;
	color: var(--pos-primary);
}

.pay-split-controls {
	display: grid;
	grid-template-columns: minmax(0, 190px) minmax(0, 1fr);
	gap: 0.55rem;
	align-items: start;
}

.pay-method-select {
	border-radius: 9px;
	padding: 0.6rem 0.7rem;
	font-size: 0.78rem;
	min-width: 0;
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	background: rgb(var(--pos-primary-rgb) / 0.03);
	color: var(--mg-text-main);
	font-family: inherit;
	height: 44px;
}

.pay-amount-input {
	border-radius: 9px;
	padding: 0.6rem 0.7rem;
	font-size: 0.85rem;
	text-align: left;
	min-height: 44px;
}

.pay-split-remove {
	width: 26px;
	height: 26px;
	border: none;
	border-radius: 7px;
	background: rgb(var(--pos-danger-rgb) / 0.08);
	color: var(--pos-danger);
	font-size: 0.95rem;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	transition: background 0.12s ease;
}

.pay-credit-hint {
	margin: 0;
	font-size: 0.74rem;
	line-height: 1.6;
	color: rgb(var(--pos-primary-rgb) / 0.62);
	background: rgb(var(--pos-accent-rgb) / 0.08);
	border-radius: 10px;
	padding: 0.5rem 0.65rem;
}

.pay-split-remove:hover {
	background: rgb(var(--pos-danger-rgb) / 0.15);
}

.pay-add-split-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.4rem;
	border: 1px dashed rgb(var(--pos-primary-rgb) / 0.15);
	border-radius: 10px;
	background: transparent;
	color: rgb(var(--pos-primary-rgb) / 0.5);
	font-size: 0.76rem;
	font-family: inherit;
	padding: 0.42rem;
	cursor: pointer;
	transition: all 0.15s ease;
}

.pay-add-split-btn:hover {
	background: rgb(var(--pos-primary-rgb) / 0.04);
	color: var(--pos-primary);
	border-color: rgb(var(--pos-primary-rgb) / 0.25);
}

.pay-remaining-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.55rem 0.75rem;
	border-radius: 10px;
	background: rgb(var(--pos-accent-rgb) / 0.08);
	font-size: 0.8rem;
	font-weight: 600;
	color: var(--pos-accent);
	transition: all 0.2s ease;
}

.pay-remaining-row.zero {
	background: rgb(var(--pos-success-rgb) / 0.08);
	color: var(--pos-success);
}

.pay-remaining-row.over {
	background: rgb(var(--pos-danger-rgb) / 0.08);
	color: var(--pos-danger);
}

.pay-split-summary {
	border-top: 1px solid rgb(var(--pos-primary-rgb) / 0.06);
	padding-top: 0.45rem;
	display: flex;
	flex-direction: column;
	gap: 0.25rem;
}

.pay-split-summary-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: 0.76rem;
	color: rgb(var(--pos-primary-rgb) / 0.55);
}

.pay-split-summary-label {
	display: inline-flex;
	align-items: center;
	gap: 0.35rem;
}

.pay-popup-footer {
	display: grid;
	grid-template-columns: 1fr 2fr;
	gap: 0.4rem;
	padding-top: 0.15rem;
}

.pay-cancel-btn {
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	background: transparent;
	color: rgb(var(--pos-primary-rgb) / 0.6);
	border-radius: 10px;
	padding: 0.6rem;
	cursor: pointer;
	font-size: 0.82rem;
	font-family: inherit;
	transition: all 0.12s ease;
}

.pay-cancel-btn:hover {
	background: rgb(var(--pos-primary-rgb) / 0.05);
	color: var(--mg-text-main);
}

.pay-confirm-btn {
	border: 0;
	border-radius: 10px;
	background: var(--pos-primary);
	color: var(--mg-bg-surface);
	padding: 0.6rem;
	cursor: pointer;
	font-size: 0.82rem;
	font-weight: 700;
	font-family: inherit;
	transition: all 0.15s ease;
}

.pay-confirm-btn:hover:not(:disabled) {
	box-shadow: 0 4px 14px rgb(var(--pos-primary-rgb) / 0.3);
}

.pay-confirm-btn:disabled {
	opacity: 0.4;
	cursor: not-allowed;
}

.dark-input {
	border: 1px solid rgb(var(--pos-primary-rgb) / 0.12);
	background: rgb(var(--pos-primary-rgb) / 0.03);
	color: var(--mg-text-main);
}

.dark-input::placeholder {
	color: rgb(var(--pos-primary-rgb) / 0.35);
}

@media (max-width: 640px) {
	.pay-popup {
		width: min(100vw - 1rem, 100%);
		padding: 1rem;
		border-radius: 18px;
	}

	.pay-split-controls {
		grid-template-columns: 1fr;
	}

	.pay-popup-footer {
		grid-template-columns: 1fr;
	}
}
</style>
