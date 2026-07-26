"""Candidate ranking and Pareto-front helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    reward: float
    penalty: float
    instability: float

    @property
    def scalar(self) -> float:
        return self.reward - self.penalty - self.instability


def pareto_front(scores: list[CandidateScore]) -> list[CandidateScore]:
    front: list[CandidateScore] = []
    for score in scores:
        dominated = False
        for other in scores:
            if other is score:
                continue
            if (
                other.reward >= score.reward
                and other.penalty <= score.penalty
                and other.instability <= score.instability
                and (
                    other.reward > score.reward
                    or other.penalty < score.penalty
                    or other.instability < score.instability
                )
            ):
                dominated = True
                break
        if not dominated:
            front.append(score)
    return front
