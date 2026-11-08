import { onlineBasemap } from '../features/map/mapStyle';
import { useRef, useState } from 'react';
import { Icon } from './Icon';
import type { LayerState } from '../hooks/useMunicipalData';
export function MapToolbar({ query, setQuery, listOpen, setListOpen, layers, setLayers, synthetic = false, ratingsUnavailable = '' }: {
  query: string; setQuery: (v: string) => void; listOpen: boolean; setListOpen: (v: boolean) => void;
  layers?: LayerState; setLayers?: (v: LayerState) => void; synthetic?: boolean; ratingsUnavailable?: string;
}) {
  const [open, setOpen] = useState(false);
  const layerButton = useRef<HTMLButtonElement>(null);
  return <div className="map-tools" onKeyDown={e => { if (e.key === 'Escape') { setOpen(false); setListOpen(false); if (open) { e.stopPropagation(); layerButton.current?.focus(); } } }}>
    <div className="search-control"><Icon name="search"/><input aria-label="Find road segments" maxLength={100} placeholder="Search streets or identifiers" value={query} onClick={() => setListOpen(true)} onChange={e => { setQuery(e.target.value); setListOpen(true); }}/><button aria-label={listOpen ? 'Close street list' : 'Open street list'} aria-expanded={listOpen} onClick={() => setListOpen(!listOpen)}><Icon name={listOpen ? 'close' : 'list'}/></button></div>
    {layers && setLayers && <div className="layer-control"><button ref={layerButton} className={open ? 'active' : ''} aria-expanded={open} onClick={() => setOpen(!open)}><Icon name="layers"/>Layers</button>{open && <fieldset><legend>Visible map layers</legend>{(Object.keys(layers) as (keyof LayerState)[]).map(key => <label key={key}><input type="checkbox" checked={!!layers[key] && !(key === 'ratings' && !!ratingsUnavailable)} disabled={key === 'basemap' && !onlineBasemap || key === 'ratings' && !!ratingsUnavailable} onChange={e => setLayers({ ...layers, [key]: e.target.checked })}/>{{ streets: 'Official street geometry', ratings: 'Indicative Street Ratings', conditions: 'Pavement observations', permits: 'Permit locations', shoreline: 'Shoreline', basemap: 'Detailed basemap' }[key]}</label>)}{ratingsUnavailable && <p role="status">Indicative ratings unavailable: {ratingsUnavailable}</p>}{!onlineBasemap && <p>Local basemap mode. Set VITE_BASEMAP=osm for online detail.</p>}<p>Pavement lines are inspection geometries. Nearby records are not confirmed road links or conflicts.</p></fieldset>}</div>}
    {synthetic && <span className="synthetic-map-label">Synthetic geometry</span>}
  </div>;
}
