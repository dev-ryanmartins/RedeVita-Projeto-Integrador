"""
Utilitário de Métricas e Diagnóstico de Performance do Sistema.

Este módulo fornece funções para monitorar a saúde da aplicação,
incluindo uptime, uso de memória e integridade da conexão com banco de dados.
"""

import time
import psutil
import os
from datetime import datetime, timedelta
from flask import current_app


class SystemHealthMonitor:
    """Monitor de saúde do sistema com métricas em tempo real."""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())
    
    def get_uptime(self):
        """
        Retorna o uptime da aplicação em segundos e formatado.
        
        Returns:
            dict: Uptime em segundos e formato legível
        """
        uptime_seconds = time.time() - self.start_time
        uptime_formatted = str(timedelta(seconds=int(uptime_seconds)))
        
        return {
            "seconds": round(uptime_seconds, 2),
            "formatted": uptime_formatted,
            "started_at": datetime.fromtimestamp(self.start_time).isoformat()
        }
    
    def get_memory_usage(self):
        """
        Retorna métricas de uso de memória do processo e do sistema.
        
        Returns:
            dict: Métricas de memória do processo e do sistema
        """
        # Memória do processo
        process_memory = self.process.memory_info()
        process_memory_percent = self.process.memory_percent()
        
        # Memória do sistema
        system_memory = psutil.virtual_memory()
        
        return {
            "process": {
                "rss_mb": round(process_memory.rss / (1024 * 1024), 2),
                "vms_mb": round(process_memory.vms / (1024 * 1024), 2),
                "percent": round(process_memory_percent, 2)
            },
            "system": {
                "total_mb": round(system_memory.total / (1024 * 1024), 2),
                "available_mb": round(system_memory.available / (1024 * 1024), 2),
                "used_mb": round(system_memory.used / (1024 * 1024), 2),
                "percent": system_memory.percent
            }
        }
    
    def get_cpu_usage(self):
        """
        Retorna métricas de uso de CPU.
        
        Returns:
            dict: Métricas de CPU do processo e do sistema
        """
        cpu_percent = self.process.cpu_percent(interval=0.1)
        system_cpu = psutil.cpu_percent(interval=0.1)
        
        return {
            "process_percent": round(cpu_percent, 2),
            "system_percent": round(system_cpu, 2),
            "cpu_count": psutil.cpu_count()
        }
    
    def check_database_connection(self, db):
        """
        Verifica a integridade da conexão com o banco de dados.
        
        Args:
            db: Instância do banco de dados SQLAlchemy
            
        Returns:
            dict: Status da conexão e tempo de resposta
        """
        try:
            start_time = time.time()
            
            # Executa query simples para testar conexão
            db.session.execute(db.text("SELECT 1"))
            
            response_time = (time.time() - start_time) * 1000  # em milissegundos
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "message": "Conexão com banco de dados estável"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "message": f"Erro na conexão: {str(e)}"
            }
    
    def get_disk_usage(self):
        """
        Retorna métricas de uso de disco.
        
        Returns:
            dict: Métricas de uso de disco
        """
        disk = psutil.disk_usage('/')
        
        return {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        }
    
    def get_network_info(self):
        """
        Retorna informações de rede básicas.
        
        Returns:
            dict: Informações de rede
        """
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception:
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            }
    
    def get_full_health_report(self, db):
        """
        Retorna relatório completo de saúde do sistema.
        
        Args:
            db: Instância do banco de dados SQLAlchemy
            
        Returns:
            dict: Relatório completo com todas as métricas
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": self.get_uptime(),
            "memory": self.get_memory_usage(),
            "cpu": self.get_cpu_usage(),
            "database": self.check_database_connection(db),
            "disk": self.get_disk_usage(),
            "network": self.get_network_info(),
            "overall_status": self._calculate_overall_status(db)
        }
    
    def _calculate_overall_status(self, db):
        """
        Calcula status geral do sistema baseado nas métricas.
        
        Args:
            db: Instância do banco de dados SQLAlchemy
            
        Returns:
            str: Status geral (healthy, warning, critical)
        """
        db_status = self.check_database_connection(db)
        memory = self.get_memory_usage()
        cpu = self.get_cpu_usage()
        disk = self.get_disk_usage()
        
        # Critério para status
        if db_status["status"] != "healthy":
            return "critical"
        
        if (memory["system"]["percent"] > 90 or 
            cpu["system_percent"] > 90 or 
            disk["percent"] > 90):
            return "warning"
        
        return "healthy"


# Instância global do monitor
_system_monitor = None


def get_system_monitor():
    """
    Retorna a instância global do monitor de sistema.
    
    Returns:
        SystemHealthMonitor: Instância do monitor
    """
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemHealthMonitor()
    return _system_monitor


def get_health_summary(db):
    """
    Retorna resumo simplificado de saúde do sistema.
    
    Args:
        db: Instância do banco de dados SQLAlchemy
        
    Returns:
        dict: Resumo simplificado das métricas principais
    """
    monitor = get_system_monitor()
    full_report = monitor.get_full_health_report(db)
    
    return {
        "status": full_report["overall_status"],
        "uptime": full_report["uptime"]["formatted"],
        "memory_percent": full_report["memory"]["system"]["percent"],
        "cpu_percent": full_report["cpu"]["system_percent"],
        "database_status": full_report["database"]["status"],
        "disk_percent": full_report["disk"]["percent"],
        "timestamp": full_report["timestamp"]
    }
