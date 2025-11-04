
import { getCollection } from '../../utils/mongo';
import { NextResponse } from 'next/server';
import { ObjectId } from 'mongodb';

export async function GET(request: Request, { params }: { params: { doc_id?: string } }) {
  try {
    const collection = await getCollection('documentStatus');
    const url = new URL(request.url);
    const docId = url.pathname.split('/').pop();
    if (docId && docId !== 'status') {
      // Buscar por ID
      let objectId;
      try {
        objectId = new ObjectId(docId);
      } catch {
        return NextResponse.json({ error: 'ID inválido' }, { status: 400 });
      }
      const document = await collection.findOne({ _id: objectId });
      if (!document) {
        return NextResponse.json({ error: 'Documento no encontrado' }, { status: 404 });
      }
      return NextResponse.json(document);
    } else {
      // Devolver todos
      const documents = await collection.find({}).toArray();
      return NextResponse.json({ documents });
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
