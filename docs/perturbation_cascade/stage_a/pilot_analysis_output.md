# Stage A pilot analysis output

Verbatim stdout of `python -B docs/perturbation_cascade/stage_a/analyze_pilot.py`
(the lines between the fences, byte for byte).

```text
=== 0. lineage ('basal_maternal', 'e2_primed_maternal', 'hormone_treated_maternal')
B_all_h25 memory nodes 45 states 16
A_canon_h25 memory nodes 35 states 16

=== 1. control arm: switching without perturbation
B_all_h25: nodes switching in control: 0; max p_switch 0.000; any at-risk at horizon 0.000
A_canon_h25: nodes switching in control: 8; max p_switch 1.000; any at-risk at horizon 0.000
                                  p_init_on  p_switch  p_net_change  p_multi
node                                                                        
E_PAEP                                  0.0     1.000         1.000      0.0
OUT_EPITHELIAL_RECEPTIVE                0.0     1.000         1.000      0.0
OUT_MATERNAL_ADHESION_COMPETENCE        0.0     0.826         0.826      0.0
OUT_STROMAL_DECIDUALIZED                0.0     1.000         1.000      0.0
S_IGFBP1                                0.0     1.000         1.000      0.0
S_PRL                                   0.0     1.000         1.000      0.0
X_ADHESION_ROUTE_REDUNDANT              0.0     0.407         0.407      0.0
X_ADHESION_ROUTE_SPP1                   0.0     0.710         0.710      0.0
B_all_h50: nodes switching in control: 0; max p_switch 0.000; any at-risk at horizon 0.000
B_all_declared: nodes switching in control: 38; max p_switch 0.955; any at-risk at horizon 0.000
                                  p_init_on  p_switch  p_net_change  p_multi
node                                                                        
E_ANXA2_ACTIN                         0.769     0.231         0.231    0.000
E_CD98_CD9                            0.356     0.644         0.644    0.000
E_DAG1_CLEAVED                        0.563     0.437         0.437    0.000
E_DAG1_FULL                           0.445     0.445         0.445    0.000
E_ESTROGENIC_PROLIFERATION            0.421     0.423         0.421    0.002
E_GP130_STAT3                         0.557     0.443         0.443    0.000
E_HBEGF                               0.753     0.247         0.247    0.000
E_IHH                                 0.910     0.090         0.090    0.000
E_ITGAVB3_5                           0.775     0.225         0.225    0.000
E_LIF                                 0.744     0.256         0.256    0.000
E_MUC1_BARRIER                        0.227     0.227         0.227    0.000
E_MUC1_SLEX                           0.747     0.253         0.253    0.000
E_PAEP                                0.766     0.234         0.234    0.000
E_PC6                                 0.754     0.246         0.246    0.000
E_PGR                                 0.989     0.011         0.011    0.000
E_PODXL                               0.228     0.228         0.228    0.000
E_RECEPTIVE_SURFACE                   0.102     0.898         0.898    0.001
E_SECRETORY_STATE                     0.908     0.092         0.092    0.000
E_SPP1_EXPR                           0.752     0.248         0.248    0.000
OUT_EPITHELIAL_RECEPTIVE              0.045     0.955         0.955    0.001
OUT_MATERNAL_ADHESION_COMPETENCE      0.001     0.828         0.828    0.000
OUT_STROMAL_DECIDUALIZED              0.443     0.557         0.557    0.000
S_BMP2                                0.863     0.137         0.137    0.000
S_DECIDUALIZED                        0.648     0.352         0.352    0.000
S_FGF_MITOGENIC                       0.240     0.240         0.240    0.000
S_HAND2                               0.907     0.093         0.093    0.000
S_IGFBP1                              0.435     0.565         0.565    0.000
S_NR2F2                               0.704     0.296         0.296    0.000
S_PGR                                 0.981     0.019         0.019    0.000
S_PKA                                 0.983     0.017         0.017    0.000
S_PRL                                 0.437     0.563         0.563    0.000
S_SPP1                                0.429     0.571         0.571    0.000
S_TAZ_ECM                             0.438     0.562         0.562    0.000
X_ADHESION_ROUTE_REDUNDANT            0.018     0.399         0.399    0.000
X_ADHESION_ROUTE_SPP1                 0.020     0.697         0.697    0.000
X_ANTIADHESIVE_ROUTE                  0.153     0.154         0.153    0.001
X_MECHANICAL_PERMISSIVE_ECM           0.271     0.729         0.729    0.000
X_SPP1_LUMEN_FREE                     0.649     0.351         0.351    0.000

=== 2. withdrawal vs mifepristone (policy B, h25, same states+seeds)
B_all_h25 network sha distinct: True | overrides wd: {} | mife: {'E_PGR': '(IN_PROGESTIN) and not 1', 'S_PGR': '(IN_PROGESTIN) and not 1'}
  pathwise identical first_time: 1.0000; identical n_min 1.0000; identical final 1.0000
  max |p_switch diff| 0.0000; max |median diff| 0.00e+00
A_canon_h25 network sha distinct: True | overrides wd: {} | mife: {'E_PGR': '(IN_PROGESTIN) and not 1', 'S_PGR': '(IN_PROGESTIN) and not 1'}
  pathwise identical first_time: 1.0000; identical n_min 1.0000; identical final 1.0000
  max |p_switch diff| 0.0000; max |median diff| 0.00e+00

=== 3. policy A (canonical extended_maternal_joint) vs B (all non-inputs), withdrawal arm
memory nodes in B but not A: ['E_PAEP', 'OUT_EPITHELIAL_RECEPTIVE', 'OUT_MATERNAL_ADHESION_COMPETENCE', 'OUT_STABLE_ADHESION', 'OUT_STROMAL_DECIDUALIZED', 'S_IGFBP1', 'S_PRL', 'X_ADHESION_ROUTE_REDUNDANT', 'X_ADHESION_ROUTE_SPP1', 'X_ANTIADHESIVE_ROUTE']
                                  init_A  init_B   sw_A   sw_B  med_A  med_B
node                                                                        
E_CD98_CD9                           1.0   1.000  1.000  1.000  4.550  4.734
E_PAEP                               0.0   1.000  0.743  1.000  0.477  2.638
OUT_EPITHELIAL_RECEPTIVE             0.0   1.000  0.914  1.000  0.593  4.021
OUT_MATERNAL_ADHESION_COMPETENCE     0.0   0.826  0.320  0.826  1.265  2.498
OUT_STROMAL_DECIDUALIZED             0.0   1.000  0.742  1.000  0.467  2.672
S_HAND2                              1.0   1.000  1.000  1.000  3.620  3.440
S_IGFBP1                             0.0   1.000  0.750  1.000  0.467  2.661
S_PRL                                0.0   1.000  0.755  1.000  0.524  2.678
X_ADHESION_ROUTE_REDUNDANT           0.0   0.407  0.372  0.407  0.615  3.934
X_ADHESION_ROUTE_SPP1                0.0   0.710  0.630  0.710  0.605  3.737

=== 4. initialisation horizon: starting distributions and withdrawal medians
TV(start h25, B_all_h50) = 0.0000
   max |median first-time diff| vs h25: 0.000 at E_ANXA2_ACTIN; max |p_switch diff| 0.000
TV(start h25, B_all_declared) = 0.9993
   max |median first-time diff| vs h25: 2.320 at E_CD98_CD9; max |p_switch diff| 0.780

=== 5. tick / horizon invariance on v0.6.0 (first 200 trajectories, same states and seeds)
B_tick005: max |first_time diff| 3.55e-15; switch presence agree 1.0000; n_min agree 1.0000; unresolved first 0.0000
B_tick0001: max |first_time diff| 1.78e-15; switch presence agree 1.0000; n_min agree 1.0000; unresolved first 0.0000
B_h40: max |first_time diff| 0.00e+00; switch presence agree 1.0000; n_min agree 1.0000; unresolved first 0.0000

=== 6. withdrawal arm event categories (policy B, h25)
category
single_switch    35135
no_switch         9865
unresolved first windows: 0
                                  p_init_on  p_switch  p_multi  p_transient  p_net_change  p_at_risk_end  med_first
node                                                                                                               
E_PGR                                 1.000     1.000      0.0          0.0         1.000            0.0      0.700
S_PGR                                 1.000     1.000      0.0          0.0         1.000            0.0      0.703
S_NR2F2                               1.000     1.000      0.0          0.0         1.000            0.0      1.521
E_IHH                                 1.000     1.000      0.0          0.0         1.000            0.0      1.572
S_DECIDUALIZED                        1.000     1.000      0.0          0.0         1.000            0.0      1.600
E_SECRETORY_STATE                     1.000     1.000      0.0          0.0         1.000            0.0      1.684
OUT_MATERNAL_ADHESION_COMPETENCE      0.826     0.826      0.0          0.0         0.826            0.0      2.498
E_ANXA2_ACTIN                         1.000     1.000      0.0          0.0         1.000            0.0      2.577
S_SPP1                                1.000     1.000      0.0          0.0         1.000            0.0      2.598
E_PC6                                 1.000     1.000      0.0          0.0         1.000            0.0      2.602
S_TAZ_ECM                             1.000     1.000      0.0          0.0         1.000            0.0      2.624
E_PAEP                                1.000     1.000      0.0          0.0         1.000            0.0      2.638
E_PODXL                               0.000     1.000      0.0          0.0         1.000            0.0      2.648
E_MUC1_SLEX                           1.000     1.000      0.0          0.0         1.000            0.0      2.657
S_BMP2                                1.000     1.000      0.0          0.0         1.000            0.0      2.660
S_IGFBP1                              1.000     1.000      0.0          0.0         1.000            0.0      2.661
X_MECHANICAL_PERMISSIVE_ECM           1.000     1.000      0.0          0.0         1.000            0.0      2.664
OUT_STROMAL_DECIDUALIZED              1.000     1.000      0.0          0.0         1.000            0.0      2.672
E_LIF                                 1.000     1.000      0.0          0.0         1.000            0.0      2.672
S_PRL                                 1.000     1.000      0.0          0.0         1.000            0.0      2.678
E_HBEGF                               1.000     1.000      0.0          0.0         1.000            0.0      2.697
E_MUC1_BARRIER                        0.000     1.000      0.0          0.0         1.000            0.0      2.699
E_SPP1_EXPR                           1.000     1.000      0.0          0.0         1.000            0.0      2.739
X_ANTIADHESIVE_ROUTE                  0.000     0.192      0.0          0.0         0.192            0.0      2.981
E_RECEPTIVE_SURFACE                   1.000     1.000      0.0          0.0         1.000            0.0      3.017
S_HAND2                               1.000     1.000      0.0          0.0         1.000            0.0      3.440
E_DAG1_CLEAVED                        1.000     1.000      0.0          0.0         1.000            0.0      3.619
E_DAG1_FULL                           0.000     1.000      0.0          0.0         1.000            0.0      3.696
E_GP130_STAT3                         1.000     1.000      0.0          0.0         1.000            0.0      3.720
X_ADHESION_ROUTE_SPP1                 0.710     0.710      0.0          0.0         0.710            0.0      3.737
X_ADHESION_ROUTE_REDUNDANT            0.407     0.407      0.0          0.0         0.407            0.0      3.934
OUT_EPITHELIAL_RECEPTIVE              1.000     1.000      0.0          0.0         1.000            0.0      4.021
E_ITGAVB3_5                           1.000     1.000      0.0          0.0         1.000            0.0      4.126
S_FGF_MITOGENIC                       0.000     1.000      0.0          0.0         1.000            0.0      4.456
E_CD98_CD9                            1.000     1.000      0.0          0.0         1.000            0.0      4.734
X_SPP1_LUMEN_FREE                     1.000     1.000      0.0          0.0         1.000            0.0      4.744
E_ESTROGENIC_PROLIFERATION            0.000     1.000      0.0          0.0         1.000            0.0      5.483
never switching nodes: ['E_CDH1_APICAL', 'E_KLF12_HIGH', 'OUT_STABLE_ADHESION', 'S_PKA', 'X_INTERFACE_ANTIADHESIVE_RELAY', 'X_INTERFACE_REDUNDANT_RELAY', 'X_INTERFACE_SPP1_RELAY', 'X_MECHANICAL_STRESS_RELAY']

=== 7. position statistics: robustness
block1 vs block2 (independent states+seeds, n=1000 each):
  abs    spearman 0.926  max|diff| 0.153  scale(IQR of medians) 1.094
  rank   spearman 0.944  max|diff| 0.067  scale(IQR of medians) 0.248
  ntime  spearman 0.934  max|diff| 0.046  scale(IQR of medians) 0.160
  drop last node E_ESTROGENIC_PROLIFERATION:
     rank   max|shift| 0.025  median|shift| 0.013  spearman 0.997
     ntime  max|shift| 0.028  median|shift| 0.015  spearman 0.994
  drop OUT_*:
     rank   max|shift| 0.019  median|shift| 0.005  spearman 0.995
     ntime  max|shift| 0.017  median|shift| 0.005  spearman 0.998
  drop first two E_PGR,S_PGR:
     rank   max|shift| 0.053  median|shift| 0.033  spearman 1.000
     ntime  max|shift| 0.066  median|shift| 0.042  spearman 0.989
  relay X_INTERFACE_ANTIADHESIVE_RELAY (P on 0.19) abs   : max|median shift| among non-X nodes 0.361 at OUT_STROMAL_DECIDUALIZED
  relay X_INTERFACE_ANTIADHESIVE_RELAY (P on 0.19) rank  : max|median shift| among non-X nodes 0.088 at OUT_STROMAL_DECIDUALIZED
  relay X_INTERFACE_ANTIADHESIVE_RELAY (P on 0.19) ntime : max|median shift| among non-X nodes 0.057 at OUT_MATERNAL_ADHESION_COMPETENCE
  relay X_INTERFACE_REDUNDANT_RELAY (P on 0.41) abs   : max|median shift| among non-X nodes 0.383 at S_IGFBP1
  relay X_INTERFACE_REDUNDANT_RELAY (P on 0.41) rank  : max|median shift| among non-X nodes 0.069 at S_PRL
  relay X_INTERFACE_REDUNDANT_RELAY (P on 0.41) ntime : max|median shift| among non-X nodes 0.040 at E_MUC1_SLEX
  relay X_INTERFACE_SPP1_RELAY (P on 0.71) abs   : max|median shift| among non-X nodes 0.234 at E_MUC1_SLEX
  relay X_INTERFACE_SPP1_RELAY (P on 0.71) rank  : max|median shift| among non-X nodes 0.035 at E_ITGAVB3_5
  relay X_INTERFACE_SPP1_RELAY (P on 0.71) ntime : max|median shift| among non-X nodes 0.047 at E_DAG1_FULL
  relay X_MECHANICAL_STRESS_RELAY (P on 0.30) abs   : max|median shift| among non-X nodes 0.262 at E_ESTROGENIC_PROLIFERATION
  relay X_MECHANICAL_STRESS_RELAY (P on 0.30) rank  : max|median shift| among non-X nodes 0.073 at S_PRL
  relay X_MECHANICAL_STRESS_RELAY (P on 0.30) ntime : max|median shift| among non-X nodes 0.045 at E_CD98_CD9
  adjacent pairs in ntime-median order: 36; P(a first) in [0.4,0.6]: 0.92; >0.9: 0.00
  all pairs: 666; unresolved [0.4,0.6]: 0.28; strict (0 or 1): 0.11
  pairwise precedence block1 vs block2: max|diff| 0.099, median 0.012

=== 8. n adequacy: bootstrap 95% CI half-width of per-node median at n=1000
  abs    median CI half-width: median 0.1314 max 0.2618 | q97.5 CI half-width median 0.4638 max 1.1309
  rank   median CI half-width: median 0.0219 max 0.0441 | q97.5 CI half-width median 0.0147 max 0.0597
  ntime  median CI half-width: median 0.0199 max 0.0468 | q97.5 CI half-width median 0.0355 max 0.0946
  switching counts (n contributing) min over switching nodes: 192 X_ANTIADHESIVE_ROUTE
```
