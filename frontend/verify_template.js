const fs = require('fs');
const src = fs.readFileSync('src/components/MenuQuickAddSheet.vue', 'utf8');
const templateMatch = src.match(/<template>([\s\S]*?)<\/template>\s*<script/s);
if (!templateMatch) { console.log('No template found'); process.exit(1); }
try {
  const { compileTemplate } = require('@vue/compiler-sfc');
  const result = compileTemplate({
    source: templateMatch[1],
    filename: 'MenuQuickAddSheet.vue',
    id: 'test',
  });
  if (result.errors.length) {
    console.log('Template errors:');
    result.errors.forEach(e => console.log(e));
  } else {
    console.log('Template compiles OK');
  }
} catch(e) { console.log('Error:', e.message); }
