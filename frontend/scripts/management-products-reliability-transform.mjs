export function transformManagementProductsPage(input) {
  let code = String(input || '')
  if (!code.includes('async function loadProducts()')) return code

  if (!code.includes("from '@/utils/posReliabilityApi'")) {
    const importLine = "import { listManagementProductsSafe } from '@/utils/posReliabilityApi'"
    if (code.includes('<script setup>')) {
      code = code.replace('<script setup>', `<script setup>\n${importLine}`)
    }
  }

  code = code.replaceAll(
    'await listManagementProducts({',
    'await listManagementProductsSafe({',
  )
  return code
}
