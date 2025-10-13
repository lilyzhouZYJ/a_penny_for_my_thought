from typing import List

from app.models import RetrievedContext


JOURNALING_SYSTEM_PROMPT = """You are a thoughtful journaling companion. You help users reflect on their thoughts and experiences through natural conversation.

Be empathetic, ask clarifying questions when appropriate, and help users explore their thoughts more deeply. Your goal is to facilitate meaningful self-reflection and personal growth.

{context_instruction}

Respond naturally and conversationally. Keep your responses focused and not overly long unless the user asks for detailed exploration of a topic."""


def format_retrieved_context(contexts: List[RetrievedContext]) -> str:
    """
    Format retrieved contexts for inclusion in LLM prompt.
    
    Converts RetrievedContext objects into a readable string that provides
    the LLM with relevant context from past conversations.
    
    Args:
        contexts: List of context chunks retrieved from vector store
    
    Returns:
        Formatted context string for prompt injection, or empty string if no contexts
    """
    if not contexts:
        return ""
    
    context_str = "Here are some relevant excerpts from past conversations:\n\n"
    
    for i, ctx in enumerate(contexts, 1):
        # Extract date from metadata if available
        date = ctx.metadata.get('date', 'Unknown date')
        session_id = ctx.metadata.get('session_id', '')
        
        context_str += f"{i}. From {date}"
        if session_id:
            context_str += f" (Session: {session_id[:8]}...)"
        context_str += f":\n{ctx.content}\n\n"
    
    # Wrap with instructions for the LLM
    formatted_context = f"""
CONTEXT FROM PAST CONVERSATIONS:
{context_str}

Use this context to provide continuity and reference past discussions when relevant.
Don't force connections if they're not natural to the current conversation.
"""
    
    return formatted_context

def create_chat_prompt(user_message: str, retrieved_contexts: List[RetrievedContext] = None) -> List[Dict[str, str]]:
    """
    Create chat prompt messages list for LLM.
    
    Args:
        user_message: The user's current message
        retrieved_contexts: Optional contexts retrieved from RAG
    
    Returns:
        List of message dicts for OpenAI API format
    """
    # Format context if available
    context_instruction = ""
    if retrieved_contexts:
        context_instruction = format_retrieved_context(retrieved_contexts)
    
    # Build messages list
    system_message = JOURNALING_SYSTEM_PROMPT.format(
        context_instruction=context_instruction
    )
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    return messages

