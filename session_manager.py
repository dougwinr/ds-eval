import json
import os
from datetime import datetime, timedelta
from database import Database

class SessionManager:
    def __init__(self, session_file="sessions.json"):
        self.session_file = session_file
        self.db = Database()
        self.load_sessions()
    
    def load_sessions(self):
        """Load sessions from file"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    self.sessions = json.load(f)
            except:
                self.sessions = {}
        else:
            self.sessions = {}
    
    def save_sessions(self):
        """Save sessions to file"""
        with open(self.session_file, 'w') as f:
            json.dump(self.sessions, f)
    
    def create_session(self, username, is_admin, current_page="home"):
        """Create a new session"""
        # Create session in database
        session_token = self.db.create_session(username, is_admin)
        
        if session_token:
            # Store in file for persistence
            self.sessions[session_token] = {
                'username': username,
                'is_admin': is_admin,
                'current_page': current_page,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            self.save_sessions()
            return session_token
        return None
    
    def validate_session(self, session_token):
        """Validate a session token"""
        # First check database
        user_info = self.db.validate_session(session_token)
        
        if user_info:
            # Update file session if needed
            if session_token in self.sessions:
                self.sessions[session_token]['expires_at'] = (datetime.now() + timedelta(hours=24)).isoformat()
                self.save_sessions()
            return user_info
        
        # If not in database, check file
        if session_token in self.sessions:
            session_data = self.sessions[session_token]
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            
            if datetime.now() < expires_at:
                # Session is still valid, restore to database
                self.db.create_session(session_data['username'], session_data['is_admin'])
                return {
                    'username': session_data['username'],
                    'is_admin': session_data['is_admin']
                }
            else:
                # Session expired, remove from file
                del self.sessions[session_token]
                self.save_sessions()
        
        return None
    
    def delete_session(self, session_token):
        """Delete a session"""
        # Delete from database
        self.db.delete_session(session_token)
        
        # Delete from file
        if session_token in self.sessions:
            del self.sessions[session_token]
            self.save_sessions()
    
    def update_current_page(self, session_token, current_page):
        """Update the current page for a session"""
        if session_token in self.sessions:
            self.sessions[session_token]['current_page'] = current_page
            self.save_sessions()
    
    def clear_all_sessions(self):
        """Clear all sessions (for logout)"""
        # Clear all sessions from file
        self.sessions = {}
        self.save_sessions()
        
        # Clean up database sessions
        self.db.cleanup_expired_sessions()
    
    def get_current_session(self):
        """Get the current active session from file"""
        if not self.sessions:
            return None
        
        # Get the most recent session
        current_time = datetime.now()
        valid_sessions = []
        
        for token, session_data in self.sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if current_time < expires_at:
                valid_sessions.append((token, session_data))
        
        if valid_sessions:
            # Return the most recent valid session
            valid_sessions.sort(key=lambda x: x[1]['created_at'], reverse=True)
            token, session_data = valid_sessions[0]
            return {
                'username': session_data['username'],
                'is_admin': session_data['is_admin'],
                'current_page': session_data.get('current_page', 'home'),
                'token': token
            }
        
        return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_tokens = []
        
        for token, session_data in self.sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if current_time >= expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
        
        if expired_tokens:
            self.save_sessions()
        
        # Also cleanup database
        self.db.cleanup_expired_sessions()
