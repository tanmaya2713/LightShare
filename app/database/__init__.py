"""
Database module for ZeroConfig Local Network File Transfer.
SQLite3 schema, automatic migration, SHA-256 hash tracking, clipboard beaming, and parallel chunk checkpoints.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any

SCHEMA_VERSION = 5

def get_schema() -> str:
    """Return base database schema SQL."""
    return """
    CREATE TABLE IF NOT EXISTS transfers (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        size INTEGER NOT NULL DEFAULT 0,
        uploaded_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'uploading',
        bytes_received INTEGER DEFAULT 0,
        content_type TEXT,
        filepath TEXT,
        file_category TEXT DEFAULT 'other',
        sha256_hash TEXT DEFAULT '',
        pin_code TEXT DEFAULT '',
        sender_name TEXT DEFAULT 'Anonymous',
        target_peer TEXT DEFAULT '',
        is_pin_required INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS peer_nodes (
        id TEXT PRIMARY KEY,
        device_name TEXT NOT NULL,
        device_type TEXT NOT NULL DEFAULT 'Mobile',
        ip TEXT NOT NULL,
        avatar TEXT DEFAULT 'astronaut',
        signal_dbm INTEGER DEFAULT -45,
        distance TEXT DEFAULT '1.5m',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS clipboard_beams (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        sender_name TEXT NOT NULL DEFAULT 'Anonymous',
        beam_type TEXT NOT NULL DEFAULT 'text',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS upload_checkpoints (
        upload_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_size INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (upload_id, chunk_index)
    );

    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create a configured SQLite connection."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # WAL mode for high concurrency
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def detect_category(filename: str, content_type: Optional[str] = None) -> str:
    """Categorize file for categorized media and document browsing including Apple & iOS formats."""
    ext = os.path.splitext(filename.lower())[1]
    ct = (content_type or "").lower()
    
    # Photos including Apple HEIC/HEIF and ProRAW DNG
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.heic', '.heif', '.dng', '.avif', '.raw', '.cr2', '.nef') or ct.startswith('image/'):
        return 'photo'
    # Videos including Apple QuickTime MOV, ProRes, MP4, M4V
    elif ext in ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.3gp', '.m4v', '.ts') or ct.startswith('video/'):
        return 'video'
    # Music including Apple Lossless ALAC, AIFF, CAF, AAC, M4A, FLAC, MP3
    elif ext in ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.aiff', '.caf', '.alac') or ct.startswith('audio/'):
        return 'music'
    # Apps including iOS IPA, macOS DMG/APP, Android APK/AAB, Windows EXE/MSI, Linux DEB/RPM
    elif ext in ('.apk', '.xapk', '.aab', '.ipa', '.dmg', '.app', '.exe', '.msi', '.deb', '.rpm', '.pkg'):
        return 'app'
    # Documents including Apple Pages/Numbers/Keynote, PDF, Office, Text
    elif ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv', '.rtf', '.odt', '.ods', '.odp', '.pages', '.key', '.numbers'):
        return 'document'
    # 30GB+ Archives
    elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso', '.bin', '.tgz', '.xz', '.dmg'):
        return 'archive'
    return 'other'

def initialize(db_path: str) -> None:
    """Initialize database with full schema, automatic migrations, clipboard beaming, and parallel chunk checkpoints."""
    if os.path.dirname(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Ensure tables exist
    cursor.executescript(get_schema())
    
    # 2. Check and perform safe migrations for existing tables
    cursor.execute("PRAGMA table_info(transfers)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    
    if "file_category" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN file_category TEXT DEFAULT 'other'")
    if "bytes_received" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN bytes_received INTEGER DEFAULT 0")
    if "content_type" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN content_type TEXT")
    if "filepath" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN filepath TEXT")
    if "sha256_hash" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN sha256_hash TEXT DEFAULT ''")
    if "pin_code" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN pin_code TEXT DEFAULT ''")
    if "sender_name" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN sender_name TEXT DEFAULT 'Anonymous'")
    if "target_peer" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN target_peer TEXT DEFAULT ''")
    if "is_pin_required" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN is_pin_required INTEGER DEFAULT 1")
    if "created_at" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN created_at TEXT DEFAULT ''")
    if "updated_at" not in existing_cols:
        cursor.execute("ALTER TABLE transfers ADD COLUMN updated_at TEXT DEFAULT ''")
        
    # 3. Create indices safely after columns exist
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_uploaded_at ON transfers(uploaded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_category ON transfers(file_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_filename ON transfers(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clipboard_created ON clipboard_beams(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_upload_id ON upload_checkpoints(upload_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_pin ON transfers(pin_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_peers_last_seen ON peer_nodes(last_seen)")
    
    # 4. Backfill categories for existing files in database
    cursor.execute("SELECT id, filename, content_type FROM transfers")
    rows = cursor.fetchall()
    for row in rows:
        correct_cat = detect_category(row["filename"], row["content_type"])
        cursor.execute("UPDATE transfers SET file_category = ? WHERE id = ?", (correct_cat, row["id"]))

    cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()
    conn.close()