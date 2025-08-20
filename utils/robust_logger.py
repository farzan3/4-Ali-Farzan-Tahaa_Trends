"""
Robust Logging System for Hunter Platform
Provides comprehensive logging with detailed error tracking, performance metrics, and scraping validation
"""

import logging
import logging.handlers
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import traceback
import sys
from functools import wraps

class RobustLogger:
    """Comprehensive logging system with multiple handlers and metrics tracking"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Performance metrics
        self.metrics = {
            'scraping_attempts': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_items_scraped': 0,
            'average_response_time': 0,
            'error_counts': {},
            'last_reset': datetime.now(),
            'uptime_start': datetime.now()
        }
        
        # Setup handlers
        self._setup_handlers()
        
        # Log startup
        self.info(f"RobustLogger initialized for {name}")
    
    def _setup_handlers(self):
        """Setup multiple logging handlers for different purposes"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Rotating file handler for general logs
        general_log_file = self.log_dir / f"{self.name}_general.log"
        file_handler = logging.handlers.RotatingFileHandler(
            general_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error-only file handler
        error_log_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # JSON handler for structured logs (scraping data)
        json_log_file = self.log_dir / f"{self.name}_data.jsonl"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """Debug level logging with optional extra data"""
        self.logger.debug(message, extra={'data': kwargs})
    
    def info(self, message: str, **kwargs):
        """Info level logging with optional extra data"""
        self.logger.info(message, extra={'data': kwargs})
    
    def warning(self, message: str, **kwargs):
        """Warning level logging with optional extra data"""
        self.logger.warning(message, extra={'data': kwargs})
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Error level logging with exception details"""
        error_data = kwargs.copy()
        
        if exception:
            error_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        
        self.logger.error(message, extra={'data': error_data})
        
        # Update error metrics
        error_type = type(exception).__name__ if exception else 'Unknown'
        self.metrics['error_counts'][error_type] = self.metrics['error_counts'].get(error_type, 0) + 1
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Critical level logging with exception details"""
        self.error(message, exception, **kwargs)
        self.logger.critical(message, extra={'data': kwargs})
    
    def log_scraping_attempt(self, source: str, url: str, params: Dict[str, Any] = None):
        """Log a scraping attempt with detailed information"""
        self.metrics['scraping_attempts'] += 1
        
        self.info("Scraping attempt started", 
                 source=source, 
                 url=url, 
                 params=params,
                 attempt_number=self.metrics['scraping_attempts'])
    
    def log_scraping_success(self, source: str, url: str, items_count: int, 
                           response_time: float, data_sample: Dict[str, Any] = None):
        """Log successful scraping with metrics"""
        self.metrics['successful_scrapes'] += 1
        self.metrics['total_items_scraped'] += items_count
        
        # Update average response time
        total_attempts = self.metrics['scraping_attempts']
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (total_attempts - 1) + response_time) / total_attempts
        )
        
        self.info("Scraping completed successfully",
                 source=source,
                 url=url,
                 items_scraped=items_count,
                 response_time_ms=round(response_time * 1000, 2),
                 success_rate=round(self.get_success_rate() * 100, 2),
                 sample_data=data_sample)
    
    def log_scraping_failure(self, source: str, url: str, error: Exception, 
                           retry_count: int = 0, will_retry: bool = False):
        """Log failed scraping with detailed error information"""
        self.metrics['failed_scrapes'] += 1
        
        self.error("Scraping failed",
                  exception=error,
                  source=source,
                  url=url,
                  retry_count=retry_count,
                  will_retry=will_retry,
                  success_rate=round(self.get_success_rate() * 100, 2))
    
    def log_data_validation(self, source: str, expected_fields: List[str], 
                          actual_data: Dict[str, Any], validation_passed: bool):
        """Log data validation results"""
        missing_fields = [field for field in expected_fields if field not in actual_data]
        extra_fields = [field for field in actual_data.keys() if field not in expected_fields]
        
        level = "info" if validation_passed else "warning"
        method = getattr(self, level)
        
        method("Data validation completed",
               source=source,
               validation_passed=validation_passed,
               expected_fields=expected_fields,
               missing_fields=missing_fields,
               extra_fields=extra_fields,
               data_completeness=round((len(expected_fields) - len(missing_fields)) / len(expected_fields) * 100, 2))
    
    def log_performance_metrics(self, operation: str, duration: float, **kwargs):
        """Log performance metrics for operations"""
        self.info("Performance metrics",
                 operation=operation,
                 duration_seconds=round(duration, 3),
                 **kwargs)
    
    def get_success_rate(self) -> float:
        """Calculate current success rate"""
        total = self.metrics['scraping_attempts']
        if total == 0:
            return 1.0
        return self.metrics['successful_scrapes'] / total
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        uptime = datetime.now() - self.metrics['uptime_start']
        
        return {
            'logger_name': self.name,
            'uptime_hours': round(uptime.total_seconds() / 3600, 2),
            'total_scraping_attempts': self.metrics['scraping_attempts'],
            'successful_scrapes': self.metrics['successful_scrapes'],
            'failed_scrapes': self.metrics['failed_scrapes'],
            'success_rate_percent': round(self.get_success_rate() * 100, 2),
            'total_items_scraped': self.metrics['total_items_scraped'],
            'average_response_time_ms': round(self.metrics['average_response_time'] * 1000, 2),
            'error_breakdown': self.metrics['error_counts'],
            'last_reset': self.metrics['last_reset'].isoformat()
        }
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'scraping_attempts': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_items_scraped': 0,
            'average_response_time': 0,
            'error_counts': {},
            'last_reset': datetime.now(),
            'uptime_start': self.metrics['uptime_start']  # Keep original uptime
        }
        self.info("Metrics reset completed")


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'logger': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra data if present
        if hasattr(record, 'data') and record.data:
            log_entry['data'] = record.data
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def log_method_calls(logger: RobustLogger):
    """Decorator to automatically log method calls and performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            method_name = func.__name__
            
            # Log method start
            logger.debug(f"Method {method_name} started", 
                        args_count=len(args), 
                        kwargs_keys=list(kwargs.keys()))
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log successful completion
                logger.debug(f"Method {method_name} completed successfully",
                           duration_seconds=round(duration, 3))
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log method failure
                logger.error(f"Method {method_name} failed", 
                           exception=e,
                           duration_seconds=round(duration, 3))
                raise
        
        return wrapper
    return decorator


# Global logger instances
_loggers = {}

def get_logger(name: str) -> RobustLogger:
    """Get or create a logger instance"""
    if name not in _loggers:
        _loggers[name] = RobustLogger(name)
    return _loggers[name]


# Predefined loggers for different components
app_store_logger = get_logger("app_store_scraper")
steam_logger = get_logger("steam_scraper") 
events_logger = get_logger("events_scraper")
pipeline_logger = get_logger("data_pipeline")
analytics_logger = get_logger("analytics")