<template>
	<article
		class="pos-product-card"
		:class="[
			`pos-product-card--${view}`,
			{ 'is-out-of-stock': isOutOfStock, 'has-quantity': quantity > 0 },
		]"
	>
		<template v-if="view === 'compact'">
			<button
				type="button"
				class="pos-product-card__compact-main"
				:disabled="isOutOfStock"
				:title="`افزودن سریع ${title}`"
				@click="$emit('increment')"
			>
				<span class="pos-product-card__name">{{ title }}</span>
				<span class="pos-product-card__price">{{ priceLabel }}</span>
				<span v-if="quantity > 0" class="pos-product-card__quantity-badge">× {{ displayQuantity }}</span>
			</button>
		</template>
		<template v-else>
			<button
				type="button"
				class="pos-product-card__image-button"
				:disabled="isOutOfStock"
				@click="$emit('increment')"
			>
				<img v-if="imageSource" class="pos-product-card__image" :src="imageSource" :alt="title" />
				<span v-else class="pos-product-card__image-placeholder" aria-hidden="true">{{ title.charAt(0) }}</span>
			</button>
			<div class="pos-product-card__body">
				<h4>{{ title }}</h4>
				<strong>{{ priceLabel }}</strong>
				<small v-if="isOutOfStock" class="pos-product-card__out-of-stock">ناموجود</small>
			</div>
		</template>

		<DsButton
			variant="quiet"
			size="sm"
			class="pos-product-card__quick-edit"
			title="ویرایش سریع محصول"
			aria-label="ویرایش سریع محصول"
			@click.stop="$emit('quick-edit')"
		>
			<AlertCircle :size="15" :stroke-width="2.4" />
		</DsButton>
		<DsButton
			variant="secondary"
			size="sm"
			class="pos-product-card__customize"
			title="سفارشی‌سازی محصول"
			aria-label="سفارشی‌سازی محصول"
			@click.stop="$emit('open-bom')"
		>
			<SlidersHorizontal :size="14" :stroke-width="2.3" />
		</DsButton>

		<div class="pos-product-card__actions">
			<div class="pos-product-card__counter" aria-label="تعداد محصول">
				<DsButton
					variant="secondary"
					size="sm"
					class="pos-product-card__counter-button"
					:disabled="quantity <= 0"
					aria-label="کم کردن تعداد"
					@click.stop="$emit('decrement')"
				>
					−
				</DsButton>
				<span>{{ displayQuantity }}</span>
				<DsButton
					variant="secondary"
					size="sm"
					class="pos-product-card__counter-button"
					:disabled="isOutOfStock"
					aria-label="افزودن تعداد"
					@click.stop="$emit('increment')"
				>
					+
				</DsButton>
			</div>
		</div>
	</article>
</template>

<script setup>
import { computed } from 'vue'
import { AlertCircle, SlidersHorizontal } from 'lucide-vue-next'
import DsButton from '@/components/design/DsButton.vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
	item: { type: Object, required: true },
	view: { type: String, default: 'grid' },
	quantity: { type: Number, default: 0 },
	currency: { type: String, default: 'IRR' },
	fallbackImage: { type: String, default: '' },
})

defineEmits(['increment', 'decrement', 'open-bom', 'quick-edit'])

const title = computed(() => String(props.item?.title || props.item?.name || 'محصول'))
const price = computed(() => Number(props.item?.base_price || props.item?.standard_rate || 0))
const priceLabel = computed(() => formatMoney(price.value, props.currency))
const imageSource = computed(() => String(props.item?.image || props.fallbackImage || '').trim())
const isOutOfStock = computed(() => Number(props.item?.out_of_stock) === 1)
const displayQuantity = computed(() => {
	const value = Number(props.quantity || 0)
	if (!value) return '۰'
	if (Math.abs(value - Math.round(value)) < 0.0001) return Math.round(value).toLocaleString('fa-IR')
	return Number(value.toFixed(3)).toLocaleString('fa-IR', { maximumFractionDigits: 3 })
})
</script>

<style scoped>
.pos-product-card {
	position: relative;
	min-width: 0;
	min-height: 128px;
	display: flex;
	flex-direction: column;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
	border-radius: 16px;
	background: var(--mg-bg-surface);
	box-shadow: 0 14px 30px rgb(52 38 31 / 0.07);
	overflow: hidden;
	transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.pos-product-card:hover {
	transform: translateY(-2px);
	border-color: color-mix(in srgb, var(--mg-primary) 44%, var(--mg-border-light) 56%);
	box-shadow: 0 20px 40px rgb(52 38 31 / 0.12);
}

.pos-product-card.has-quantity {
	border-color: color-mix(in srgb, var(--mg-primary) 72%, var(--mg-border-light) 28%);
	box-shadow: 0 0 0 2px color-mix(in srgb, var(--mg-primary) 12%, transparent), 0 16px 32px color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.pos-product-card.is-out-of-stock { opacity: 0.58; }
.pos-product-card.is-out-of-stock .pos-product-card__image { filter: grayscale(0.9); }

.pos-product-card__image-button {
	width: 100%;
	height: 80px;
	padding: 0;
	border: 0;
	background: color-mix(in srgb, var(--mg-bg-page) 60%, var(--mg-bg-surface) 40%);
	cursor: pointer;
	overflow: hidden;
}

.pos-product-card__image { width: 100%; height: 100%; display: block; object-fit: cover; object-position: center; }
.pos-product-card__image-placeholder {
	display: grid;
	place-items: center;
	height: 100%;
	font-size: 1.8rem;
	font-weight: 800;
	color: var(--mg-primary);
	background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface));
}

.pos-product-card__body {
	min-width: 0;
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 0.15rem;
	padding: 0.55rem 0.65rem 0.25rem;
}

.pos-product-card__body h4,
.pos-product-card__name { margin: 0; min-width: 0; color: var(--mg-text-main); font-size: 0.82rem; font-weight: 700; line-height: 1.35; overflow-wrap: anywhere; }
.pos-product-card__body strong,
.pos-product-card__price { color: var(--mg-primary); font-size: 0.8rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.pos-product-card__out-of-stock { color: var(--mg-danger); font-size: 0.68rem; font-weight: 700; }

.pos-product-card__quick-edit {
	position: absolute;
	top: 0.35rem;
	inset-inline-start: 0.35rem;
	z-index: 2;
	width: 34px;
	min-height: 34px;
	padding: 0;
	border-radius: 999px;
	background: color-mix(in srgb, var(--mg-bg-surface) 90%, transparent);
	color: var(--mg-primary);
	box-shadow: 0 5px 14px rgb(52 38 31 / 0.18);
}

.pos-product-card__customize {
	position: absolute;
	top: 0.35rem;
	inset-inline-end: 0.35rem;
	z-index: 2;
	width: 34px;
	min-height: 34px;
	padding: 0;
	border-radius: 999px;
	background: color-mix(in srgb, var(--mg-bg-surface) 90%, transparent);
	color: var(--mg-primary);
	box-shadow: 0 5px 14px rgb(52 38 31 / 0.18);
}

.pos-product-card__actions { display: flex; align-items: center; justify-content: space-between; gap: 0.35rem; padding: 0.3rem 0.6rem 0.55rem; margin-top: auto; flex-wrap: wrap; }
.pos-product-card__counter { display: inline-flex; align-items: center; gap: 0.15rem; }
.pos-product-card__counter > span { min-width: 28px; text-align: center; color: var(--mg-text-main); font-size: 0.78rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.pos-product-card__counter-button { width: 30px; min-height: 30px; padding: 0; border-radius: 10px; font-size: 1rem; }

.pos-product-card--list { min-height: 80px; flex-direction: row; align-items: center; }
.pos-product-card--list .pos-product-card__image-button { width: 64px; height: 64px; margin: 0.35rem; border-radius: 10px; flex-shrink: 0; }
.pos-product-card--list .pos-product-card__body { flex-direction: row; align-items: center; justify-content: space-between; padding: 0.35rem 0.55rem; gap: 0.4rem; }
.pos-product-card--list .pos-product-card__actions { margin-top: 0; padding: 0.3rem 0.55rem; flex-shrink: 0; }

.pos-product-card--compact { min-height: 96px; padding: 0.7rem; }
.pos-product-card__compact-main { min-width: 0; min-height: 54px; display: grid; align-content: start; gap: 0.22rem; padding: 0; border: 0; background: transparent; text-align: right; cursor: pointer; font: inherit; }
.pos-product-card--compact .pos-product-card__actions { padding: 0; }
.pos-product-card__quantity-badge { position: absolute; top: 0.45rem; inset-inline-start: 0.45rem; padding: 0.14rem 0.42rem; border-radius: 999px; background: var(--mg-primary); color: var(--mg-bg-surface); font-size: 0.68rem; font-weight: 700; }

@media (max-width: 860px) {
	.pos-product-card--list { flex-direction: column; align-items: stretch; }
	.pos-product-card--list .pos-product-card__image-button { width: 100%; height: 80px; margin: 0; border-radius: 0; }
	.pos-product-card--list .pos-product-card__body { flex-direction: column; align-items: flex-start; }
	.pos-product-card--list .pos-product-card__actions { padding: 0.3rem 0.55rem 0.55rem; }
}
</style>
