import { onlineBasemap } from '../features/map/mapStyle';
import { useState } from 'react';
import { Icon } from './Icon';
import type { LayerState } from '../hooks/useMunicipalData';
export function MapToolbar({ query, setQuery, listOpen, setListOpen, layers, setLayers, synthetic = false }: {
  query: string; setQuery: (v: string) => void; listOpen: boolean; setListOpen: (v: boolean) => void;
  layers?: LayerState; setLayers?: (v: LayerState) => void; synthetic?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return <div className="map-tools" onKeyDown={e => { if (e.key === 'Escape') { setOpen(false); setListOpen(false); } }}>
    <div className="search-control"><Icon name="search"/><input aria-label="Find road segments" maxLength={100} placeholder="Search streets or identifiers" value={query} onClick={() => setListOpen(true)} onChange={e => { setQuery(e.target.value); setListOpen(true); }}/><button aria-label={listOpen ? 'Close street list' : 'Open street list'} aria-expanded={listOpen} onClick={() => setListOpen(!listOpen)}><Icon name={listOpen ? 'close' : 'list'}/></button></div>
    {layers && setLayers && <div className="layer-control"><button className={open ? 'active' : ''} aria-expanded={open} onClick={() => setOpen(!open)}><Icon name="layers"/>Layers</button>{open && <fieldset><legend>Visible map layers</legend>{(Object.keys(layers) as (keyof LayerState)[]).map(key => <label key={key}><input type="checkbox" checked={layers[key]} disabled={key === 'basemap' && !onlineBasemap} onChange={e => setLayers({ ...layers, [key]: e.target.checked })}/>{{ streets: 'Official streets', conditions: 'Pavement observations', permits: 'Located permits', shoreline: 'Shoreline', basemap: 'Street basemap' }[key]}</label>)}<p>Pavement lines are inspection geometries. Nearby records are not confirmed road links or conflicts.</p></fieldset>}</div>}
    {synthetic && <span className="synthetic-map-label">Synthetic geometry</span>}
  </div>;
}
