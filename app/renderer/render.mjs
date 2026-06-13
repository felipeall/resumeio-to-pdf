import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { join } from "path";
import vm from "vm";

let input;
if (!process.stdin.isTTY) {
  input = await new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
} else if (existsSync("/dev/stdin")) {
  input = readFileSync("/dev/stdin", "utf8");
} else {
  input = await new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}
const { document: doc, config, workerDir } = JSON.parse(input);
try {
  process.stderr.write(`DOC_KEYS:${JSON.stringify(Object.keys(doc || {}))}\n`);
  try {
    const payloadPreview = JSON.stringify(JSON.parse(input), null, 2).slice(0, 2000);
    process.stderr.write(`PAYLOAD_PREVIEW:${payloadPreview}\n`);
  } catch (e) {
    process.stderr.write(`PAYLOAD_PREVIEW_ERROR:${String(e)}\n`);
  }
} catch (e) {
  process.stderr.write(`DOC_KEYS_ERROR:${String(e)}\n`);
}

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const WORKER_DIR = workerDir || join(__dirname, ".worker_cache");

let onmessageHandler = null;
let resolveResult, rejectResult;
const resultPromise = new Promise((resolve, reject) => {
  resolveResult = resolve;
  rejectResult = reject;
});

const sandbox = {
  self: null,
  console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  queueMicrotask,
  Promise,
  URL,
  Blob: globalThis.Blob,
  Response: globalThis.Response,
  fetch: globalThis.fetch,
  TextEncoder,
  TextDecoder,
  Object,
  Array,
  String,
  Number,
  Boolean,
  RegExp,
  Error,
  TypeError,
  RangeError,
  ReferenceError,
  SyntaxError,
  URIError,
  EvalError,
  Map,
  Set,
  WeakMap,
  WeakSet,
  WeakRef,
  FinalizationRegistry,
  Symbol,
  Proxy,
  Reflect,
  Iterator: globalThis.Iterator,
  Int8Array,
  Uint8Array,
  Uint8ClampedArray,
  Int16Array,
  Uint16Array,
  Int32Array,
  Uint32Array,
  Float32Array,
  Float64Array,
  BigInt64Array,
  BigUint64Array,
  ArrayBuffer,
  SharedArrayBuffer,
  DataView,
  BigInt,
  Math,
  JSON,
  Date,
  NaN,
  Infinity,
  undefined,
  isNaN,
  isFinite,
  parseInt,
  parseFloat,
  encodeURIComponent,
  decodeURIComponent,
  encodeURI,
  decodeURI,
  btoa: globalThis.btoa,
  atob: globalThis.atob,
  structuredClone: globalThis.structuredClone,
  AbortController: globalThis.AbortController,
  AbortSignal: globalThis.AbortSignal,
  Headers: globalThis.Headers,
  Request: globalThis.Request,
  ReadableStream: globalThis.ReadableStream,
  WritableStream: globalThis.WritableStream,
  TransformStream: globalThis.TransformStream,
  performance: globalThis.performance,
  crypto: globalThis.crypto,

  postMessage(data) {
    try {
      process.stderr.write(`WORKER_POST:${JSON.stringify(data)}\n`);
    } catch (e) {
      process.stderr.write(`WORKER_POST_ERROR:${String(e)}\n`);
    }
    if (data.success) resolveResult(data.result);
    else rejectResult(new Error(data.error?.message || "Rendering failed"));
  },

  importScripts(...urls) {
    for (const url of urls) {
      const filename = url.split("/").pop();
      const path = join(WORKER_DIR, filename);
      const code = readFileSync(path, "utf8");
      vm.runInContext(code, context);
    }
  },

  webpackChunk_rio_web_worker: [],
};

sandbox.self = sandbox;
sandbox.globalThis = sandbox;

Object.defineProperty(sandbox, "onmessage", {
  get() {
    return onmessageHandler;
  },
  set(fn) {
    onmessageHandler = fn;
  },
  configurable: true,
});

const context = vm.createContext(sandbox);

const workerCode = readFileSync(join(WORKER_DIR, "rendering.js"), "utf8");
vm.runInContext(workerCode, context);

await new Promise((resolve, reject) => {
  let elapsed = 0;
  const check = () => {
    if (onmessageHandler) return resolve();
    elapsed += 10;
    if (elapsed > 5000) return reject(new Error("onmessage handler not registered"));
    setTimeout(check, 10);
  };
  check();
});

onmessageHandler({
  data: { taskId: "render", document: doc, config },
});

try {
  const result = await Promise.race([
    resultPromise,
    new Promise((_, rej) =>
      setTimeout(() => rej(new Error("Rendering timed out")), 60000),
    ),
  ]);
  process.stdout.write(Buffer.from(result));
} catch (e) {
  process.stderr.write(`error: ${e.stack || e.message}\n`);
  process.exit(1);
}
