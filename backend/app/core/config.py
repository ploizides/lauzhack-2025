"""
Configuration module for Real-Time Podcast AI Assistant.
Handles environment variables, API keys, and LLM prompts.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    deepgram_api_key: str
    together_api_key: str
    huggingface_api_key: Optional[str] = None

    # Configuration Parameters
    fact_check_rate_limit: int = 10  # seconds between fact checks
    topic_update_threshold: int = 5  # finalized sentences before topic update

    # Model Configuration
    together_model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"

    # Transcript Buffer Configuration
    max_buffer_size: int = 1000  # Increased to hold more segments

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()


# ============================================================================
# LLM PROMPTS
# ============================================================================

CLAIM_DETECTION_PROMPT = """You are a fact-checking assistant analyzing conversation transcripts.

Your task: Determine if the following statement contains a FACTUAL CLAIM that can be verified.

Statement: "{statement}"

A factual claim is:
- A statement about objective reality (dates, numbers, events, scientific facts)
- Something that can be verified as true or false
- NOT an opinion, feeling, or subjective statement

Respond in JSON format:
{{
    "is_claim": true/false,
    "claim_text": "extracted claim if any",
    "reason": "brief explanation"
}}

Examples:
- "The Eiffel Tower is 324 meters tall" → is_claim: true
- "I think Paris is beautiful" → is_claim: false
- "Studies show coffee reduces heart disease risk" → is_claim: true
- "We should meet tomorrow" → is_claim: false
"""


CLAIM_VERIFICATION_PROMPT = """You are a fact-checking assistant verifying claims against evidence.

CLAIM: "{claim}"

EVIDENCE FROM WEB SEARCH:
{evidence}

Your task: Determine if the claim is supported, contradicted, or uncertain based on the evidence.

Respond in JSON format:
{{
    "verdict": "SUPPORTED" | "CONTRADICTED" | "UNCERTAIN",
    "confidence": 0.0-1.0,
    "explanation": "brief explanation citing specific evidence",
    "key_facts": ["fact1", "fact2"]
}}

Guidelines:
- SUPPORTED: Evidence clearly confirms the claim
- CONTRADICTED: Evidence clearly refutes the claim
- UNCERTAIN: Insufficient or conflicting evidence
- Be conservative: prefer UNCERTAIN over hasty conclusions
- Cite specific snippets from evidence in explanation
"""


TOPIC_EXTRACTION_PROMPT = """You are analyzing a conversation transcript to identify the main topic.

Text: "{text}"

Extract the primary topic or subject being discussed. Be concise (1-5 words).

Respond in JSON format:
{{
    "topic": "main topic",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}

Examples:
- "Let's talk about climate change effects" → topic: "Climate Change"
- "The latest AI models are impressive" → topic: "AI Models"
"""


# ============================================================================
# SEARCH CONFIGURATION
# ============================================================================

SEARCH_CONFIG = {
    "max_results": 3,  # Number of search results to retrieve
    "region": "wt-wt",  # Worldwide search
    "safesearch": "moderate",
    "timeout": 10,  # seconds
}


# ============================================================================
# TOPIC TREE CONFIGURATION
# ============================================================================

TOPIC_CONFIG = {
    "similarity_threshold": 0.7,  # Threshold for creating new topic node
    "max_depth": 5,  # Maximum depth of topic tree
    "decay_factor": 0.9,  # Weight decay for older topics
}
