## Descripcion general

Este proyecto resuelve el problema de Ruteo de Vehiculos con Capacidad
(CVRP) utilizando un Algoritmo Genetico (AG) con representacion de tipo
Giant Tour (Esquema Entero / IES).


## Estructura del codigo

- `estructura.py`: Estructuras de datos del problema y del AG
  (InstanciaCVRP, Vehiculo, Individuo, generacion de poblacion inicial, etc.)
- `codigo.py`: Script principal de ejecucion (carga las instancias,
  construye la poblacion inicial, evalua fitness, y --proximamente--
  ejecuta el bucle evolutivo completo)
- `01_facil.txt`, `02_medio.txt`, `03_dificil.txt`: instancias del problema
  (formato TSPLIB/CVRPLIB)


## Instrucciones de ejecucion

Requisitos: Python 3 (no requiere librerias externas, solo modulos
estandar: `math`, `random`, `heapq`, `os`).

1. Colocar los archivos `01_facil.txt`, `02_medio.txt` y `03_dificil.txt`
   en la misma carpeta que `codigo.py` y `estructura.py` (o ajustar la
   variable `CarpetaInstancias` al inicio de `codigo.py` con la ruta
   correspondiente).

2. Ejecutar desde la terminal:

   ```
   python3 codigo.py
   ```

3. El script imprime, para cada instancia:
   - Resumen de la instancia (nodos, capacidad, demanda total, vehiculos
     minimos requeridos)
   - Estadisticas de la poblacion inicial del AG (mejor fitness, fitness
     promedio, individuos factibles, etc.)


## Referencias / inspiracion metodologica

El esquema de codificacion (Giant Tour / IES), la estrategia de manejo de
restricciones mediante penalizacion, y algunos parametros del AG fueron
inspirados en el siguiente trabajo academico (no se reutilizo codigo de
este trabajo, solo conceptos metodologicos):

> Lima, S. J. A., Araujo, S. A. (2020). "Genetic Algorithm Applied to the
> Capacitated Vehicle Routing Problem: An Analysis of the Influence of
> Different Encoding Schemes on the Population Behavior". American
> Scientific Research Journal for Engineering, Technology, and Sciences
> (ASRJETS), 73(1), 96-110.


## Estado del proyecto (checklist)

### Listo

**Estructuras de datos (base)**
- [x] Parser de instancias CVRP (formato TSPLIB) - `LeerInstanciaCVRP`
- [x] Matriz de distancias (adjacency matrix)
- [x] Listas paralelas de demandas y coordenadas
- [x] Arreglo de vehiculos (`Vehiculo`, `CrearFlota`)

**Algoritmo Genetico - Representacion y Poblacion**
- [x] Representacion: Giant Tour (Esquema Entero / IES)
- [x] Decodificacion de cromosoma a rutas reales (llenado por capacidad)
- [x] Generacion de poblacion inicial (semi-aleatoria con vecino mas cercano)
- [x] Funcion de fitness con penalizacion (exceso de vehiculos sobre flota disponible)
- [x] Validado y probado con las 3 instancias (Facil, Medio, Dificil)

### Falta

**Bucle evolutivo (el AG propiamente dicho) - PENDIENTE: [NOMBRE RESPONSABLE]**
- [ ] Operador de seleccion (ruleta)
- [ ] Operador de cruce - Order Crossover (OX), apto para permutaciones
- [ ] Operador de mutacion - swap mutation
- [ ] Elitismo
- [ ] Bucle de generaciones con criterio de parada
- [ ] Registro del historial de fitness por generacion (para graficar convergencia)

**Experimentacion (requerido por la Tarea 2)**
- [ ] Definir y declarar el presupuesto computacional (tiempo limite o N de evaluaciones)
- [ ] Capturar el valor de `COMMENT` del archivo (optimo/mejor conocido) para calcular el GAP
- [ ] Ejecutar 10 corridas por instancia, calcular media y desviacion estandar
- [ ] Generar graficos (ej. boxplots) de los resultados

**Entregables de codigo (requisitos formales de la tarea)**
- [ ] Completar nombre y RUT de todos los integrantes en este README
- [ ] Revisar referencia al paper en la seccion de implementacion del informe
