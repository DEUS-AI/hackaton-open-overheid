// New ingest endpoint migrated from former /api/upload
// Accepts either a multipart file (field name: "file") or a URL (field name: "sourceUrl").
// Generates a doc_id and publishes a message to the ingestion queue.
import { updateStatus, upsertInitial } from "@/app/utils/pipelineStatus";
import { ServiceBusClient } from "@azure/service-bus";
import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";

export const runtime = "nodejs";
export const revalidate = 0;

function ensureEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`${name} is not set`);
  return v;
}

async function saveFileToUploads(file: File, docId: string): Promise<string> {
  const uploadDir = process.env.WEBAPP_UPLOAD_DIR || "/uploads";
  await fs.mkdir(uploadDir, { recursive: true }).catch(() => {});

  const original = (file.name || "document.dat").replace(/[/\\]/g, "_");
  const stored = `${docId}_${original}`;
  const storedPath = path.join(uploadDir, stored);
  const buf = Buffer.from(await file.arrayBuffer());
  await fs.writeFile(storedPath, buf);
  return storedPath;
}

async function delay(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

async function publishToIngestion(
  docId: string,
  filename: string,
  storedPathOrUrl: string,
  source: string = "web-upload"
) {
  const connectionString = ensureEnv("AZURE_SERVICEBUS_CONNECTION_STRING");
  const ingestionQueue = process.env.AZURE_DOCUMENT_INGESTION_QUEUE || "ingestion-queue";
  const ext = path.extname(filename).replace(/^\./, "") || "dat";

  const appMessage = {
    data: {
      id: docId,
      source,
      name: filename,
      url: storedPathOrUrl,
      extension: ext,
      payload: {},
    },
    validation: null,
    pii: null,
    metadata: null,
  };

  const maxAttempts = Number(process.env.SB_SEND_RETRIES || 5);
  const baseDelay = Number(process.env.SB_SEND_RETRY_DELAY_MS || 1000);
  let lastErr: unknown = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const client = new ServiceBusClient(connectionString);
    const sender = client.createSender(ingestionQueue);
    try {
      await sender.sendMessages({ body: appMessage, contentType: "application/json", subject: "document_ingest" });
      return; // success
    } catch (err) {
      lastErr = err;
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`ServiceBus send attempt ${attempt}/${maxAttempts} failed: ${msg}`);
      if (attempt === maxAttempts) break;
      const sleep = baseDelay * Math.pow(2, attempt - 1);
      await delay(sleep);
    } finally {
      try { await sender.close(); } catch {}
      try { await client.close(); } catch {}
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error(String(lastErr));
}

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData();
    const file = form.get("file");
    const sourceUrlRaw = form.get("sourceUrl");

    if (!(file instanceof File) && typeof sourceUrlRaw !== "string") {
      return NextResponse.json({ error: "No file or sourceUrl provided" }, { status: 400 });
    }

    const docId = randomUUID();

    if (file instanceof File) {
      const filename = file.name || `document-${docId}.dat`;
      const storedPath = await saveFileToUploads(file, docId);
      const size = (await fs.stat(storedPath)).size;
      await upsertInitial(docId, { filename, size }, "uploaded");
      await updateStatus("ingestion", docId, "queued");
      await publishToIngestion(docId, filename, storedPath, "web-upload");
      return NextResponse.json({ doc_id: docId });
    }

    const sourceUrl = (sourceUrlRaw as string).trim();
    let parsed: URL;
    try {
      parsed = new URL(sourceUrl);
    } catch {
      return NextResponse.json({ error: "Invalid sourceUrl" }, { status: 400 });
    }
    if (!/^https?:/i.test(parsed.protocol)) {
      return NextResponse.json({ error: "Only http(s) URLs allowed" }, { status: 400 });
    }

    const base = path.basename(parsed.pathname) || "document";
    const filename = base.includes(".") ? base : `${base}.dat`;

    await upsertInitial(docId, { filename, sourceUrl }, "submitted");
    await updateStatus("ingestion", docId, "queued", { mode: "url" });
    await publishToIngestion(docId, filename, sourceUrl, "web-url");
    return NextResponse.json({ doc_id: docId });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("/api/ingest error", err);
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
