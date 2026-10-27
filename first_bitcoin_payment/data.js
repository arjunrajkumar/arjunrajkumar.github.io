// Public historical transaction supplied by the learner and checked against Blockstream.
export const TXID = 'f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16';
export const HEX = '0100000001c997a5e56e104102fa209c6a852dd90660a20b2d9c352423edce25857fcd3704000000004847304402204e45e16932b8af514961a1d3a1a25fdf3f4f7732e9d624c6c61548ab5fb8cd410220181522ec8eca07de4860a4acdd12909d831cc56cbbac4622082221a8768d1d0901ffffffff0200ca9a3b00000000434104ae1a62fe09c5f51b13905f07f06b99a2f7159b2225f374cd378d71302fa28414e7aab37397f554a7df5f142c21c1b7303b8a0626f1baded5c72a704f7e6cd84cac00286bee0000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000';
export const bytes = Uint8Array.from(HEX.match(/../g), h => parseInt(h, 16));
export const binaryByte = value => value.toString(2).padStart(8, '0');
export const bits = Array.from(bytes, binaryByte).join('');

export function parseTransaction(data) {
  let pos = 0;
  const fields = [];
  function take(id, name, size, group, value, explanation) {
    if (pos + size > data.length) throw new Error('Transaction ends inside a field.');
    const field = {id, name, start: pos, length: size, group, value, explanation};
    fields.push(field); pos += size; return field;
  }
  function uint(start, size) {
    let n = 0n;
    for (let i = size - 1; i >= 0; i--) n = (n << 8n) | BigInt(data[start + i]);
    return n;
  }
  function compact(id, name, group, explanation) {
    const tag = data[pos];
    const width = tag < 253 ? 1 : tag === 253 ? 3 : tag === 254 ? 5 : 9;
    const value = tag < 253 ? tag : Number(uint(pos + 1, width - 1));
    take(id, name, width, group, String(value), explanation + ' CompactSize uses fewer bytes for small numbers.');
    return value;
  }
  take('version', 'Version', 4, 'structure', String(Number(uint(0, 4))), 'The transaction version is 1. These four bytes form one number. The byte with the smallest place value comes first. This order is called little-endian.');
  const inputs = compact('input-count', 'Input count', 'structure', 'This transaction has one input.');
  for (let i = 0; i < inputs; i++) {
    const displayId = Array.from(data.slice(pos, pos + 32)).reverse().map(b => b.toString(16).padStart(2, '0')).join('');
    take('previous-id-' + i, 'Earlier transaction ID', 32, 'input', displayId, 'This identifies the earlier transaction in block 9. The explorer displays its ID with the byte order reversed. The bits here keep the order stored in this input.');
    take('previous-index-' + i, 'Earlier output number', 4, 'input', String(Number(uint(pos, 4))), 'This input spends output 0 of the earlier transaction. Output numbering starts at 0. These four bytes use little-endian order.');
    const n = compact('input-script-length-' + i, 'Input script length', 'input', 'The next 72 bytes contain the input script.');
    take('input-script-' + i, 'Input script · signature', n, 'input', n + ' bytes', 'An input script supplies data needed to spend an earlier output. Here: one byte tells Script to push 71 bytes; the next 70 bytes encode the signature; the last byte selects SIGHASH_ALL, which covers all outputs.');
    take('sequence-' + i, 'Sequence', 4, 'input', String(Number(uint(pos, 4))), 'All 32 bits are 1. The value is 4,294,967,295. This is the final sequence value.');
  }
  const outputs = compact('output-count', 'Output count', 'structure', 'This transaction creates two outputs.');
  for (let i = 0; i < outputs; i++) {
    const amount = uint(pos, 8);
    const btc = Number(amount) / 100000000;
    const group = i === 0 ? 'payment' : 'change';
    take('amount-' + i, 'Output ' + i + ' · amount', 8, group, btc + ' BTC', amount.toLocaleString('en-US') + ' satoshis. A satoshi is one hundred-millionth of a bitcoin. These eight bytes form a little-endian number.');
    const n = compact('output-script-length-' + i, 'Output ' + i + ' · script length', group, 'The next 67 bytes contain this output’s script.');
    take('output-script-' + i, 'Output ' + i + ' · locking script', n, group, 'Public key + signature check', 'A locking script sets the conditions for spending an output. Here: one byte pushes a 65-byte public key; the final byte is OP_CHECKSIG, which checks a signature. The full script is 67 bytes.');
  }
  take('locktime', 'Locktime', 4, 'structure', String(Number(uint(pos, 4))), 'The value is 0. This transaction sets no minimum time or block height for inclusion.');
  if (pos !== data.length) throw new Error('Unparsed bytes remain.');
  return {fields, inputs, outputs};
}
export const transaction = parseTransaction(bytes);
