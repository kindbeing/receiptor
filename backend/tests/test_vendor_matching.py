"""
Test suite for vendor matching service using RapidFuzz.
Following TDD approach - these tests should fail initially.
"""
import pytest
import pytest_asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subcontractor
from services.vendor_matching_service import VendorMatchingService, MatchCandidate


@pytest_asyncio.fixture
async def test_subcontractors(test_db: AsyncSession):
    """Create test subcontractors for matching"""
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    other_builder_id = UUID('00000000-0000-0000-0000-000000000002')
    
    subcontractors = [
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000001'),
            name='ABC Plumbing LLC',
            builder_id=builder_id,
            contact_info={"phone": "555-0101"}
        ),
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000002'),
            name='Smith Electric Inc',
            builder_id=builder_id,
            contact_info={"phone": "555-0102"}
        ),
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000003'),
            name='Johnson HVAC Services',
            builder_id=builder_id,
            contact_info={"phone": "555-0103"}
        ),
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000004'),
            name='A.B.C. Plumbing',
            builder_id=builder_id,
            contact_info={"phone": "555-0104"}
        ),
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000005'),
            name='Davis Roofing & Siding',
            builder_id=builder_id,
            contact_info={"phone": "555-0105"}
        ),
        # Different builder - should not match
        Subcontractor(
            id=UUID('10000000-0000-0000-0000-000000000099'),
            name='ABC Plumbing LLC',
            builder_id=other_builder_id,
            contact_info={"phone": "555-0199"}
        ),
    ]
    
    for sub in subcontractors:
        test_db.add(sub)
    await test_db.commit()
    
    return subcontractors


@pytest.mark.asyncio
async def test_exact_match(test_db: AsyncSession, test_subcontractors):
    """Test exact vendor name match returns 100% score"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("ABC Plumbing LLC", builder_id)
    
    assert len(matches) > 0
    assert matches[0].score == 100
    assert matches[0].subcontractor_name == "ABC Plumbing LLC"
    assert matches[0].subcontractor_id == UUID('10000000-0000-0000-0000-000000000001')


@pytest.mark.asyncio
async def test_close_typo_match(test_db: AsyncSession, test_subcontractors):
    """Test typo in vendor name still returns high score (90%+)"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    # Missing one 'C' in ABC
    matches = await service.match("AB Plumbing LLC", builder_id)
    
    assert len(matches) > 0
    assert matches[0].score >= 90
    assert "ABC Plumbing" in matches[0].subcontractor_name


@pytest.mark.asyncio
async def test_abbreviation_match(test_db: AsyncSession, test_subcontractors):
    """Test abbreviation variations match with 85%+ score"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    # "ABC Plumbing" should match both "ABC Plumbing LLC" and "A.B.C. Plumbing"
    matches = await service.match("ABC Plumbing", builder_id)
    
    assert len(matches) >= 2
    # Top match should be high confidence
    assert matches[0].score >= 85
    # Should include both variations
    names = [m.subcontractor_name for m in matches]
    assert any("ABC Plumbing" in name for name in names)


@pytest.mark.asyncio
async def test_no_match_below_threshold(test_db: AsyncSession, test_subcontractors):
    """Test completely different name returns low score or no matches"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("XYZ Totally Different Company", builder_id)
    
    # Should either return no matches or all below 70% threshold
    if len(matches) > 0:
        assert all(m.score < 70 for m in matches)


@pytest.mark.asyncio
async def test_top_three_candidates_sorted(test_db: AsyncSession, test_subcontractors):
    """Test returns top 3 matches sorted by score descending"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("ABC Plumbing", builder_id)
    
    # Should return at most 3 matches
    assert len(matches) <= 3
    
    # Should be sorted by score descending
    if len(matches) > 1:
        for i in range(len(matches) - 1):
            assert matches[i].score >= matches[i + 1].score


@pytest.mark.asyncio
async def test_builder_isolation(test_db: AsyncSession, test_subcontractors):
    """Test matching only searches within builder's subcontractors (multi-tenancy)"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("ABC Plumbing LLC", builder_id)
    
    # Should only match the builder_id=1 subcontractor, not builder_id=2
    assert len(matches) > 0
    for match in matches:
        # Verify by checking the ID - should be the builder 1 version
        assert match.subcontractor_id != UUID('10000000-0000-0000-0000-000000000099')


@pytest.mark.asyncio
async def test_case_insensitive_matching(test_db: AsyncSession, test_subcontractors):
    """Test matching is case insensitive"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    # All lowercase
    matches = await service.match("abc plumbing llc", builder_id)
    
    assert len(matches) > 0
    assert matches[0].score >= 95  # Should be very high since only case differs


@pytest.mark.asyncio
async def test_special_characters_handling(test_db: AsyncSession, test_subcontractors):
    """Test matching handles special characters (dots, commas, etc.)"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    # "A.B.C. Plumbing" in DB, searching without dots
    matches = await service.match("ABC Plumbing", builder_id)
    
    assert len(matches) > 0
    # Should match "A.B.C. Plumbing" with high confidence
    assert any("A.B.C." in m.subcontractor_name for m in matches)


@pytest.mark.asyncio
async def test_empty_vendor_name(test_db: AsyncSession, test_subcontractors):
    """Test graceful handling of empty vendor name"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("", builder_id)
    
    # Should return empty list, not crash
    assert matches == []


@pytest.mark.asyncio
async def test_match_candidate_structure(test_db: AsyncSession, test_subcontractors):
    """Test MatchCandidate has all required fields"""
    service = VendorMatchingService(test_db)
    builder_id = UUID('00000000-0000-0000-0000-000000000001')
    
    matches = await service.match("ABC Plumbing LLC", builder_id)
    
    assert len(matches) > 0
    candidate = matches[0]
    
    # Verify all fields exist
    assert hasattr(candidate, 'subcontractor_id')
    assert hasattr(candidate, 'subcontractor_name')
    assert hasattr(candidate, 'score')
    assert hasattr(candidate, 'contact_info')
    
    # Verify types
    assert isinstance(candidate.subcontractor_id, UUID)
    assert isinstance(candidate.subcontractor_name, str)
    assert isinstance(candidate.score, int)
    assert 0 <= candidate.score <= 100

