#!/usr/bin/env python3
"""
Auto-resolve git conflicts by keeping both versions intelligently
"""

def resolve_task_service_conflicts():
    """Resolve conflicts in task_service.py"""
    with open('src/microservices/tasks/task_service.py', 'r') as f:
        content = f.read()
    
    # Pattern 1: Simple select query conflict (keep main's version with recurrence fields)
    content = content.replace(
        '''<<<<<<< HEAD
            .select("task_id,title,due_date,status,priority,description,created_at,owner_id,project_id,collaborators")
=======
            .select("task_id,title,due_date,status,priority,description,created_at,updated_at,owner_id,project_id,collaborators,isSubtask,parent_task_id,recurrence")
>>>>>>> main''',
        '''            .select("task_id,title,due_date,status,priority,description,created_at,updated_at,owner_id,project_id,collaborators,isSubtask,parent_task_id,recurrence")'''
    )
    
    # Write back
    with open('src/microservices/tasks/task_service.py', 'w') as f:
        f.write(content)
    
    print("✅ Resolved task_service.py conflicts")

if __name__ == '__main__':
    resolve_task_service_conflicts()

