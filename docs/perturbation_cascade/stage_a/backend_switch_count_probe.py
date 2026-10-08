import cmaboss, numpy as np, os, sys
S=sys.argv[1]; NET=os.path.join(S,"syn","net.bnd"); CFG=os.path.join(S,"syn","c6.cfg")
os.makedirs(os.path.join(S, "syn"), exist_ok=True)  # the probe network, embedded so the probe needs only a scratch dir
open(os.path.join(S, "syn", "net.bnd"), "w").write("Node A { logic = !A; }\nNode D { logic = 0; }\nNode I { logic = I; }\nNode P { logic = I; }\nNode Q { logic = 0; }\n")
TOL=1e-9
def run(tick,seed,T=5.0):
    open(CFG,"w").write(f"A.istate=0;\nD.istate=1;\nI.istate=1;\nP.istate=1;\nQ.istate=1;\nsample_count=1;\nmax_time={T};\ntime_tick={tick};\ndiscrete_time=0;\nuse_physrandgen=0;\nseed_pseudorandom={seed};\nthread_count=1;\n")
    r=cmaboss.MaBoSSSim(network=NET,config=CFG).run(); a,t,n=r.get_nodes_probtraj()[:3]
    x=np.asarray(a,float)[:,0]; v=snap(x[-1:])[0]
    return x, (int(v) if v in (0.0,1.0) else None)
def snap(x): return np.where(x<TOL,0.0,np.where(x>1-TOL,1.0,x))
def min_switches(x,s0,s_end):
    INF=10**9; cost=[0,INF] if s0==0 else [INF,0]
    for v in snap(x):
        new=[INF,INF]
        for s in (0,1):
            if cost[s]>=INF: continue
            if v in (0.0,1.0):
                if s==v: new[s]=min(new[s],cost[s])
            else:
                for e in (0,1): new[e]=min(new[e],cost[s]+(1 if s!=e else 2))
        cost=new
    return cost[s_end] if s_end is not None else min(cost)
def exact_events(x,s0):
    """Times of switches in windows holding exactly one inferable switch; None if any window is ambiguous."""
    ...
seeds=[int(s) for s in np.random.SeedSequence(99).generate_state(200)%(2**31-2)+1]
rows=[]
for s in seeds:
    xf,fin=run(1e-4,s); r={"truth":min_switches(xf,0,fin)}
    for tk in (0.5,0.1,0.01,0.001):
        x,f2=run(tk,s); assert f2 is None or fin is None or f2==fin; r[tk]=min_switches(x,0,f2)
    rows.append(r)
truth=np.array([r["truth"] for r in rows]); print("mean count",truth.mean(),"(expect 5.0 for a rate-1 toggle over T=5)")
for tk in (0.5,0.1,0.01,0.001):
    lb=np.array([r[tk] for r in rows])
    print(f"tick {tk}: lb<=truth {(lb<=truth).all()}  exact {np.mean(lb==truth):.1%}  mean deficit {np.mean(truth-lb):.3f}")
