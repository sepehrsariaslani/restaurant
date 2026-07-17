import fs from 'fs'

const appPath = '/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/App.vue'
const source = fs.readFileSync(appPath, 'utf8')

const checks = [
  {
    name: 'management route resolves to management-kitchen',
    ok: source.includes("if (pathname.startsWith('/management/kitchen')) return 'management-kitchen'"),
  },
  {
    name: 'management layout renders ManagementKitchenPage',
    ok: source.includes("<ManagementKitchenPage v-else-if=\"page === 'management-kitchen'\" />"),
  },
  {
    name: 'ManagementKitchenPage import exists',
    ok: source.includes("import ManagementKitchenPage from './pages/management/ManagementKitchenPage.vue'"),
  },
]

const failed = checks.filter((check) => !check.ok)
if (failed.length) {
  console.error('Kitchen management route verification failed:')
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log('Kitchen management route verification passed.')
