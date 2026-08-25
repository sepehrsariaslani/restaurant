const { parse, compileTemplate } = require('@vue/compiler-sfc');
const fs = require('fs');
const path = '/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/components/MenuQuickAddSheet.vue';
try {
  const s = fs.readFileSync(path, 'utf8');
  const { descriptor } = parse(s);
  console.log('Parse OK');
  console.log('Template:', descriptor.template ? 'present' : 'absent');
  console.log('ScriptSetup:', descriptor.scriptSetup ? 'present' : 'absent');
  if (descriptor.template) {
    const r = compileTemplate({
      source: descriptor.template.content,
      filename: 'MenuQuickAddSheet.vue',
      id: 'x',
    });
    if (r.errors.length) {
      console.log('Template errors:');
      r.errors.forEach(e => console.log(e));
    } else {
      console.log('Template compile OK');
    }
  }
} catch(e) {
  console.log('Error:', e.message);
}
