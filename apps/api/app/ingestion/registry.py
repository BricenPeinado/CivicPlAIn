"""Reviewed fixed origins. No caller-supplied URL or inferred open-data license."""
from pathlib import Path
import json

PILOT = [-74.020, 40.700, -73.985, 40.725]
CONTEXT = [-74.030, 40.695, -73.980, 40.730]
STUDY_AREA = 'lower-manhattan-pilot-v2'
VERSION = 'nyc-adapters-1'
LION = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/LION/FeatureServer/0'
TERMS = 'https://data.cityofnewyork.us/stories/s/Terms-of-Use/k9k7-3cje'
CITY_TERMS = 'https://www.nyc.gov/main/terms-of-use'
DOT_TERMS = 'https://www.nyc.gov/html/dot/html/about/datafeeds.shtml'
SOURCES = {
    'lion': {'id': 'dcp-lion-arcgis', 'catalog': 'https://data.cityofnewyork.us/d/2v4z-66xt',
        'metadata': LION+'?f=json', 'endpoint': LION+'/query', 'crs': 'EPSG:2263',
        'cadence': 'DCP catalog quarterly; ArcGIS revision independent of catalog edition',
        'attribution': 'NYC Department of City Planning',
        'dictionary': 'https://data.cityofnewyork.us/api/views/2v4z-66xt/files/0bee8766-28f5-4583-81ee-f310d41b43a2?download=true&filename=data_dictionary.xlsx'},
    'pavement': {'id':'6yyb-pb25', 'crs':'EPSG:4326', 'cadence':'Monthly publication; underlying data daily',
        'attribution':'NYC Department of Transportation',
        'dictionary':'https://data.cityofnewyork.us/api/views/6yyb-pb25/files/0582f80f-e210-4d2d-91e2-9e0a14917ee5?download=true&filename=Data+Dictionary+-+StreetPavementRating_Final.xlsx'},
    'permits': {'id':'tqtj-sjs8', 'crs':'unknown (WKT has no declared CRS)', 'cadence':'Daily',
        'attribution':'NYC Department of Transportation',
        'dictionary':'https://data.cityofnewyork.us/api/views/tqtj-sjs8/files/7e404c9a-4419-4c05-a321-03c3d9e7cfbc?download=true&filename=Street_Construction_Permit_Collections_Data_Dictionary2025.xlsx'},
    'context': {'id':'59xk-wagz', 'crs':'EPSG:4326', 'cadence':'As needed',
        'attribution':'NYC Office of Technology and Innovation',
        'dictionary':'https://data.cityofnewyork.us/api/views/59xk-wagz/files/ad5e5ca9-8dd7-4e7a-9e29-c34ed67f00a8?download=true&filename=Shoreline_Data+Dictionary.xlsx'},
}
for key, source in SOURCES.items():
    if key != 'lion':
        source.update(catalog=f'https://data.cityofnewyork.us/d/{source["id"]}',
            metadata=f'https://data.cityofnewyork.us/api/views/{source["id"]}.json',
            endpoint=f'https://data.cityofnewyork.us/resource/{source["id"]}.json')
SCHEMAS = json.loads(Path(__file__).with_name('source_schemas.json').read_text())


def schema(metadata, kind):
    return sorted([[c['name'], c['type']] for c in metadata['fields']] if kind == 'lion' else
        [[c['fieldName'], c['dataTypeName']] for c in metadata['columns'] if not c['fieldName'].startswith(':')])
