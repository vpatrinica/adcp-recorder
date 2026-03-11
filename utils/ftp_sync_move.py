#!/usr/bin/env python3
"""FTP Sync & Backup — Mirror to FTP and move old files to backup."""

from __future__ import annotations

import argparse
import fnmatch
import ftplib
import logging
import os
import shutil
import sys
import time
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

WIN_DEFAULT_LOCAL_DIR = r"C:\s1000\data"
LINUX_DEFAULT_LOCAL_DIR_NAME = "adcp_data"

DEFAULT_SYNC_DIRS: list[str] = ["nmea", "db", "parquet"]
DEFAULT_EXCLUDE_PATTERNS: list[str] = ["*.duckdb", "*.duckdb.wal", "*.wal", "*.log"]

logger = logging.getLogger("ftp_sync")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_default_local_dir() -> str:
    if sys.platform == "win32":
        return WIN_DEFAULT_LOCAL_DIR
    return str(Path.home() / LINUX_DEFAULT_LOCAL_DIR_NAME)

def _should_exclude(rel_path: str, patterns: list[str]) -> bool:
    name = os.path.basename(rel_path)
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)

def _remote_mkdir_p(ftp: ftplib.FTP, remote_dir: str) -> None:
    parts = PurePosixPath(remote_dir).parts
    current = ""
    for part in parts:
        current = str(PurePosixPath(current) / part)
        try:
            ftp.mkd(current)
        except ftplib.error_perm:
            pass

def _remote_file_size(ftp: ftplib.FTP, remote_path: str) -> int | None:
    try:
        return ftp.size(remote_path)
    except ftplib.error_perm:
        return None

# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

class FtpSyncer:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        local_dir: str,
        remote_dir: str = "/",
        backup_dir: str | None = None,
        port: int = 21,
        sync_dirs: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.local_dir = Path(local_dir).resolve()
        self.remote_dir = remote_dir.rstrip("/") or "/"
        self.backup_dir = Path(backup_dir).resolve() if backup_dir else None
        self.port = port
        self.sync_dirs = sync_dirs or list(DEFAULT_SYNC_DIRS)
        self.exclude_patterns = exclude_patterns or list(DEFAULT_EXCLUDE_PATTERNS)
        self.dry_run = dry_run

        self.uploaded = 0
        self.skipped = 0
        self.excluded = 0
        self.errors = 0
        self.moved = 0

    def sync(self) -> None:
        if not self.local_dir.is_dir():
            logger.error("Local directory does not exist: %s", self.local_dir)
            sys.exit(1)

        logger.info("Connecting to %s:%d as '%s'...", self.host, self.port, self.user)
        if self.dry_run:
            logger.info("*** DRY-RUN MODE — no files will be transferred or moved ***")

        ftp = ftplib.FTP()
        ftp.connect(self.host, self.port, timeout=30)
        try:
            ftp.login(self.user, self.password)
            ftp.set_pasv(True)
            logger.info("Connected. Server: %s", ftp.getwelcome().strip())

            self._walk_and_upload(ftp)

            logger.info(
                "Sync complete — uploaded: %d | skipped: %d | moved to backup: %d | errors: %d",
                self.uploaded, self.skipped, self.moved, self.errors,
            )
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def _walk_and_upload(self, ftp: ftplib.FTP) -> None:
        for subdir in self.sync_dirs:
            local_subdir = self.local_dir / subdir
            if not local_subdir.is_dir():
                logger.warning("Sync directory does not exist, skipping: %s", local_subdir)
                continue

            logger.info("Syncing subdirectory: %s", subdir)
            for dirpath, _, filenames in os.walk(local_subdir):
                for fname in filenames:
                    local_file = Path(dirpath) / fname
                    rel = local_file.relative_to(self.local_dir).as_posix()

                    if _should_exclude(rel, self.exclude_patterns):
                        self.excluded += 1
                        continue

                    remote_path = str(PurePosixPath(self.remote_dir) / rel)
                    self._sync_file(ftp, local_file, remote_path)

    def _sync_file(self, ftp: ftplib.FTP, local_file: Path, remote_path: str) -> None:
        """Upload local_file to remote_path if changed, then move to backup if old."""
        local_stat = local_file.stat()
        local_size = local_stat.st_size
        remote_size = _remote_file_size(ftp, remote_path)
        
        success = False

        # 1. Handle Upload Logic
        if remote_size is not None and remote_size == local_size:
            logger.debug("Up-to-date: %s", remote_path)
            self.skipped += 1
            success = True 
        else:
            action = "upload" if remote_size is None else "update"
            logger.info("%s %s → %s", "[DRY-RUN]" if self.dry_run else action.upper(), local_file.name, remote_path)
            
            if self.dry_run:
                success = True
                self.uploaded += 1
            else:
                remote_parent = str(PurePosixPath(remote_path).parent)
                if remote_parent and remote_parent != ".":
                    _remote_mkdir_p(ftp, remote_parent)
                try:
                    with open(local_file, "rb") as fh:
                        ftp.storbinary(f"STOR {remote_path}", fh)
                    self.uploaded += 1
                    success = True
                except ftplib.error_perm as exc:
                    logger.error("Failed to upload %s: %s", remote_path, exc)
                    self.errors += 1

        # 2. Handle Backup Logic (Post-Upload)
        if success and self.backup_dir:
            file_age_seconds = time.time() - local_stat.st_mtime
            if file_age_seconds > (24 * 3600):
                self._move_to_backup(local_file)

    def _move_to_backup(self, local_file: Path) -> None:
        """Move file to backup directory while maintaining subfolder structure."""
        rel_path = local_file.relative_to(self.local_dir)
        dest_path = self.backup_dir / rel_path

        if self.dry_run:
            logger.info("[DRY-RUN] Would move %s to %s", local_file.name, dest_path)
            self.moved += 1
            return

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            # Use shutil.move to handle cross-device moves if necessary
            shutil.move(str(local_file), str(dest_path))
            logger.info("Moved to backup: %s", rel_path)
            self.moved += 1
        except Exception as e:
            logger.error("Failed to move %s to backup: %s", local_file, e)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FTP Sync with 24h Backup Move.")
    parser.add_argument("-H", "--host", default=os.environ.get("FTP_HOST", ""), help="FTP Host")
    parser.add_argument("-u", "--user", default=os.environ.get("FTP_USER", ""), help="FTP User")
    parser.add_argument("-p", "--password", default=os.environ.get("FTP_PASS", ""), help="FTP Password")
    parser.add_argument("-l", "--local-dir", default=_get_default_local_dir(), help="Local Data Dir")
    parser.add_argument("-r", "--remote-dir", default="/", help="Remote FTP Dir")
    parser.add_argument("-b", "--backup-dir", help="Local directory for files older than 24h")
    parser.add_argument("--port", type=int, default=21)
    parser.add_argument("-s", "--sync-dir", action="append", dest="sync_dirs")
    parser.add_argument("-e", "--exclude", action="append")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser

def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    if not all([args.host, args.user, args.password]):
        parser.error("Host, User, and Password are required.")

    syncer = FtpSyncer(
        host=args.host, user=args.user, password=args.password,
        local_dir=args.local_dir, remote_dir=args.remote_dir,
        backup_dir=args.backup_dir, port=args.port,
        sync_dirs=args.sync_dirs, exclude_patterns=args.exclude,
        dry_run=args.dry_run,
    )
    syncer.sync()

if __name__ == "__main__":
    main()