# CLAUDE.md

Course Finder: a small Flask + SQLite + vanilla JS tool that lets learners search courses and enroll in them.

## Workflow rules

1. **One branch per piece of work.** Never commit directly to `main`.
2. **One worktree per branch** so that parallel agents don't conflict:
   `git worktree add ../worktrees/<type>-<slug> -b <type>/<slug> <base>`
3. **Conventional Commits** for every commit message, with types `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`
   (e.g. `feat: add course search endpoint`).
4. **Small, surgical commits.** Each commit makes one logical change.
5. **Branch names and PR titles use the same convention:**
   - Branch: `<type>/<short-kebab-slug>` (e.g. `feat/course-search`)
   - PR title: a Conventional Commit subject (e.g. `feat: add course search endpoint`)
6. **Small, focused PRs** that a human can review in one sitting. Stack PRs when one change depends on another.
   Every PR description includes:
   - **Summary**: one line
   - **What** changed
   - **Why**
   - **How to test**
   - **Reviewer checklist**: a few `- [ ]` items the reviewer should verify

## Conventions

- Tests are collocated: `test_<module>.py` sits next to `<module>.py`. Run them with `pytest`.
