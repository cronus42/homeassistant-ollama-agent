# Release Process

This document describes the release process for the Home Assistant Ollama Conversation Integration.

## Prerequisites

1. GitHub CLI installed and authenticated (gh command)
2. Clean working tree - no uncommitted changes
3. Tests passing - run "make test-simple" before release

## Version Numbering

Semantic Versioning (semver.org):
- Major (X.0.0): Breaking changes
- Minor (0.X.0): New features, backward compatible  
- Patch (0.0.X): Bug fixes, backward compatible

## Release Steps

### 1. Update Version

Edit custom_components/ollama_conversation/manifest.json version field

### 2. Update CHANGELOG.md

Add new section at top with version, date, and changes

### 3. Commit Changes

git add custom_components/ollama_conversation/manifest.json CHANGELOG.md
git commit -m "Bump version to X.X.X"
git push origin main

### 4. Run Release Command

With tests: make release
Without tests: make release-quick

This will create tag, push to GitHub, and create GitHub release

### 5. Verify Release

Check GitHub releases page and verify tag exists

## Manual Release

git tag -a "vX.X.X" -m "Release vX.X.X"
git push origin "vX.X.X"
gh release create "vX.X.X" --title "Release vX.X.X" --notes-file CHANGELOG.md

## Troubleshooting

Tag already exists: Delete with git tag -d and git push origin :refs/tags/vX.X.X
Working tree dirty: Commit or stash changes
gh not found: Install GitHub CLI

## Release Checklist

- Version updated in manifest.json
- CHANGELOG.md updated
- Tests passing
- Changes committed and pushed
- Working tree clean
- GitHub CLI authenticated
- Release created
- GitHub release verified
- Tag pushed and visible

## Quick Reference

make version          - Check current version
make test-simple      - Run tests
make release          - Create release with tests
make release-quick    - Create release without tests
gh release view       - View latest release
