"""
Redis-based session storage for Flask.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

from flask import current_app
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

logger = logging.getLogger(__name__)


class RedisSession(CallbackDict, SessionMixin):
    """Redis-backed session implementation."""
    
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.permanent = True


class RedisSessionInterface(SessionInterface):
    """Redis session interface for Flask."""
    
    serializer = json
    session_class = RedisSession
    
    def __init__(self, redis_client=None, key_prefix='session:', 
                 use_signer=True, permanent=True):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent
    
    def generate_sid(self):
        """Generate a new session ID."""
        return str(uuid4())
    
    def get_redis_expiration_time(self, app, session):
        """Get Redis expiration time for session."""
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)
    
    def get_redis_key(self, sid):
        """Get Redis key for session ID."""
        return f"{self.key_prefix}{sid}"
    
    def open_session(self, app, request):
        """Open a session from Redis."""
        if not self.redis_client or not self.redis_client.is_available():
            logger.warning("Redis not available, using default session")
            return None
        
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        
        if self.use_signer:
            try:
                sid = self.get_signing_serializer(app).loads(sid)
            except Exception as e:
                logger.warning(f"Invalid session signature: {e}")
                sid = self.generate_sid()
                return self.session_class(sid=sid, new=True)
        
        try:
            redis_key = self.get_redis_key(sid)
            data = self.redis_client.get(redis_key)
            
            if data is not None:
                try:
                    session_data = self.serializer.loads(data) if isinstance(data, str) else data
                    return self.session_class(session_data, sid=sid)
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to deserialize session data: {e}")
            
            # Session not found or invalid, create new one
            return self.session_class(sid=sid, new=True)
            
        except Exception as e:
            logger.error(f"Error opening session: {e}")
            return self.session_class(sid=self.generate_sid(), new=True)
    
    def save_session(self, app, session, response):
        """Save session to Redis."""
        if not self.redis_client or not self.redis_client.is_available():
            logger.warning("Redis not available, session not saved")
            return
        
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        if not session:
            # Delete session
            if session.modified:
                try:
                    redis_key = self.get_redis_key(session.sid)
                    self.redis_client.delete(redis_key)
                    response.delete_cookie(
                        app.session_cookie_name,
                        domain=domain,
                        path=path
                    )
                except Exception as e:
                    logger.error(f"Error deleting session: {e}")
            return
        
        # Determine expiration
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        
        try:
            # Serialize session data
            session_data = dict(session)
            serialized_data = self.serializer.dumps(session_data)
            
            # Save to Redis
            redis_key = self.get_redis_key(session.sid)
            timeout = int(redis_exp.total_seconds()) if redis_exp else None
            
            if not self.redis_client.set(redis_key, serialized_data, timeout):
                logger.error("Failed to save session to Redis")
                return
            
            # Set cookie
            sid = session.sid
            if self.use_signer:
                sid = self.get_signing_serializer(app).dumps(sid)
            
            response.set_cookie(
                app.session_cookie_name,
                sid,
                expires=cookie_exp,
                httponly=self.get_cookie_httponly(app),
                domain=domain,
                path=path,
                secure=self.get_cookie_secure(app),
                samesite=self.get_cookie_samesite(app)
            )
            
        except Exception as e:
            logger.error(f"Error saving session: {e}")


class SessionManager:
    """High-level session management utilities."""
    
    def __init__(self, redis_client, key_prefix='session:'):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID."""
        if not self.redis_client.is_available():
            return None
        
        try:
            redis_key = f"{self.key_prefix}{session_id}"
            data = self.redis_client.get(redis_key)
            
            if data:
                return json.loads(data) if isinstance(data, str) else data
            return None
            
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session by session ID."""
        if not self.redis_client.is_available():
            return False
        
        try:
            redis_key = f"{self.key_prefix}{session_id}"
            return bool(self.redis_client.delete(redis_key))
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        if not self.redis_client.is_available():
            return 0
        
        try:
            # Find all session keys
            pattern = f"{self.key_prefix}*"
            session_keys = self.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in session_keys:
                session_data = self.redis_client.get(key)
                if session_data:
                    try:
                        data = json.loads(session_data) if isinstance(session_data, str) else session_data
                        if data.get('user_id') == user_id:
                            if self.redis_client.delete(key):
                                deleted_count += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get active sessions, optionally filtered by user."""
        if not self.redis_client.is_available():
            return {}
        
        try:
            pattern = f"{self.key_prefix}*"
            session_keys = self.redis_client.keys(pattern)
            
            active_sessions = {}
            for key in session_keys:
                session_data = self.redis_client.get(key)
                if session_data:
                    try:
                        data = json.loads(session_data) if isinstance(session_data, str) else session_data
                        
                        # Filter by user if specified
                        if user_id and data.get('user_id') != user_id:
                            continue
                        
                        session_id = key.replace(self.key_prefix, '')
                        active_sessions[session_id] = {
                            'user_id': data.get('user_id'),
                            'created_at': data.get('created_at'),
                            'last_activity': data.get('last_activity'),
                            'ip_address': data.get('ip_address'),
                            'user_agent': data.get('user_agent')
                        }
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return {}
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles this automatically, but useful for monitoring)."""
        if not self.redis_client.is_available():
            return 0
        
        try:
            pattern = f"{self.key_prefix}*"
            session_keys = self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in session_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error checking expired sessions: {e}")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if not self.redis_client.is_available():
            return {'error': 'Redis not available'}
        
        try:
            pattern = f"{self.key_prefix}*"
            session_keys = self.redis_client.keys(pattern)
            
            total_sessions = len(session_keys)
            user_sessions = {}
            
            for key in session_keys:
                session_data = self.redis_client.get(key)
                if session_data:
                    try:
                        data = json.loads(session_data) if isinstance(session_data, str) else session_data
                        user_id = data.get('user_id', 'anonymous')
                        user_sessions[user_id] = user_sessions.get(user_id, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            return {
                'total_sessions': total_sessions,
                'unique_users': len([u for u in user_sessions.keys() if u != 'anonymous']),
                'anonymous_sessions': user_sessions.get('anonymous', 0),
                'user_sessions': user_sessions
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {'error': str(e)}