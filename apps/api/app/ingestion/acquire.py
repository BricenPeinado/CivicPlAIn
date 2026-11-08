"""Bounded fixed-source HTTPS acquisition. No redirects, secrets, ZIP extraction or startup I/O."""
import hashlib
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from app.ingestion.registry import SOURCES, SCHEMAS, PILOT, CONTEXT, TERMS, CITY_TERMS, DOT_TERMS, schema
from app.services.municipal_data import canonical, digest

ALLOWED_HOSTS = {'data.cityofnewyork.us', 'services5.arcgis.com', 'www.arcgis.com', 'www.nyc.gov'}
MAX_BYTES = 25_000_000
PERMIT_FIELDS = ['permitnumber','applicationtrackingid','sequencenumber','permitstatusshortdesc',
    'permittypedesc','permitissuedate','issuedworkstartdate','issuedworkenddate','boroughname',
    'onstreetname','fromstreetname','tostreetname','modifiedon','oftcode','wkt','locationgeometry']
LION_FIELDS = ['OBJECTID','SegmentID','Street','FeatureTyp','LBoro','RBoro','StreetCode','NodeIDFrom','NodeIDTo']


def fetch(url, path):
    """Use system curl's verified HTTPS trust store (macOS Python store may differ).

    Fail closed on redirects/status/timeouts/oversize; no shell, proxy URL override or --insecure.
    """
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port:
        raise ValueError('Unapproved source URL')
    result = subprocess.run(['/usr/bin/curl', '--fail', '--silent', '--show-error',
        '--proto', '=https', '--max-time', '30', '--retry', '2', '--retry-delay', '1', '--retry-max-time', '60', '--max-filesize', str(MAX_BYTES),
        '--output', str(path), '--write-out', '%{http_code}', url], capture_output=True, text=True)
    if result.returncode or result.stdout != '200':
        raise ValueError('Official source acquisition failed; no snapshot published')
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Empty or oversized response')
    return raw


def json_fetch(url, path):
    raw = fetch(url, path)
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ValueError('Source did not return JSON') from None
    if isinstance(value, dict) and ('error' in value or 'errorCode' in value):
        raise ValueError('Source returned API error')
    return value


def source_stamp(meta, kind):
    return meta.get('editingInfo') if kind == 'lion' else meta.get('rowsUpdatedAt')


def paged_socrata(kind, where, folder, cap, prefix=''):
    source = SOURCES[kind]
    params = {'$where':where}
    count = int(json_fetch(source['endpoint']+'?'+urlencode(params|{'$select':'count(*)'}), folder/f'{prefix}count-before.json')[0]['count'])
    if count > cap:
        raise ValueError(f'{kind} selection exceeds configured safety cap; narrow the scope')
    rows = []
    for offset in range(0, count, 1000):
        query = params | {'$limit':1000, '$offset':offset, '$order':':id'}
        if kind == 'permits':
            query['$select'] = ','.join(PERMIT_FIELDS)
        elif kind == 'pavement':
            query['$select'] = '*, :id AS source_row_id'
        page = json_fetch(source['endpoint']+'?'+urlencode(query), folder/f'page-{prefix}{offset:06d}.json')
        if not isinstance(page, list) or len(page) != min(1000,count-offset):
            raise ValueError('Truncated source page')
        rows.extend(page)
    after = int(json_fetch(source['endpoint']+'?'+urlencode(params|{'$select':'count(*)'}), folder/f'{prefix}count-after.json')[0]['count'])
    if count != after:
        raise ValueError('Source changed during pagination; reacquire')
    return rows, params


def acquire(output: Path, permit_since: str):
    since = date.fromisoformat(permit_since)
    if since.year < 2020 or since > date.today():
        raise ValueError('Permit issue lower bound must be 2020 or later and not future')
    # Never overwrite a prior evidence bundle, including a failed one.
    output.mkdir(parents=True, exist_ok=False)
    terms = {}
    for key, url in [('portal',TERMS)]:
        raw = fetch(url, output/f'terms-{key}.html')
        if b'<html' not in raw.lower() and b'<!doctype' not in raw.lower():
            raise ValueError('Invalid terms response')
        terms[key] = {'url':url, 'sha256':hashlib.sha256(raw).hexdigest()}
    terms['city']={'url':CITY_TERMS,'review':'Official page reviewed 2026-11-07; automated download returns 403; no raw-page hash claimed'}
    terms['dot']={'url':DOT_TERMS,'review':'Official page reviewed 2026-11-07; automated download returns 403; no raw-page hash claimed'}
    bundle = {'format':'civicplain-nyc-acquisition-1', 'retrieved_at':datetime.now(timezone.utc).isoformat(),
        'study_area':'lower-manhattan-pilot-v2', 'bbox':PILOT, 'context_bbox':CONTEXT,
        'permit_since':permit_since, 'terms':terms, 'sources':{}}
    for kind, source in SOURCES.items():
        folder = output/kind
        folder.mkdir()
        meta = json_fetch(source['metadata'],folder/'metadata.json')
        if schema(meta,kind) != SCHEMAS[kind]:
            raise ValueError(f'{kind} schema drift; review adapter before acquisition')
        if kind == 'lion':
            item = json_fetch('https://www.arcgis.com/sharing/rest/content/items/db6fdacfc5ff44e7a244e2f798d98a7d?f=json',folder/'item.json')
            if item.get('owner') != 'DCP_GIS' or item.get('orgId') != 'GfwWNkhOj9bNBqoJ':
                raise ValueError('Unrecognized LION publisher')
            sr = meta['extent']['spatialReference']
            if sr.get('latestWkid',sr.get('wkid')) != 2263:
                raise ValueError('LION CRS changed')
            catalog = json_fetch('https://data.cityofnewyork.us/api/views/2v4z-66xt.json',folder/'catalog.json')
            bundle['lion_catalog_description'] = catalog.get('description')
        dictionary = fetch(source['dictionary'],folder/'dictionary.xlsx')
        if not dictionary.startswith(b'PK'):
            raise ValueError('Invalid source dictionary')
        if kind == 'lion':
            params = {'f':'json','where':"(LBoro=1 OR RBoro=1) AND FeatureTyp='0'", 'geometry':','.join(map(str,PILOT)),
                'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'}
            ids = json_fetch(source['endpoint']+'?'+urlencode(params|{'returnIdsOnly':'true'}),folder/'ids.json').get('objectIds',[])
            if not ids or len(ids)>10000:
                raise ValueError('Invalid/oversized LION selection')
            rows=[]
            for offset in range(0,len(ids),100):
                page=json_fetch(source['endpoint']+'?'+urlencode({'f':'json','objectIds':','.join(map(str,sorted(ids)[offset:offset+100])),
                    'outFields':','.join(LION_FIELDS),'returnGeometry':'true','outSR':2263}),folder/f'page-{offset:06d}.json')
                if page.get('exceededTransferLimit') or len(page.get('features',[])) != len(ids[offset:offset+100]):
                    raise ValueError('Truncated LION response')
                rows.extend(page['features'])
        else:
            bounds = CONTEXT if kind=='context' else PILOT
            w,s,e,n=bounds
            polygon=f'POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))'
            where=f"intersects(the_geom, '{polygon}')"
            if kind=='pavement':
                where="boroughname='Manhattan' AND "+where
            if kind=='permits':
                streets=sorted({r['attributes']['Street'] for r in bundle['sources']['lion']['rows'] if r['attributes'].get('Street')})
                rows,queries=[],[]
                for start in range(0,len(streets),20):
                    names=','.join("'"+name.replace("'","''")+"'" for name in streets[start:start+20])
                    where=f"boroughname='MANHATTAN' AND permitissuedate >= '{since.isoformat()}T00:00:00' AND onstreetname in({names})"
                    batch,query=paged_socrata(kind,where,folder,20000-len(rows),prefix=f'{start:04d}-')
                    rows.extend(batch)
                    queries.append(query)
                params={'partitions':queries}
            else:
                rows,params=paged_socrata(kind,where,folder,10000)
        after=json_fetch(source['metadata'],folder/'metadata-after.json')
        if source_stamp(meta,kind)!=source_stamp(after,kind) or schema(after,kind)!=SCHEMAS[kind]:
            raise ValueError('Source revision changed during acquisition; reacquire')
        if not rows:
            raise ValueError(f'{kind} returned zero records; review coverage before accepting absence')
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}
        bundle['sources'][kind]={'rows':rows, 'metadata':meta, 'query':params,'files':files,
            'source_updated_at':source_stamp(meta,kind), 'schema_fingerprint':digest(SCHEMAS[kind]),
            'dictionary_sha256':hashlib.sha256(dictionary).hexdigest(),
            'license':{'identifier':meta.get('licenseId'), 'terms':terms,
                'source_disclaimer':item.get('licenseInfo') if kind=='lion' else None,
                'application_disclaimer_url':DOT_TERMS+'#disclaimer' if kind in {'pavement','permits'} else None,
                'application_disclaimer_required':kind in {'pavement','permits'},
                'note':'No standardized license identifier supplied; NYC terms and agency disclaimers apply'},
            'source':source}
    (output/'acquisition.json').write_text(canonical(bundle)+'\n')
    return {k:len(v['rows']) for k,v in bundle['sources'].items()}
