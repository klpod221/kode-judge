#!/bin/sh
# Worker startup script with concurrency support

WORKER_CONCURRENCY=${WORKER_CONCURRENCY:-4}
REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}"
QUEUE_NAME="${REDIS_PREFIX}_submission_queue"

echo "Starting $WORKER_CONCURRENCY RQ workers..."

# Start workers in background
for i in $(seq 1 $((WORKER_CONCURRENCY - 1))); do
    echo "Starting worker $i..."
    rq worker --url "$REDIS_URL" "$QUEUE_NAME" --name "worker-$i" &
done

# Start the last worker in foreground to keep container running
echo "Starting worker $WORKER_CONCURRENCY (main process)..."
exec rq worker --url "$REDIS_URL" "$QUEUE_NAME" --name "worker-$WORKER_CONCURRENCY"
