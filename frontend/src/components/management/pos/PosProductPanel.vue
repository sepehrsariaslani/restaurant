<template>
	<section class="products-panel">
		<div class="customer-row">
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
			<DsButton
				variant="primary"
				size="sm"
				class="cust-add-btn"
				@click="$emit('add-customer')"
				title="مشتری جدید"
				aria-label="مشتری جدید"
			>
				<Plus :size="15" :stroke-width="2.4" />
			</DsButton>

			<div
				v-if="secondaryCustomerVisible"
				class="secondary-customer-field"
				:title="'نام مشتری ثانویه (سفارش‌دهنده) — از لیست مشتری‌ها انتخاب کنید یا نام جدید بنویسید'"
			>
				<span class="sc-icon"><UserRound :size="14" :stroke-width="2.1" /></span>
				<div class="sc-wrap">
					<input
						class="input dark-input sc-input"
						:value="secondaryCustomer"
						@input="onSecondaryInput"
						@focus="openSecondaryDropdown"
						@blur="onSecondaryBlur"
						@keydown.down.prevent="moveSecondaryActive(1)"
						@keydown.up.prevent="moveSecondaryActive(-1)"
						@keydown.enter.prevent="selectSecondaryActive"
						@keydown.esc="closeSecondaryDropdown"
						placeholder="مشتری ثانویه..."
					/>
					<div
						v-if="secondaryDropdownOpen && secondaryDropdownOptions.length"
						class="cust-dropdown"
					>
						<button
							v-for="(customer, index) in secondaryDropdownOptions"
							:key="customer.key || index"
							type="button"
							class="cust-option"
							:class="{ active: index === secondaryActiveIndex }"
							@mousedown.prevent="pickSecondaryCustomer(customer)"
						>
							<span class="cust-option-name">{{ customer.is_new ? `جدید: ${customer.label}` : customer.label }}</span>
							<span class="cust-option-meta">
								<span v-if="customer.is_new" class="cust-new-tag">جدید</span>
								<span v-if="customer.mobile">{{ customer.mobile }}</span>
								<span>{{ Number(customer.orders_count || 0).toLocaleString('fa-IR') }} خرید</span>
							</span>
						</button>
					</div>
				</div>
				<button
					v-if="secondaryCustomer"
					type="button"
					class="sc-clear"
					title="پاک کردن مشتری ثانویه"
					aria-label="پاک کردن مشتری ثانویه"
					@click="clearSecondaryCustomer"
				>
					×
				</button>
			</div>
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
						aria-label="نمای شبکه‌ای"
					>
						<Grid2x2 :size="16" :stroke-width="2.2" />
					</button>
					<button
						type="button"
						:class="{ active: productView === 'compact' }"
						@click="$emit('update:productView', 'compact')"
						title="فشرده بدون عکس"
						aria-label="نمای فشرده"
					>
						<Rows3 :size="16" :stroke-width="2.2" />
					</button>
					<button
						type="button"
						:class="{ active: productView === 'list' }"
						@click="$emit('update:productView', 'list')"
						title="لیستی"
						aria-label="نمای لیستی"
					>
						<List :size="16" :stroke-width="2.2" />
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
				<DsButton variant="primary" size="sm" class="scan-btn" @click="$emit('scan-scale')">
					تحلیل بارکد
				</DsButton>
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
							<ManagementPosProductCard
								v-for="item in group.items"
								:key="item.slug || item.name"
								:item="item"
								:view="productView"
								:quantity="quantityValue(item.slug)"
								:currency="currency"
								:fallback-image="fallbackImage"
								@increment="$emit('increment-product', item)"
								@decrement="$emit('decrement-product', item)"
								@open-bom="$emit('open-bom', item)"
								@quick-edit="$emit('quick-edit', item)"
							/>
						</div>
					</section>
				</div>
			</section>
		</div>
	</section>
</template>

<script setup>
import { computed, ref } from "vue";
import { Grid2x2, List, Plus, Rows3, Search, UserRound } from "lucide-vue-next";
import DsButton from "@/components/design/DsButton.vue";
import ManagementPosProductCard from "@/components/management/pos/ManagementPosProductCard.vue";

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
	secondaryCustomer: { type: String, default: "" },
	secondaryCustomerVisible: { type: Boolean, default: false },
});

const emit = defineEmits([
	"update:searchTerm",
	"update:productView",
	"update:selectedCategory",
	"increment-product",
	"decrement-product",
	"open-bom",
	"quick-edit",
	"update:scannerInput",
	"scan-scale",
	"update:customerQuery",
	"select-customer",
	"create-customer",
	"add-customer",
	"update:secondaryCustomer",
	"secondary-query",
]);

const customerInputRef = ref(null);
const dropdownOpen = ref(false);
const activeIndex = ref(-1);

// دراپ‌داون «مشتری ثانویه» — از همان لیست مشتری‌ها
const secondaryDropdownOpen = ref(false);
const secondaryActiveIndex = ref(-1);
const secondaryQuery = ref("");

const secondaryFilteredOptions = computed(() => {
	const all = Array.isArray(props.customerOptions) ? props.customerOptions : [];
	const q = String(secondaryQuery.value || "")
		.trim()
		.toLowerCase();
	if (!q) return all.slice(0, 8);
	const digits = q.replace(/\D/g, "");
	return all
		.filter((c) => {
			const label = String(c.label || "").toLowerCase();
			const mobile = String(c.mobile || "");
			if (label.includes(q)) return true;
			if (digits && mobile.replace(/\D/g, "").includes(digits)) return true;
			return false;
		})
		.slice(0, 8);
});

const secondaryCreateOption = computed(() => {
	const q = String(secondaryQuery.value || "").trim();
	// گزینه «جدید» فقط وقتی نمایش داده می‌شود که هیچ مشتری‌ای با این نام پیدا نشود
	// تا تایپ «زهرا» + Enter اشتباهاً «زهرا» جدید نسازد و «زهرا قاسمی» انتخاب شود
	if (!q || secondaryFilteredOptions.value.length) return null;
	return {
		key: `sec-create-${q}`,
		label: q,
		mobile: "",
		orders_count: 0,
		is_new: true,
	};
});

const secondaryDropdownOptions = computed(() => {
	const opts = [...secondaryFilteredOptions.value];
	if (secondaryCreateOption.value) opts.unshift(secondaryCreateOption.value);
	return opts;
});

function onSecondaryInput(event) {
	const value = event.target.value;
	secondaryQuery.value = value;
	emit("update:secondaryCustomer", value);
	emit("secondary-query", value);
	secondaryDropdownOpen.value = true;
	secondaryActiveIndex.value = -1;
}

function openSecondaryDropdown() {
	secondaryQuery.value = String(props.secondaryCustomer || "");
	secondaryDropdownOpen.value = true;
	secondaryActiveIndex.value = -1;
}

function onSecondaryBlur() {
	// فرصت بده کلیک روی گزینه‌های دراپ‌داون اول اجرا شود
	window.setTimeout(() => {
		secondaryDropdownOpen.value = false;
	}, 120);
}

function closeSecondaryDropdown() {
	secondaryDropdownOpen.value = false;
}

function moveSecondaryActive(delta) {
	const count = secondaryDropdownOptions.value.length;
	if (!count) return;
	secondaryActiveIndex.value = (secondaryActiveIndex.value + delta + count) % count;
}

function selectSecondaryActive() {
	const option = secondaryDropdownOptions.value[secondaryActiveIndex.value];
	if (option) pickSecondaryCustomer(option);
}

function pickSecondaryCustomer(customer) {
	if (!customer) return;
	const name = String(customer.label || "").trim();
	emit("update:secondaryCustomer", name);
	secondaryQuery.value = name;
	secondaryDropdownOpen.value = false;
	secondaryActiveIndex.value = -1;
}

function clearSecondaryCustomer() {
	emit("update:secondaryCustomer", "");
	secondaryQuery.value = "";
	secondaryDropdownOpen.value = false;
	secondaryActiveIndex.value = -1;
}

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

</script>

<style scoped>
.products-panel {
	/* Use the page-level management tokens directly. The previous
	 * self-referential aliases made some controls resolve to `unset` in
	 * Chromium (especially after the cart changed state). */
	--pos-white: var(--mg-bg-surface);
	--pos-primary: var(--mg-primary);
	--pos-primary-rgb: var(--mg-primary-rgb);
	--pos-success: var(--mg-success);
	--pos-success-rgb: var(--mg-success-rgb);
	--pos-border: var(--mg-border-light);
	--pos-page: var(--mg-bg-page);
	border-radius: 24px;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 95%, transparent);
	background: linear-gradient(180deg, color-mix(in srgb, var(--mg-bg-surface) 62%, var(--mg-bg-surface) 38%) 0%, color-mix(in srgb, var(--mg-bg-surface) 96%, var(--mg-bg-surface) 4%) 100%);
	padding: 0.9rem;
	color: var(--mg-text-main);
	height: 100%;
	display: grid;
	grid-template-rows: auto auto 1fr;
	overflow: hidden;
	gap: 0.65rem;
	box-shadow: 0 22px 44px rgb(52 38 31 / 0.08);
}

.customer-row {
	display: flex;
	align-items: center;
	gap: 0.55rem;
}

.customer-search-wrap {
	position: relative;
	flex: 1;
	min-width: 0;
	display: grid;
	grid-template-columns: 26px 1fr auto;
	align-items: center;
	border-radius: 14px;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
	background: var(--mg-bg-surface);
	padding: 0 0.65rem;
	min-height: 44px;
}

.cust-icon {
	font-size: 0.85rem;
	color: var(--mg-text-muted);
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
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.55);
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
	border-radius: 16px;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 88%, transparent);
	background: var(--mg-bg-surface);
	box-shadow: 0 22px 40px rgb(52 38 31 / 0.12);
	max-height: 240px;
	overflow-y: auto;
	z-index: 50;
}

.cust-option {
	width: 100%;
	border: 0;
	border-bottom: 1px solid rgb(var(--mg-primary-rgb, 1 90 114) / 0.1);
	background: transparent;
	color: var(--mg-text-main);
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
	background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface) 93%);
}

.cust-option-name {
	font-size: 0.8rem;
	font-weight: 600;
}

.cust-option-meta {
	display: inline-flex;
	gap: 0.4rem;
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.68);
	font-size: 0.69rem;
}

.cust-new-tag {
	background: rgb(var(--mg-primary-rgb, 255 152 54) / 0.15);
	color: var(--mg-primary);
	border-radius: 999px;
	padding: 0.05rem 0.4rem;
}

.cust-empty {
	padding: 0.5rem;
	font-size: 0.75rem;
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.68);
	text-align: center;
}

.secondary-customer-field {
	flex: 1;
	min-width: 0;
	display: grid;
	grid-template-columns: 26px 1fr auto;
	align-items: center;
	gap: 0.35rem;
	margin: 0;
	padding: 0 0.65rem;
	min-height: 44px;
	border-radius: 14px;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
	background: var(--mg-bg-surface);
}

.sc-icon {
	font-size: 0.85rem;
	color: var(--mg-text-muted);
	display: inline-flex;
}

.sc-wrap {
	position: relative;
	flex: 1;
	min-width: 0;
}

.sc-input {
	width: 100%;
	min-width: 0;
	min-height: 2rem;
	border-radius: 9px;
	font-size: 0.82rem;
	border: 0;
	background: transparent;
	padding-right: 0;
}

.sc-clear {
	border: 0;
	background: transparent;
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.55);
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

.cust-add-btn {
	width: 40px;
	min-height: 40px;
	padding: 0;
	border-radius: 12px;
	flex-shrink: 0;
}

.panel-top {
	display: grid;
	gap: 0.6rem;
	flex-shrink: 0;
	padding: 0.15rem 0 0.2rem;
}

.toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.8rem;
}

.search-box {
	display: grid;
	grid-template-columns: 24px 1fr auto;
	align-items: center;
	border-radius: 14px;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
	background: var(--mg-bg-surface);
	padding: 0 0.7rem;
	flex: 1;
	min-height: 48px;
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
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.66);
	cursor: pointer;
	width: 24px;
	height: 24px;
	border-radius: 999px;
	font-size: 1rem;
	line-height: 1;
}

.clear-search-btn:hover {
	background: rgb(var(--mg-primary-rgb, 1 90 114) / 0.1);
	color: var(--mg-primary);
}

.icon {
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.55);
}

.view-toggle {
	display: inline-flex;
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 95%, transparent);
	border-radius: 14px;
	overflow: hidden;
	flex-shrink: 0;
	background: color-mix(in srgb, var(--mg-bg-surface) 70%, var(--mg-bg-page) 30%);
}

.view-toggle button {
	border: 0;
	background: transparent;
	color: var(--mg-text-muted);
	padding: 0.7rem 0.82rem;
	cursor: pointer;
	min-width: 44px;
	min-height: 44px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
}

.view-toggle button.active {
	background: var(--mg-primary);
	color: var(--mg-bg-surface);
}

.scan-row {
	display: grid;
	grid-template-columns: 1fr auto;
	gap: 0.45rem;
}

.scan-btn {
	border: 1px solid var(--mg-primary);
	background: var(--mg-primary);
	border-radius: 14px;
	color: var(--mg-bg-surface);
	padding: 0.7rem 1rem;
	cursor: pointer;
	font-family: inherit;
	font-size: 0.88rem;
	font-weight: 600;
	min-height: 44px;
}

.scan-feedback {
	margin: 0;
	color: var(--mg-primary);
	font-size: 0.77rem;
}

.category-bar {
	display: flex;
	gap: 0.45rem;
	overflow-x: auto;
	padding-bottom: 0.15rem;
	scrollbar-width: thin;
	scrollbar-color: var(--mg-border-light) transparent;
}

.category-bar::-webkit-scrollbar {
	height: 3px;
}

.category-bar::-webkit-scrollbar-thumb {
	background: var(--mg-border-light);
	border-radius: 99px;
}

.cat-chip {
	border: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
	border-radius: 999px;
	padding: 0.58rem 1rem;
	background: color-mix(in srgb, var(--mg-bg-surface) 84%, var(--mg-bg-page) 16%);
	color: var(--mg-text-main);
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
	background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface) 93%);
	border-color: color-mix(in srgb, var(--mg-primary) 42%, var(--mg-border-light) 58%);
}

.cat-chip.active {
	background: var(--mg-primary);
	color: var(--mg-bg-surface);
	border-color: var(--mg-primary);
	font-weight: 700;
	box-shadow: 0 10px 24px color-mix(in srgb, var(--mg-primary) 22%, transparent);
}

.hint {
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.72);
	margin: 0;
}

.error {
	color: var(--mg-primary);
	margin: 0;
}

.products-sections {
	display: grid;
	gap: 1rem;
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
	padding-bottom: 0.55rem;
	border-bottom: 1px solid color-mix(in srgb, var(--mg-border-light) 96%, transparent);
}

.category-section-copy {
	display: grid;
	gap: 0.18rem;
}

.category-section-copy h3 {
	margin: 0;
	font-size: 1rem;
	font-weight: 800;
	color: var(--mg-text-main);
}

.category-section-copy p {
	margin: 0;
	font-size: 0.76rem;
	color: var(--mg-text-muted);
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
	color: var(--mg-primary);
}

.subcategory-section-head span {
	font-size: 0.72rem;
	color: var(--mg-text-muted);
}

.products-grid {
	display: grid;
	gap: 0.45rem;
	align-content: start;
}

.products-grid.mode-grid {
	grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
}

.products-grid.mode-list {
	grid-template-columns: 1fr;
	gap: 0.35rem;
}

.products-grid.mode-compact {
	grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
	gap: 0.45rem;
}

.dark-input {
	border: 1px solid var(--mg-border-light);
	background: var(--mg-bg-surface);
	color: var(--mg-text-main);
}

.dark-input::placeholder {
	color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.55);
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
}
</style>
