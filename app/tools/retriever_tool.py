from langchain.tools import ToolRuntime
from langchain_classic.schema import Document
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from app.core.embeddings import get_embedding_model
from app.core.pinecone_client import pinecone_index
from app.schema.agent_schema import AgentContext


class RetrieverInput(BaseModel):
    query: str = Field(description="The search query to look up in the document database")



@tool("retriever", args_schema=RetrieverInput, response_format="content_and_artifact")
async def retriever_tool(
        query: str, 
        runtime: ToolRuntime[AgentContext]
    ):
    """
        Search the knowledge base for the query relevant information. 
        It will return top 3 relavent docs, use only related docs to answer.
    """
    
    doc_id = runtime.context.get('doc_id')

    result = await query_documents(
        query=query,
        doc_id=doc_id
    )

    docs = "\n\n".join(
        m["metadata"]["text"]
        for m in result.matches
    )

    artifact = [
        Document(
            page_content=m['metadata']['text'],
            metadata={
                "source": {
                    "file_name": m['metadata']['file_name'],
                    "page_no": m['metadata']['page_no'],
                    "score": m['score']
                }
            }
        ) for m in result.matches
    ]
    
    return (docs, artifact)



async def query_documents(query: str, doc_id: str):

    embedding_model = get_embedding_model()

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

