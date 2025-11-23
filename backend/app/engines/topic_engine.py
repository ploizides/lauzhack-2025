"""
Topic Engine for Real-Time Podcast AI Assistant.
Handles semantic drift detection and topic tree updates.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from together import Together

from backend.app.core.config import settings, TOPIC_EXTRACTION_PROMPT, TOPIC_CONFIG
from backend.app.core.state_manager import state

logger = logging.getLogger(__name__)


class TopicEngine:
    """
    Manages topic detection and semantic drift tracking.
    Updates the topic tree as the conversation evolves.
    """

    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.embedding_cache: Dict[str, np.ndarray] = {}

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

            response = self.client.chat.completions.create(
                model=settings.together_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a topic extraction assistant. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
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

    def detect_topic_shift(self, new_topic: str) -> bool:
        """
        Detect if there's a significant topic shift.

        Args:
            new_topic: Newly extracted topic

        Returns:
            True if this represents a new topic (shift detected)
        """
        # If no current topic, this is definitely new
        if state.current_topic_id is None:
            return True

        # Get current topic text
        current_node = state.topic_tree.nodes[state.current_topic_id]["data"]
        current_topic_text = current_node.topic

        # Compute similarity
        similarity = self.compute_similarity(current_topic_text, new_topic)

        logger.info(
            f"Topic similarity: {similarity:.2f} "
            f"(current: '{current_topic_text}', new: '{new_topic}')"
        )

        # If similarity is below threshold, it's a new topic
        return similarity < TOPIC_CONFIG["similarity_threshold"]

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

            # Check if this is a new topic (semantic drift)
            if self.detect_topic_shift(topic):
                # Create new topic node
                topic_id = state.add_topic_node(
                    topic=topic, keywords=keywords, timestamp=datetime.now()
                )
                logger.info(f"New topic detected: {topic} (id={topic_id})")
                return topic_id
            else:
                # Update existing topic
                state.update_current_topic()
                logger.info(f"Continuing current topic: {topic}")
                return state.current_topic_id

        except Exception as e:
            logger.error(f"Failed to update topic tree: {e}")
            return None

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
