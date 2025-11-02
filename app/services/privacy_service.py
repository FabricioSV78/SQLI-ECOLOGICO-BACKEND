"""
Servicio para gestionar solicitudes de privacidad de datos (PRF2)
Implementa los derechos GDPR: acceso, rectificación y eliminación
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.privacy_request import PrivacyRequest, PrivacyRequestType, PrivacyRequestStatus
from app.models.user import User
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.vulnerability import Vulnerability
from app.models.analysis_metrics import AnalysisMetrics
from app.models.user_role import UserRole
from app.services.audit_logger import AuditLogger

class PrivacyService:
    """
    Servicio para gestionar solicitudes de privacidad según GDPR/LOPD.
    Implementa PRF2: Flujo para solicitudes de acceso, rectificación o eliminación.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = AuditLogger(db)

    # === CREAR SOLICITUDES ===

    def create_access_request(self, user_id: int, description: str = None) -> PrivacyRequest:
        """
        Crea una solicitud de acceso a datos personales (Art. 15 GDPR).
        El titular tiene derecho a obtener información sobre el tratamiento de sus datos.
        """
        return self._create_request(
            usuario_id =user_id,
            request_type=PrivacyRequestType.ACCESS,
            descripcion =description or "Solicitud de acceso a mis datos personales"
        )

    def create_rectification_request(self, user_id: int, rectification_data: Dict[str, Any], description: str = None) -> PrivacyRequest:
        """
        Crea una solicitud de rectificación de datos personales (Art. 16 GDPR).
        El titular puede solicitar la corrección de datos inexactos.
        """
        return self._create_request(
            usuario_id =user_id,
            request_type=PrivacyRequestType.RECTIFICATION,
            descripcion =description or "Solicitud de rectificación de mis datos personales",
            rectification_data=json.dumps(rectification_data)
        )

    def create_erasure_request(self, user_id: int, description: str = None) -> PrivacyRequest:
        """
        Crea una solicitud de eliminación/olvido (Art. 17 GDPR).
        El titular puede solicitar la eliminación de sus datos personales.
        """
        return self._create_request(
            usuario_id =user_id,
            request_type=PrivacyRequestType.ERASURE,
            descripcion =description or "Solicitud de eliminación de mis datos personales"
        )

    def _create_request(self, user_id: int, request_type: PrivacyRequestType, 
                       description: str, rectification_data: str = None) -> PrivacyRequest:
        """Método interno para crear solicitudes de privacidad"""
        
        # Verificar que el usuario existe
        usuario = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")

        # Crear la solicitud
        request = PrivacyRequest(
            usuario_id =user_id,
            request_type=request_type,
            descripcion =description,
            rectification_data=rectification_data,
            status=PrivacyRequestStatus.PENDING
        )

        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

        # Log de auditoría
        self.audit_logger.log_privacy_request_created(
            usuario_id =user_id,
            request_id=request.id,
            request_type=request_type.value
        )

        return request

    # === CONSULTAR SOLICITUDES ===

    def get_user_requests(self, user_id: int) -> List[PrivacyRequest]:
        """Obtiene todas las solicitudes de privacidad de un usuario"""
        return self.db.query(PrivacyRequest).filter(
            PrivacyRequest.usuario_id == user_id
        ).order_by(PrivacyRequest.fecha_creacion.desc()).all()

    def get_pending_requests(self) -> List[PrivacyRequest]:
        """Obtiene todas las solicitudes pendientes (para administradores)"""
        return self.db.query(PrivacyRequest).filter(
            PrivacyRequest.status == PrivacyRequestStatus.PENDING
        ).order_by(PrivacyRequest.fecha_creacion.asc()).all()

    def get_request_by_id(self, request_id: int, user_id: int = None) -> Optional[PrivacyRequest]:
        """Obtiene una solicitud específica"""
        consulta = self.db.query(PrivacyRequest).filter(PrivacyRequest.id == request_id)
        
        if user_id:
            # Si se especifica user_id, solo devolver si es su solicitud
            consulta = query.filter(PrivacyRequest.usuario_id == user_id)
            
        return query.first()

    # === PROCESAR SOLICITUDES ===

    def process_access_request(self, request_id: int, processor_id: int) -> Dict[str, Any]:
        """
        Procesa una solicitud de acceso y genera un reporte con todos los datos del usuario.
        """
        request = self.get_request_by_id(request_id)
        if not request or request.request_type != PrivacyRequestType.ACCESS:
            raise ValueError("Solicitud de acceso no encontrada")

        # Actualizar estado
        request.status = PrivacyRequestStatus.IN_PROGRESS
        request.processed_by = processor_id
        request.processed_at = datetime.utcnow()
        self.db.commit()

        # Recopilar todos los datos del usuario
        user_data = self._collect_user_data(request.usuario_id)

        # Marcar como completado
        request.status = PrivacyRequestStatus.COMPLETED
        request.completed_at = datetime.utcnow()
        self.db.commit()

        self.audit_logger.log_privacy_request_processed(
            request_id=request_id,
            processor_id=processor_id,
            action="access_granted"
        )

        return user_data

    def process_rectification_request(self, request_id: int, processor_id: int, approve: bool, reason: str = None) -> bool:
        """
        Procesa una solicitud de rectificación de datos.
        """
        request = self.get_request_by_id(request_id)
        if not request or request.request_type != PrivacyRequestType.RECTIFICATION:
            raise ValueError("Solicitud de rectificación no encontrada")

        request.status = PrivacyRequestStatus.IN_PROGRESS
        request.processed_by = processor_id
        request.processed_at = datetime.utcnow()

        if approve:
            # Aplicar las rectificaciones
            rectification_data = json.loads(request.rectification_data) if request.rectification_data else {}
            self._apply_rectifications(request.usuario_id, rectification_data)
            
            request.status = PrivacyRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            
            self.audit_logger.log_privacy_request_processed(
                request_id=request_id,
                processor_id=processor_id,
                action="rectification_applied"
            )
        else:
            request.status = PrivacyRequestStatus.REJECTED
            request.rejection_reason = reason
            
            self.audit_logger.log_privacy_request_processed(
                request_id=request_id,
                processor_id=processor_id,
                action="rectification_rejected",
                details=reason
            )

        self.db.commit()
        return approve

    def process_erasure_request(self, request_id: int, processor_id: int, approve: bool, reason: str = None) -> bool:
        """
        Procesa una solicitud de eliminación/olvido.
        ATENCIÓN: Esta operación es irreversible.
        """
        request = self.get_request_by_id(request_id)
        if not request or request.request_type != PrivacyRequestType.ERASURE:
            raise ValueError("Solicitud de eliminación no encontrada")

        request.status = PrivacyRequestStatus.IN_PROGRESS
        request.processed_by = processor_id
        request.processed_at = datetime.utcnow()

        if approve:
            # Eliminar todos los datos del usuario
            self._erase_user_data(request.usuario_id)
            
            request.status = PrivacyRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            
            self.audit_logger.log_privacy_request_processed(
                request_id=request_id,
                processor_id=processor_id,
                action="data_erased"
            )
        else:
            request.status = PrivacyRequestStatus.REJECTED
            request.rejection_reason = reason
            
            self.audit_logger.log_privacy_request_processed(
                request_id=request_id,
                processor_id=processor_id,
                action="erasure_rejected",
                details=reason
            )

        self.db.commit()
        return approve

    # === MÉTODOS AUXILIARES ===

    def _collect_user_data(self, user_id: int) -> Dict[str, Any]:
        """Recopila todos los datos personales de un usuario"""
        usuario = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        # Datos básicos del usuario
        user_data = {
            "user_info": {
                "id": user.id,
                "email": user.correo,
                "role": user.rol.value if user.rol else None,
                "created_at": user.fecha_creacion.isoformat() if user.fecha_creacion else None
            },
            "projects": [],
            "files_uploaded": [],
            "vulnerabilities_found": [],
            "analysis_metrics": []
        }

        # Proyectos del usuario
        projects = self.db.query(Project).filter(Project.usuario_id == user_id).all()
        for project in projects:
            project_data = {
                "id": project.id,
                "name": project.nombre,
                "description": project.descripcion,
                "created_at": project.fecha_creacion.isoformat() if project.fecha_creacion else None
            }
            user_data["projects"].append(project_data)

            # Archivos del proyecto
            files = self.db.query(ProjectFile).filter(ProjectFile.proyecto_id == project.id).all()
            for file in files:
                file_data = {
                    "id": file.id,
                    "filename": file.nombre_archivo,
                    "file_path": file.ruta_archivo,
                    "project_id": project.id,
                    "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None
                }
                user_data["files_uploaded"].append(file_data)

            # Vulnerabilidades encontradas
            vulnerabilities = self.db.query(Vulnerability).filter(Vulnerability.proyecto_id == project.id).all()
            for vuln in vulnerabilities:
                vuln_data = {
                    "id": vuln.id,
                    "type": vuln.type,
                    "severity": vuln.severity,
                    "description": vuln.descripcion,
                    "file_path": vuln.ruta_archivo,
                    "line_number": vuln.line_number,
                    "project_id": project.id,
                    "detected_at": vuln.detected_at.isoformat() if vuln.detected_at else None
                }
                user_data["vulnerabilities_found"].append(vuln_data)

            # Métricas de análisis
            metrics = self.db.query(AnalysisMetrics).filter(AnalysisMetrics.proyecto_id == project.id).all()
            for metric in metrics:
                metric_data = {
                    "id": metric.id,
                    "total_files": metric.total_files,
                    "analyzed_files": metric.analyzed_files,
                    "vulnerabilities_found": metric.vulnerabilities_found,
                    "analysis_time": metric.analysis_time,
                    "project_id": project.id,
                    "created_at": metric.fecha_creacion.isoformat() if metric.fecha_creacion else None
                }
                user_data["analysis_metrics"].append(metric_data)

        return user_data

    def _apply_rectifications(self, user_id: int, rectification_data: Dict[str, Any]):
        """Aplica rectificaciones a los datos del usuario"""
        usuario = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        # Actualizar campos permitidos
        if "email" in rectification_data:
            user.correo = rectification_data["email"]

        # Agregar más campos según sea necesario
        # NOTA: No permitir cambio de ID, contrasena(requiere proceso separado), etc.

        self.db.commit()

    def _erase_user_data(self, user_id: int):
        """
        Elimina todos los datos del usuario de forma irreversible.
        CUIDADO: Esta operación elimina TODOS los datos relacionados.
        """
        # Eliminar en orden de dependencias (de hijo a padre)
        
        # 1. Eliminar métricas de análisis
        self.db.query(AnalysisMetrics).filter(
            AnalysisMetrics.proyecto_id.in_(
                self.db.query(Project.id).filter(Project.usuario_id == user_id)
            )
        ).delete(synchronize_session=False)

        # 2. Eliminar vulnerabilidades
        self.db.query(Vulnerability).filter(
            Vulnerability.proyecto_id.in_(
                self.db.query(Project.id).filter(Project.usuario_id == user_id)
            )
        ).delete(synchronize_session=False)

        # 3. Eliminar archivos
        self.db.query(ProjectFile).filter(
            ProjectFile.proyecto_id.in_(
                self.db.query(Project.id).filter(Project.usuario_id == user_id)
            )
        ).delete(synchronize_session=False)

        # 4. Eliminar proyectos
        self.db.query(Project).filter(Project.usuario_id == user_id).delete()

        # 5. Eliminar solicitudes de privacidad (excepto la actual)
        self.db.query(PrivacyRequest).filter(
            PrivacyRequest.usuario_id == user_id,
            PrivacyRequest.status != PrivacyRequestStatus.IN_PROGRESS
        ).delete()

        # 6. Finalmente, eliminar el usuario
        self.db.query(User).filter(User.id == user_id).delete()

        self.db.commit()

    def get_expired_requests(self, days_limit: int = 30) -> List[PrivacyRequest]:
        """Obtiene solicitudes que han excedido el tiempo legal de respuesta"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_limit)
        
        return self.db.query(PrivacyRequest).filter(
            PrivacyRequest.status == PrivacyRequestStatus.PENDING,
            PrivacyRequest.fecha_creacion < cutoff_date
        ).all()
