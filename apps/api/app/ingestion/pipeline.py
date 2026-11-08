"""Offline staging and immutable publication; acquisition is a separate explicit step."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.adapters import normalize
from app.ingestion.registry import VERSION, SCHEMAS, SOURCES, PILOT, CONTEXT, STUDY_AREA, schema
from app.services.municipal_data import canonical, candidate_matches, digest

CAPABILITIES = {name:{'available':False,'reason':'NO_REAL_PLANNING_CONTRACT'}
    for name in ['estimate','conflict_analysis','scenario_evaluation','ai_explanation']}
CAPABILITIES['inspection']={'available':True,'reason':None}


def stage(acquisition: Path, decisions: dict | None = None):
    bundle=json.loads(acquisition.read_text())
    if (bundle.get('format')!='civicplain-nyc-acquisition-1' or bundle.get('bbox')!=PILOT
            or bundle.get('context_bbox')!=CONTEXT or set(bundle['sources'])!=set(SOURCES)):
        raise ValueError('Unsupported acquisition scope/format')
    # Verify original files, not only a caller-edited normalized blob.
    for key, terms in bundle['terms'].items():
        if 'sha256' in terms and hashlib.sha256((acquisition.parent/f'terms-{key}.html').read_bytes()).hexdigest()!=terms['sha256']:
            raise ValueError('Terms evidence checksum mismatch')
    records, revisions, stats, quarantines=[], [], {}, {}
    for kind, source in bundle['sources'].items():
        if (source['source']!=SOURCES[kind] or schema(source['metadata'],kind)!=SCHEMAS[kind]
                or source['schema_fingerprint']!=digest(SCHEMAS[kind])):
            raise ValueError('Unreviewed source or schema')
        folder=acquisition.parent/kind
        for filename, expected in source['files'].items():
            if Path(filename).name!=filename:
                raise ValueError('Unsafe evidence path')
            if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=expected:
                raise ValueError('Raw evidence checksum mismatch')
        pages=[]
        for filename in sorted(source['files']):
            if filename.startswith('page-'):
                page=json.loads((folder/filename).read_text())
                pages.extend(page['features'] if kind=='lion' else page)
        if pages!=source['rows']:
            raise ValueError('Acquisition rows differ from original downloaded pages')
        raw_hash=digest(sorted(source['rows'],key=canonical))
        revision={'source_id':SOURCES[kind]['id'], 'source_url':SOURCES[kind]['catalog'],
            'endpoint':SOURCES[kind]['endpoint'], 'raw_sha256':raw_hash,
            'query':source['query'], 'source_updated_at':source['source_updated_at'],
            'source_crs':SOURCES[kind]['crs'], 'cadence':SOURCES[kind]['cadence'],
            'attribution':SOURCES[kind]['attribution'], 'schema_fingerprint':source['schema_fingerprint'],
            'dictionary_url':SOURCES[kind]['dictionary'],'dictionary_sha256':source['dictionary_sha256'],
            'license':{k:v for k,v in source['license'].items() if k!='terms'},
            'terms_urls':[v['url'] for v in bundle['terms'].values()],
            'terms_review_version':'nyc-terms-review-2026-11-07', 'adapter_version':VERSION,
            'release_note':'ArcGIS editingInfo revision; not asserted to be LION catalog 26c' if kind=='lion' else 'Mutable live feed; archived content checksum is dataset version',
            'raw_page_checksums':{n:h for n,h in source['files'].items() if n.startswith('page-')}}
        if kind in {'pavement','permits'}:
            from app.ingestion.registry import DOT_TERMS
            revision['license'].update(application_disclaimer_required=True,application_disclaimer_url=DOT_TERMS)
        revision['id']=revision['source_id']+':'+digest(revision)[:32]
        from app.schemas.municipal import SourceRevision
        SourceRevision.model_validate(revision)
        # First successful publication retains acquisition time; identity excludes operational clock.
        revisions.append(revision)
        adapted,rejects,duplicates,excluded=normalize(kind,source['rows'],revision['id'])
        records.extend(adapted)
        stats[kind]={'raw':len(source['rows']), 'accepted':len(adapted),'rejected':len(rejects),
            'duplicates':duplicates,'excluded':excluded}
        quarantines[kind]=rejects
    records.sort(key=lambda r:(r['kind'],r['id']))
    if not all(stats[k]['accepted'] for k in SOURCES):
        raise ValueError('Required pilot layer has no valid records')
    if stats['lion']['accepted']>10000 or stats['permits']['accepted']>20000:
        raise ValueError('Pilot safety cap exceeded')
    # OFT is an authoritative DOT location key, not an authoritative LION segment or direction match.
    groups={}
    for r in records:
        oft=r['raw_identifiers'].get('oftcode')
        if oft:
            groups.setdefault(oft,[]).append({'kind':r['kind'],'id':r['id']})
    matches=candidate_matches(records,decisions or {})
    coverage={'study_area_id':STUDY_AREA,'bbox':PILOT,'context_bbox':CONTEXT,
        'selection':'All intersecting Manhattan LION regular streets and DOT pavement geometries; full features retained',
        'permit_selection':{'issued_on_or_after':bundle['permit_since'],
            'method':'Manhattan on-street names present among selected LION roads; may extend outside pilot',
            'membership':'Unverified street-name candidates unless reviewed road link exists',
            'completeness':'Not a census of all permits intersecting the pilot; aliases/missing names can be omitted'},
        'utility_coverage':'unknown','source_status':{k:'available' for k in SOURCES}}
    manifest={'contract_version':'municipal-record-v2','mode':'official','study_area_id':STUDY_AREA,
        'coverage':coverage,'capabilities':CAPABILITIES,'adapter_version':VERSION,
        'matching_version':'reviewed-candidates-v1','source_revision_ids':sorted(r['id'] for r in revisions),
        'runtime_versions':runtime_versions(),
        'counts':stats,'content_hash':digest({'records':records,'matches':matches}),
        'decision_hash':digest(decisions or {}),'oft_location_groups':groups,
        'warnings':['Permit presence/validity does not establish work started or a construction schedule.',
            'Unreviewed spatial/street-code candidates are not confirmed conflicts.',
            'Utility coordinates/depths and excavation safety remain unknown.',
            'DOT decimal category gaps/local-street classification unresolved; no category inferred.']}
    snapshot_hash=digest(manifest)
    snapshot_id='nyc-'+snapshot_hash[:32]
    report={'snapshot_id':snapshot_id,'manifest_hash':snapshot_hash,'counts':stats,
        'quarantine':quarantines,'match_counts':{s:sum(m['status']==s for m in matches) for s in ['matched','ambiguous','unmatched']},
        'source_revision_ids':manifest['source_revision_ids'],'warnings':manifest['warnings'],
        'quarantine_hash':digest(quarantines)}
    report['report_hash']=digest(report)
    return {'snapshot_id':snapshot_id,'manifest_hash':snapshot_hash,'manifest':manifest,
        'records':records,'matches':matches,'revisions':revisions,'report':report,
        'retrieved_at':bundle['retrieved_at'],'acquisition_hash':digest(bundle)}


def runtime_versions():
    import pyproj
    import shapely
    return {'pyproj':pyproj.__version__,'proj':pyproj.proj_version_str,
        'shapely':shapely.__version__,'geos':shapely.geos_version_string}


def publish(path, staged, approval, allow_rejects=False):
    from app.models.database import connection
    from app.schemas.municipal import MunicipalRecord, SourceRevision, GeographicMatch
    report_content={k:v for k,v in staged['report'].items() if k!='report_hash'}
    if (approval!=staged['report']['report_hash'] or approval!=digest(report_content)
            or staged['report']['snapshot_id']!=staged['snapshot_id']
            or staged['report']['manifest_hash']!=staged['manifest_hash']):
        raise ValueError('Report approval hash mismatch; review current dry-run report')
    if any(v['rejected'] for v in staged['report']['counts'].values()) and not allow_rejects:
        raise ValueError('Quarantined records require explicit --allow-rejects after report review')
    for r in staged['records']:
        MunicipalRecord.model_validate(r)
    for m in staged['matches']:
        GeographicMatch.model_validate(m)
    for revision in staged['revisions']:
        SourceRevision.model_validate(revision)
        if revision['id']!=revision['source_id']+':'+digest({k:v for k,v in revision.items() if k not in {'id','retrieved_at'}})[:32]:
            raise ValueError('Source revision identity mismatch')
    if (digest(staged['manifest'])!=staged['manifest_hash']
            or staged['snapshot_id']!='nyc-'+staged['manifest_hash'][:32]
            or digest({'records':staged['records'],'matches':staged['matches']})!=staged['manifest']['content_hash']):
        raise ValueError('Staged content hash mismatch')
    sid=staged['snapshot_id']
    with connection(path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        existing=conn.execute('SELECT manifest_hash FROM data_snapshots WHERE id=?',(sid,)).fetchone()
        if existing:
            if existing[0]!=staged['manifest_hash']:
                raise ValueError('Snapshot ID collision')
            return {'status':'unchanged','snapshot_id':sid}
        previous=conn.execute('SELECT id FROM data_snapshots WHERE study_area_id=? ORDER BY published_at DESC,id LIMIT 1',(STUDY_AREA,)).fetchone()
        old={}
        if previous:
            old={(r[0],r[1]):r[2] for r in conn.execute('SELECT kind,id,payload FROM import_records WHERE snapshot_id=?',previous)}
        new={(r['kind'],r['id']):canonical(r) for r in staged['records']}
        diff={'added':len(new.keys()-old.keys()),'removed':len(old.keys()-new.keys()),
            'changed':sum(old[k]!=new[k] for k in new.keys()&old.keys()),'previous_snapshot_id':previous[0] if previous else None}
        now=datetime.now(timezone.utc).isoformat()
        for revision in staged['revisions']:
            payload=revision|{'retrieved_at':staged['retrieved_at']}
            SourceRevision.model_validate(payload)
            previous_source=conn.execute('SELECT payload FROM source_revisions WHERE id=?',(revision['id'],)).fetchone()
            if previous_source and {k:v for k,v in json.loads(previous_source[0]).items() if k!='retrieved_at'}!=revision:
                raise ValueError('Source revision ID collision or changed stored bytes')
            conn.execute('INSERT OR IGNORE INTO source_revisions VALUES(?,?,?,?)',
                (revision['id'],revision['source_id'],revision['raw_sha256'],canonical(payload)))
        conn.execute('INSERT INTO data_snapshots VALUES(?,?,?,?,?)',(sid,STUDY_AREA,staged['manifest_hash'],canonical(staged['manifest']),now))
        for revision in staged['revisions']:
            conn.execute('INSERT INTO snapshot_sources VALUES(?,?)',(sid,revision['id']))
        for r in staged['records']:
            conn.execute('INSERT INTO import_records VALUES(?,?,?,?,?,?,?,?,?,?)',
                (sid,r['kind'],r['id'],r['source_revision_id'],r['source_record_key'],*(r['bbox'] or [None]*4),canonical(r)))
        for m in staged['matches']:
            conn.execute('INSERT INTO geographic_matches VALUES(?,?,?,?,?,?,?,?)',
                (sid,m['id'],m['source_kind'],m['source_record_id'],m['target_kind'],m['target_road_id'],m['status'],canonical(m)))
        audit=staged['report']|{'retrieved_at':staged['retrieved_at'],'acquisition_hash':staged['acquisition_hash'],
            'refresh_diff':diff,'published_at':now,'allow_rejects':allow_rejects}
        conn.execute('INSERT INTO import_runs VALUES(?,?,?)',('run-'+digest([sid,now])[:32],'published',canonical(audit)))
    return {'status':'published','snapshot_id':sid,'refresh_diff':diff}
