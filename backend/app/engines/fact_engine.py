"""
Fact Engine for Real-Time Podcast AI Assistant.
Implements the 3-step fact-checking pipeline: Detect -> Search -> Verify.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS  # Fallback for older package name
from together import Together

from backend.app.core.config import (
    settings,
    CLAIM_DETECTION_PROMPT,
    CLAIM_VERIFICATION_PROMPT,
    SEARCH_CONFIG,
)
from backend.app.core.state_manager import state, FactCheckResult
from backend.app.utils.logger_util import debug_logger

logger = logging.getLogger(__name__)


class FactEngine:
    """
    Manages the fact-checking pipeline.
    Runs asynchronously in the Slow Loop without blocking the main thread.
    """

    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.search_client = DDGS()

    async def detect_claim(self, statement: str) -> Optional[Dict]:
        """
        Step 1: Detect if the statement contains a factual claim.

        Args:
            statement: Text to analyze

        Returns:
            Dictionary with claim detection result or None if detection fails
        """
        try:
            prompt = CLAIM_DETECTION_PROMPT.format(statement=statement)

            # Run LLM call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.together_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a claim detection assistant. Always respond in valid JSON format.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=300,
                ),
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)

            logger.info(
                f"Claim detection: {result.get('is_claim', False)} - {statement[:50]}..."
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse claim detection response: {e}")
            logger.debug(f"Response content: {content}")
            return None
        except Exception as e:
            logger.error(f"Claim detection failed: {e}")
            return None

    async def search_evidence(
        self, claim: str, max_results: int = None
    ) -> List[Dict[str, str]]:
        """
        Step 2: Search for evidence using DuckDuckGo.

        Args:
            claim: The claim to search for
            max_results: Maximum number of results (defaults to SEARCH_CONFIG)

        Returns:
            List of evidence dictionaries with 'title', 'body', 'href' keys
        """
        if max_results is None:
            max_results = SEARCH_CONFIG["max_results"]

        try:
            logger.info(f"Searching evidence for: {claim[:100]}...")

            # Run search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(
                    self.search_client.text(
                        claim,
                        region=SEARCH_CONFIG["region"],
                        safesearch=SEARCH_CONFIG["safesearch"],
                        max_results=max_results,
                    )
                ),
            )

            # Extract relevant fields and include source links
            evidence = []
            for result in results:
                evidence.append(
                    {
                        "title": result.get("title", ""),
                        "body": result.get("body", ""),
                        "href": result.get("href", ""),  # Source link
                    }
                )

            logger.info(f"Found {len(evidence)} evidence sources")
            return evidence

        except Exception as e:
            logger.error(f"Evidence search failed: {e}")
            return []

    async def verify_claim(self, claim: str, evidence: List[Dict[str, str]]) -> Optional[Dict]:
        """
        Step 3: Verify the claim against the evidence.

        Args:
            claim: The claim to verify
            evidence: List of evidence dictionaries from search

        Returns:
            Verification result dictionary or None if verification fails
        """
        try:
            # Format evidence for the prompt
            evidence_text = ""
            source_links = []

            for i, item in enumerate(evidence, 1):
                evidence_text += f"\n[Source {i}] {item['title']}\n"
                evidence_text += f"{item['body']}\n"
                evidence_text += f"URL: {item['href']}\n"
                source_links.append(item["href"])

            if not evidence_text.strip():
                logger.warning("No evidence available for verification")
                return {
                    "verdict": "UNCERTAIN",
                    "confidence": 0.0,
                    "explanation": "No evidence found to verify this claim",
                    "key_facts": [],
                }

            prompt = CLAIM_VERIFICATION_PROMPT.format(
                claim=claim, evidence=evidence_text
            )

            # Run LLM call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.together_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a fact-checking assistant. Always respond in valid JSON format.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=500,
                ),
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            result["source_links"] = source_links  # Add source links to result

            logger.info(f"Verification: {result.get('verdict')} ({result.get('confidence', 0):.0%})")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse verification response: {e}")
            logger.debug(f"Response content: {content}")
            return None
        except Exception as e:
            logger.error(f"Claim verification failed: {e}")
            return None

    async def check_fact(self, statement: str) -> Optional[FactCheckResult]:
        """
        Execute the full 3-step fact-checking pipeline.

        Pipeline:
        1. Detect if statement contains a claim
        2. Search for evidence if claim detected
        3. Verify claim against evidence

        Args:
            statement: Statement to fact-check

        Returns:
            FactCheckResult or None if no claim detected
        """
        try:
            # Step 1: Detect Claim
            detection = await self.detect_claim(statement)
            if not detection or not detection.get("is_claim", False):
                logger.info(f"No factual claim detected in: {statement[:50]}...")
                return None

            claim_text = detection.get("claim_text", statement)

            # Step 2: Search for Evidence
            evidence = await self.search_evidence(claim_text)
            if not evidence:
                logger.warning(f"No evidence found for claim: {claim_text[:50]}...")
                # Still return a result, but mark as uncertain
                return FactCheckResult(
                    claim=claim_text,
                    verdict="UNCERTAIN",
                    confidence=0.0,
                    explanation="No evidence found to verify this claim",
                    key_facts=[],
                    evidence_sources=[],
                    timestamp=datetime.now(),
                )

            # Step 3: Verify Claim
            verification = await self.verify_claim(claim_text, evidence)
            if not verification:
                logger.error("Verification step failed")
                return None

            # Create result object with source links
            result = FactCheckResult(
                claim=claim_text,
                verdict=verification.get("verdict", "UNCERTAIN"),
                confidence=float(verification.get("confidence", 0.0)),
                explanation=verification.get("explanation", ""),
                key_facts=verification.get("key_facts", []),
                evidence_sources=verification.get("source_links", []),
                timestamp=datetime.now(),
            )

            logger.info(f"Fact check complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Fact checking pipeline failed: {e}")
            return None

    async def process_fact_queue(self) -> None:
        """
        Background worker that processes the fact-checking queue.

        This runs continuously and processes statements from the queue
        with rate limiting to avoid overwhelming search APIs.
        """
        logger.info("Fact queue processor started")

        while True:
            try:
                # Get next statement from queue
                statement = await state.fact_queue.get()

                # Check rate limit
                if not state.can_perform_fact_check():
                    logger.info(
                        f"Rate limit active, waiting {settings.fact_check_rate_limit}s..."
                    )
                    await asyncio.sleep(settings.fact_check_rate_limit)

                # Perform fact check
                logger.info(f"Processing fact check: {statement[:100]}...")
                result = await self.check_fact(statement)

                # Store result if claim was detected
                if result:
                    state.add_fact_result(result)
                    state.mark_fact_check_performed()
                    logger.info(f"Fact check stored: {result.verdict}")

                    # Log to JSON file
                    debug_logger.log_fact_check(
                        claim=result.claim,
                        verdict=result.verdict,
                        confidence=result.confidence,
                        explanation=result.explanation,
                        key_facts=result.key_facts,
                        evidence_sources=result.evidence_sources,
                        timestamp=result.timestamp
                    )

                # Mark task as done
                state.fact_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Fact queue processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in fact queue processor: {e}")
                # Continue processing despite errors
                await asyncio.sleep(1)


# Global fact engine instance
fact_engine = FactEngine()
