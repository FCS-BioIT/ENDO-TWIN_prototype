# Future multiscale extension (outside the funded work plan)

> **Status: future research, not a deliverable of the ENDO-TWIN grant.**
> Nothing here is implemented beyond the interfaces named in section 2.
> ENDO-TWIN models the ADOC system with one compartment-resolved MaBoSS network;
> it does not simulate space, cell numbers or mechanics.

This note records how the current architecture leaves a path towards spatially
explicit, per-cell simulation with PhysiBoSS/PhysiCell (MaBoSS networks inside
agent-based cells), and which choices were made so as not to block it.

## 1. Choices already made that keep the path open

| Requirement for per-cell coupling | Current design |
|---|---|
| The regulatory network is usable on its own | `src/endotwin/model.py` loads rules, variants and the interface without any protocol, data, figure or evaluation code. `network.bnd` is a standard MaBoSS file |
| Compartments are identifiable | Every node has a compartment (`node_dictionary.tsv`); epithelial and stromal rules live in one integrated file but separate cleanly |
| Communication goes through explicit interfaces | The two epithelial-stromal signals are declared in `interface.tsv`. `split_compartments()` produces stand-alone epithelial and stromal networks in which each received signal is an input (`RX_E_IHH`, `RX_S_PARACRINE_MITOGEN`). A test proves that coupling the two reproduces the integrated network for every input assignment and every rule-variant scenario |
| No hidden global state | Inputs are explicit per phase; there are no global constants in the rules. Medium inputs are copied into each compartment that reads them |
| Time is not assumed physical | MaBoSS time stays dimensionless; no conversion to hours is built in |
| Interventions are local | Knockdowns pin a node through its rates (`render_bnd(forced=...)`), which is how a per-cell knockout is expressed |

## 2. The per-cell interface that exists today

`src/endotwin/regulatory_unit.py` wraps one network (integrated, or one
compartment) behind the operations a per-cell driver needs:

| Operation | Method |
|---|---|
| Initialise the regulatory state from a cell state | `RegulatoryUnit.initialize({node: 0/1})` |
| Supply extracellular inputs | `set_inputs({input: 0/1})`, including received signals `RX_*` |
| Execute regulatory dynamics | `step(duration)`, with the joint state carried between steps |
| Retrieve node states or probabilities | `probabilities()`, or `sample_state(rng)` to draw one Boolean state for one agent |
| Pass selected outputs outward | `outputs()`: exported signals and functional outputs |

It runs MaBoSS through the same `cmaboss` backend as the rest of the code and is
covered by `tests/mainline/test_interface.py`. It is a seam, not a simulator.

## 3. How a future integration could proceed

1. **Cell types.** One PhysiCell cell definition per compartment (organoid
   epithelium, stroma), each carrying its compartment network from
   `split_compartments()`.
2. **Input mapping.** Medium inputs (`IN_*`) become substrates with
   experimentally defined concentrations; received signals (`RX_E_IHH`,
   `RX_S_PARACRINE_MITOGEN`) become secreted fields. Thresholds turning a local
   concentration into a Boolean input would have to be estimated, not assumed.
3. **Output mapping.** `S_PARACRINE_MITOGEN` and `E_IHH` drive secretion rates;
   `OUT_EPITHELIAL_PROLIFERATION` drives a cycle-entry probability;
   `OUT_STROMAL_DECIDUALIZATION` drives a phenotype switch.
4. **Time coupling.** A ratio between MaBoSS time and PhysiCell time per
   intracellular step must be calibrated against time-resolved data. ENDO-TWIN
   longitudinal outlet measurements could constrain it; none exists today.
5. **Further biology** that would need to be added: chip geometry and flow,
   cell-cell contact, proliferation and death, differentiation-dependent
   secretion, extracellular matrix and mechanics, and immune or inflammatory
   cells for IL-1beta sources.

## 4. What must not be inferred

- No spatial, mechanical or population-level prediction is made by ENDO-TWIN.
- The prototype once inspected a separate agent-based project for figure
  rendering only (`../THIRD_PARTY_NOTICES.md`); none of its spatial biology,
  PhysiBoSS coupling or parameters is used here.
- Per-cell execution with `RegulatoryUnit` is a software capability, not a
  validated multiscale model.
