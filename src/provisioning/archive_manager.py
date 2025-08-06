#!/usr/bin/env python3
"""
Archive Manager for GTach Application Provisioning System

Provides comprehensive archive management functionality including creation, 
validation, extraction, and integrity verification. Implements thread-safe 
operations with Protocol 8 compliant logging.

Features:
- Thread-safe archive operations
- Multiple compression formats (tar.gz, tar.bz2, zip)
- Integrity verification with checksums
- Archive metadata management
- Cross-platform compatibility
- Progress reporting for large archives
"""

import os
import tarfile
import zipfile
import gzip
import bz2
import hashlib
import json
import logging
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from enum import Enum, auto

# Import existing utilities
try:
    from ..obdii.utils.platform import get_platform_type, PlatformType
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from obdii.utils.platform import get_platform_type, PlatformType


class CompressionFormat(Enum):
    """Supported compression formats"""
    TAR_GZ = auto()
    TAR_BZ2 = auto()
    ZIP = auto()
    
    @classmethod
    def from_extension(cls, filename: str) -> 'CompressionFormat':
        """Determine format from file extension"""
        filename = filename.lower()
        if filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            return cls.TAR_GZ
        elif filename.endswith('.tar.bz2') or filename.endswith('.tbz2'):
            return cls.TAR_BZ2
        elif filename.endswith('.zip'):
            return cls.ZIP
        else:
            # Default to tar.gz
            return cls.TAR_GZ


@dataclass
class ArchiveMetadata:
    """Archive metadata and integrity information"""
    filename: str
    format: CompressionFormat
    created_at: str
    file_count: int
    uncompressed_size: int
    compressed_size: int
    checksum_sha256: Optional[str] = None
    checksum_md5: Optional[str] = None
    files: List[str] = field(default_factory=list)
    creator: str = "gtach-archive-manager"
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filename': self.filename,
            'format': self.format.name,
            'created_at': self.created_at,
            'file_count': self.file_count,
            'uncompressed_size': self.uncompressed_size,
            'compressed_size': self.compressed_size,
            'checksum_sha256': self.checksum_sha256,
            'checksum_md5': self.checksum_md5,
            'files': self.files,
            'creator': self.creator,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchiveMetadata':
        """Create instance from dictionary"""
        return cls(
            filename=data['filename'],
            format=CompressionFormat[data['format']],
            created_at=data['created_at'],
            file_count=data['file_count'],
            uncompressed_size=data['uncompressed_size'],
            compressed_size=data['compressed_size'],
            checksum_sha256=data.get('checksum_sha256'),
            checksum_md5=data.get('checksum_md5'),
            files=data.get('files', []),
            creator=data.get('creator', 'unknown'),
            version=data.get('version', '1.0.0')
        )


@dataclass
class ArchiveConfig:
    """Configuration for archive operations"""
    compression_level: int = 6  # 0-9 for gzip/bzip2
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    follow_symlinks: bool = False
    create_checksums: bool = True
    include_metadata: bool = True
    progress_callback: Optional[Callable[[int, int], None]] = None
    exclude_patterns: List[str] = field(default_factory=lambda: ['.DS_Store', 'Thumbs.db'])
    max_file_size: int = 100 * 1024 * 1024  # 100MB default limit


class ArchiveManager:
    """
    Thread-safe archive manager for deployment package operations.
    
    Provides comprehensive archive management with integrity verification,
    metadata tracking, and cross-platform compatibility. Implements
    Protocol 8 compliant logging and error handling.
    """
    
    def __init__(self):
        """Initialize ArchiveManager with thread-safe operations"""
        self.logger = logging.getLogger(f'{__name__}.ArchiveManager')
        
        # Thread safety
        self._operation_lock = threading.RLock()
        self._stats_lock = threading.Lock()
        
        # Statistics tracking
        self._operation_count = 0
        self._bytes_processed = 0
        self._archives_created = 0
        self._archives_extracted = 0
        
        # Platform detection
        self.platform = get_platform_type()
        
        self.logger.info("ArchiveManager initialized")
        self.logger.debug(f"Platform: {self.platform.name}")
    
    def create_archive(self,
                      source_dir: Union[str, Path],
                      archive_path: Union[str, Path],
                      config: Optional[ArchiveConfig] = None) -> ArchiveMetadata:
        """
        Create archive from source directory.
        
        Args:
            source_dir: Directory to archive
            archive_path: Output archive path
            config: Optional archive configuration
            
        Returns:
            Archive metadata
            
        Raises:
            RuntimeError: If archive creation fails
        """
        with self._operation_lock:
            self._increment_operation_count()
            
            config = config or ArchiveConfig()
            source_dir = Path(source_dir)
            archive_path = Path(archive_path)
            
            self.logger.info(f"Creating archive: {source_dir} -> {archive_path}")
            
            if not source_dir.exists():
                raise RuntimeError(f"Source directory does not exist: {source_dir}")
                
            # Ensure output directory exists
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine compression format
            format_type = CompressionFormat.from_extension(archive_path.name)
            
            try:
                # Collect files to archive
                files_to_archive = self._collect_files(source_dir, config)
                total_files = len(files_to_archive)
                
                self.logger.debug(f"Archiving {total_files} files with {format_type.name} compression")
                
                # Create archive based on format
                if format_type == CompressionFormat.ZIP:
                    metadata = self._create_zip_archive(
                        source_dir, archive_path, files_to_archive, config
                    )
                else:
                    metadata = self._create_tar_archive(
                        source_dir, archive_path, files_to_archive, config, format_type
                    )
                
                # Calculate checksums
                if config.create_checksums:
                    self._calculate_checksums(archive_path, metadata)
                
                # Save metadata file
                if config.include_metadata:
                    self._save_metadata(archive_path, metadata)
                
                # Update statistics
                with self._stats_lock:
                    self._archives_created += 1
                    self._bytes_processed += metadata.compressed_size
                
                self.logger.info(f"Archive created: {archive_path.name} "
                               f"({metadata.file_count} files, {metadata.compressed_size:,} bytes)")
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Archive creation failed: {e}")
                # Clean up partial archive
                if archive_path.exists():
                    try:
                        archive_path.unlink()
                    except OSError:
                        pass
                raise RuntimeError(f"Archive creation failed: {e}") from e
    
    def extract_archive(self,
                       archive_path: Union[str, Path],
                       dest_dir: Union[str, Path],
                       config: Optional[ArchiveConfig] = None,
                       verify_integrity: bool = True) -> ArchiveMetadata:
        """
        Extract archive to destination directory.
        
        Args:
            archive_path: Archive file to extract
            dest_dir: Destination directory
            config: Optional archive configuration
            verify_integrity: Whether to verify archive integrity
            
        Returns:
            Archive metadata
            
        Raises:
            RuntimeError: If extraction fails
        """
        with self._operation_lock:
            self._increment_operation_count()
            
            config = config or ArchiveConfig()
            archive_path = Path(archive_path)
            dest_dir = Path(dest_dir)
            
            self.logger.info(f"Extracting archive: {archive_path} -> {dest_dir}")
            
            if not archive_path.exists():
                raise RuntimeError(f"Archive does not exist: {archive_path}")
            
            # Verify integrity if requested
            if verify_integrity:
                self.verify_archive_integrity(archive_path)
            
            # Load metadata if available
            metadata = self._load_metadata(archive_path)
            
            # Ensure destination directory exists
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine format and extract
            format_type = CompressionFormat.from_extension(archive_path.name)
            
            try:
                if format_type == CompressionFormat.ZIP:
                    extracted_files = self._extract_zip_archive(archive_path, dest_dir, config)
                else:
                    extracted_files = self._extract_tar_archive(
                        archive_path, dest_dir, config, format_type
                    )
                
                # Update metadata if not loaded
                if metadata is None:
                    metadata = ArchiveMetadata(
                        filename=archive_path.name,
                        format=format_type,
                        created_at=datetime.now().isoformat(),
                        file_count=len(extracted_files),
                        uncompressed_size=sum(
                            (dest_dir / f).stat().st_size 
                            for f in extracted_files 
                            if (dest_dir / f).exists()
                        ),
                        compressed_size=archive_path.stat().st_size,
                        files=extracted_files
                    )
                
                # Update statistics
                with self._stats_lock:
                    self._archives_extracted += 1
                    self._bytes_processed += metadata.compressed_size
                
                self.logger.info(f"Archive extracted: {len(extracted_files)} files")
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Archive extraction failed: {e}")
                raise RuntimeError(f"Archive extraction failed: {e}") from e
    
    def verify_archive_integrity(self, archive_path: Union[str, Path]) -> bool:
        """
        Verify archive integrity.
        
        Args:
            archive_path: Archive file to verify
            
        Returns:
            True if archive is valid
            
        Raises:
            RuntimeError: If verification fails
        """
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise RuntimeError(f"Archive does not exist: {archive_path}")
        
        self.logger.debug(f"Verifying archive integrity: {archive_path}")
        
        format_type = CompressionFormat.from_extension(archive_path.name)
        
        try:
            if format_type == CompressionFormat.ZIP:
                return self._verify_zip_integrity(archive_path)
            else:
                return self._verify_tar_integrity(archive_path, format_type)
                
        except Exception as e:
            self.logger.error(f"Archive integrity verification failed: {e}")
            raise RuntimeError(f"Archive integrity verification failed: {e}") from e
    
    def _collect_files(self, source_dir: Path, config: ArchiveConfig) -> List[Path]:
        """
        Collect files to archive based on configuration.
        
        Args:
            source_dir: Source directory
            config: Archive configuration
            
        Returns:
            List of files to archive
        """
        files_to_archive = []
        total_size = 0
        
        for file_path in source_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Check exclude patterns
            if self._should_exclude_file(file_path, config.exclude_patterns):
                continue
            
            # Check file size limit
            file_size = file_path.stat().st_size
            if file_size > config.max_file_size:
                self.logger.warning(f"Skipping large file: {file_path} ({file_size:,} bytes)")
                continue
            
            files_to_archive.append(file_path)
            total_size += file_size
        
        self.logger.debug(f"Collected {len(files_to_archive)} files ({total_size:,} bytes)")
        return files_to_archive
    
    def _should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """
        Check if file should be excluded based on patterns.
        
        Args:
            file_path: File to check
            exclude_patterns: List of exclusion patterns
            
        Returns:
            True if file should be excluded
        """
        for pattern in exclude_patterns:
            if pattern in file_path.name or pattern in str(file_path):
                return True
        return False
    
    def _create_tar_archive(self,
                           source_dir: Path,
                           archive_path: Path,
                           files_to_archive: List[Path],
                           config: ArchiveConfig,
                           format_type: CompressionFormat) -> ArchiveMetadata:
        """
        Create tar archive with specified compression.
        
        Args:
            source_dir: Source directory
            archive_path: Output archive path
            files_to_archive: Files to include
            config: Archive configuration
            format_type: Compression format
            
        Returns:
            Archive metadata
        """
        # Determine tar mode
        if format_type == CompressionFormat.TAR_BZ2:
            mode = f'w:bz2'
            compresslevel_arg = 'compresslevel'
        else:  # TAR_GZ
            mode = f'w:gz'
            compresslevel_arg = 'compresslevel'
        
        uncompressed_size = 0
        archived_files = []
        processed_files = 0
        
        # Create tar archive
        tar_kwargs = {compresslevel_arg: config.compression_level}
        
        with tarfile.open(archive_path, mode, **tar_kwargs) as tar:
            for file_path in files_to_archive:
                try:
                    # Calculate archive name (relative to source directory)
                    arcname = file_path.relative_to(source_dir)
                    
                    # Add file to archive
                    if config.follow_symlinks and file_path.is_symlink():
                        tar.add(file_path, arcname=arcname, recursive=False)
                    else:
                        tar.add(file_path, arcname=arcname, recursive=False)
                    
                    uncompressed_size += file_path.stat().st_size
                    archived_files.append(str(arcname))
                    processed_files += 1
                    
                    # Progress callback
                    if config.progress_callback:
                        config.progress_callback(processed_files, len(files_to_archive))
                        
                except Exception as e:
                    self.logger.warning(f"Failed to archive file {file_path}: {e}")
                    continue
        
        # Get final archive size
        compressed_size = archive_path.stat().st_size
        
        return ArchiveMetadata(
            filename=archive_path.name,
            format=format_type,
            created_at=datetime.now().isoformat(),
            file_count=len(archived_files),
            uncompressed_size=uncompressed_size,
            compressed_size=compressed_size,
            files=archived_files
        )
    
    def _create_zip_archive(self,
                           source_dir: Path,
                           archive_path: Path,
                           files_to_archive: List[Path],
                           config: ArchiveConfig) -> ArchiveMetadata:
        """
        Create ZIP archive.
        
        Args:
            source_dir: Source directory
            archive_path: Output archive path
            files_to_archive: Files to include
            config: Archive configuration
            
        Returns:
            Archive metadata
        """
        uncompressed_size = 0
        archived_files = []
        processed_files = 0
        
        # Map compression level (0-9) to zipfile compression level
        if config.compression_level == 0:
            compression = zipfile.ZIP_STORED
        else:
            compression = zipfile.ZIP_DEFLATED
            
        with zipfile.ZipFile(archive_path, 'w', compression=compression) as zf:
            for file_path in files_to_archive:
                try:
                    # Calculate archive name
                    arcname = file_path.relative_to(source_dir)
                    
                    # Add file to zip
                    zf.write(file_path, arcname=arcname)
                    
                    uncompressed_size += file_path.stat().st_size
                    archived_files.append(str(arcname))
                    processed_files += 1
                    
                    # Progress callback
                    if config.progress_callback:
                        config.progress_callback(processed_files, len(files_to_archive))
                        
                except Exception as e:
                    self.logger.warning(f"Failed to archive file {file_path}: {e}")
                    continue
        
        compressed_size = archive_path.stat().st_size
        
        return ArchiveMetadata(
            filename=archive_path.name,
            format=CompressionFormat.ZIP,
            created_at=datetime.now().isoformat(),
            file_count=len(archived_files),
            uncompressed_size=uncompressed_size,
            compressed_size=compressed_size,
            files=archived_files
        )
    
    def _extract_tar_archive(self,
                            archive_path: Path,
                            dest_dir: Path,
                            config: ArchiveConfig,
                            format_type: CompressionFormat) -> List[str]:
        """
        Extract tar archive.
        
        Args:
            archive_path: Archive file
            dest_dir: Destination directory
            config: Archive configuration
            format_type: Compression format
            
        Returns:
            List of extracted files
        """
        # Determine tar mode
        if format_type == CompressionFormat.TAR_BZ2:
            mode = 'r:bz2'
        else:  # TAR_GZ
            mode = 'r:gz'
        
        extracted_files = []
        
        with tarfile.open(archive_path, mode) as tar:
            members = tar.getmembers()
            
            for i, member in enumerate(members):
                try:
                    # Security check - prevent directory traversal
                    if not self._is_safe_path(member.name):
                        self.logger.warning(f"Skipping unsafe path: {member.name}")
                        continue
                    
                    tar.extract(member, path=dest_dir)
                    extracted_files.append(member.name)
                    
                    # Progress callback
                    if config.progress_callback:
                        config.progress_callback(i + 1, len(members))
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract {member.name}: {e}")
                    continue
        
        return extracted_files
    
    def _extract_zip_archive(self,
                            archive_path: Path,
                            dest_dir: Path,
                            config: ArchiveConfig) -> List[str]:
        """
        Extract ZIP archive.
        
        Args:
            archive_path: Archive file
            dest_dir: Destination directory
            config: Archive configuration
            
        Returns:
            List of extracted files
        """
        extracted_files = []
        
        with zipfile.ZipFile(archive_path, 'r') as zf:
            file_list = zf.infolist()
            
            for i, info in enumerate(file_list):
                try:
                    # Security check
                    if not self._is_safe_path(info.filename):
                        self.logger.warning(f"Skipping unsafe path: {info.filename}")
                        continue
                    
                    zf.extract(info, path=dest_dir)
                    extracted_files.append(info.filename)
                    
                    # Progress callback
                    if config.progress_callback:
                        config.progress_callback(i + 1, len(file_list))
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract {info.filename}: {e}")
                    continue
        
        return extracted_files
    
    def _is_safe_path(self, path: str) -> bool:
        """
        Check if extraction path is safe (prevents directory traversal).
        
        Args:
            path: Path to check
            
        Returns:
            True if path is safe
        """
        # Normalize path and check for directory traversal
        normalized = os.path.normpath(path)
        return not (normalized.startswith('/') or '..' in normalized)
    
    def _verify_tar_integrity(self, archive_path: Path, format_type: CompressionFormat) -> bool:
        """
        Verify tar archive integrity.
        
        Args:
            archive_path: Archive file
            format_type: Compression format
            
        Returns:
            True if archive is valid
        """
        if format_type == CompressionFormat.TAR_BZ2:
            mode = 'r:bz2'
        else:
            mode = 'r:gz'
        
        try:
            with tarfile.open(archive_path, mode) as tar:
                # Try to read all members
                members = tar.getmembers()
                for member in members:
                    if member.isreg():
                        # Try to read a small chunk from each file
                        try:
                            with tar.extractfile(member) as f:
                                f.read(1024)  # Read first 1KB
                        except Exception:
                            return False
            return True
            
        except Exception:
            return False
    
    def _verify_zip_integrity(self, archive_path: Path) -> bool:
        """
        Verify ZIP archive integrity.
        
        Args:
            archive_path: Archive file
            
        Returns:
            True if archive is valid
        """
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Test the archive
                bad_file = zf.testzip()
                return bad_file is None
                
        except Exception:
            return False
    
    def _calculate_checksums(self, archive_path: Path, metadata: ArchiveMetadata) -> None:
        """
        Calculate checksums for archive file.
        
        Args:
            archive_path: Archive file
            metadata: Metadata to update with checksums
        """
        sha256_hash = hashlib.sha256()
        md5_hash = hashlib.md5()
        
        with open(archive_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256_hash.update(chunk)
                md5_hash.update(chunk)
        
        metadata.checksum_sha256 = sha256_hash.hexdigest()
        metadata.checksum_md5 = md5_hash.hexdigest()
        
        self.logger.debug(f"Calculated checksums: SHA256={metadata.checksum_sha256[:16]}...")
    
    def _save_metadata(self, archive_path: Path, metadata: ArchiveMetadata) -> None:
        """
        Save archive metadata to companion file.
        
        Args:
            archive_path: Archive file
            metadata: Metadata to save
        """
        metadata_path = archive_path.with_suffix(archive_path.suffix + '.meta')
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        self.logger.debug(f"Saved metadata: {metadata_path}")
    
    def _load_metadata(self, archive_path: Path) -> Optional[ArchiveMetadata]:
        """
        Load archive metadata from companion file.
        
        Args:
            archive_path: Archive file
            
        Returns:
            Metadata if found, None otherwise
        """
        metadata_path = archive_path.with_suffix(archive_path.suffix + '.meta')
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            return ArchiveMetadata.from_dict(data)
            
        except Exception as e:
            self.logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
            return None
    
    def _increment_operation_count(self) -> None:
        """Thread-safe increment of operation counter"""
        with self._stats_lock:
            self._operation_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get archive manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._stats_lock:
            return {
                'operation_count': self._operation_count,
                'bytes_processed': self._bytes_processed,
                'archives_created': self._archives_created,
                'archives_extracted': self._archives_extracted,
                'platform': self.platform.name
            }