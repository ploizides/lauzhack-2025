"""
Image Engine for Real-Time Podcast AI Assistant.
Handles image search and smart image subject extraction.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from groq import Groq
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS  # Fallback for older package name

from backend.app.core.config import settings, IMAGE_SUBJECT_EXTRACTION_PROMPT
from backend.app.core.state_manager import state

logger = logging.getLogger(__name__)


class ImageEngine:
    """
    Manages image search and smart subject extraction.
    Supports both topic-based and context-based image updates.
    """

    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.search_client = DDGS()

    async def search_topic_image(self, topic: str, keywords: List[str]) -> Optional[str]:
        """
        Search for a relevant image for the topic.

        Args:
            topic: The topic name
            keywords: Topic keywords to enhance search

        Returns:
            URL of the most relevant image, or None if search fails
        """
        try:
            # Create search query from topic and keywords
            search_terms = [topic] + keywords[:3]  # Use top 3 keywords
            query = " ".join(search_terms)

            logger.info(f"Searching images for: {query}")
            print(f"🖼️  Searching image for: {query}")

            # Run image search in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(
                    self.search_client.images(
                        query,  # Changed from keywords= to positional argument
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=3,
                    )
                ),
            )

            print(f"🔍 Image search returned {len(results) if results else 0} results")

            if results and len(results) > 0:
                # Return the first (most relevant) image URL
                image_url = results[0].get("image")
                print(f"   First result: {results[0]}")
                if image_url:
                    print(f"✅ Found image: {image_url[:80]}...")
                    return image_url
                else:
                    print(f"❌ No 'image' key in result")

            print(f"⚠️  No images found for: {query}")
            logger.warning(f"No images found for: {query}")
            return None

        except Exception as e:
            print(f"❌ Image search error: {e}")
            logger.error(f"Image search failed: {e}")
            return None

    async def extract_image_subject_from_context(
        self, current_topic: Optional[str], conversation_text: str
    ) -> Optional[Dict]:
        """
        Extract the most visually relevant subject from conversation context.
        Prioritizes historical figures, events, places over generic topics.

        Args:
            current_topic: Current conversation topic (if available)
            conversation_text: Recent sentences for context

        Returns:
            Dict with image_subject, subject_type, keywords, or None if no good subject
        """
        try:
            prompt = IMAGE_SUBJECT_EXTRACTION_PROMPT.format(
                current_topic=current_topic or "No current topic",
                conversation_text=conversation_text
            )

            print(f"🎯 Extracting image subject from context...")
            print(f"   Topic: {current_topic}")
            print(f"   Context: {conversation_text[:100]}...")

            # Run LLM in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an image subject extraction assistant. Always respond in valid JSON format.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
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
            
            if result.get("image_subject"):
                print(f"✅ Extracted subject: {result['image_subject']} ({result.get('subject_type', 'unknown')})")
                print(f"   Reasoning: {result.get('reasoning', 'N/A')}")
            else:
                print(f"⚠️  No specific visual subject identified")

            return result

        except Exception as e:
            logger.error(f"Image subject extraction failed: {e}")
            print(f"❌ Subject extraction error: {e}")
            return None

    async def search_and_update_smart_image(self) -> None:
        """
        Smart image update (decoupled from topics).
        Extracts most relevant visual subject and searches for image.
        """
        try:
            # Get context from state
            current_topic, conversation_text = state.get_image_context()
            
            if not conversation_text:
                print("⚠️  No conversation context for image update")
                return

            # Extract the best visual subject
            subject_data = await self.extract_image_subject_from_context(
                current_topic, conversation_text
            )

            if not subject_data or not subject_data.get("image_subject"):
                print("⚠️  No visual subject to search for")
                state.consume_image_update()
                return

            # Search for image using the extracted subject
            image_subject = subject_data["image_subject"]
            keywords = subject_data.get("search_keywords", [])
            
            image_url = await self.search_topic_image(image_subject, keywords)

            # Record the image with metadata
            if image_url:
                # Use current topic_id if available, otherwise create a generic one
                topic_id = state.current_topic_id or f"image_{datetime.now().timestamp()}"
                state.add_topic_image(topic_id, image_subject, image_url)
                print(f"✅ Smart image recorded: {image_subject}")
            else:
                print(f"⚠️  No image found for: {image_subject}")

            # Reset counter
            state.consume_image_update()

        except Exception as e:
            logger.error(f"Smart image update failed: {e}")
            print(f"❌ Smart image update error: {e}")
            state.consume_image_update()

    async def search_and_record_image(self, topic_id: str, topic: str, keywords: List[str]) -> None:
        """
        Search for topic image and record it (topic-based image update).

        Args:
            topic_id: Topic ID
            topic: Topic name
            keywords: Topic keywords
        """
        try:
            print(f"🔄 Starting image search task for: {topic}")
            image_url = await self.search_topic_image(topic, keywords)
            print(f"📝 Recording image for {topic_id}: {image_url}")
            state.add_topic_image(topic_id, topic, image_url)
            print(f"✅ Image recorded successfully")
        except Exception as e:
            print(f"❌ Failed to search/record image: {e}")
            logger.error(f"Failed to search/record image: {e}")
            state.add_topic_image(topic_id, topic, None)


# Global instance
image_engine = ImageEngine()
