import {useEffect, useRef, useState} from 'react';
import {getStandardized, type Profile, type Pavement, type StreetPermit, type Result} from '../../services/standardized';
import {timeMap} from '../map/performance';
import {sourceDate, shown} from '../../components/MunicipalEvidence';

function RecentRecords({snapshot,road,kind}: {snapshot:string;road:string;kind:'pavement'|'permits'}) {
  const [page,setPage]=useState<Result<(Pavement|StreetPermit)[]>|null>(null);
  const [open,setOpen]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState('');
  const active=useRef<AbortController|null>(null);
  useEffect(()=>()=>active.current?.abort(),[]);
  const load=(offset=0)=>{
    active.current?.abort();const ac=new AbortController();active.current=ac;setLoading(true);setError('');
    getStandardized<(Pavement|StreetPermit)[]>(snapshot,road,kind,offset,ac.signal).then(result=>{
      if(!ac.signal.aborted)setPage(previous=>({...result,data:offset&&previous?[...previous.data,...result.data]:result.data}));
    }).catch(e=>{if(!ac.signal.aborted)setError(e.message);}).finally(()=>{if(!ac.signal.aborted)setLoading(false);});
  };
  return <details onToggle={e=>{setOpen(e.currentTarget.open);if(e.currentTarget.open&&!page&&!loading&&!error)load();}}>
    <summary>{kind==='pavement'?'Recent pavement observations':'Permit details'}</summary>
    {open&&<>{loading&&<p role="status">Loading {kind}…</p>}{error&&<p role="alert">{error}<button onClick={()=>load(page?.meta.next_offset||0)}>Retry {kind}</button></p>}
    {page&&!page.data.length&&<p>No {kind==='pavement'?'named-street observations':'permits naming this street'} in this dataset.</p>}
    {page?.data.map(record=>'observation_id' in record?<article key={record.observation_id}>
      <strong>{record.rating??'Unreported'} / 10 · {record.display_condition||'Unclassified'}</strong><p>Observed {sourceDate(record.inspection_at)}</p>
      <p>On {shown(record.on_street)} · From {shown(record.from_street)} · To {shown(record.to_street)}</p>{record.non_rating_reason&&<p>Non-rating reason: {record.non_rating_reason}</p>}
      <details><summary>Observation source</summary><p>{record.observation_id} · {record.source_revision_id}</p></details>
    </article>:<article key={record.permit_id}>
      <strong>{shown(record.permit_number)}</strong><p>{shown(record.permit_type)} · {shown(record.permit_status)}</p>
      <p>On {shown(record.on_street)} · From {shown(record.from_street)} · To {shown(record.to_street)}</p>
      <p>Issued {sourceDate(record.issue_date)} · Valid from {sourceDate(record.valid_from)} · Valid to {sourceDate(record.valid_to)}</p>
      <details><summary>Permit source</summary><p>{record.permit_id} · {record.source_revision_id}</p></details>
    </article>)}
    {page?.meta.next_offset!=null&&<button disabled={loading} onClick={()=>load(page.meta.next_offset!)}>Load more {kind==='pavement'?'observations':'permits'}</button>}</>}
  </details>;
}

export function StreetEvidence({snapshot,road}: {snapshot:string;road:string}) {
  const [profile,setProfile]=useState<Profile|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
  useEffect(()=>{
    const started=performance.now();const ac=new AbortController();setProfile(null);setError('');
    getStandardized<Profile>(snapshot,road,undefined,0,ac.signal).then(r=>{if(!ac.signal.aborted){setProfile(r.data);timeMap('street.rating',started);}}).catch(e=>{if(!ac.signal.aborted)setError(e.message);});
    return()=>ac.abort();
  },[snapshot,road,retry]);
  if(error)return <section role="alert"><h2>Street evidence unavailable</h2><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry street evidence</button></section>;
  if(!profile||profile.road_id!==road)return <p role="status">Loading named-street evidence…</p>;
  return <section aria-label="Standardized street evidence">
    <h2>Indicative pavement condition</h2><strong className="rating">{profile.latest_rating??'Unknown'}{profile.latest_rating!==null&&<small> / 10</small>}</strong>
    <p><strong>{profile.latest_rating===null || profile.display_condition==='Unclassified'?'Unknown':profile.display_condition}</strong> · Latest street observation: {sourceDate(profile.latest_inspection_at)}</p>
    <p>{profile.street_observation_count} named-street pavement observations</p>
    <p>Shared street-level evidence for {profile.street_name}; not a verified measurement of the selected segment. Indicative bands are application categories, not official NYC DOT grades.</p>
    <RecentRecords key={`${snapshot}:${road}:pavement`} snapshot={snapshot} road={road} kind="pavement"/>
    <h2>Permits naming this street</h2><p><strong>{profile.permits_on_street}</strong> permits naming this street as the work street</p>
    <p>On-street matches only; cross-street mentions are excluded. These records do not establish work on this segment. Issue and validity dates are administrative, not actual construction schedules.</p>
    <RecentRecords key={`${snapshot}:${road}:permits`} snapshot={snapshot} road={road} kind="permits"/>
    <details><summary>Street source and selected geometry</summary><p>Road ID: {profile.road_id} · LION {profile.segment_id} · Row {profile.object_id}</p><p>Road source: {profile.source_revision_id}</p><p>{profile.display_basis}</p><p>Named-street associations and indicative bands: derived calculation. Original ratings: observations; permits: administrative records. No indicative rating is supplied to repair suitability or prioritization.</p><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(profile.geometry)}</pre></details>
  </section>;
}
