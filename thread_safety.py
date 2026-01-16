"""
GSC Coin Thread Safety Utilities
Provides thread-safe operations for blockchain components
"""

import threading
from typing import Any, Callable, TypeVar, Generic
from contextlib import contextmanager
import time

T = TypeVar('T')

class ThreadSafeList:
    """Thread-safe list implementation"""
    
    def __init__(self):
        self._list = []
        self._lock = threading.RLock()
    
    def append(self, item: T) -> None:
        """Thread-safe append"""
        with self._lock:
            self._list.append(item)
    
    def remove(self, item: T) -> bool:
        """Thread-safe remove"""
        with self._lock:
            try:
                self._list.remove(item)
                return True
            except ValueError:
                return False
    
    def pop(self, index: int = -1) -> T:
        """Thread-safe pop"""
        with self._lock:
            return self._list.pop(index)
    
    def clear(self) -> None:
        """Thread-safe clear"""
        with self._lock:
            self._list.clear()
    
    def copy(self) -> list[T]:
        """Thread-safe copy"""
        with self._lock:
            return self._list.copy()
    
    def __len__(self) -> int:
        """Thread-safe length"""
        with self._lock:
            return len(self._list)
    
    def __getitem__(self, index: int) -> T:
        """Thread-safe getitem"""
        with self._lock:
            return self._list[index]
    
    def __setitem__(self, index: int, value: T) -> None:
        """Thread-safe setitem"""
        with self._lock:
            self._list[index] = value
    
    def __contains__(self, item: T) -> bool:
        """Thread-safe contains"""
        with self._lock:
            return item in self._list
    
    def __iter__(self):
        """Thread-safe iteration"""
        # Return a copy to avoid modification during iteration
        return iter(self.copy())

class ThreadSafeDict:
    """Thread-safe dictionary implementation"""
    
    def __init__(self):
        self._dict = {}
        self._lock = threading.RLock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Thread-safe get"""
        with self._lock:
            return self._dict.get(key, default)
    
    def set(self, key: Any, value: Any) -> None:
        """Thread-safe set"""
        with self._lock:
            self._dict[key] = value
    
    def __setitem__(self, key: Any, value: Any) -> None:
        """Thread-safe setitem"""
        with self._lock:
            self._dict[key] = value
    
    def __getitem__(self, key: Any) -> Any:
        """Thread-safe getitem"""
        with self._lock:
            return self._dict[key]
    
    def __contains__(self, key: Any) -> bool:
        """Thread-safe contains"""
        with self._lock:
            return key in self._dict
    
    def __delitem__(self, key: Any) -> None:
        """Thread-safe delitem"""
        with self._lock:
            del self._dict[key]
    
    def keys(self):
        """Thread-safe keys"""
        with self._lock:
            return list(self._dict.keys())
    
    def values(self):
        """Thread-safe values"""
        with self._lock:
            return list(self._dict.values())
    
    def items(self):
        """Thread-safe items"""
        with self._lock:
            return list(self._dict.items())
    
    def clear(self) -> None:
        """Thread-safe clear"""
        with self._lock:
            self._dict.clear()
    
    def copy(self) -> dict:
        """Thread-safe copy"""
        with self._lock:
            return self._dict.copy()
    
    def update(self, other: dict) -> None:
        """Thread-safe update"""
        with self._lock:
            self._dict.update(other)

class AtomicCounter:
    """Thread-safe counter"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.RLock()
    
    def increment(self, amount: int = 1) -> int:
        """Increment counter and return new value"""
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount: int = 1) -> int:
        """Decrement counter and return new value"""
        with self._lock:
            self._value -= amount
            return self._value
    
    def get(self) -> int:
        """Get current value"""
        with self._lock:
            return self._value
    
    def set(self, value: int) -> None:
        """Set counter value"""
        with self._lock:
            self._value = value

class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = ThreadSafeList()
        self.lock = threading.RLock()
    
    def is_allowed(self) -> bool:
        """Check if call is allowed"""
        current_time = time.time()
        
        # Remove old calls outside time window
        with self.lock:
            self.calls = ThreadSafeList([
                call_time for call_time in self.calls
                if current_time - call_time < self.time_window
            ])
            
            if len(self.calls) < self.max_calls:
                self.calls.append(current_time)
                return True
            
            return False
    
    def wait_time(self) -> float:
        """Get time to wait before next allowed call"""
        if len(self.calls) == 0:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))

@contextmanager
def timeout_context(seconds: float):
    """Context manager for timeout operations"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Note: This only works on Unix-like systems
    if hasattr(threading, '_thread'):
        import signal
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows fallback - just yield without timeout
        yield

class ThreadSafeSet:
    """Thread-safe set implementation"""
    
    def __init__(self):
        self._set = set()
        self._lock = threading.RLock()
    
    def add(self, item: T) -> None:
        """Thread-safe add"""
        with self._lock:
            self._set.add(item)
    
    def remove(self, item: T) -> bool:
        """Thread-safe remove"""
        with self._lock:
            try:
                self._set.remove(item)
                return True
            except KeyError:
                return False
    
    def discard(self, item: T) -> None:
        """Thread-safe discard"""
        with self._lock:
            self._set.discard(item)
    
    def __contains__(self, item: T) -> bool:
        """Thread-safe contains"""
        with self._lock:
            return item in self._set
    
    def __len__(self) -> int:
        """Thread-safe length"""
        with self._lock:
            return len(self._set)
    
    def copy(self) -> set:
        """Thread-safe copy"""
        with self._lock:
            return self._set.copy()
    
    def clear(self) -> None:
        """Thread-safe clear"""
        with self._lock:
            self._set.clear()
    
    def __iter__(self):
        """Thread-safe iteration"""
        # Return a copy to avoid modification during iteration
        return iter(self.copy())
