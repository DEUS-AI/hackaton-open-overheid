export interface Document {
  name: string;
  id: string;
  reasons: string[];
  tags: string[];
  confidence: number;
  link: string;
}

export interface MindmapData {
  summary: string;
  documents: Document[];
}
