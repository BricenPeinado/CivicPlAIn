"""Verified November 2026 source mappings. Preserve missing/unmatched source rows."""
from datetime import datetime
from decimal import Decimal

from shapely.geometry import box, shape
from shapely.errors import GEOSException

from app.ingestion.registry import PILOT, CONTEXT
from app.schemas.municipal import MunicipalRecord
from app.services.municipal_data import digest, geometry

OBS = 'official_observation'
ADMIN = 'imported_administrative_record'
FIELDS={
    'road':{'name':'Street','feature_type':'FeatureTyp'},
    'condition':{'on_street':'onstreetna','from_street':'fromstreet','to_street':'tostreetna',
        'rating':'systemrating','inspection_at':'inspection','non_rating_reason':'nonratingreason',
        'direction':'direction','road_type':'road_type'},
    'permit':{'on_street':'onstreetname','from_street':'fromstreetname','to_street':'tostreetname',
        'permit_status':'permitstatusshortdesc','permit_type':'permittypedesc','issued_at':'permitissuedate',
        'valid_from':'issuedworkstartdate','valid_to':'issuedworkenddate','modified_at':'modifiedon'},
    'context':{'feature_code':'feat_code','status':'status'}}


def text(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValueError('Identifier/text must remain a string')
    return value


def timestamp(value):
    value = text(value)
    if value is not None:
        datetime.fromisoformat(value)
    return value


def record(kind, key, revision, geom, identifiers, values, classification, lineage):
    raw=lineage.get('raw_fields',lineage.get('raw_attributes',{}))
    provenance={k:{'source_revision_id':revision,'source_record_key':key,'source_field':FIELDS[kind].get(k),
        'original_value':raw.get(FIELDS[kind].get(k)), 'method_version':None,'original_unit':None}
        for k in values}
    provenance['geometry']={'source_revision_id':revision,'source_record_key':key,
        'source_field':'geometry' if kind=='road' else 'wkt' if kind=='permit' else 'the_geom',
        'classification':'derived_calculation' if kind=='road' else 'unknown' if geom is None else classification,
        'method_version':'pyproj-2263-to-4326-always-xy-v1' if kind=='road' else None,
        'original_unit':'US survey foot' if kind=='road' else 'unknown' if kind=='permit' else 'degree'}
    result = MunicipalRecord(id=kind+'-'+digest([revision.split(':')[0], key])[:24], kind=kind,
        source_record_key=key, source_revision_id=revision, classification=classification,
        geometry=geom, bbox=shape(geom).bounds if geom else None, raw_identifiers=identifiers,
        values=values, field_classifications={k: classification if v is not None else 'unknown' for k,v in values.items()},
        unknown_reasons={k:'Not supplied or not interpretable in this source' for k,v in values.items() if v is None},
        lineage=lineage,field_provenance=provenance,
        limitations=['Published source information does not establish accuracy, completeness or excavation safety.'])
    return result.model_dump(mode='json')


def adapt(kind, row, revision):
    if kind == 'lion':
        a = row['attributes']
        if a.get('LBoro') != 1 and a.get('RBoro') != 1:
            raise ValueError('Non-Manhattan LION row')
        # FeatureTyp 0 is regular street; other linear features remain out of road scope.
        if a.get('FeatureTyp') != '0':
            return None
        segment = text(a.get('SegmentID'))
        if not segment:
            raise ValueError('Missing LION SegmentID')
        # SegmentID repeats in this official service. OID is the actual export row key.
        key = segment+':'+str(a['OBJECTID'])
        g = geometry({'type':'MultiLineString', 'coordinates':row['geometry']['paths']}, 'EPSG:2263')
        return record('road', key, revision, g,
            {'segment_id':segment, 'object_id':str(a['OBJECTID']), 'street_code':text(a.get('StreetCode'))},
            {'name':text(a.get('Street')), 'feature_type':a['FeatureTyp'], 'utility_coordinates':None,
             'utility_depth_m':None, 'cost':None, 'construction_schedule':None}, OBS,
            {'geometry_transform':'EPSG:2263 US survey feet -> EPSG:4326; always_xy', 'raw_geometry':row['geometry'],
             'raw_attributes':a})
    if kind == 'pavement':
        if row.get('boroughname') != 'Manhattan':
            raise ValueError('Non-Manhattan pavement row')
        oft = text(row.get('oftcode'))
        if oft is not None and (len(oft) != 18 or not oft.isdigit()):
            raise ValueError('Invalid OFT identifier')
        inspection = timestamp(row.get('inspection'))
        rating = text(row.get('systemrating'))
        if rating is not None and (not Decimal(rating).is_finite() or not 0 <= Decimal(rating) <= 10):
            raise ValueError('Invalid pavement rating')
        # No source primary key: preserve direction/type/multipass/date at observation grain.
        key = text(row.get('source_row_id')) or digest(row)
        g = geometry(row['the_geom']) if row.get('the_geom') else None
        return record('condition', key, revision, g, {'oftcode':oft,'source_row_id':text(row.get('source_row_id'))},
            {'on_street':text(row.get('onstreetna')), 'from_street':text(row.get('fromstreet')),
             'to_street':text(row.get('tostreetna')), 'rating':rating, 'inspection_at':inspection,
             'non_rating_reason':text(row.get('nonratingreason')), 'direction':text(row.get('direction')),
             'road_type':text(row.get('road_type')), 'official_category':None}, OBS,
            {'rating_definition':'DOT SystemRating 1.00–10.00; dictionary also lists poor 0–3. Preserve raw decimals; category unresolved.',
             'timestamp_semantics':'Source inspection local/floating datetime; no timezone inferred', 'raw_fields':row})
    if kind == 'permits':
        if str(row.get('boroughname','')).upper() != 'MANHATTAN':
            raise ValueError('Non-Manhattan permit row')
        key = text(row.get('permitnumber'))
        if not key:
            raise ValueError('Missing permit primary key')
        oft = text(row.get('oftcode'))
        if oft is not None and (len(oft) != 18 or not oft.isdigit()):
            raise ValueError('Invalid OFT identifier')
        start, end = timestamp(row.get('issuedworkstartdate')), timestamp(row.get('issuedworkenddate'))
        if start and end and datetime.fromisoformat(start) > datetime.fromisoformat(end):
            raise ValueError('Reversed permit validity dates')
        # WKT has no declared source CRS. Retain it without guessing geometry or a point on a road.
        return record('permit', key, revision, None,
            {'permit_number':key, 'oftcode':oft, 'application_tracking_id':text(row.get('applicationtrackingid'))},
            {'on_street':text(row.get('onstreetname')), 'from_street':text(row.get('fromstreetname')),
             'to_street':text(row.get('tostreetname')), 'permit_status':text(row.get('permitstatusshortdesc')),
             'permit_type':text(row.get('permittypedesc')), 'issued_at':timestamp(row.get('permitissuedate')),
             'valid_from':start, 'valid_to':end, 'modified_at':timestamp(row.get('modifiedon')),
             'work_started':None, 'confirmed_construction_dates':None, 'utility_coordinates':None,
             'utility_depth_m':None, 'cost':None}, ADMIN,
            {'raw_wkt':text(row.get('wkt')), 'raw_location_geometry':text(row.get('locationgeometry')),
             'geometry_reason':'Source WKT CRS unspecified; not transformed or used for geographic confirmation',
             'timestamp_semantics':'Permit effectiveness/expiration, not confirmed construction dates; floating datetime',
             'raw_fields':row})
    if kind == 'context':
        key = str(row['source_id'])
        return record('context', key, revision, geometry(row['the_geom']), {'source_id':key},
            {'feature_code':text(row.get('feat_code')), 'status':text(row.get('status'))}, OBS,
            {'raw_fields':row, 'meaning':'Planimetric shoreline context; not a surveyed excavation boundary'})
    raise ValueError('Unknown adapter')


def normalize(kind, rows, revision):
    records, rejects, duplicates, excluded = {}, [], 0, 0
    scope = box(*(CONTEXT if kind == 'context' else PILOT))
    for index, row in enumerate(rows):
        try:
            item = adapt(kind, row, revision)
            if item is None or (item['geometry'] and not shape(item['geometry']).intersects(scope)):
                excluded += 1
                continue
            key = item['id']
            if key in records:
                if records[key] != item:
                    raise ValueError('Conflicting duplicate source identity')
                duplicates += 1
            records[key] = item
        except (ValueError, KeyError, TypeError, ArithmeticError, GEOSException) as exc:
            rejects.append({'row_index':index, 'code':type(exc).__name__, 'reason':str(exc)[:180]})
    return sorted(records.values(), key=lambda r:r['id']), rejects, duplicates, excluded
