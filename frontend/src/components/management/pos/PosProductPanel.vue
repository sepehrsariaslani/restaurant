<template>
	<section class="products-panel">
		<div class="customer-search-bar">
			<div class="customer-search-wrap">
				<span class="cust-icon"><UserRound :size="15" :stroke-width="2.1" /></span>
				<input
					ref="customerInputRef"
					class="input dark-input cust-input"
					:value="customerQuery"
					@input="$emit('update:customerQuery', $event.target.value)"
					@focus="openDropdown"
					@click="openDropdown"
					@blur="onBlur"
					@keydown.down.prevent="moveActive(1)"
					@keydown.up.prevent="moveActive(-1)"
					@keydown.enter.prevent="selectActive"
					placeholder="جستجوی مشتری..."
				/>
				<button
					v-if="customerQuery"
					type="button"
					class="cust-clear"
					@mousedown.prevent="$emit('update:customerQuery', '')"
				>
					×
				</button>
				<div v-if="dropdownOpen && dropdownOptions.length" class="cust-dropdown">
					<button
						v-for="(customer, index) in dropdownOptions"
						:key="customer.key || index"
						type="button"
						class="cust-option"
						:class="{ active: index === activeIndex }"
						@mousedown.prevent="pickCustomer(customer)"
					>
						<span class="cust-option-name">{{ customer.label }}</span>
						<span class="cust-option-meta">
							<span v-if="customer.is_new" class="cust-new-tag">مشتری جدید</span>
							<template v-else>
								<span v-if="customer.mobile">{{ customer.mobile }}</span>
								<span>{{ Number(customer.orders_count || 0).toLocaleString('fa-IR') }} خرید</span>
							</template>
						</span>
					</button>
				</div>
				<div
					v-else-if="dropdownOpen && customerQuery && !dropdownOptions.length"
					class="cust-dropdown"
				>
					<div class="cust-empty">مشتری‌ای پیدا نشد.</div>
				</div>
			</div>
			<button
				type="button"
				class="cust-add-btn"
				@click="$emit('add-customer')"
				title="مشتری جدید"
			>
				<Plus :size="15" :stroke-width="2.4" />
			</button>
		</div>

		<div class="panel-top">
			<div class="toolbar">
				<div class="search-box">
					<span class="icon"><Search :size="15" :stroke-width="2.2" /></span>
					<input
						class="input dark-input product-search-input"
						:value="searchTerm"
						@input="$emit('update:searchTerm', $event.target.value)"
						placeholder="نام یا کد محصول"
					/>
					<button
						v-if="searchTerm"
						type="button"
						class="clear-search-btn"
						@click="$emit('update:searchTerm', '')"
					>
						×
					</button>
				</div>

				<div class="view-toggle">
					<button
						type="button"
						:class="{ active: productView === 'grid' }"
						@click="$emit('update:productView', 'grid')"
						title="شبکه‌ای با عکس"
					>
						⊞
					</button>
					<button
						type="button"
						:class="{ active: productView === 'compact' }"
						@click="$emit('update:productView', 'compact')"
						title="فشرده بدون عکس"
					>
						≡
					</button>
					<button
						type="button"
						:class="{ active: productView === 'list' }"
						@click="$emit('update:productView', 'list')"
						title="لیستی"
					>
						☰
					</button>
				</div>
			</div>

			<div class="scan-row">
				<input
					class="input dark-input"
					:value="scannerInput"
					@input="$emit('update:scannerInput', $event.target.value)"
					@keyup.enter="$emit('scan-scale')"
					placeholder="بارکد وزنی ترازو"
				/>
				<button type="button" class="scan-btn" @click="$emit('scan-scale')">
					تحلیل بارکد
				</button>
			</div>
			<p class="scan-feedback" v-if="scannerFeedback">{{ scannerFeedback }}</p>

			<div class="category-bar" v-if="categories.length">
				<button
					type="button"
					class="cat-chip"
					:class="{ active: selectedCategory === '' }"
					@click="$emit('update:selectedCategory', '')"
				>
					همه
				</button>
				<button
					v-for="cat in categories"
					:key="cat.slug || cat.name"
					type="button"
					class="cat-chip"
					:class="{ active: selectedCategory === (cat.slug || cat.name) }"
					@click="$emit('update:selectedCategory', cat.slug || cat.name)"
				>
					{{ cat.title || cat.name }}
				</button>
			</div>
		</div>

		<p class="hint" v-if="loading">در حال دریافت محصولات...</p>
		<p class="error" v-else-if="error">{{ error }}</p>

		<div v-else class="products-sections">
			<section
				v-for="category in groupedProductSections"
				:key="category.key"
				class="category-section"
			>
				<header class="category-section-head">
					<div class="category-section-copy">
						<h3>{{ category.title }}</h3>
						<p>{{ category.countLabel }}</p>
					</div>
				</header>

				<div class="subcategory-stack">
					<section
						v-for="group in category.groups"
						:key="group.key"
						class="subcategory-section"
					>
						<header
							v-if="group.title"
							class="subcategory-section-head"
						>
							<h4>{{ group.title }}</h4>
							<span>{{ group.items.length.toLocaleString('fa-IR') }}</span>
						</header>

						<div class="products-grid" :class="`mode-${productView}`">
							<template v-if="productView === 'compact'">
								<article
									v-for="item in group.items"
									:key="item.slug || item.name"
									class="compact-card"
									:class="{ 'has-qty': quantityValue(item.slug) > 0 }"
								>
									<button
										type="button"
										class="compact-main-btn"
										@click="$emit('increment-product', item)"
										:title="`افزودن سریع ${item.title || item.name}`"
									>
										<span class="compact-name">{{ item.title || item.name }}</span>
										<span class="compact-price">{{
											formatMoney(item.base_price || item.standard_rate || 0, currency)
										}}</span>
										<span class="compact-qty" v-if="quantityValue(item.slug) > 0"
											>× {{ displayQty(item.slug) }}</span
										>
									</button>
									<div class="compact-actions">
										<button
											type="button"
											class="compact-action-btn compact-action-btn--primary"
											:title="`افزودن سریع ${item.title || item.name}`"
											@click="$emit('increment-product', item)"
										>
											<Plus :size="14" :stroke-width="2.4" />
										</button>
										<button
											v-if="supportsCustomization(item)"
											type="button"
											class="compact-action-btn"
											:title="`سفارشی سازی ${item.title || item.name}`"
											@click="$emit('open-bom', item)"
										>
											<SlidersHorizontal :size="14" :stroke-width="2.3" />
										</button>
									</div>
								</article>
							</template>

							<template v-else>
								<article
									class="product-card"
									v-for="item in group.items"
									:key="item.slug || item.name"
								>
									<button
										type="button"
										class="image-btn"
										@click="$emit('increment-product', item)"
									>
										<img
											class="product-image"
											:src="item.image || fallbackImage"
											:alt="item.title || item.name"
										/>
									</button>

									<div class="product-body">
										<h4>{{ item.title || item.name }}</h4>
										<strong>{{
											formatMoney(item.base_price || item.standard_rate || 0, currency)
										}}</strong>
									</div>

									<div class="product-actions">
										<div class="counter">
											<button type="button" @click="$emit('decrement-product', item)">
												-
											</button>
											<span>{{ displayQty(item.slug) }}</span>
											<button type="button" @click="$emit('increment-product', item)">
												+
											</button>
										</div>
										<button type="button" class="bom-btn" @click="$emit('open-bom', item)">
											BOM
										</button>
									</div>
								</article>
							</template>
						</div>
					</section>
				</div>
			</section>
		</div>
	</section>
</template>

<script setup>
import { computed, ref } from "vue";
import { Plus, Search, SlidersHorizontal, UserRound } from "lucide-vue-next";
import { formatMoney } from "@/utils/format";

const props = defineProps({
	products: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	error: { type: String, default: "" },
	searchTerm: { type: String, default: "" },
	scannerInput: { type: String, default: "" },
	scannerFeedback: { type: String, default: "" },
	productView: { type: String, default: "grid" },
	quantityMap: { type: Object, default: () => ({}) },
	fallbackImage: { type: String, default: "" },
	currency: { type: String, default: "IRR" },
	categories: { type: Array, default: () => [] },
	selectedCategory: { type: String, default: "" },
	customerQuery: { type: String, default: "" },
	customerOptions: { type: Array, default: () => [] },
});

const emit = defineEmits([
	"update:searchTerm",
	"update:productView",
	"update:selectedCategory",
	"increment-product",
	"decrement-product",
	"open-bom",
	"update:scannerInput",
	"scan-scale",
	"update:customerQuery",
	"select-customer",
	"create-customer",
	"add-customer",
]);

const customerInputRef = ref(null);
const dropdownOpen = ref(false);
const activeIndex = ref(-1);

const filteredCustomers = computed(() => {
	const all = Array.isArray(props.customerOptions) ? props.customerOptions : [];
	const q = String(props.customerQuery || "")
		.trim()
		.toLowerCase();
	if (!q) return all.slice(0, 10);
	const digits = q.replace(/\D/g, "");
	return all
		.filter((c) => {
			const label = String(c.label || "").toLowerCase();
			const mobile = String(c.mobile || "");
			if (label.includes(q)) return true;
			if (digits && mobile.replace(/\D/g, "").includes(digits)) return true;
			return false;
		})
		.slice(0, 10);
});

const createOption = computed(() => {
	const q = String(props.customerQuery || "").trim();
	if (!q) return null;
	const exact = filteredCustomers.value.some(
		(c) =>
			String(c.label || "")
				.trim()
				.toLowerCase() === q.toLowerCase(),
	);
	if (exact) return null;
	return {
		key: `create-${q}`,
		label: `ایجاد: ${q}`,
		mobile: "",
		orders_count: 0,
		is_new: true,
		raw_query: q,
	};
});

const dropdownOptions = computed(() => {
	const opts = [...filteredCustomers.value];
	if (createOption.value) opts.unshift(createOption.value);
	return opts;
});

const groupedProductSections = computed(() => {
	const productRows = Array.isArray(props.products) ? props.products : [];
	const categoryRows = Array.isArray(props.categories) ? props.categories : [];

	if (!productRows.length) {
		return [];
	}

	const categoryBuckets = [];
	const categoryMap = new Map();

	function normalizeKey(value) {
		return String(value || "").trim();
	}

	function resolveCategoryKey(category = {}, item = {}) {
		return (
			normalizeKey(category?.slug) ||
			normalizeKey(category?.name) ||
			normalizeKey(item?.category_slug) ||
			normalizeKey(item?.category) ||
			normalizeKey(item?.category_title) ||
			"uncategorized"
		);
	}

	function resolveCategoryTitle(category = {}, item = {}) {
		return (
			normalizeKey(category?.title) ||
			normalizeKey(category?.name) ||
			normalizeKey(item?.category_title) ||
			normalizeKey(item?.category) ||
			"سایر محصولات"
		);
	}

	function resolveSubcategoryKey(subcategory = {}, item = {}) {
		return (
			normalizeKey(subcategory?.slug) ||
			normalizeKey(subcategory?.name) ||
			normalizeKey(item?.subcategory_slug) ||
			normalizeKey(item?.subcategory) ||
			normalizeKey(item?.subcategory_title)
		);
	}

	function resolveSubcategoryTitle(subcategory = {}, item = {}) {
		return (
			normalizeKey(subcategory?.title) ||
			normalizeKey(subcategory?.name) ||
			normalizeKey(item?.subcategory_title) ||
			normalizeKey(item?.subcategory)
		);
	}

	function ensureCategoryBucket(category = {}, item = {}) {
		const key = resolveCategoryKey(category, item);
		if (categoryMap.has(key)) {
			return categoryMap.get(key);
		}

		const bucket = {
			key,
			title: resolveCategoryTitle(category, item),
			items: [],
			groups: [],
			groupMap: new Map(),
		};
		categoryMap.set(key, bucket);
		categoryBuckets.push(bucket);
		return bucket;
	}

	function ensureSubcategoryBucket(categoryBucket, subcategory = {}, item = {}) {
		const key = resolveSubcategoryKey(subcategory, item) || "__misc__";
		if (categoryBucket.groupMap.has(key)) {
			return categoryBucket.groupMap.get(key);
		}

		const title = key === "__misc__" ? "" : resolveSubcategoryTitle(subcategory, item);
		const bucket = {
			key,
			title,
			items: [],
		};
		categoryBucket.groupMap.set(key, bucket);
		categoryBucket.groups.push(bucket);
		return bucket;
	}

	for (const category of categoryRows) {
		const categoryBucket = ensureCategoryBucket(category);
		for (const subcategory of Array.isArray(category?.subcategories) ? category.subcategories : []) {
			ensureSubcategoryBucket(categoryBucket, subcategory);
		}
	}

	for (const item of productRows) {
		const categoryKey =
			normalizeKey(item?.category_slug) ||
			normalizeKey(item?.category) ||
			normalizeKey(item?.category_title);
		const matchedCategory =
			categoryRows.find((row) => resolveCategoryKey(row) === categoryKey) || {};
		const categoryBucket = ensureCategoryBucket(matchedCategory, item);
		categoryBucket.items.push(item);
		const subgroup = ensureSubcategoryBucket(categoryBucket, {}, item);
		subgroup.items.push(item);
	}

	return categoryBuckets
		.filter((category) => category.items.length > 0)
		.map((category) => {
			const visibleGroups = category.groups.filter((group) => group.items.length > 0);
			const showGroupHeading =
				visibleGroups.length > 1 ||
				visibleGroups.some((group) => Boolean(String(group.title || "").trim()));

			return {
				key: category.key,
				title: category.title,
				groups: visibleGroups.map((group) => ({
					...group,
					title: showGroupHeading ? group.title : "",
				})),
				countLabel: `${category.items.length.toLocaleString("fa-IR")} آیتم`,
			};
		});
});

function openDropdown() {
	dropdownOpen.value = true;
	activeIndex.value = dropdownOptions.value.length ? 0 : -1;
}

function onBlur() {
	setTimeout(() => {
		dropdownOpen.value = false;
		activeIndex.value = -1;
	}, 130);
}

function moveActive(step) {
	if (!dropdownOpen.value) {
		openDropdown();
		return;
	}
	const len = dropdownOptions.value.length;
	if (!len) return;
	const cur = activeIndex.value < 0 ? 0 : activeIndex.value;
	activeIndex.value = (cur + step + len) % len;
}

function selectActive() {
	if (!dropdownOpen.value || !dropdownOptions.value.length) return;
	const idx = activeIndex.value < 0 ? 0 : activeIndex.value;
	pickCustomer(dropdownOptions.value[idx]);
}

function pickCustomer(customer) {
	if (customer?.is_new) {
		emit("create-customer", customer);
	} else {
		emit("select-customer", customer);
	}
	dropdownOpen.value = false;
	activeIndex.value = -1;
}

function displayQty(slug) {
	const raw = quantityValue(slug);
	if (!raw) {
		return "۰";
	}
	if (Math.abs(raw - Math.round(raw)) < 0.0001) {
		return Math.round(raw).toLocaleString("fa-IR");
	}
	return Number(raw.toFixed(3)).toLocaleString("fa-IR", { maximumFractionDigits: 3 });
}

function quantityValue(slug) {
	return Number(props.quantityMap?.[slug] || 0);
}

function supportsCustomization(item = {}) {
	return Boolean(
		Number(item?.has_customization || 0) === 1 ||
		Number(item?.restaurant_builder_active || 0) === 1,
	);
}
</script>

<style scoped>
.products-panel {
	border-radius: 18px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	padding: 0.65rem;
	color: var(--pos-text);
	height: 100%;
	display: grid;
	grid-template-rows: auto auto 1fr;
	overflow: hidden;
	gap: 0.4rem;
}

.customer-search-bar {
	display: grid;
	grid-template-columns: 1fr 36px;
	gap: 0.4rem;
	align-items: center;
}

.customer-search-wrap {
	position: relative;
	display: grid;
	grid-template-columns: 26px 1fr auto;
	align-items: center;
	border-radius: 12px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	padding: 0 0.45rem;
}

.cust-icon {
	font-size: 0.85rem;
	opacity: 0.65;
}

.cust-input {
	border: 0;
	background: transparent;
	padding-right: 0;
	font-size: 0.82rem;
}

.cust-clear {
	border: 0;
	background: transparent;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
	cursor: pointer;
	width: 22px;
	height: 22px;
	border-radius: 999px;
	font-size: 0.9rem;
	line-height: 1;
	display: flex;
	align-items: center;
	justify-content: center;
}

.cust-dropdown {
	position: absolute;
	top: calc(100% + 0.3rem);
	inset-inline: 0;
	border-radius: 12px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	box-shadow: 0 14px 24px rgb(var(--pos-primary-rgb, 1 90 114) / 0.14);
	max-height: 240px;
	overflow-y: auto;
	z-index: 50;
}

.cust-option {
	width: 100%;
	border: 0;
	border-bottom: 1px solid rgb(var(--pos-primary-rgb, 1 90 114) / 0.1);
	background: transparent;
	color: var(--pos-text);
	padding: 0.38rem 0.55rem;
	display: grid;
	gap: 0.1rem;
	text-align: right;
	cursor: pointer;
	font-family: inherit;
}

.cust-option:last-of-type {
	border-bottom: 0;
}

.cust-option.active,
.cust-option:hover {
	background: var(--pos-soft);
}

.cust-option-name {
	font-size: 0.8rem;
	font-weight: 600;
}

.cust-option-meta {
	display: inline-flex;
	gap: 0.4rem;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.68);
	font-size: 0.69rem;
}

.cust-new-tag {
	background: rgb(var(--pos-accent-rgb, 255 152 54) / 0.15);
	color: var(--pos-accent);
	border-radius: 999px;
	padding: 0.05rem 0.4rem;
}

.cust-empty {
	padding: 0.5rem;
	font-size: 0.75rem;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.68);
	text-align: center;
}

.cust-add-btn {
	width: 36px;
	height: 36px;
	border-radius: 10px;
	border: 1px solid var(--pos-accent);
	background: var(--pos-accent);
	color: #fff;
	font-size: 1.2rem;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.panel-top {
	display: grid;
	gap: 0.45rem;
	flex-shrink: 0;
}

.toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.65rem;
}

.search-box {
	display: grid;
	grid-template-columns: 24px 1fr auto;
	align-items: center;
	border-radius: 12px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	padding: 0 0.55rem;
	flex: 1;
	min-height: 44px;
}

.search-box .input {
	border: 0;
	background: transparent;
	padding-right: 0;
	font-size: 0.95rem;
}

.clear-search-btn {
	border: 0;
	background: transparent;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.66);
	cursor: pointer;
	width: 24px;
	height: 24px;
	border-radius: 999px;
	font-size: 1rem;
	line-height: 1;
}

.clear-search-btn:hover {
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.1);
	color: var(--pos-primary);
}

.icon {
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

.view-toggle {
	display: inline-flex;
	border: 1px solid var(--pos-border);
	border-radius: 11px;
	overflow: hidden;
	flex-shrink: 0;
}

.view-toggle button {
	border: 0;
	background: var(--pos-white);
	color: var(--pos-text);
	padding: 0.55rem 0.75rem;
	cursor: pointer;
	font-size: 1.05rem;
	line-height: 1;
	min-width: 44px;
	min-height: 44px;
}

.view-toggle button.active {
	background: var(--pos-primary);
	color: var(--pos-white);
}

.scan-row {
	display: grid;
	grid-template-columns: 1fr auto;
	gap: 0.45rem;
}

.scan-btn {
	border: 1px solid var(--pos-primary);
	background: var(--pos-primary);
	border-radius: 10px;
	color: var(--pos-white);
	padding: 0.55rem 1rem;
	cursor: pointer;
	font-family: inherit;
	font-size: 0.88rem;
	font-weight: 600;
	min-height: 44px;
}

.scan-feedback {
	margin: 0;
	color: var(--pos-primary);
	font-size: 0.77rem;
}

.category-bar {
	display: flex;
	gap: 0.3rem;
	overflow-x: auto;
	padding-bottom: 0.15rem;
	scrollbar-width: thin;
	scrollbar-color: var(--pos-border) transparent;
}

.category-bar::-webkit-scrollbar {
	height: 3px;
}

.category-bar::-webkit-scrollbar-thumb {
	background: var(--pos-border);
	border-radius: 99px;
}

.cat-chip {
	border: 1px solid var(--pos-border);
	border-radius: 999px;
	padding: 0.5rem 0.95rem;
	background: var(--pos-white);
	color: var(--pos-text);
	cursor: pointer;
	white-space: nowrap;
	font-size: 0.85rem;
	font-weight: 500;
	font-family: inherit;
	flex-shrink: 0;
	min-height: 40px;
	transition: all 0.15s ease;
}

.cat-chip:hover {
	background: var(--pos-soft);
	border-color: var(--pos-primary);
}

.cat-chip.active {
	background: var(--pos-primary);
	color: var(--pos-white);
	border-color: var(--pos-primary);
	font-weight: 700;
	box-shadow: 0 2px 8px rgb(var(--pos-primary-rgb, 1 90 114) / 0.25);
}

.hint {
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
	margin: 0;
}

.error {
	color: var(--pos-accent);
	margin: 0;
}

.products-sections {
	display: grid;
	gap: 0.9rem;
	overflow-y: auto;
	overflow-x: hidden;
	align-content: start;
	min-height: 0;
	padding-inline-end: 0.25rem;
}

.category-section {
	display: grid;
	gap: 0.7rem;
}

.category-section-head {
	display: flex;
	align-items: flex-end;
	justify-content: space-between;
	gap: 0.65rem;
	padding-bottom: 0.45rem;
	border-bottom: 1px solid rgb(var(--pos-primary-rgb, 1 90 114) / 0.12);
}

.category-section-copy {
	display: grid;
	gap: 0.18rem;
}

.category-section-copy h3 {
	margin: 0;
	font-size: 1rem;
	font-weight: 800;
	color: var(--pos-text);
}

.category-section-copy p {
	margin: 0;
	font-size: 0.76rem;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.64);
}

.subcategory-stack {
	display: grid;
	gap: 0.75rem;
}

.subcategory-section {
	display: grid;
	gap: 0.5rem;
}

.subcategory-section-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.65rem;
}

.subcategory-section-head h4 {
	margin: 0;
	font-size: 0.82rem;
	font-weight: 700;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.84);
}

.subcategory-section-head span {
	font-size: 0.72rem;
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.58);
}

.products-grid {
	display: grid;
	gap: 0.45rem;
	align-content: start;
}

.products-grid.mode-grid {
	grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
}

.products-grid.mode-list {
	grid-template-columns: 1fr;
	gap: 0.35rem;
}

.products-grid.mode-compact {
	grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
	gap: 0.3rem;
}

.product-card {
	border: 1px solid var(--pos-border);
	border-radius: 10px;
	background: var(--pos-white);
	display: flex;
	flex-direction: column;
	box-shadow: 0 1px 3px rgb(0 0 0 / 0.03);
	cursor: pointer;
	transition:
		transform 0.15s ease,
		box-shadow 0.15s ease,
		border-color 0.15s ease;
}

.product-card:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 12px rgb(0 0 0 / 0.08);
	border-color: var(--pos-primary);
}

.product-card:active {
	transform: translateY(0);
	box-shadow: 0 1px 3px rgb(0 0 0 / 0.04);
}

.products-grid.mode-list .product-card {
	flex-direction: row;
	align-items: center;
}

.image-btn {
	border: 0;
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.04);
	padding: 0;
	cursor: pointer;
	width: 100%;
	display: block;
	aspect-ratio: 4 / 3;
	overflow: hidden;
	flex-shrink: 0;
}

.products-grid.mode-list .image-btn {
	width: 56px;
	height: 56px;
	aspect-ratio: 1 / 1;
	border-radius: 8px;
	margin: 0.3rem;
}

.product-image {
	width: 100%;
	height: 100%;
	object-fit: contain;
	object-position: center;
	display: block;
}

.product-body {
	padding: 0.35rem 0.5rem 0.2rem;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 0.15rem;
	flex: 1;
	min-width: 0;
}

.products-grid.mode-list .product-body {
	flex-direction: row;
	align-items: center;
	justify-content: space-between;
	flex: 1;
	padding: 0.35rem 0.55rem;
	gap: 0.4rem;
}

.product-body h4 {
	margin: 0;
	font-size: 0.76rem;
	line-height: 1.3;
	font-weight: 600;
	color: var(--pos-text);
	word-break: break-word;
}

.products-grid.mode-list .product-body h4 {
	font-size: 0.8rem;
}

.product-body strong {
	font-size: 0.74rem;
	font-weight: 700;
	color: var(--pos-accent);
	flex-shrink: 0;
	font-variant-numeric: tabular-nums;
}

.product-actions {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.35rem;
	padding: 0.25rem 0.45rem 0.35rem;
	margin-top: auto;
}

.products-grid.mode-list .product-actions {
	padding: 0.3rem 0.55rem;
	margin-top: 0;
	flex-shrink: 0;
}

.counter {
	display: inline-flex;
	align-items: center;
	gap: 0.15rem;
}

.counter button {
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	color: var(--pos-primary);
	cursor: pointer;
	font-size: 0.95rem;
	font-weight: 600;
	transition: background 0.12s ease;
}

.counter button:hover {
	background: var(--pos-soft);
}

.counter span {
	min-width: 28px;
	text-align: center;
	font-size: 0.78rem;
	font-weight: 600;
	font-variant-numeric: tabular-nums;
}

.bom-btn {
	border: 1px solid var(--pos-accent);
	background: var(--pos-accent);
	color: var(--pos-white);
	border-radius: 8px;
	padding: 0.3rem 0.6rem;
	cursor: pointer;
	font-size: 0.72rem;
	font-weight: 600;
	min-height: 28px;
	transition: opacity 0.12s ease;
}

.bom-btn:hover {
	opacity: 0.88;
}

.dark-input {
	border: 1px solid var(--pos-border);
	background: var(--pos-white);
	color: var(--pos-text);
}

.dark-input::placeholder {
	color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

.compact-card {
	border: 1px solid var(--pos-border);
	border-radius: 12px;
	background: var(--pos-white);
	display: grid;
	gap: 0.4rem;
	transition: all 0.12s;
	position: relative;
	padding: 0.55rem;
	min-height: 112px;
}

.compact-card:hover {
	border-color: var(--pos-primary);
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.04);
}

.compact-card.has-qty {
	border-color: var(--pos-primary);
	background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.06);
}

.compact-name {
	font-size: 0.83rem;
	font-weight: 700;
	color: var(--pos-primary);
	line-height: 1.45;
	display: block;
}

.compact-price {
	font-size: 0.74rem;
	color: var(--pos-accent);
	display: block;
	font-weight: 700;
}

.compact-qty {
	position: absolute;
	top: 0.45rem;
	left: 0.45rem;
	background: var(--pos-primary);
	color: #fff;
	border-radius: 999px;
	font-size: 0.68rem;
	padding: 0.14rem 0.42rem;
	font-weight: 700;
}

.compact-main-btn {
	border: 0;
	background: transparent;
	padding: 0;
	text-align: right;
	cursor: pointer;
	font-family: inherit;
	display: grid;
	gap: 0.22rem;
	align-content: start;
	min-height: 62px;
}

.compact-actions {
	display: flex;
	align-items: center;
	gap: 0.35rem;
	margin-top: auto;
}

.compact-action-btn {
	width: 34px;
	height: 34px;
	border-radius: 9px;
	border: 1px solid var(--pos-border);
	background: color-mix(in srgb, var(--pos-white) 92%, transparent);
	color: var(--pos-primary);
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.15s ease;
}

.compact-action-btn:hover {
	background: var(--pos-soft);
	border-color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.25);
}

.compact-action-btn--primary {
	background: var(--pos-primary);
	color: var(--pos-white);
	border-color: var(--pos-primary);
}

.compact-action-btn--primary:hover {
	filter: brightness(0.96);
	background: var(--pos-primary);
}

@media (max-width: 1200px) {
	.products-grid.mode-grid {
		grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
	}
}

@media (max-width: 860px) {
	.products-grid.mode-grid {
		grid-template-columns: repeat(auto-fill, minmax(115px, 1fr));
	}
	.products-grid.mode-list .product-card {
		flex-direction: column;
		align-items: stretch;
	}
	.products-grid.mode-list .image-btn {
		width: 100%;
		height: auto;
		margin: 0;
		border-radius: 0;
	}
}
</style>
