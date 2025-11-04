import neo4j, { Driver, Record as Neo4jRecord, Session } from "neo4j-driver";
import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

// Ensure Node.js runtime (not edge) for native deps and model downloads
export const runtime = "nodejs";

// Singleton: Neo4j driver
let neo4jDriver: Driver | null = null;
function getNeo4jDriver() {
  if (!neo4jDriver) {
    const uri = process.env.NEO4J_URI;
    const user = process.env.NEO4J_USERNAME;
    const pass = process.env.NEO4J_PASSWORD;
    if (!uri || !user || !pass) {
      throw new Error("NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD are not set");
    }
    neo4jDriver = neo4j.driver(uri, neo4j.auth.basic(user, pass));
  }
  return neo4jDriver;
}

// Singleton: OpenAI client
let openaiClient: OpenAI | null = null;
function getOpenAI() {
  if (!openaiClient) {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error("OPENAI_API_KEY is not set");
    }
    openaiClient = new OpenAI({ apiKey });
  }
  return openaiClient;
}

// Embeddings using OpenAI (simpler deployment)
async function getEmbedding(text: string): Promise<number[]> {
  const client = getOpenAI();
  const resp = await client.embeddings.create({
    model: "text-embedding-3-small",
    input: text,
  });
  return resp.data[0].embedding as unknown as number[];
}

const systemPrompt = `
You are a helpful assistant that generates a reason for the relevance of a document to a query.
    document_recommendation_explanation:
  purpose: >
    Ensure the assistant clearly explains in Dutch why a specific document is being recommended,
    based on the user's context and information needs.
  instruction: >
    When presenting a document, explain why it is relevant by giving approximately 3
    clear, concrete reasons in Dutch. These reasons should be directly connected to what the
    user shared earlier (e.g. their role, goal, topic of interest, or personal situation).
  example_structure:
    - Relevance to user query or concern
    - Source or authority of the document (e.g. key institution or actor involved)
    - Content that aligns with user's purpose (e.g. findings, data, actions, decisions)
  tone_guidelines:
    - Keep the explanation short and specific
    - Use neutral and factual language
    - Avoid vague phrasing or generic praise
  sample_output: >
    "This document is relevant because:  
    1. It discusses the compensation measures you're researching.  
    2. It was published by the Ministry of Finance, which is directly responsible.  
    3. It includes a timeline of policy changes you mentioned earlier."
`;

async function generateReasonViaOpenAI(
  query: string,
  titel: string,
  tags: string[]
): Promise<string> {
  const tagsStr = tags.filter(Boolean).join(", ");
  const prompt = `
    You have a user's query: "${query}".
    You also have the title of a government document: "${titel}".
    The tags associated with this document are: "${tagsStr}".
    Based on the title and these tags, give me an array of 3 reasons why this document is relevant to the user's query.
  `;
  try {
    const client = getOpenAI();
    const resp = await client.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt },
      ],
      temperature: 0.2,
      max_tokens: 200,
      n: 1,
    });
    return resp.choices?.[0]?.message?.content ?? "";
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return `Error generating reason: ${msg}`;
  }
}

type QueryRequest = { query: string };

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as QueryRequest;
    const q = (body?.query ?? "").trim();
    if (!q) {
      return NextResponse.json({ error: "Missing query" }, { status: 400 });
    }

    // 1) Embedding
    const embedding = await getEmbedding(q);

    // 2) Neo4j semantic search
    const query = `
    WITH $embedding AS e
    MATCH (d:Document)
    WHERE d.embedding IS NOT NULL
    WITH d,
        reduce(s = 0.0, i in range(0, size(e)-1) | s + e[i] * d.embedding[i]) AS dot_product,
        reduce(s = 0.0, i in range(0, size(e)-1) | s + e[i]^2) AS norm_e,
        reduce(s = 0.0, i in range(0, size(d.embedding)-1) | s + d.embedding[i]^2) AS norm_d
    WITH d,
        dot_product / (sqrt(norm_e) * sqrt(norm_d)) AS score
    OPTIONAL MATCH (d)-[:HAS]->(m:Metadata)
    RETURN d.identifier AS id, d.titel AS titel, d.pdf_url AS pdf_url, score,
           m.documentsoort AS documentsoort, m.thema AS thema
    ORDER BY score DESC
    LIMIT 10
    `;

    const driver = getNeo4jDriver();
    const session: Session = driver.session();
    type NeoRecord = {
      id: string;
      titel: string;
      pdf_url: string;
      score: number;
      documentsoort?: string | null;
      thema?: string | null;
    };
    let records: NeoRecord[] = [];
    try {
      const res = await session.run(query, { embedding });
      records = res.records.map((r: Neo4jRecord) => ({
        id: r.get("id"),
        titel: r.get("titel"),
        pdf_url: r.get("pdf_url"),
        score: r.get("score"),
        documentsoort: r.get("documentsoort"),
        thema: r.get("thema"),
      }));
    } finally {
      await session.close();
    }

    // 3) Generate reasons in parallel
    const reasonsMap: Record<string, string> = {};
    await Promise.all(
      records.map(async (rec) => {
        const docTags = [rec["documentsoort"], rec["thema"]].filter(Boolean) as string[];
        const reason = await generateReasonViaOpenAI(q, rec["titel"], docTags);
        reasonsMap[rec["id"]] = reason;
      })
    );

    // 4) Build response (mirror Python behavior)
    const staticPdfLink = "https://zoek.officielebekendmakingen.nl/kst-31066-924.pdf";
    const documents = records.map((rec) => {
      const rawReason = reasonsMap[rec["id"]] || "No reason generated.";
      const matches = Array.from(rawReason.matchAll(/\d+\.\s+([\s\S]*?)(?=\n|$)/g)).map((m) =>
        m[1].trim()
      );
      const reasons = matches.length > 0 ? matches : [rawReason].filter(Boolean);
      const rawTags = [rec["documentsoort"], rec["thema"]];
      const processedTags = rawTags.filter(Boolean);
      return {
        id: rec["id"],
        name: rec["titel"],
        link: staticPdfLink,
        confidence: rec["score"],
        tags: processedTags,
        reasons,
      };
    });

    const response = { summary: q, documents };
    return NextResponse.json(response);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("/api/search error", err);
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
