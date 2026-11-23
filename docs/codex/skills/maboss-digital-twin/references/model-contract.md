# MaBoSS model contract

## Core formalism

MaBoSS simulates an asynchronous continuous-time Markov process on a Boolean
state space. A transition changes one node at a time. Logical rules determine
whether a transition is enabled; upward and downward rates determine relative
transition timing.

## Baseline artifacts

Require:

- `.bnd`: nodes, logical rules, rate-up/rate-down expressions, and
  internal/output status;
- `.cfg`: initial-state distributions, simulation settings, observables, and
  parameter values;
- node dictionary;
- edge-evidence table;
- phenotype definitions;
- provenance record and hashes.

Do not rely on a `.bnd`/`.cfg` pair without the dictionaries and evidence
tables.

## Node contract

Record stable identifier, biological entity or process, spatial/cellular
context, meanings of states 0 and 1, measurement proxies, model role, evidence
source, and confidence.

Avoid nodes whose binary state has no interpretable biological meaning.

## Edge and rule contract

For each edge record source, target, sign, direction, mechanism, evidence source,
and confidence. For each logical rule:

- explain AND as joint necessity;
- explain OR as alternative sufficiency;
- explain NOT as inhibition or absence requirement;
- flag uncertain operators and define alternative-rule sensitivity variants.

Network diagrams are not sufficient evidence for executable rule semantics.

## Rate contract

Record whether every rate is a default assumption, qualitative ordering
constraint, estimate from external temporal data, or fitted value.

Rates are inverse relative time scales. Do not label MaBoSS time with physical
units unless calibration supports that mapping. Avoid fitting many weakly
identifiable rates to sparse endpoints.

## Initial-state contract

Record every initial probability and its evidence. Distinguish known state,
uncertain distribution, and arbitrary default. Patient data most naturally
inform initial context when they measure the system near simulation start.

## Phenotype contract

Define each phenotype as an explicit Boolean expression before simulation.
Separate mechanistic internal nodes from reported phenotypes. A result is not
comparable across runs if the phenotype definition changes.

## Perturbation contract

Record target, direction, mechanism, dose abstraction, timing abstraction, and
matched baseline. A clamp is not automatically equivalent to a real drug; state
the abstraction and known off-target omissions.
