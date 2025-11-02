"""
Servicio de escaneo de seguridad para SRF3.
Valida archivos ZIP antes del análisis y rechaza/cuarentena binarios.
"""

import zipfile
import os
import shutil
import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityScanner:
    """
    Escáner de seguridad para archivos ZIP - SRF3.
    Detecta y bloquea archivos binarios peligrosos.
    """
    
    # Extensiones de archivos binarios peligrosos
    BINARY_EXTENSIONS = {
        '.exe', '.msi', '.bat', '.cmd', '.com', '.scr', '.pif',
        '.dll', '.so', '.dylib', '.bin', '.deb', '.rpm', '.dmg',
        '.pkg', '.app', '.vbs', '.ps1', '.jar', '.war', '.ear'
    }
    
    # Tipos MIME binarios peligrosos
    DANGEROUS_MIME_TYPES = {
        'application/x-executable',
        'application/x-msdownload', 
        'application/x-dosexec',
        'application/octet-stream'  # Solo si tiene extensión peligrosa
    }
    
    # Archivos permitidos (código fuente)
    ALLOWED_EXTENSIONS = {
        '.java', '.xml', '.properties', '.yml', '.yaml', '.json',
        '.txt', '.md', '.sql', '.css', '.js', '.html', '.jsp',
        '.gradle', '.maven', '.pom'
    }

    def __init__(self, quarantine_dir: str):
        """
        Inicializa el escáner de seguridad.
        
        Args:
            quarantine_dir: Directorio para archivos en cuarentena
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
    def scan_zip_file(self, zip_path: str) -> Dict:
        """
        Escanea un archivo ZIP en busca de binarios peligrosos.
        
        Args:
            zip_path: Ruta del archivo ZIP a escanear
            
        Returns:
            Dict con resultado del escaneo
        """
        result = {
            "safe": True,
            "threats_found": [],
            "total_files": 0,
            "scanned_files": 0,
            "quarantined": False,
            "quarantine_path": None,
            "scan_time": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"🔍 SRF3: Iniciando escaneo de seguridad de {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                result["total_files"] = len(file_list)
                
                for file_name in file_list:
                    result["scanned_files"] += 1
                    
                    # Verificar si es un archivo binario peligroso
                    threat = self._check_file_threat(file_name, zip_ref, file_name)
                    
                    if threat:
                        result["threats_found"].append(threat)
                        result["safe"] = False
                        
                # Si hay amenazas, mover a cuarentena
                if not result["safe"]:
                    quarantine_path = self._quarantine_file(zip_path)
                    result["quarantined"] = True
                    result["quarantine_path"] = str(quarantine_path)
                    
                    logger.warning(f"⚠️ SRF3: Archivo {zip_path} movido a cuarentena")
                    logger.warning(f"📁 Amenazas encontradas: {len(result['threats_found'])}")
                else:
                    logger.info(f"✅ SRF3: Archivo {zip_path} aprobado para procesamiento")
                    
        except Exception as e:
            logger.error(f"❌ SRF3: Error escaneando {zip_path}: {e}")
            result["safe"] = False
            result["threats_found"].append({
                "type": "scan_error",
                "file": zip_path,
                "reason": f"Error de escaneo: {str(e)}"
            })
            
        return result
    
    def _check_file_threat(self, file_name: str, zip_ref: zipfile.ZipFile, zip_entry: str) -> Dict:
        """
        Verifica si un archivo individual es una amenaza.
        
        Args:
            file_name: Nombre del archivo
            zip_ref: Referencia al ZIP
            zip_entry: Entrada del ZIP
            
        Returns:
            Dict con información de amenaza o None si es seguro
        """
        file_path = Path(file_name)
        file_ext = file_path.suffix.lower()
        
        # 1. Verificar extensión binaria peligrosa
        if file_ext in self.BINARY_EXTENSIONS:
            return {
                "type": "binary_executable",
                "file": file_name,
                "extension": file_ext,
                "reason": f"Archivo binario ejecutable detectado: {file_ext}"
            }
        
        # 2. Verificar archivos sin extensión (posibles binarios)
        if not file_ext and not file_name.endswith('/'):
            try:
                # Intentar leer una pequeña muestra del archivo
                with zip_ref.open(zip_entry) as f:
                    sample = f.read(512)  # Leer primeros 512 bytes
                    
                # Verificar si contiene muchos bytes nulos (indicativo de binario)
                null_count = sample.count(b'\x00')
                if null_count > 10:  # Umbral básico
                    return {
                        "type": "suspected_binary",
                        "file": file_name,
                        "reason": "Archivo sin extensión con contenido binario sospechoso"
                    }
            except Exception:
                # Si no se puede leer, considerarlo sospechoso
                return {
                    "type": "unreadable_file",
                    "file": file_name,
                    "reason": "Archivo no legible o corrupto"
                }
        
        # 3. Verificar nombres de archivos sospechosos
        suspicious_names = ['autorun.inf', 'desktop.ini', 'thumbs.db']
        if file_path.name.lower() in suspicious_names:
            return {
                "type": "suspicious_system_file",
                "file": file_name,
                "reason": f"Archivo de sistema sospechoso: {file_path.name}"
            }
        
        # 4. Verificar rutas muy profundas (posible zip bomb básico)
        if len(file_path.parts) > 10:
            return {
                "type": "deep_path",
                "file": file_name,
                "reason": "Ruta de archivo excesivamente profunda (posible zip bomb)"
            }
            
        return None
    
    def _quarantine_file(self, file_path: str) -> Path:
        """
        Mueve un archivo peligroso a cuarentena.
        
        Args:
            file_path: Ruta del archivo a poner en cuarentena
            
        Returns:
            Ruta del archivo en cuarentena
        """
        original_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        quarantine_filename = f"{timestamp}_{original_path.nombre}"
        quarantine_path = self.quarantine_dir / quarantine_filename
        
        # Mover archivo a cuarentena
        shutil.move(file_path, quarantine_path)
        
        # Crear archivo de metadatos
        metadata_path = quarantine_path.with_suffix('.metadata.json')
        metadata = {
            "original_path": str(original_path),
            "quarantine_time": datetime.now().isoformat(),
            "reason": "SRF3: Archivo binario detectado en escaneo de seguridad"
        }
        
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"📁 Archivo movido a cuarentena: {quarantine_path}")
        return quarantine_path
    
    def get_scan_summary(self, scan_result: Dict) -> str:
        """
        Genera un resumen legible del escaneo.
        
        Args:
            scan_result: Resultado del escaneo
            
        Returns:
            Resumen en texto
        """
        summary = []
        summary.append(f"🔍 SRF3 - Escaneo de Seguridad")
        summary.append(f"📊 Archivos escaneados: {scan_result['scanned_files']}/{scan_result['total_files']}")
        
        if scan_result["safe"]:
            summary.append(f"✅ Estado: APROBADO para procesamiento")
        else:
            summary.append(f"⚠️ Estado: RECHAZADO - Amenazas detectadas")
            summary.append(f"🚨 Amenazas encontradas: {len(scan_result['threats_found'])}")
            
            for threat in scan_result['threats_found'][:3]:  # Mostrar solo las primeras 3
                summary.append(f"   • {threat['file']}: {threat['reason']}")
                
            if len(scan_result['threats_found']) > 3:
                summary.append(f"   • ... y {len(scan_result['threats_found']) - 3} más")
        
        if scan_result["quarantined"]:
            summary.append(f"📁 Archivo en cuarentena: {scan_result['quarantine_path']}")
            
        return "\n".join(summary)


def scan_uploaded_zip(zip_path: str, quarantine_dir: str) -> Tuple[bool, Dict]:
    """
    Función de conveniencia para escanear archivos ZIP subidos.
    
    Args:
        zip_path: Ruta del archivo ZIP
        quarantine_dir: Directorio de cuarentena
        
    Returns:
        Tuple (is_safe, scan_result)
    """
    scanner = SecurityScanner(quarantine_dir)
    scan_result = scanner.scan_zip_file(zip_path)
    
    # Log del resultado
    summary = scanner.get_scan_summary(scan_result)
    for line in summary.split('\n'):
        if 'RECHAZADO' in line or 'Amenazas' in line:
            logger.warning(line)
        else:
            logger.info(line)
    
    return scan_result["safe"], scan_result
