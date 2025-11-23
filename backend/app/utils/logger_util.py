"""
JSON logging utility for debugging the Real-Time Podcast AI Assistant.
Logs transcripts, topics, and fact-checks to separate JSON files in logs/ folder.
Each session gets its own subdirectory.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class DebugLogger:
    """Handles JSON logging for debugging purposes."""

    def __init__(self, base_logs_dir: Optional[Path] = None):
        """
        Initialize the debug logger with session info.
        
        Args:
            base_logs_dir: Base directory for logs. If None, uses default location.
        """
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        self.transcripts: List[Dict[str, Any]] = []
        self.topics: List[Dict[str, Any]] = []
        self.facts: List[Dict[str, Any]] = []

        # Create base logs directory if not provided
        if base_logs_dir is None:
            base_logs_dir = Path(__file__).parent / "logs"
        
        # Create session-specific directory
        self.session_dir = base_logs_dir / f"session_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Define log file paths within session directory
        self.transcript_log = self.session_dir / "transcripts.json"
        self.topic_log = self.session_dir / "topics.json"
        self.fact_log = self.session_dir / "facts.json"
        self.session_log = self.session_dir / "session.json"

        # Write session header
        self._write_session_header()
        logger.info(f"Debug logging initialized - Session: {self.session_id}")
        logger.info(f"Session directory: {self.session_dir}")

    def _write_session_header(self):
        """Write session metadata."""
        session_info = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "session_directory": str(self.session_dir),
            "logs": {
                "transcripts": str(self.transcript_log),
                "topics": str(self.topic_log),
                "facts": str(self.fact_log),
            }
        }
        with open(self.session_log, 'w') as f:
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
        with open(self.transcript_log, 'a') as f:
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
        with open(self.topic_log, 'a') as f:
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
        with open(self.fact_log, 'a') as f:
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
            "session_id": self.session_id,
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
        with open(self.session_log, 'r') as f:
            session_data = json.load(f)

        session_data["summary"] = summary

        with open(self.session_log, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session summary saved: {summary['total_transcripts']} transcripts, "
                   f"{summary['total_topics']} topics, {summary['total_facts']} facts")
