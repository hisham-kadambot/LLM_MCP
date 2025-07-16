from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import os
from openai import OpenAI
from anthropic import Anthropic
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_user_by_username, get_user_api_key
import easy_llama as ez
from ollama import chat as ollama_chat


class LLMInterface(ABC):
    """Abstract base class for LLM interfaces."""
    
    def __init__(self, api_key: str):
        """Initialize the LLM interface with an API key.
        
        Args:
            api_key: The API key for the LLM service
        """
        self._key = api_key
    
    @abstractmethod
    def chat(self, message: str, **kwargs) -> str:
        """Send a message to the LLM and return the response.
        
        Args:
            message: The message to send to the LLM
            **kwargs: Additional parameters for the chat request
            
        Returns:
            The response from the LLM
        """
        pass


class OpenAIInterface(LLMInterface):
    """OpenAI LLM interface implementation."""
    
    def __init__(self, api_key: str):
        """Initialize OpenAI interface.
        
        Args:
            api_key: OpenAI API key
        """
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)
    
    def chat(self, message: str, model: str = "gpt-3.5-turbo", **kwargs) -> str:
        """Send a message to OpenAI and return the response.
        
        Args:
            message: The message to send
            model: The OpenAI model to use (default: gpt-3.5-turbo)
            **kwargs: Additional parameters for the chat completion
            
        Returns:
            The response from OpenAI
        """
        # return "Hello, world!"
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicInterface(LLMInterface):
    """Anthropic LLM interface implementation."""
    
    def __init__(self, api_key: str):
        """Initialize Anthropic interface.
        
        Args:
            api_key: Anthropic API key
        """
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
    
    def chat(self, message: str, model: str = "claude-3-sonnet-20240229", **kwargs) -> str:
        """Send a message to Anthropic and return the response.
        
        Args:
            message: The message to send
            model: The Anthropic model to use (default: claude-3-sonnet-20240229)
            **kwargs: Additional parameters for the message
            
        Returns:
            The response from Anthropic
        """
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=[{"role": "user", "content": message}],
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class OllamaInterface(LLMInterface):
    """Ollama LLM interface implementation using the official ollama Python client."""
    def __init__(self, model_name: str):
        """Initialize Ollama interface.
        Args:
            model_name: The name of the model to use in Ollama
        """
        super().__init__(model_name)
        self.model_name = model_name

    def chat(self, message: str, max_tokens: int = 256, temperature: float = 0.8, **kwargs) -> str:
        """Send a message to Ollama and return the response.
        Args:
            message: The message to send
            max_tokens: Number of tokens to generate (passed as num_predict)
            temperature: Sampling temperature
            **kwargs: Additional parameters (ignored for now)
        Returns:
            The response from Ollama
        """
        response = ollama_chat(
            model=self.model_name,
            messages=[{"role": "user", "content": message}],
            options={"num_predict": max_tokens, "temperature": temperature}
        )
        # The response object has a .message.content attribute
        return response.message.content


# In-memory cache for storing model instances
_model_cache: Dict[str, LLMInterface] = {}


def get_llm_interface(username: str, model_name: str, db: Session = None) -> LLMInterface:
    """Factory function to get or create an LLM interface instance.
    
    Args:
        username: The username for caching purposes
        model_name: The name of the model (openai, anthropic, etc.)
        db: Database session (optional, will create one if not provided)
        
    Returns:
        An LLM interface instance
        
    Raises:
        ValueError: If the model name is not supported
        Exception: If API key is not found for the user and model
    """
    cache_key = f"{username}:{model_name}"
    
    # Check if instance exists in cache
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    # Get database session if not provided
    if db is None:
        db = next(get_db())
    
    # Get user from database
    user = get_user_by_username(db, username)
    if not user:
        raise Exception(f"User '{username}' not found in database.")
    
    # Create new instance based on model name
    if model_name.lower() in ["openai", "gpt", "gpt-3.5-turbo", "gpt-4"]:
        # Try to get API key from database first, fallback to environment variable
        api_key_obj = get_user_api_key(db, user.id, "openai")
        api_key = api_key_obj.api_key if api_key_obj else os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception(f"OpenAI API key not found for user '{username}'. Please set it using /set_api_key endpoint.")
        instance = OpenAIInterface(api_key)
    
    elif model_name.lower() in ["anthropic", "claude", "claude-3"]:
        # Try to get API key from database first, fallback to environment variable
        api_key_obj = get_user_api_key(db, user.id, "anthropic")
        api_key = api_key_obj.api_key if api_key_obj else os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise Exception(f"Anthropic API key not found for user '{username}'. Please set it using /set_api_key endpoint.")
        instance = AnthropicInterface(api_key)
    
    else:
        # If not OpenAI or Anthropic, treat as Ollama model (no API key required)
        instance = OllamaInterface(model_name)
    
    # Cache the instance
    _model_cache[cache_key] = instance
    return instance


def clear_cache():
    """Clear the in-memory cache."""
    global _model_cache
    _model_cache.clear()


def get_cache_info() -> Dict[str, Any]:
    """Get information about the current cache state.
    
    Returns:
        Dictionary containing cache information
    """
    return {
        "cache_size": len(_model_cache),
        "cached_models": list(_model_cache.keys())
    }
