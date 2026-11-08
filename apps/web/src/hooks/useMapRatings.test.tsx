import {act,renderHook} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {useMapRatings} from './useMapRatings';
import {getMapRatings} from '../services/standardized';
import {APIError} from '../services/http';
vi.mock('../services/standardized',()=>({getMapRatings:vi.fn()}));
afterEach(()=>vi.useRealTimers());
it('keeps an incompatible snapshot disabled across pans until explicit retry',async()=>{
 vi.useFakeTimers();vi.mocked(getMapRatings).mockRejectedValueOnce(new APIError('snapshot mismatch','STANDARDIZED_SNAPSHOT_MISMATCH',409)).mockResolvedValue([]);
 const a:[number,number,number,number]=[-74.01,40.71,-74,40.72],b:[number,number,number,number]=[-74.02,40.71,-74.01,40.72];
 const hook=renderHook(({bounds,retry})=>useMapRatings('snapshot',bounds,retry),{initialProps:{bounds:a,retry:0}});
 await act(async()=>{await vi.advanceTimersByTimeAsync(181);});expect(hook.result.current.error).toBe('snapshot mismatch');
 hook.rerender({bounds:b,retry:0});await act(async()=>{await vi.advanceTimersByTimeAsync(181);});expect(getMapRatings).toHaveBeenCalledOnce();
 hook.rerender({bounds:b,retry:1});await act(async()=>{await vi.advanceTimersByTimeAsync(181);});expect(getMapRatings).toHaveBeenCalledTimes(2);expect(hook.result.current.error).toBe('');
});
