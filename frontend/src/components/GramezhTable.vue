<template>
  <div class="gramezh-table">
    <table class="w-full">
      <thead>
        <tr>
          <th>آیتم</th>
          <th>مقدار</th>
          <th>قیمت</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, i) in items" :key="i">
          <td>{{ item.item_name || item.name || '-' }}</td>
          <td>{{ item.qty || item.quantity || '-' }}</td>
          <td>{{ item.rate || item.price || '-' }} {{ currency }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  currency: { type: String, default: 'ریال' },
})
</script>
