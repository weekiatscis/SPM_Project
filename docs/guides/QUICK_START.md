# Quick Start: Merge Your Notification Fixes to Main

## Option 1: Use the Automated Script (RECOMMENDED)

```bash
cd /Users/zenia/Documents/GitHub/SPM_Project
./safe_merge.sh
```

The script will guide you through each step interactively!

---

## Option 2: Manual Commands

If you prefer to run commands manually:

```bash
cd /Users/zenia/Documents/GitHub/SPM_Project

# 1. Fetch latest changes
git fetch origin

# 2. Update your local main
git checkout main
git pull origin main

# 3. Go back to your feature branch
git checkout fix/comment-notifications

# 4. Merge main INTO your feature branch (conflicts appear here if any)
git merge main

# 5. If conflicts occur:
#    - Open conflicted files
#    - Keep BOTH main features AND your fixes
#    - git add <filename> after resolving each file
#    - git commit after all conflicts resolved

# 6. Push your feature branch
git push origin fix/comment-notifications

# 7. Merge to main
git checkout main
git merge fix/comment-notifications
git push origin main

# Done! 🎉
```

---

## Key Principles for Conflict Resolution

1. **KEEP** all new features from main (don't delete them!)
2. **KEEP** all your notification fixes
3. **COMBINE** intelligently when both change the same area
4. **TEST** after merging but before pushing to main

---

## Files That May Have Conflicts

Watch out for these files (you modified them):
- `src/microservices/tasks/task_service.py`
- `src/microservices/projects/project_service.py`
- `src/microservices/notifications/notification_service.py`
- `src/microservices/notifications/email_service.py`
- `src/components/notifications/NotificationDropdown.vue`
- Vue component files in `src/components/tasks/`

---

## Emergency Commands

**Cancel a merge in progress:**
```bash
git merge --abort
```

**Undo last commit (before pushing):**
```bash
git reset --hard HEAD~1
```

**See what changed in a file:**
```bash
git diff main fix/comment-notifications -- <filename>
```

---

## Need Help?

1. Read the detailed guide: `MERGE_GUIDE.md`
2. Check conflict resolution examples in the guide
3. Ask for help if conflicts are complex!

**Remember**: The safe_merge.sh script pauses at each step so you can review!

