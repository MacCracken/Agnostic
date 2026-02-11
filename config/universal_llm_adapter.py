"""
Universal LLM Adapter for CrewAI
Provides compatibility between the model manager and CrewAI's expected interface
"""

import os
import sys
import json
import asyncio
import logging
# Add config path for imports
from config.environment import config
from typing import Dict, List, Any, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field

# Add the config directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from model_manager import model_manager
except ImportError:
    print("Warning: model_manager not available, using fallback")
    model_manager = None

logger = logging.getLogger(__name__)

class UniversalLLMAdapter(LLM):
    """
    Universal LLM adapter that bridges CrewAI with the model manager
    Supports multiple model providers through a unified interface
    """
    
    provider_name: str = Field(default="openai")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=4000)
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provider_name = kwargs.get('provider_name', 'openai')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4000)
        
        # Initialize model manager if available
        if model_manager is None:
            logger.warning("Model manager not available, using direct OpenAI")
            self._init_direct_openai()
    
    def _init_direct_openai(self) -> Dict[str, Any]:
        """Initialize direct OpenAI connection as fallback"""
        try:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
            
            if api_key:
                self.direct_llm = ChatOpenAI(
                    model=model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    openai_api_key=api_key
                )
                logger.info("Initialized direct OpenAI connection")
            else:
                self.direct_llm = None
                logger.error("No OpenAI API key found")
        except ImportError:
            logger.error("langchain_openai not available")
            self.direct_llm = None
    
    @property
    def _llm_type(self) -> str:
        return f"universal_{self.provider_name}"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Synchronous call to the LLM
        """
        try:
            # Use asyncio to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._acall(prompt, stop, run_manager, **kwargs))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in synchronous LLM call: {e}")
            return f"Error: {str(e)}"
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Asynchronous call to the LLM
        """
        try:
            # Convert prompt to message format
            messages = [{"role": "user", "content": prompt}]
            
            # Use model manager if available
            if model_manager:
                result = await model_manager.chat_completion(
                    messages=messages,
                    provider=self.provider_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    **kwargs
                )
                
                if result.get("success", False):
                    return result["content"]
                else:
                    logger.error(f"Model manager call failed: {result.get('error', 'Unknown error')}")
                    # Try fallback if available
                    if hasattr(self, 'direct_llm') and self.direct_llm:
                        logger.info("Falling back to direct OpenAI connection")
                        return await self._fallback_direct_call(prompt, **kwargs)
                    else:
                        return f"Error: {result.get('error', 'Unknown error')}"
            
            # Fallback to direct connection
            elif hasattr(self, 'direct_llm') and self.direct_llm:
                return await self._fallback_direct_call(prompt, **kwargs)
            
            else:
                return "Error: No LLM provider available"
                
        except Exception as e:
            logger.error(f"Error in async LLM call: {e}")
            return f"Error: {str(e)}"
    
    async def _fallback_direct_call(self, prompt: str, **kwargs) -> str:
        """Fallback to direct LLM call"""
        try:
            if hasattr(self.direct_llm, 'ainvoke'):
                # Use async invoke if available
                response = await self.direct_llm.ainvoke(prompt)
                return response.content
            else:
                # Use synchronous invoke
                response = self.direct_llm.invoke(prompt)
                return response.content
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}")
            return f"Error: {str(e)}"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters"""
        return {
            "provider_name": self.provider_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

def create_llm(provider_name: Optional[str] = None, **kwargs) -> UniversalLLMAdapter:
    """
    Create an LLM instance for CrewAI
    
    Args:
        provider_name: Name of the provider to use
        **kwargs: Additional parameters
    
    Returns:
        UniversalLLMAdapter instance
    """
    # Determine provider from environment or parameter
    if not provider_name:
        provider_name = os.getenv("PRIMARY_MODEL_PROVIDER", "openai")
    
    return UniversalLLMAdapter(
        provider_name=provider_name,
        **kwargs
    )

# Factory function for easy integration
def get_crewai_llm() -> LLM:
    """
    Get a CrewAI-compatible LLM instance
    This is the main entry point for CrewAI integration
    """
    return create_llm()