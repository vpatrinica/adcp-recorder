#!/usr/bin/env python3
"""FTP Sync — rsync-like mirror of a local directory to a remote FTP server.

Recursively walks a local directory and uploads files that are missing or
differ in size on the remote FTP server.  Designed to run standalone or as
a periodic systemd service for the ADCP Recorder project.

Usage examples:
    # Sync default data directory (C:\\s1000\\data on Windows)
    python ftp_sync.py -H ftp.example.com -u myuser -p mypass

    # Sync a specific directory, exclude DuckDB files
    python ftp_sync.py -H ftp.example.com -u myuser -p mypass \
        -l /var/lib/adcp/data -r /adcp-upload \
        -e "*.duckdb" -e "*.wal"

    # Dry-run to see what would be uploaded
    python ftp_sync.py -H ftp.example.com -u myuser -p mypass --dry-run

Environment variables (used as fallbacks for CLI arguments):
    FTP_HOST     FTP server hostname
    FTP_USER     FTP username
    FTP_PASS     FTP password
"""

from __future__ import annotations

import argparse
import fnmatch
import ftplib
import logging
import os
import sys
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

WIN_DEFAULT_LOCAL_DIR = r"C:\s1000\data"
LINUX_DEFAULT_LOCAL_DIR_NAME = "adcp_data"

# Only sync these subdirectories of the data root by default
DEFAULT_SYNC_DIRS: list[str] = [
    "nmea",
    "db",
    "parquet",
]

DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    "*.duckdb",
    "*.duckdb.wal",
    "*.wal",
    "*.log",
]

logger = logging.getLogger("ftp_sync")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_default_local_dir() -> str:
    """Return the platform-appropriate default local data directory."""
    if sys.platform == "win32":
        return WIN_DEFAULT_LOCAL_DIR
    return str(Path.home() / LINUX_DEFAULT_LOCAL_DIR_NAME)


def _should_exclude(rel_path: str, patterns: list[str]) -> bool:
    """Return True if *rel_path* matches any of the exclusion *patterns*."""
    name = os.path.basename(rel_path)
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _remote_mkdir_p(ftp: ftplib.FTP, remote_dir: str) -> None:
    """Recursively create directories on the FTP server (like mkdir -p)."""
    parts = PurePosixPath(remote_dir).parts
    current = ""
    for part in parts:
        current = str(PurePosixPath(current) / part)
        try:
            ftp.mkd(current)
            logger.debug("Created remote directory: %s", current)
        except ftplib.error_perm:
            # Directory likely already exists
            pass


def _remote_file_size(ftp: ftplib.FTP, remote_path: str) -> int | None:
    """Return the size of a remote file, or None if it doesn't exist."""
    try:
        return ftp.size(remote_path)
    except ftplib.error_perm:
        return None


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


class FtpSyncer:
    """Mirrors a local directory tree to a remote FTP server."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        local_dir: str,
        remote_dir: str = "/",
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
        self.port = port
        self.sync_dirs = sync_dirs or list(DEFAULT_SYNC_DIRS)
        self.exclude_patterns = exclude_patterns or list(DEFAULT_EXCLUDE_PATTERNS)
        self.dry_run = dry_run

        # Counters
        self.uploaded = 0
        self.skipped = 0
        self.excluded = 0
        self.errors = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync(self) -> None:
        """Connect and mirror the local directory to the remote server."""
        if not self.local_dir.is_dir():
            logger.error("Local directory does not exist: %s", self.local_dir)
            sys.exit(1)

        logger.info(
            "Connecting to %s:%d as '%s' …",
            self.host,
            self.port,
            self.user,
        )

        if self.dry_run:
            logger.info("*** DRY-RUN MODE — no files will be transferred ***")

        ftp = ftplib.FTP()
        ftp.connect(self.host, self.port, timeout=30)
        try:
            ftp.login(self.user, self.password)
            ftp.set_pasv(True)
            logger.info("Connected.  Server: %s", ftp.getwelcome())

            self._walk_and_upload(ftp)

            logger.info(
                "Sync complete — uploaded: %d | skipped: %d | excluded: %d | errors: %d",
                self.uploaded,
                self.skipped,
                self.excluded,
                self.errors,
            )
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _walk_and_upload(self, ftp: ftplib.FTP) -> None:
        """Walk only the configured subdirectories and upload changed files."""
        for subdir in self.sync_dirs:
            local_subdir = self.local_dir / subdir
            if not local_subdir.is_dir():
                logger.warning("Sync directory does not exist, skipping: %s", local_subdir)
                continue

            logger.info("Syncing subdirectory: %s", subdir)
            for dirpath, _dirnames, filenames in os.walk(local_subdir):
                for fname in filenames:
                    local_file = Path(dirpath) / fname
                    rel = local_file.relative_to(self.local_dir).as_posix()

                    # Exclusion check
                    if _should_exclude(rel, self.exclude_patterns):
                        logger.debug("Excluded: %s", rel)
                        self.excluded += 1
                        continue

                    remote_path = str(PurePosixPath(self.remote_dir) / rel)
                    self._sync_file(ftp, local_file, remote_path)

    def _sync_file(
        self, ftp: ftplib.FTP, local_file: Path, remote_path: str
    ) -> None:
        """Upload *local_file* to *remote_path* if it has changed."""
        local_size = local_file.stat().st_size
        remote_size = _remote_file_size(ftp, remote_path)

        if remote_size is not None and remote_size == local_size:
            logger.debug("Up-to-date: %s (%d bytes)", remote_path, local_size)
            self.skipped += 1
            return

        action = "upload" if remote_size is None else "update"
        logger.info(
            "%s %s → %s (%d bytes)",
            "[DRY-RUN]" if self.dry_run else action.upper(),
            local_file.relative_to(self.local_dir),
            remote_path,
            local_size,
        )

        if self.dry_run:
            self.uploaded += 1
            return

        # Ensure the remote parent directory exists
        remote_parent = str(PurePosixPath(remote_path).parent)
        if remote_parent and remote_parent != ".":
            _remote_mkdir_p(ftp, remote_parent)

        try:
            with open(local_file, "rb") as fh:
                ftp.storbinary(f"STOR {remote_path}", fh)
            self.uploaded += 1
        except ftplib.error_perm as exc:
            logger.error("Failed to upload %s: %s", remote_path, exc)
            self.errors += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Mirror a local directory to a remote FTP server (rsync-like).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-H",
        "--host",
        default=os.environ.get("FTP_HOST", ""),
        help="FTP server hostname (env: FTP_HOST)",
    )
    parser.add_argument(
        "-u",
        "--user",
        default=os.environ.get("FTP_USER", ""),
        help="FTP username (env: FTP_USER)",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=os.environ.get("FTP_PASS", ""),
        help="FTP password (env: FTP_PASS)",
    )
    parser.add_argument(
        "-l",
        "--local-dir",
        default=_get_default_local_dir(),
        help="Local directory to sync (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--remote-dir",
        default="/",
        help="Remote base directory on the FTP server (default: /)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=21,
        help="FTP port (default: 21)",
    )
    parser.add_argument(
        "-s",
        "--sync-dir",
        action="append",
        default=None,
        metavar="DIR",
        dest="sync_dirs",
        help="Subdirectory to sync (repeatable). "
        "Defaults: nmea, db, parquet",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        default=None,
        metavar="PATTERN",
        help="Glob pattern to exclude (repeatable). "
        "Defaults: *.duckdb, *.duckdb.wal, *.wal, *.log",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually transferring",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Logging setup
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validate required arguments
    if not args.host:
        parser.error("FTP host is required (--host or FTP_HOST env var)")
    if not args.user:
        parser.error("FTP user is required (--user or FTP_USER env var)")
    if not args.password:
        parser.error("FTP password is required (--password or FTP_PASS env var)")

    syncer = FtpSyncer(
        host=args.host,
        user=args.user,
        password=args.password,
        local_dir=args.local_dir,
        remote_dir=args.remote_dir,
        port=args.port,
        sync_dirs=args.sync_dirs,
        exclude_patterns=args.exclude,
        dry_run=args.dry_run,
    )
    syncer.sync()


if __name__ == "__main__":
    main()
