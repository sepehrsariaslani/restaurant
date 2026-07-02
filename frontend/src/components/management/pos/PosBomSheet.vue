<template>
	<div class="sheet-overlay" v-if="open" @click.self="$emit('close')">
		<section class="sheet-card">
			<header class="sheet-head">
				<div>
					<h3>سفارشی سازی BOM</h3>
					<p>{{ item?.title || "-" }}</p>
				</div>
				<button type="button" class="close-btn" @click="$emit('close')">بستن</button>
			</header>

			<p class="hint" v-if="loading">در حال دریافت جزئیات BOM...</p>
			<p class="error" v-else-if="error">{{ error }}</p>

			<template v-else-if="item">
				<div class="qty-row">
					<small>تعداد</small>
					<div class="counter">
						<button
							type="button"
							@click="$emit('update:qty', Math.max(Number(qty || 1) - 1, 1))"
						>
							-
						</button>
						<strong>{{ Number(qty || 0).toLocaleString('fa-IR') }}</strong>
						<button type="button" @click="$emit('update:qty', Number(qty || 1) + 1)">
							+
						</button>
					</div>
				</div>

				<IngredientQuantityEditor
					v-if="ingredients.length"
					:ingredients="ingredients"
					:model-value="customization"
					:currency="currency"
					compact
					@update:model-value="$emit('update-customization', $event)"
				/>

				<ModifierRecipeImpactSelector
					v-if="modifierGroups.length"
					:groups="modifierGroups"
					:currency="currency"
					:model-value="customization.selected_modifiers"
					compact
					@update:model-value="$emit('update-modifiers', $event)"
				/>

				<p class="hint" v-if="!ingredients.length && !modifierGroups.length">
					این محصول سفارشی سازی BOM ندارد.
				</p>

				<footer class="sheet-foot">
					<strong>قیمت واحد: {{ formatMoney(preview.unitPrice || 0, currency) }}</strong>
					<strong>مجموع: {{ formatMoney(preview.lineTotal || 0, currency) }}</strong>
					<button type="button" class="submit-btn" @click="$emit('confirm')">
						{{ confirmLabel }}
					</button>
				</footer>
			</template>
		</section>
	</div>
</template>

<script setup>
import IngredientQuantityEditor from "@/components/IngredientQuantityEditor.vue";
import ModifierRecipeImpactSelector from "@/components/ModifierRecipeImpactSelector.vue";
import { formatMoney } from "@/utils/format";

defineProps({
	open: {
		type: Boolean,
		default: false,
	},
	loading: {
		type: Boolean,
		default: false,
	},
	error: {
		type: String,
		default: "",
	},
	item: {
		type: Object,
		default: null,
	},
	ingredients: {
		type: Array,
		default: () => [],
	},
	modifierGroups: {
		type: Array,
		default: () => [],
	},
	customization: {
		type: Object,
		default: () => ({
			ingredient_adjustments: [],
			selected_modifiers: [],
			selected_alternatives: [],
		}),
	},
	qty: {
		type: Number,
		default: 1,
	},
	preview: {
		type: Object,
		default: () => ({
			unitPrice: 0,
			lineTotal: 0,
		}),
	},
	currency: {
		type: String,
		default: "IRR",
	},
	confirmLabel: {
		type: String,
		default: "افزودن به سبد",
	},
});

defineEmits(["close", "update:qty", "update-customization", "update-modifiers", "confirm"]);
</script>

<style scoped>
.sheet-overlay {
	position: fixed;
	inset: 0;
	z-index: 120;
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.24);
	display: grid;
	place-items: center;
	padding: 1rem;
}

.sheet-card {
	width: min(880px, 100%);
	max-height: calc(100vh - 2rem);
	overflow: auto;
	border-radius: 18px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	color: var(--pos-text);
	padding: 0.8rem;
	display: grid;
	gap: 0.65rem;
}

.sheet-head {
	display: flex;
	align-items: start;
	justify-content: space-between;
	gap: 0.6rem;
}

.sheet-head h3,
.sheet-head p {
	margin: 0;
}

.sheet-head p {
	margin-top: 0.2rem;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
}

.close-btn,
.submit-btn,
.counter button {
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	color: var(--pos-primary);
	border-radius: 10px;
	cursor: pointer;
	font-family: inherit;
}

.close-btn {
	padding: 0.5rem 0.9rem;
	font-size: 0.9rem;
	min-height: 40px;
}

.qty-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.6rem 0.8rem;
	border-radius: 14px;
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.04);
	border: 1px solid var(--pos-border);
}

.qty-row small {
	font-size: 0.92rem;
	font-weight: 600;
	color: var(--pos-text);
}

.counter {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
}

.counter button {
	width: 44px;
	height: 44px;
	font-size: 1.3rem;
	font-weight: 700;
	line-height: 1;
}

.counter strong {
	min-width: 2.5rem;
	text-align: center;
	font-size: 1.05rem;
}

.hint {
	margin: 0;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
	font-size: 0.92rem;
}

.error {
	margin: 0;
	color: var(--pos-accent);
	font-size: 0.92rem;
}

.sheet-foot {
	border-top: 1px dashed var(--pos-border);
	padding-top: 0.6rem;
	display: flex;
	flex-wrap: wrap;
	gap: 0.6rem;
	justify-content: space-between;
	align-items: center;
}

.sheet-foot strong {
	font-size: 0.95rem;
}

.submit-btn {
	background: var(--pos-accent);
	border-color: var(--pos-accent);
	color: var(--pos-white);
	padding: 0.7rem 1.4rem;
	font-size: 0.98rem;
	font-weight: 700;
	min-height: 48px;
}

.submit-btn:hover {
	filter: brightness(0.95);
}
</style>
