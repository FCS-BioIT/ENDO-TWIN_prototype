# Phase 2B pre-registration, amendment 19 (disclosure and coordination)

Committed **before any KLF12 value of any candidate was read**. It is
committed on its own and records the owner's decision of 2026-09-27.

It changes no rule, criterion, layer, quantity, derivation, code or pin.

## Recorded

1. C4 continues. It derives the KLF12 endpoint definition on the Cell Ranger
   9.0.1 filtered-count layer, exactly as amendment 16 froze it.
2. `src/dt_adoc/personalization/phase2a_contract.py` stays untouched and
   pinned.
3. Its RR04 still requires the historical deposited decontX layer
   (`ADOC_LAYER`). The legacy C6 verdict `QUALIFIED_REFERENCE_FOUND` is
   therefore **unreachable** for the new endpoint definition.
4. C6 must not report `QUALIFIED_REFERENCE_FOUND`. Under the existing verdict
   vocabulary, the verdict is at most `BLOCKED_OWNER_DECISION` (a deferred
   contract update). It stays so until the later Phase-2A redefinition unit
   that amendment 15 reserves.
5. This does **not** mean that:
   - C4 failed;
   - the reference is biologically unsuitable;
   - the filtered-count endpoint definition is invalid;
   - comparability failed.

   It means only that the legacy Phase-2A machine contract has not yet been
   migrated to the endpoint-observation architecture of amendments 15 and 16.

## Evidence referenced

This is the value-blind stack-identification lineage record that amendment 16
relies on:

    docs/phase2b_c4/stack_identification_cr9.0.1.json
    commit c527c43b167eee0c9a7a28979ecc5a9dad113065
    sha256 0a6870728ec06898ea8e82ce7d6968a471f742d52370cd5362df9dd4954499c7

## Not changed

- Phase-2A code;
- the ADOC per-cell values;
- the node-support artifacts;
- every existing pin. Amendment 12's pins are carried verbatim.

Every rule of amendments 01-18 stands. Review is degraded, and no cross-vendor
review is claimed.
