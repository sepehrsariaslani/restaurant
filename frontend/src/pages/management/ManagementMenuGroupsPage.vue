<template>
  <ManagementPageScaffold title="دسته‌بندی محصولات" subtitle="مدیریت کامل دسته‌ها و زیر‌دسته‌های منو در یک صفحه مستقل">
    <template #actions>
      <a class="secondary-btn" href="/management/menu-group">دسته جدید</a>
    </template>

    <ManagementMenuGroupsSettings />
  </ManagementPageScaffold>
</template>

<script setup>
import ManagementMenuGroupsSettings from '@/components/management/ManagementMenuGroupsSettings.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
</script>
