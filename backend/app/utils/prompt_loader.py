"""
Utility module for loading persona-specific prompt templates.
Caches loaded prompts in memory for performance.
"""

import os
from pathlib import Path
from typing import Dict, Optional

# In-memory cache for loaded prompts
_PROMPT_CACHE: Dict[str, str] = {}


def load_prompt(persona_type: str) -> str:
    """
    Load a persona-specific prompt template from file.
    
    Args:
        persona_type: The persona type (e.g., 'high_utilization', 'variable_income')
    
    Returns:
        The prompt template as a string
    
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        ValueError: If persona_type is invalid
    """
    # Validate persona type
    valid_personas = [
        'high_utilization',
        'variable_income',
        'subscription_heavy',
        'savings_builder',
        'wealth_builder'
    ]
    
    if persona_type not in valid_personas:
        raise ValueError(
            f"Invalid persona_type: {persona_type}. "
            f"Must be one of: {', '.join(valid_personas)}"
        )
    
    # Check cache first
    if persona_type in _PROMPT_CACHE:
        return _PROMPT_CACHE[persona_type]
    
    # Construct file path
    # Get the directory where this file is located
    current_dir = Path(__file__).parent.parent
    prompts_dir = current_dir / 'prompts'
    prompt_file = prompts_dir / f"{persona_type}.txt"
    
    # Check if file exists
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}. "
            f"Expected persona types: {', '.join(valid_personas)}"
        )
    
    # Read file contents
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
    except Exception as e:
        raise IOError(f"Error reading prompt file {prompt_file}: {str(e)}")
    
    # Cache the loaded prompt
    _PROMPT_CACHE[persona_type] = prompt_content
    
    return prompt_content


def clear_cache() -> None:
    """Clear the prompt cache. Useful for testing or reloading prompts."""
    global _PROMPT_CACHE
    _PROMPT_CACHE.clear()


def get_cached_personas() -> list[str]:
    """Get list of persona types currently cached."""
    return list(_PROMPT_CACHE.keys())

