import re, json
import numpy as np, pandas as pd
OUT="output/progesterone_withdrawal/"
bnd=open('models/superset/adoc-literature-superset-v0.5.1/network.bnd').read()
logic=dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", bnd))
meta=json.load(open(OUT+'run_metadata.json'))
inputs=meta['arm_inputs']['withdrawal']
ev=pd.read_csv(OUT+'per_trajectory_events.tsv',sep='\t')
compiled={n:compile(e.replace('!',' not '),n,'eval') for n,e in logic.items()}
n_events=viol=0; examples=[]; min_gap=np.inf
direct_pairs={}  # regulator->target order stats over direct edges
for k,g in ev.groupby('traj'):
    state={**{n:bool(v) for n,v in inputs.items()}, **{r.node:bool(r.initial) for r in g.itertuples()}}
    evs=g[g.switch_time.notna()].sort_values('switch_time')
    times=evs.switch_time.to_numpy()
    if len(times)>1: min_gap=min(min_gap,np.diff(times).min())
    for r in evs.itertuples():
        target=eval(compiled[r.node],{},dict(state))
        n_events+=1
        if target==state[r.node]:
            viol+=1
            if len(examples)<5: examples.append((k,r.node,r.switch_time))
        state[r.node]=not state[r.node]
    # final state must be a fixed point
    for n in logic:
        if n in inputs: continue
        if eval(compiled[n],{},dict(state))!=state[n]:
            viol+=1; examples.append((k,n,'not fixed at end'))
print('events checked',n_events,'unjustified switches',viol,examples)
print('smallest gap between two events in a trajectory',min_gap)
# direct edges: regulator switched before target in how many trajectories
wide=ev.pivot(index='traj',columns='node',values='switch_time')
rows=[]
for tgt,e in logic.items():
    for reg in set(re.findall(r"[A-Za-z_]\w*",e))-{'and','or','not',tgt}:
        if reg in wide and tgt in wide:
            both=wide[[reg,tgt]].dropna()
            if len(both): rows.append((reg,tgt,len(both),(both[reg]<both[tgt]).mean()))
d=pd.DataFrame(rows,columns=['regulator','target','n','p_reg_first']).sort_values('p_reg_first')
print(d.to_string())
