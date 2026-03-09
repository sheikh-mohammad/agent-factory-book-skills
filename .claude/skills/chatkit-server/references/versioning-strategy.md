# Versioning and Maintenance Strategy

Guide for keeping the chatkit-server skill up-to-date with evolving ChatKit framework.

---

## Version Tracking

### Current Skill Version
- **Skill Version**: 1.0.0
- **Based on**: OpenAI ChatKit (March 2026)
- **OpenAI SDK**: openai==1.12.0
- **FastAPI**: 0.109.0
- **Last Updated**: 2026-03-09

### Semantic Versioning

Follow semantic versioning for skill updates:

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (architecture patterns change)
MINOR: New features (new industry patterns, tools)
PATCH: Bug fixes, documentation updates
```

**Examples**:
- `1.0.0` → `1.0.1`: Fix typo in security guide
- `1.0.0` → `1.1.0`: Add new industry pattern (real estate)
- `1.0.0` → `2.0.0`: ChatKit moves from beta to GA with breaking changes

---

## Update Triggers

### When to Update Skill

| Trigger | Action | Priority |
|---------|--------|----------|
| **OpenAI API breaking change** | Update references, test examples | Critical |
| **New ChatKit feature** | Add to architecture patterns | High |
| **Security vulnerability** | Update security.md, templates | Critical |
| **New industry request** | Add to industry-patterns.md | Medium |
| **Dependency update** | Update requirements.txt, test | Medium |
| **User feedback** | Improve clarity, add examples | Low |

### Monitoring Sources

Check these sources monthly:
1. **OpenAI Changelog**: https://platform.openai.com/docs/changelog
2. **OpenAI Python SDK Releases**: https://github.com/openai/openai-python/releases
3. **FastAPI Releases**: https://github.com/tiangolo/fastapi/releases
4. **Security Advisories**: GitHub Dependabot, Snyk
5. **User Issues**: Skill usage feedback, error reports

---

## Update Process

### 1. Assess Impact

```
New Change Detected
    ↓
Is it breaking? → YES → MAJOR update required
    ↓ NO
Does it add features? → YES → MINOR update
    ↓ NO
Is it a fix/improvement? → YES → PATCH update
```

### 2. Update Checklist

For each update:

- [ ] Review official OpenAI documentation for changes
- [ ] Update affected reference files
- [ ] Update code examples in SKILL.md
- [ ] Update templates in assets/
- [ ] Update init-project.py script if needed
- [ ] Test examples with new versions
- [ ] Update version numbers in:
  - This document (versioning-strategy.md)
  - requirements.txt
  - package.json template
- [ ] Document changes in skill commit message
- [ ] Validate skill with skill-validator

### 3. Testing Protocol

Before releasing updates:

```bash
# Test initialization script
python scripts/init-project.py --name test-simple --pattern simple
cd test-simple
npm install
uv pip install -r requirements.txt

# Test with latest OpenAI SDK
pip install --upgrade openai
python -c "from openai import OpenAI; print(OpenAI().models.list())"

# Verify templates work
docker-compose build
docker-compose up -d
curl http://localhost:8000/health
```

---

## Backward Compatibility

### Maintaining Compatibility

**Goal**: Minimize breaking changes for existing users

**Strategies**:
1. **Deprecation Period**: Warn before removing patterns (3 months)
2. **Version Branches**: Support previous major version for 6 months
3. **Migration Guides**: Provide upgrade paths in references/
4. **Feature Flags**: Allow opt-in to new patterns

### Breaking Change Communication

When breaking changes are necessary:

```markdown
## Breaking Changes in v2.0.0

### Changed: Vector Store API
**Old Pattern** (deprecated):
```python
vector_store = client.vector_stores.create(...)
```

**New Pattern**:
```python
vector_store = client.beta.vector_stores.create(...)
```

**Migration**: Update all vector store calls to use beta namespace.
**Timeline**: Old pattern removed in v3.0.0 (6 months)
```

---

## Reference File Maintenance

### Update Frequency by File

| File | Update Frequency | Trigger |
|------|------------------|---------|
| `architecture-patterns.md` | Quarterly | New patterns emerge |
| `chatkit-api.md` | Monthly | API changes |
| `industry-patterns.md` | As needed | New industry requests |
| `tool-patterns.md` | Quarterly | Best practices evolve |
| `vector-stores.md` | Monthly | Vector store API changes |
| `deployment.md` | Quarterly | New deployment options |
| `error-handling.md` | As needed | New error types |
| `security.md` | Monthly | Security advisories |
| `testing.md` | Quarterly | Testing tools evolve |
| `troubleshooting.md` | As needed | New common issues |

### Content Review Process

**Quarterly Review**:
1. Check all external links (OpenAI docs, GitHub)
2. Verify code examples still work
3. Update version numbers
4. Remove deprecated patterns
5. Add new best practices

**Annual Review**:
1. Comprehensive rewrite if major framework changes
2. Consolidate similar patterns
3. Remove obsolete industry patterns
4. Update all examples to latest syntax

---

## Dependency Management

### Python Dependencies

```python
# requirements.txt versioning strategy

# Pin major versions, allow minor/patch updates
fastapi>=0.109.0,<0.110.0
openai>=1.12.0,<2.0.0

# Security-critical: pin exact versions
cryptography==41.0.7

# Development: allow latest
pytest>=7.4.3
```

### Node Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.0"  // Allow minor updates
  },
  "devDependencies": {
    "vite": "^5.0.0"   // Allow minor updates
  }
}
```

### Update Schedule

- **Security patches**: Immediate
- **Minor updates**: Monthly review
- **Major updates**: Quarterly review with testing

---

## Deprecation Policy

### Deprecation Process

1. **Announce** (Version N): Mark as deprecated in documentation
2. **Warn** (Version N+1): Add deprecation warnings in examples
3. **Remove** (Version N+2): Remove deprecated pattern

**Example Timeline**:
- v1.5.0: Announce deprecation of old vector store pattern
- v1.6.0: Add warnings, provide migration guide
- v2.0.0: Remove old pattern completely

### Deprecation Notice Format

```markdown
⚠️ **DEPRECATED**: This pattern is deprecated as of v1.5.0 and will be removed in v2.0.0.

**Reason**: OpenAI moved vector stores to beta namespace

**Migration**: See `references/migration-guides/v1-to-v2.md`
```

---

## Community Contributions

### Accepting Updates

When users suggest improvements:

1. **Evaluate**: Does it improve reusability?
2. **Verify**: Is it based on official documentation?
3. **Test**: Does it work with current versions?
4. **Document**: Is it well-documented?
5. **Integrate**: Add to appropriate reference file

### Contribution Guidelines

**Good Contributions**:
- New industry patterns with real use cases
- Security improvements with references
- Performance optimizations with benchmarks
- Bug fixes with reproduction steps

**Reject**:
- Requirement-specific patterns (not reusable)
- Unverified "best practices"
- Breaking changes without migration path
- Undocumented code

---

## Emergency Updates

### Critical Security Issues

**Process**:
1. **Assess**: Severity and impact
2. **Fix**: Update affected files immediately
3. **Test**: Verify fix works
4. **Release**: Push update as PATCH version
5. **Notify**: Document in security advisory

**Timeline**: Within 24 hours of disclosure

### API Breaking Changes

**Process**:
1. **Monitor**: OpenAI announces breaking change
2. **Plan**: Determine update strategy
3. **Update**: Modify references and examples
4. **Test**: Comprehensive testing
5. **Release**: MAJOR version bump
6. **Communicate**: Migration guide

**Timeline**: Before OpenAI deprecates old API

---

## Version History Template

Maintain version history in skill commits:

```markdown
## v1.1.0 (2026-04-15)

### Added
- New industry pattern: Real Estate
- Support for GPT-4 Turbo with Vision
- Streaming response examples

### Changed
- Updated OpenAI SDK to 1.15.0
- Improved error handling patterns

### Fixed
- Vector store initialization bug
- CORS configuration example

### Deprecated
- Old authentication pattern (remove in v2.0.0)

### Security
- Updated cryptography dependency
- Added rate limiting examples
```

---

## Maintenance Checklist

### Monthly
- [ ] Check OpenAI changelog
- [ ] Update dependencies (security patches)
- [ ] Review and respond to user feedback
- [ ] Test examples with latest SDK

### Quarterly
- [ ] Comprehensive reference file review
- [ ] Update all code examples
- [ ] Check external links
- [ ] Run skill-validator
- [ ] Update version numbers

### Annually
- [ ] Major framework review
- [ ] Consolidate patterns
- [ ] Remove obsolete content
- [ ] Comprehensive rewrite if needed

---

## Contact and Support

**Skill Maintainer**: Track via skill repository
**Issues**: Report via skill feedback mechanism
**Updates**: Monitor skill changelog
**Questions**: Use skill documentation first, then ask maintainer
