"""
Codigo general de ejecucion.

Carga las instancias CVRP (01_facil.txt, 02_medio.txt, 03_dificil.txt)
usando las estructuras definidas en estructura.py, y muestra un resumen
de cada una junto con la flota minima de vehiculos requerida.
"""

import os
from estructura import LeerInstanciaCVRP, GenerarPoblacionInicial


# ============================================================
# BLOQUE 1: CONFIGURACION DE RUTAS DE LAS INSTANCIAS
# ============================================================
CarpetaInstancias = "F:\Optimizacion"
ArchivosInstancias = ["01_facil.txt", "02_medio.txt", "03_dificil.txt"]


# ============================================================
# BLOQUE 2: CARGA Y RESUMEN DE CADA INSTANCIA DISPONIBLE
# Por cada archivo encontrado, se construye la InstanciaCVRP
# (matriz de distancias, listas de demandas/coordenadas) y se
# crea el Arreglo de Vehiculos minimo necesario para cubrir la
# demanda total.
# ============================================================
ListaInstancias = []

for NombreArchivo in ArchivosInstancias:
    RutaCompleta = os.path.join(CarpetaInstancias, NombreArchivo)

    if not os.path.exists(RutaCompleta):
        print("Aviso: no se encontro el archivo {}, se omite.".format(NombreArchivo))
        continue

    Instancia = LeerInstanciaCVRP(RutaCompleta)
    NumVehiculosMinimo = Instancia.ObtenerNumVehiculosMinimo()
    Instancia.CrearFlota(NumVehiculosMinimo)
    ListaInstancias.append(Instancia)

    print("=" * 50)
    print("Instancia: {}".format(Instancia.Nombre))
    print("Numero de nodos (deposito + clientes): {}".format(Instancia.NumNodos))
    print("Capacidad por vehiculo: {}".format(Instancia.Capacidad))
    print("Demanda total: {}".format(Instancia.ObtenerDemandaTotal()))
    print("Vehiculos minimos requeridos (cota inferior): {}".format(NumVehiculosMinimo))
    print("Nodo deposito: {}".format(Instancia.NodoDeposito))


# ============================================================
# BLOQUE 3: ALGORITMO GENETICO - POBLACION INICIAL Y FITNESS
# Para cada instancia se fija la flota disponible (igual a la cota
# minima de vehiculos) y se calibra el peso de penalizacion en
# funcion de la escala de distancias de la instancia. Luego se
# genera la poblacion inicial (giant tour semi-aleatorio con
# vecino mas cercano) y se reporta su fitness.
# ============================================================
TamanoPoblacion = 200
FactorAleatoriedadNN = 3

for Instancia in ListaInstancias:
    NumVehiculosDisponibles = len(Instancia.ArregloVehiculos)
    PesoPenalizacion = 100 * Instancia.ObtenerDistanciaMaxima()

    Poblacion = GenerarPoblacionInicial(
        Instancia, TamanoPoblacion, NumVehiculosDisponibles, PesoPenalizacion, FactorAleatoriedadNN
    )

    ListaFitness = [Ind.Fitness for Ind in Poblacion]
    ListaDistancias = [Ind.DistanciaTotal for Ind in Poblacion]
    NumFactibles = sum(1 for Ind in Poblacion if Ind.EsFactible())
    MejorIndividuo = min(Poblacion, key=lambda Ind: Ind.Fitness)

    print("=" * 50)
    print("Algoritmo Genetico - Instancia: {}".format(Instancia.Nombre))
    print("Tamano de poblacion: {}".format(TamanoPoblacion))
    print("Vehiculos disponibles (flota fija): {}".format(NumVehiculosDisponibles))
    print("Peso de penalizacion: {:.2f}".format(PesoPenalizacion))
    print("Individuos factibles (sin exceso de flota): {}/{}".format(NumFactibles, TamanoPoblacion))
    print("Mejor fitness inicial: {:.2f} (distancia={:.2f}, rutas usadas={})".format(
        MejorIndividuo.Fitness, MejorIndividuo.DistanciaTotal, MejorIndividuo.NumRutasUsadas
    ))
    print("Fitness promedio inicial: {:.2f}".format(sum(ListaFitness) / len(ListaFitness)))
    print("Distancia promedio inicial: {:.2f}".format(sum(ListaDistancias) / len(ListaDistancias)))


# ============================================================
# BLOQUE 4: VERIFICACION RAPIDA DE LA MATRIZ DE DISTANCIAS
# Se imprime la distancia entre el deposito y el primer cliente
# de la primera instancia cargada, a modo de prueba rapida de
# que la matriz se construyo correctamente.
# ============================================================
if ListaInstancias:
    PrimeraInstancia = ListaInstancias[0]
    DistanciaEjemplo = PrimeraInstancia.MatrizDistancias[0][1]
    print("\nEjemplo: distancia entre el deposito y el nodo 2 en '{}': {:.2f}".format(
        PrimeraInstancia.Nombre, DistanciaEjemplo
    ))