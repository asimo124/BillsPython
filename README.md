# Bills Python Worker Service

This project converts the PHP Bills processing system to a Python worker service for better performance on heavy database operations.

## Files

- `worker.py` - Main worker service that processes jobs from a queue
- `bills.py` - Python class that handles all bill generation logic (converted from PHP)
- `add_bill_job.py` - Python script to add bill generation jobs to the queue
- `queue_bill_job.php` - PHP script to queue jobs (can be called from your existing web app)
- `requirements.txt` - Python dependencies

## Database Setup

You'll need a `jobs` table to queue the work:

```sql
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    command TEXT NOT NULL,
    status ENUM('pending', 'running', 'done', 'error') DEFAULT 'pending',
    output TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Update database connection settings in:
   - `worker.py`
   - `add_bill_job.py`
   - Make sure your PHP `includes.php` has the database connection for the PHP scripts

## Usage

### Running the Worker Service

Start the worker service (runs continuously):

```bash
python worker.py
```

### Queuing Bill Generation Jobs

**From Python:**

```bash
python add_bill_job.py [user_id] [num_reps]
# Example: python add_bill_job.py 1 42
```

**From PHP (CLI):**

```bash
php queue_bill_job.php [user_id] [num_reps]
# Example: php queue_bill_job.php 1 42
```

**From Web Application:**

```php
// Include the script in your existing PHP application
require_once('queue_bill_job.php');

// Queue a job
$result = addBillGenerationJob($user_id, $num_reps);

if ($result['success']) {
    echo "Job queued with ID: " . $result['job_id'];
} else {
    echo "Error: " . $result['error'];
}
```

**Via HTTP (for AJAX calls):**

```
GET/POST: queue_bill_job.php?user_id=1&num_reps=42
```

## How It Works

1. Instead of running the heavy bill generation directly in Apache/PHP, you queue a job
2. The Python worker service picks up the job and processes it using the converted Python logic
3. The worker updates the job status and stores any output
4. Your web application can check job status by querying the jobs table

## Conversion Notes

The Python `Bills` class replicates all functionality from the original PHP version:

- `deleteOldDates()` - Cleans up old dates and expired bills
- `setPayPeriod()` - Calculates pay periods based on current date
- `generateBillDatesByUserID()` - Main function that generates all bill dates
- All frequency types: Once, Monthly, Weekly, Bi-weekly, etc.
- Email notifications for future charges

## Benefits

- **Performance**: Heavy database operations run outside of web server
- **Scalability**: Multiple workers can process jobs in parallel
- **Reliability**: Jobs are queued and can be retried if they fail
- **Monitoring**: Job status and output are tracked in the database
