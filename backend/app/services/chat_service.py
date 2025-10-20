import logging
import time
from typing import AsyncGenerator, Dict, List

from app.chains.prompts import (
    JOURNALING_SYSTEM_PROMPT,
    format_retrieved_context,
)
from app.models import ChatResponse, Message, RetrievedContext, StreamEvent
from app.services.journal_service import JournalService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.token_counter import TokenCounter
from app.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    """
    Chat service orchestrating RAG, LLM, and journal saving.
    
    Features:
    - In-conversation memory (sends conversation history to LLM)
    - RAG context from past conversations
    - Token counting and dynamic summarization
    - Automatic journal saving after each message
    """
    
    MAX_CONTEXT_TOKENS = 8000
    RECENT_MESSAGES_TO_KEEP = 10
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        journal_service: JournalService
    ):
        """
        Initialize chat service.
        
        Args:
            llm_service: LLM service for completions
            rag_service: RAG service for context retrieval
            journal_service: Journal service for auto-saving
        """
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.journal_service = journal_service
        self.token_counter = TokenCounter(model=settings.openai_model)
    
    async def send_message(
        self,
        message: str,
        session_id: str,
        conversation_history: List[Message],
        use_rag: bool = True
    ) -> ChatResponse:
        """
        Process user message and generate AI response.
        
        Features:
        - Sends conversation history for in-conversation memory
        - Retrieves RAG context from past conversations
        - Manages tokens with dynamic summarization
        - Auto-saves after response
        
        Args:
            message: User's current message
            session_id: Session UUID
            conversation_history: Full conversation history (for memory)
            use_rag: Whether to retrieve context from past conversations
        
        Returns:
            ChatResponse with AI message, context, and auto-save status
        """
        start_time = time.time()
        retrieved_context = []
        retrieval_time_ms = 0
        auto_saved = False
        
        # Step 1: Retrieve RAG context from past conversations
        if use_rag:
            try:
                rag_start = time.time()
                retrieved_context = await self.rag_service.retrieve_context(
                    query=message,
                    top_k=5,
                    similarity_threshold=0.7
                )
                retrieval_time_ms = int((time.time() - rag_start) * 1000)
                logger.info(f"Retrieved {len(retrieved_context)} context chunks in {retrieval_time_ms}ms")
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
                # Continue without RAG context (graceful degradation)
        
        # Step 2: Build messages for LLM with conversation history
        messages_for_llm = await self._build_llm_messages(
            current_message=message,
            conversation_history=conversation_history,
            retrieved_contexts=retrieved_context
        )
        
        # Step 3: Get LLM completion
        try:
            ai_response_content = await self.llm_service.complete(
                messages=messages_for_llm,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise
        
        # Step 4: Create AI message object
        ai_message = Message(
            role="assistant",
            content=ai_response_content
        )
        
        # Step 5: Auto-save conversation (like ChatGPT)
        try:
            save_start = time.time()
            
            # Build complete conversation including new messages
            user_message = Message(role="user", content=message)
            complete_conversation = conversation_history + [user_message, ai_message]
            
            # Determine journal_id if this is a continuation
            journal_id = None
            if conversation_history:
                # This is a continuation - find existing journal
                # We'll use the first save's filename stored in metadata
                # For now, let journal_service handle it
                pass
            
            await self.journal_service.save_journal(
                session_id=session_id,
                messages=complete_conversation,
                journal_id=journal_id,
                title=None  # Auto-generate for new, preserve for existing
            )
            
            save_time_ms = int((time.time() - save_start) * 1000)
            auto_saved = True
            logger.info(f"Auto-saved conversation in {save_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            # Don't fail the whole request - user still gets AI response
            # Graceful degradation: chat works even if save fails
        
        # Step 6: Build response with metadata
        total_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            message=ai_message,
            retrieved_context=retrieved_context,
            auto_saved=auto_saved,
            metadata={
                "retrieval_time_ms": retrieval_time_ms,
                "response_time_ms": total_time_ms,
                "tokens_used": 0,  # TODO: Extract from LLM response
                "context_chunks_retrieved": len(retrieved_context),
                "conversation_length": len(conversation_history) + 2
            }
        )
    
    async def stream_message(
        self,
        message: str,
        session_id: str,
        conversation_history: List[Message],
        use_rag: bool = True
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream AI response token by token.
        
        Same features as send_message but with streaming.
        
        Args:
            message: User's current message
            session_id: Session UUID
            conversation_history: Full conversation history
            use_rag: Whether to retrieve RAG context
        
        Yields:
            StreamEvent objects (context, token, done, or error events)
        """
        start_time = time.time()
        retrieved_context = []
        auto_saved = False
        
        try:
            # Step 1: Retrieve RAG context
            if use_rag:
                try:
                    rag_start = time.time()
                    retrieved_context = await self.rag_service.retrieve_context(
                        query=message,
                        top_k=5,
                        similarity_threshold=0.7
                    )
                    retrieval_time_ms = int((time.time() - rag_start) * 1000)
                    
                    # Yield context event
                    yield StreamEvent(
                        type="context",
                        data={
                            "contexts": [
                                {
                                    "content": ctx.content,
                                    "metadata": ctx.metadata,
                                    "similarity": ctx.similarity_score
                                }
                                for ctx in retrieved_context
                            ],
                            "retrieval_time_ms": retrieval_time_ms
                        }
                    )
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")
            
            # Step 2: Build messages for LLM
            messages_for_llm = await self._build_llm_messages(
                current_message=message,
                conversation_history=conversation_history,
                retrieved_contexts=retrieved_context
            )
            
            # Step 3: Stream LLM response
            ai_response_content = ""
            
            async for token in self.llm_service.stream_complete(
                messages=messages_for_llm,
                temperature=0.7
            ):
                ai_response_content += token
                
                # Yield token event
                yield StreamEvent(
                    type="token",
                    data={"content": token}
                )
            
            # Step 4: Create AI message
            ai_message = Message(
                role="assistant",
                content=ai_response_content
            )
            
            # Step 5: Auto-save conversation
            try:
                user_message = Message(role="user", content=message)
                complete_conversation = conversation_history + [user_message, ai_message]
                
                await self.journal_service.save_journal(
                    session_id=session_id,
                    messages=complete_conversation,
                    journal_id=None,
                    title=None
                )
                
                auto_saved = True
                logger.info("Auto-saved streaming conversation")
                
            except Exception as e:
                logger.error(f"Auto-save failed during streaming: {e}")
            
            # Step 6: Yield completion event
            total_time_ms = int((time.time() - start_time) * 1000)
            
            yield StreamEvent(
                type="done",
                data={
                    "metadata": {
                        "response_time_ms": total_time_ms,
                        "auto_saved": auto_saved,
                        "context_chunks_retrieved": len(retrieved_context)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield StreamEvent(
                type="error",
                data={"message": str(e)}
            )
    
    async def _build_llm_messages(
        self,
        current_message: str,
        conversation_history: List[Message],
        retrieved_contexts: List[RetrievedContext]
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM with smart context management.
        
        Includes:
        - System prompt with RAG context
        - Summarized older messages (if token limit exceeded)
        - Recent messages (full)
        - Current message
        
        Args:
            current_message: User's current message
            conversation_history: Full conversation history
            retrieved_contexts: Retrieved RAG contexts
        
        Returns:
            List of message dicts for OpenAI API
        """
        messages = []
        
        # Format RAG context for system message
        context_instruction = format_retrieved_context(retrieved_contexts)
        
        # Add system message with RAG context
        system_prompt = JOURNALING_SYSTEM_PROMPT.format(context_instruction=context_instruction)
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Count tokens in system message
        system_tokens = self.token_counter.count_dict_message_tokens(messages[0])
        current_msg_tokens = self.token_counter.count_tokens(current_message)
        
        available_tokens = self.MAX_CONTEXT_TOKENS - system_tokens - current_msg_tokens - 100  # Buffer
        
        # Add conversation history with smart truncation
        if conversation_history:
            history_messages = await self._manage_conversation_history(
                conversation_history,
                available_tokens
            )
            messages.extend(history_messages)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        total_tokens = self.token_counter.count_dict_messages_tokens(messages)
        logger.info(f"Built LLM prompt with {total_tokens} tokens ({len(messages)} messages)")
        
        return messages
    
    async def _manage_conversation_history(
        self,
        conversation_history: List[Message],
        available_tokens: int
    ) -> List[Dict[str, str]]:
        """
        Manage conversation history to fit within token budget.
        
        Strategy:
        1. Always keep recent N messages (full)
        2. If total tokens > available, summarize older messages
        3. Return formatted messages for LLM
        
        Args:
            conversation_history: Full conversation history
            available_tokens: Available tokens for history
        
        Returns:
            List of message dicts (possibly with summarized older messages)
        """
        if not conversation_history:
            return []
        
        # Convert to message dicts
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ]
        
        # Count total tokens
        total_tokens = self.token_counter.count_dict_messages_tokens(history_dicts)
        
        # If fits within budget, return all messages
        if total_tokens <= available_tokens:
            logger.info(f"Conversation history fits in budget: {total_tokens}/{available_tokens} tokens")
            return history_dicts
        
        # Need to manage tokens - keep recent messages, summarize older
        logger.info(f"Conversation history exceeds budget: {total_tokens}/{available_tokens} tokens")
        
        # Keep recent N messages
        recent_messages = conversation_history[-self.RECENT_MESSAGES_TO_KEEP:]
        recent_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
        recent_tokens = self.token_counter.count_dict_messages_tokens(recent_dicts)
        
        # If recent messages alone exceed budget, just use them (truncate more aggressively)
        if recent_tokens >= available_tokens:
            logger.warning("Even recent messages exceed budget, using last 5")
            return recent_dicts[-5:]
        
        # Summarize older messages
        older_messages = conversation_history[:-self.RECENT_MESSAGES_TO_KEEP]
        
        if older_messages:
            try:
                summary = await self._summarize_messages(older_messages)
                
                # Add summary as system-like message
                result = [
                    {"role": "system", "content": f"Summary of earlier conversation:\n{summary}"}
                ]
                result.extend(recent_dicts)
                
                logger.info(f"Summarized {len(older_messages)} older messages, kept {len(recent_messages)} recent")
                return result
                
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                # Fallback: just use recent messages
                return recent_dicts
        
        return recent_dicts
    
    async def _summarize_messages(self, messages: List[Message]) -> str:
        """
        Summarize older messages using LLM.
        
        Args:
            messages: Messages to summarize
        
        Returns:
            Summary text
        """
        # Build conversation text
        conversation_text = ""
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            conversation_text += f"{role_label}: {msg.content}\n\n"
        
        # Create summarization prompt
        summary_prompt = [
            {
                "role": "system",
                "content": "Summarize the following conversation concisely, preserving key topics, decisions, and important context. Keep it under 200 words."
            },
            {
                "role": "user",
                "content": f"Summarize this conversation:\n\n{conversation_text}"
            }
        ]
        
        # Get summary
        summary = await self.llm_service.complete(
            messages=summary_prompt,
            temperature=0.3,  # Lower temp for consistent summaries
            max_tokens=300
        )
        
        return summary

