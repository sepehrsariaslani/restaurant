import test from 'node:test'
import assert from 'node:assert/strict'

import { calculateNutritionTargets, calculatePlanTotals, localWeekdayIndex } from '../src/utils/nutritionPlanning.js'

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

test('adds verified restaurant nutrition and manual foods without treating unknown values as zero', () => {
	const result = calculatePlanTotals([
		{ source_type: 'وی‌درخت', item_code: 'FOOD-1', qty: 2 },
		{ source_type: 'ثبت دستی', manual_name: 'میوه', qty: 1, nutrition: { kcal: 70, protein_g: 1 } },
		{ source_type: 'ثبت دستی', manual_name: 'چای', qty: 1, nutrition: { kcal: null, protein_g: null } },
	], {
		'FOOD-1': { nutrition_verified: true, nutrition: { kcal: 300, protein_g: 25, carb_g: 12, fat_g: 8 }, base_price: 180000 },
	})
	assert.equal(result.totals.kcal, 670)
	assert.equal(result.totals.protein_g, 51)
	assert.equal(result.totals.price, 360000)
	assert.equal(result.complete, false)
	assert.deepEqual(result.unknownNutrition, ['چای'])
})

test('maps the local week to Saturday-first weekdays', () => {
	assert.equal(localWeekdayIndex(new Date('2026-09-26T12:00:00+03:30')), 0)
	assert.equal(localWeekdayIndex(new Date('2026-09-27T12:00:00+03:30')), 1)
})
