from typing import Annotated
import uuid
from datetime import datetime
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.core.embeddings import get_embedding
from app.core.pinecone_client import get_index



def upsert_document(texts: list[str], user_id: str, file_name: str, index, embed_fn):

    doc_id = str(uuid.uuid4())

    embeddings = embed_fn(texts)

    vectors = []
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        vectors.append({
            "id": f"{user_id}:{doc_id}:{i}",
            "values": emb,
            "metadata": {
                "user_id": user_id,
                "doc_id": doc_id,
                "text": text
            }
        })

    index.upsert(vectors)

    return doc_id



def query_documents(query: str, user_id: str, index, embed_fn, doc_id: str = None,):

    vector = embed_fn([query])[0]

    results = index.query(
        vector=vector,
        top_k=5,
        include_metadata=True,
        filter={
            "user_id": user_id,
            # "doc_id": doc_id
        }
    )

    return results


@tool
def retriever(query: str, state: Annotated[dict, InjectedState]):
    """
        Search the knowledge base for the query relevant information. 
        It will return top 3 relavent docs, use only related docs to answer.
    """

    result = query_documents(
        query=query,
        user_id=state['user_id'],
        doc_id=state['doc_id'],
        index=get_index(),
        embed_fn=get_embedding
    )

    docs = [m['metadata']['text'] for m in result.matches]

    return {
        "retrieved_docs": result
    }