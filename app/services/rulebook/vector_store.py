"""
In-Memory Vector Store & Semantic Retrieval Engine for Statutory Procurement Clauses
Supports semantic vector scoring, BM25-style keyword boosting, and category filtering.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from app.models.rule_schemas import PolicyClauseMatch, PolicySearchResponse, RuleClause


def tokenize(text: str) -> List[str]:
    """Extracts normalized alphanumeric word tokens."""
    return re.findall(r"\b[a-z0-9]{3,}\b", text.lower())


def compute_vector(tokens: List[str], idf_weights: Dict[str, float]) -> Dict[str, float]:
    """Computes a normalized TF-IDF vector representation."""
    tf = Counter(tokens)
    total = len(tokens) or 1
    vec = {}
    norm_sq = 0.0

    for token, count in tf.items():
        weight = (count / total) * idf_weights.get(token, 1.0)
        vec[token] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) or 1.0
    return {k: v / norm for k, v in vec.items()}


def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    """Calculates cosine similarity between two sparse vector representations."""
    intersection = set(v1.keys()) & set(v2.keys())
    return sum(v1[k] * v2[k] for k in intersection)


class PolicyVectorStore:
    """
    High-performance, zero-external-dependency Vector & Semantic Search Index
    for Indian Public Procurement Statutory Rulebooks.
    """

    def __init__(self) -> None:
        self.clauses: Dict[str, RuleClause] = {}
        self.vectors: Dict[str, Dict[str, float]] = {}
        self.doc_freq: Dict[str, int] = Counter()
        self.total_docs: int = 0
        self.idf: Dict[str, float] = {}

    def clear(self) -> None:
        self.clauses.clear()
        self.vectors.clear()
        self.doc_freq.clear()
        self.total_docs = 0
        self.idf.clear()

    def add_clause(self, clause: RuleClause) -> None:
        """Adds a single clause to the vector store and updates indices."""
        self.clauses[clause.id] = clause
        self.rebuild_index()

    def add_clauses(self, clauses: List[RuleClause]) -> None:
        """Adds multiple clauses and rebuilds the vector index."""
        for c in clauses:
            self.clauses[c.id] = c
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """Recalculates IDF and embeddings across all stored clauses."""
        self.total_docs = len(self.clauses)
        if self.total_docs == 0:
            return

        # 1. Compute Document Frequencies
        df_counter: Counter = Counter()
        clause_tokens: Dict[str, List[str]] = {}

        for cid, clause in self.clauses.items():
            corpus_text = f"{clause.title} {clause.category} {clause.legal_text} {' '.join(clause.keywords)}"
            tokens = tokenize(corpus_text)
            clause_tokens[cid] = tokens
            unique_tokens = set(tokens)
            df_counter.update(unique_tokens)

        # 2. Compute Smoothed IDF
        self.idf = {
            t: math.log(1.0 + (self.total_docs / (df + 1.0))) + 1.0
            for t, df in df_counter.items()
        }

        # 3. Compute Vectors
        self.vectors.clear()
        for cid, tokens in clause_tokens.items():
            self.vectors[cid] = compute_vector(tokens, self.idf)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
    ) -> PolicySearchResponse:
        """
        Executes hybrid semantic vector search with keyword boost.
        """
        query_tokens = tokenize(query)
        if not query_tokens or not self.clauses:
            return PolicySearchResponse(query=query, total_matches=0, matches=[])

        query_vec = compute_vector(query_tokens, self.idf)
        scores: List[Tuple[str, float, List[str]]] = []

        query_token_set = set(query_tokens)

        for cid, clause in self.clauses.items():
            if category_filter and category_filter.lower() not in clause.category.lower():
                continue

            # Vector similarity
            vec_sim = cosine_similarity(query_vec, self.vectors.get(cid, {}))

            # Keyword matches in title/keywords
            clause_text = f"{clause.title} {clause.category} {clause.legal_text} {' '.join(clause.keywords)}".lower()
            keyword_overlap = [t for t in query_tokens if t in clause_text]
            keyword_boost = len(keyword_overlap) / max(len(query_tokens), 1) * 0.35

            total_score = min(1.0, (vec_sim * 0.65) + keyword_boost)

            if total_score > 0.05:
                # Find highlight snippets
                highlights = [
                    sentence.strip()
                    for sentence in re.split(r"[.\n]", clause.legal_text)
                    if any(t in sentence.lower() for t in query_tokens)
                ][:2]

                scores.append((cid, total_score, highlights))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        matches = [
            PolicyClauseMatch(
                clause=self.clauses[cid],
                similarity_score=round(score, 3),
                matched_highlights=highlights,
            )
            for cid, score, highlights in top_results
        ]

        return PolicySearchResponse(
            query=query,
            total_matches=len(matches),
            matches=matches,
        )


# Global singleton instance
policy_vector_store = PolicyVectorStore()
