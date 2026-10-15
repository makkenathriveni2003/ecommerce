import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.join(__dirname, "frontend", "dist");
const PORT = 5050;

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
};

const server = http.createServer((req, res) => {
  let reqPath = (req.url || "/").split("?")[0];
  let filePath = path.join(DIST_DIR, reqPath);

  if (reqPath === "/" || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(DIST_DIR, "index.html");
  }

  if (!fs.existsSync(filePath)) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found");
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || "application/octet-stream";
  const fileContent = fs.readFileSync(filePath);

  const acceptEncoding = req.headers["accept-encoding"] || "";
  const isHtml = ext === ".html";
  const cacheControl = isHtml
    ? "no-cache"
    : "public, max-age=31536000, immutable";

  const headers = {
    "Content-Type": contentType,
    "Cache-Control": cacheControl,
    "Access-Control-Allow-Origin": "*",
  };

  if (/\bgzip\b/.test(acceptEncoding) && (ext === ".html" || ext === ".js" || ext === ".css" || ext === ".svg" || ext === ".json")) {
    headers["Content-Encoding"] = "gzip";
    headers["Vary"] = "Accept-Encoding";
    const compressed = zlib.gzipSync(fileContent, { level: 9 });
    res.writeHead(200, headers);
    res.end(compressed);
  } else {
    res.writeHead(200, headers);
    res.end(fileContent);
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Server listening on http://127.0.0.1:${PORT}`);
});
