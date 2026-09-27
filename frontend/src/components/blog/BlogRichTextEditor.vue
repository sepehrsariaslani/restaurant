<template>
  <section class="blog-editor" dir="rtl"><div class="blog-editor__tools" role="toolbar" aria-label="قالب‌بندی متن"><button v-for="tool in tools" :key="tool.command" type="button" :title="tool.label" @mousedown.prevent="run(tool.command, tool.value)">{{ tool.label }}</button></div><div ref="editor" class="blog-editor__content" contenteditable="true" role="textbox" aria-multiline="true" data-placeholder="متن مقاله را اینجا بنویسید..." @input="emitValue" @blur="emitValue"></div></section>
</template>
<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
const props=defineProps({modelValue:{type:String,default:''}});const emit=defineEmits(['update:modelValue']);const editor=ref(null)
const tools=[{command:'formatBlock',value:'h2',label:'عنوان'},{command:'bold',label:'پررنگ'},{command:'italic',label:'کج'},{command:'insertUnorderedList',label:'فهرست'},{command:'createLink',label:'پیوند'}]
onMounted(()=>{if(editor.value)editor.value.innerHTML=props.modelValue||''})
watch(()=>props.modelValue,async v=>{await nextTick();if(editor.value&&editor.value.innerHTML!==v)editor.value.innerHTML=v||''})
function run(command,value){editor.value?.focus();if(command==='createLink'){const url=window.prompt('نشانی پیوند');if(!url)return;document.execCommand(command,false,url)}else document.execCommand(command,false,value||null);emitValue()}
function emitValue(){emit('update:modelValue',editor.value?.innerHTML||'')}
</script>
<style scoped>.blog-editor{border:1px solid var(--mg-border-light);border-radius:14px;overflow:hidden;background:var(--mg-bg-surface)}.blog-editor__tools{display:flex;gap:.35rem;flex-wrap:wrap;padding:.55rem;border-bottom:1px solid var(--mg-border-light);background:var(--mg-bg-page)}.blog-editor__tools button{min-height:38px;border:1px solid var(--mg-border-light);border-radius:8px;background:var(--mg-bg-surface);color:var(--mg-text-main);padding:.35rem .65rem;font:inherit;cursor:pointer}.blog-editor__content{min-height:280px;padding:1rem;outline:0;color:var(--mg-text-main);line-height:1.9}.blog-editor__content:empty:before{content:attr(data-placeholder);color:var(--mg-text-muted)}.blog-editor__content :deep(h2){font-size:1.4rem}</style>
