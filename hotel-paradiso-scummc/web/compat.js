// Loaded by scummvm.html before ScummVM itself, to smooth over browser
// differences in the web port.

// ScummVM downloads its data with Response.bytes(), which older browsers
// (Chrome < 132, Firefox < 128) don't have.
if (!Response.prototype.bytes) {
  Response.prototype.bytes = async function () {
    return new Uint8Array(await this.arrayBuffer());
  };
}

// The page asks for WebMIDI at startup and doesn't handle a refusal. Firefox
// refuses unless a site-permission add-on is installed, and the unhandled error
// crashes the page. This game has no MIDI music, so report "no MIDI devices".
if ('requestMIDIAccess' in navigator) {
  Object.defineProperty(Navigator.prototype, 'requestMIDIAccess', {
    configurable: true,
    writable: true,
    value: () => Promise.resolve({ inputs: new Map(), outputs: new Map(), onstatechange: null }),
  });
}
