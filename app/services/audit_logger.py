"""
Servicio de logs inmutables para auditoría - SRF5.
Registra acciones de usuario con integridad garantizada mediante hash.
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Tipos de acciones auditables para SRF5."""
    UPLOAD = "UPLOAD"           # Subida de archivos
    ANALYSIS = "ANALYSIS"       # Análisis de código
    DOWNLOAD = "DOWNLOAD"       # Descarga de reportes
    LOGIN = "LOGIN"             # Inicio de sesión
    LOGOUT = "LOGOUT"           # Cierre de sesión
    SECURITY_SCAN = "SECURITY_SCAN"  # Escaneo de seguridad (SRF3)
    PRIVACY_REQUEST = "PRIVACY_REQUEST"  # Solicitud de privacidad (PRF2)
    PRIVACY_PROCESS = "PRIVACY_PROCESS"  # Procesamiento de privacidad (PRF2)
    DATA_ACCESS = "DATA_ACCESS"  # Acceso a datos personales (PRF2)
    DATA_RECTIFICATION = "DATA_RECTIFICATION"  # Rectificación de datos (PRF2)
    DATA_ERASURE = "DATA_ERASURE"  # Eliminación de datos (PRF2)
    TREATMENT_CREATE = "TREATMENT_CREATE"  # Creación de tratamiento (PRF4)
    TREATMENT_UPDATE = "TREATMENT_UPDATE"  # Actualización de tratamiento (PRF4)
    TREATMENT_DELETE = "TREATMENT_DELETE"  # Eliminación de tratamiento (PRF4)
    DPA_CREATE = "DPA_CREATE"  # Creación de DPA (PRF5)
    DPA_UPDATE = "DPA_UPDATE"  # Actualización de DPA (PRF5)
    DPA_STATUS_CHANGE = "DPA_STATUS_CHANGE"  # Cambio de estado DPA (PRF5)

class AuditResult(Enum):
    """Resultados de acciones auditables."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE" 
    REJECTED = "REJECTED"       # Para SRF3 - archivos rechazados
    ERROR = "ERROR"

class ImmutableAuditLogger:
    """
    Logger de auditoría inmutable para SRF5.
    Garantiza integridad mediante hash encadenado y timestamps precisos.
    """
    
    def __init__(self, audit_dir: str):
        """
        Inicializa el logger de auditoría inmutable.
        
        Args:
            audit_dir: Directorio para logs de auditoría
        """
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de logs diario
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.audit_dir / f"audit_{today}.jsonl"
        
        # Archivo de integridad (hashes)
        self.integrity_file = self.audit_dir / f"integrity_{today}.hash"
        
        # Hash del último registro (para encadenamiento)
        self.last_hash = self._get_last_hash()
    
    def log_audit_event(
        self, 
        user_id: int, 
        username: str,
        action: AuditAction, 
        result: AuditResult,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Registra un evento de auditoría de forma inmutable.
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario
            action: Tipo de acción realizada
            result: Resultado de la acción
            details: Detalles adicionales de la acción
            ip_address: Dirección IP del usuario
            user_agent: User-Agent del navegador
            
        Returns:
            Hash del registro creado
        """
        # Timestamp preciso con microsegundos
        timestamp = datetime.now().isoformat()
        
        # Crear registro de auditoría
        audit_record = {
            "timestamp": timestamp,
            "user_id": user_id,
            "username": username,
            "action": action.value,
            "result": result.value,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "previous_hash": self.last_hash
        }
        
        # Calcular hash del registro (inmutabilidad)
        record_hash = self._calculate_record_hash(audit_record)
        audit_record["record_hash"] = record_hash
        
        # Escribir al archivo de logs
        self._write_audit_record(audit_record)
        
        # Actualizar archivo de integridad
        self._update_integrity_file(record_hash, audit_record)
        
        # Actualizar hash para próximo registro
        self.last_hash = record_hash
        
        logger.info(f"📝 SRF5: Evento auditado - Usuario: {username}, Acción: {action.value}, Resultado: {result.value}")
        
        return record_hash
    
    def _calculate_record_hash(self, record: Dict) -> str:
        """
        Calcula hash SHA-256 del registro para garantizar inmutabilidad.
        
        Args:
            record: Registro de auditoría
            
        Returns:
            Hash SHA-256 del registro
        """
        # Crear cadena determinística del registro (sin el hash)
        record_copy = record.copy()
        if "record_hash" in record_copy:
            del record_copy["record_hash"]
        
        # Serializar de forma determinística
        record_string = json.dumps(record_copy, sort_keys=True, separators=(',', ':'))
        
        # Calcular SHA-256
        return hashlib.sha256(record_string.encode('utf-8')).hexdigest()
    
    def _write_audit_record(self, record: Dict) -> None:
        """
        Escribe registro al archivo de logs (append-only).
        
        Args:
            record: Registro de auditoría a escribir
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(record, f, separators=(',', ':'))
            f.write('\n')  # JSONL format
    
    def _update_integrity_file(self, record_hash: str, record: Dict) -> None:
        """
        Actualiza archivo de integridad con hash y metadatos.
        
        Args:
            record_hash: Hash del registro
            record: Registro original
        """
        integrity_entry = {
            "timestamp": record["timestamp"],
            "user_id": record["user_id"],
            "action": record["action"],
            "result": record["result"],
            "record_hash": record_hash,
            "previous_hash": record.get("previous_hash", ""),
            "file_position": self._get_file_position()
        }
        
        with open(self.integrity_file, 'a', encoding='utf-8') as f:
            json.dump(integrity_entry, f, separators=(',', ':'))
            f.write('\n')
    
    def _get_last_hash(self) -> str:
        """
        Obtiene el hash del último registro para encadenamiento.
        
        Returns:
            Hash del último registro o cadena vacía
        """
        if not self.integrity_file.exists():
            return ""
        
        try:
            with open(self.integrity_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    last_entry = json.loads(last_line)
                    return last_entry.get("record_hash", "")
        except Exception as e:
            logger.warning(f"Error obteniendo último hash: {e}")
        
        return ""
    
    def _get_file_position(self) -> int:
        """
        Obtiene la posición actual en el archivo de logs.
        
        Returns:
            Posición en bytes del archivo
        """
        return self.log_file.stat().st_size if self.log_file.exists() else 0
    
    def verify_audit_integrity(self) -> Dict[str, Any]:
        """
        Verifica la integridad de los logs de auditoría.
        
        Returns:
            Resultado de verificación de integridad
        """
        verification_result = {
            "verified": True,
            "total_records": 0,
            "verified_records": 0,
            "errors": [],
            "hash_chain_valid": True
        }
        
        if not self.log_file.exists():
            verification_result["errors"].append("Archivo de logs no existe")
            verification_result["verified"] = False
            return verification_result
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                previous_hash = ""
                
                for line_num, line in enumerate(f, 1):
                    linea = line.strip()
                    if not line:
                        continue
                    
                    verification_result["total_records"] += 1
                    
                    try:
                        record = json.loads(line)
                        
                        # Verificar hash del registro
                        stored_hash = record.get("record_hash", "")
                        calculated_hash = self._calculate_record_hash(record)
                        
                        if stored_hash != calculated_hash:
                            error = f"Línea {line_num}: Hash inválido - esperado {calculated_hash}, encontrado {stored_hash}"
                            verification_result["errors"].append(error)
                            verification_result["verified"] = False
                        
                        # Verificar encadenamiento
                        if record.get("previous_hash", "") != previous_hash:
                            error = f"Línea {line_num}: Cadena rota - esperado {previous_hash}, encontrado {record.get('previous_hash')}"
                            verification_result["errors"].append(error)
                            verification_result["hash_chain_valid"] = False
                            verification_result["verified"] = False
                        
                        if stored_hash == calculated_hash:
                            verification_result["verified_records"] += 1
                        
                        previous_hash = stored_hash
                        
                    except json.JSONDecodeError as e:
                        error = f"Línea {line_num}: JSON inválido - {e}"
                        verification_result["errors"].append(error)
                        verification_result["verified"] = False
                        
        except Exception as e:
            verification_result["errors"].append(f"Error leyendo archivo: {e}")
            verification_result["verified"] = False
        
        return verification_result

    def get_audit_summary(self, user_id: Optional[int] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Obtiene resumen de actividad de auditoría.
        
        Args:
            user_id: Filtrar por usuario específico (opcional)
            hours: Últimas N horas a incluir
            
        Returns:
            Resumen de actividad
        """
        summary = {
            "total_events": 0,
            "by_action": {},
            "by_result": {},
            "by_user": {},
            "time_range": f"Últimas {hours} horas",
            "file": str(self.log_file)
        }
        
        if not self.log_file.exists():
            return summary
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    linea = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        record_time = datetime.fromisoformat(record["timestamp"]).timestamp()
                        
                        # Filtrar por tiempo
                        if record_time < cutoff_time:
                            continue
                        
                        # Filtrar por usuario si se especifica
                        if user_id and record.get("user_id") != user_id:
                            continue
                        
                        summary["total_events"] += 1
                        
                        # Contar por acción
                        action = record.get("action", "UNKNOWN")
                        summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
                        
                        # Contar por resultado
                        result = record.get("result", "UNKNOWN")
                        summary["by_result"][result] = summary["by_result"].get(result, 0) + 1
                        
                        # Contar por usuario
                        nombre_usuario = record.get("username", "unknown")
                        summary["by_user"][username] = summary["by_user"].get(username, 0) + 1
                        
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
        
        return summary


# Instancia global del logger
_audit_logger: Optional[ImmutableAuditLogger] = None

def get_audit_logger(audit_dir: str) -> ImmutableAuditLogger:
    """
    Obtiene instancia singleton del logger de auditoría.
    
    Args:
        audit_dir: Directorio de auditoría
        
    Returns:
        Instancia del logger
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = ImmutableAuditLogger(audit_dir)
    return _audit_logger

class AuditLogger:
    """
    Clase simplificada para logging de auditoría con soporte para privacidad.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        from app.config.config import settings
        self._audit_logger = get_audit_logger(settings.AUDIT_DIR)
    
    def log_privacy_request_created(self, user_id: int, request_id: int, request_type: str):
        """Log cuando se crea una solicitud de privacidad"""
        return self._audit_logger.log_audit_event(
            usuario_id =user_id,
            nombre_usuario =f"user_{user_id}",
            action=AuditAction.PRIVACY_REQUEST,
            result=AuditResult.SUCCESS,
            details={
                "request_id": request_id,
                "request_type": request_type,
                "action": "created"
            }
        )
    
    def log_privacy_request_processed(self, request_id: int, processor_id: int, action: str, details: str = None):
        """Log cuando se procesa una solicitud de privacidad"""
        return self._audit_logger.log_audit_event(
            usuario_id =processor_id,
            nombre_usuario =f"admin_{processor_id}",
            action=AuditAction.PRIVACY_PROCESS,
            result=AuditResult.SUCCESS,
            details={
                "request_id": request_id,
                "action": action,
                "details": details
            }
        )
    
    def log_data_access(self, user_id: int, accessed_by: int, data_type: str):
        """Log cuando se accede a datos personales"""
        return self._audit_logger.log_audit_event(
            usuario_id =accessed_by,
            nombre_usuario =f"user_{accessed_by}",
            action=AuditAction.DATA_ACCESS,
            result=AuditResult.SUCCESS,
            details={
                "target_user_id": user_id,
                "data_type": data_type
            }
        )
    
    def log_data_rectification(self, user_id: int, modified_by: int, changes: dict):
        """Log cuando se modifican datos personales"""
        return self._audit_logger.log_audit_event(
            usuario_id =modified_by,
            nombre_usuario =f"admin_{modified_by}",
            action=AuditAction.DATA_RECTIFICATION,
            result=AuditResult.SUCCESS,
            details={
                "target_user_id": user_id,
                "changes": changes
            }
        )
    
    def log_data_erasure(self, user_id: int, erased_by: int):
        """Log cuando se eliminan datos personales"""
        return self._audit_logger.log_audit_event(
            usuario_id =erased_by,
            nombre_usuario =f"admin_{erased_by}",
            action=AuditAction.DATA_ERASURE,
            result=AuditResult.SUCCESS,
            details={
                "target_user_id": user_id,
                "action": "complete_erasure"
            }
        )

def log_user_action(
    user_id: int,
    username: str, 
    action: AuditAction,
    result: AuditResult,
    details: Optional[Dict[str, Any]] = None,
    audit_dir: str = "audit_logs"
) -> str:
    """
    Función de conveniencia para registrar acciones de usuario.
    
    Args:
        user_id: ID del usuario
        username: Nombre del usuario
        action: Acción realizada
        result: Resultado de la acción
        details: Detalles adicionales
        audit_dir: Directorio de auditoría
        
    Returns:
        Hash del registro creado
    """
    audit_logger = get_audit_logger(audit_dir)
    return audit_logger.log_audit_event(user_id, username, action, result, details)
