#!/usr/bin/env python3
"""
Simple script to add a bill generation job to the queue
"""
import mysql.connector
import json
from datetime import datetime

try:
    # Connect to database
    db = mysql.connector.connect(
        host="localhost",
        user="",
        password="",
        database=""
    )
    cursor = db.cursor()
    
    # Add a test job
    params = {"user_id": 1, "num_reps": 10}  # Small number for testing
    command = f"generate_bill_dates:{json.dumps(params)}"
    
    # Insert job into queue
    query = "INSERT INTO date_job (command, status, created_at) VALUES (%s, %s, %s)"
    cursor.execute(query, (command, 'pending', datetime.now()))
    db.commit()
    
    job_id = cursor.lastrowid
    print(f"✓ Job added successfully with ID: {job_id}")
    print(f"Command: {command}")
    print("\nNow run your worker.py to process this job")
    
    cursor.close()
    db.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
