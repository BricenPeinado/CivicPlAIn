"""Source-neutral municipal inspection records. Never accepted by v1 calculators."""
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import shape

Classification = Literal['official_observation', 'imported_administrative_record',
    'derived_calculation', 'planning_assumption', 'synthetic_fixture', 'unknown']


class SourceRevision(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    id: str
    source_id: str
    source_url: str
    endpoint: str
    raw_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    query: dict
    source_updated_at: int | dict | None
    source_crs: str
    cadence: str
    attribution: str
    schema_fingerprint: str = Field(pattern=r'^[0-9a-f]{64}$')
    dictionary_url: str
    dictionary_sha256: str
    license: dict
    terms_urls: list[str]
    terms_review_version: str
    adapter_version: str
    release_note: str
    raw_page_checksums: dict[str,str]
    retrieved_at: str | None = None


class GeographicMatch(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    id: str
    source_kind: Literal['condition','permit']
    source_record_id: str
    target_kind: Literal['road']
    target_road_id: str | None
    status: Literal['matched','ambiguous','unmatched']
    method: Literal['reviewed-candidates-v1']
    tolerance_m: Literal[5]
    metric_crs: Literal['EPSG:32618']
    candidates: list[dict]
    decision: dict | None
    reason: str = Field(min_length=1)
    confidence: Literal['human_reviewed','unconfirmed']

    @model_validator(mode='after')
    def consistent_status(self):
        if (self.status=='matched') != (self.target_road_id is not None):
            raise ValueError('Matched status requires a target; other statuses forbid it')
        if self.target_road_id is not None and (self.decision is None or self.confidence!='human_reviewed'
                or self.target_road_id not in {c.get('road_id') for c in self.candidates}):
            raise ValueError('Accepted candidate requires review evidence')
        if self.status=='unmatched' and self.candidates:
            raise ValueError('Unmatched record cannot have eligible candidates')
        return self


class MunicipalRecord(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    contract_version: Literal['municipal-record-v2'] = 'municipal-record-v2'
    id: str = Field(min_length=1,max_length=150)
    kind: Literal['road', 'condition', 'permit', 'context']
    source_revision_id: str
    source_record_key: str
    classification: Classification
    geometry: dict | None
    bbox: tuple[float, float, float, float] | None
    raw_identifiers: dict[str, str | None]
    values: dict
    field_classifications: dict[str, Classification]
    unknown_reasons: dict[str, str]
    lineage: dict
    field_provenance: dict[str, dict]
    limitations: list[str]
    contains_synthetic: bool = False
    contains_assumptions: bool = False

    @model_validator(mode='after')
    def validate_geometry(self):
        if set(self.values) != set(self.field_classifications):
            raise ValueError('Every value requires its field classification')
        if not set(self.values)<=set(self.field_provenance):
            raise ValueError('Every value requires field provenance')
        if any(v is None and self.field_classifications[k] != 'unknown'
               for k, v in self.values.items()):
            raise ValueError('Null values must be classified unknown')
        if any(self.values.get(k) is None and k not in self.unknown_reasons
               for k in self.values):
            raise ValueError('Unknown values require a reason')
        if self.geometry is None:
            if self.bbox is not None:
                raise ValueError('Unlocated records have no bbox')
        else:
            g = shape(self.geometry)
            allowed = {'LineString', 'MultiLineString'} if self.kind in {'road', 'condition', 'context'} else {
                'Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon'}
            if g.geom_type not in allowed or g.is_empty or not g.is_valid:
                raise ValueError('Invalid or unsupported geometry')
            if g.geom_type in {'LineString', 'MultiLineString'} and g.length == 0:
                raise ValueError('Zero-length line')
            west, south, east, north = g.bounds
            if not all(math.isfinite(v) for v in g.bounds) or not (
                    -180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                raise ValueError('Geometry is not finite WGS84 longitude/latitude')
            # Pilot-specific sanity gate catches swapped longitude/latitude and wrong CRS.
            if not (-74.3 < west <= east < -73.6 and 40.4 < south <= north < 41):
                raise ValueError('Geometry outside NYC sanity envelope')
            if self.bbox is None or tuple(g.bounds) != self.bbox:
                raise ValueError('Geometry/bbox disagreement')
        return self
