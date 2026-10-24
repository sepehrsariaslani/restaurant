import { readFile } from "node:fs/promises";
import { test } from "node:test";
import assert from "node:assert/strict";

const footerSource = await readFile(
	new URL("../src/components/SiteFooter.vue", import.meta.url),
	"utf8",
);

test("Veederakht footer includes the SME Enamad trust seal without rel attribute", () => {
	assert.match(
		footerSource,
		/https:\/\/trustseal\.enamad\.ir\/\?id=8041746&Code=2PT46vOdEVXChL4zRLKfLaNM6LjFqu2g/,
	);
	assert.match(
		footerSource,
		/https:\/\/trustseal\.enamad\.ir\/logo\.aspx\?id=8041746&Code=2PT46vOdEVXChL4zRLKfLaNM6LjFqu2g/,
	);
	assert.doesNotMatch(footerSource, /enamad[^<]*rel=/i);
});
