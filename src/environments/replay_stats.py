"""
Statistics tracking for replay infrastructure.

Tracks request matching outcomes during trajectory replay to provide visibility into:
- How many requests required LLM judge
- How many failed to match
- Distribution of LLM disambiguation results
- Percentage that matched deterministically
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MatchOutcome(str, Enum):
    """Outcome types for request matching."""

    IGNORED = "ignored"  # Request was in ignore list
    EXACT_MATCH_SINGLE = "exact_match_single"  # Exact URL match, single candidate
    EXACT_MATCH_MULTI_CACHE = "exact_match_multi_cache"  # Multiple exact matches, resolved via cache
    EXACT_MATCH_MULTI_LM = "exact_match_multi_lm"  # Multiple exact matches, required LM
    CHAR_MATCH_PERFECT = "char_match_perfect"  # Character-based perfect match
    CHAR_MATCH_SINGLE = "char_match_single"  # Character-based single candidate
    CHAR_MATCH_MULTI_CACHE = "char_match_multi_cache"  # Multiple char matches, resolved via cache
    CHAR_MATCH_MULTI_LM = "char_match_multi_lm"  # Multiple char matches, required LM
    PLAYWRIGHT_HAR_MATCH = "playwright_har_match"  # Handled by Playwright's route_from_har (deterministic)
    NO_MATCH_STATIC = "no_match_static"  # Static asset with no match (ignored)
    NO_MATCH_FAILED = "no_match_failed"  # No match found, request failed
    ABORTED = "aborted"  # Request was aborted (no entry selected)


@dataclass
class LMMatchResult:
    """Details of an LM disambiguation call."""

    request_url: str
    request_method: str
    num_candidates: int
    selected_index: int
    confidence: float
    reasoning: str
    match_type: str  # "exact" or "char_based"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RequestMatchRecord:
    """Record of a single request match attempt."""

    url: str
    method: str
    resource_type: str
    outcome: MatchOutcome
    num_candidates: int = 0
    selected_index: Optional[int] = None
    lm_confidence: Optional[float] = None
    char_match_score_pct: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReplayStats:
    """
    Statistics tracker for replay infrastructure.

    Tracks detailed statistics about request matching during trajectory replay,
    providing visibility into deterministic vs LM-based matching.
    """

    def __init__(self, bundle_path: Optional[Path] = None):
        self.bundle_path = bundle_path
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        # Request matching records
        self._records: List[RequestMatchRecord] = []

        # LM match details
        self._lm_matches: List[LMMatchResult] = []

        # Counters by outcome
        self._outcome_counts: Dict[MatchOutcome, int] = {
            outcome: 0 for outcome in MatchOutcome
        }

        # LM disambiguation distribution (index -> count)
        self._lm_index_distribution: Dict[int, int] = {}

        # LM confidence stats
        self._lm_confidences: List[float] = []

        # Char match score distribution
        self._char_match_scores: List[float] = []

    def record_request(
        self,
        url: str,
        method: str,
        resource_type: str,
        outcome: MatchOutcome,
        num_candidates: int = 0,
        selected_index: Optional[int] = None,
        lm_confidence: Optional[float] = None,
        char_match_score_pct: Optional[float] = None,
    ) -> None:
        """Record a request matching attempt."""
        record = RequestMatchRecord(
            url=url[:200],  # Truncate long URLs
            method=method,
            resource_type=resource_type,
            outcome=outcome,
            num_candidates=num_candidates,
            selected_index=selected_index,
            lm_confidence=lm_confidence,
            char_match_score_pct=char_match_score_pct,
        )
        self._records.append(record)
        self._outcome_counts[outcome] += 1

        if char_match_score_pct is not None:
            self._char_match_scores.append(char_match_score_pct)

    def record_lm_match(
        self,
        request_url: str,
        request_method: str,
        num_candidates: int,
        selected_index: int,
        confidence: float,
        reasoning: str,
        match_type: str,
    ) -> None:
        """Record details of an LM disambiguation call."""
        result = LMMatchResult(
            request_url=request_url[:200],
            request_method=request_method,
            num_candidates=num_candidates,
            selected_index=selected_index,
            confidence=confidence,
            reasoning=reasoning,
            match_type=match_type,
        )
        self._lm_matches.append(result)

        # Update distribution
        self._lm_index_distribution[selected_index] = (
            self._lm_index_distribution.get(selected_index, 0) + 1
        )

        # Track confidence
        self._lm_confidences.append(confidence)

    def finalize(self) -> None:
        """Mark the replay as complete and set end time."""
        self.end_time = datetime.now()

    # ===================== Summary Statistics =====================

    @property
    def total_requests(self) -> int:
        """Total number of requests processed."""
        return len(self._records)

    @property
    def total_ignored(self) -> int:
        """Total requests ignored (in ignore list or static assets)."""
        return (
            self._outcome_counts[MatchOutcome.IGNORED]
            + self._outcome_counts[MatchOutcome.NO_MATCH_STATIC]
        )

    @property
    def total_deterministic(self) -> int:
        """Total requests matched deterministically (no LM needed)."""
        deterministic_outcomes = [
            MatchOutcome.EXACT_MATCH_SINGLE,
            MatchOutcome.EXACT_MATCH_MULTI_CACHE,
            MatchOutcome.CHAR_MATCH_PERFECT,
            MatchOutcome.CHAR_MATCH_SINGLE,
            MatchOutcome.CHAR_MATCH_MULTI_CACHE,
            MatchOutcome.PLAYWRIGHT_HAR_MATCH,
        ]
        return sum(self._outcome_counts[o] for o in deterministic_outcomes)

    @property
    def total_lm_required(self) -> int:
        """Total requests that required LM disambiguation."""
        lm_outcomes = [
            MatchOutcome.EXACT_MATCH_MULTI_LM,
            MatchOutcome.CHAR_MATCH_MULTI_LM,
        ]
        return sum(self._outcome_counts[o] for o in lm_outcomes)

    @property
    def total_failed(self) -> int:
        """Total requests that failed to match."""
        return (
            self._outcome_counts[MatchOutcome.NO_MATCH_FAILED]
            + self._outcome_counts[MatchOutcome.ABORTED]
        )

    @property
    def total_successful(self) -> int:
        """Total requests that were successfully matched (not ignored/failed)."""
        return self.total_deterministic + self.total_lm_required

    @property
    def pct_deterministic(self) -> float:
        """Percentage of successful matches that were deterministic."""
        if self.total_successful == 0:
            return 0.0
        return (self.total_deterministic / self.total_successful) * 100

    @property
    def pct_lm_required(self) -> float:
        """Percentage of successful matches that required LM."""
        if self.total_successful == 0:
            return 0.0
        return (self.total_lm_required / self.total_successful) * 100

    @property
    def pct_failed(self) -> float:
        """Percentage of non-ignored requests that failed."""
        non_ignored = self.total_requests - self.total_ignored
        if non_ignored == 0:
            return 0.0
        return (self.total_failed / non_ignored) * 100

    @property
    def avg_lm_confidence(self) -> Optional[float]:
        """Average LM confidence score."""
        if not self._lm_confidences:
            return None
        return sum(self._lm_confidences) / len(self._lm_confidences)

    @property
    def lm_index_distribution(self) -> Dict[int, int]:
        """Distribution of LM-selected indices."""
        return dict(sorted(self._lm_index_distribution.items()))

    @property
    def lm_index_0_rate(self) -> float:
        """Rate at which LM selects index 0 (first candidate)."""
        total_lm = sum(self._lm_index_distribution.values())
        if total_lm == 0:
            return 0.0
        return (self._lm_index_distribution.get(0, 0) / total_lm) * 100

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary dictionary of all statistics."""
        duration = None
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "duration_seconds": duration,
            "total_requests": self.total_requests,
            "total_ignored": self.total_ignored,
            "total_successful": self.total_successful,
            "total_deterministic": self.total_deterministic,
            "total_lm_required": self.total_lm_required,
            "total_failed": self.total_failed,
            "pct_deterministic": round(self.pct_deterministic, 1),
            "pct_lm_required": round(self.pct_lm_required, 1),
            "pct_failed": round(self.pct_failed, 1),
            "lm_calls": len(self._lm_matches),
            "avg_lm_confidence": (
                round(self.avg_lm_confidence, 3) if self.avg_lm_confidence else None
            ),
            "lm_index_distribution": self.lm_index_distribution,
            "lm_index_0_rate": round(self.lm_index_0_rate, 1),
            "outcome_breakdown": {
                outcome.value: count for outcome, count in self._outcome_counts.items()
            },
        }

    def log_summary(self, log: logging.Logger = None) -> None:
        """Log a human-readable summary of the statistics."""
        log = log or logger
        self.finalize()

        summary = self.get_summary()

        log.info("")
        log.info("=" * 70)
        log.info("REPLAY STATISTICS SUMMARY")
        log.info("=" * 70)

        # Duration
        if summary["duration_seconds"]:
            log.info(f"Duration: {summary['duration_seconds']:.1f} seconds")

        log.info("")
        log.info("REQUEST COUNTS:")
        log.info(f"  Total requests intercepted: {summary['total_requests']}")
        log.info(f"  - Ignored (tracking/static): {summary['total_ignored']}")
        log.info(f"  - Successfully matched:      {summary['total_successful']}")
        log.info(f"  - Failed to match:           {summary['total_failed']}")

        log.info("")
        log.info("MATCHING METHOD BREAKDOWN:")
        log.info(
            f"  Deterministic matches: {summary['total_deterministic']} ({summary['pct_deterministic']}%)"
        )
        log.info(
            f"  LM disambiguation:     {summary['total_lm_required']} ({summary['pct_lm_required']}%)"
        )
        log.info(f"  Failed matches:        {summary['total_failed']} ({summary['pct_failed']}%)")

        if summary["lm_calls"] > 0:
            log.info("")
            log.info("LM DISAMBIGUATION DETAILS:")
            log.info(f"  Total LM calls: {summary['lm_calls']}")
            if summary["avg_lm_confidence"]:
                log.info(f"  Average confidence: {summary['avg_lm_confidence']}")
            log.info(f"  Index 0 selection rate: {summary['lm_index_0_rate']}%")
            if summary["lm_index_distribution"]:
                log.info("  Index distribution:")
                for idx, count in summary["lm_index_distribution"].items():
                    pct = (count / summary["lm_calls"]) * 100
                    log.info(f"    Index {idx}: {count} ({pct:.1f}%)")

        log.info("")
        log.info("DETAILED OUTCOME BREAKDOWN:")
        for outcome, count in summary["outcome_breakdown"].items():
            if count > 0:
                log.info(f"  {outcome}: {count}")

        log.info("=" * 70)
        log.info("")

    def save_to_file(self, output_path: Optional[Path] = None) -> Path:
        """Save detailed statistics to a JSON file."""
        if output_path is None:
            if self.bundle_path:
                logs_dir = self.bundle_path / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = logs_dir / f"replay_stats_{timestamp}.json"
            else:
                output_path = Path(f"replay_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        self.finalize()

        data = {
            "summary": self.get_summary(),
            "lm_matches": [
                {
                    "request_url": m.request_url,
                    "request_method": m.request_method,
                    "num_candidates": m.num_candidates,
                    "selected_index": m.selected_index,
                    "confidence": m.confidence,
                    "reasoning": m.reasoning,
                    "match_type": m.match_type,
                    "timestamp": m.timestamp,
                }
                for m in self._lm_matches
            ],
            "records": [
                {
                    "url": r.url,
                    "method": r.method,
                    "resource_type": r.resource_type,
                    "outcome": r.outcome.value,
                    "num_candidates": r.num_candidates,
                    "selected_index": r.selected_index,
                    "lm_confidence": r.lm_confidence,
                    "char_match_score_pct": r.char_match_score_pct,
                    "timestamp": r.timestamp,
                }
                for r in self._records
            ],
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Replay statistics saved to: {output_path}")
        return output_path
