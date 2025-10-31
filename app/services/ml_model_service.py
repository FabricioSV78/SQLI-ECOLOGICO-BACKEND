def analizar_consultas_con_modelo(resultados, modelo):
	"""
	Extrae las firmas completas (o consultas SQL) de los resultados y las pasa al modelo de ML.
	Retorna una lista con el archivo, la firma/consulta y el resultado del modelo.
	"""
	analisis = []
	for archivo in resultados:
		for consulta in archivo.get('queries', []):
			signature = consulta.get('signature') or consulta.get('sql', '')
			resultado = modelo.predecir(signature) 
			analisis.append({
				'project': archivo.get('project'),
				'file': archivo.get('file'),
				'signature': signature,
				'resultado_modelo': resultado
			})
	return analisis
