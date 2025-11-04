import { MongoClient, Collection, Db, Document } from "mongodb";

let client: MongoClient | null = null;
let db: Db | null = null;

function mongoUri(): string {
  const uri = process.env.MONGO_URI;
  if (uri) return uri;
  const host = process.env.MONGO_HOST || "mongodb";
  const port = process.env.MONGO_PORT || "27017";
  const dbName = process.env.MONGO_DB || "overheid";
  const user = process.env.MONGO_USER || "mongoadmin";
  const pwd = process.env.MONGO_PASSWORD || "mongopass";
  const authDb = process.env.MONGO_AUTH_DB || "admin";
  return `mongodb://${user}:${pwd}@${host}:${port}/${dbName}?authSource=${authDb}`;
}

export async function getDb(): Promise<Db> {
  if (db && client) return db;
  const uri = mongoUri();
  // Reuse global across hot reloads
  if (!(globalThis as any)._mongoClient) {
    (globalThis as any)._mongoClient = new MongoClient(uri);
  }
  client = (globalThis as any)._mongoClient as MongoClient;
  // mongodb v6 no longer exposes topology; connect() is idempotent
  await client.connect();
  const dbName = process.env.MONGO_DB || "overheid";
  db = client.db(dbName);
  return db;
}

export async function getCollection<T extends Document = Document>(name: string): Promise<Collection<T>> {
  const database = await getDb();
  return database.collection<T>(name);
}
