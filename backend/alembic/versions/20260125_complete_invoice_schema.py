"""Complete invoice automation schema

Revision ID: 20260125_invoice
Revises: 3496d88d5878
Create Date: 2026-01-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260125_invoice'
down_revision: Union[str, Sequence[str], None] = '3496d88d5878'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create all invoice automation tables."""
    
    # Core invoice storage
    op.create_table('invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('builder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='uploaded', nullable=True),
        sa.Column('processing_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_builder_id'), 'invoices', ['builder_id'], unique=False)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)
    
    # Extraction results (stores output from OCR/Vision AI)
    op.create_table('extracted_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_name', sa.String(length=255), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_fields_invoice_id'), 'extracted_fields', ['invoice_id'], unique=False)
    
    # Subcontractor master list (for vendor matching)
    op.create_table('subcontractors',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('builder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subcontractors_builder_id'), 'subcontractors', ['builder_id'], unique=False)
    op.create_index(op.f('ix_subcontractors_name'), 'subcontractors', ['name'], unique=False)
    
    # Vendor matching results
    op.create_table('vendor_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subcontractor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('match_score', sa.Integer(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subcontractor_id'], ['subcontractors.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_matches_invoice_id'), 'vendor_matches', ['invoice_id'], unique=False)
    
    # Cost code master list
    op.create_table('cost_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('builder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cost_codes_builder_id'), 'cost_codes', ['builder_id'], unique=False)
    op.create_index(op.f('ix_cost_codes_code'), 'cost_codes', ['code'], unique=False)
    
    # Line items extracted from invoices
    op.create_table('line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('suggested_code', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('confirmed_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_line_items_invoice_id'), 'line_items', ['invoice_id'], unique=False)
    
    # Human corrections tracking
    op.create_table('correction_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_correction_history_invoice_id'), 'correction_history', ['invoice_id'], unique=False)
    
    # Performance tracking
    op.create_table('processing_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processing_metrics_invoice_id'), 'processing_metrics', ['invoice_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Drop all invoice automation tables."""
    op.drop_index(op.f('ix_processing_metrics_invoice_id'), table_name='processing_metrics')
    op.drop_table('processing_metrics')
    
    op.drop_index(op.f('ix_correction_history_invoice_id'), table_name='correction_history')
    op.drop_table('correction_history')
    
    op.drop_index(op.f('ix_line_items_invoice_id'), table_name='line_items')
    op.drop_table('line_items')
    
    op.drop_index(op.f('ix_cost_codes_code'), table_name='cost_codes')
    op.drop_index(op.f('ix_cost_codes_builder_id'), table_name='cost_codes')
    op.drop_table('cost_codes')
    
    op.drop_index(op.f('ix_vendor_matches_invoice_id'), table_name='vendor_matches')
    op.drop_table('vendor_matches')
    
    op.drop_index(op.f('ix_subcontractors_name'), table_name='subcontractors')
    op.drop_index(op.f('ix_subcontractors_builder_id'), table_name='subcontractors')
    op.drop_table('subcontractors')
    
    op.drop_index(op.f('ix_extracted_fields_invoice_id'), table_name='extracted_fields')
    op.drop_table('extracted_fields')
    
    op.drop_index(op.f('ix_invoices_status'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_builder_id'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_id'), table_name='invoices')
    op.drop_table('invoices')

