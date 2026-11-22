"""
Retrieval Quality Evaluation Benchmark for AI Grama Sahayak.
Evaluates retrieval performance across all four public-service domains in Telugu and English,
measuring Hit Rate@1, Hit Rate@3, Mean Reciprocal Rank (MRR), and negative query precision.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.services.retrieval.service import RetrievalService

logger = logging.getLogger("ai_grama_sahayak.services.retrieval.evaluator")


class RetrievalEvaluator:
    """
    Automated benchmark runner against knowledge_base/evaluation_dataset.json.
    """

    def __init__(self, kb_base_dir: Optional[str] = None):
        if kb_base_dir:
            self.kb_base_dir = Path(kb_base_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parent.parent.parent.parent
            self.kb_base_dir = repo_root / "knowledge_base"

        self.eval_path = self.kb_base_dir / "evaluation_dataset.json"
        self.service = RetrievalService(kb_base_dir=str(self.kb_base_dir))
        self.service.initialize(include_demo=False)

    def load_dataset(self) -> List[Dict[str, Any]]:
        if not self.eval_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.eval_path}")
        with open(self.eval_path, mode="r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluation(self) -> Dict[str, Any]:
        dataset = self.load_dataset()
        total_queries = len(dataset)
        positive_queries = 0
        negative_queries = 0

        hits_at_1 = 0
        hits_at_3 = 0
        sum_reciprocal_rank = 0.0
        correct_negatives = 0
        domain_leakage_count = 0

        detailed_results = []

        for item in dataset:
            query_id = item["id"]
            query = item["query"]
            assistant = item["assistant"]
            language = item.get("language", "en")
            state = item.get("state")
            district = item.get("district")
            expected_source_id = item.get("expected_source_id")

            # Execute retrieval
            retrieved = self.service.retrieve(
                query=query,
                assistant=assistant,
                language=language,
                state=state,
                district=district,
                top_k=5,
            )

            # Check for domain leakage (critical safety check)
            for c in retrieved:
                chunk_domain = c.get("metadata", {}).get("domain", "")
                if chunk_domain.lower() != assistant.lower():
                    domain_leakage_count += 1

            retrieved_doc_ids = [
                c.get("metadata", {}).get("doc_id", "") for c in retrieved
            ]

            result_entry = {
                "id": query_id,
                "query": query,
                "assistant": assistant,
                "language": language,
                "expected_source_id": expected_source_id,
                "retrieved_count": len(retrieved),
                "top_retrieved_ids": retrieved_doc_ids[:3],
                "hit_at_1": False,
                "hit_at_3": False,
                "reciprocal_rank": 0.0,
                "correct_negative": False,
            }

            if expected_source_id is None:
                # Negative / Irrelevant query test
                negative_queries += 1
                if len(retrieved) == 0:
                    correct_negatives += 1
                    result_entry["correct_negative"] = True
            else:
                # Positive query test
                positive_queries += 1
                rank = None
                for idx, doc_id in enumerate(retrieved_doc_ids):
                    if doc_id == expected_source_id:
                        rank = idx + 1
                        break

                if rank == 1:
                    hits_at_1 += 1
                    hits_at_3 += 1
                    reciprocal_rank = 1.0
                    result_entry["hit_at_1"] = True
                    result_entry["hit_at_3"] = True
                elif rank in (2, 3):
                    hits_at_3 += 1
                    reciprocal_rank = 1.0 / rank
                    result_entry["hit_at_3"] = True
                elif rank is not None:
                    reciprocal_rank = 1.0 / rank
                else:
                    reciprocal_rank = 0.0

                sum_reciprocal_rank += reciprocal_rank
                result_entry["reciprocal_rank"] = reciprocal_rank

            detailed_results.append(result_entry)

        hit_rate_at_1 = hits_at_1 / positive_queries if positive_queries > 0 else 0.0
        hit_rate_at_3 = hits_at_3 / positive_queries if positive_queries > 0 else 0.0
        mrr = sum_reciprocal_rank / positive_queries if positive_queries > 0 else 0.0
        negative_accuracy = correct_negatives / negative_queries if negative_queries > 0 else 1.0

        summary = {
            "total_queries": total_queries,
            "positive_queries": positive_queries,
            "negative_queries": negative_queries,
            "hits_at_1": hits_at_1,
            "hits_at_3": hits_at_3,
            "hit_rate_at_1": round(hit_rate_at_1, 4),
            "hit_rate_at_3": round(hit_rate_at_3, 4),
            "mean_reciprocal_rank": round(mrr, 4),
            "negative_rejection_accuracy": round(negative_accuracy, 4),
            "domain_leakage_violations": domain_leakage_count,
            "detailed_results": detailed_results,
        }

        return summary


def main():
    evaluator = RetrievalEvaluator()
    summary = evaluator.run_evaluation()
    print("=" * 60)
    print("AI GRAMA SAHAYAK — RETRIEVAL QUALITY EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Test Queries:       {summary['total_queries']}")
    print(f"Positive Test Queries:    {summary['positive_queries']}")
    print(f"Negative/Irrelevant:      {summary['negative_queries']}")
    print(f"Hit Rate @ 1:             {summary['hit_rate_at_1'] * 100:.1f}% ({summary['hits_at_1']}/{summary['positive_queries']})")
    print(f"Hit Rate @ 3:             {summary['hit_rate_at_3'] * 100:.1f}% ({summary['hits_at_3']}/{summary['positive_queries']})")
    print(f"Mean Reciprocal Rank:     {summary['mean_reciprocal_rank']:.4f}")
    print(f"Negative Rejection Rate:  {summary['negative_rejection_accuracy'] * 100:.1f}%")
    print(f"Domain Leakage Violations:{summary['domain_leakage_violations']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
