// Runs inside the browser's audio thread: passes each block of microphone samples to the page.
// The page converts them to 16-bit numbers and sends them to the local Kettle server. Nothing is stored.
class KettleTap extends AudioWorkletProcessor {
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (ch) this.port.postMessage(ch.slice(0));
    return true;
  }
}
registerProcessor("kettle-tap", KettleTap);
