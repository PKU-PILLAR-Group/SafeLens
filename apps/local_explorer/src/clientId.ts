/**
 * Generate a client-side identifier in both secure and ordinary HTTP contexts.
 * Web Crypto's randomUUID is unavailable on non-secure platform previews.
 */
export function createClientId(): string {
  const webCrypto = globalThis.crypto;
  let value: string;

  if (typeof webCrypto?.randomUUID === "function") {
    value = webCrypto.randomUUID();
  } else if (typeof webCrypto?.getRandomValues === "function") {
    const bytes = new Uint8Array(16);
    webCrypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    value = [...bytes]
      .map((byte, index) => {
        const separator = index === 3 || index === 5 || index === 7 || index === 9 ? "-" : "";
        return `${byte.toString(16).padStart(2, "0")}${separator}`;
      })
      .join("");
  } else {
    value = [
      Date.now().toString(36),
      Math.random().toString(36).slice(2),
      Math.random().toString(36).slice(2)
    ].join("-");
  }

  return value;
}
