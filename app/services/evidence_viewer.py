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

from app.services.evidence_locations import location_label

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


_CELL_SEPARATOR = re.compile(r' ?\| ?')
HEADER_SCAN_ROWS = 10
_NUMBER = re.compile(r'[-+]?[\d,.]+%?')


def _finish_sheet(sheet):
    """Pick the header row: the first early row as wide as the widest, with no empty or numeric cells.

    Workbooks often put a title or metadata rows above the real column names; those
    rows go to a preamble shown above the table instead of becoming its header.
    """
    rows = [[cell.strip() for cell in _CELL_SEPARATOR.split(line)] for line in sheet.pop('lines')]
    width = max((len(row) for row in rows), default=0)
    start = next((index for index, row in enumerate(rows[:HEADER_SCAN_ROWS])
                  if width > 1 and len(row) == width and all(row) and not any(_NUMBER.fullmatch(cell) for cell in row)), None)
    if start is None:
        sheet['preamble'], sheet['header'], body = [], None, rows
    else:
        sheet['preamble'], sheet['header'], body = rows[:start], rows[start], rows[start + 1:]
    sheet['rows'] = [row + [''] * (width - len(row)) for row in body]


def text_blocks(text, tabular):
    """Preserve every stored row; extraction markers are notes outside tables."""
    blocks = []
    sheet = None
    for line in text.splitlines():
        marker = line.startswith(('[stored rows ', '[sheet ', '[OCR page '))
        if marker or line.strip() == '[cell truncated]':
            blocks.append({'kind': 'note', 'text': line})
        elif tabular and line.startswith('Sheet: '):
            sheet = {'kind': 'sheet', 'name': line[7:], 'lines': []}
            blocks.append(sheet)
        elif tabular and sheet is not None and line:
            sheet['lines'].append(line)
            if '[cell truncated]' in line:
                blocks.append({'kind': 'note', 'text': f"Sheet {sheet['name']}: [cell truncated]"})
        else:
            if blocks and blocks[-1]['kind'] == 'text':
                blocks[-1]['text'] += '\n' + line
            else:
                blocks.append({'kind': 'text', 'text': line})
    for block in blocks:
        if block['kind'] == 'sheet':
            _finish_sheet(block)
    return blocks


def _control_title(framework_id, requirement_id):
    from app.frameworks.registry import FrameworkRegistry

    framework = FrameworkRegistry.get_or_none(framework_id)
    control = framework.get_control(requirement_id) if framework else None
    return f'{control.title} ({requirement_id})' if control else requirement_id


def _span_href(version_id, ref):
    return '/evidence-versions/' + version_id + '/span?' + urlencode({'ref': ref}) + '#cited-span'


def _control(framework_ids, control_id):
    """Title and id for a coverage area; areas that are not control ids keep the raw id."""
    from app.frameworks.registry import FrameworkRegistry

    for framework_id in framework_ids:
        framework = FrameworkRegistry.get_or_none(framework_id)
        control = framework.get_control(control_id) if framework else None
        if control:
            return {'id': control_id, 'title': control.title}
    return {'id': control_id, 'title': None}


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
                    areas = entry.get('coverage_areas')
                    controls = [_control(assessment.frameworks, area) for area in areas
                                if isinstance(area, str) and area] if isinstance(areas, list) else []
                    catalog.append({'entry': entry, 'assessment': assessment.display_name, 'controls': controls})
    citations = []
    version_ids = {item['id'] for item in evidence['versions']}
    # Include historical revisions: citations refer to immutable versions.
    # Narrow in SQL to rows naming one of these versions; the JSON check below stays exact.
    mentions = lambda column: or_(*(column.contains(version_id) for version_id in version_ids))
    rows = db.query(ConclusionRevision, Conclusion).join(
        Conclusion, ConclusionRevision.conclusion_id == Conclusion.id,
    ).filter(mentions(ConclusionRevision.citations_json)).all() if version_ids else []
    sources = [(rev.citations_json, f'Conclusion: {_control_title(con.framework_id, con.requirement_id)}',
                con.assessment_id) for rev, con in rows]
    findings = db.query(DeskReviewFinding).filter(
        mentions(DeskReviewFinding.citations_json)).all() if version_ids else []
    sources += [(row.citations_json, row.content, row.assessment_id) for row in findings]
    passages = {}
    for row in findings:
        if row.finding_type != 'evidence' or not row.requirement_id:
            continue
        for citation in _json_list(row.citations_json):
            if not isinstance(citation, dict) or citation.get('evidence_version_id') not in version_ids:
                continue
            if row.framework_id:
                framework_ids = [row.framework_id]
            else:
                finding_assessment = db.get(Assessment, row.assessment_id)
                framework_ids = finding_assessment.frameworks if finding_assessment else []
            group = passages.setdefault(row.requirement_id,
                                        {**_control(framework_ids, row.requirement_id), 'passages': []})
            ref = citation.get('location_ref', 'whole')
            href = _span_href(citation['evidence_version_id'], ref)
            if any(passage['href'] == href for passage in group['passages']):
                continue
            group['passages'].append({
                'excerpt': citation.get('excerpt') or row.source_quote or '',
                'location': location_label(ref), 'href': href,
            })
    for payload, label, assessment_id in sources:
        for citation in _json_list(payload):
            if not isinstance(citation, dict) or citation.get('evidence_version_id') not in version_ids:
                continue
            ref = citation.get('location_ref', 'whole')
            assessment = db.get(Assessment, assessment_id)
            citations.append({
                'label': label, 'assessment': assessment.display_name if assessment else 'Assessment',
                'location': location_label(ref), 'excerpt': citation.get('excerpt', ''),
                'href': _span_href(citation['evidence_version_id'], ref),
            })
    return {
        'viewer_version': version,
        'file_available': bool(version and version.status == 'active' and evidence['status'] == 'active'),
        'inline_file': bool(version and version.mime_type in INLINE_MIMES),
        'text_blocks': text_blocks(version.extracted_text or '', version.mime_type in TABULAR_MIMES)
                       if version else [],
        'catalog_entries': catalog, 'viewer_citations': citations,
        'key_passages': sorted(passages.values(), key=lambda group: group['id']) if catalog else [],
    }


def safe_filename(filename: str) -> str:
    basename = filename.replace('\\', '/').split('/')[-1]
    return re.sub(r'[\x00-\x1f\x7f";]', '_', basename).strip('. ') or 'evidence'
