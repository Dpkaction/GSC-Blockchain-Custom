"""
GSC Coin Logging Configuration
Centralized logging system for the entire GSC Blockchain application
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class GSCLogger:
    """Centralized logger for GSC Coin"""
    
    def __init__(self):
        self.loggers = {}
        self.log_dir = "logs"
        self.setup_log_directory()
        self.setup_main_logger()
    
    def setup_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_main_logger(self):
        """Setup the main application logger"""
        # Create main logger
        main_logger = logging.getLogger('gsc_coin')
        main_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        main_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        main_logger.addHandler(console_handler)
        
        # File handler for all logs
        log_file = os.path.join(self.log_dir, f"gsc_coin_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        main_logger.addHandler(file_handler)
        
        # Error file handler
        error_file = os.path.join(self.log_dir, f"gsc_coin_errors_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        main_logger.addHandler(error_handler)
        
        self.loggers['main'] = main_logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger for a specific module"""
        if name not in self.loggers:
            logger = logging.getLogger(f'gsc_coin.{name}')
            logger.setLevel(logging.DEBUG)
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def set_level(self, level: str):
        """Set logging level for all loggers"""
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        for logger in self.loggers.values():
            logger.setLevel(log_level)

# Global logger instance
gsc_logger = GSCLogger()

def get_logger(name: str = 'main') -> logging.Logger:
    """Get logger instance"""
    return gsc_logger.get_logger(name)

def set_log_level(level: str):
    """Set global log level"""
    gsc_logger.set_level(level)

# Module-specific loggers
blockchain_logger = get_logger('blockchain')
network_logger = get_logger('network')
rpc_logger = get_logger('rpc')
wallet_logger = get_logger('wallet')
gui_logger = get_logger('gui')
mining_logger = get_logger('mining')
