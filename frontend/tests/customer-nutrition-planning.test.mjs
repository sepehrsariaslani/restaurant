import test from 'node:test'
import assert from 'node:assert/strict'

import { buildCalorieAwareMealSuggestions, calculateNutritionTargets, calculatePlanTotals, filterNutritionMenuProducts, hasNutritionValues, isNutritionBeverage, localWeekdayIndex } from '../src/utils/nutritionPlanning.js'
import { formatMoney } from '../src/utils/format.js'

test('distinguishes stored positive nutrition from default zero values', () => {
	assert.equal(hasNutritionValues({ nutrition: { kcal: 0, protein_g: 0 }, nutrition_verified: 0 }), false)
	assert.equal(hasNutritionValues({ nutrition: { kcal: 0, protein_g: 0 }, nutrition_verified: 1 }), true)
	assert.equal(hasNutritionValues({ nutrition: { kcal: 120, protein_g: 0 }, nutrition_verified: 0 }), true)
	assert.equal(hasNutritionValues({ nutrition: { kcal: 120, protein_g: null }, nutrition_verified: 0 }), false)
	assert.equal(hasNutritionValues({ nutrition: { kcal: null, protein_g: 20 }, nutrition_verified: 0 }), false)
	assert.equal(hasNutritionValues({ nutrition: { kcal: '', protein_g: 20 }, nutrition_verified: 0 }), false)
})

test('recognizes drinks from menu groups without treating a barbecue food name as a drink', () => {
	assert.equal(isNutritionBeverage({ title: 'اسپرسو', category_title: 'بار', subcategory_title: 'بار گرم' }), true)
	assert.equal(isNutritionBeverage({ title: 'گرم‌نوش طبیعت', category_title: 'بار', subcategory_title: 'دم‌نوش' }), true)
	assert.equal(isNutritionBeverage({ title: 'باربیکیو مرغ', category_title: 'کاسه' }), false)
})

test('keeps every branch menu item available in the planner regardless of review, stock, price, or meal-slot tags', () => {
	const menu = [
		{ name: 'SOUP-1', title: 'سوپ روز', nutrition_verified: 0, allergen_reviewed: 0, ingredients_reviewed: 0, out_of_stock: 1, base_price: 0, meal_slots: [] },
		{ name: 'SALAD-1', title: 'سالاد سبز', nutrition_verified: 1, allergen_reviewed: 1, ingredients_reviewed: 1, out_of_stock: 0, base_price: 120000, meal_slots: ['ناهار'] },
	]
	assert.deepEqual(filterNutritionMenuProducts(menu), menu)
	assert.deepEqual(filterNutritionMenuProducts(menu, 'سوپ'), [menu[0]])
	assert.deepEqual(filterNutritionMenuProducts(menu, 'SALAD-1'), [menu[1]])
})

test('calorie-aware suggestions use stored macros even before review, prefer target matches, and exclude water', () => {
	const product = (name, title, kcal, protein_g, meal_slots, category_title = '') => ({
		name, title, nutrition: { kcal, protein_g }, nutrition_verified: 0,
		allergen_reviewed: 1, ingredients_reviewed: 1, meal_slots, category_title,
		base_price: 100000, out_of_stock: 0, allergens: [], ingredient_tags: [],
	})
	const result = buildCalorieAwareMealSuggestions({
		branch: 'BRANCH-1', calorieTarget: 1900, proteinTarget: 60,
		catalog: [
			product('LUNCH-NEAR', 'ناهار مرغ', 650, 30, ['ناهار']),
			product('LUNCH-FAR', 'ناهار سبک', 280, 12, ['ناهار']),
			product('DINNER-NEAR', 'شام مرغ', 550, 25, ['شام']),
			product('DINNER-FAR', 'شام سنگین', 900, 30, ['شام']),
			product('WATER-1', 'آب واتا کوچولو', 0, 0, ['میان‌وعده']),
			product('ESPRESSO-1', 'اسپرسو', 650, 30, ['ناهار'], 'بار'),
			product('HERBAL-1', 'گرم‌نوش طبیعت', 190, 6, ['میان‌وعده'], 'بار'),
		],
	})
	const first = result.suggestions[0]
	assert.deepEqual(first.items.map((item) => item.item_code), ['LUNCH-NEAR', 'DINNER-NEAR', 'HERBAL-1'])
	assert.equal(result.suggestions.some((suggestion) => suggestion.items.some((item) => item.item_code === 'ESPRESSO-1')), true)
	assert.equal(result.suggestions.some((suggestion) => suggestion.items.some((item) => item.item_code === 'WATER-1')), false)
	assert.deepEqual(first.covered_slots, ['ناهار', 'شام', 'میان‌وعده'])
	assert.equal(first.full_day, false)
	assert.equal(first.branch, 'BRANCH-1')
	assert.equal(first.nutrition_reviewed, false)
	assert.equal(first.items[0].nutrition_verified, false)
	assert.match(result.reason, /صبحانه/)
	assert.match(result.reason, /مقادیر هنوز توسط مدیریت بازبینی نشده‌اند/)
})

test('ingredient preferences match first-level recipe ingredients when recipe data is available', () => {
	const base = {
		name: 'MEAL-1', title: 'سالاد مرغ', nutrition: { kcal: 420, protein_g: 28 },
		base_price: 21000000, out_of_stock: 0, meal_slots: ['ناهار'], allergens: [],
		ingredient_tags: ['مرغ', 'گردو'], nutrition_ingredient_tags: ['مرغ', 'گردو'],
		ingredient_composition_available: true, allergen_reviewed: 0, ingredients_reviewed: 0,
	}
	const result = buildCalorieAwareMealSuggestions({
		calorieTarget: 1900, allergens: ['گردو'], catalog: [base],
	})
	assert.deepEqual(result.suggestions, [])
	const liked = buildCalorieAwareMealSuggestions({
		calorieTarget: 1900, likedIngredients: ['مرغ'], catalog: [{ ...base, ingredient_tags: ['مرغ'], nutrition_ingredient_tags: ['مرغ'] }],
	})
	assert.equal(liked.suggestions.length, 3)
})

test('nutrition plan prices show ERP IRR values as customer-facing toman', () => {
	assert.equal(formatMoney(21000000, 'TOMAN'), '۲.۱۰۰.۰۰۰ تومان')
})

test('does not fabricate suggestions when calorie or protein values are missing or calories are zero', () => {
	const result = buildCalorieAwareMealSuggestions({
		calorieTarget: 1800,
		catalog: [
			{ name: 'WATER-1', title: 'آب واتا کوچولو', nutrition: { kcal: 0, protein_g: 0 }, nutrition_verified: 0, base_price: 10000, meal_slots: ['میان‌وعده'] },
			{ name: 'UNKNOWN-1', title: 'خوراک نامشخص', nutrition: { kcal: null, protein_g: null }, nutrition_verified: 0, base_price: 10000, meal_slots: ['ناهار'] },
		],
	})
	assert.deepEqual(result.suggestions, [])
	assert.match(result.reason, /کالریِ بیشتر از صفر و مقدار پروتئین ثبت‌شده/)
})

test('keeps nutrition-bearing menu items in plans when price or current stock is unavailable', () => {
	const result = buildCalorieAwareMealSuggestions({
		calorieTarget: 1800,
		catalog: [{
			name: 'TEMPORARILY-UNAVAILABLE', title: 'خوراک دارای اطلاعات تغذیه',
			nutrition: { kcal: 480, protein_g: 32 }, nutrition_verified: 1,
			base_price: 0, out_of_stock: 1, meal_slots: ['ناهار'],
		}],
	})
	assert.equal(result.suggestions.length, 3)
	assert.ok(result.suggestions.every((suggestion) => suggestion.items[0].item_code === 'TEMPORARILY-UNAVAILABLE'))
})

test('estimates BMI, maintenance calories, goal calories, and reference protein for an adult', () => {
	const result = calculateNutritionTargets({
		age_years: 30,
		formula_sex: 'مرد',
		height_cm: 180,
		weight_kg: 80,
		activity_level: 'فعالیت متوسط',
		goal: 'کاهش وزن',
	})
	assert.equal(result.bmi, 24.7)
	assert.equal(result.maintenance_kcal, 2759)
	assert.equal(result.calorie_target_kcal, 2483)
	assert.equal(result.protein_reference_g, 64)
	assert.equal(result.estimate_available, true)
})

test('does not calculate automatic targets for specialist cases or an underweight weight-loss goal', () => {
	const specialist = calculateNutritionTargets({ needs_specialist: true, height_cm: 170, weight_kg: 70, age_years: 30 })
	assert.equal(specialist.maintenance_kcal, null)
	assert.equal(specialist.estimate_available, false)
	assert.equal(specialist.protein_reference_g, null)

	const underweight = calculateNutritionTargets({
		age_years: 24,
		formula_sex: 'زن',
		height_cm: 170,
		weight_kg: 48,
		activity_level: 'کم‌تحرک',
		goal: 'کاهش وزن',
	})
	assert.equal(underweight.estimate_available, false)
	assert.equal(underweight.calorie_target_kcal, null)
})

test('supports manual calorie goals when formula inputs are missing but requires adult age for suggestions', () => {
	const result = calculateNutritionTargets({ age_years: 30, calorie_target: 1900, weight_kg: 70 })
	assert.equal(result.calorie_target_kcal, 1900)
	assert.equal(result.estimate_available, true)
	assert.equal(result.protein_reference_g, 56)

	const ageMissing = calculateNutritionTargets({ calorie_target: 1900, weight_kg: 70 })
	assert.equal(ageMissing.calorie_target_kcal, 1900)
	assert.equal(ageMissing.estimate_available, false)
	assert.equal(ageMissing.protein_reference_g, null)
})

test('does not show adult protein references for minors', () => {
	const result = calculateNutritionTargets({ age_years: 16, weight_kg: 60, calorie_target: 2000 })
	assert.equal(result.estimate_available, false)
	assert.equal(result.calorie_target_kcal, null)
	assert.equal(result.protein_reference_g, null)
})

test('adds stored restaurant nutrition before review and manual foods without treating unknown values as zero', () => {
	const result = calculatePlanTotals([
		{ source_type: 'وی‌درخت', item_code: 'FOOD-1', qty: 2 },
		{ source_type: 'ثبت دستی', manual_name: 'میوه', qty: 1, nutrition: { kcal: 70, protein_g: 1 } },
		{ source_type: 'ثبت دستی', manual_name: 'چای', qty: 1, nutrition: { kcal: null, protein_g: null } },
	], {
		'FOOD-1': { nutrition_verified: false, nutrition: { kcal: 300, protein_g: 25, carb_g: 12, fat_g: 8 }, base_price: 180000 },
	})
	assert.equal(result.totals.kcal, 670)
	assert.equal(result.totals.protein_g, 51)
	assert.equal(result.totals.price, 360000)
	assert.equal(result.complete, false)
	assert.deepEqual(result.unknownNutrition, ['چای'])
	assert.deepEqual(result.unreviewedNutrition, ['FOOD-1'])
})

test('treats unreviewed zero-value product defaults as missing nutrition in plan totals', () => {
	const result = calculatePlanTotals([
		{ source_type: 'وی‌درخت', item_code: 'UNREVIEWED-1', qty: 1 },
	], {
		'UNREVIEWED-1': { title: 'آب واتا کوچولو', nutrition_verified: 0, nutrition: { kcal: 0, protein_g: 0 }, base_price: 12000 },
	})
	assert.equal(result.complete, false)
	assert.deepEqual(result.unknownNutrition, ['آب واتا کوچولو'])
	assert.deepEqual(result.unreviewedNutrition, [])
})

test('maps the local week to Saturday-first weekdays', () => {
	assert.equal(localWeekdayIndex(new Date('2026-09-26T12:00:00+03:30')), 0)
	assert.equal(localWeekdayIndex(new Date('2026-09-27T12:00:00+03:30')), 1)
})
