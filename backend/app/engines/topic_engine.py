"""
Topic Engine for Real-Time Podcast AI Assistant.
Handles semantic drift detection and topic tree updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from groq import Groq
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS  # Fallback for older package name

from backend.app.core.config import settings, TOPIC_EXTRACTION_PROMPT, TOPIC_CONFIG
from backend.app.core.state_manager import state

logger = logging.getLogger(__name__)


class TopicEngine:
    """
    Manages topic detection and semantic drift tracking.
    Updates the topic tree as the conversation evolves.
    """

    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.embedding_cache: Dict[str, np.ndarray] = {}
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

    async def extract_topic(self, text: str) -> Optional[Tuple[str, List[str]]]:
        """
        Extract the main topic and keywords from text using LLM.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (topic, keywords) or None if extraction fails
        """
        try:
            prompt = TOPIC_EXTRACTION_PROMPT.format(text=text)

            # Run in executor since Groq client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a topic extraction assistant. Always respond in valid JSON format.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=200,
                ),
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            # Handle markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)

            topic = result.get("topic", "").strip()
            keywords = result.get("keywords", [])

            if not topic:
                logger.warning("Topic extraction returned empty topic")
                return None

            return topic, keywords

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content}")
            return None
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return None

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text.

        TODO: Replace with actual embedding model (e.g., sentence-transformers)
        For now, using a mock implementation with simple hashing.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        # MOCK IMPLEMENTATION - Replace with actual embeddings
        # For hackathon MVP, using simple word-based features
        words = text.lower().split()
        vocab_size = 1000
        embedding_dim = 128

        # Simple bag-of-words style embedding
        embedding = np.zeros(embedding_dim)
        for word in words:
            # Use hash to get consistent indices
            idx = hash(word) % embedding_dim
            embedding[idx] += 1

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Cache it
        self.embedding_cache[text] = embedding

        return embedding

        # TODO: Real implementation example:
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # embedding = model.encode(text)
        # return np.array(embedding)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2)

        # Ensure in [0, 1] range
        return float(max(0.0, min(1.0, similarity)))

    def find_existing_topic(self, new_topic: str) -> Optional[str]:
        """
        Check if this topic already exists in the tree.

        If a highly similar topic exists, return its ID instead of creating a duplicate.

        Args:
            new_topic: The new topic text to compare

        Returns:
            topic_id if match found, None otherwise
        """
        if len(state.topic_tree.nodes) == 0:
            return None

        # Check all existing topics
        for topic_id in state.topic_tree.nodes:
            node_data = state.topic_tree.nodes[topic_id]["data"]
            topic_text = node_data.topic

            similarity = self.compute_similarity(topic_text, new_topic)

            # If very similar, consider it the same topic
            if similarity >= TOPIC_CONFIG["similarity_threshold"]:
                logger.info(f"Found existing topic: '{topic_text}' (similarity: {similarity:.2f})")
                return topic_id

        return None

    def detect_topic_shift(self, new_topic: str) -> Tuple[bool, Optional[str]]:
        """
        Check if this is a new topic or returning to an existing one.

        Args:
            new_topic: Newly extracted topic

        Returns:
            Tuple of (is_new_topic, existing_topic_id)
            - is_new_topic: True if we need to create a new topic node
            - existing_topic_id: ID of existing topic if found, None otherwise
        """
        # Check if this topic already exists
        existing_id = self.find_existing_topic(new_topic)

        if existing_id:
            # Found existing topic - reuse it
            return (False, existing_id)
        else:
            # New topic - will be created
            return (True, None)

    async def update_topic_tree(self, text: str) -> Optional[str]:
        """
        Update the topic tree based on new text.

        This is called periodically (every N finalized sentences) from the Fast Loop.

        Args:
            text: Accumulated finalized text to analyze

        Returns:
            Topic ID if topic was added/updated, None otherwise
        """
        try:
            # Extract topic and keywords
            result = await self.extract_topic(text)
            if result is None:
                logger.warning("Failed to extract topic, skipping update")
                return None

            topic, keywords = result

            # Check if this topic already exists
            is_new_topic, existing_topic_id = self.detect_topic_shift(topic)

            if is_new_topic:
                # Create new topic node (without image for now)
                topic_id = state.add_topic_node(
                    topic=topic,
                    keywords=keywords,
                    timestamp=datetime.now()
                )
                logger.info(f"New topic: {topic} (id={topic_id})")

                # Search for image asynchronously (don't block)
                asyncio.create_task(self._search_and_record_image(topic_id, topic, keywords))

                return topic_id
            else:
                # Returning to existing topic - switch to it
                state.switch_to_topic(existing_topic_id)
                logger.info(f"Returning to existing topic: {topic} (id={existing_topic_id})")
                return existing_topic_id

        except Exception as e:
            logger.error(f"Failed to update topic tree: {e}")
            return None

    async def _search_and_record_image(self, topic_id: str, topic: str, keywords: List[str]) -> None:
        """
        Search for topic image and record it (called as background task).

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

    def get_topic_summary(self) -> Dict:
        """
        Get a summary of the current topic tree.

        Returns:
            Dictionary with topic timeline and statistics
        """
        timeline = state.get_topic_timeline()

        return {
            "current_topic": (
                state.topic_tree.nodes[state.current_topic_id]["data"].topic
                if state.current_topic_id
                else None
            ),
            "total_topics": len(timeline),
            "timeline": [
                {
                    "topic": node.topic,
                    "keywords": node.keywords,
                    "timestamp": node.timestamp.isoformat(),
                    "sentence_count": node.sentence_count,
                    "weight": node.weight,
                }
                for node in timeline
            ],
        }


# Global topic engine instance
topic_engine = TopicEngine()
