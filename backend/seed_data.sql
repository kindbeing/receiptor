-- Seed data for invoice automation demo
-- This provides test subcontractors and cost codes for Agent 2 to test matching/classification

-- Test builder ID (use this when uploading invoices)
-- Builder ID: 00000000-0000-0000-0000-000000000001

-- Insert test subcontractors
INSERT INTO subcontractors (id, name, builder_id, contact_info) VALUES
    ('10000000-0000-0000-0000-000000000001', 'ABC Plumbing LLC', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0101", "email": "contact@abcplumbing.com"}'),
    ('10000000-0000-0000-0000-000000000002', 'Smith Electric Inc', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0102", "email": "info@smithelectric.com"}'),
    ('10000000-0000-0000-0000-000000000003', 'Johnson HVAC Services', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0103", "email": "service@johnsonhvac.com"}'),
    ('10000000-0000-0000-0000-000000000004', 'A.B.C. Plumbing', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0104", "email": "office@abcplumb.com"}'),
    ('10000000-0000-0000-0000-000000000005', 'Davis Roofing & Siding', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0105", "email": "davis@roofing.com"}'),
    ('10000000-0000-0000-0000-000000000006', 'Premier Drywall Solutions', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0106", "email": "info@premierdrywall.com"}'),
    ('10000000-0000-0000-0000-000000000007', 'Elite Painting Co', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0107", "email": "elite@painting.com"}'),
    ('10000000-0000-0000-0000-000000000008', 'Martinez Concrete Works', '00000000-0000-0000-0000-000000000001', '{"phone": "555-0108", "email": "concrete@martinez.com"}');

-- Insert test cost codes (BuilderTrend standard + custom)
INSERT INTO cost_codes (id, code, label, description, builder_id) VALUES
    ('20000000-0000-0000-0000-000000000001', '15140', 'Plumbing - Rough-in', 'Install pipes, drains, and water supply lines', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000002', '15150', 'Plumbing - Fixtures', 'Install sinks, toilets, faucets, and fixtures', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000003', '16050', 'Electrical - Wiring', 'Install electrical wiring and conduit', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000004', '16060', 'Electrical - Fixtures', 'Install light fixtures, outlets, and switches', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000005', '23000', 'HVAC - Installation', 'Install heating and cooling systems', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000006', '23010', 'HVAC - Ductwork', 'Install and seal ductwork', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000007', '07000', 'Roofing - Materials', 'Roofing shingles and underlayment', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000008', '07010', 'Roofing - Labor', 'Roof installation labor', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000009', '09200', 'Drywall - Materials', 'Drywall sheets, mud, tape', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000010', '09210', 'Drywall - Labor', 'Hanging, taping, and finishing drywall', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000011', '09900', 'Painting - Interior', 'Interior painting and finishing', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000012', '09910', 'Painting - Exterior', 'Exterior painting and finishing', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000013', '03000', 'Concrete - Foundation', 'Foundation and slab concrete work', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000014', '03010', 'Concrete - Flatwork', 'Driveways, sidewalks, and patios', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000015', '06100', 'Framing - Lumber', 'Framing lumber and materials', '00000000-0000-0000-0000-000000000001'),
    ('20000000-0000-0000-0000-000000000016', '06110', 'Framing - Labor', 'Framing labor', '00000000-0000-0000-0000-000000000001');

-- Example: How Agent 2 should test
-- 1. Upload an invoice with builder_id = '00000000-0000-0000-0000-000000000001'
-- 2. Extract vendor name like "ABC Plumbing" (should match '10000000-0000-0000-0000-000000000001' or '10000000-0000-0000-0000-000000000004')
-- 3. Extract line items like "Install copper piping" (should match cost code '15140')

