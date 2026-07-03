import { getBlockType, BLOCK_TYPE_LIST } from "../src/utils/blockRegistry.js";

const failures = [];

for (const def of BLOCK_TYPE_LIST) {
  const resolved = getBlockType(def.type);
  if (!resolved) {
    failures.push(`missing block type: ${def.type}`);
    continue;
  }

  const component = resolved.component;
  const hasAsyncWrapper =
    component &&
    (typeof component === "object" || typeof component === "function") &&
    "__asyncLoader" in component;

  if (!hasAsyncWrapper) {
    failures.push(`${def.type} component is not a Vue async component wrapper`);
  }
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("block registry async components OK");
