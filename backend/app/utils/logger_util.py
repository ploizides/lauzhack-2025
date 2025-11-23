"""
JSON logging utility for debugging the Real-Time Podcast AI Assistant.
Logs transcripts, topics, and fact-checks to separate JSON files in logs/ folder.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Generate session ID based on timestamp
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

# Log file paths
TRANSCRIPT_LOG = LOGS_DIR / f"transcripts_{SESSION_ID}.json"
TOPIC_LOG = LOGS_DIR / f"topics_{SESSION_ID}.json"
FACT_LOG = LOGS_DIR / f"facts_{SESSION_ID}.json"
SESSION_LOG = LOGS_DIR / f"session_{SESSION_ID}.json"

logger = logging.getLogger(__name__)


class DebugLogger:
    """Handles JSON logging for debugging purposes."""

    def __init__(self):
        """Initialize the debug logger with session info."""
        self.session_start = datetime.now()
        self.transcripts: List[Dict[str, Any]] = []
        self.topics: List[Dict[str, Any]] = []
        self.facts: List[Dict[str, Any]] = []

        # Write session header
        self._write_session_header()
        logger.info(f"Debug logging initialized - Session: {SESSION_ID}")
        logger.info(f"Logs directory: {LOGS_DIR}")

    def _write_session_header(self):
        """Write session metadata."""
        session_info = {
            "session_id": SESSION_ID,
            "start_time": self.session_start.isoformat(),
            "logs": {
                "transcripts": str(TRANSCRIPT_LOG),
                "topics": str(TOPIC_LOG),
                "facts": str(FACT_LOG),
            }
        }
        with open(SESSION_LOG, 'w') as f:
            json.dump(session_info, f, indent=2)

    def log_transcript(self, text: str, is_final: bool, confidence: float, timestamp: datetime = None):
        """
        Log a transcript segment.

        Args:
            text: Transcribed text
            is_final: Whether this is a final transcript
            confidence: Confidence score (0-1)
            timestamp: Timestamp of the transcript
        """
        if timestamp is None:
            timestamp = datetime.now()

        entry = {
            "timestamp": timestamp.isoformat(),
            "text": text,
            "is_final": is_final,
            "confidence": confidence,
            "session_time_seconds": (timestamp - self.session_start).total_seconds()
        }

        self.transcripts.append(entry)

        # Append to file (one line per entry for easy streaming)
        with open(TRANSCRIPT_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        logger.debug(f"Logged transcript: {'FINAL' if is_final else 'PARTIAL'} - {text[:50]}...")

    def log_topic(self, topic: str, keywords: List[str], sentence_count: int, timestamp: datetime = None):
        """
        Log a topic update.

        Args:
            topic: The detected topic
            keywords: Keywords associated with the topic
            sentence_count: Number of sentences accumulated for this topic
            timestamp: Timestamp of topic detection
        """
        if timestamp is None:
            timestamp = datetime.now()

        entry = {
            "timestamp": timestamp.isoformat(),
            "topic": topic,
            "keywords": keywords,
            "sentence_count": sentence_count,
            "session_time_seconds": (timestamp - self.session_start).total_seconds(),
            "topic_number": len(self.topics) + 1
        }

        self.topics.append(entry)

        # Append to file
        with open(TOPIC_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(f"Logged topic #{entry['topic_number']}: {topic} (keywords: {', '.join(keywords[:3])}...)")

    def log_fact_check(
        self,
        claim: str,
        verdict: str,
        confidence: float,
        explanation: str,
        key_facts: List[str],
        evidence_sources: List[str],
        timestamp: datetime = None
    ):
        """
        Log a fact-check result.

        Args:
            claim: The claim being checked
            verdict: SUPPORTED, CONTRADICTED, or UNCERTAIN
            confidence: Confidence score (0-1)
            explanation: Explanation of the verdict
            key_facts: Key facts found
            evidence_sources: URLs of evidence sources
            timestamp: Timestamp of fact check
        """
        if timestamp is None:
            timestamp = datetime.now()

        entry = {
            "timestamp": timestamp.isoformat(),
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation,
            "key_facts": key_facts,
            "evidence_sources": evidence_sources,
            "session_time_seconds": (timestamp - self.session_start).total_seconds(),
            "fact_number": len(self.facts) + 1
        }

        self.facts.append(entry)

        # Append to file
        with open(FACT_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(f"Logged fact #{entry['fact_number']}: {verdict} - {claim[:50]}...")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.

        Returns:
            Dictionary with session statistics
        """
        session_duration = (datetime.now() - self.session_start).total_seconds()

        return {
            "session_id": SESSION_ID,
            "duration_seconds": session_duration,
            "total_transcripts": len(self.transcripts),
            "final_transcripts": sum(1 for t in self.transcripts if t["is_final"]),
            "total_topics": len(self.topics),
            "total_facts": len(self.facts),
            "fact_verdicts": {
                "SUPPORTED": sum(1 for f in self.facts if f["verdict"] == "SUPPORTED"),
                "CONTRADICTED": sum(1 for f in self.facts if f["verdict"] == "CONTRADICTED"),
                "UNCERTAIN": sum(1 for f in self.facts if f["verdict"] == "UNCERTAIN"),
            }
        }

    def save_summary(self):
        """Save final session summary."""
        summary = self.get_summary()
        summary["end_time"] = datetime.now().isoformat()

        # Update session log with final summary
        with open(SESSION_LOG, 'r') as f:
            session_data = json.load(f)

        session_data["summary"] = summary

        with open(SESSION_LOG, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session summary saved: {summary['total_transcripts']} transcripts, "
                   f"{summary['total_topics']} topics, {summary['total_facts']} facts")


# Global debug logger instance
debug_logger = DebugLogger()
