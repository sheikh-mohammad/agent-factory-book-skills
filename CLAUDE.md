# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of production-grade skills for Claude Code, used for teaching the Skills concept in the AI Native Development book (Lesson 04, Chapter 5). Each skill extends Claude's capabilities with specialized domain knowledge, workflows, or tool integrations.

**Reading Material**: [Claude Code Features and Workflows](https://ai-native.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)

## Working with Skills

### Creating New Skills

Use the `skill-creator-pro` skill to create production-grade skills:

```
/skill-creator-pro <skill-name> - <description>
```

The skill creation workflow:
1. **Domain Discovery**: Research official documentation and gather authentic domain knowledge
2. **User Clarifications**: Ask about specific requirements (not domain knowledge)
3. **Skill Structure**: Create SKILL.md with frontmatter, references, scripts, and assets
4. **Validation**: Run skill-validator to ensure 90-100/100 score

### Validating Skills

Use the `skill-validator` skill to validate any skill:

```
/skill-validator <skill-name>
```

Validation evaluates 9 criteria categories:
- Structure & Anatomy (12%)
- Content Quality (15%)
- User Interaction (12%)
- Documentation & References (10%)
- Domain Standards (10%)
- Technical Robustness (8%)
- Maintainability (8%)
- Zero-Shot Implementation (12%)
- Reusability (13%)

**Target Score**: 90-100 for production-grade skills

### Improving Existing Skills

After validation, address identified weaknesses:
1. Review validation report recommendations
2. Make improvements systematically
3. Re-validate to confirm 100/100 score
4. Commit with validation score in message

## Skill Architecture

### Standard Structure

```
.claude/skills/<skill-name>/
├── SKILL.md                    # Main skill file (<500 lines)
│   ├── YAML frontmatter        # name, description, allowed-tools, model
│   └── Markdown content        # Workflows, patterns, examples
├── references/                 # Detailed domain knowledge
│   ├── patterns.md
│   ├── api-reference.md
│   └── ...
├── scripts/                    # Executable scripts (optional)
│   └── init-project.py
└── assets/                     # Templates, boilerplate (optional)
    └── templates/
        ├── Dockerfile
        └── ...
```

### SKILL.md Requirements

**Frontmatter**:
```yaml
---
name: skill-name                # lowercase, hyphens, ≤64 chars
description: |                  # ≤1024 chars, [What] + [When]
  [What] Capability statement.
  [When] This skill should be used when...
allowed-tools: Read, Grep       # optional: restrict tools
model: claude-opus-4            # optional: specify model
---
```

**Content Sections**:
- What This Skill Does / Does NOT Do
- Before Implementation (context gathering)
- Required Clarifications / Optional Clarifications
- Implementation Workflow
- Decision Trees
- Common Patterns / Anti-Patterns
- Good vs Bad Examples
- Reference Files
- Troubleshooting

### Skill Types

1. **Builder**: Creates artifacts (code, documents, projects)
   - Must have: Clarifications, Output Spec, Standards, Checklist

2. **Guide**: Provides step-by-step instructions
   - Must have: Workflow Steps, Examples, Official Docs links

3. **Automation**: Executes workflows with scripts
   - Must have: Scripts, Dependencies, Error Handling, I/O Spec

4. **Analyzer**: Extracts insights from data/code
   - Must have: Analysis Scope, Criteria, Output Format

5. **Validator**: Enforces quality standards
   - Must have: Criteria, Scoring Rubric, Thresholds, Remediation

### Key Principles

**Zero-Shot Implementation**:
- Embed all domain expertise in `references/` directory
- Only ask users for THEIR specific requirements
- Never instruct to "research" or "discover" at runtime

**Reusability**:
- Handle variations, not single requirements
- Capture what VARIES in clarifications
- Encode what's CONSTANT in references

**Progressive Disclosure**:
- Keep SKILL.md <500 lines (context is precious)
- Move detailed content to `references/`
- Use tables and decision trees for clarity

## Git Workflow

### Commit Message Format

Use conventional commits with validation scores:

```bash
git commit -m "feat: Add production-grade <Skill Name> skill (100/100 validation score)

- Brief description of skill capabilities
- Key features (bullet points)
- Domain coverage
- Validation score and criteria met
- Based on official documentation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Commit Types**:
- `feat:` - New skill or major feature
- `fix:` - Bug fix or correction
- `docs:` - Documentation updates
- `chore:` - Maintenance tasks

### Pushing Changes

```bash
git add .claude/skills/<skill-name>
git commit -m "feat: Add production-grade <Skill Name> skill (100/100 validation score)"
git push origin main
```

## Quality Standards

### Production-Grade Criteria

A skill is production-ready when it achieves:
- ✅ 90-100/100 validation score
- ✅ All domain expertise embedded (no runtime discovery)
- ✅ Clear required vs optional clarifications
- ✅ Anti-patterns documented with correct approaches
- ✅ Good/bad examples for key patterns
- ✅ Version awareness and maintenance strategy
- ✅ Complete reference documentation
- ✅ Production-ready templates (if applicable)

### Common Validation Issues

**Structure (12%)**:
- SKILL.md >500 lines → Move content to references
- Missing frontmatter → Add name and description
- Extraneous files → Remove README.md, CHANGELOG.md

**User Interaction (12%)**:
- No clarifications → Add required/optional sections
- Over-asking → Limit to 3-5 required questions
- Missing pacing note → Add "Avoid asking too many questions"

**Domain Standards (10%)**:
- No anti-patterns → Add "Must Avoid" section
- Missing examples → Add good vs bad code comparisons
- No checklist → Add production checklist

**Documentation (10%)**:
- No version awareness → Add compatibility notes
- Missing official links → Link to source documentation
- No maintenance strategy → Add versioning guide

## Skill Discovery

### Finding Skills

All skills are in `.claude/skills/` directory:

```bash
ls .claude/skills/
```

### Reading Skills

Each skill's SKILL.md describes:
- What it does and when to use it
- Required clarifications
- Implementation workflow
- Reference files for detailed knowledge

### Using Skills

Skills are invoked automatically by Claude Code based on:
- User requests matching skill description
- Code context (imports, file types)
- Explicit skill invocation: `/skill-name`

## Repository Maintenance

### Adding New Skills

1. Use `/skill-creator-pro` to create skill
2. Validate with `/skill-validator`
3. Improve to 100/100 score
4. Commit with validation score
5. Push to repository

### Updating Existing Skills

1. Read skill's SKILL.md and references
2. Make improvements
3. Re-validate with `/skill-validator`
4. Update version in references/versioning-strategy.md (if exists)
5. Commit with updated validation score

### Skill Naming Conventions

- Lowercase with hyphens: `skill-name`
- ≤64 characters
- Descriptive: `chatkit-server`, `fastapi`, `mcp-server`
- Avoid generic names: `helper`, `utils`, `common`

## Important Notes

### Context Window Management

- Skills are loaded into context when invoked
- SKILL.md should be <500 lines (context is precious)
- Use progressive disclosure: details in `references/`
- Large reference files (>10k words) should include grep patterns

### Domain Expertise

- Always research official documentation before creating skills
- Use `fetch-library-docs` skill to gather authentic patterns
- Embed expertise in `references/`, not in runtime instructions
- Never assume or hallucinate domain knowledge

### Skill Reusability

- Skills should handle variations, not single requirements
- Avoid hardcoding specific data, tools, or configurations
- Capture variable elements in clarifications
- Encode constant patterns in references

### Zero-Shot Implementation

Skills should enable single-interaction implementation:
- Gather context from: Codebase, Conversation, Skill References, User Guidelines
- Only ask users for THEIR requirements (not domain knowledge)
- All domain expertise embedded in skill
- No runtime discovery or research needed
