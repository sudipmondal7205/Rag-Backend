from langchain.messages import SystemMessage
from langchain_classic.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate


grade_docs_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """
            You are a strict data auditor. Evaluate whether the provided text context contains
            semantically useful information to answer the user's question. Return a binary 
            score structure: 'yes' or 'no'.
        """
    ),
    HumanMessagePromptTemplate.from_template(
        """
            User Query: {user_query}
            Retrieved Text: {retrieved_text}
        """
    )
])



transform_query_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """
            You are an expert search string optimizer. Your job is to rewrite a failed search query into a completely 
            new, alternative search string.
            CRITICAL RULES:
                1. Do NOT reuse the words, phrases, or structure from the FAILED_PREVIOUS_QUERY.
                2. Focus purely on target noun entities, alternative synonyms, or broader categorization keywords related to the ORIGINAL_USER_QUESTION.
                3. Do not include conversational fluff, instructions, or label prefixes.
                4. Return ONLY the raw optimized string line.
        """
    ),
    HumanMessagePromptTemplate.from_template(
        """
            ORIGINAL_USER_QUESTION: {user_query}
            FAILED_PREVIOUS_QUERY: {updated_query}
            REJECTED_IRRELEVANT_CONTEXT:{retrieved_text}
            TASK: Provide a completely revised, DIFFERENT alternative search query string based on the rules above.
        """
    )
])



generator_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """
            You are a professional research agent. Synthesize a clean answer to the user prompt.
            You must base your answer ONLY on the provided Context text block. If the retrived text does not 
            contain the answer for the user query then you just say that you can't find any usefull information
            from the provided documents.
        """
    ),
    HumanMessagePromptTemplate.from_template(
        """
            User Query: {user_query},
            Retrieved text: {retrieved_text}
        """
    )
])


system_message = SystemMessage(
    """
        You are a factual AI assistant. Your ONLY source of truth is the retrieved context from the tools. Do not rely on any outside knowledge, assumptions, or your pre-trained memory.

        <instructions>
        1. Analyze the retrieved context carefully.
        2. Answer the user's query using ONLY the facts and data present in the context.
        3. Cite the document or source whenever possible.
        </instructions>
    """
)