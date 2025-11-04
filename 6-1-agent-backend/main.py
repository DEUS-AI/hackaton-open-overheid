import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from models import Document, QueryRequest, SummaryResponse
from promps import systemPrompt
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

DATABASE_NAME = "overheid"
COLLECTION_NAME = "chunks"

openai.api_key = OPENAI_API_KEY
openai_client = openai.OpenAI()
model = SentenceTransformer("all-MiniLM-L6-v2")

mongo_client = MongoClient(MONGO_URI)

database = mongo_client[DATABASE_NAME]
collection = database[COLLECTION_NAME]


def get_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()


def generate_reason_via_openai(query: str, tittle: str, chunk: str, tags: list[str]) -> str:
    tags_str = ", ".join(filter(None, tags))
    prompt = f"""
    You have a user's query: "{query}".
    You also have the title of a government document: "{tittle}".
    The tags associated with this document are: "{tags_str}".
    You also have a chunk of text from the document: "{chunk}".
    Based on the title and these tags, give me an array of 3 reasons why this document is relevant to the user's query.
"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": systemPrompt}, {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
            n=1,
            stream=False,
            timeout=5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating reason: {str(e)}"


def search_documents(embedding: list[float], query: str) -> list[Document]:
    try:
        pipeline = [
            {"$search": {"cosmosSearch": {"vector": embedding, "path": "embedding", "k": 70}}},
            {
                "$group": {
                    "_id": "$document_id",  # Group by document_id
                    "best_score": {"$max": {"$meta": "searchScore"}},
                    "chunks": {"$push": {"text": "$text", "score": {"$meta": "searchScore"}}},
                    "document_mongo_id": {"$first": "$document_mongo_id"},
                }
            },
            {
                "$sort": {"best_score": -1}  # Sort by the best score
            },
            {"$limit": 10},
            {
                "$lookup": {
                    "from": "messages",
                    "let": {"doc_id": "$document_mongo_id"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$doc_id"}]}}}],
                    "as": "document",
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "document_id": "$_id",
                    "best_score": 1,
                    "chunks": 1,
                    "document": {"$arrayElemAt": ["$document", 0]},
                }
            },
        ]

        records = list(collection.aggregate(pipeline))

        def generate_reason(record):
            try:
                doc_tags = record.get("document", {}).get("metadata", {}).get("keywords", [])
                return generate_reason_via_openai(
                    query=query,
                    tittle=record.get("document", {}).get("data", {}).get("title", ""),
                    chunk=record.get("chunks", [{}])[0].get("text", ""),
                    tags=[tag for tag in doc_tags if tag is not None],
                )
            except Exception as e:
                return f"Error generating reason: {str(e)}"

        reasons_map = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(generate_reason, r): r for r in records}
            for future in as_completed(futures):
                record = futures[future]
                reasons_map[record["document_id"]] = future.result()

        results = []
        for record in records:
            reason = reasons_map.get(record["document_id"], "No reason generated.")
            reasons = re.findall(r"\d+\.\s+(.*?)(?=\n|$)", reason, re.DOTALL)
            reasons = [r.strip() for r in reasons]

            doc_data = record.get("document", {}).get("data", {})
            doc_metadata = record.get("document", {}).get("metadata", {})
            document = Document(
                name=doc_data.get("name", "Unknown"),
                id=record["document_id"],
                reasons=reasons,
                tags=doc_metadata.get("keywords", []),
                confidence=record["best_score"],
                link=doc_data.get("url"),
            )
            results.append(document)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app = FastAPI(
    title="Terminal ZOO Backend", description="Backend API for the Terminal ZOO Hackathon project", version="0.1.0"
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to Terminal ZOO API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/search", response_model=SummaryResponse)
def search(req: QueryRequest):
    try:
        embedding = get_embedding(req.query)
        results = search_documents(embedding, req.query)
        response = SummaryResponse(summary=req.query, documents=results)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
