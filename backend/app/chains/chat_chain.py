from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough

from app.chains.prompts import JOURNALING_SYSTEM_PROMPT

def create_chat_chain(
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    api_key: str = None
):
    """
    Create LangChain chat chain for journaling conversations.
    
    Args:
        model_name: OpenAI model to use
        temperature: Sampling temperature
        api_key: OpenAI API key
    
    Returns:
        Runnable chain for chat completions
    """
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", JOURNALING_SYSTEM_PROMPT),
        ("human", "{user_message}")
    ])
    
    # Create LLM
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        streaming=True,
        openai_api_key=api_key
    )
    
    # Create chain
    chain = (
        RunnablePassthrough()
        | prompt
        | llm
    )
    
    return chain

