from backend.database.db import (
    init_db,
    save_processed_email,
    insert_audit_log,
    add_to_approval_queue,
    get_approval_queue,
    update_approval_status,
    get_audit_logs,
    get_processed_emails,
    get_system_stats,
    get_db_connection
)
