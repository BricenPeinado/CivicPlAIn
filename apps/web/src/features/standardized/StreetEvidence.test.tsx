import {render,screen,waitFor,fireEvent} from '@testing-library/react';
import {beforeEach,it,expect,vi} from 'vitest';
import {StreetEvidence} from './StreetEvidence';
import {getStandardized} from '../../services/standardized';
vi.mock('../../services/standardized');
const profile={road_id:'road-a',street_name:'TEST STREET',latest_rating:4.91,display_condition:'Fair',latest_inspection_at:'2026-03-14',street_observation_count:53,permits_on_street:33};
beforeEach(()=>vi.mocked(getStandardized).mockImplementation(async (_s,r,kind)=>({data:kind?[]:{...profile,road_id:r},meta:{total_matching:0,next_offset:null}} as any)));
it('shows indicative values and separate permit counts; expands reads on demand',async()=>{
 render(<StreetEvidence snapshot="snapshot" road="road-a"/>);
 expect(await screen.findByText('4.91')).toBeVisible();expect(screen.getByText('Fair')).toBeVisible();
 expect(screen.getByText('53 named-street pavement observations')).toBeVisible();expect(screen.getByText('33')).toBeVisible();
 expect(screen.getByText(/not a verified measurement/)).toBeVisible();
 expect(getStandardized).toHaveBeenCalledTimes(1);
 fireEvent.click(screen.getByText('Permit details'));
 await waitFor(()=>expect(getStandardized).toHaveBeenCalledWith('snapshot','road-a','permits',0,expect.any(AbortSignal)));
 expect(await screen.findByText('No permits naming this street in this dataset.')).toBeVisible();
});
it('suppresses late responses from a previous street',async()=>{
 let resolve!:(r:any)=>void;
 vi.mocked(getStandardized).mockImplementationOnce(()=>new Promise(r=>{resolve=r;}));
 const view=render(<StreetEvidence snapshot="snapshot" road="road-a"/>);
 view.rerender(<StreetEvidence snapshot="snapshot" road="road-b"/>);
 await screen.findByText('4.91');resolve({data:{...profile,latest_rating:9.99},meta:{}});
 await waitFor(()=>expect(screen.queryByText('9.99')).not.toBeInTheDocument());
});
it('shows explicit failures with retry and no fabricated unknown counts',async()=>{
 vi.mocked(getStandardized).mockRejectedValueOnce(new Error('Snapshot mismatch'));
 render(<StreetEvidence snapshot="snapshot" road="road-a"/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('Snapshot mismatch');
 expect(screen.queryByText('0')).not.toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Retry street evidence'}));expect(await screen.findByText('4.91')).toBeVisible();
});
