import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { AIAdvisor } from './AIAdvisor';
import { ReviewNote } from './ReviewNote';
import { explainContext, getAIStatus, saveReviewNote } from '../../services/api';
import type { AIContext, AIExplanation } from '../../types/ai';
vi.mock('../../services/api');
import { answer, meta } from './testData';
beforeEach(() => {
  vi.mocked(explainContext).mockResolvedValue({data:answer,meta});
  vi.mocked(getAIStatus).mockResolvedValue({data:{default_mode:'deterministic',provider_configured:false,configured_provider:'deterministic',model_label:null,timeout_seconds:8,max_output_tokens:1200,max_calls_per_hour:20,live_provider_verified:false,free_text_generation:false},meta});
});
it.each([
  [{type:'estimate',record_ids:['saved-estimate']},'Explain this estimate'],
  [{type:'conflict',record_ids:['saved-conflict']},'Explain this conflict'],
  [{type:'comparison',record_ids:['a','b','c']},'Explain tradeoffs'],
] as [AIContext,string][])('explain button sends only trusted context references for %s', async(context,label) => {
  const user=userEvent.setup();render(<AIAdvisor context={context} label={label}/>);
  expect(explainContext).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button',{name:label}));
  expect(await screen.findByRole('article',{name:'Grounded explanation'})).toHaveTextContent('DETERMINISTIC FALLBACK');
  expect(explainContext).toHaveBeenCalledWith(context,'deterministic',undefined,expect.any(AbortSignal));
  expect(screen.getByText('SYNTHETIC INPUTS')).toBeInTheDocument();
  expect(screen.getByText(/Fallback reason: not configured/)).toBeInTheDocument();
  expect(screen.getByText('Calculated facts and cost drivers')).toBeInTheDocument();
  expect(screen.getByText(/Recorded fields and assumptions/)).toBeInTheDocument();
  const links=screen.getAllByRole('link',{name:'Inspect source 1'});
  const target=links[0].getAttribute('href')!.slice(1);
  expect(document.getElementById(target)).toHaveTextContent('saved-estimate');
  await user.click(links[0]);
  expect(screen.getByText('Supporting evidence (1)').closest('details')).toHaveAttribute('open');
  expect(document.getElementById(target)).toHaveFocus();
});
it('submits a bounded question, optional provider mode, and transparent disclosure',async()=>{
  const user=userEvent.setup();render(<AIAdvisor context={{type:'road',record_ids:['road-a']}}/>);
  await user.click(screen.getByRole('button',{name:'Ask about this evidence'}));
  await user.click(screen.getByRole('checkbox',{name:/Request configured AI emphasis/}));
  const input=screen.getByLabelText('Question about attached evidence');expect(input).toHaveAttribute('maxLength','500');
  await user.type(input,'Which assumptions should we verify?');
  await user.click(screen.getByRole('button',{name:'Ask contextual question'}));
  expect(explainContext).toHaveBeenCalledWith({type:'road',record_ids:['road-a']},'ai','Which assumptions should we verify?',expect.any(AbortSignal));
  await user.click(screen.getByText('How AI works'));
  expect(screen.getByText(/AI does not approve projects or spending/)).toBeInTheDocument();
  await user.click(screen.getByRole('button',{name:'Check provider status'}));
  expect(await screen.findByText(/Provider not configured/)).toBeInTheDocument();
});
it('shows loading and error, then retries without fabricating an answer',async()=>{
  let reject: (e: Error)=>void = ()=>{};
  vi.mocked(explainContext).mockImplementationOnce(()=>new Promise((_,r)=>{reject=r;}));
  const user=userEvent.setup();render(<AIAdvisor context={{type:'estimate',record_ids:['saved']}} label="Explain this estimate"/>);
  await user.click(screen.getByRole('button',{name:'Explain this estimate'}));
  expect(screen.getByRole('status')).toHaveTextContent('Building evidence');
  expect(screen.queryByRole('article',{name:'Grounded explanation'})).not.toBeInTheDocument();
  reject(new Error('Local API unavailable'));
  expect(await screen.findByRole('alert')).toHaveTextContent('Local API unavailable');
  await user.click(screen.getByRole('button',{name:'Retry explanation'}));
  expect(await screen.findByRole('article',{name:'Grounded explanation'})).toHaveTextContent('53400.00 USD');
});
it('clears answers and aborts requests when context changes',async()=>{
  const user=userEvent.setup();const view=render(<AIAdvisor context={{type:'road',record_ids:['a']}}/>);
  await user.click(screen.getByRole('button',{name:'Explain selected evidence'}));
  await screen.findByRole('article',{name:'Grounded explanation'});
  const signal=vi.mocked(explainContext).mock.calls[0][3]!;
  view.rerender(<AIAdvisor context={{type:'road',record_ids:['b']}}/>);
  expect(signal.aborted).toBe(true);
  expect(screen.queryByRole('article',{name:'Grounded explanation'})).not.toBeInTheDocument();
});
it('preserves insufficient evidence and explicit truncation indicators',async()=>{
  vi.mocked(explainContext).mockResolvedValue({data:{...answer,summary:'Insufficient evidence to predict future deterioration.',validation_status:'insufficient_evidence',key_findings:[],evidence:{...answer.evidence,truncated:true,omitted_fact_count:40}},meta});
  const user=userEvent.setup();render(<AIAdvisor context={{type:'road',record_ids:['a']}}/>);
  await user.click(screen.getByRole('button',{name:'Explain selected evidence'}));
  expect(await screen.findByText(/Insufficient evidence to predict/)).toBeInTheDocument();
  expect(screen.getByText(/Evidence truncated: 40 facts omitted/)).toBeInTheDocument();
});
it('records an explicit human note independently of AI',async()=>{
  vi.mocked(saveReviewNote).mockResolvedValue({data:{id:'review-1',action:'review_note',authorizes_work:false},meta});
  const user=userEvent.setup();render(<ReviewNote evaluationId="evaluation-a"/>);
  await user.click(screen.getByText('Record a human review note'));
  await user.type(screen.getByLabelText('Reviewer alias'),'Planner');
  await user.type(screen.getByLabelText('Review note'),'Verify conditions.');
  const save=screen.getByRole('button',{name:'Save human review note'});expect(save).toBeDisabled();
  await user.click(screen.getByRole('checkbox'));
  await user.click(save);
  expect(await screen.findByRole('status')).toHaveTextContent('No work authorized');
  expect(saveReviewNote).toHaveBeenCalledWith('evaluation-a','Planner','Verify conditions.',expect.any(AbortSignal));
  expect(explainContext).not.toHaveBeenCalled();
});
