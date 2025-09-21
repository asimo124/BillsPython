# Testing the Bills Python Worker

Since you can't run commands locally, here's how to test the system:

## Step 1: Queue a Test Job

Run this script to add a job to the queue:

```bash
python queue_test_job.py
```

This will output something like:

```
✓ Job added successfully with ID: 123
Command: generate_bill_dates:{"user_id": 1, "num_reps": 10}

Now run your worker.py to process this job
```

## Step 2: Start the Worker

In another terminal, start the worker:

```bash
python worker.py
```

The worker should:

1. Pick up the job from the queue
2. Process it using the Python Bills class
3. Update the job status to 'done' or 'error'

## Step 3: Check Job Status

Run this to see job results:

```bash
python check_jobs.py
```

This will show recent jobs with their status and any output/errors.

## What to Look For

**Success**: Job status should be 'done' and output should show something like:

```
Bill generation completed successfully for user 1 with 10 repetitions
```

**Error**: Job status will be 'error' and output will show the specific error message.

## Common Issues and Fixes

1. **Date parsing errors**: The improved code now handles MySQL date objects better
2. **Missing database fields**: Check that your vnd_bills table has all required columns
3. **Database connection**: Verify connection settings in worker.py match your MySQL setup

## Database Schema Check

Make sure your tables exist:

```sql
-- Check if tables exist
SHOW TABLES LIKE 'vnd_%';
SHOW TABLES LIKE 'date_job';

-- Check vnd_bills structure
DESCRIBE vnd_bills;

-- Check if you have test data
SELECT * FROM vnd_bills LIMIT 5;
```

## Debugging

If you get errors, the improved code will show:

- Which bill is being processed
- Specific date conversion issues
- More detailed error messages

The debug output in the worker will help identify exactly where the issue occurs.
