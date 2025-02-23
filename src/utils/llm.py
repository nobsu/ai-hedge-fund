"""Helper functions for LLM"""

import json
from typing import TypeVar, Type, Optional, Any, Callable
from pydantic import BaseModel, ValidationError
from utils.progress import progress
from colorama import Fore, Style
from utils.logger import log_llm_call, log_error

T = TypeVar('T', bound=BaseModel)

def call_llm(
    prompt: Any,
    model_name: str,
    model_provider: str,
    pydantic_model: Type[T],
    agent_name: Optional[str] = None,
    max_retries: int = 3,
    default_factory: Callable[[], T] = None
) -> T:
    """
    Makes an LLM call with retry logic, handling both Deepseek and non-Deepseek models.
    
    Args:
        prompt: The prompt to send to the LLM
        model_name: Name of the model to use
        model_provider: Provider of the model
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates
        max_retries: Maximum number of retries (default: 3)
        default_factory: Optional factory function to create default response on failure
        
    Returns:
        An instance of the specified Pydantic model
    """
    from llm.models import get_model, get_model_info
    
    try:
        model = get_model(model_name, model_provider)
        model_info = get_model_info(model_name)
        
        if not model:
            raise ValueError(f"Failed to initialize model {model_name}")
            
        # 调用LLM
        response = model.invoke(prompt)
        
        # 记录到日志文件
        log_llm_call(
            model_name=model_name,
            model_provider=model_provider,
            agent_name=agent_name or "Unknown Agent",
            prompt=prompt.to_string(),
            response=response.content
        )
        
        # 只在终端显示简短信息
        print(f"\n{Fore.CYAN}[{agent_name}] Called {model_provider}-{model_name} model{Style.RESET_ALL}")
        
        try:
            # 处理 Deepseek 模型的响应
            if model_info and model_info.is_deepseek():
                result = extract_json_from_deepseek_response(response.content)
                if not result:
                    raise json.JSONDecodeError("Failed to extract JSON from Deepseek response", response.content, 0)
            else:
                # 处理其他模型的响应
                result = json.loads(response.content)
            
            return pydantic_model(**result)
            
        except (json.JSONDecodeError, ValidationError) as e:
            log_error(f"Error parsing model response: {e}")
            if default_factory:
                return default_factory()
            raise
            
    except Exception as e:
        log_error(f"Error calling {model_provider} model: {e}")
        if default_factory:
            return default_factory()
        raise

def create_default_response(model_class: Type[T]) -> T:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}
        else:
            # For other types (like Literal), try to use the first allowed value
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None
    
    return model_class(**default_values)

def extract_json_from_deepseek_response(content: str) -> Optional[dict]:
    """Extracts JSON from Deepseek's markdown-formatted response."""
    try:
        # 尝试直接解析整个响应
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 markdown 代码块中提取
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7:]
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
        
        # 尝试查找第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            json_text = content[start:end + 1]
            return json.loads(json_text)
            
    except Exception as e:
        log_error(f"Error extracting JSON from Deepseek response: {e}")
    return None
