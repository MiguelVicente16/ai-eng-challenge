// Downsamples browser float32 mono @ context.sampleRate to int16 @ 16kHz
// and posts frames as ArrayBuffer. Keeps a rolling fractional index so
// we don't accumulate sample drift over time.
class PcmCapture extends AudioWorkletProcessor {
  constructor() {
    super();
    this._frac = 0;
    this._target = 16000;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const ch = input[0];
    if (!ch) return true;
    const ratio = sampleRate / this._target;
    const out = new Int16Array(Math.floor((ch.length + this._frac) / ratio));
    let j = 0;
    let idx = this._frac;
    while (idx < ch.length && j < out.length) {
      const i = Math.floor(idx);
      const s = Math.max(-1, Math.min(1, ch[i]));
      out[j++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      idx += ratio;
    }
    this._frac = idx - ch.length;
    if (out.length > 0) {
      this.port.postMessage(out.buffer, [out.buffer]);
    }
    return true;
  }
}
registerProcessor("pcm-capture", PcmCapture);
