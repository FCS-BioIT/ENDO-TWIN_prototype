import cmaboss, numpy as np, os, sys
from scipy import stats
S=sys.argv[1]; NET=os.path.join(S,"syn","net.bnd")
os.makedirs(os.path.join(S, "syn"), exist_ok=True)  # the probe network, embedded so the probe needs only a scratch dir
open(os.path.join(S, "syn", "net.bnd"), "w").write("Node A { logic = !A; }\nNode D { logic = 0; }\nNode I { logic = I; }\nNode P { logic = I; }\nNode Q { logic = 0; }\n")
CFG=os.path.join(S,"syn","c3.cfg")
def run(tick, seed, T=5.0, I=1, P=1):
    open(CFG,"w").write(f"A.istate=0;\nD.istate=1;\nI.istate={I};\nP.istate={P};\nQ.istate=1;\nsample_count=1;\nmax_time={T};\ntime_tick={tick};\ndiscrete_time=0;\nuse_physrandgen=0;\nseed_pseudorandom={seed};\nthread_count=1;\n")
    r=cmaboss.MaBoSSSim(network=NET,config=CFG).run()
    arr,times,nodes=r.get_nodes_probtraj()[:3]
    return np.asarray(arr,float), list(nodes)
def single_switch_time(x, tick, x0):
    x=np.where(np.abs(x)<1e-12,0,np.where(np.abs(x-1)<1e-12,1,x))
    k=np.nonzero(x!=x0)[0]
    if k.size==0: return np.nan
    k=k[0]; occ_old = x[k] if x0==1 else 1-x[k]
    return k*tick + occ_old*tick
def min_switches(x, s0):
    """Minimum switch count consistent with window occupancies, start state s0 known."""
    x=np.where(np.abs(x)<1e-12,0,np.where(np.abs(x-1)<1e-12,1,x))
    INF=10**9; cost={s0:0, 1-s0:INF}
    for v in x:
        new={0:INF,1:INF}
        for s,c in cost.items():
            if c>=INF: continue
            if v in (0,1):
                if s==v: new[s]=min(new[s],c)   # whole window: no switch, state must equal
            else:
                for e in (0,1):
                    new[e]=min(new[e], c+(1 if s!=e else 2))
        cost=new
    return min(cost.values())
rng=np.random.default_rng(1)
seeds=[int(s) for s in np.random.SeedSequence(20261008).generate_state(300)%(2**31-1)+1]
# 1. tick invariance of single-switch reconstruction (D: Exp(1) decay)
ticks=[1.0,0.1,0.01,0.001]
res={tk:[] for tk in ticks}
for s in seeds[:200]:
    for tk in ticks:
        a,n=run(tk,s,T=8.0); res[tk].append(single_switch_time(a[:,n.index("D")],tk,1))
ref=np.array(res[0.001])
for tk in ticks: d=np.nanmax(np.abs(np.array(res[tk])-ref)); print(f"tick {tk}: max|t-t(0.001)| = {d:.2e}  nan={np.isnan(res[tk]).sum()}")
print("KS vs Exp(1):", stats.kstest(ref[~np.isnan(ref)],"expon").pvalue, "censored>8:",np.isnan(ref).sum())
# 2. toggle A: true count from tick 1e-4; lower bound at coarser ticks
T=5.0; rows=[]
for s in seeds[:100]:
    a,n=run(1e-4,s,T=T); x=a[:,n.index("A")]; truth=min_switches(x,0)
    r={"truth":truth}
    for tk in (0.5,0.1,0.01):
        b,_=run(tk,s,T=T); r[tk]=min_switches(b[:,n.index("A")],0)
    rows.append(r)
truth=np.array([r["truth"] for r in rows])
print("toggle T=5 mean count (fine)",truth.mean(),"expected ~5 (rate-1 toggle)")
for tk in (0.5,0.1,0.01):
    lb=np.array([r[tk] for r in rows]); print(f" tick {tk}: lower bound never exceeds truth: {(lb<=truth).all()}  exact in {np.mean(lb==truth):.0%}  mean deficit {np.mean(truth-lb):.2f}")
# 3. seed correlation of event streams: consecutive vs SeedSequence
def dtimes(seedlist):
    return np.array([single_switch_time(run(0.01,s,T=20.0)[0][:,4],0.01,1) for s in seedlist])  # Q column
cons=dtimes(range(1,401)); ss=dtimes(seeds[:300]+[int(x) for x in np.random.SeedSequence(7).generate_state(100)%(2**31-1)+1])
for name,v in (("consecutive",cons),("seedsequence",ss)):
    print(name,"lag-1 corr",round(np.corrcoef(v[:-1],v[1:])[0,1],3),"KS p",round(stats.kstest(v,"expon").pvalue,3))
# 4. pairing: Q independent of I; same seed, I=1 vs I=0 (P starts 1, so P decays only when I=0)
same=0; diffs=[]
for s in seeds[:100]:
    q1=single_switch_time(run(0.01,s,T=20,I=1)[0][:,4],0.01,1)
    q0=single_switch_time(run(0.01,s,T=20,I=0)[0][:,4],0.01,1)
    diffs.append(abs(q1-q0)); same+= abs(q1-q0)<1e-9
print("pairing: Q switch time identical across arms in",same,"/100; median |diff|",np.median(diffs))
