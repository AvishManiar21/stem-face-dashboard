"""
CSV File Watcher Module
Monitors CSV files for changes and triggers data reload
"""
import logging
from pathlib import Path
from typing import Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog library not available. Install with: pip install watchdog")


class CSVReloadHandler(FileSystemEventHandler):
    """Handles CSV file change events"""
    
    def __init__(self, reload_callback: Callable, data_dir: Path):
        super().__init__()
        self.reload_callback = reload_callback
        self.data_dir = data_dir
        self.last_reload_time = {}
        self.reload_cooldown = 2.0  # Minimum seconds between reloads for same file
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
        
        if not event.src_path.endswith('.csv'):
            return
        
        # Only watch files in data directory
        try:
            file_path = Path(event.src_path)
            if self.data_dir not in file_path.parents:
                return
        except:
            return
        
        # Cooldown check - prevent multiple rapid reloads
        current_time = time.time()
        if event.src_path in self.last_reload_time:
            time_since_last = current_time - self.last_reload_time[event.src_path]
            if time_since_last < self.reload_cooldown:
                logger.debug(f"Skipping reload for {event.src_path} (cooldown)")
                return
        
        self.last_reload_time[event.src_path] = current_time
        
        logger.info(f"CSV file modified: {event.src_path}")
        
        try:
            # Call the reload callback
            if self.reload_callback:
                self.reload_callback()
                logger.info("Data reloaded successfully")
        except Exception as e:
            logger.error(f"Error during auto-reload: {e}")


class CSVWatcher:
    """Manages CSV file watching"""
    
    def __init__(self, data_dir: str = 'data/core', reload_callback: Optional[Callable] = None):
        self.data_dir = Path(data_dir)
        self.reload_callback = reload_callback
        self.observer: Optional[Observer] = None
        self.is_watching = False
        
        if not WATCHDOG_AVAILABLE:
            logger.warning("CSV file watching disabled - watchdog library not installed")
    
    def start_watching(self):
        """Start watching CSV files for changes"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Cannot start file watcher - watchdog library not available")
            return False
        
        if self.is_watching:
            logger.warning("File watcher is already running")
            return False
        
        try:
            self.observer = Observer()
            event_handler = CSVReloadHandler(self.reload_callback, self.data_dir)
            self.observer.schedule(event_handler, str(self.data_dir), recursive=False)
            self.observer.start()
            self.is_watching = True
            logger.info(f"Started watching CSV files in {self.data_dir}")
            return True
        except Exception as e:
            logger.error(f"Error starting file watcher: {e}")
            return False
    
    def stop_watching(self):
        """Stop watching CSV files"""
        if not self.is_watching or not self.observer:
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            logger.info("Stopped watching CSV files")
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
    
    def is_active(self) -> bool:
        """Check if file watcher is active"""
        return self.is_watching and self.observer and self.observer.is_alive()

