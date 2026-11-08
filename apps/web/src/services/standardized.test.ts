import {beforeEach,it,expect,vi} from 'vitest';
import {getStandardized} from './standardized';
import {readMunicipal} from './municipal';
import {APIError} from './http';
vi.mock('./municipal',()=>({readMunicipal:vi.fn()}));
const result={data:{road_id:'road-a'},meta:{contract_version:'standardized-read-v1',snapshot_id:'snapshot-a',road_id:'road-a',association_basis:'on_street_name',verified_segment_condition:false}};
beforeEach(()=>vi.mocked(readMunicipal).mockResolvedValue(result));
it('binds exact snapshot/road and bounds paging at the separate read path',async()=>{
 await getStandardized('snapshot-a','road-a','permits',10);
 expect(readMunicipal).toHaveBeenCalledWith('/standardized/roads/road-a/permits?snapshot_id=snapshot-a&limit=10&offset=10',undefined);
});
it('rejects foreign profile and response contexts',async()=>{
 vi.mocked(readMunicipal).mockResolvedValueOnce({...result,data:{road_id:'road-b'}});
 await expect(getStandardized('snapshot-a','road-a')).rejects.toThrow('identity differs');
 vi.mocked(readMunicipal).mockResolvedValueOnce({...result,meta:{...result.meta,snapshot_id:'snapshot-b'}});
 await expect(getStandardized('snapshot-a','road-a')).rejects.toThrow('context differs');
 vi.mocked(readMunicipal).mockResolvedValueOnce({...result,data:[{road_id:'road-a'},{road_id:'road-b'}]});
 await expect(getStandardized('snapshot-a','road-a','permits')).rejects.toThrow('identity differs');
});
it('identifies an outdated API route separately from a missing road',async()=>{
 vi.mocked(readMunicipal).mockRejectedValueOnce(new APIError('Not Found','NOT_FOUND',404));
 await expect(getStandardized('snapshot-a','road-a')).rejects.toThrow('Restart the backend');
 vi.mocked(readMunicipal).mockRejectedValueOnce(new APIError('Standardized road not found','NOT_FOUND',404));
 await expect(getStandardized('snapshot-a','road-a')).rejects.toThrow('Standardized road not found');
});
