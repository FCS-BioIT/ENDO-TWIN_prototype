import cmaboss, numpy as np, os, sys
from scipy import stats
S=sys.argv[1]; NET=os.path.join(S,"syn","net.bnd"); CFG=os.path.join(S,"syn","c4.cfg")
os.makedirs(os.path.join(S, "syn"), exist_ok=True)  # the probe network, embedded so the probe needs only a scratch dir
open(os.path.join(S, "syn", "net.bnd"), "w").write("Node A { logic = !A; }\nNode D { logic = 0; }\nNode I { logic = I; }\nNode P { logic = I; }\nNode Q { logic = 0; }\n")
def qtime(seed, gen):
    extra = "use_mtrandgen = TRUE;\n" if gen=="mt" else ""
    open(CFG,"w").write(f"A.istate=0;\nD.istate=1;\nI.istate=1;\nP.istate=1;\nQ.istate=1;\nsample_count=1;\nmax_time=30;\ntime_tick=0.01;\ndiscrete_time=0;\nuse_physrandgen=0;\nseed_pseudorandom={seed};\nthread_count=1;\n{extra}")
    r=cmaboss.MaBoSSSim(network=NET,config=CFG).run()
    a,_,n=r.get_nodes_probtraj()[:3]; a=np.asarray(a,float)
    out=[]
    for node in ("D","Q"):
        x=a[:,list(n).index(node)]; k=np.nonzero(x<1-1e-9)[0][0]; out.append(0.01*k+0.01*(1-(1-x[k])))
    return out
N=1500
ss=[int(s) for s in np.random.SeedSequence(20261008).generate_state(N)%(2**31-2)+1]
for gen in ("rand48","mt"):
    for name,seeds in (("consecutive",list(range(1,N+1))),("seedsequence",ss)):
        v=np.array([qtime(s,gen) for s in seeds])
        u=np.exp(-v)  # first-switch of D or Q: two competing Exp(1) -> the switch times are each Exp(1)
        dq=v[:,0]
        print(f"{gen:7s} {name:12s} KS(D~Exp1) p={stats.kstest(dq,'expon').pvalue:.3g}  lag1 corr={np.corrcoef(dq[:-1],dq[1:])[0,1]:+.3f}  corr(D,Q within traj)={np.corrcoef(v[:,0],v[:,1])[0,1]:+.3f}")
