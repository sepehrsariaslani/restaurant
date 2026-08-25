<template>
	<div class="section" :class="{ 'is-compact': compact }">
		<h3>سایز و افزودنی‌ها</h3>

		<div class="groups" v-if="groups.length">
			<section class="group" v-for="group in groups" :key="group.group_name">
				<header class="group-head">
					<div>
						<h4>{{ group.title }}</h4>
						<small>
							{{ formatNumber(group.min_select) }} تا {{ formatNumber(group.max_select) }}
							<span v-if="Number(group.required) === 1">(اجباری)</span>
						</small>
					</div>
				</header>

				<div class="single-options" v-if="rendersSingleChoiceOptions(group)">
					<button
						v-if="Number(group.required) !== 1"
						type="button"
						class="option-choice clear-option"
						:class="{ active: !singleValue(group.group_name) }"
						@click="selectSingleChoice(group, '')"
					>
						<span class="choice-main">
							<span class="indicator circle" :class="{ active: !singleValue(group.group_name) }" />
							<span class="choice-meta">
								<span class="choice-title">بدون انتخاب</span>
								<span class="choice-submeta">
									<small>بدون تغییر</small>
								</span>
							</span>
						</span>
						<span class="choice-check" :class="{ active: !singleValue(group.group_name) }">انتخاب</span>
					</button>

					<button
						v-for="option in group.options"
						:key="optionKey(option)"
						type="button"
						class="option-choice"
						:class="{ active: singleValue(group.group_name) === optionKey(option) }"
						:disabled="!optionSelectable(option)"
						@click="selectSingleChoice(group, optionKey(option))"
					>
						<span class="choice-main">
							<span
								class="indicator circle"
								:class="{ active: singleValue(group.group_name) === optionKey(option) }"
							/>
							<span class="choice-meta">
								<span class="choice-title">{{ optionDisplay(option) }}</span>
								<span class="choice-submeta">
									<small v-if="optionChoiceMeta(option)">{{ optionChoiceMeta(option) }}</small>
									<small v-if="optionTypeLabel(option)">{{ optionTypeLabel(option) }}</small>
								</span>
							</span>
						</span>
						<span class="choice-check" :class="{ active: singleValue(group.group_name) === optionKey(option) }">
							{{ singleValue(group.group_name) === optionKey(option) ? 'انتخاب شد' : 'انتخاب' }}
						</span>
					</button>
				</div>

				<div class="quantity-options" v-else>
					<article
						v-for="option in selectableOptions(group)"
						:key="optionKey(option)"
						class="quantity-row"
						:class="{ active: currentQty(group.group_name, optionKey(option)) > 0 }"
					>
						<div class="quantity-copy">
							<strong>{{ optionDisplay(option) }}</strong>
							<div class="choice-submeta">
								<small v-if="optionPriceLabel(option)">{{ optionPriceLabel(option) }}</small>
								<small v-if="optionStepLabel(option)">{{ optionStepLabel(option) }}</small>
							</div>
						</div>

						<div class="qty-control">
							<button
								type="button"
								class="qty-btn"
								@click="decreaseOption(group, option)"
								:disabled="currentQty(group.group_name, optionKey(option)) <= 0"
							>
								−
							</button>
							<div class="qty-pill">
								<strong>{{ formatQty(currentQty(group.group_name, optionKey(option))) }}</strong>
								<small>{{ optionUom(option) || 'عدد' }}</small>
							</div>
							<button
								type="button"
								class="qty-btn"
								@click="increaseOption(group, option)"
								:disabled="!canIncrease(group, option)"
							>
								+
							</button>
						</div>
					</article>
				</div>
			</section>
		</div>

		<p class="muted" v-else>برای این محصول گزینه‌ای تعریف نشده است.</p>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatMoney, toPersianNumber } from "@/utils/format";

const props = defineProps({
	groups: { type: Array, default: () => [] },
	modelValue: { type: Array, default: () => [] },
	currency: { type: String, default: "TOMAN" },
	compact: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const EPSILON = 1e-8;

const selections = computed(() =>
	Array.isArray(props.modelValue)
		? props.modelValue
				.map((row) => ({
					group: String(row.group || row.group_name || "").trim(),
					option: String(row.option || row.option_name || "").trim(),
					qty: Number(row.qty || 0),
				}))
				.filter((row) => row.group && row.option && Number.isFinite(row.qty) && row.qty > 0)
		: [],
);

function apply(next) {
	emit("update:modelValue", next);
}

function formatNumber(value, options = {}) {
	const numeric = Number(value || 0);
	if (!Number.isFinite(numeric)) {
		return "۰";
	}
	return toPersianNumber(numeric, options);
}

function optionKey(option = {}) {
	return String(option.name || option.option_key || "").trim();
}

function optionDisplay(option = {}) {
	return String(option.label || option.option_label || option.name || "").trim();
}

function optionTypeLabel(option = {}) {
	const type = String(option.modifier_type || option.action_type || "").trim();
	if (type === "bom_variant") {
		return "سایز / فرمول دیگر";
	}
	return "";
}

function optionUom(option = {}) {
	return String(option.option_uom || option.stock_uom || "").trim();
}

function optionBaseQty(option = {}) {
	const value = Number(option.base_qty ?? option.option_qty ?? option.qty_step ?? 1);
	return Number.isFinite(value) && value > 0 ? value : 1;
}

function optionMin(option = {}) {
	const value = Number(option.min_qty ?? 0);
	return Number.isFinite(value) ? Math.max(value, 0) : 0;
}

function optionMax(option = {}) {
	const minimum = optionMin(option);
	const value = Number(option.max_qty ?? optionBaseQty(option));
	if (!Number.isFinite(value)) {
		return Math.max(minimum, optionBaseQty(option));
	}
	return Math.max(value, minimum, optionBaseQty(option));
}

function optionStep(option = {}) {
	const value = Number(option.qty_step ?? optionBaseQty(option));
	return Number.isFinite(value) && value > 0 ? value : optionBaseQty(option);
}

function optionSelectable(option = {}) {
	return Number(option?.is_selectable ?? 1) === 1 && Number(option?.disabled ?? 0) !== 1;
}

function formatQty(value) {
	const numeric = Number(value || 0);
	if (!Number.isFinite(numeric) || numeric <= 0) {
		return "۰";
	}
	const rounded = Math.abs(numeric - Math.round(numeric)) < EPSILON ? Math.round(numeric) : Number(numeric.toFixed(2));
	return toPersianNumber(rounded);
}

function optionPriceLabel(option = {}) {
	const basePrice = Number(option.base_price ?? option.price_delta ?? 0);
	if (!Number.isFinite(basePrice) || basePrice <= 0) {
		return "";
	}
	const qtyLabel = `${formatQty(optionBaseQty(option))} ${optionUom(option)}`.trim();
	return `از ${formatMoney(basePrice, props.currency)} برای ${qtyLabel}`;
}

function optionStepLabel(option = {}) {
	const step = optionStep(option);
	const max = optionMax(option);
	const stepLabel = `${formatQty(step)} ${optionUom(option)}`.trim();
	const maxLabel = `${formatQty(max)} ${optionUom(option)}`.trim();
	return `گام ${stepLabel} • تا ${maxLabel}`;
}

function isBomVariantOption(option = {}) {
	return String(option.action_type || option.modifier_type || "").trim() === "bom_variant";
}

function isSingleUnitChoice(option = {}) {
	const baseQty = optionBaseQty(option);
	const step = optionStep(option);
	const minimum = optionMin(option);
	return Math.abs(baseQty - 1) < EPSILON && Math.abs(step - 1) < EPSILON && minimum <= 1 + EPSILON;
}

function optionChoiceMeta(option = {}) {
	if (!optionSelectable(option)) {
		return String(option?.unavailable_reason || "فعلاً در دسترس نیست").trim();
	}
	const basePrice = Number(option.base_price ?? option.price_delta ?? 0);
	if (Number.isFinite(basePrice) && basePrice > 0) {
		return `+${formatMoney(basePrice, props.currency)}`;
	}
	if (!String(option.option_item || "").trim()) {
		return "حالت پایه";
	}
	return "بدون تغییر قیمت";
}

function currentQty(groupName, optionName) {
	const row = selections.value.find(
		(entry) => entry.group === groupName && entry.option === optionName,
	);
	return row ? Math.max(Number(row.qty || 0), 0) : 0;
}

function selectedOptionCount(groupName) {
	return selections.value.filter((row) => row.group === groupName).length;
}

function selectableOptions(group = {}) {
	return (group.options || []).filter((option) => optionSelectable(option));
}

function rendersSingleChoiceOptions(group = {}) {
	const options = selectableOptions(group);
	if (String(group.selection_mode || "single") !== "single" || !options.length) {
		return false;
	}
	return options.every((option) => isBomVariantOption(option) || isSingleUnitChoice(option));
}

function singleValue(groupName) {
	const row = selections.value.find((entry) => entry.group === groupName);
	return row ? row.option : "";
}

function selectSingleChoice(group, optionName) {
	const next = selections.value.filter((row) => row.group !== group.group_name);
	if (optionName) {
		const option = (group.options || []).find((entry) => optionKey(entry) === optionName);
		if (!option || !optionSelectable(option)) {
			apply(next);
			return;
		}
		next.push({ group: group.group_name, option: optionName, qty: optionBaseQty(option) });
	}
	apply(next);
}

function normalizeQty(value, option = {}) {
	const minimum = optionMin(option);
	const maximum = optionMax(option);
	const step = optionStep(option);
	const numeric = Number(value || 0);

	if (!Number.isFinite(numeric) || numeric <= 0) {
		return 0;
	}

	if (minimum <= 0 && numeric < minimum + step - EPSILON) {
		return 0;
	}

	const snapped = minimum + Math.round((numeric - minimum) / step) * step;
	const clamped = Math.min(Math.max(snapped, minimum || step), maximum);
	return Number(clamped.toFixed(4));
}

function setOptionQty(group, option, qty) {
	const key = optionKey(option);
	const next = selections.value.filter(
		(row) => !(row.group === group.group_name && row.option === key),
	);
	const normalizedQty = normalizeQty(qty, option);

	if (normalizedQty > 0) {
		if (String(group.selection_mode || "multi") === "single") {
			const singleNext = next.filter((row) => row.group !== group.group_name);
			singleNext.push({ group: group.group_name, option: key, qty: normalizedQty });
			apply(singleNext);
			return;
		}

		if (
			currentQty(group.group_name, key) <= 0 &&
			selectedOptionCount(group.group_name) >= Number(group.max_select || 1)
		) {
			return;
		}

		next.push({ group: group.group_name, option: key, qty: normalizedQty });
	}

	apply(next);
}

function increaseOption(group, option) {
	const key = optionKey(option);
	const current = currentQty(group.group_name, key);
	const startQty = Math.max(optionBaseQty(option), optionStep(option), optionMin(option));
	const nextQty = current > 0 ? current + optionStep(option) : startQty;
	setOptionQty(group, option, nextQty);
}

function decreaseOption(group, option) {
	const key = optionKey(option);
	const current = currentQty(group.group_name, key);
	if (current <= 0) {
		return;
	}
	const minimum = optionMin(option);
	const nextQty = current - optionStep(option);
	if (minimum <= 0 && nextQty < optionStep(option) - EPSILON) {
		setOptionQty(group, option, 0);
		return;
	}
	setOptionQty(group, option, nextQty < minimum ? minimum : nextQty);
}

function canIncrease(group, option) {
	const key = optionKey(option);
	const current = currentQty(group.group_name, key);
	if (current > 0) {
		return current + optionStep(option) <= optionMax(option) + EPSILON;
	}
	if (String(group.selection_mode || "multi") === "single") {
		return true;
	}
	return selectedOptionCount(group.group_name) < Number(group.max_select || 1);
}
</script>

<style scoped>
.section {
	display: grid;
	gap: 0.7rem;
}

.section h3 {
	margin: 0;
	font-size: 1.05rem;
}

.groups {
	display: grid;
	gap: 0.65rem;
}

.group {
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.52);
	border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
	padding: 0.72rem;
}

.group-head {
	display: flex;
	align-items: start;
	justify-content: space-between;
	gap: 0.6rem;
}

.group h4 {
	margin: 0;
}

.group small {
	color: var(--text-muted);
}

.single-options,
.quantity-options {
	margin-top: 0.55rem;
	display: grid;
	gap: 0.45rem;
}

.option-choice,
.quantity-row {
	border-radius: 12px;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.28);
	background: rgba(255, 255, 255, 0.72);
}

.option-choice {
	width: 100%;
	color: var(--text-primary);
	font-family: inherit;
	text-align: right;
	padding: 0.72rem 0.78rem;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.8rem;
}

.option-choice:disabled {
	opacity: 0.52;
	cursor: not-allowed;
}

.option-choice.active,
.quantity-row.active {
	border-color: rgba(120, 82, 52, 0.45);
	background: rgba(255, 249, 242, 0.96);
}

.clear-option {
	align-items: center;
	font-size: 0.76rem;
}

.choice-main {
	min-width: 0;
	display: flex;
	align-items: flex-start;
	gap: 0.6rem;
}

.quantity-row {
	padding: 0.62rem 0.72rem;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.8rem;
}

.quantity-copy {
	display: grid;
	gap: 0.18rem;
	min-width: 0;
}

.choice-title,
.quantity-copy strong {
	font-size: 0.88rem;
	font-weight: 700;
}

.choice-meta {
	display: grid;
	gap: 0.16rem;
}

.choice-submeta {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 0.45rem;
}

.choice-submeta small {
	color: var(--text-muted);
	font-size: 0.72rem;
}

.choice-check {
	flex: 0 0 auto;
	min-width: 4.5rem;
	padding: 0.34rem 0.6rem;
	border-radius: 999px;
	border: 1px solid rgba(120, 82, 52, 0.14);
	background: rgba(255, 255, 255, 0.86);
	color: var(--text-muted);
	font-size: 0.72rem;
	font-weight: 700;
	text-align: center;
}

.choice-check.active {
	border-color: rgba(120, 82, 52, 0.35);
	background: rgba(120, 82, 52, 0.12);
	color: var(--text-primary);
}

.indicator {
	width: 18px;
	height: 18px;
	border: 2px solid rgb(var(--palette-deep-saffron-rgb) / 0.55);
	background: #fff;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	flex: 0 0 auto;
	margin-top: 1px;
}

.indicator.circle {
	border-radius: 999px;
}

.indicator.active {
	border-color: rgba(120, 82, 52, 0.72);
	background: rgba(120, 82, 52, 0.92);
}

.indicator.active::after {
	content: "";
	width: 8px;
	height: 8px;
	background: #fff;
	border-radius: inherit;
}

.qty-control {
	display: inline-flex;
	align-items: center;
	gap: 0.45rem;
	flex: 0 0 auto;
}

.qty-btn {
	width: 2.15rem;
	height: 2.15rem;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
	border-radius: 10px;
	background: rgba(255, 255, 255, 0.92);
	font: inherit;
	font-size: 1.05rem;
}

.qty-btn:disabled {
	opacity: 0.45;
}

.qty-pill {
	min-width: 4.35rem;
	padding: 0.36rem 0.5rem;
	border-radius: 10px;
	background: rgba(255, 255, 255, 0.92);
	border: 1px solid rgba(120, 82, 52, 0.14);
	display: grid;
	justify-items: center;
}

.qty-pill strong {
	font-size: 0.92rem;
	line-height: 1.05;
}

.qty-pill small {
	font-size: 0.68rem;
}

.muted {
	color: var(--text-muted);
}

@media (max-width: 640px) {
	.quantity-row {
		padding: 0.56rem 0.58rem;
		gap: 0.55rem;
	}

	.option-choice {
		padding: 0.62rem 0.64rem;
		align-items: flex-start;
	}

	.choice-check {
		min-width: 4rem;
		padding-inline: 0.5rem;
	}

	.qty-pill {
		min-width: 3.7rem;
	}
}
</style>
