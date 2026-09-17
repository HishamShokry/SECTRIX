#!/usr/bin/env node
/**
 * Remove library version strings from built front-end assets.
 *
 * Wappalyzer and similar scanners read these straight out of the served files
 * and report the exact version, which is the shortcut from "this site uses
 * Alpine" to "this site uses an Alpine with CVE-XXXX". Attribution is kept --
 * only the version number is dropped, so the MIT notices remain intact.
 *
 * This is fingerprint reduction, not a fix: keeping the libraries patched is
 * what actually protects the site. It removes the free lookup, nothing more.
 *
 * Runs as part of `npm run build`.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";

const targets = [
  {
    file: "static/css/tailwind.css",
    // "/*! tailwindcss v3.4.19 | MIT License | ..." -> "/*! tailwindcss | MIT License | ..."
    replacements: [[/tailwindcss v\d+\.\d+\.\d+/g, "tailwindcss"]],
  },
  {
    file: "static/js/alpine.min.js",
    // Alpine exposes its version as a public property; blanking the value
    // keeps the property (so anything reading it still works) without
    // advertising the release.
    replacements: [[/version:"\d+\.\d+\.\d+"/g, 'version:""']],
  },
];

let changed = 0;
for (const { file, replacements } of targets) {
  if (!existsSync(file)) {
    console.error(`  skip (not built yet): ${file}`);
    continue;
  }
  const before = readFileSync(file, "utf8");
  let after = before;
  for (const [pattern, value] of replacements) after = after.replace(pattern, value);

  if (after !== before) {
    writeFileSync(file, after);
    console.log(`  stripped version strings: ${file}`);
    changed++;
  } else {
    console.log(`  already clean: ${file}`);
  }
}
console.log(`strip-asset-versions: ${changed} file(s) rewritten`);
