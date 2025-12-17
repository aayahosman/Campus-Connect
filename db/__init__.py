"""
Database Module Package

This package contains all database abstraction layers for Campus Connect.
Each module provides functions for CRUD operations on a specific entity:

  - login_db: User authentication and registration
  - event_db: Event management (create, list, update, delete)
  - resources_db: Resource management (create, list, update, delete)
  - services_db: Service management (create, list, update, delete)
  - comment_db: Comments on events and resources
  - vote_db: Voting/rating system for events and resources

All functions accept a database connection as their first parameter.
Using parameterized queries prevents SQL injection attacks.
"""
