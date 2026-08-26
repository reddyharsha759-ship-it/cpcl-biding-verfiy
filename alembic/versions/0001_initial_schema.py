"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-23 15:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Bidders Table
    op.create_table(
        'bidders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('pan', sa.String(length=10), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=False),
        sa.Column('udyam_reg_no', sa.String(length=30), nullable=True),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('trade_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bidders_id'), 'bidders', ['id'], unique=False)
    op.create_index(op.f('ix_bidders_pan'), 'bidders', ['pan'], unique=False)
    op.create_index(op.f('ix_bidders_gstin'), 'bidders', ['gstin'], unique=True)
    op.create_index(op.f('ix_bidders_udyam_reg_no'), 'bidders', ['udyam_reg_no'], unique=False)

    # 2. Create Tenders Table
    op.create_table(
        'tenders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('gem_bid_number', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('required_nic_codes', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('min_turnover_inr', sa.Float(), nullable=True),
        sa.Column('mii_preference_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenders_id'), 'tenders', ['id'], unique=False)
    op.create_index(op.f('ix_tenders_gem_bid_number'), 'tenders', ['gem_bid_number'], unique=True)

    # 3. Create Verification Jobs Table
    jobstatus_enum = sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='jobstatus_enum')
    risktier_enum = sa.Enum('GREEN', 'AMBER', 'RED', name='risktier_enum')

    op.create_table(
        'verification_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tender_id', sa.Uuid(), nullable=False),
        sa.Column('bidder_id', sa.Uuid(), nullable=False),
        sa.Column('status', jobstatus_enum, nullable=False),
        sa.Column('bci_score', sa.Float(), nullable=True),
        sa.Column('risk_tier', risktier_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['bidder_id'], ['bidders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_jobs_id'), 'verification_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_verification_jobs_bidder_id'), 'verification_jobs', ['bidder_id'], unique=False)
    op.create_index(op.f('ix_verification_jobs_tender_id'), 'verification_jobs', ['tender_id'], unique=False)
    op.create_index(op.f('ix_verification_jobs_status'), 'verification_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_verification_jobs_risk_tier'), 'verification_jobs', ['risk_tier'], unique=False)

    # 4. Create Compliance Audit Logs Table
    pillartype_enum = sa.Enum('GST', 'UDYAM', 'PAN', 'MII', 'DEBARMENT', 'OEM', name='pillartype_enum')

    op.create_table(
        'compliance_audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_id', sa.Uuid(), nullable=False),
        sa.Column('pillar', pillartype_enum, nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('payload_sha256', sa.String(length=64), nullable=False),
        sa.Column('is_compliant', sa.Boolean(), nullable=False),
        sa.Column('findings', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['verification_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_audit_logs_id'), 'compliance_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_job_id'), 'compliance_audit_logs', ['job_id'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_pillar'), 'compliance_audit_logs', ['pillar'], unique=False)
    op.create_index('ix_compliance_audit_job_pillar', 'compliance_audit_logs', ['job_id', 'pillar'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_compliance_audit_job_pillar', table_name='compliance_audit_logs')
    op.drop_index(op.f('ix_compliance_audit_logs_pillar'), table_name='compliance_audit_logs')
    op.drop_index(op.f('ix_compliance_audit_logs_job_id'), table_name='compliance_audit_logs')
    op.drop_index(op.f('ix_compliance_audit_logs_id'), table_name='compliance_audit_logs')
    op.drop_table('compliance_audit_logs')

    op.drop_index(op.f('ix_verification_jobs_risk_tier'), table_name='verification_jobs')
    op.drop_index(op.f('ix_verification_jobs_status'), table_name='verification_jobs')
    op.drop_index(op.f('ix_verification_jobs_tender_id'), table_name='verification_jobs')
    op.drop_index(op.f('ix_verification_jobs_bidder_id'), table_name='verification_jobs')
    op.drop_index(op.f('ix_verification_jobs_id'), table_name='verification_jobs')
    op.drop_table('verification_jobs')

    op.drop_index(op.f('ix_tenders_gem_bid_number'), table_name='tenders')
    op.drop_index(op.f('ix_tenders_id'), table_name='tenders')
    op.drop_table('tenders')

    op.drop_index(op.f('ix_bidders_udyam_reg_no'), table_name='bidders')
    op.drop_index(op.f('ix_bidders_gstin'), table_name='bidders')
    op.drop_index(op.f('ix_bidders_pan'), table_name='bidders')
    op.drop_index(op.f('ix_bidders_id'), table_name='bidders')
    op.drop_table('bidders')

    # Drop enums
    sa.Enum(name='pillartype_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='risktier_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobstatus_enum').drop(op.get_bind(), checkfirst=True)
