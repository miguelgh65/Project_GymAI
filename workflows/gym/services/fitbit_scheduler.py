import sys
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import requests
import base64
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fitbit_scheduler')

# Load environment variables
load_dotenv()

# Database connection config
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'postgres_gymdb'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_fitbit_credentials():
    """Get Fitbit API credentials from environment variables"""
    return {
        'client_id': os.getenv('FITBIT_CLIENT_ID'),
        'client_secret': os.getenv('FITBIT_CLIENT_SECRET'),
        'token_url': os.getenv('FITBIT_TOKEN_URL', 'https://api.fitbit.com/oauth2/token')
    }

def refresh_tokens():
    """
    Check for expiring Fitbit tokens and refresh them.
    This function will be called on a schedule.
    """
    logger.info("🔄 Starting Fitbit token refresh check")
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get tokens that expire within the next hour
        expire_threshold = datetime.now() + timedelta(hours=1)
        query = """
            SELECT user_id, refresh_token, expires_at 
            FROM fitbit_tokens 
            WHERE expires_at < %s
        """
        
        cur.execute(query, (expire_threshold,))
        tokens_to_refresh = cur.fetchall()
        
        logger.info(f"Found {len(tokens_to_refresh)} tokens that need refreshing")
        
        # Get Fitbit credentials
        credentials = get_fitbit_credentials()
        
        # Process each token that needs refreshing
        for token_data in tokens_to_refresh:
            user_id, refresh_token, expires_at = token_data
            try:
                logger.info(f"Refreshing token for user {user_id}")
                
                # Create authorization header
                auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
                auth_bytes = auth_string.encode('utf-8')
                auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                
                headers = {
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                # Request data
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
                
                # Make the request to refresh token
                response = requests.post(
                    credentials['token_url'],
                    headers=headers,
                    data=data
                )
                
                if response.status_code == 200:
                    new_tokens = response.json()
                    
                    # Calculate new expiration time
                    expires_in = new_tokens.get('expires_in', 28800)  # Default 8 hours
                    new_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    # Update the token in database
                    update_query = """
                        UPDATE fitbit_tokens
                        SET access_token = %s, 
                            refresh_token = %s,
                            expires_at = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """
                    
                    cur.execute(
                        update_query,
                        (
                            new_tokens.get('access_token'),
                            new_tokens.get('refresh_token'),
                            new_expires_at,
                            user_id
                        )
                    )
                    
                    logger.info(f"✅ Successfully refreshed token for user {user_id}")
                else:
                    logger.error(f"❌ Failed to refresh token for user {user_id}: {response.status_code}")
                    logger.error(f"Response: {response.text[:200]}")
            except Exception as e:
                logger.error(f"❌ Error refreshing token for user {user_id}: {str(e)}")
        
        # Commit all changes
        conn.commit()
        
        # Close database connection
        cur.close()
        conn.close()
        
        logger.info("🏁 Token refresh check completed")
    except Exception as e:
        logger.error(f"❌ Error in refresh_tokens job: {str(e)}")

def sync_fitbit_data():
    """
    Sync the latest data from Fitbit for all users.
    This function will be called on a schedule.
    """
    logger.info("🔄 Starting Fitbit data sync")
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get all valid tokens
        query = """
            SELECT user_id, access_token
            FROM fitbit_tokens 
            WHERE expires_at > CURRENT_TIMESTAMP
        """
        
        cur.execute(query)
        valid_tokens = cur.fetchall()
        
        logger.info(f"Found {len(valid_tokens)} users with valid tokens")
        
        # Process each user
        for token_data in valid_tokens:
            user_id, access_token = token_data
            try:
                logger.info(f"Syncing data for user {user_id}")
                
                # TODO: Implement Fitbit data sync logic here
                # This would involve fetching activity, sleep, etc. data
                # and storing it in your database
                
                # For now, just log that we would sync data
                logger.info(f"✅ Would sync data for user {user_id}")
                
            except Exception as e:
                logger.error(f"❌ Error syncing data for user {user_id}: {str(e)}")
        
        # Close database connection
        cur.close()
        conn.close()
        
        logger.info("🏁 Data sync completed")
    except Exception as e:
        logger.error(f"❌ Error in sync_fitbit_data job: {str(e)}")

def start_scheduler():
    """Initialize and start the scheduler for periodic tasks"""
    scheduler = BackgroundScheduler()
    
    # Add job to refresh tokens every hour
    scheduler.add_job(
        refresh_tokens,
        trigger=IntervalTrigger(hours=1),
        id='refresh_fitbit_tokens',
        name='Refresh Fitbit Tokens',
        replace_existing=True
    )
    
    # Add job to sync data every 3 hours
    # Commented out for now - uncomment when you implement the sync logic
    # scheduler.add_job(
    #     sync_fitbit_data,
    #     trigger=IntervalTrigger(hours=3),
    #     id='sync_fitbit_data',
    #     name='Sync Fitbit Data',
    #     replace_existing=True
    # )
    
    # Start the scheduler
    scheduler.start()
    logger.info("⏰ Fitbit scheduler started")
    
    return scheduler