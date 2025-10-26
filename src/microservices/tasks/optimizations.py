# Task Service Optimizations
# This file contains optimized endpoints and caching mechanisms

from functools import lru_cache
from typing import Dict, List, Any
import time
import json

# In-memory cache for user data (in production, use Redis)
USER_CACHE = {}
PROJECT_CACHE = {}
CACHE_TTL = 300  # 5 minutes

def get_cached_user(user_id: str) -> Dict[str, Any]:
    """Get user data from cache or fetch and cache it"""
    cache_key = f"user_{user_id}"
    current_time = time.time()
    
    if cache_key in USER_CACHE:
        cached_data, timestamp = USER_CACHE[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data
    
    # Fetch from database
    try:
        response = supabase.table("user").select("user_id, name, email, department").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            USER_CACHE[cache_key] = (user_data, current_time)
            return user_data
    except Exception as e:
        print(f"Error fetching user {user_id}: {e}")
    
    return None

def get_cached_project(project_id: str) -> Dict[str, Any]:
    """Get project data from cache or fetch and cache it"""
    cache_key = f"project_{project_id}"
    current_time = time.time()
    
    if cache_key in PROJECT_CACHE:
        cached_data, timestamp = PROJECT_CACHE[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data
    
    # Fetch from database (assuming we have access to project service)
    # For now, return None - this would need to be implemented based on your architecture
    return None

def batch_fetch_users(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch multiple users in a single query"""
    if not user_ids:
        return {}
    
    # Check cache first
    users_data = {}
    missing_ids = []
    current_time = time.time()
    
    for user_id in user_ids:
        cache_key = f"user_{user_id}"
        if cache_key in USER_CACHE:
            cached_data, timestamp = USER_CACHE[cache_key]
            if current_time - timestamp < CACHE_TTL:
                users_data[user_id] = cached_data
                continue
        missing_ids.append(user_id)
    
    # Fetch missing users in batch
    if missing_ids:
        try:
            response = supabase.table("user").select("user_id, name, email, department").in_("user_id", missing_ids).execute()
            if response.data:
                for user in response.data:
                    user_id = user["user_id"]
                    users_data[user_id] = user
                    USER_CACHE[f"user_{user_id}"] = (user, current_time)
        except Exception as e:
            print(f"Error batch fetching users: {e}")
    
    return users_data

def optimize_task_with_metadata(task_data: Dict[str, Any], user_cache: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """Optimize task data with cached user and project information"""
    optimized_task = task_data.copy()
    
    # Add user names
    if task_data.get("owner_id") and user_cache:
        owner_data = user_cache.get(task_data["owner_id"])
        if owner_data:
            optimized_task["owner_name"] = owner_data.get("name", "Unknown User")
            optimized_task["owner_email"] = owner_data.get("email", "")
    
    # Add collaborator names
    collaborators = task_data.get("collaborators", [])
    if isinstance(collaborators, str):
        try:
            collaborators = json.loads(collaborators)
        except:
            collaborators = []
    
    if collaborators and user_cache:
        collaborator_names = []
        for collab_id in collaborators:
            collab_data = user_cache.get(collab_id)
            if collab_data:
                collaborator_names.append({
                    "user_id": collab_id,
                    "name": collab_data.get("name", "Unknown User"),
                    "email": collab_data.get("email", "")
                })
        optimized_task["collaborator_details"] = collaborator_names
    
    return optimized_task