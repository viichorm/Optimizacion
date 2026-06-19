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
   `py DarioFuentes_VicenteMartinez_VRP.py`

El programa procesará las 3 instancias secuencialmente y emitirá los resultados finales en la salida estándar de la consola.



============================================================
## PARÁMETROS DEL ALGORITMO
============================================================
 
*  Población inicial        : 35.700 individuos aleatorios
*  SLS - individuos         : 35.700 (todos pasan por SLS)
*  SLS - iteraciones c/u    : 100
*  AG - Mu (padres)         : 600
*  AG - Lambda (hijos)      : 1000
*  AG - Generaciones        : 2500
*  AG - Tasa de mutación    : 0.15 (15%)
*  AG - Reinyección periód. : cada 50 gen, reemplaza 20% de Mu
*  AG - Reinyección emerg.  : tras 100 gen sin mejora, 40% de Mu
 
============================================================
## ESTRUCTURA DEL CÓDIGO
============================================================
 
*  BLOQUE 1  - Clase Vehiculo
*  BLOQUE 2  - Clase InstanciaCVRP
*  BLOQUE 3  - Lectura de archivo (formato TSPLIB)
*  BLOQUE 4  - Generación de población inicial aleatoria
*  BLOQUE 5  - Decodificador (permutación → rutas)
*  BLOQUE 6  - Cálculo de distancia total y fitness
*  BLOQUE 7  - Operadores genéticos (OX, Swap, Inserción)
*  BLOQUE 8  - Búsqueda Local Estocástica (SLS)
*  BLOQUE 9  - Ciclo del Algoritmo Genético (mu + lambda)
*  BLOQUE 10 - Impresión de resultados
*  BLOQUE 11 - Main (parámetros y ejecución)
 
============================================================
