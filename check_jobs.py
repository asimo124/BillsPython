#!/usr/bin/env python3
"""
Script to check job status and output
"""
import mysql.connector

try:
    # Connect to database
    db = mysql.connector.connect(
        host="localhost",
        user="",
        password="",
        database=""
    )
    cursor = db.cursor(dictionary=True)
    
    # Get recent jobs
    query = "SELECT * FROM date_job ORDER BY created_at DESC LIMIT 5"
    cursor.execute(query)
    jobs = cursor.fetchall()
    
    print("Recent Jobs:")
    print("-" * 80)
    for job in jobs:
        print(f"ID: {job['id']}")
        print(f"Command: {job['command']}")
        print(f"Status: {job['status']}")
        print(f"Created: {job['created_at']}")
        if job['output']:
            print(f"Output: {job['output']}")
        print("-" * 40)
    
    cursor.close()
    db.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
