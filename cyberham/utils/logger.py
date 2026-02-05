"""
Centralized logging utilities for security-relevant events.

This module provides logging functions for:
- Authentication attempts (success/failure)
- Elevated privilege operations (deletions, awards)
- CRUD operations on sensitive data
"""

import logging
from datetime import datetime
from typing import Optional
from cyberham.types import Permissions

# Create a dedicated security logger
security_logger = logging.getLogger("cyberham.security")


def log_auth_attempt(
    token: str,
    permission: Permissions,
    success: bool,
    endpoint: Optional[str] = None,
) -> None:
    """
    Log authentication attempts to the dashboard.
    
    Args:
        token: The authentication token used (first 8 chars for privacy)
        permission: The permission level of the token
        success: Whether the authentication was successful
        endpoint: Optional endpoint being accessed
    """
    token_preview = token[:8] + "..." if len(token) > 8 else token
    timestamp = datetime.now().isoformat()
    status = "SUCCESS" if success else "FAILED"
    
    message = f"[AUTH {status}] Token: {token_preview}, Permission: {permission.name}, Time: {timestamp}"
    if endpoint:
        message += f", Endpoint: {endpoint}"
    
    if success:
        security_logger.info(message)
    else:
        security_logger.warning(message)


def log_elevated_operation(
    operation: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """
    Log operations requiring elevated privileges.
    
    Args:
        operation: Description of the operation (e.g., "delete_all_events", "award_points")
        user_id: Discord user ID performing the operation
        user_name: Discord user name
        details: Additional context about the operation
    """
    timestamp = datetime.now().isoformat()
    message = f"[ELEVATED] Operation: {operation}, Time: {timestamp}"
    
    if user_id:
        message += f", User ID: {user_id}"
    if user_name:
        message += f", User Name: {user_name}"
    if details:
        message += f", Details: {details}"
    
    security_logger.warning(message)


def log_crud_operation(
    operation: str,
    table: str,
    token: Optional[str] = None,
    permission: Optional[Permissions] = None,
    record_id: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """
    Log CRUD operations on database tables.
    
    Args:
        operation: Type of operation (CREATE, UPDATE, DELETE, REPLACE)
        table: Name of the database table
        token: Authentication token (first 8 chars for privacy)
        permission: Permission level of the user
        record_id: Identifier of the record being modified
        details: Additional context
    """
    timestamp = datetime.now().isoformat()
    token_preview = token[:8] + "..." if token and len(token) > 8 else token or "N/A"
    perm_name = permission.name if permission else "N/A"
    
    message = f"[CRUD {operation}] Table: {table}, Token: {token_preview}, Permission: {perm_name}, Time: {timestamp}"
    
    if record_id:
        message += f", Record ID: {record_id}"
    if details:
        message += f", Details: {details}"
    
    if operation == "DELETE":
        security_logger.warning(message)
    else:
        security_logger.info(message)


def log_dashboard_access(
    endpoint: str,
    token: str,
    permission: Permissions,
    method: str = "GET",
) -> None:
    """
    Log access to dashboard endpoints.
    
    Args:
        endpoint: The endpoint being accessed
        token: Authentication token (first 8 chars for privacy)
        permission: Permission level of the user
        method: HTTP method
    """
    token_preview = token[:8] + "..." if len(token) > 8 else token
    timestamp = datetime.now().isoformat()
    
    message = f"[DASHBOARD] Method: {method}, Endpoint: {endpoint}, Token: {token_preview}, Permission: {permission.name}, Time: {timestamp}"
    
    security_logger.info(message)
