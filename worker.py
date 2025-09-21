import time
print("Worker started at", time.strftime("%Y-%m-%d %H:%M:%S"))

import time
import subprocess
import mysql.connector
import json
from bills import Bills

import os
import time

def notify_systemd():
    try:
        with open("/run/systemd/notify", "w") as f:
            f.write("WATCHDOG=1\n")
    except Exception:
        pass

db = mysql.connector.connect(
    host="localhost",
    user="",
    password="",
    database=""
)
cursor = db.cursor(dictionary=True)

def fetch_job():
    cursor.execute("SELECT * FROM date_job WHERE status='pending' ORDER BY created_at ASC LIMIT 1")
    return cursor.fetchone()

def update_status(job_id, status, output=None):
    cursor.execute("UPDATE date_job SET status=%s, output=%s WHERE id=%s", (status, output, job_id))
    db.commit()

def process_bill_generation(job_params):
    """Process bill generation job with Python code instead of shell command"""
    try:
        # Parse job parameters
        params = json.loads(job_params) if job_params else {}
        num_reps = params.get('num_reps', 42)
        user_id = params.get('user_id', 1)
        
        # Create Bills instance
        bill = Bills(num_reps, db)
        
        # Execute the bill generation process
        bill.delete_old_dates()
        bill.set_pay_period()
        bill.generate_bill_dates_by_user_id(user_id)
        
        return f"Bill generation completed successfully for user {user_id} with {num_reps} repetitions"
        
    except Exception as e:
        raise Exception(f"Bill generation failed: {str(e)}")

def execute_job(job):
    """Execute a job - either as shell command or Python function"""
    command = job['command']
    
    # Check if this is a bill generation command
    if command.startswith('generate_bill_dates'):
        # Extract parameters if any (format: generate_bill_dates:{"user_id": 1, "num_reps": 42})
        if ':' in command:
            _, params_str = command.split(':', 1)
            return process_bill_generation(params_str)
        else:
            return process_bill_generation('{}')
    else:
        # Execute as shell command (original behavior)
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        output = result.stdout + "\n" + result.stderr
        if result.returncode != 0:
            raise Exception(output)
        return output

while True:

    notify_systemd()

    job = fetch_job()
    if job:
        update_status(job['id'], 'running')
        try:
            output = execute_job(job)
            status = 'done'
        except Exception as e:
            output = str(e)
            status = 'error'
        update_status(job['id'], status, output)
    time.sleep(2)