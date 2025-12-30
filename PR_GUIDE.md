# How to Create a Pull Request on Your GitHub Repository

## Quick Steps

### 1. Create a new branch for your changes
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make your changes
Edit files, add features, fix bugs, etc.

### 3. Stage and commit your changes
```bash
git add .
git commit -m "Description of your changes"
```

### 4. Push the branch to GitHub
```bash
git push -u origin feature/your-feature-name
```

### 5. Create the Pull Request

**Option A: Using GitHub Web UI (Easiest)**
- After pushing, GitHub will show a banner on your repo page with a "Compare & pull request" button
- Click it, fill in the PR title and description
- Click "Create pull request"

**Option B: Using GitHub CLI (if installed)**
```bash
gh pr create --title "Your PR Title" --body "Description of changes"
```

**Option C: Direct URL**
- Go to: `https://github.com/gokulanv/LeetCode-AI-Revision/compare/main...feature/your-feature-name`
- Fill in details and create the PR

### 6. Review and merge
- Review your PR on GitHub
- Once satisfied, click "Merge pull request"
- Delete the branch if prompted (optional, GitHub suggests this)

## Example Workflow

```bash
# 1. Create branch
git checkout -b add-new-feature

# 2. Make changes (edit files)

# 3. Commit
git add .
git commit -m "Add new feature"

# 4. Push
git push -u origin add-new-feature

# 5. Create PR via GitHub web or CLI
gh pr create
```

## Notes
- You can create PRs on your own repo - it's great for code review and maintaining a clean main branch
- Always create feature branches instead of committing directly to main
- Write clear PR descriptions explaining what and why


