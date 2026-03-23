import os
from datetime import datetime, timedelta

# FUNCIÓN: Construye la ruta buscando siempre dentro de la carpeta 'src'
def obtener_ruta(nombre_archivo):
    if not nombre_archivo.endswith(".txt"):
        nombre_archivo += ".txt"
    
    return os.path.join(os.path.dirname(__file__), "src", nombre_archivo)

# FUNCIÓN: Procesa los rangos horarios y genera bloques de 1 hora
def expandir_bloques_horarios(texto_rangos):
    lista_bloques = []
    if not texto_rangos:
        return lista_bloques
        
    for segmento in texto_rangos.split(","):
        try:
            segmento = segmento.strip()
            if not segmento: continue
            
            # Separa día y rango (Ej: "Lunes" y "8:00 - 12:00")
            partes = segmento.split(" ", 1)
            if len(partes) < 2: continue
            
            dia = partes[0].strip()
            # Limpia espacios extra para procesar "8:00-12:00"
            rango_limpio = partes[1].replace(" ", "") 
            
            inicio_txt, fin_txt = rango_limpio.split("-")
            
            # Rellena con cero si falta (8:00 -> 08:00)
            def normalizar(t):
                return t.zfill(5) if ":" in t else t

            hora_inicio = datetime.strptime(normalizar(inicio_txt.strip()), "%H:%M")
            hora_fin = datetime.strptime(normalizar(fin_txt.strip()), "%H:%M")
            
            while hora_inicio < hora_fin:
                lista_bloques.append(dia + " " + hora_inicio.strftime("%H:%M"))
                hora_inicio += timedelta(hours=1)
        except Exception as error:
            print("Error en formato de horario:", segmento, "->", error)
    return lista_bloques

# FUNCIÓN: Carga los datos desde la carpeta src
def cargar_datos_universidad():
    docentes, materias, aulas = [], [], []

    # Carga de Docentes
    ruta_d = obtener_ruta("docentes")
    if os.path.exists(ruta_d):
        with open(ruta_d, "r", encoding="utf-8") as f:
            for linea in f:
                p = linea.strip().split(";")
                if len(p) == 2:
                    docentes.append({
                        "nombre": p[0].strip(),
                        "disponibilidad": expandir_bloques_horarios(p[1]),
                        "carga_total": 0
                    })
    else:
        print("⚠️ No se encontró el archivo:", ruta_d)

    # Carga de Materias
    ruta_m = obtener_ruta("materias")
    if os.path.exists(ruta_m):
        with open(ruta_m, "r", encoding="utf-8") as f:
            for linea in f:
                p = linea.strip().split(";")
                if len(p) == 3:
                    materias.append({
                        "nombre": p[0].strip(),
                        "docente_asig": p[1].strip(),
                        "horas_sem": int(p[2].strip())
                    })
        materias.sort(key=lambda x: x["horas_sem"], reverse=True)

    # Carga de Aulas
    ruta_a = obtener_ruta("aula")
    if os.path.exists(ruta_a):
        with open(ruta_a, "r", encoding="utf-8") as f:
            for linea in f:
                p = linea.strip().split(";")
                if len(p) == 2:
                    aulas.append({
                        "nombre": p[0].strip(),
                        "disponibilidad": expandir_bloques_horarios(p[1]),
                        "ocupacion": []
                    })
    
    return docentes, materias, aulas

# FUNCIÓN: Genera la asignación evitando traslapes
def generar_horario_final(lista_docentes, lista_materias, lista_aulas):
    horario_resultado = []
    
    for mat in lista_materias:
        nombre_m = mat["nombre"]
        nombre_d = mat["docente_asig"]
        horas_pendientes = mat["horas_sem"]
        
        docente_obj = next((d for d in lista_docentes if d["nombre"] == nombre_d), None)
        
        if not docente_obj:
            print("⚠️ No se encontró al docente:", nombre_d)
            continue

        for bloque in docente_obj["disponibilidad"][:]:
            if horas_pendientes <= 0: break
            
            # Busca un aula libre para ese bloque
            aula_libre = next((au for au in lista_aulas if bloque in au["disponibilidad"] and bloque not in au["ocupacion"]), None)
            
            if aula_libre:
                horario_resultado.append({
                    "tiempo": bloque, "materia": nombre_m, "docente": nombre_d, "aula": aula_libre["nombre"]
                })
                aula_libre["ocupacion"].append(bloque)
                docente_obj["disponibilidad"].remove(bloque)
                docente_obj["carga_total"] += 1
                horas_pendientes -= 1
                print("Asignado:", nombre_m, "-", bloque, "-", aula_libre["nombre"])
        
        if horas_pendientes > 0:
            print("❌ Alerta:", nombre_m, "quedó incompleta por", horas_pendientes, "horas.")

    return horario_resultado

# FUNCIÓN: Guarda el reporte con el formato de tabla solicitado
def guardar_reporte(horario, docentes, nombre_archivo="horario.txt"):
    # El resultado también se guarda en la carpeta src
    ruta_s = obtener_ruta(nombre_archivo)
    c1, c2, c3, c4 = 20, 30, 30, 15
    horario.sort(key=lambda x: x["tiempo"])

    with open(ruta_s, "w", encoding="utf-8") as f:
        f.write("Día y Hora".ljust(c1) + "Materia".ljust(c2) + "Docente".ljust(c3) + "Aula".ljust(c4) + "\n")
        f.write("=" * (c1 + c2 + c3 + c4) + "\n")
        
        for h in horario:
            f.write(h["tiempo"].ljust(c1) + h["materia"].ljust(c2) + h["docente"].ljust(c3) + h["aula"].ljust(c4) + "\n")
        
        # Resumen de carga al final del archivo
        f.write("\n\n" + "-" * 40 + "\n")
        f.write("RESUMEN DE CARGA HORARIA DOCENTE\n")
        f.write("-" * 40 + "\n")
        for d in docentes:
            f.write(d["nombre"].ljust(30) + ": " + str(d["carga_total"]) + " horas asignadas.\n")

    print("\n✅ Reporte guardado con éxito en:", ruta_s)

# INICIO DEL PROGRAMA
if __name__ == "__main__":
    print("--- GESTOR DE COORDINACIÓN UNIVERSITARIA ---\n")
    
    docs, mats, aus = cargar_datos_universidad()
    
    if docs and mats and aus:
        malla_final = generar_horario_final(docs, mats, aus)
        guardar_reporte(malla_final, docs)
        
        # Resumen en consola para el usuario
        print("\nRESUMEN FINAL DE CARGA EN CONSOLA:")
        print("-" * 30)
        for d in docs:
            print(d["nombre"], "->", d["carga_total"], "horas.")
        print("-" * 30)
    else:
        print("Error: No se pudieron cargar los datos. Verifica que los archivos estén en 'src'.")