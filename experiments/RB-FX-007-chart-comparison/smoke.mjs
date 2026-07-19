import fs from 'node:fs';
import path from 'node:path';

const root = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, '$1'));
const candidates = [
  ['echarts', 'dist/echarts.min.js'],
  ['lightweight-charts', 'dist/lightweight-charts.standalone.production.js'],
];
const results = [];
for (const [pkg, rel] of candidates) {
  const pkgJson = JSON.parse(fs.readFileSync(path.join(root, 'node_modules', pkg, 'package.json'), 'utf8'));
  const target = path.join(root, 'node_modules', pkg, rel);
  results.push({
    package: pkg,
    version: pkgJson.version,
    license: pkgJson.license,
    browser_bundle: rel,
    browser_bundle_bytes: fs.statSync(target).size,
    runtime_external_network_required: false,
  });
}
results.push({package:'native-html-css-svg', version:'platform', license:'no third-party component', browser_bundle_bytes:0, runtime_external_network_required:false});
console.log(JSON.stringify(results, null, 2));
