from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.llm import llm
from app.db.conv_checkpoint_pool import pool
from langgraph.graph import StateGraph, START
from app.schema.agent_schema import AgentState
from app.services.vector_service import retriever
from langchain_core.messages import HumanMessage



class ChatService:

    def __init__(self):
        self.checkpointer = None
        self.agent = None


    async def _get_agent(self):

        if self.agent:
            return self.agent
        
        self.checkpointer = AsyncPostgresSaver(pool)

        graph = StateGraph(AgentState)

        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", ToolNode([retriever]))

        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")

        self.agent = graph.compile(checkpointer=self.checkpointer)

        return self.agent


    async def _agent_node(self, state: AgentState):
        """
        LLM node that may answer or request a tool call.
        """

        llm_with_tools = llm.bind_tools([retriever])

        response = await llm_with_tools.ainvoke(state['messages'])

        return {
            "messages": [response]
        }
    

    async def ask_question(self, user_id: str, doc_id: str, thread_id: str, query: str):

        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "messages": [HumanMessage(content=query)],
            "user_id": user_id,
            "doc_id": doc_id
        }

        agent = await self._get_agent()

        final_state = await agent.ainvoke(state, config=config)

        return final_state['messages'][-1].content
    



chatService = ChatService()


