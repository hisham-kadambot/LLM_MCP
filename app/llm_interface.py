from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import os
from openai import OpenAI
from anthropic import Anthropic
from .auth import user_api_keys


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


# In-memory cache for storing model instances
_model_cache: Dict[str, LLMInterface] = {}


def get_llm_interface(username: str, model_name: str) -> LLMInterface:
    """Factory function to get or create an LLM interface instance.
    
    Args:
        username: The username for caching purposes
        model_name: The name of the model (openai, anthropic, etc.)
        
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
    
    # Get user's API key for the specified model
    if username not in user_api_keys:
        raise Exception(f"No API keys found for user '{username}'. Please set API keys first.")
    
    user_keys = user_api_keys[username]
    
    # Create new instance based on model name
    if model_name.lower() in ["openai", "gpt", "gpt-3.5-turbo", "gpt-4"]:
        # Try to get API key from user storage first, fallback to environment variable
        api_key = user_keys.get("openai") or user_keys.get("gpt") or user_keys.get("gpt-3.5-turbo") or user_keys.get("gpt-4") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception(f"OpenAI API key not found for user '{username}'. Please set it using /set_api_key endpoint.")
        instance = OpenAIInterface(api_key)
    
    elif model_name.lower() in ["anthropic", "claude", "claude-3"]:
        # Try to get API key from user storage first, fallback to environment variable
        api_key = user_keys.get("anthropic") or user_keys.get("claude") or user_keys.get("claude-3") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise Exception(f"Anthropic API key not found for user '{username}'. Please set it using /set_api_key endpoint.")
        instance = AnthropicInterface(api_key)
    
    else:
        # For any other model, try to get the exact model name from user storage
        api_key = user_keys.get(model_name)
        if not api_key:
            raise Exception(f"API key for model '{model_name}' not found for user '{username}'. Please set it using /set_api_key endpoint.")
        
        # Try to determine the interface type based on model name patterns
        if any(keyword in model_name.lower() for keyword in ["gpt", "openai"]):
            instance = OpenAIInterface(api_key)
        elif any(keyword in model_name.lower() for keyword in ["claude", "anthropic"]):
            instance = AnthropicInterface(api_key)
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
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
        "cached_keys": list(_model_cache.keys())
    }
