import { NextResponse } from 'next/server';
import { getCollection } from '../../utils/mongo';

export async function GET() {
  try {
    const collection = await getCollection('documentStatus');
    const documents = await collection.find({}).toArray();
    return NextResponse.json({ documents });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
