from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def create_title_generation_chain(api_key: str = None):
    """
    Create LangChain chain for generating concise journal titles.
    
    Uses GPT-3.5-turbo for speed and cost efficiency.
    
    Args:
        api_key: OpenAI API key
    
    Returns:
        Runnable chain for title generation
    """
    # Create prompt template
    prompt = ChatPromptTemplate.from_template("""Based on the following conversation, generate a concise, descriptive title (maximum 50 characters). The title should capture the main theme or topic.

Conversation:
{conversation}

Title (50 characters max, no quotes):""")
    
    # Create LLM (GPT-3.5 for speed/cost)
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.3,  # Lower temperature for consistent titles
        max_tokens=20,
        openai_api_key=api_key
    )
    
    # Create chain
    chain = prompt | llm
    
    return chain

