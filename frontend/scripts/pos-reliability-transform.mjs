export function transformPosReliabilityPage(input) {
  let code = String(input || '')

  code = code.replaceAll(
    '@page { margin: 0; }',
    '@page { margin: 0; }\n*, *::before, *::after { box-sizing: border-box; }',
  )
  code = code.replaceAll(
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow: visible; }',
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow-x: hidden; overflow-y: visible; }',
  )
  code = code.replaceAll(
    '.receipt { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: visible; }',
    '.receipt { width: ${paperWidthMm}mm; max-width: 100%; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: hidden; }\n.receipt table, .receipt img, .receipt svg { max-width: 100%; }\n.receipt td, .receipt th, .receipt span, .receipt p { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }',
  )

  return code
}
