function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export function calculatePosTotals({
  cartLines = [],
  discountType = 'fixed',
  discountValue = 0,
  serviceType = 'fixed',
  serviceValue = 0,
  taxAmount = 0,
  tipAmount = 0,
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

  const tax = Math.max(toNumber(taxAmount, 0), 0)
  const tip = Math.max(toNumber(tipAmount, 0), 0)

  const payableAmount = Math.max(itemsTotal - discountAmount - walletApplied + tax + tip + serviceAmount, 0)

  return {
    itemsTotal,
    discountAmount,
    serviceAmount,
    walletApplied,
    taxAmount: tax,
    tipAmount: tip,
    payableAmount,
  }
}
