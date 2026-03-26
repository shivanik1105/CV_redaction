from app import QUEUE_AVAILABLE, get_queue_manager

print(f"QUEUE_AVAILABLE: {QUEUE_AVAILABLE}")

qm = get_queue_manager()
print(f"Queue Manager: {qm}")

if qm:
    stats = qm.get_queue_stats()
    print(f"Stats: {stats}")
else:
    print("Queue manager is None")
