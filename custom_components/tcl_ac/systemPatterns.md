## Git Command Patterns

1. Never ask for confirmation before using git commands
2. Chain multiple git commands together when possible (e.g., `git add && git commit && git tag`)
3. Assume approval is granted for standard git operations (add, commit, push, tag)
4. Only require approval for destructive operations (force push, branch deletion, etc.)

## Version Bump Workflow

1. Update version in manifest.json
2. Chain commands: `git add && git commit -m "Bump version" && git tag`
3. Push changes: `git push origin main && git push origin <tag>`
4. Create release: `gh release create`
