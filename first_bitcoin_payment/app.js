import {HEX, bytes, binaryByte, transaction} from './data.js';
const binary = document.getElementById('binary');
const hex = document.getElementById('hex');
const streams = [binary, hex];
const tooltips = streams.map((stream, i) => {
  const label = document.createElement('div');
  label.id = 'field-tooltip-' + i; label.className = 'field-tooltip'; label.hidden = true;
  const title = document.createElement('strong'); title.className = 'tooltip-title';
  const detail = document.createElement('span'); detail.className = 'tooltip-detail';
  label.append(title, detail);
  label.setAttribute('role', 'tooltip'); document.body.append(label); return label;
});
let hoveredField = null, focusedField = null;
function positionTooltips() {
  const activeField = hoveredField || focusedField;
  if (!activeField) { tooltips.forEach(label => { label.hidden = true; }); return; }
  const sourceStart = Number(activeField.target.dataset.start);
  const sourceEnd = Number(activeField.target.dataset.end);
  streams.forEach((stream, i) => {
    const matches = Array.from(stream.querySelectorAll('.field')).filter(part => part.dataset.label === activeField.label);
    const overlapsSource = part => Number(part.dataset.start) < sourceEnd && Number(part.dataset.end) > sourceStart;
    const isVisible = part => {
      const rect = part.getBoundingClientRect(); return rect.bottom > 0 && rect.top < innerHeight;
    };
    const anchor = matches.find(part => part === activeField.target)
      || matches.find(part => overlapsSource(part) && isVisible(part))
      || matches.find(isVisible) || matches.find(overlapsSource) || matches[0];
    if (!anchor) return;
    const label = tooltips[i];
    label.querySelector('.tooltip-title').textContent = activeField.label;
    const detail = label.querySelector('.tooltip-detail');
    detail.textContent = activeField.target.dataset.detail || '';
    detail.hidden = !detail.textContent;
    label.className = 'field-tooltip ' + Array.from(anchor.classList).find(name => /^f\d+$/.test(name));
    label.hidden = false;
    const rect = anchor.getBoundingClientRect(), pane = stream.getBoundingClientRect();
    const width = label.offsetWidth, height = label.offsetHeight;
    const right = i === 0 ? Math.min(pane.right - 8, innerWidth - 8) : innerWidth - 8;
    const left = Math.max(8, Math.min(rect.left, right - width));
    let top = rect.top - height - 8;
    if (top < 8 || (i === 1 && pane.width < width + 16)) top = rect.bottom + 8;
    label.style.left = left + 'px';
    label.style.top = Math.max(8, Math.min(top, innerHeight - height - 8)) + 'px';
  });
}
function updateActiveField() {
  const activeField = hoveredField || focusedField;
  document.querySelectorAll('.field').forEach(part => {
    part.classList.toggle('is-active', part.dataset.label === activeField?.label);
  });
  positionTooltips();
}
function describeOnHover(element, label) {
  element.tabIndex = 0;
  element.addEventListener('pointerenter', () => { hoveredField = {label, target: element}; updateActiveField(); });
  element.addEventListener('pointerleave', () => { hoveredField = null; updateActiveField(); });
  element.addEventListener('focus', () => { focusedField = {label, target: element}; updateActiveField(); });
  element.addEventListener('blur', () => { focusedField = null; updateActiveField(); });
}
const fieldInfo = [
  {label: 'Version'},
  {label: 'Input count'},
  {label: 'Hash of the tx that input #0 came from:'},
  {label: 'Index of the output spent by input #0 in the funding transaction'},
  {label: 'Input script length'},
  {label: 'scriptSig to authorize spending input #0'},
  {label: 'Sequence'},
  {label: 'Output count'},
  {label: 'Output 0 · amount', detail: '(10 BTC or 1,000,000,000 satoshis)'},
  {label: 'Output 0 · script length'},
  {label: 'Output 0 scriptPubKey', detail: "(Hal Finney's public key plus OP_CHECKSIG)"},
  {label: 'Output 1 · amount', detail: '(40 BTC or 4,000,000,000 satoshis)'},
  {label: 'Output 1 · script length'},
  {label: 'Output 1 scriptPubKey', detail: "(Satoshi's own public key again, for change)"},
  {label: 'Locktime'}
];
let lastWidth = 0;
function fillStream(element, isBinary) {
  const style = getComputedStyle(element);
  const sample = document.createElement('span'); sample.className = 'measure'; element.append(sample);
  const alphabet = isBinary ? '01' : '0123456789abcdef';
  const widths = Object.fromEntries(Array.from(alphabet, digit => {
    sample.textContent = digit.repeat(10);
    return [digit, sample.getBoundingClientRect().width / 10];
  }));
  sample.remove();
  const available = element.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight) - 2;
  let start = 0, rowWidth = 0;
  bytes.forEach((byte, index) => {
    const digits = isBinary ? binaryByte(byte) : HEX.slice(index * 2, index * 2 + 2);
    const byteWidth = Array.from(digits).reduce((sum, digit) => sum + widths[digit], 0);
    if (rowWidth + byteWidth > available && index > start) {
      appendRow(element, start, index, isBinary);
      start = index; rowWidth = 0;
    }
    rowWidth += byteWidth;
  });
  appendRow(element, start, bytes.length, isBinary);
}
function appendRow(target, start, end, isBinary) {
  const row = document.createElement('div'); row.className = 'stream-row';
  transaction.fields.forEach((field, index) => {
    const a = Math.max(start, field.start), b = Math.min(end, field.start + field.length);
    if (a >= b) return;
    const part = document.createElement('span'); part.className = 'field f' + index;
    part.dataset.field = field.id;
    part.dataset.start = a;
    part.dataset.end = b;
    const info = fieldInfo[index];
    part.dataset.label = info.label;
    part.dataset.detail = info.detail || '';
    part.setAttribute('aria-label', `${info.label}${info.detail ? ' ' + info.detail : ''} · bytes ${field.start}–${field.start + field.length - 1}`);
    part.setAttribute('aria-describedby', isBinary ? 'field-tooltip-0' : 'field-tooltip-1');
    describeOnHover(part, info.label);
    const content = document.createElement('span'); content.className = 'field-content';
    content.textContent = isBinary ? Array.from(bytes.slice(a, b), binaryByte).join('') : HEX.slice(a * 2, b * 2);
    part.append(content);
    row.append(part);
  });
  target.append(row);
}
function render() {
  const width = document.getElementById('streams').clientWidth;
  if (lastWidth === width) return;
  lastWidth = width;
  hoveredField = null; focusedField = null; updateActiveField();
  binary.replaceChildren(); hex.replaceChildren();
  fillStream(binary, true); fillStream(hex, false);
}
render();
document.fonts.ready.then(() => { lastWidth = 0; render(); });
new ResizeObserver(render).observe(document.getElementById('streams'));
window.addEventListener('scroll', positionTooltips, {passive: true, capture: true});
