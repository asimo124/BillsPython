#!/usr/bin/env python3
"""
Script to queue a bill generation job
Usage: python add_bill_job.py [user_id] [num_reps]
"""
import sys
import mysql.connector
import json
from datetime import datetime

def add_bill_job(user_id=1, num_reps=42):
    """Add a bill generation job to the queue"""
    try:
        # Connect to database
        db = mysql.connector.connect(
            host="localhost",
            user="", 
            password="",
            database=""
        )
        cursor = db.cursor()
        
        # Prepare job parameters
        params = {}
        
        # Create the command for the worker
        command = f"generate_bill_dates:{json.dumps(params)}"
        
        # Insert job into queue
        query = """INSERT INTO date_job (command, status, created_at) 
                   VALUES (%s, %s, %s)"""
        
        cursor.execute(query, (command, 'pending', datetime.now()))
        db.commit()
        
        job_id = cursor.lastrowid
        print(f"Bill generation job added to queue with ID: {job_id}")
        print(f"Parameters: User ID = {user_id}, Repetitions = {num_reps}")
        
        cursor.close()
        db.close()
        
        return job_id
        
    except Exception as e:
        print(f"Error adding job to queue: {str(e)}")
        return None

if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    num_reps = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    
    print(f"Adding bill generation job for user {user_id} with {num_reps} repetitions...")
    add_bill_job(user_id, num_reps)
