from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.llm import llm
from app.db.conv_checkpoint_pool import pool
from langgraph.graph import StateGraph, START
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.models.user import User
from app.schema.agent_schema import AgentState
from app.schema.chat_schema import ChatResponse, InputQuery
from app.tools import TOOLS
from langchain_core.messages import HumanMessage
from app.services.conversation_service import conversationService
from sqlmodel.ext.asyncio.session import AsyncSession



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

        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", ToolNode(TOOLS))

        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")

        self._agent = graph.compile(checkpointer=self._checkpointer)

        return self._agent


    async def _agent_node(self, state: AgentState):
        """
        LLM node that may answer or request a tool call.
        """

        llm_with_tools = llm.bind_tools(TOOLS)

        response = await llm_with_tools.ainvoke(state['messages'])

        return {
            "messages": [response]
        }
    

    async def ask_question(self, session: AsyncSession, input_query: InputQuery, user: User):
        
        config = {"configurable": {"thread_id": input_query.thread_id}}

        conversation = await self.conv_service.get_conversation_by_id(session, input_query.thread_id)
        if conversation is None or (conversation.user_id != user.id):
            raise ConversationNotFoundException(conversation.id)
        
        state = {
            "messages": [HumanMessage(content=input_query.query)],
            "doc_id": conversation.doc_id
        }

        agent = await self._get_agent()

        final_state = await agent.ainvoke(state, config=config)
    
        return ChatResponse.model_validate(final_state['messages'][-1])




chatService = ChatService()

