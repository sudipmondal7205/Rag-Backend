from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.llm import llm
from app.db.conv_checkpoint_pool import pool
from langgraph.graph import END, StateGraph, START
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.models.user import User
from app.schema.agent_schema import AgentState
from app.schema.chat_schema import ChatMessage, InputQuery
from app.schema.stream_events import DoneEvent
from app.render_messages.streaming.transformer import transform_events
from app.tools import TOOLS
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.services.conversation_service import conversationService
from sqlmodel.ext.asyncio.session import AsyncSession

system_prompt = """
    You are a factual AI assistant. Your ONLY source of truth is the retrieved context provided below. Do not rely on any outside knowledge, assumptions, or your pre-trained memory.

    <instructions>
    1. Analyze the retrieved context carefully.
    2. Answer the user's query using ONLY the facts and data present in the context.
    3. Cite the document or source whenever possible.
    4. If the retrieved context does not contain the answer, you must respond EXACTLY with: "I cannot answer this question based on the provided information."
    </instructions>
"""

class ChatService:

    def __init__(self):
        self._checkpointer = None
        self._agent = None
        self.conv_service = conversationService

    async def _get_agent(self):

        if self._agent:
            return self._agent
        
        self._checkpointer = AsyncPostgresSaver(pool)

        graph = StateGraph(AgentState)
        tool_node = ToolNode(TOOLS)

        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self._tools_node)

        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", self._condition)
        graph.add_edge("tools", "agent")

        self._agent = graph.compile(checkpointer=self._checkpointer)

        return self._agent


    async def _agent_node(self, state: AgentState):
        """
        LLM node that may answer or request a tool call.
        """
        MAX_ITERATION = 5
        llm_with_tools = llm.bind_tools(TOOLS)
        if state.get('tool_call_count', 0) >= MAX_ITERATION:
            state['messages'].append(HumanMessage(
                content="""
                You have reached the tool limit.
                So now answer on whatever you have retrieved from the docs.
                Do not answer from your own context.
                """
            ))
            response = await llm_with_tools.ainvoke(state['messages'])
        else:
            response = await llm_with_tools.ainvoke(state['messages'])

        return {
            "messages": [response],
        }
    

    async def _tools_node(self, state: AgentState):
        tool_node = ToolNode(TOOLS)
        result = await tool_node.ainvoke(state)
        return {
            **result,
            "tool_call_count":
                state.get("tool_call_count", 0) + 1
        }
    
    def _condition(self, state: AgentState):
        last_msg = state['messages'][-1]
        if last_msg.tool_calls:
            return "tools"
        return END


    async def ask_question(self, session: AsyncSession, input_query: InputQuery, user: User):
        
        config = {"configurable": {"thread_id": input_query.thread_id}}

        conversation = await self.conv_service.get_conversation_by_id(session, input_query.thread_id)
        if conversation is None or (conversation.user_id != user.id):
            raise ConversationNotFoundException(conversation.id)
        
        state = {
            "messages": [HumanMessage(content=input_query.query)],
            "doc_id": conversation.doc_id,
            "tool_call_count": 0
        }
        agent = await self._get_agent()
        final_state = await agent.ainvoke(state, config=config)
    
        return ChatMessage(
            role="assistant",
            content=final_state['messages'][-1].content
        )



    async def ask_question_stream(self, session: AsyncSession, input_query: InputQuery, user: User):

        config = {"configurable": {"thread_id": input_query.thread_id}}

        conversation = await self.conv_service.get_conversation_by_id(session, input_query.thread_id)
        if conversation is None or (conversation.user_id != user.id):
            raise ConversationNotFoundException(conversation.id)
        
        state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=input_query.query)
            ],
            "doc_id": conversation.doc_id,
            "tool_call_count": 0
        }

        agent = await self._get_agent()

        async def event_generator():
            async for event in agent.astream_events(state, config=config, version='v2'):
                
                transformed = transform_events(event)
                if transformed:
                    yield transformed.model_dump_json() + "\n"
            
            yield DoneEvent(
                type="done"
            ).model_dump_json() + "\n"

        return StreamingResponse(
            event_generator(),
            media_type="application/x-ndjson"
        )




chatService = ChatService()

