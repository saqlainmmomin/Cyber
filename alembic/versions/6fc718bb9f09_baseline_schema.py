"""baseline schema: current schema as of PR #14

Frozen, revision-owned DDL — a snapshot of the schema as it existed when
this revision was written, generated once from Base.metadata via
alembic.autogenerate and hand-verified against app/models/*.py. It does
NOT read Base.metadata at migration-run time: a historical migration must
produce the same DDL forever, regardless of how the ORM models change
later. Future schema changes belong in new revisions, never in edits here.

Each table is guarded with "create only if missing" purely by inspecting
the target database's *current* table list (never Base.metadata) — this
is the adoption path for a pre-existing, unversioned database that already
has these tables (from the old create_all()-based startup) but no
alembic_version row yet. A brand-new database has none of these tables, so
every guard is a no-op and the full frozen DDL below runs.

Revision ID: 6fc718bb9f09
Revises:
Create Date: 2026-09-22 10:53:57.257026

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6fc718bb9f09'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if 'assessments' not in existing_tables:
        op.create_table(
            'assessments',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('company_name', sa.String(length=255), nullable=False),
            sa.Column('industry', sa.String(length=100), nullable=False),
            sa.Column('company_size', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('scope_answers', sa.Text(), nullable=True),
            sa.Column('applicable_requirements', sa.Text(), nullable=True),
            sa.Column('context_answers', sa.Text(), nullable=True),
            sa.Column('context_profile', sa.Text(), nullable=True),
            sa.Column('desk_review_status', sa.String(length=20), nullable=True),
            sa.Column('screening_status', sa.String(length=20), nullable=True),
            sa.Column('screening_results', sa.Text(), nullable=True),
            sa.Column('selected_frameworks', sa.Text(), nullable=True),
            sa.Column('review_status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'assessment_documents' not in existing_tables:
        op.create_table(
            'assessment_documents',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_type', sa.String(length=10), nullable=False),
            sa.Column('document_category', sa.String(length=50), nullable=False),
            sa.Column('extracted_text', sa.Text(), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_assessment_documents_assessment_id'),
            'assessment_documents', ['assessment_id'], unique=False,
        )

    if 'desk_review_summaries' not in existing_tables:
        op.create_table(
            'desk_review_summaries',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('document_catalog', sa.Text(), nullable=True),
            sa.Column('coverage_summary', sa.Text(), nullable=True),
            sa.Column('raw_ai_response', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('legacy_history', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_desk_review_summaries_assessment_id'),
            'desk_review_summaries', ['assessment_id'], unique=True,
        )

    if 'gap_reports' not in existing_tables:
        op.create_table(
            'gap_reports',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('overall_score', sa.Float(), nullable=False),
            sa.Column('chapter_scores', sa.Text(), nullable=False),
            sa.Column('executive_summary', sa.Text(), nullable=False),
            sa.Column('raw_ai_response', sa.Text(), nullable=False),
            sa.Column('framework_scores', sa.Text(), nullable=True),
            sa.Column('legacy_history', sa.Text(), nullable=True),
            sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_gap_reports_assessment_id'),
            'gap_reports', ['assessment_id'], unique=True,
        )

    if 'questionnaire_responses' not in existing_tables:
        op.create_table(
            'questionnaire_responses',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('question_id', sa.String(length=50), nullable=False),
            sa.Column('answer', sa.String(length=20), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('evidence_reference', sa.Text(), nullable=True),
            sa.Column('na_reason', sa.String(length=50), nullable=True),
            sa.Column('confidence', sa.String(length=20), nullable=True),
            sa.Column('cluster_id', sa.String(length=80), nullable=True),
            sa.Column('answer_source', sa.String(length=20), nullable=True),
            sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "answer IN ('fully_implemented', 'partially_implemented', 'planned', 'not_implemented', 'not_applicable')",
                name='ck_questionnaire_responses_answer_valid',
            ),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_questionnaire_responses_assessment_id'),
            'questionnaire_responses', ['assessment_id'], unique=False,
        )

    if 'rfi_documents' not in existing_tables:
        op.create_table(
            'rfi_documents',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('introduction', sa.Text(), nullable=False),
            sa.Column('evidence_items', sa.Text(), nullable=False),
            sa.Column('response_instructions', sa.Text(), nullable=False),
            sa.Column('appendix', sa.Text(), nullable=True),
            sa.Column('total_items', sa.Integer(), nullable=False),
            sa.Column('critical_items', sa.Integer(), nullable=False),
            sa.Column('raw_ai_response', sa.Text(), nullable=True),
            sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_rfi_documents_assessment_id'),
            'rfi_documents', ['assessment_id'], unique=True,
        )

    if 'desk_review_findings' not in existing_tables:
        op.create_table(
            'desk_review_findings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('assessment_id', sa.String(length=36), nullable=False),
            sa.Column('finding_type', sa.String(length=20), nullable=False),
            sa.Column('requirement_id', sa.String(length=30), nullable=True),
            sa.Column('document_id', sa.String(length=36), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('source_quote', sa.Text(), nullable=True),
            sa.Column('source_location', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id']),
            sa.ForeignKeyConstraint(['document_id'], ['assessment_documents.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_desk_review_findings_assessment_id'),
            'desk_review_findings', ['assessment_id'], unique=False,
        )

    if 'gap_items' not in existing_tables:
        op.create_table(
            'gap_items',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('report_id', sa.String(length=36), nullable=False),
            sa.Column('requirement_id', sa.String(length=50), nullable=False),
            sa.Column('framework_id', sa.String(length=30), nullable=True),
            sa.Column('cluster_id', sa.String(length=80), nullable=True),
            sa.Column('control_reference', sa.String(length=100), nullable=True),
            sa.Column('chapter', sa.String(length=50), nullable=False),
            sa.Column('requirement_title', sa.String(length=255), nullable=False),
            sa.Column('compliance_status', sa.String(length=30), nullable=False),
            sa.Column('current_state', sa.Text(), nullable=False),
            sa.Column('gap_description', sa.Text(), nullable=False),
            sa.Column('risk_level', sa.String(length=20), nullable=False),
            sa.Column('remediation_action', sa.Text(), nullable=False),
            sa.Column('remediation_priority', sa.Integer(), nullable=False),
            sa.Column('remediation_effort', sa.String(length=20), nullable=False),
            sa.Column('timeline_weeks', sa.Integer(), nullable=False),
            sa.Column('maturity_level', sa.Integer(), nullable=True),
            sa.Column('root_cause_category', sa.String(length=30), nullable=True),
            sa.Column('evidence_quote', sa.Text(), nullable=True),
            sa.Column('evidence_confidence', sa.String(length=20), nullable=True),
            sa.Column('remediation_status', sa.String(length=20), nullable=True),
            sa.Column('remediation_owner', sa.String(length=255), nullable=True),
            sa.Column('remediation_target_date', sa.DateTime(), nullable=True),
            sa.Column('remediation_notes', sa.Text(), nullable=True),
            sa.Column('remediation_closed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('review_status', sa.String(length=20), nullable=True),
            sa.Column('needs_review', sa.Boolean(), server_default='0', nullable=True),
            sa.Column('ai_compliance_status', sa.Text(), nullable=True),
            sa.Column('ai_gap_description', sa.Text(), nullable=True),
            sa.Column('ai_risk_level', sa.String(length=20), nullable=True),
            sa.Column('reviewer_notes', sa.Text(), nullable=True),
            sa.Column('reviewed_by', sa.String(length=255), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['report_id'], ['gap_reports.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_gap_items_report_id'), 'gap_items', ['report_id'], unique=False)

    if 'initiatives' not in existing_tables:
        op.create_table(
            'initiatives',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('report_id', sa.String(length=36), nullable=False),
            sa.Column('initiative_id', sa.String(length=20), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('root_cause', sa.Text(), nullable=False),
            sa.Column('root_cause_category', sa.String(length=30), nullable=False),
            sa.Column('requirements_addressed', sa.Text(), nullable=False),
            sa.Column('combined_effort', sa.String(length=20), nullable=False),
            sa.Column('combined_timeline_weeks', sa.Integer(), nullable=False),
            sa.Column('priority', sa.Integer(), nullable=False),
            sa.Column('budget_estimate_band', sa.String(length=50), nullable=True),
            sa.Column('suggested_approach', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['report_id'], ['gap_reports.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_initiatives_report_id'), 'initiatives', ['report_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if 'initiatives' in existing_tables:
        op.drop_index(op.f('ix_initiatives_report_id'), table_name='initiatives')
        op.drop_table('initiatives')
    if 'gap_items' in existing_tables:
        op.drop_index(op.f('ix_gap_items_report_id'), table_name='gap_items')
        op.drop_table('gap_items')
    if 'desk_review_findings' in existing_tables:
        op.drop_index(op.f('ix_desk_review_findings_assessment_id'), table_name='desk_review_findings')
        op.drop_table('desk_review_findings')
    if 'rfi_documents' in existing_tables:
        op.drop_index(op.f('ix_rfi_documents_assessment_id'), table_name='rfi_documents')
        op.drop_table('rfi_documents')
    if 'questionnaire_responses' in existing_tables:
        op.drop_index(op.f('ix_questionnaire_responses_assessment_id'), table_name='questionnaire_responses')
        op.drop_table('questionnaire_responses')
    if 'gap_reports' in existing_tables:
        op.drop_index(op.f('ix_gap_reports_assessment_id'), table_name='gap_reports')
        op.drop_table('gap_reports')
    if 'desk_review_summaries' in existing_tables:
        op.drop_index(op.f('ix_desk_review_summaries_assessment_id'), table_name='desk_review_summaries')
        op.drop_table('desk_review_summaries')
    if 'assessment_documents' in existing_tables:
        op.drop_index(op.f('ix_assessment_documents_assessment_id'), table_name='assessment_documents')
        op.drop_table('assessment_documents')
    if 'assessments' in existing_tables:
        op.drop_table('assessments')
