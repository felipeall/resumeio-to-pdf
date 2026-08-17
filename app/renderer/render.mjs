import { webcrypto } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import vm from "node:vm";

const STARTUP_TIMEOUT_MS = 10_000;
const RENDER_TIMEOUT_MS = 60_000;

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

const { document, config, assetsDir, entry, host } = JSON.parse(await readStdin());

let settle;
const rendered = new Promise((resolve, reject) => {
  settle = { resolve, reject };
});

// A fresh context brings its own ECMAScript globals; anything else the worker needs has to be
// handed over explicitly, and host functions must keep globalThis as their receiver or Node
// rejects the call with ERR_INVALID_THIS.
const context = vm.createContext();
Object.assign(context, {
  importScripts(...urls) {
    for (const url of urls) {
      const file = join(assetsDir, url.split("/").pop());
      vm.runInContext(readFileSync(file, "utf8"), context, { filename: file });
    }
  },
  postMessage(message) {
    if (message.success) settle.resolve(message.result);
    else settle.reject(new Error(message.error?.message || "worker reported failure"));
  },
  location: new URL(host),
  console,
  setTimeout: setTimeout.bind(globalThis),
  clearTimeout: clearTimeout.bind(globalThis),
  setInterval: setInterval.bind(globalThis),
  clearInterval: clearInterval.bind(globalThis),
  queueMicrotask: queueMicrotask.bind(globalThis),
  structuredClone: structuredClone.bind(globalThis),
  fetch: fetch.bind(globalThis),
  btoa: btoa.bind(globalThis),
  atob: atob.bind(globalThis),
  TextEncoder,
  TextDecoder,
  URL,
  URLSearchParams,
  Blob,
  Response,
  Request,
  Headers,
  AbortController,
  AbortSignal,
  ReadableStream,
  performance,
  crypto: globalThis.crypto ?? webcrypto,
  webpackChunk_rio_web_worker: [],
});
context.self = context;

vm.runInContext(readFileSync(join(assetsDir, entry), "utf8"), context, { filename: entry });

// The handler is registered only once the worker has pulled in its lazy chunks.
for (let waited = 0; typeof context.onmessage !== "function"; waited += 10) {
  if (waited > STARTUP_TIMEOUT_MS) throw new Error("worker did not register an onmessage handler");
  await new Promise((resolve) => setTimeout(resolve, 10));
}

context.onmessage({ data: { taskId: "render", document, config, host } });

const timeout = new Promise((_, reject) =>
  setTimeout(() => reject(new Error("rendering timed out")), RENDER_TIMEOUT_MS).unref(),
);

process.stdout.write(Buffer.from(await Promise.race([rendered, timeout])));
