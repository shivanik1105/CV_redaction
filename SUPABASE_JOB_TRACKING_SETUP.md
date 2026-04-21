# Supabase Upload Job Tracking Setup

## Problem Solved
When Render runs multiple app instances for load balancing, upload jobs created in one instance are not visible in another instance (since they were stored in memory). This causes 404 errors when polling job status.

## Solution
Store upload jobs in Supabase database instead of in-memory dictionary. All app instances share the same database, so jobs are visible across all instances.

---

## Setup Instructions

### Step 1: Create the Upload Jobs Table in Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click on "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy and paste the contents of `supabase_upload_jobs_table.sql`
6. Click "Run" to execute the SQL

This will create:
- `upload_jobs` table with all necessary columns
- Indexes for faster lookups
- Auto-update trigger for `updated_at` timestamp
- Cleanup function to remove old jobs (older than 1 hour)
- Row Level Security policies

### Step 2: Verify Table Creation

Run this query in SQL Editor to verify:

```sql
SELECT * FROM upload_jobs LIMIT 1;
```

You should see the table structure (even if empty).

### Step 3: Deploy to Render

The code automatically uses Supabase if available, with fallback to memory storage.

1. Push the code to GitHub (already done)
2. Render will auto-deploy the new version
3. Check Render logs for:
   - `Created upload job in Supabase: job_xxx` (success)
   - `Failed to create job in Supabase, using memory fallback` (if Supabase unavailable)

### Step 4: Test Upload

1. Go to your Render app URL
2. Upload a CV file
3. Check browser console (F12 → Console tab)
4. You should see successful polling without 404 errors

### Step 5: Monitor Jobs in Supabase

You can monitor upload jobs in real-time:

```sql
-- See all current jobs
SELECT job_id, status, original_filename, submitted_at, started_at, completed_at
FROM upload_jobs
ORDER BY submitted_at DESC
LIMIT 20;

-- See job statistics
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_processing_seconds
FROM upload_jobs
WHERE started_at IS NOT NULL
GROUP BY status;

-- Manually cleanup old jobs
SELECT cleanup_old_upload_jobs();
```

---

## How It Works

### Job Creation Flow

1. User uploads CV → `/upload` endpoint
2. App creates job in Supabase with status='queued'
3. Job ID returned to frontend
4. Worker picks up job from queue
5. Worker updates status to 'processing' in Supabase
6. Worker processes CV
7. Worker updates status to 'completed' or 'failed' in Supabase

### Job Polling Flow

1. Frontend polls `/api/upload-jobs/{job_id}` every 2 seconds
2. App checks Supabase first for job status
3. If not in Supabase, checks memory (fallback)
4. Returns current status to frontend
5. Frontend continues polling until status is 'completed' or 'failed'

### Multi-Instance Support

- Instance A creates job → stored in Supabase
- Instance B polls job → reads from Supabase ✓
- Instance C processes job → updates Supabase ✓
- All instances see the same job state

---

## Automatic Cleanup

Old completed/failed jobs are automatically cleaned up:

- Jobs older than 1 hour are deleted
- Cleanup runs via Supabase function: `cleanup_old_upload_jobs()`
- You can also run cleanup manually in SQL Editor

---

## Fallback Behavior

If Supabase is unavailable:
- Jobs are stored in memory (old behavior)
- Works fine for single-instance deployments
- May cause 404 errors in multi-instance deployments

---

## Troubleshooting

### Jobs still returning 404

1. Check Supabase connection:
   ```
   Visit: https://your-app.onrender.com/api/connection-status
   ```

2. Check if table exists:
   ```sql
   SELECT * FROM upload_jobs LIMIT 1;
   ```

3. Check Render logs for errors:
   ```
   Failed to create job in Supabase: [error message]
   ```

### Jobs stuck in 'queued' status

1. Check if workers are running (Render logs):
   ```
   Upload worker started: upload-worker-1
   Upload worker started: upload-worker-2
   ...
   ```

2. Check for processing errors in Render logs

3. Check job queue size:
   ```
   Visit: https://your-app.onrender.com/api/connection-status
   ```

### Supabase connection issues

1. Verify environment variables in Render:
   - `SUPABASE_URL` is set correctly
   - `SUPABASE_KEY` is set correctly (use service_role key, not anon key)

2. Check if Supabase project is paused (free tier pauses after inactivity)

3. Test connection manually:
   ```python
   from supabase import create_client
   client = create_client(SUPABASE_URL, SUPABASE_KEY)
   response = client.table('upload_jobs').select('*').limit(1).execute()
   print(response.data)
   ```

---

## Benefits

✓ Fixes 404 errors in multi-instance deployments
✓ Jobs persist across app restarts
✓ Real-time monitoring via Supabase dashboard
✓ Automatic cleanup of old jobs
✓ Graceful fallback to memory storage
✓ No code changes needed for single-instance deployments

---

## Next Steps

After deployment:
1. Test upload functionality
2. Monitor Render logs for any errors
3. Check Supabase dashboard to see jobs being created
4. Verify no more 404 errors in browser console

If you see any issues, check the Troubleshooting section above.
