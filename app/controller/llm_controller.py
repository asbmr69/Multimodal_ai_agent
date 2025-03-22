import logging
import asyncio
import os
from typing import Dict, Any, Optional, List
import json

# Import providers - conditionally based on what's installed
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Add new provider imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import mistralai.client
    from mistralai.client import MistralClient
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

try:
    import deepseek
    from deepseek import DeepSeekClient
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

from config import Config

class LLMController:
    """Manages communication with various LLM providers."""
    
    def __init__(self, event_manager):
        self.logger = logging.getLogger(__name__)
        self.event_manager = event_manager
        self.config = Config()
        
        # Initialize provider clients
        self.clients = {}
        self._initialize_providers()
        
        # Set default provider
        self.current_provider = self.config.settings['llm']['provider']
        self.current_model = self.config.settings['llm']['model']
        
        # Register event handlers
        self._register_events()
        
        self.logger.info(f"LLM Controller initialized with provider: {self.current_provider}")
    
    def _initialize_providers(self) -> None:
        """Initialize LLM provider clients based on configuration."""
        llm_config = self.config.settings['llm']
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and llm_config.get('api_key'):
            try:
                self.clients['openai'] = openai.AsyncOpenAI(
                    api_key=llm_config.get('api_key')
                )
                self.logger.info("OpenAI client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Initialize Anthropic client if available
        if ANTHROPIC_AVAILABLE and llm_config.get('anthropic_api_key'):
            try:
                self.clients['anthropic'] = anthropic.AsyncAnthropic(
                    api_key=llm_config.get('anthropic_api_key')
                )
                self.logger.info("Anthropic client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {str(e)}")
                
        # Initialize Gemini client if available
        if GEMINI_AVAILABLE and llm_config.get('gemini_api_key'):
            try:
                genai.configure(api_key=llm_config.get('gemini_api_key'))
                self.clients['gemini'] = genai
                self.logger.info("Gemini client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {str(e)}")
                
        # Initialize Mistral client if available
        if MISTRAL_AVAILABLE and llm_config.get('mistral_api_key'):
            try:
                self.clients['mistral'] = MistralClient(
                    api_key=llm_config.get('mistral_api_key')
                )
                self.logger.info("Mistral client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Mistral client: {str(e)}")
                
        # Initialize DeepSeek client if available
        if DEEPSEEK_AVAILABLE and llm_config.get('deepseek_api_key'):
            try:
                self.clients['deepseek'] = DeepSeekClient(
                    api_key=llm_config.get('deepseek_api_key')
                )
                self.logger.info("DeepSeek client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
    
    def _register_events(self) -> None:
        """Register handlers for LLM-related events."""
        self.event_manager.subscribe("config_updated", self._on_config_updated)
    
    async def _on_config_updated(self, event_type: str, data: Any) -> None:
        """Handle config updated event."""
        if 'llm' in data:
            self.logger.info("LLM configuration updated, reinitializing clients")
            self._initialize_providers()
            self.current_provider = self.config.settings['llm']['provider']
            self.current_model = self.config.settings['llm']['model']
    
    async def chat_completion(self, 
                              messages: List[Dict[str, str]], 
                              temperature: Optional[float] = None,
                              provider: Optional[str] = None,
                              model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a chat completion using the configured LLM.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Optional temperature override
            provider: Optional provider override
            model: Optional model override
            
        Returns:
            Response from the LLM
        """
        provider = provider or self.current_provider
        model = model or self.current_model
        temperature = temperature if temperature is not None else self.config.settings['llm']['temperature']
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                await self.event_manager.emit("llm_request_start", {
                    "provider": provider,
                    "model": model,
                    "message_count": len(messages)
                })
                
                response = await self._send_request(provider, model, messages, temperature)
                
                await self.event_manager.emit("llm_request_complete", {
                    "provider": provider,
                    "model": model,
                    "success": True
                })
                
                return response
            except (TimeoutError, ConnectionError) as e:
                # Transient errors that might resolve with retry
                retry_count += 1
                self.logger.warning(f"Retrying LLM request ({retry_count}/{max_retries}): {str(e)}")
                await asyncio.sleep(1 * retry_count)  # Exponential backoff
            except Exception as e:
                # Non-transient errors
                self.logger.error(f"Error in LLM request: {str(e)}")
                await self.event_manager.emit("llm_error", {"error": str(e), "provider": provider})
                raise
        
        # If we get here, all retries failed
        error_msg = f"Failed to get LLM response after {max_retries} attempts"
        self.logger.error(error_msg)
        raise Exception(error_msg)
    
    async def _send_request(self, 
                           provider: str, 
                           model: str, 
                           messages: List[Dict[str, str]], 
                           temperature: float) -> Dict[str, Any]:
        """Send request to appropriate provider."""
        if provider == "openai":
            return await self._send_openai_request(model, messages, temperature)
        elif provider == "anthropic":
            return await self._send_anthropic_request(model, messages, temperature)
        elif provider == "gemini":
            return await self._send_gemini_request(model, messages, temperature)
        elif provider == "mistral":
            return await self._send_mistral_request(model, messages, temperature)
        elif provider == "deepseek":
            return await self._send_deepseek_request(model, messages, temperature)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _send_openai_request(self, 
                                  model: str, 
                                  messages: List[Dict[str, str]], 
                                  temperature: float) -> Dict[str, Any]:
        """Send request to OpenAI."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is not installed")
        
        response = await self.clients['openai'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "provider": "openai",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def _send_anthropic_request(self, 
                                     model: str, 
                                     messages: List[Dict[str, str]], 
                                     temperature: float) -> Dict[str, Any]:
        """Send request to Anthropic."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package is not installed")
        
        # Convert messages to Anthropic format
        system_message = ""
        conversation = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                conversation.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                conversation.append({"role": "assistant", "content": msg["content"]})
        
        response = await self.clients['anthropic'].messages.create(
            model=model,
            system=system_message if system_message else None,
            messages=conversation,
            temperature=temperature
        )
        
        return {
            "content": response.content[0].text,
            "model": response.model,
            "provider": "anthropic",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def _send_gemini_request(self,
                                  model: str,
                                  messages: List[Dict[str, str]],
                                  temperature: float) -> Dict[str, Any]:
        """Send request to Gemini."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI package is not installed")
        
        # Convert messages to Gemini format
        gemini_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
        
        # Create model instance
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 0,
        }
        
        gemini_model = self.clients['gemini'].GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )
        
        # Add system instruction if provided
        if system_message:
            gemini_model = gemini_model.with_system_instruction(system_message)
        
        # Create chat session and get response
        chat = gemini_model.start_chat(history=gemini_messages)
        response = await chat.send_message_async(gemini_messages[-1]["parts"][0]["text"])
        
        return {
            "content": response.text,
            "model": model,
            "provider": "gemini",
            "usage": {
                # Gemini might not provide token usage in the same way
                "total_tokens": getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            }
        }
    
    async def _send_mistral_request(self,
                                   model: str,
                                   messages: List[Dict[str, str]],
                                   temperature: float) -> Dict[str, Any]:
        """Send request to Mistral."""
        if not MISTRAL_AVAILABLE:
            raise ImportError("Mistral AI package is not installed")
        
        # Mistral uses a similar format to OpenAI
        # Convert only if needed
        mistral_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant", "system"]:
                mistral_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Create async response - we need to handle the synchronous Mistral client
        response = await asyncio.to_thread(
            self.clients['mistral'].chat,
            model=model,
            messages=mistral_messages,
            temperature=temperature
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": model,
            "provider": "mistral",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def _send_deepseek_request(self,
                                    model: str,
                                    messages: List[Dict[str, str]],
                                    temperature: float) -> Dict[str, Any]:
        """Send request to DeepSeek."""
        if not DEEPSEEK_AVAILABLE:
            raise ImportError("DeepSeek package is not installed")
        
        # Convert messages to DeepSeek format if needed
        deepseek_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant", "system"]:
                deepseek_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Create async response - using to_thread if DeepSeek client is synchronous
        response = await asyncio.to_thread(
            self.clients['deepseek'].chat.completions.create,
            model=model,
            messages=deepseek_messages,
            temperature=temperature
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": model,
            "provider": "deepseek",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    async def extract_agent_action(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract agent actions.
        
        Args:
            content: Response content from LLM
            
        Returns:
            Dictionary with agent type and action details
        """
        # Simple heuristic detection
        content_lower = content.lower()
        
        # Check for code-related content
        if ("```" in content and any(lang in content_lower for lang in ["python", "javascript", "java", "c++"])) or \
           any(keyword in content_lower for keyword in ["code", "function", "class", "programming"]):
            return {
                "agent_type": "coder",
                "action": "analyze_code",
                "content": content
            }
        
        # Check for system operation content
        elif any(keyword in content_lower for keyword in ["file", "directory", "folder", "execute", "command", "terminal"]):
            return {
                "agent_type": "computer",
                "action": "process_command",
                "content": content
            }
        
        # Default to assistant
        else:
            return {
                "agent_type": "assistant",
                "action": "provide_information",
                "content": content
            }
