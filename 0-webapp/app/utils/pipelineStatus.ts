import { getCollection } from "@/app/utils/mongo";

// Shape of documents stored in the status collection
export interface PipelineStatusDoc {
  _id: string; // we use UUID strings as document ids
  created_at?: string;
  updated_at?: string;
  // states per pipeline service (e.g., ingestion, validation, etc.)
  states?: Record<
    string,
    {
      status: string;
      ts: string; // ISO timestamp
      extra?: Record<string, any>;
    }
  >;
}

type AnyRecord = Record<string, any>;

const DEFAULT_COLLECTION = process.env.MONGO_STATUS_COLLECTION || "pipeline_status";

export async function getStatusCollection() {
  // Explicitly type the collection so filters accept string _id
  return getCollection<PipelineStatusDoc>(DEFAULT_COLLECTION);
}

export async function upsertInitial(documentId: string, extra: AnyRecord = {}, initialState = "uploaded") {
  const col = await getStatusCollection();
  const now = new Date().toISOString();
  await col.findOneAndUpdate(
    { _id: documentId },
    {
      $setOnInsert: { _id: documentId, created_at: now },
      $set: { updated_at: now, "states.ingestion": { status: initialState, ts: now, extra } },
    },
    { upsert: true, returnDocument: "after" as any }
  );
}

export async function updateStatus(service: string, documentId: string, status: string, extra: AnyRecord = {}) {
  if (!documentId) throw new Error("document_id required");
  const col = await getStatusCollection();
  const now = new Date().toISOString();
  const stageField = `states.${service}`;
  await col.findOneAndUpdate(
    { _id: documentId },
    { $set: { [stageField]: { status, ts: now, extra }, updated_at: now }, $setOnInsert: { created_at: now, _id: documentId } },
    { upsert: true, returnDocument: "after" as any }
  );
}
