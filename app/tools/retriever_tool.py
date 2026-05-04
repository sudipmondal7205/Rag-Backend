from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from app.core.embeddings import get_embedding
from app.core.pinecone_client import get_index



class RetrieverInput(BaseModel):
    query: str = Field(description="The search query to look up in the document database")



@tool("retriever", args_schema=RetrieverInput)
def retriever_tool(query: str, state: Annotated[dict, InjectedState]):
    """
        Search the knowledge base for the query relevant information. 
        It will return top 3 relavent docs, use only related docs to answer.
    """

    result = query_documents(
        query=query,
        doc_id=state['doc_id'],
        index=get_index(),
        embed_fn=get_embedding
    )

    # docs = [m['metadata']['text'] for m in result.matches]

    return {
        "retrieved_docs": result
    }


def query_documents(query: str, index, embed_fn, doc_id: str):

        vector = embed_fn([query])[0]

        results = index.query(
            vector=vector,
            top_k=3,
            include_metadata=True,
            filter={
                "doc_id": doc_id
            }
        )

        return results

