import logging
from typing import AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.models import LLMError

logger = logging.getLogger(__name__)

class LLMService:
    """
    Handles all interactions with OpenAI's API.
    
    Uses singleton pattern for client connection pooling.
    """
    
    _async_client: Optional[AsyncOpenAI] = None
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o"):
        """
        Initialize LLM service.
        
        Args:
            openai_api_key: OpenAI API key
            model_name: Model to use for chat (default: gpt-4o)
        """
        self.api_key = openai_api_key
        self.model_name = model_name
        self.title_model = "gpt-3.5-turbo"  # cheaper/faster for title generation
    
    @classmethod
    def get_async_client(cls, api_key: str) -> AsyncOpenAI:
        """Get or create async OpenAI client (singleton)."""
        if cls._async_client is None:
            cls._async_client = AsyncOpenAI(api_key=api_key)
        return cls._async_client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get LLM completion (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
        
        Returns:
            Assistant's response content
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content or ""
            
            logger.info(f"LLM completion: {response.usage.total_tokens} tokens used")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise LLMError(str(e))
    
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM completion token by token.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
        
        Yields:
            Token strings as they are generated
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            logger.info("LLM streaming completed")
            
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            raise LLMError(str(e))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_title(
        self,
        conversation: str,
        max_length: int = 50
    ) -> str:
        """
        Generate concise title for conversation using GPT-3.5-turbo.
        
        Uses cheaper/faster model since title generation is simple.
        
        Args:
            conversation: Conversation text (usually first few messages)
            max_length: Maximum title length
        
        Returns:
            Generated title (concise, descriptive)
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            prompt = f"""Based on the following conversation, generate a concise, descriptive title (maximum {max_length} characters). The title should capture the main theme or topic.

Conversation:
{conversation[:1000]}

Title ({max_length} characters max, no quotes):"""
            
            response = await client.chat.completions.create(
                model=self.title_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent titles
                max_tokens=20
            )
            
            title = response.choices[0].message.content or "Untitled"
            
            # Strip quotes if present
            title = title.strip('"\'')
            
            # Truncate to max length
            if len(title) > max_length:
                title = title[:max_length].rsplit(' ', 1)[0]  # Trim to last complete word
            
            logger.info(f"Generated title: {title}")
            
            return title
            
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            # Return default instead of raising - title generation is not critical
            return "Untitled Conversation"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_title_from_content(
        self,
        content: str,
        max_length: int = 50
    ) -> str:
        """
        Generate concise title for write mode content using GPT-3.5-turbo.
        
        Args:
            content: Write mode content
            max_length: Maximum title length
        
        Returns:
            Generated title (concise, descriptive)
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            prompt = f"""Based on the following journal content, generate a concise, descriptive title (maximum {max_length} characters). The title should capture the main theme or topic.

Journal Content:
{content[:1000]}

Title ({max_length} characters max, no quotes):"""
            
            response = await client.chat.completions.create(
                model=self.title_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent titles
                max_tokens=20
            )
            
            title = response.choices[0].message.content or "Untitled"
            
            # Strip quotes if present
            title = title.strip('"\'')
            
            # Truncate to max length
            if len(title) > max_length:
                title = title[:max_length].rsplit(' ', 1)[0]  # Trim to last complete word
            
            logger.info(f"Generated title from content: {title}")
            
            return title
            
        except Exception as e:
            logger.error(f"Title generation from content failed: {e}")
            # Return default instead of raising - title generation is not critical
            return "Untitled Journal"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_therapeutic_response(
        self,
        journal_content: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Generate therapeutic response to journal content.
        
        Args:
            journal_content: The main journal content
            conversation_history: Previous AI interactions
        
        Returns:
            Therapeutic response message
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            # Build conversation context
            context = ""
            if conversation_history:
                context = "\nPrevious conversation:\n"
                for msg in conversation_history[-4:]:  # Last 4 messages for context
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n"
            
            prompt = f"""You are a compassionate, professional therapist providing thoughtful responses to journal entries. Your role is to:

1. Acknowledge the person's feelings and experiences with empathy
2. Offer gentle insights and observations
3. Ask thoughtful questions to encourage deeper reflection
4. Provide supportive guidance without being prescriptive
5. Maintain a warm, non-judgmental tone

Journal Entry:
{journal_content[:2000]}

{context}

Please provide a thoughtful, therapeutic response that acknowledges their feelings and offers gentle guidance. Keep it conversational and supportive, as if you're responding in a chat bubble. Do not include any formatting or quotes."""
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a compassionate therapist providing supportive responses to journal entries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content or "I appreciate you sharing your thoughts with me. How are you feeling about what you've written?"
            
            logger.info("Generated therapeutic response")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Therapeutic response generation failed: {e}")
            raise LLMError(str(e))
    
    async def stream_therapeutic_response(
        self,
        journal_content: str,
        conversation_history: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """
        Stream therapeutic response to journal content.
        
        Args:
            journal_content: The main journal content
            conversation_history: Previous AI interactions
        
        Yields:
            Token strings as they are generated
        
        Raises:
            LLMError: If API call fails
        """
        try:
            client = self.get_async_client(self.api_key)
            
            # Build conversation context
            context = ""
            if conversation_history:
                context = "\nPrevious conversation:\n"
                for msg in conversation_history[-4:]:  # Last 4 messages for context
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n"
            
            prompt = f"""You are a compassionate, professional therapist providing thoughtful responses to journal entries. Your role is to:

1. Acknowledge the person's feelings and experiences with empathy
2. Offer gentle insights and observations
3. Ask thoughtful questions to encourage deeper reflection
4. Provide supportive guidance without being prescriptive
5. Maintain a warm, non-judgmental tone

Journal Entry:
{journal_content[:2000]}

{context}

Please provide a thoughtful, therapeutic response that acknowledges their feelings and offers gentle guidance. Keep it conversational and supportive, as if you're responding in a chat bubble. Do not include any formatting or quotes."""
            
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a compassionate therapist providing supportive responses to journal entries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            logger.info("Therapeutic response streaming completed")
            
        except Exception as e:
            logger.error(f"Therapeutic response streaming failed: {e}")
            raise LLMError(str(e))

