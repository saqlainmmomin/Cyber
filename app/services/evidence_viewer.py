"""Read-only presentation of stored evidence text, catalog entries and citations."""
import json
import re
from urllib.parse import urlencode

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.evidence import EvidenceVersion

INLINE_MIMES = frozenset({'application/pdf', 'image/png', 'image/jpeg', 'image/webp'})
TABULAR_MIMES = frozenset({
    'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
})


def _json_list(value):
    try:
        decoded = json.loads(value or '[]')
    except (ValueError, TypeError):
        return []
    return decoded if isinstance(decoded, list) else []


def text_blocks(text, tabular):
    """Preserve every stored row; extraction markers are notes outside tables."""
    blocks = []
    sheet = None
    for line in text.splitlines():
        marker = line.startswith(('[stored rows ', '[sheet ', '[OCR page '))
        if marker or line.strip() == '[cell truncated]':
            blocks.append({'kind': 'note', 'text': line})
        elif tabular and line.startswith('Sheet: '):
            sheet = {'kind': 'sheet', 'name': line[7:], 'header': None, 'rows': []}
            blocks.append(sheet)
        elif tabular and sheet is not None and line:
            cells = line.split(' | ')
            if sheet['header'] is None:
                sheet['header'] = cells
            else:
                sheet['rows'].append(cells)
            if '[cell truncated]' in line:
                blocks.append({'kind': 'note', 'text': f"Sheet {sheet['name']}: [cell truncated]"})
        else:
            if blocks and blocks[-1]['kind'] == 'text':
                blocks[-1]['text'] += '\n' + line
            else:
                blocks.append({'kind': 'text', 'text': line})
    return blocks


def viewer_context(db: Session, evidence: dict) -> dict:
    current = evidence['current_version']
    version = db.get(EvidenceVersion, current['id']) if current else None
    assessment_ids = {use['assessment_id'] for use in evidence['uses']}
    if evidence['assessment_id']:
        assessment_ids.add(evidence['assessment_id'])
    catalog = []
    if version and assessment_ids:
        summaries = db.query(DeskReviewSummary).filter(
            DeskReviewSummary.assessment_id.in_(assessment_ids),
            DeskReviewSummary.status == 'completed',
        ).order_by(DeskReviewSummary.assessment_id).all()
        for summary in summaries:
            assessment = db.get(Assessment, summary.assessment_id)
            for entry in _json_list(summary.document_catalog):
                if isinstance(entry, dict) and entry.get('filename') == version.original_filename:
                    catalog.append({'entry': entry, 'assessment': assessment.display_name})
    citations = []
    version_ids = {item['id'] for item in evidence['versions']}
    # Include historical revisions: citations refer to immutable versions.
    # Narrow in SQL to rows naming one of these versions; the JSON check below stays exact.
    mentions = lambda column: or_(*(column.contains(version_id) for version_id in version_ids))
    rows = db.query(ConclusionRevision, Conclusion).join(
        Conclusion, ConclusionRevision.conclusion_id == Conclusion.id,
    ).filter(mentions(ConclusionRevision.citations_json)).all() if version_ids else []
    sources = [(rev.citations_json, f'Conclusion: {con.requirement_id}', con.assessment_id)
               for rev, con in rows]
    sources += [(row.citations_json, row.content, row.assessment_id)
                for row in db.query(DeskReviewFinding).filter(mentions(DeskReviewFinding.citations_json)).all()] if version_ids else []
    for payload, label, assessment_id in sources:
        for citation in _json_list(payload):
            if not isinstance(citation, dict) or citation.get('evidence_version_id') not in version_ids:
                continue
            ref = citation.get('location_ref', 'whole')
            location = ('Whole document' if ref == 'whole' else
                        'Characters ' + ref[6:].replace('-', '–') if ref.startswith('chars:') else
                        'Page ' + ref[5:] if ref.startswith('page:') else ref)
            assessment = db.get(Assessment, assessment_id)
            citations.append({
                'label': label, 'assessment': assessment.display_name if assessment else 'Assessment',
                'location': location, 'excerpt': citation.get('excerpt', ''),
                'href': '/evidence-versions/' + citation['evidence_version_id'] + '/span?' +
                        urlencode({'ref': ref}) + '#cited-span',
            })
    return {
        'viewer_version': version,
        'file_available': bool(version and version.status == 'active' and evidence['status'] == 'active'),
        'inline_file': bool(version and version.mime_type in INLINE_MIMES),
        'text_blocks': text_blocks(version.extracted_text or '', version.mime_type in TABULAR_MIMES)
                       if version else [],
        'catalog_entries': catalog, 'viewer_citations': citations,
    }


def safe_filename(filename: str) -> str:
    basename = filename.replace('\\', '/').split('/')[-1]
    return re.sub(r'[\x00-\x1f\x7f";]', '_', basename).strip('. ') or 'evidence'
