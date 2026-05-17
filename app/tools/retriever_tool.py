from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field
from app.core.embeddings import embedding_model
from app.core.pinecone_client import pinecone_index



class RetrieverInput(BaseModel):
    query: str = Field(description="The search query to look up in the document database")



@tool("retriever", args_schema=RetrieverInput, response_format="content_and_artifact")
async def retriever_tool(query: str, state: Annotated[dict, InjectedState]):
    """
        Search the knowledge base for the query relevant information. 
        It will return top 3 relavent docs, use only related docs to answer.
    """

    result = await query_documents(
        query=query,
        doc_id=state['doc_id']
    )
    state['tool_call_count'] = state.get('tool_call_count', 0) + 1

    docs = "\n\n".join(
        m["metadata"]["text"]
        for m in result.matches
    )
    artifact = {
        "sources": [{'file_name': m['metadata']['file_name'], 'page_no': m['metadata']['page_no'], 'score': m['score']} for m in result.matches]
    }
    return (docs, artifact)



async def query_documents(query: str, doc_id: str):

    vector = await embedding_model.aembed_query(query)
    results = pinecone_index.query(
        vector=vector,
        top_k=3,
        include_metadata=True,
        filter={
            "doc_id": doc_id
        }
    )
    return results

