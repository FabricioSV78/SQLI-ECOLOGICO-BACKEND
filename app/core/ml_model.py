import torch
from transformers import BertTokenizer, BertForSequenceClassification
import os
import logging

# Configurar logging para el modelo
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Ajusta la ruta de tu modelo exportado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "MODELO_ML")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"🤖 Cargando modelo ML desde: {MODEL_PATH}")
print(f"🖥️  Dispositivo de ejecución: {device}")

tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
model.eval()

print("✅ Modelo ML cargado exitosamente")

def classify_query(query):
    # Preparar entrada
    inputs = tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Realizar predicción
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        label = torch.argmax(probs, dim=1).item()
        confidence = torch.max(probs, dim=1)[0].item()
        
    # Determinar resultado
    resultado = "Posible SQLi" if label == 1 else "Consulta segura"
    
    # Mostrar reporte en consola
    print("\n" + "="*80)
    print("🧠 REPORTE DE PREDICCIÓN DEL MODELO ML")
    print("="*80)
    print(f"📝 Consulta analizada: {query[:100]}{'...' if len(query) > 100 else ''}")
    print(f"🔍 Predicción: {resultado}")
    print(f"📊 Confianza: {confidence:.4f} ({confidence*100:.2f}%)")
    print(f"🏷️  Etiqueta numérica: {label} (0=Segura, 1=Vulnerable)")
    print(f"📈 Probabilidades: Segura={probs[0][0]:.4f}, Vulnerable={probs[0][1]:.4f}")
    print(f"🖥️  Dispositivo: {device}")
    print("="*80)
    
    # Log adicional
    logger.info(f"Predicción: {resultado} | Confianza: {confidence:.4f} | Query: {query[:50]}...")
    
    return resultado

def analyze_code(parsed_data):
    safe = []
    vulnerable = []
    total_queries = 0
    
    print("\n" + "🚀" + "="*78 + "🚀")
    print("🔬 INICIANDO ANÁLISIS COMPLETO DEL CÓDIGO")
    print("🚀" + "="*78 + "🚀")
    
    for archivo in parsed_data:
        archivo_nombre = archivo.get('file', 'archivo_desconocido')
        queries = archivo.get("queries", [])
        total_queries += len(queries)
        
        if queries:
            print(f"\n📁 Analizando archivo: {archivo_nombre}")
            print(f"   📊 Consultas encontradas: {len(queries)}")
        
        for i, consulta in enumerate(queries, 1):
            # Usar la firma completa si existe, si no usar el SQL
            signature = consulta.get("signature") or consulta.get("sql", "")
            
            print(f"\n   🔍 Consulta {i}/{len(queries)}:")
            resultado = classify_query(signature)
            
            if resultado == "Consulta segura":
                safe.append(consulta)
            else:
                vulnerable.append(consulta)
    
    # Resumen final
    print("\n" + "📊" + "="*78 + "📊")
    print("📈 RESUMEN DEL ANÁLISIS COMPLETO")
    print("📊" + "="*78 + "📊")
    print(f"🔢 Total de consultas analizadas: {total_queries}")
    print(f"✅ Consultas seguras: {len(safe)} ({len(safe)/total_queries*100:.1f}%)")
    print(f"⚠️  Consultas vulnerables: {len(vulnerable)} ({len(vulnerable)/total_queries*100:.1f}%)")
    print(f"📁 Archivos procesados: {len(parsed_data)}")
    
    if vulnerable:
        print(f"\n🚨 VULNERABILIDADES DETECTADAS:")
        for i, vuln in enumerate(vulnerable, 1):
            query = vuln.get('signature') or vuln.get('sql', '')
            print(f"   {i}. {query[:80]}{'...' if len(query) > 80 else ''}")
    
    print("📊" + "="*78 + "📊\n")
    
    return {"safe": safe, "vulnerable": vulnerable}


