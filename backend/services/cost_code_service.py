from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from models import CostCode, LineItem
import uuid


class CostCodeService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._embeddings_cache = {}
    
    def classify_line_items(
        self, 
        line_items: List[Dict], 
        builder_id: str,
        db: Session
    ) -> List[Dict]:
        """
        Classify line items to cost codes using semantic similarity.
        
        Args:
            line_items: List of dicts with 'description' field
            builder_id: UUID of the builder
            db: Database session
            
        Returns:
            List of dicts with suggested_code and confidence added
        """
        cost_codes = db.query(CostCode).filter(
            CostCode.builder_id == uuid.UUID(builder_id)
        ).all()
        
        if not cost_codes:
            return [{
                **item,
                'suggested_code': None,
                'confidence': 0.0
            } for item in line_items]
        
        cost_code_texts = [
            f"{cc.code} {cc.label} {cc.description or ''}" 
            for cc in cost_codes
        ]
        
        cache_key = f"{builder_id}_{len(cost_codes)}"
        if cache_key not in self._embeddings_cache:
            self._embeddings_cache[cache_key] = self.model.encode(
                cost_code_texts, 
                convert_to_tensor=False
            )
        
        cost_code_embeddings = self._embeddings_cache[cache_key]
        
        results = []
        for item in line_items:
            description = item.get('description', '')
            if not description:
                results.append({
                    **item,
                    'suggested_code': None,
                    'confidence': 0.0
                })
                continue
            
            item_embedding = self.model.encode([description], convert_to_tensor=False)[0]
            
            similarities = self._cosine_similarity(item_embedding, cost_code_embeddings)
            
            best_idx = np.argmax(similarities)
            best_score = float(similarities[best_idx])
            best_code = cost_codes[best_idx]
            
            results.append({
                **item,
                'suggested_code': best_code.code,
                'confidence': best_score
            })
        
        return results
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between a vector and matrix of vectors."""
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2, axis=1, keepdims=True)
        return np.dot(vec2_norm, vec1_norm)
    
    def clear_cache(self):
        """Clear embeddings cache (useful for testing or when cost codes change)."""
        self._embeddings_cache.clear()


cost_code_service = CostCodeService()
