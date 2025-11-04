import { NextRequest, NextResponse } from "next/server";
import { getStatusCollection, PipelineStatusDoc } from "@/app/utils/pipelineStatus";

export const runtime = "nodejs";
export const revalidate = 0;

export async function GET(req: NextRequest, { params }: { params: { doc_id: string } }) {
  try {
    const { doc_id } = params;
    const col = await getStatusCollection();
    const doc = await col.findOne({ _id: doc_id } as Partial<PipelineStatusDoc>);
    if (!doc) return NextResponse.json({ error: "not_found", doc_id }, { status: 404 });
    return NextResponse.json({ doc_id, states: doc.states || {}, updated_at: doc.updated_at });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("/api/status error", err);
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
