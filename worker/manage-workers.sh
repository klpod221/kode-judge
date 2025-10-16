#!/bin/sh
# Worker management utility script

COMMAND=${1:-help}

case "$COMMAND" in
    list)
        echo "Listing all workers..."
        python3 -m app.worker_manager list
        ;;
    
    cleanup)
        echo "Cleaning up all workers..."
        python3 -m app.worker_manager cleanup
        ;;
    
    cleanup-stale)
        echo "Cleaning up stale workers only..."
        python3 -m app.worker_manager cleanup-stale
        ;;
    
    info)
        if [ -z "$2" ]; then
            echo "Usage: $0 info <worker_name>"
            exit 1
        fi
        python3 -m app.worker_manager info "$2"
        ;;
    
    restart)
        echo "Restarting workers..."
        echo "1. Cleaning up all workers..."
        python3 -m app.worker_manager cleanup
        
        echo "2. Stopping any running worker processes..."
        pkill -f "rq worker" || true
        
        echo "3. Starting workers..."
        exec /app/start-workers.sh
        ;;
    
    help|*)
        echo "Worker Management Utility"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  list              List all workers and their status"
        echo "  cleanup           Clean up all worker registrations"
        echo "  cleanup-stale     Clean up only stale workers"
        echo "  info <name>       Show detailed info about a worker"
        echo "  restart           Clean up and restart all workers"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 cleanup-stale"
        echo "  $0 info worker-1"
        echo "  $0 restart"
        ;;
esac
