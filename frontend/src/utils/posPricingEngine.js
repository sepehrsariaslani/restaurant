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

  const baseArgs = { ...args, targetPayableAmount: null }
  const baseTotals = calculateTotalsWithoutTarget(baseArgs)
  const desired = clamp(target, 0, baseTotals.payableAmount)
  let low = 0
  let high = baseTotals.itemsTotal

  // Find the fixed discount that makes the payable amount converge to the
  // requested final invoice amount, including percentage tax/service and wallet rules.
  for (let index = 0; index < 42; index += 1) {
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
    targetPayableAmount: desired,
    automaticDiscount: true,
  }
}
