"""OpenAI service for LLM and embeddings."""

from typing import List, Dict, Any, Optional
import openai

from app.core.config import settings


class OpenAIService:
    """OpenAI API service for LLM and embeddings."""

    def __init__(self):
        """Initialize OpenAI client."""
        openai.api_key = settings.OPENAI_API_KEY
        self.llm_model = settings.DEFAULT_LLM_MODEL
        self.embedding_model = settings.DEFAULT_EMBEDDING_MODEL

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with optional function calling.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool/function definitions
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Completion response dict
        """
        try:
            params = {
                "model": self.llm_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = openai.chat.completions.create(**params)

            return {
                "content": response.choices[0].message.content,
                "tool_calls": (
                    response.choices[0].message.tool_calls
                    if hasattr(response.choices[0].message, "tool_calls")
                    else None
                ),
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            print(f"Error in chat completion: {str(e)}")
            raise

    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Create an embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector (list of floats) or None
        """
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text,
            )

            return response.data[0].embedding

        except Exception as e:
            print(f"Error creating embedding: {str(e)}")
            return None

    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts in a batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            print(f"Error creating batch embeddings: {str(e)}")
            return []
