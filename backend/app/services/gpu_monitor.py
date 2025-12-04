"""
GPU monitoring and management utilities for tracking GPU utilization.
"""
import logging
import subprocess
import sys
from typing import Optional, Dict
import time

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Monitor GPU usage and performance."""
    
    def __init__(self):
        self.nvidia_smi_available = self._check_nvidia_smi()
    
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_gpu_info(self) -> Optional[Dict]:
        """
        Get GPU information and utilization.
        
        Returns:
            Dictionary with GPU info or None if not available
        """
        if not self.nvidia_smi_available:
            return None
        
        try:
            # Get GPU utilization and memory info
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.strip().split('\n')
            gpus = []
            
            for line in lines:
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 6:
                        gpus.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'memory_used_mb': int(parts[2]),
                            'memory_total_mb': int(parts[3]),
                            'utilization_percent': int(parts[4]),
                            'temperature_c': int(parts[5]),
                            'memory_usage_percent': int((int(parts[2]) / int(parts[3])) * 100) if int(parts[3]) > 0 else 0
                        })
            
            return {'gpus': gpus, 'timestamp': time.time()}
            
        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            return None
    
    def log_gpu_status(self):
        """Log current GPU status."""
        gpu_info = self.get_gpu_info()
        
        if gpu_info is None:
            logger.info("GPU monitoring not available (nvidia-smi not found)")
            return
        
        logger.info("=" * 60)
        logger.info("GPU Status:")
        logger.info("=" * 60)
        
        for gpu in gpu_info['gpus']:
            logger.info(f"GPU {gpu['index']}: {gpu['name']}")
            logger.info(f"  Utilization: {gpu['utilization_percent']}%")
            logger.info(f"  Memory: {gpu['memory_used_mb']}MB / {gpu['memory_total_mb']}MB "
                       f"({gpu['memory_usage_percent']}%)")
            logger.info(f"  Temperature: {gpu['temperature_c']}°C")
        
        logger.info("=" * 60)
    
    def is_gpu_busy(self, threshold: int = 80) -> bool:
        """
        Check if GPU utilization is above threshold.
        
        Args:
            threshold: Utilization percentage threshold (default 80%)
            
        Returns:
            True if GPU utilization > threshold
        """
        gpu_info = self.get_gpu_info()
        if gpu_info is None:
            return False
        
        for gpu in gpu_info['gpus']:
            if gpu['utilization_percent'] > threshold:
                return True
        
        return False
    
    def get_gpu_memory_usage(self, device_id: int = 0) -> Optional[float]:
        """
        Get GPU memory usage as percentage.
        
        Args:
            device_id: GPU device ID
            
        Returns:
            Memory usage percentage (0-100) or None
        """
        gpu_info = self.get_gpu_info()
        if gpu_info is None:
            return None
        
        for gpu in gpu_info['gpus']:
            if gpu['index'] == device_id:
                return gpu['memory_usage_percent']
        
        return None


# Global GPU monitor instance
_gpu_monitor: Optional[GPUMonitor] = None


def get_gpu_monitor() -> GPUMonitor:
    """Get or create global GPU monitor instance."""
    global _gpu_monitor
    if _gpu_monitor is None:
        _gpu_monitor = GPUMonitor()
    return _gpu_monitor

