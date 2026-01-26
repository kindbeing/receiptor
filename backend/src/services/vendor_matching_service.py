"""
Vendor Matching Service using RapidFuzz for fuzzy string matching.
Matches extracted vendor names to known subcontractors in builder's database.
"""
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from rapidfuzz import fuzz, process

from models import Subcontractor


@dataclass
class MatchCandidate:
    """Represents a potential vendor match with confidence score"""
    subcontractor_id: UUID
    subcontractor_name: str
    score: int  # 0-100
    contact_info: Optional[dict] = None


class VendorMatchingService:
    """
    Fuzzy matching service for vendor names.
    
    Scoring thresholds:
    - 90-100: High confidence (auto-approve)
    - 85-90: Auto-approve
    - 70-85: Show for review
    - <70: Flag as low confidence / suggest "Add New Vendor"
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.min_threshold = 70  # Don't show matches below this
    
    async def match(
        self, 
        extracted_vendor: str, 
        builder_id: UUID,
        limit: int = 3
    ) -> List[MatchCandidate]:
        """
        Find top N matching subcontractors for the extracted vendor name.
        
        Args:
            extracted_vendor: Vendor name from OCR/Vision AI extraction
            builder_id: Builder's UUID for multi-tenancy isolation
            limit: Maximum number of matches to return (default 3)
        
        Returns:
            List of MatchCandidate objects sorted by score (highest first)
        """
        # Handle empty input
        if not extracted_vendor or not extracted_vendor.strip():
            return []
        
        # Fetch all subcontractors for this builder
        result = await self.db.execute(
            select(Subcontractor).where(Subcontractor.builder_id == builder_id)
        )
        subcontractors = result.scalars().all()
        
        if not subcontractors:
            return []
        
        # Prepare names for matching
        subcontractor_names = {sub.name: sub for sub in subcontractors}
        
        # Use RapidFuzz to find best matches
        # fuzz.ratio: Standard Levenshtein distance ratio
        matches = process.extract(
            extracted_vendor,
            subcontractor_names.keys(),
            scorer=fuzz.ratio,
            limit=limit
        )
        
        # Build candidate list
        candidates = []
        for name, score, _ in matches:
            # Only include matches above threshold
            if score >= self.min_threshold:
                sub = subcontractor_names[name]
                candidates.append(
                    MatchCandidate(
                        subcontractor_id=sub.id,
                        subcontractor_name=sub.name,
                        score=int(score),
                        contact_info=sub.contact_info
                    )
                )
        
        return candidates
    
    def get_confidence_level(self, score: int) -> str:
        """
        Return confidence level based on match score.
        
        Returns: "high", "auto_approve", "review", or "low"
        """
        if score >= 90:
            return "high"
        elif score >= 85:
            return "auto_approve"
        elif score >= 70:
            return "review"
        else:
            return "low"

