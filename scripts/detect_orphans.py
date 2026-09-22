"""Find rows in child tables whose assessment_id/report_id doesn't exist in the parent table."""

from sqlalchemy import create_engine, text

from app.config import settings


def detect_orphans(db_url: str | None = None):
    url = db_url or settings.database_url
    engine = create_engine(url)

    checks = [
        ("assessment_documents", "assessment_id", "assessments", "id"),
        ("questionnaire_responses", "assessment_id", "assessments", "id"),
        ("desk_review_summaries", "assessment_id", "assessments", "id"),
        ("desk_review_findings", "assessment_id", "assessments", "id"),
        ("gap_reports", "assessment_id", "assessments", "id"),
        ("rfi_documents", "assessment_id", "assessments", "id"),
        ("gap_items", "report_id", "gap_reports", "id"),
        ("initiatives", "report_id", "gap_reports", "id"),
    ]

    found_any = False
    with engine.connect() as conn:
        for child_table, child_col, parent_table, parent_col in checks:
            # Skip if table doesn't exist
            exists = conn.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{child_table}'")
            ).fetchone()
            if not exists:
                continue

            orphans = conn.execute(
                text(
                    f"SELECT c.{child_col}, COUNT(*) as cnt "
                    f"FROM {child_table} c "
                    f"LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col} "
                    f"WHERE p.{parent_col} IS NULL "
                    f"GROUP BY c.{child_col}"
                )
            ).fetchall()

            if orphans:
                found_any = True
                total = sum(row[1] for row in orphans)
                print(f"ORPHANS: {child_table}.{child_col} -> {parent_table}.{parent_col}: "
                      f"{total} rows across {len(orphans)} missing parents")
                for row in orphans:
                    print(f"  missing {parent_col}={row[0]}: {row[1]} orphaned rows")
            else:
                print(f"  OK: {child_table}.{child_col} -> {parent_table}.{parent_col}")

    engine.dispose()

    if not found_any:
        print("\nNo orphans found.")
    return not found_any


if __name__ == "__main__":
    import sys
    db_url = sys.argv[1] if len(sys.argv) > 1 else None
    clean = detect_orphans(db_url)
    sys.exit(0 if clean else 1)
