<template>
  <ManagementPageScaffold
    title="مدیریت Modifier"
    subtitle="گروه‌های modifier، وضعیت قیمت‌گذاری ERPNext و آیتم‌های انتخابی مشتری را از یک صفحه مدیریت کنید."
  >
    <ManagementModifierGroupsSettings />
  </ManagementPageScaffold>
</template>

<script setup>
import ManagementModifierGroupsSettings from '@/components/management/ManagementModifierGroupsSettings.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
</script>
