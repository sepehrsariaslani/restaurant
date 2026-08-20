function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function calculateTotalsWithoutTarget({
  cartLines = [],
  discountType = 'fixed',
  discountValue = 0,
  serviceType = 'fixed',
  serviceValue = 0,
  taxType = 'fixed',
  taxValue = 0,
  tipAmount = 0,
  packagingAmount = 0,
  useWallet = false,
  walletBalance = 0,
} = {}) {
  const itemsTotal = (cartLines || []).reduce((sum, line) => {
    return sum + toNumber(line.unit_price || line.price, 0) * toNumber(line.qty, 0)
  }, 0)

  const cleanDiscountValue = Math.max(toNumber(discountValue, 0), 0)
  const cleanServiceValue = Math.max(toNumber(serviceValue, 0), 0)

  const fixedDiscount = discountType === 'fixed' ? cleanDiscountValue : 0
  const percentDiscount = discountType === 'percent' ? (itemsTotal * cleanDiscountValue) / 100 : 0
  const discountAmount = clamp(fixedDiscount + percentDiscount, 0, itemsTotal)

  const fixedService = serviceType === 'fixed' ? cleanServiceValue : 0
  const percentService = serviceType === 'percent' ? (itemsTotal * cleanServiceValue) / 100 : 0
  const serviceAmount = Math.max(fixedService + percentService, 0)

  const walletCapacity = Math.max(itemsTotal - discountAmount, 0)
  const walletApplied = useWallet ? clamp(toNumber(walletBalance, 0), 0, walletCapacity) : 0

  const cleanTaxValue = Math.max(toNumber(taxValue, 0), 0)
  const taxableBase = Math.max(itemsTotal - discountAmount - walletApplied + serviceAmount, 0)
  const fixedTax = taxType === 'fixed' ? cleanTaxValue : 0
  const percentTax = taxType === 'percent' ? (taxableBase * cleanTaxValue) / 100 : 0
  const tax = Math.max(fixedTax + percentTax, 0)
  const tip = Math.max(toNumber(tipAmount, 0), 0)
  const packaging = Math.max(toNumber(packagingAmount, 0), 0)

  const payableAmount = Math.max(itemsTotal - discountAmount - walletApplied + tax + tip + serviceAmount + packaging, 0)

  return {
    itemsTotal,
    discountAmount,
    serviceAmount,
    walletApplied,
    taxAmount: tax,
    tipAmount: tip,
    packagingAmount: packaging,
    payableAmount,
  }
}

export function calculatePosTotals(args = {}) {
  const target = Number(args.targetPayableAmount)
  if (!Number.isFinite(target) || target <= 0) {
    return calculateTotalsWithoutTarget(args)
  }

  // هدف مبلغ نهایی است: مبلغی که مشتری باید بپردازد.
  // همه‌ی اجزا (تخفیف + حق سرویس + مالیات + پکیج + انعام) باید طوری
  // تنظیم شوند که جمع نهایی دقیقاً برابر همان هدف باشد — نه بیشتر.
  const desired = Math.max(target, 0)
  const baseArgs = { ...args, targetPayableAmount: null }

  // ۱) حالت بدون تخفیف: اگر حتی با صفر تخفیف، جمع نهایی از هدف کمتر است
  //    (یعنی هدف بزرگ‌تر از مبلغ کالاهاست) — مابه‌التفاوت به عنوان حق سرویس
  //    اضافه می‌شود تا مبلغ نهایی دقیقاً هدف باشد.
  const noDiscountTotals = calculateTotalsWithoutTarget({ ...baseArgs, discountType: 'fixed', discountValue: 0 })
  if (noDiscountTotals.payableAmount < desired) {
    const serviceAdjustment = desired - noDiscountTotals.payableAmount
    return {
      ...noDiscountTotals,
      serviceAmount: noDiscountTotals.serviceAmount + serviceAdjustment,
      payableAmount: desired,
      targetPayableAmount: desired,
      automaticDiscount: false,
      automaticService: serviceAdjustment > 0,
    }
  }

  // ۲) حالت با تخفیف: تخفیف ثابت را طوری پیدا می‌کنیم که جمع نهایی
  //    (با همان حق سرویس و مالیات و پکیج) دقیقاً برابر هدف شود.
  let low = 0
  let high = noDiscountTotals.itemsTotal

  for (let index = 0; index < 48; index += 1) {
    const candidate = (low + high) / 2
    const candidateTotals = calculateTotalsWithoutTarget({
      ...baseArgs,
      discountType: 'fixed',
      discountValue: candidate,
    })
    if (candidateTotals.payableAmount > desired) low = candidate
    else high = candidate
  }

  const result = calculateTotalsWithoutTarget({
    ...baseArgs,
    discountType: 'fixed',
    discountValue: high,
  })

  return {
    ...result,
    // اگر حق سرویس / مالیات / پکیج باعث شد مبلغ نهایی از هدف بیشتر شود،
    // تخفیف را کمی بیشتر می‌کنیم تا دقیقاً روی هدف بنشیند.
    discountAmount: Math.min(result.discountAmount + Math.max(result.payableAmount - desired, 0), result.itemsTotal),
    payableAmount: Math.max(desired, 0),
    targetPayableAmount: desired,
    automaticDiscount: true,
    automaticService: false,
  }
}
