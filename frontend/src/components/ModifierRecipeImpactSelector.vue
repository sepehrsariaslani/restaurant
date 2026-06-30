<template>
	<div class="section" :class="{ 'is-compact': compact }">
		<h3>سایز و افزودنی‌ها</h3>

		<div class="groups" v-if="groups.length">
			<section class="group" v-for="group in groups" :key="group.group_name">
				<header>
					<h4>{{ group.title }}</h4>
					<small>
						{{ group.min_select }} تا {{ group.max_select }}
						<span v-if="Number(group.required) === 1">(اجباری)</span>
					</small>
				</header>

				<div class="single-options" v-if="group.selection_mode === 'single'">
					<button
						v-if="Number(group.required) !== 1"
						type="button"
						class="option-choice clear-option"
						:class="{ active: !singleValue(group.group_name) }"
						@click="selectSingle(group, '')"
					>
						<span
							class="indicator circle"
							:class="{ active: !singleValue(group.group_name) }"
						/>
						بدون انتخاب
					</button>

					<button
						v-for="option in group.options"
						:key="optionKey(option)"
						type="button"
						class="option-choice"
						:class="{ active: singleValue(group.group_name) === optionKey(option) }"
						@click="selectSingle(group, optionKey(option))"
					>
						<span
							class="indicator circle"
							:class="{
								active: singleValue(group.group_name) === optionKey(option),
							}"
						/>
						<span class="choice-meta">
							<span class="choice-title">{{ optionDisplay(option) }}</span>
							<span class="choice-submeta">
								<small v-if="optionTypeLabel(option)">{{
									optionTypeLabel(option)
								}}</small>
								<small v-if="Number(option.price_delta || 0)"
									>+{{ formatMoney(option.price_delta, currency) }}</small
								>
							</span>
						</span>
					</button>
				</div>

				<div class="multi-options" v-else>
					<button
						class="option-choice"
						v-for="option in group.options"
						:key="optionKey(option)"
						type="button"
						:class="{ active: isSelected(group.group_name, optionKey(option)) }"
						@click="toggleMulti(group, option)"
					>
						<span
							class="indicator square"
							:class="{ active: isSelected(group.group_name, optionKey(option)) }"
						/>
						<span class="choice-meta">
							<span class="choice-title">{{ optionDisplay(option) }}</span>
							<span class="choice-submeta">
								<small v-if="optionTypeLabel(option)">{{
									optionTypeLabel(option)
								}}</small>
								<small v-if="Number(option.price_delta || 0)"
									>+{{ formatMoney(option.price_delta, currency) }}</small
								>
							</span>
						</span>
					</button>
				</div>
			</section>
		</div>

		<p class="muted" v-else>برای این محصول گزینه‌ای تعریف نشده است.</p>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatMoney } from "@/utils/format";

const props = defineProps({
	groups: { type: Array, default: () => [] },
	modelValue: { type: Array, default: () => [] },
	currency: { type: String, default: "TOMAN" },
	compact: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const selections = computed(() =>
	Array.isArray(props.modelValue)
		? props.modelValue
				.map((row) => ({
					group: String(row.group || row.group_name || "").trim(),
					option: String(row.option || row.option_name || "").trim(),
					qty: Number(row.qty || 0),
				}))
				.filter(
					(row) => row.group && row.option && Number.isFinite(row.qty) && row.qty > 0,
				)
		: [],
);

function apply(next) {
	emit("update:modelValue", next);
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

function optionMin(option = {}) {
	const value = Number(option.min_qty ?? 1);
	return Number.isFinite(value) ? Math.max(value, 0) : 1;
}

function optionMax(option = {}) {
	const min = optionMin(option);
	const value = Number(option.max_qty ?? 9);
	if (!Number.isFinite(value)) {
		return Math.max(min, 9);
	}
	return Math.max(value, min);
}

function optionStep(option = {}) {
	const value = Number(option.qty_step ?? 1);
	return Number.isFinite(value) && value > 0 ? value : 1;
}

function snapQty(value, option = {}) {
	const min = optionMin(option);
	const max = optionMax(option);
	const step = optionStep(option);

	if (!Number.isFinite(value) || value <= 0) {
		return 0;
	}

	const rounded = min + Math.round((value - min) / step) * step;
	const clamped = Math.min(Math.max(rounded, min), max);
	return Number(clamped.toFixed(4));
}

function singleValue(groupName) {
	const row = selections.value.find((entry) => entry.group === groupName);
	return row ? row.option : "";
}

function selectSingle(group, optionName) {
	const next = selections.value.filter((row) => row.group !== group.group_name);
	if (optionName) {
		next.push({ group: group.group_name, option: optionName, qty: 1 });
	}
	apply(next);
}

function multiQty(groupName, optionName) {
	const row = selections.value.find(
		(entry) => entry.group === groupName && entry.option === optionName,
	);
	return row ? Math.max(Number(row.qty || 0), 0) : 0;
}

function selectedOptionCount(groupName) {
	return selections.value.filter((row) => row.group === groupName).length;
}

function setMultiQty(group, option, qty) {
	const key = optionKey(option);
	const next = selections.value.filter(
		(row) => !(row.group === group.group_name && row.option === key),
	);

	const normalizedQty = snapQty(qty, option);
	if (normalizedQty > 0) {
		if (
			multiQty(group.group_name, key) <= 0 &&
			selectedOptionCount(group.group_name) >= Number(group.max_select || 1)
		) {
			apply(selections.value);
			return;
		}

		next.push({ group: group.group_name, option: key, qty: normalizedQty });
	}

	apply(next);
}

function isSelected(groupName, optionName) {
	return multiQty(groupName, optionName) > 0;
}

function toggleMulti(group, option) {
	const key = optionKey(option);
	if (isSelected(group.group_name, key)) {
		setMultiQty(group, option, 0);
		return;
	}

	const start = Math.max(optionMin(option), 1);
	setMultiQty(group, option, start);
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
	gap: 0.6rem;
}

.group {
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.52);
	border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
	padding: 0.65rem;
}

.group h4 {
	margin: 0;
}

.group small {
	color: var(--text-muted);
}

.single-options {
	margin-top: 0.45rem;
	display: grid;
	gap: 0.35rem;
}

.option-choice {
	width: 100%;
	border-radius: 12px;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.28);
	background: rgba(255, 255, 255, 0.72);
	color: var(--text-primary);
	font-family: inherit;
	text-align: right;
	padding: 0.48rem 0.56rem;
	cursor: pointer;
	display: flex;
	align-items: flex-start;
	gap: 0.55rem;
}

.option-choice.active {
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.56);
	background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.clear-option {
	align-items: center;
	font-size: 0.76rem;
}

.choice-title {
	font-size: 0.86rem;
	font-weight: 600;
}

.choice-meta {
	display: grid;
	gap: 0.16rem;
}

.choice-submeta {
	display: flex;
	align-items: center;
	gap: 0.4rem;
}

.choice-submeta small {
	color: var(--text-muted);
	font-size: 0.71rem;
}

.multi-options {
	margin-top: 0.45rem;
	display: grid;
	gap: 0.35rem;
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

.indicator.square {
	border-radius: 4px;
}

.indicator.active {
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.7);
	background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
}

.indicator.active::after {
	content: "";
	width: 8px;
	height: 8px;
	background: #fff;
	border-radius: inherit;
}

/* ===== Compact mode (POS BOM Sheet) ===== */
.is-compact.section {
	gap: 0.55rem;
}

.is-compact .group {
	background: #fff;
	border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.14);
	border-radius: 14px;
	padding: 0.6rem 0.7rem;
}

.is-compact .group h4 {
	font-size: 0.95rem;
}

.is-compact .single-options,
.is-compact .multi-options {
	margin-top: 0.5rem;
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
	gap: 0.4rem;
}

.is-compact .option-choice {
	min-height: 56px;
	padding: 0.65rem 0.85rem;
	border-radius: 12px;
	border: 1.5px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.16);
	background: #fff;
	align-items: center;
	gap: 0.65rem;
	transition:
		border-color 0.15s ease,
		background-color 0.15s ease,
		transform 0.12s ease;
}

.is-compact .option-choice:hover {
	border-color: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.35);
	background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.03);
}

.is-compact .option-choice:active {
	transform: scale(0.98);
}

.is-compact .option-choice.active {
	border-color: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.7);
	background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
	box-shadow: 0 0 0 3px rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
}

.is-compact .indicator {
	width: 22px;
	height: 22px;
	border-width: 2px;
	flex-shrink: 0;
}

.is-compact .indicator.active::after {
	width: 10px;
	height: 10px;
}

.is-compact .choice-title {
	font-size: 0.98rem;
	font-weight: 700;
	line-height: 1.25;
}

.is-compact .choice-submeta small {
	font-size: 0.78rem;
}
</style>
