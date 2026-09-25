# Phase 2B pre-registration, amendment 04

Committed **before any candidate KLF12 value was read**, and on its own. It
changes no Phase-2B rule. It re-pins the implementation after a fix to the
RR14 repository-citation check that amendment 03 adopted.

**The fix.** The check resolved a cited path before inspecting it. That had
two consequences:
- a symlink was verified against its target, not the path it names;
- the `data/` exclusion never saw the resolved path.

Now the named path is refused if it, or any parent below the repository
root, is a symlink. This is checked before anything is resolved. The
resolved file must also lie inside the repository and outside `data/`.

**Stated plainly.** That the repository form is used only for a custom
method is the owner's rule. It is not a machine check.

The owner ratifications recorded in amendment 03 stand unchanged.
