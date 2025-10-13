#!/bin/bash
# Safe Merge Script: fix/comment-notifications → main
# This script will help you merge your changes safely

set -e  # Exit on error

echo "🔍 Current branch: $(git branch --show-current)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Safe Merge Process Starting${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Step 1: Show current status
echo -e "${GREEN}Step 1: Checking current status...${NC}"
git status
echo ""

read -p "Press Enter to continue to Step 2..."

# Step 2: Fetch latest changes
echo -e "${GREEN}Step 2: Fetching latest changes from remote...${NC}"
git fetch origin
echo ""

# Show what's new in main
echo -e "${YELLOW}New commits in origin/main:${NC}"
git log main..origin/main --oneline --max-count=10 || echo "No new commits or main branch not found locally"
echo ""

read -p "Press Enter to continue to Step 3..."

# Step 3: Update local main branch
echo -e "${GREEN}Step 3: Updating local main branch...${NC}"
git checkout main
git pull origin main
echo ""

echo -e "${YELLOW}Your local main is now up to date!${NC}"
echo ""

read -p "Press Enter to continue to Step 4..."

# Step 4: Go back to feature branch
echo -e "${GREEN}Step 4: Switching back to fix/comment-notifications...${NC}"
git checkout fix/comment-notifications
echo ""

read -p "Press Enter to continue to Step 5 (THE MERGE)..."

# Step 5: Merge main into feature branch
echo -e "${GREEN}Step 5: Merging main INTO fix/comment-notifications...${NC}"
echo -e "${RED}⚠️  IMPORTANT: Conflicts may occur here!${NC}"
echo ""

if git merge main; then
    echo -e "${GREEN}✅ Merge completed successfully with no conflicts!${NC}"
    echo ""
else
    echo -e "${RED}❌ CONFLICTS DETECTED!${NC}"
    echo ""
    echo -e "${YELLOW}Conflicted files:${NC}"
    git status | grep "both modified" || git status
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  MERGE PAUSED - RESOLVE CONFLICTS${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Instructions:"
    echo "1. Open each conflicted file"
    echo "2. Look for <<<<<<< and >>>>>>> markers"
    echo "3. Keep BOTH main's features AND your fixes"
    echo "4. Remove the conflict markers"
    echo "5. Save the file"
    echo "6. Run: git add <filename>"
    echo "7. After ALL conflicts resolved, run: git commit"
    echo "8. Then re-run this script to continue"
    echo ""
    exit 1
fi

read -p "Press Enter to continue to Step 6..."

# Step 6: Show merge result
echo -e "${GREEN}Step 6: Verifying merge...${NC}"
echo ""
echo "Current branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"
echo ""

read -p "Press Enter to continue to Step 7..."

# Step 7: Push feature branch
echo -e "${GREEN}Step 7: Pushing updated feature branch...${NC}"
echo -e "${YELLOW}This will push fix/comment-notifications to remote${NC}"
echo ""

read -p "Are you ready to push? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin fix/comment-notifications
    echo -e "${GREEN}✅ Feature branch pushed!${NC}"
else
    echo -e "${YELLOW}Skipping push. You can push later with:${NC}"
    echo "git push origin fix/comment-notifications"
fi
echo ""

read -p "Press Enter to continue to Step 8..."

# Step 8: Merge to main
echo -e "${GREEN}Step 8: Merging to main...${NC}"
echo -e "${RED}⚠️  This is the final step - merging to main!${NC}"
echo ""

read -p "Ready to merge to main and push? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git checkout main
    git merge fix/comment-notifications
    echo ""
    echo -e "${YELLOW}Merged! Now pushing to origin/main...${NC}"
    git push origin main
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ MERGE COMPLETE!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Your notification fixes are now in main! 🎉"
else
    echo -e "${YELLOW}Merge to main skipped.${NC}"
    echo "When ready, run:"
    echo "  git checkout main"
    echo "  git merge fix/comment-notifications"
    echo "  git push origin main"
fi

echo ""
echo -e "${GREEN}Done!${NC}"

