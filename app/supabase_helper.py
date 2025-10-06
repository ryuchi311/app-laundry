"""
Optional Supabase Client Integration

This module provides helper functions to use Supabase features beyond basic PostgreSQL.
You can use this for:
- Real-time subscriptions (live updates when data changes)
- Supabase Auth (alternative to Flask-Login)
- Storage API (file uploads with CDN)
- Edge Functions
- Row Level Security policies

Note: This is OPTIONAL. Your Flask app works fine with just PostgreSQL via SQLAlchemy.

Installation:
    pip install -r requirements.txt
    
    This will install the 'supabase' package. The import error you see is expected
    until you run the installation command.
"""

import os
from typing import Optional, Any

# Only import if supabase package is installed
# Note: Import error is expected until you run: pip install -r requirements.txt
try:
    from supabase import create_client  # type: ignore[import-untyped]
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None  # type: ignore


class SupabaseHelper:
    """
    Helper class to interact with Supabase features.
    
    Usage:
        from app.supabase_helper import supabase_helper
        
        # Get real-time updates
        supabase_helper.subscribe_to_table('laundry', callback_function)
        
        # Upload file
        supabase_helper.upload_file('receipts', 'file.pdf', file_data)
    """
    
    def __init__(self):
        self.client: Optional[Any] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase client from environment variables"""
        if not SUPABASE_AVAILABLE:
            return
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if url and key:
            try:
                self.client = create_client(url, key)
            except Exception as e:
                print(f"Warning: Could not initialize Supabase client: {e}")
    
    def is_available(self) -> bool:
        """Check if Supabase client is available and configured"""
        return self.client is not None
    
    def subscribe_to_table(self, table_name: str, callback, event: str = "*"):
        """
        Subscribe to real-time updates on a table.
        
        Args:
            table_name: Name of the table to watch
            callback: Function to call when data changes
            event: Event type ('INSERT', 'UPDATE', 'DELETE', or '*' for all)
        
        Example:
            def on_order_update(payload):
                order_id = payload['data']['id']
                print(f"Order {order_id} was updated!")
            
            supabase_helper.subscribe_to_table('laundry', on_order_update, 'UPDATE')
        """
        if not self.is_available():
            print("Supabase client not available for real-time subscriptions")
            return None
        
        try:
            return (
                self.client.table(table_name)
                .on(event, callback)
                .subscribe()
            )
        except Exception as e:
            print(f"Error subscribing to table {table_name}: {e}")
            return None
    
    def upload_file(self, bucket: str, path: str, file_data: bytes):
        """
        Upload file to Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
            file_data: File content as bytes
        
        Returns:
            dict: Upload response with 'path' and 'fullPath'
        
        Example:
            with open('receipt.pdf', 'rb') as f:
                result = supabase_helper.upload_file('receipts', 'order_123.pdf', f.read())
                print(f"File URL: {result['publicURL']}")
        """
        if not self.is_available():
            raise Exception("Supabase client not available for storage operations")
        
        try:
            result = self.client.storage.from_(bucket).upload(path, file_data)
            return result
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise
    
    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Get public URL for a file in Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
        
        Returns:
            str: Public URL
        """
        if not self.is_available():
            raise Exception("Supabase client not available")
        
        try:
            result = self.client.storage.from_(bucket).get_public_url(path)
            return result
        except Exception as e:
            print(f"Error getting public URL: {e}")
            raise
    
    def delete_file(self, bucket: str, path: str):
        """
        Delete file from Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
        """
        if not self.is_available():
            raise Exception("Supabase client not available")
        
        try:
            result = self.client.storage.from_(bucket).remove([path])
            return result
        except Exception as e:
            print(f"Error deleting file: {e}")
            raise
    
    def call_edge_function(self, function_name: str, body: dict = None):
        """
        Call a Supabase Edge Function.
        
        Args:
            function_name: Name of the edge function
            body: Request body as dictionary
        
        Returns:
            Response from edge function
        
        Example:
            result = supabase_helper.call_edge_function('generate-receipt', {
                'order_id': 123
            })
        """
        if not self.is_available():
            raise Exception("Supabase client not available")
        
        try:
            result = self.client.functions.invoke(function_name, invoke_options={"body": body})
            return result
        except Exception as e:
            print(f"Error calling edge function: {e}")
            raise
    
    def query_table(self, table_name: str):
        """
        Direct query to Supabase table (alternative to SQLAlchemy).
        
        This is useful for quick queries or when you want to use Supabase's
        auto-generated REST API instead of SQLAlchemy.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Supabase table query object
        
        Example:
            # Get all active customers
            customers = (
                supabase_helper.query_table('customer')
                .select('*')
                .eq('is_active', True)
                .execute()
            )
            
            # Get orders with customer info
            orders = (
                supabase_helper.query_table('laundry')
                .select('*, customer(*)')
                .order('date_created', desc=True)
                .limit(10)
                .execute()
            )
        """
        if not self.is_available():
            raise Exception("Supabase client not available")
        
        return self.client.table(table_name)


# Global instance
supabase_helper = SupabaseHelper()


# Example usage functions for common patterns

def setup_realtime_order_updates(socketio):
    """
    Example: Setup real-time order updates using SocketIO.
    
    This will emit SocketIO events when orders are updated in the database,
    allowing for live dashboard updates without polling.
    
    Args:
        socketio: Flask-SocketIO instance
    
    Usage:
        from app import socketio
        from app.supabase_helper import setup_realtime_order_updates
        
        setup_realtime_order_updates(socketio)
    """
    def on_order_change(payload):
        event_type = payload.get('eventType')  # INSERT, UPDATE, DELETE
        data = payload.get('new', {})  # New data
        old_data = payload.get('old', {})  # Old data (for UPDATE/DELETE)
        
        # Emit SocketIO event to connected clients
        socketio.emit('order_updated', {
            'type': event_type,
            'order': data,
            'old_order': old_data
        }, namespace='/notifications')
    
    if supabase_helper.is_available():
        supabase_helper.subscribe_to_table('laundry', on_order_change)
        print("✓ Real-time order updates enabled")
    else:
        print("⚠ Supabase client not available for real-time updates")


def setup_customer_search_with_fts():
    """
    Example: Setup full-text search for customers.
    
    PostgreSQL has excellent full-text search capabilities.
    This is much faster than LIKE queries for large datasets.
    
    Usage:
        results = search_customers_fulltext("John Doe")
    """
    def search_customers_fulltext(query: str, limit: int = 20):
        if not supabase_helper.is_available():
            # Fallback to SQLAlchemy LIKE query
            from app.models import Customer
            from app import db
            return Customer.query.filter(
                Customer.full_name.ilike(f"%{query}%")
            ).limit(limit).all()
        
        # Use PostgreSQL full-text search
        result = (
            supabase_helper.query_table('customer')
            .select('*')
            .text_search('full_name', query)
            .limit(limit)
            .execute()
        )
        return result.data
    
    return search_customers_fulltext


# Decorator for Supabase Auth (if you want to migrate from Flask-Login)
def supabase_auth_required(f):
    """
    Decorator to require Supabase authentication.
    
    This is an alternative to Flask-Login's @login_required.
    Only use this if you migrate to Supabase Auth completely.
    
    Example:
        @app.route('/dashboard')
        @supabase_auth_required
        def dashboard():
            return render_template('dashboard.html')
    """
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not supabase_helper.is_available():
            return jsonify({"error": "Supabase auth not configured"}), 500
        
        # Get JWT token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "No authorization token"}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Verify token with Supabase
            user = supabase_helper.client.auth.get_user(token)
            if not user:
                return jsonify({"error": "Invalid token"}), 401
            
            # Add user to request context
            request.supabase_user = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 401
    
    return decorated_function
