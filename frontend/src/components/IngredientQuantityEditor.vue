<template>
	<div class="ingredient-section" :class="{ 'is-preview': isPreview, 'is-compact': compact }">
		<!-- Section Header -->
		<div class="section-header">
			<h3 class="section-title">مواد تشکیل‌دهنده</h3>
			<span class="section-count">{{ ingredients.length }} مورد</span>
		</div>

		<!-- Search -->
		<div class="search-wrap" v-if="ingredients.length">
			<Search class="search-icon" :size="18" />
			<input
				type="search"
				v-model.trim="search"
				placeholder="جستجوی مواد…"
				class="search-input"
			/>
		</div>

		<!-- Ingredients Grid -->
		<div class="ingredient-grid" v-if="filteredIngredients.length">
			<div
				class="ingredient-card"
				v-for="ingredient in filteredIngredients"
				:key="ingredient.key || ingredient.name"
				:class="{ 'is-disabled': !isPreview && getMultiplier(ingredient) <= 0 }"
			>
				<!-- Card Content: horizontal grid (RTL: text right, image left) -->
				<div class="card-content">
					<!-- Text Info (first column in RTL → right side) -->
					<div class="card-info">
						<div class="card-name">
							{{ ingredient.customer_label || ingredient.name }}
						</div>
						<div class="card-qty">
							{{ ingredient.base_qty }} {{ ingredient.qty_uom || "" }}
						</div>
						<div class="card-meta" v-if="hasIngredientMeta(ingredient)">
							<span class="meta-kcal" v-if="hasPositiveKcal(ingredient)">
								<Flame class="meta-kcal-icon" :size="13" />
								{{ formatKcal(ingredient.nutrition_kcal) }}
							</span>
							<span
								class="meta-extra"
								v-if="Number(ingredient.extra_when_added || 0)"
							>
								+{{ formatMoney(ingredient.extra_when_added, currency) }}
							</span>
						</div>
					</div>

					<!-- Card Image (second column in RTL → left side) -->
					<div class="card-img" v-if="!compact" @click="onImageClick(ingredient)">
						<img
							v-if="ingredient.image"
							:src="ingredient.image"
							:alt="ingredient.customer_label || ingredient.name"
						/>
						<div v-else class="card-img-placeholder">
							{{ (ingredient.customer_label || ingredient.name || "?").slice(0, 1) }}
						</div>
					</div>
				</div>

				<!-- Alternative selector in card (editor only) -->
				<div class="card-alt" v-if="!isPreview && isReplaceable(ingredient)">
					<span class="alt-label">جایگزین:</span>
					<div class="alt-options">
						<button
							type="button"
							class="alt-btn"
							:class="{ active: !selectedAlternative(ingredient) }"
							@click="setAlternative(ingredient, '')"
						>
							{{ baseAlternativeLabel(ingredient) }}
						</button>
						<button
							v-for="option in getAlternativeOptions(ingredient)"
							:key="option.alternative_item"
							type="button"
							class="alt-btn"
							:class="{
								active:
									selectedAlternative(ingredient) ===
									String(option.alternative_item || '').trim(),
							}"
							@click="setAlternative(ingredient, option.alternative_item)"
						>
							{{ alternativeOptionLabel(ingredient, option) }}
						</button>
					</div>
				</div>

				<!-- Card Actions (editor only) -->
				<div
					class="card-actions"
					v-if="!isPreview && (canEditQty(ingredient) || canQuickRemove(ingredient))"
				>
					<template v-if="canEditQty(ingredient)">
						<button
							class="qty-btn"
							type="button"
							:disabled="isDecDisabled(ingredient)"
							@click="decrease(ingredient)"
							aria-label="کاهش"
						>
							−
						</button>
						<span class="qty-val">x{{ getMultiplier(ingredient) }}</span>
						<button
							class="qty-btn"
							type="button"
							:disabled="isIncDisabled(ingredient)"
							@click="increase(ingredient)"
							aria-label="افزایش"
						>
							+
						</button>
					</template>
					<button
						v-if="canQuickRemove(ingredient) && getMultiplier(ingredient) > 0"
						class="remove-btn"
						type="button"
						@click="quickRemove(ingredient)"
						title="حذف"
						aria-label="حذف"
					>
						<Trash2 :size="14" />
					</button>
					<button
						v-if="canQuickRemove(ingredient) && getMultiplier(ingredient) <= 0"
						class="restore-btn"
						type="button"
						@click="restore(ingredient)"
						title="بازگردانی"
						aria-label="بازگردانی"
					>
						<RotateCcw :size="14" />
					</button>
				</div>
				<span v-if="!isPreview && !isRequired(ingredient)" class="fixed-badge">ثابت</span>
			</div>
		</div>

		<!-- Nutrition summary (editor only, shown in MenuQuickAddSheet preview) -->
		<div
			class="nutrition-summary"
			v-if="!isPreview && filteredIngredients.length && hasAnyNutrition"
		>
			<h4 class="nutrition-title">ارزش غذایی کل</h4>
			<div class="nutrition-grid">
				<div class="nutrition-item" v-if="totalNutrition.kcal > 0">
					<span class="nutrition-label">کالری</span>
					<strong class="nutrition-value">{{ Math.round(totalNutrition.kcal) }}</strong>
					<span class="nutrition-unit">kcal</span>
				</div>
				<div class="nutrition-item" v-if="totalNutrition.protein_g > 0">
					<span class="nutrition-label">پروتئین</span>
					<strong class="nutrition-value">{{
						Math.round(totalNutrition.protein_g)
					}}</strong>
					<span class="nutrition-unit">g</span>
				</div>
				<div class="nutrition-item" v-if="totalNutrition.carb_g > 0">
					<span class="nutrition-label">کربوهیدرات</span>
					<strong class="nutrition-value">{{
						Math.round(totalNutrition.carb_g)
					}}</strong>
					<span class="nutrition-unit">g</span>
				</div>
				<div class="nutrition-item" v-if="totalNutrition.fat_g > 0">
					<span class="nutrition-label">چربی</span>
					<strong class="nutrition-value">{{ Math.round(totalNutrition.fat_g) }}</strong>
					<span class="nutrition-unit">g</span>
				</div>
			</div>
		</div>

		<!-- Empty states -->
		<p class="empty-msg" v-else-if="!isPreview && ingredients.length">
			ماده‌ای با این جستجو پیدا نشد.
		</p>
		<p class="empty-msg" v-else-if="!isPreview">
			برای این محصول ماده قابل تنظیم تعریف نشده است.
		</p>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { Flame, Search, Trash2, RotateCcw } from "lucide-vue-next";
import {
	sanitizeCustomization,
	getIngredientMultiplier,
	upsertIngredientMultiplier,
	ingredientQtyStep,
} from "@/utils/itemConfig";
import { formatMoney } from "@/utils/format";

const props = defineProps({
	ingredients: {
		type: Array,
		default: () => [],
	},
	modelValue: {
		type: Object,
		default: () => ({}),
	},
	currency: {
		type: String,
		default: "TOMAN",
	},
	variant: {
		type: String,
		default: "editor", // 'editor' | 'preview'
	},
	compact: {
		type: Boolean,
		default: false,
	},
});

const isPreview = computed(() => props.variant === "preview");

const emit = defineEmits(["update:modelValue", "ingredient-image-tap"]);

const customization = computed(() =>
	sanitizeCustomization(props.modelValue || {}, props.ingredients || []),
);
const search = ref("");

function onImageClick(ingredient) {
	if (ingredient?.image) {
		emit("ingredient-image-tap", ingredient);
	}
}

const filteredIngredients = computed(() => {
	const query = String(search.value || "")
		.trim()
		.toLowerCase();
	if (!query) {
		return props.ingredients || [];
	}

	return (props.ingredients || []).filter((ingredient) => {
		const key = String(ingredient.key || "").toLowerCase();
		const name = String(ingredient.name || "").toLowerCase();
		const label = String(ingredient.customer_label || "").toLowerCase();
		return key.includes(query) || name.includes(query) || label.includes(query);
	});
});

const totalNutrition = computed(() => {
	const result = { kcal: 0, protein_g: 0, carb_g: 0, fat_g: 0 };
	const list = filteredIngredients.value || [];
	for (const ingredient of list) {
		const mult = getMultiplier(ingredient);
		const kcal = Number(ingredient?.nutrition_kcal || 0);
		const protein = Number(ingredient?.nutrition_protein_g || 0);
		const carb = Number(ingredient?.nutrition_carb_g || 0);
		const fat = Number(ingredient?.nutrition_fat_g || 0);
		if (kcal > 0) result.kcal += kcal * mult;
		if (protein > 0) result.protein_g += protein * mult;
		if (carb > 0) result.carb_g += carb * mult;
		if (fat > 0) result.fat_g += fat * mult;
	}
	return result;
});

const hasAnyNutrition = computed(() => {
	const n = totalNutrition.value;
	return n.kcal > 0 || n.protein_g > 0 || n.carb_g > 0 || n.fat_g > 0;
});

function min(ingredient) {
	return Number(ingredient.min_multiplier ?? 0);
}

function max(ingredient) {
	return Math.max(Number(ingredient.max_multiplier ?? 3), min(ingredient));
}

function getMultiplier(ingredient) {
	return getIngredientMultiplier(customization.value, ingredient);
}

function update(ingredient, nextMultiplier) {
	const next = upsertIngredientMultiplier(customization.value, ingredient, nextMultiplier);
	emit("update:modelValue", sanitizeCustomization(next, props.ingredients || []));
}

function getAlternativeOptions(ingredient) {
	return Array.isArray(ingredient?.alternative_options) ? ingredient.alternative_options : [];
}

function isReplaceable(ingredient) {
	return (
		Number(ingredient?.is_replaceable || 0) === 1 &&
		getAlternativeOptions(ingredient).length > 0
	);
}

function selectedAlternative(ingredient) {
	const key = String(ingredient?.key || ingredient?.name || "").trim();
	const row = (customization.value.selected_alternatives || []).find(
		(entry) => String(entry.ingredient_key || "").trim() === key,
	);
	return row ? String(row.alternative_item || "").trim() : "";
}

function setAlternative(ingredient, alternativeItem) {
	const key = String(ingredient?.key || ingredient?.name || "").trim();
	if (!key) {
		return;
	}

	const list = Array.isArray(customization.value.selected_alternatives)
		? [...customization.value.selected_alternatives]
		: [];
	const index = list.findIndex((row) => String(row.ingredient_key || "").trim() === key);

	if (!alternativeItem) {
		if (index >= 0) {
			list.splice(index, 1);
		}
	} else {
		const row = {
			ingredient_key: key,
			alternative_item: String(alternativeItem || "").trim(),
		};
		if (index >= 0) {
			list[index] = row;
		} else {
			list.push(row);
		}
	}

	emit(
		"update:modelValue",
		sanitizeCustomization(
			{
				...customization.value,
				selected_alternatives: list,
			},
			props.ingredients || [],
		),
	);
}

function alternativeOptionLabel(ingredient, option) {
	const label = String(option?.item_name || option?.alternative_item || "").trim();
	const baseQty = Number(ingredient?.base_qty || 0);
	const multiplier = Number(option?.qty_multiplier ?? 1);
	const addition = Number(option?.qty_addition || 0);
	const finalQty =
		baseQty * (Number.isFinite(multiplier) ? multiplier : 1) +
		(Number.isFinite(addition) ? addition : 0);
	const uom = String(option?.uom || option?.stock_uom || ingredient?.qty_uom || "").trim();

	if (!Number.isFinite(finalQty) || finalQty <= 0 || Math.abs(finalQty - baseQty) < 1e-8) {
		return label;
	}
	const qtyText = Number.isInteger(finalQty)
		? String(finalQty)
		: String(finalQty.toFixed(3)).replace(/\.?0+$/, "");
	return `${label} (${qtyText} ${uom})`;
}

function baseAlternativeLabel(ingredient = {}) {
	const label = String(ingredient?.customer_label || ingredient?.name || "").trim();
	return label || "گزینه اصلی";
}

function increase(ingredient) {
	update(ingredient, getMultiplier(ingredient) + multiplierStep(ingredient));
}

function decrease(ingredient) {
	update(ingredient, getMultiplier(ingredient) - multiplierStep(ingredient));
}

function isLocked(ingredient) {
	return Number(ingredient.is_editable_qty) !== 1;
}

function isRequired(ingredient) {
	return Number(ingredient?.is_required || 0) === 1;
}

function canEditQty(ingredient) {
	return !isLocked(ingredient);
}

function canQuickRemove(ingredient) {
	if (Number(ingredient?.can_remove || 0) !== 1) {
		return false;
	}
	if (isRequired(ingredient)) {
		return false;
	}
	return min(ingredient) <= 0;
}

function quickRemove(ingredient) {
	update(ingredient, 0);
}

function restore(ingredient) {
	update(ingredient, 1);
}

function hasPositiveKcal(ingredient) {
	const kcal = Number(ingredient?.nutrition_kcal);
	return Number.isFinite(kcal) && kcal > 0;
}

function formatKcal(value) {
	const numeric = Number(value || 0);
	if (!Number.isFinite(numeric) || numeric <= 0) {
		return "";
	}
	if (Math.abs(numeric - Math.round(numeric)) < 1e-8) {
		return String(Math.round(numeric));
	}
	return numeric.toFixed(1).replace(/\.0$/, "");
}

function hasIngredientMeta(ingredient) {
	return hasPositiveKcal(ingredient) || Number(ingredient?.extra_when_added || 0) > 0;
}

function isDecDisabled(ingredient) {
	if (isLocked(ingredient)) {
		return true;
	}
	return getMultiplier(ingredient) <= min(ingredient);
}

function isIncDisabled(ingredient) {
	if (isLocked(ingredient)) {
		return true;
	}
	return getMultiplier(ingredient) >= max(ingredient);
}

function multiplierStep(ingredient) {
	const baseQty = Number(ingredient?.base_qty || 0);
	const qtyStep = Number(ingredientQtyStep(ingredient) || 0);
	if (Number.isFinite(baseQty) && baseQty > 0 && Number.isFinite(qtyStep) && qtyStep > 0) {
		const asMultiplier = qtyStep / baseQty;
		if (Number.isFinite(asMultiplier) && asMultiplier > 0) {
			return asMultiplier;
		}
	}

	const fallback = Number(ingredient?.step_multiplier || 0.5);
	return fallback > 0 ? fallback : 0.5;
}
</script>

<style scoped>
.ingredient-section {
	display: grid;
	gap: 1rem;
}

/* ── Section Header ── */
.section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.75rem;
}

.section-title {
	margin: 0;
	font-size: 1.5rem;
	font-weight: 800;
	color: var(--accent-green, #6f4a31);
	letter-spacing: -0.02em;
}

.section-count {
	font-size: 0.8rem;
	font-weight: 600;
	color: var(--text-muted, #888);
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.1);
	padding: 0.25rem 0.75rem;
	border-radius: 999px;
	white-space: nowrap;
}

/* ── Search ── */
.search-wrap {
	position: relative;
}

.search-icon {
	position: absolute;
	right: 1rem;
	top: 50%;
	transform: translateY(-50%);
	color: var(--text-muted, #888);
	pointer-events: none;
	opacity: 0.7;
}

.search-input {
	width: 100%;
	border: 1.5px solid rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.18);
	background: rgb(var(--palette-eggshell-rgb, 251, 248, 244) / 0.7);
	border-radius: 14px;
	padding: 0.85rem 2.75rem 0.85rem 1.1rem;
	font-family: inherit;
	font-size: 0.9rem;
	color: var(--text-primary, #3f2a1d);
	transition:
		border-color 0.2s ease,
		box-shadow 0.2s ease,
		background 0.2s ease;
}

.search-input:focus {
	outline: none;
	border-color: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.45);
	box-shadow: 0 0 0 4px rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.07);
	background: #fff;
}

.search-input::placeholder {
	color: var(--text-muted, #888);
	opacity: 0.6;
}

/* ── Ingredient Grid ── */
.ingredient-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 0.75rem;
}

/* ── Ingredient Card ── */
.ingredient-card {
	border-radius: 16px;
	overflow: hidden;
	background: rgb(var(--palette-eggshell-rgb, 251, 248, 244) / 0.7);
	border: 1px solid rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.1);
	transition:
		box-shadow 0.2s ease,
		border-color 0.2s ease,
		opacity 0.2s ease;
}

.ingredient-card:hover {
	box-shadow: 0 4px 16px rgb(0 0 0 / 0.06);
	border-color: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.25);
}

.ingredient-card.is-disabled {
	opacity: 0.55;
}

/* ── Card Image ── */
.card-img {
	width: 100%;
	height: 100px;
	overflow: hidden;
	cursor: pointer;
	background: linear-gradient(
		135deg,
		rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.05),
		rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.03)
	);
}

.card-img img {
	width: 100%;
	height: 100%;
	object-fit: contain;
	padding: 12px;
	cursor: zoom-in;
	transition: transform 0.25s ease;
}

.card-img:hover img {
	transform: scale(1.06);
}

.card-img-placeholder {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(
		135deg,
		rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.1),
		rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.05)
	);
	color: var(--accent-gold, #c98d42);
	font-weight: 800;
	font-size: 1.6rem;
}

/* ── Card Body ── */
.card-body {
	padding: 0.65rem 0.75rem 0.75rem;
	display: flex;
	flex-direction: column;
	gap: 0.3rem;
}

.card-name {
	font-size: 0.85rem;
	font-weight: 700;
	color: var(--ink-900, #3f2a1d);
	line-height: 1.3;
}

.card-qty {
	font-size: 0.75rem;
	font-weight: 600;
	color: var(--text-muted, #846b58);
}

/* ── Card Meta ── */
.card-meta {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	min-height: 1rem;
	flex-wrap: wrap;
}

.meta-kcal {
	font-size: 0.7rem;
	font-weight: 600;
	color: var(--accent-gold, #c98d42);
}

.meta-extra {
	font-size: 0.7rem;
	font-weight: 500;
	color: var(--text-muted, #846b58);
}

/* ── Card Alternative ── */
.card-alt {
	display: flex;
	align-items: center;
	gap: 0.3rem;
	flex-wrap: wrap;
}

.card-alt .alt-label {
	font-size: 0.65rem;
	font-weight: 600;
	color: var(--text-muted, #846b58);
}

.alt-options {
	display: flex;
	flex-wrap: wrap;
	gap: 0.3rem;
}

.alt-btn {
	border-radius: 999px;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.2);
	background: rgba(255, 255, 255, 0.6);
	color: var(--text-primary, #3f2a1d);
	font-family: inherit;
	font-size: 0.68rem;
	font-weight: 500;
	padding: 0.2rem 0.55rem;
	cursor: pointer;
	transition: all 0.15s ease;
}

.alt-btn:hover {
	border-color: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.4);
	background: rgba(255, 255, 255, 0.9);
}

.alt-btn.active {
	background: rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.85);
	color: #fff;
	border-color: transparent;
}

/* ── Card Actions ── */
.card-actions {
	display: flex;
	align-items: center;
	gap: 0.35rem;
	flex-shrink: 0;
	margin-top: 0.25rem;
}

.qty-btn {
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.3);
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.07);
	color: var(--accent-gold, #c98d42);
	font-size: 1rem;
	font-weight: 700;
	line-height: 1;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.15s ease;
}

.qty-btn:hover:not(:disabled) {
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.15);
}

.qty-btn:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}

.qty-val {
	font-size: 0.82rem;
	font-weight: 700;
	color: var(--text-primary, #3f2a1d);
	min-width: 1.75rem;
	text-align: center;
}

.remove-btn,
.restore-btn {
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: none;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.15s ease;
}

.remove-btn {
	background: rgb(var(--danger-rgb, 220, 38, 38) / 0.07);
	color: var(--danger, #dc2626);
}

.remove-btn:hover {
	background: rgb(var(--danger-rgb, 220, 38, 38) / 0.14);
}

.restore-btn {
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.08);
	color: var(--accent-gold, #c98d42);
}

.restore-btn:hover {
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.16);
}

/* ── Fixed Badge ── */
.fixed-badge {
	font-size: 0.68rem;
	font-weight: 600;
	color: var(--text-muted, #846b58);
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.06);
	padding: 0.15rem 0.5rem;
	border-radius: 6px;
	white-space: nowrap;
	align-self: flex-start;
	margin-top: 0.25rem;
}

/* ── Nutrition Summary ── */
.nutrition-summary {
	margin-top: 1rem;
	padding: 0.85rem 1rem;
	border-radius: 16px;
	border: 1px solid rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.18);
	background: rgb(var(--palette-eggshell-rgb, 251, 248, 244) / 0.65);
	backdrop-filter: blur(8px);
}

.nutrition-title {
	margin: 0 0 0.65rem;
	font-size: 0.85rem;
	font-weight: 700;
	color: var(--ink-800, #3f2a1d);
}

.nutrition-grid {
	display: flex;
	flex-wrap: wrap;
	gap: 0.5rem;
}

.nutrition-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 0.4rem 0.75rem;
	border-radius: 12px;
	background: rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.07);
	min-width: 64px;
}

.nutrition-label {
	font-size: 0.65rem;
	color: var(--text-muted, #846b58);
	font-weight: 600;
}

.nutrition-value {
	font-size: 1rem;
	font-weight: 700;
	color: var(--ink-900, #3f2a1d);
	font-variant-numeric: tabular-nums;
	line-height: 1.1;
}

.nutrition-unit {
	font-size: 0.6rem;
	color: var(--text-muted, #846b58);
	font-weight: 500;
}

/* ── Empty Message ── */
.empty-msg {
	margin: 0;
	text-align: center;
	color: var(--text-muted, #846b58);
	font-size: 0.85rem;
	padding: 1.25rem 0.5rem;
}

/* ── Preview Variant ── */
.ingredient-section.is-preview {
	gap: 0.6rem;
}

.is-preview .section-header {
	padding: 0 2px;
}

.is-preview .section-title {
	font-size: 0.95rem;
	font-weight: 700;
	color: var(--accent-green);
}

.is-preview .section-count {
	font-size: 0.7rem;
	background: rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.06);
	color: var(--text-muted, #846b58);
}

/* Hide search in preview mode */
.is-preview .search-wrap {
	display: none;
}

.is-preview .ingredient-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 10px;
}

/* ── Preview: Horizontal Card — text right, image left (RTL) ──
   2-column grid always, even on mobile. Card is a compact
   horizontal layout: info (right) + small square image (left). */
.is-preview .ingredient-card {
	padding: 10px;
	border-radius: 16px;
	overflow: hidden;
	background: var(--pos-surface-color, #ffffff);
	border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.08);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
	transition: border-color 0.15s ease;
}

.is-preview .ingredient-card:hover {
	border-color: rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.16);
}

.is-preview .ingredient-card.is-disabled {
	opacity: 0.45;
}

/* Horizontal: info (right in RTL) + image (left in RTL) */
.is-preview .card-content {
	direction: rtl;
	display: grid !important;
	grid-template-columns: minmax(0, 1fr) 80px;
	grid-template-areas: "info image";
	align-items: center;
	gap: 8px;
	height: 100%;
}

.is-preview .card-info {
	grid-area: info;
	min-width: 0;
	text-align: right;
	display: flex;
	flex-direction: column;
	justify-content: center;
	gap: 3px;
}

.is-preview .card-img {
	grid-area: image;
	width: 80px !important;
	height: 80px !important;
	background: rgb(var(--palette-eggshell-rgb, 251, 248, 244) / 0.5) !important;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
	border-radius: 12px;
	flex-shrink: 0;
}

.is-preview .card-img img {
	width: 100%;
	height: 100%;
	object-fit: contain;
	padding: 6px;
	cursor: default;
}

.is-preview .card-img:hover img {
	transform: none;
}

.is-preview .card-img-placeholder {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(
		135deg,
		rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.05),
		rgb(var(--palette-deep-saffron-rgb, 201, 141, 66) / 0.04)
	);
	color: var(--accent-green);
	font-weight: 700;
	font-size: 1.1rem;
	border-radius: 10px;
}

.is-preview .card-name {
	font-size: 13px;
	font-weight: 800;
	color: var(--text-primary, #3f2a1d);
	line-height: 1.3;
	overflow: hidden;
	text-overflow: ellipsis;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
}

.is-preview .card-qty {
	font-size: 11px;
	font-weight: 500;
	color: var(--text-muted, #846b58);
	display: inline-flex;
	align-items: center;
	gap: 3px;
}

.is-preview .card-meta {
	display: flex;
	align-items: center;
	gap: 0.3rem;
	flex-wrap: wrap;
	min-height: 1rem;
	margin-top: 1px;
}

.is-preview .meta-kcal {
	font-size: 11px;
	font-weight: 600;
	color: var(--accent-green);
	display: inline-flex;
	align-items: center;
	gap: 2px;
	background: rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.06);
	padding: 1px 6px;
	border-radius: 5px;
}

.is-preview .meta-kcal-icon {
	color: var(--accent-green);
	flex-shrink: 0;
}

.is-preview .meta-extra {
	font-size: 0.6rem;
	font-weight: 500;
	color: var(--text-muted, #846b58);
	background: rgb(var(--palette-deep-sapphire-rgb, 111, 74, 49) / 0.06);
	padding: 1px 6px;
	border-radius: 5px;
}

/* ── Mobile (<=600px): keep TWO columns, horizontal cards ── */
@media (max-width: 600px) {
	.is-preview .ingredient-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 8px;
	}

	.is-preview .ingredient-card {
		padding: 8px;
		border-radius: 14px;
	}

	.is-preview .card-content {
		grid-template-columns: minmax(0, 1fr) 68px;
		gap: 6px;
	}

	.is-preview .card-img {
		width: 68px !important;
		height: 68px !important;
	}

	.is-preview .card-name {
		font-size: 11.5px;
	}

	.is-preview .card-qty {
		font-size: 10px;
	}
}

/* ── Extra-small (<=380px): shrink a bit more ── */
@media (max-width: 380px) {
	.is-preview .ingredient-grid {
		gap: 6px;
	}

	.is-preview .card-content {
		grid-template-columns: minmax(0, 1fr) 58px;
	}

	.is-preview .card-img {
		width: 58px !important;
		height: 58px !important;
	}

	.is-preview .card-name {
		font-size: 11px;
	}

	.is-preview .card-qty {
		font-size: 9px;
	}
}

/* ── Desktop / wide sheets ── */
@media (min-width: 940px) {
	.is-preview .ingredient-grid {
		gap: 12px;
	}

	.is-preview .card-content {
		grid-template-columns: minmax(0, 1fr) 100px;
		gap: 10px;
	}

	.is-preview .card-img {
		width: 100px !important;
		height: 100px !important;
	}

	.is-preview .card-name {
		font-size: 14px;
	}
}

/* ===== Compact mode (POS BOM Sheet): no images, larger tap targets ===== */
.is-compact .ingredient-grid {
	grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
	gap: 0.5rem;
}

.is-compact .ingredient-card {
	padding: 0.65rem 0.75rem;
	border-radius: 12px;
	border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.16);
	background: #fff;
}

.is-compact .card-content {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.5rem;
	padding: 0;
}

.is-compact .card-info {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 0.15rem;
}

.is-compact .card-name {
	font-size: 0.98rem;
	font-weight: 700;
	line-height: 1.25;
}

.is-compact .card-qty {
	font-size: 0.78rem;
	color: var(--text-muted, #846b58);
}

.is-compact .card-meta {
	display: flex;
	gap: 0.45rem;
	flex-wrap: wrap;
	margin-top: 0.2rem;
}

.is-compact .card-alt {
	margin-top: 0.5rem;
	padding-top: 0.5rem;
	border-top: 1px dashed rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.14);
	gap: 0.4rem;
}

.is-compact .card-alt .alt-label {
	font-size: 0.78rem;
}

.is-compact .alt-options {
	display: flex;
	flex-wrap: wrap;
	gap: 0.35rem;
}

.is-compact .alt-btn {
	min-height: 40px;
	padding: 0.45rem 0.85rem;
	font-size: 0.92rem;
	font-weight: 600;
	border-radius: 10px;
}

.is-compact .card-actions {
	margin-top: 0;
	gap: 0.45rem;
}

.is-compact .qty-btn {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	font-size: 1.35rem;
	font-weight: 700;
}

.is-compact .qty-val {
	font-size: 1rem;
	min-width: 2.25rem;
	font-weight: 800;
}

.is-compact .remove-btn,
.is-compact .restore-btn {
	width: 44px;
	height: 44px;
	border-radius: 12px;
}

.is-compact .section-title {
	font-size: 1rem;
}

.is-compact .fixed-badge {
	font-size: 0.7rem;
}
</style>
