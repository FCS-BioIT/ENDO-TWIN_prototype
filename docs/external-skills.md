# External skill provenance

External skills are globally installed under `~/.codex/skills` and registered
by the global Agent Harness. Repository-local scientific contracts take
precedence.

| Skill | Source path | Source revision inspected | License |
|---|---|---|---|
| `tooluniverse-systems-biology` | `mims-harvard/ToolUniverse/plugin/skills/tooluniverse-systems-biology` | `089eb8e6308fc64ae5af3de4bfbec32b5cf07b61` | Apache-2.0 |
| `systems-biology-expert` | `luokai0/ai-agent-skills-by-luo-kai/ai-agent-skills/17-emerging-tech (by Luo Kai)/systems-biology-expert` | `4d2fb89cdfb75f3f6fd3c6c5ec9ad90ea129eb3c` | No repository license returned by the GitHub API; treat reuse beyond local guidance as license-unverified |

The current `skills` npm CLI could not run on Node 18.19.1 because it requires
Node 22.20.0 or newer. The skills were installed with Codex's GitHub skill
installer instead.

For Codex compatibility, registry-specific frontmatter was removed after
installation:

- ToolUniverse: `disable-model-invocation`.
- systems-biology-expert: `version`, `author`, and `tags`.

The skill bodies were not changed.

No credible public MaBoSS-specific skill was found in the bounded search. The
repository-local `maboss-digital-twin` skill is therefore the authoritative
MaBoSS workflow.
