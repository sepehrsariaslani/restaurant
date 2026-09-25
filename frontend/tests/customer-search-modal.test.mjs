import test from 'node:test'
import assert from 'node:assert/strict'
import { useSearchModal } from '../src/composables/useSearchModal.js'

test('search opens empty from a click and preserves an explicit legacy query', () => {
  const { searchOpen, searchQuery, openSearch, closeSearch } = useSearchModal()

  openSearch({ type: 'click' })
  assert.equal(searchOpen.value, true)
  assert.equal(searchQuery.value, '')

  closeSearch()
  openSearch('مرغ')
  assert.equal(searchQuery.value, 'مرغ')
  closeSearch()
})
