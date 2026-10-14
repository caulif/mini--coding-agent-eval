// Exercise language initialization and navigation without claiming browser QA.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const script = fs.readFileSync(path.join(__dirname, '../tutorial/app.js'), 'utf8');
for (const lang of ['en', 'zh-CN']) {
  const element = () => ({
    style: {}, textContent: '',
    addEventListener(type, fn) { this[type] = fn; },
    setAttribute(key, value) { this[key] = value; }
  });
  const targets = Object.fromEntries([
    '.language-switch', '.contents', '#resume-reading', '#resume-label',
    '#resume-link', '#dismiss-resume', '#progress', '#reading-location'
  ].map(key => [key, element()]));
  const heading = {id: 'ch2-s1', textContent: 'Section title', getBoundingClientRect: () => ({top: 0})};
  const chapter = {
    id: 'ch2', dataset: {stage: 'Stage'}, getBoundingClientRect: () => ({top: 0}),
    querySelectorAll: () => [heading]
  };
  const document = {
    documentElement: {lang, scrollHeight: 3000}, querySelector: selector => targets[selector],
    querySelectorAll: selector => selector === '.chapter' ? [chapter]
      : selector === '.chapter h2, .chapter h3' ? [heading] : []
  };
  const context = {
    document, location: {hash: ''},
    localStorage: {getItem: () => JSON.stringify({id: heading.id}), setItem() {}},
    matchMedia: () => ({matches: true}), innerHeight: 800, scrollY: 200,
    setTimeout: () => 1, clearTimeout() {}, requestAnimationFrame: fn => fn(), addEventListener() {}
  };
  vm.runInNewContext(script, context);
  assert(targets['#reading-location'].textContent.includes(heading.textContent));
  assert(targets['#resume-label'].textContent.startsWith(lang === 'en' ? 'Last read: ' : '\u4e0a\u6b21\u8bfb\u5230\uff1a'));
  context.location.hash = '#ch1';
  targets['.language-switch'].click();
  assert.equal(targets['.language-switch'].hash, '#ch2-s1');
  assert.equal(targets['.contents'].open, false);
}
console.log('PASS: both languages initialize, resume, and switch at the current section (DOM simulation).');
