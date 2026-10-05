/// Pushes locally-queued data (progress updates, AI question logs, analytics
/// events) to the backend when connectivity is available, and pulls new
/// content releases. Reads from the `sync_queue` table (see local_database.dart)
/// and drains it against POST /sync/* once the backend implements those
/// endpoints for real (currently stubs — see backend/app/routers/sync.py).
///
/// Phase 2 scope: interface only.
library sync_engine;
