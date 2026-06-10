import uuid
from fastapi.responses import StreamingResponse
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode
from psycopg_pool import AsyncConnectionPool
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import AIMessage, HumanMessage
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.render_messages.streaming.transformer import transform_events_v2
from app.repository.conversation_repo import ConversationRepository
from app.schema.agent_schema import AgentContext, AgentStateV2 as AgentState, GradeDocuments
from app.schema.chat_schema import InputQuery
from app.schema.stream_events import DoneEvent
from app.tools.retriever_tool import retriever_tool
from app.llm_prompts.agent_prompts import grade_docs_prompt, transform_query_prompt, generator_prompt, system_message
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
from langgraph.runtime import Runtime




class AgentService:

    def __init__(self, llm: BaseChatModel, embedding: Embeddings, pool: AsyncConnectionPool, conversation_repo: ConversationRepository):
        self._llm = llm
        self._embedding = embedding
        self._conv_repo = conversation_repo
        self._checkpointer = AsyncPostgresSaver(pool)
        self._agent = None

    def _build_agent(self):
        if self._agent:
            return self._agent
        
        async def route_node(state: AgentState, runtime: Runtime[AgentContext]):
            _llm_with_tools = self._llm.bind_tools([retriever_tool])
            response = await _llm_with_tools.ainvoke(state['messages'])
            return {
                "messages": [response]
            }
        
        def sync_artifacts_node(state: AgentState, runtime: Runtime[AgentContext]):
            """Safely extracts tool artifacts and assigns them to the state channel."""
            last_tool_message = next((msg for msg in reversed(state["messages"]) if msg.type == "tool"), None)
            if last_tool_message:
                artifacts = getattr(last_tool_message, "artifact", []) or []
                return {"documents": artifacts}
            return {}

        async def grade_docs(state: AgentState, runtime: Runtime[AgentContext]):  
            grade__llm = self._llm.with_structured_output(GradeDocuments)
            retrieved_text = "\n\n".join([docs.page_content for docs in state.get('documents', [])])
            prompt = await grade_docs_prompt.aformat_messages(user_query=state['user_query'], retrieved_text=retrieved_text)
            assesment = await grade__llm.ainvoke(prompt)
            documents = state['documents']
            if assesment.binary_score == 'no':
                documents = []
            return {
                "grade_result": assesment.binary_score,
                "documents": documents
            }
        
        async def query_transformer(state: AgentState, runtime: Runtime[AgentContext]):
            retrieved_text = "\n\n".join([docs.page_content for docs in state['documents']])
            prompt = await transform_query_prompt.aformat_messages(
                user_query=state['user_query'],
                updated_query=state.get('updated_query', ''),
                retrieved_text=retrieved_text
            )
            new_query = await self._llm.ainvoke(prompt)
            new_query = new_query.content.strip()
            state_msg = AIMessage(
                content="Refining my documentation lookup to isolate data...",
                tool_calls=[{"name": "retriever", "args": {'query': new_query}, "id": "retry_call_id_" + str(state.get("loop_count", 0))}]
            )
            return {
                'messages': [state_msg],
                'updated_query': new_query,
                'loop_count': state.get("loop_count", 0) + 1,
            }
        
        async def generator(state: AgentState, runtime: Runtime[AgentContext]):
            retrieved_text = "\n\n".join([docs.page_content for docs in state['documents']])
            prompt = await generator_prompt.aformat_messages(user_query=state['user_query'], retrieved_text=retrieved_text)
            response = await self._llm.ainvoke(prompt)
            return {
                "messages": [response]
            }

        def route_intent(state: AgentState, runtime: Runtime[AgentContext]):
            last_msg = state['messages'][-1]
            if last_msg.tool_calls:
                return 'tools'
            return 'end'
        
        def route_generator(state: AgentState, runtime: Runtime[AgentContext]):
            if state['grade_result'] == 'yes':
                return 'generator'
            if state['loop_count'] >= 2:
                return 'generator'
            return 'query_transform'


        builder = StateGraph(state_schema=AgentState, context_schema=AgentContext)

        builder.add_node('agent', route_node)
        builder.add_node('tools', ToolNode([retriever_tool]))
        builder.add_node('sync_artifacts_node', sync_artifacts_node)
        builder.add_node('grade_docs', grade_docs)
        builder.add_node('query_transformer', query_transformer)
        builder.add_node('generator', generator)

        builder.add_edge(START, 'agent')
        builder.add_conditional_edges(
            'agent', route_intent,
            {
                'tools': 'tools',
                'end': END
            }
        )
        builder.add_edge('tools', 'sync_artifacts_node')
        builder.add_edge('sync_artifacts_node', 'grade_docs')
        builder.add_conditional_edges(
            'grade_docs',
            route_generator,
            {
                'generator': 'generator',
                'query_transform': 'query_transformer'
            }
        )
        builder.add_edge('query_transformer', 'tools')
        builder.add_edge('generator', END)

        self._agent = builder.compile(checkpointer=self._checkpointer)
        return self._agent



    async def chat_stream(self, input_query: InputQuery, user_id: uuid.UUID, session: AsyncSession):

        conversation = await self._conv_repo.get_conversation(session, input_query.thread_id)
        if conversation is None or (conversation.user_id != user_id):
            raise ConversationNotFoundException(input_query.thread_id)
        
        agent = self._build_agent()
        config = {"configurable": {"thread_id": input_query.thread_id}}

        run_context = AgentContext(doc_id=conversation.doc_id)
        initial_state = {
            "messages": [
                system_message,
                HumanMessage(content=input_query.query)
            ],
            "user_query": input_query.query,
            "updated_query": "",
            "documents": [],
            "loop_count": 0,
            "grade_result": "no"
        }

        async def event_generator():
            async for event in agent.astream_events(initial_state, context=run_context, config=config, version='v2'):
                transformed = transform_events_v2(event)
                if transformed:
                    yield f"data: {transformed.model_dump_json()}\n\n"

            yield f"data: {DoneEvent(
                type='done'
            ).model_dump_json()}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
