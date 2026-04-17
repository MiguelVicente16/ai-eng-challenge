import "@testing-library/jest-dom";

// jsdom 29 + vitest 4 ships a broken localStorage/sessionStorage on window
// (plain object, no Storage prototype methods). Polyfill a minimal in-memory
// Storage so components relying on window.localStorage can run under test.
function createMemoryStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => (store.has(key) ? (store.get(key) as string) : null),
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, String(value));
    },
  };
}

if (typeof window !== "undefined") {
  // Radix UI Select / Popover primitives call pointer-capture and
  // scrollIntoView methods that jsdom does not implement. Polyfill as no-ops
  // so component tests can open/close listboxes without unhandled exceptions.
  const ElementProto = window.Element.prototype as unknown as {
    hasPointerCapture?: (pointerId: number) => boolean;
    setPointerCapture?: (pointerId: number) => void;
    releasePointerCapture?: (pointerId: number) => void;
    scrollIntoView?: (arg?: boolean | ScrollIntoViewOptions) => void;
  };
  if (typeof ElementProto.hasPointerCapture !== "function") {
    ElementProto.hasPointerCapture = () => false;
  }
  if (typeof ElementProto.setPointerCapture !== "function") {
    ElementProto.setPointerCapture = () => {};
  }
  if (typeof ElementProto.releasePointerCapture !== "function") {
    ElementProto.releasePointerCapture = () => {};
  }
  if (typeof ElementProto.scrollIntoView !== "function") {
    ElementProto.scrollIntoView = () => {};
  }

  if (typeof window.localStorage?.getItem !== "function") {
    Object.defineProperty(window, "localStorage", {
      value: createMemoryStorage(),
      configurable: true,
      writable: true,
    });
  }
  if (typeof window.sessionStorage?.getItem !== "function") {
    Object.defineProperty(window, "sessionStorage", {
      value: createMemoryStorage(),
      configurable: true,
      writable: true,
    });
  }
  if (typeof window.matchMedia !== "function") {
    Object.defineProperty(window, "matchMedia", {
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }),
      configurable: true,
      writable: true,
    });
  }
}
