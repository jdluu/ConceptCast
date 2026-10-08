# Vendored ManimCE skill files

These Markdown files are adapted from **Manim Skills Repository** by Adithya S
Kolavi and are used under the MIT License.

- **Source:** https://github.com/adithya-s-k/manim_skill
- **Upstream path:** `skills/manimce-best-practices/rules/`
- **License:** MIT — see [LICENSE](LICENSE) in this directory.

**Changes made on vendoring.** The YAML frontmatter block (`name`, `description`,
`metadata`) was removed from every file, and a few lines were trimmed from some.
Nine of the eighteen files are otherwise byte-identical to upstream; the remaining
nine differ only by 3-9 deleted lines and share 97-99% of their content.

**Consumed by.** `lookup_manim_pattern` in
`apps/backend/src/infra/ai/tools/patterns.py`, which serves one file per topic on
request. The upstream frontmatter is not needed for that lookup, which is why it
was dropped.
