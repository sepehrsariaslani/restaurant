import { ref } from 'vue'

const searchOpen = ref(false)
const searchQuery = ref('')

export function useSearchModal() {
  function openSearch(query = '') {
    searchQuery.value = typeof query === 'string' ? query : ''
    searchOpen.value = true
  }
  function closeSearch() {
    searchOpen.value = false
  }
  function toggleSearch() {
    searchOpen.value = !searchOpen.value
  }
  return { searchOpen, searchQuery, openSearch, closeSearch, toggleSearch }
}
