import argparse,json,math
from pathlib import Path

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',nargs='+',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--expected-tasks',type=int,default=17); a=p.parse_args()
 errors=[]; receipts=[]; seen=set()
 for f in a.input:
  if not f.is_file(): errors.append(f'missing receipt: {f}'); continue
  try: d=json.loads(f.read_text(encoding='utf-8'))
  except Exception as e: errors.append(f'invalid receipt {f}: {type(e).__name__}'); continue
  pr=d.get('protocol',{}); seeds=pr.get('seeds',[]); seed=seeds[0] if len(seeds)==1 else None
  if pr.get('benchmark')!='SGAnalog': errors.append(f'{f}: wrong benchmark')
  if d.get('summary',{}).get('tasks')!=a.expected_tasks: errors.append(f'{f}: task count mismatch')
  if seed is None: errors.append(f'{f}: expected one seed')
  for row in d.get('results',[]):
   key=(seed,row.get('task',{}).get('task_id'),row.get('model'))
   if key in seen: errors.append(f'duplicate cell: {key}')
   seen.add(key); val=row.get('score',{}).get('score')
   if not isinstance(val,(int,float)) or not math.isfinite(float(val)): errors.append(f'non-finite score: {key}')
  receipts.append((seed,pr,d))
 seeds=sorted(s for s,_,_ in receipts if s is not None)
 if seeds!=[0,1,2]: errors.append(f'expected seeds [0,1,2], observed {seeds}')
 rows=[dict(row,seed=seed) for seed,_,d in receipts for row in d.get('results',[])]
 out={'schema':'sganalog-native-merged/v1','benchmark':'SGAnalog','protocol':{'source_commits':sorted({pr.get('benchmark_commit') for _,pr,_ in receipts}),'models':sorted({pr.get('model') for _,pr,_ in receipts}),'simulators':sorted({pr.get('simulator') for _,pr,_ in receipts}),'budget':{'simulations':300,'llm_calls':12},'seeds':seeds},'summary':{'receipts':len(receipts),'tasks_per_seed':a.expected_tasks,'rows':len(rows),'seeds':seeds,'complete':not errors,'mean_score':sum(float(r['score']['score']) for r in rows)/max(1,len(rows)),'converged':sum(bool(r['score'].get('model_converged')) for r in rows)},'rows':rows,'errors':errors}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out['summary'],sort_keys=True));
 if errors: raise SystemExit('SGAnalog merge failed: '+'; '.join(errors[:8]))
if __name__=='__main__': main()
