"""
State Manager for Real-Time Podcast AI Assistant.
Centralized state management for transcript buffer, topic tree, and fact queue.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional
import networkx as nx

from config import settings


@dataclass
class TranscriptSegment:
    """Represents a single transcript segment from Deepgram."""

    text: str
    is_final: bool
    timestamp: datetime = field(default_factory=datetime.now)
    speaker: Optional[str] = None
    confidence: float = 1.0

    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.text}"


@dataclass
class FactCheckResult:
    """Result of a fact-checking operation."""

    claim: str
    verdict: str  # SUPPORTED, CONTRADICTED, UNCERTAIN
    confidence: float
    explanation: str
    key_facts: List[str]
    evidence_sources: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        status_emoji = {
            "SUPPORTED": "✓",
            "CONTRADICTED": "✗",
            "UNCERTAIN": "?",
        }
        emoji = status_emoji.get(self.verdict, "?")
        return f"{emoji} {self.claim} ({self.verdict}, {self.confidence:.0%})"


@dataclass
class TopicNode:
    """Represents a topic in the conversation timeline."""

    topic: str
    keywords: List[str]
    timestamp: datetime
    sentence_count: int = 0
    weight: float = 1.0  # Importance weight

    def __str__(self) -> str:
        return f"{self.topic} (n={self.sentence_count}, w={self.weight:.2f})"


class StateManager:
    """
    Central state manager for the application.
    Manages transcript buffer, topic tree, and fact-checking queue.
    """

    def __init__(self):
        # Transcript Buffer - stores recent transcript segments
        self.transcript_buffer: Deque[TranscriptSegment] = deque(
            maxlen=settings.max_buffer_size
        )

        # Finalized Sentences - accumulated until topic update threshold
        self.finalized_sentences: List[str] = []
        self.finalized_count: int = 0

        # Topic Tree - NetworkX directed graph for conversation flow
        self.topic_tree: nx.DiGraph = nx.DiGraph()
        self.current_topic_id: Optional[str] = None
        self.topic_counter: int = 0

        # Fact Check Queue - async queue for fact-checking tasks
        self.fact_queue: asyncio.Queue = asyncio.Queue()

        # Fact Check Results - stored results for retrieval
        self.fact_results: List[FactCheckResult] = []

        # Rate Limiting for Fact Checks
        self.last_fact_check_time: Optional[datetime] = None

        # Statistics
        self.stats = {
            "total_segments": 0,
            "finalized_segments": 0,
            "fact_checks_performed": 0,
            "topics_identified": 0,
        }

    def add_transcript_segment(self, segment: TranscriptSegment) -> None:
        """
        Add a new transcript segment to the buffer.

        Args:
            segment: TranscriptSegment to add
        """
        self.transcript_buffer.append(segment)
        self.stats["total_segments"] += 1

        if segment.is_final:
            self.finalized_sentences.append(segment.text)
            self.finalized_count += 1
            self.stats["finalized_segments"] += 1

    def get_recent_context(self, num_segments: int = 10) -> str:
        """
        Get recent context as a single string.

        Args:
            num_segments: Number of recent segments to include

        Returns:
            Combined text of recent segments
        """
        recent = list(self.transcript_buffer)[-num_segments:]
        return " ".join(seg.text for seg in recent)

    def should_update_topics(self) -> bool:
        """
        Check if we should update the topic tree.

        Returns:
            True if threshold reached
        """
        return self.finalized_count >= settings.topic_update_threshold

    def consume_finalized_sentences(self) -> str:
        """
        Get all finalized sentences and reset the counter.

        Returns:
            Combined finalized sentences
        """
        text = " ".join(self.finalized_sentences)
        self.finalized_sentences.clear()
        self.finalized_count = 0
        return text

    def can_perform_fact_check(self) -> bool:
        """
        Check if enough time has passed since last fact check.

        Returns:
            True if fact check is allowed
        """
        if self.last_fact_check_time is None:
            return True

        elapsed = (datetime.now() - self.last_fact_check_time).total_seconds()
        return elapsed >= settings.fact_check_rate_limit

    def mark_fact_check_performed(self) -> None:
        """Record that a fact check was performed."""
        self.last_fact_check_time = datetime.now()
        self.stats["fact_checks_performed"] += 1

    def add_fact_result(self, result: FactCheckResult) -> None:
        """
        Store a fact-checking result.

        Args:
            result: FactCheckResult to store
        """
        self.fact_results.append(result)

    def add_topic_node(
        self, topic: str, keywords: List[str], timestamp: datetime
    ) -> str:
        """
        Add a new topic node to the topic tree.

        Args:
            topic: Topic name
            keywords: Associated keywords
            timestamp: When the topic was identified

        Returns:
            Topic ID
        """
        topic_id = f"topic_{self.topic_counter}"
        self.topic_counter += 1
        self.stats["topics_identified"] += 1

        node = TopicNode(
            topic=topic, keywords=keywords, timestamp=timestamp, sentence_count=1
        )

        self.topic_tree.add_node(topic_id, data=node)

        # Link to previous topic if exists
        if self.current_topic_id is not None:
            self.topic_tree.add_edge(self.current_topic_id, topic_id)

        self.current_topic_id = topic_id
        return topic_id

    def update_current_topic(self) -> None:
        """Increment sentence count for current topic."""
        if self.current_topic_id is not None:
            node_data = self.topic_tree.nodes[self.current_topic_id]["data"]
            node_data.sentence_count += 1

    def get_topic_timeline(self) -> List[TopicNode]:
        """
        Get chronological list of topics.

        Returns:
            List of TopicNode objects in temporal order
        """
        if self.topic_tree.number_of_nodes() == 0:
            return []

        nodes = []
        for node_id in self.topic_tree.nodes():
            node_data = self.topic_tree.nodes[node_id]["data"]
            nodes.append(node_data)

        # Sort by timestamp
        nodes.sort(key=lambda x: x.timestamp)
        return nodes

    def get_stats(self) -> Dict:
        """
        Get current statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            **self.stats,
            "buffer_size": len(self.transcript_buffer),
            "pending_sentences": self.finalized_count,
            "fact_queue_size": self.fact_queue.qsize(),
            "fact_results_count": len(self.fact_results),
            "topics_count": self.topic_tree.number_of_nodes(),
        }

    def clear(self) -> None:
        """Reset all state (useful for testing)."""
        self.transcript_buffer.clear()
        self.finalized_sentences.clear()
        self.finalized_count = 0
        self.topic_tree.clear()
        self.current_topic_id = None
        self.topic_counter = 0
        self.fact_results.clear()
        self.last_fact_check_time = None
        # Don't clear the queue as it's async
        self.stats = {
            "total_segments": 0,
            "finalized_segments": 0,
            "fact_checks_performed": 0,
            "topics_identified": 0,
        }


# Global state manager instance
state = StateManager()
