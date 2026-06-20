# Tarea 2 Metaheurísticas - Algoritmo Genético para CVRP

## Integrantes
- Vicente Martínez | RUT: 21.839.146-K
- Dario Fuentes | RUT: 21.862.824-9 

## Requisitos del Sistema
- Python 3.x
- Librerías estándar: `math`, `random`, `time`. No requiere dependencias externas.

## Estructura del Directorio
El código fuente y los archivos de texto de las instancias deben residir exactamente en la misma carpeta.
- `DarioFuentes_VicenteMartinez_VRP.py`
- `01_facil.txt`
- `02_medio.txt`
- `03_dificil.txt`

## Instrucciones de Ejecución
1. Abrir la terminal o consola de comandos.
2. Navegar al directorio que contiene los archivos.
3. Ejecutar el script mediante el comando:
   `py DarioFuentes_VicenteMartinez_VRP.py` o sino `python DarioFuentes_VicenteMartinez_VRP.py`

El programa procesará las 3 instancias secuencialmente y emitirá los resultados finales en la salida estándar de la consola.
============================================================
## PARÁMETROS DEL ALGORITMO
============================================================

*  Presupuesto por ejecución : 35.700 evaluaciones (tope duro)
*  Población inicial         : 300 individuos aleatorios
*  SLS - individuos (TopN)   : 40 (los 40 mejores pasan por SLS)
*  SLS - iteraciones c/u     : 25
*  AG - Mu (padres)          : 25
*  AG - Lambda (hijos)       : 70
*  AG - Generaciones (tope)  : 100.000 (el presupuesto corta antes)
*  AG - Tasa de mutación     : 0.15 (15%)
*  AG - Reinyección periód.  : cada 40 gen, reemplaza 20% de Mu
*  AG - Reinyección emerg.   : tras 50 gen sin mejora, 40% de Mu
*  Repeticiones por instancia: 10 ejecuciones (semillas distintas)

============================================================
## ESTRUCTURA DEL CÓDIGO
============================================================

*  Control de presupuesto    - Contador global de evaluaciones (corte en 35.700)
*  Clase Vehiculo            - Representación de un vehículo
*  Clase InstanciaCVRP       - Lectura y parseo (formato TSPLIB)
*  Generación de población   - Individuos iniciales aleatorios
*  Decodificador             - Permutación → rutas (respeta capacidad)
*  Distancia y fitness       - Función objetivo y evaluación
*  Operadores genéticos      - Cruce OX, mutación Swap e Inserción
*  Búsqueda Local Estocástica (SLS) - Mejora la población inicial
*  Ciclo del Algoritmo Genético (mu + lambda) - Evolución con reinyecciones
*  Impresión de resultados   - Mejor solución por instancia
*  Experimento multi-semilla - 10 corridas, guarda CSV
*  Main                      - Parámetros y ejecución

============================================================
