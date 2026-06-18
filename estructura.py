"""
Modulo de Estructuras de Datos para el problema CVRP.

Contiene las estructuras necesarias para representar una instancia del
problema (formato TSPLIB / CVRPLIB) usando:
    - Matriz de Distancias (Adjacency Matrix)
    - Listas Paralelas de Demandas y Ubicaciones (Node Attributes)
    - Arreglo de Vehiculos (Vehicle Array)
"""

import math
import random
import heapq


# ============================================================
# BLOQUE 1: CLASE VEHICULO
# Representa una unidad de la flota: su capacidad maxima y su
# nodo de deposito, que actua como inicio y fin de su ruta.
# ============================================================
class Vehiculo:
    def __init__(self, Id, Capacidad, NodoDeposito):
        self.Id = Id
        self.Capacidad = Capacidad
        self.NodoDeposito = NodoDeposito
        self.CargaActual = 0
        self.Ruta = [NodoDeposito]

    def __repr__(self):
        return "Vehiculo {} (Capacidad={}, Deposito={})".format(
            self.Id, self.Capacidad, self.NodoDeposito
        )


# ============================================================
# BLOQUE 2: CLASE INSTANCIA CVRP
# Estructura central del problema. Guarda la Matriz de Distancias,
# las Listas Paralelas (Demandas y Coordenadas) y construye el
# Arreglo de Vehiculos de la flota.
# ============================================================
class InstanciaCVRP:
    def __init__(self, Nombre, Capacidad, NodoDeposito, ListaCoordenadas, ListaDemandas):
        self.Nombre = Nombre
        self.Capacidad = Capacidad
        self.NodoDeposito = NodoDeposito
        self.ListaCoordenadas = ListaCoordenadas
        self.ListaDemandas = ListaDemandas
        self.NumNodos = len(ListaCoordenadas)
        self.MatrizDistancias = self.ConstruirMatrizDistancias()
        self.ArregloVehiculos = []

    def ConstruirMatrizDistancias(self):
        # Construye la matriz NxN de distancias euclidianas (EUC_2D) a partir
        # de las coordenadas de cada nodo. Permite obtener en O(1) el costo
        # de viaje entre cualquier par de nodos i, j.
        N = self.NumNodos
        Matriz = [[0.0] * N for _ in range(N)]
        for i in range(N):
            Xi, Yi = self.ListaCoordenadas[i]
            for j in range(N):
                if i != j:
                    Xj, Yj = self.ListaCoordenadas[j]
                    Matriz[i][j] = math.sqrt((Xi - Xj) ** 2 + (Yi - Yj) ** 2)
        return Matriz

    def ObtenerDemandaTotal(self):
        return sum(self.ListaDemandas)

    def ObtenerNumVehiculosMinimo(self):
        # Cota inferior teorica: demanda total dividida por la capacidad,
        # redondeada hacia arriba.
        DemandaTotal = self.ObtenerDemandaTotal()
        return math.ceil(DemandaTotal / self.Capacidad)

    def ObtenerDistanciaMaxima(self):
        # Distancia mas grande presente en la matriz. Sirve como referencia
        # de escala para calibrar el peso de penalizacion del fitness.
        return max(max(Fila) for Fila in self.MatrizDistancias)

    def CrearFlota(self, NumVehiculos):
        # Genera el Arreglo de Vehiculos: todos con la misma capacidad y
        # el mismo nodo de deposito como inicio/fin de ruta.
        self.ArregloVehiculos = []
        IndiceDeposito = self.NodoDeposito - 1
        for k in range(NumVehiculos):
            NuevoVehiculo = Vehiculo(Id=k + 1, Capacidad=self.Capacidad, NodoDeposito=IndiceDeposito)
            self.ArregloVehiculos.append(NuevoVehiculo)
        return self.ArregloVehiculos

    def __repr__(self):
        return "InstanciaCVRP({}, NumNodos={}, Capacidad={})".format(
            self.Nombre, self.NumNodos, self.Capacidad
        )


# ============================================================
# BLOQUE 3: FUNCION DE LECTURA / PARSEO DEL ARCHIVO
# Lee un archivo de instancia en formato TSPLIB/CVRPLIB (como
# 01_facil.txt, 02_medio.txt, 03_dificil.txt) y construye un
# objeto InstanciaCVRP con toda la informacion necesaria.
# ============================================================
def LeerInstanciaCVRP(RutaArchivo):
    with open(RutaArchivo, "r") as Archivo:
        Lineas = [Linea.strip() for Linea in Archivo.readlines()]

    Nombre = ""
    Capacidad = 0
    ListaCoordenadas = []
    ListaDemandas = []
    NodoDeposito = 1
    SeccionActual = None

    for Linea in Lineas:
        if Linea == "" or Linea == "EOF":
            continue

        # --- Encabezados con metadatos de la instancia ---
        if Linea.startswith("NAME"):
            Nombre = Linea.split(":")[1].strip()
            continue
        if Linea.startswith("CAPACITY"):
            Capacidad = int(Linea.split(":")[1].strip())
            continue
        if Linea.startswith(("TYPE", "COMMENT", "DIMENSION", "EDGE_WEIGHT_TYPE")):
            continue

        # --- Marcadores de inicio de seccion ---
        if Linea.startswith("NODE_COORD_SECTION"):
            SeccionActual = "COORDENADAS"
            continue
        if Linea.startswith("DEMAND_SECTION"):
            SeccionActual = "DEMANDAS"
            continue
        if Linea.startswith("DEPOT_SECTION"):
            SeccionActual = "DEPOSITO"
            continue

        # --- Lectura de los datos segun la seccion activa ---
        Valores = Linea.split()
        if SeccionActual == "COORDENADAS":
            ListaCoordenadas.append((float(Valores[1]), float(Valores[2])))
        elif SeccionActual == "DEMANDAS":
            ListaDemandas.append(int(Valores[1]))
        elif SeccionActual == "DEPOSITO":
            ValorDeposito = int(Valores[0])
            if ValorDeposito != -1:
                NodoDeposito = ValorDeposito

    return InstanciaCVRP(Nombre, Capacidad, NodoDeposito, ListaCoordenadas, ListaDemandas)


# ============================================================
# BLOQUE 4: CLASE INDIVIDUO (CROMOSOMA - GIANT TOUR / IES)
# Representacion de permutacion: el cromosoma es una secuencia de
# clientes (sin el deposito) que define el orden de servicio. La
# decodificacion construye las rutas llenando vehiculos en ese
# orden; al excederse la capacidad se abre una nueva ruta, por lo
# que ninguna ruta individual viola jamas la capacidad. La
# restriccion que se vigila y penaliza es el tamano de la flota:
# si se necesitan mas rutas que vehiculos disponibles, se penaliza
# el exceso directamente en el fitness.
# ============================================================
class Individuo:
    def __init__(self, Cromosoma, Instancia, NumVehiculosDisponibles, PesoPenalizacion):
        self.Cromosoma = Cromosoma
        self.Instancia = Instancia
        self.NumVehiculosDisponibles = NumVehiculosDisponibles
        self.PesoPenalizacion = PesoPenalizacion
        self.ListaRutas = []
        self.NumRutasUsadas = 0
        self.ExcesoVehiculos = 0
        self.DistanciaTotal = 0.0
        self.Fitness = 0.0
        self.Decodificar()
        self.EvaluarFitness()

    def Decodificar(self):
        # Asume que ninguna demanda individual supera la capacidad del
        # vehiculo (supuesto estandar en CVRP), por lo que siempre es
        # posible abrir una ruta nueva para cualquier cliente.
        Capacidad = self.Instancia.Capacidad
        ListaDemandas = self.Instancia.ListaDemandas
        IndiceDeposito = self.Instancia.NodoDeposito - 1

        self.ListaRutas = []
        RutaActual = [IndiceDeposito]
        CargaActual = 0

        for Cliente in self.Cromosoma:
            Demanda = ListaDemandas[Cliente]
            if CargaActual + Demanda > Capacidad:
                RutaActual.append(IndiceDeposito)
                self.ListaRutas.append(RutaActual)
                RutaActual = [IndiceDeposito]
                CargaActual = 0
            RutaActual.append(Cliente)
            CargaActual += Demanda

        RutaActual.append(IndiceDeposito)
        self.ListaRutas.append(RutaActual)
        self.NumRutasUsadas = len(self.ListaRutas)

    def EvaluarFitness(self):
        # Funcion objetivo: distancia total recorrida por todas las rutas.
        MatrizDistancias = self.Instancia.MatrizDistancias
        DistanciaTotal = 0.0
        for Ruta in self.ListaRutas:
            for i in range(len(Ruta) - 1):
                DistanciaTotal += MatrizDistancias[Ruta[i]][Ruta[i + 1]]

        # Restriccion a vigilar: flota disponible (numero de vehiculos).
        # Penalizacion lineal ponderada sobre el exceso de rutas usadas.
        self.ExcesoVehiculos = max(0, self.NumRutasUsadas - self.NumVehiculosDisponibles)

        self.DistanciaTotal = DistanciaTotal
        self.Fitness = DistanciaTotal + self.PesoPenalizacion * self.ExcesoVehiculos

    def EsFactible(self):
        return self.ExcesoVehiculos == 0

    def __repr__(self):
        return "Individuo(Fitness={:.2f}, Distancia={:.2f}, RutasUsadas={}, ExcesoVehiculos={})".format(
            self.Fitness, self.DistanciaTotal, self.NumRutasUsadas, self.ExcesoVehiculos
        )


# ============================================================
# BLOQUE 5: HEURISTICA SEMI-ALEATORIA DE VECINO MAS CERCANO
# Construye un giant tour eligiendo, en cada paso, al azar entre
# los "FactorAleatoriedad" clientes no visitados mas cercanos al
# nodo actual (en vez de siempre el mas cercano). Esto entrega
# individuos de buena calidad pero distintos entre si, combinando
# guia heuristica con diversidad aleatoria en la poblacion.
# ============================================================
def ConstruirGiantTourVecinoMasCercano(Instancia, FactorAleatoriedad=3):
    IndiceDeposito = Instancia.NodoDeposito - 1
    ClientesPorVisitar = set(range(Instancia.NumNodos)) - {IndiceDeposito}
    NodoActual = IndiceDeposito
    GiantTour = []

    while ClientesPorVisitar:
        K = min(FactorAleatoriedad, len(ClientesPorVisitar))
        Candidatos = heapq.nsmallest(
            K, ClientesPorVisitar, key=lambda c: Instancia.MatrizDistancias[NodoActual][c]
        )
        SiguienteNodo = random.choice(Candidatos)
        GiantTour.append(SiguienteNodo)
        ClientesPorVisitar.remove(SiguienteNodo)
        NodoActual = SiguienteNodo

    return GiantTour


# ============================================================
# BLOQUE 6: GENERACION DE LA POBLACION INICIAL
# Crea "TamanoPoblacion" individuos, cada uno con un giant tour
# construido mediante la heuristica semi-aleatoria de vecino mas
# cercano, y ya evaluados en fitness.
# ============================================================
def GenerarPoblacionInicial(Instancia, TamanoPoblacion, NumVehiculosDisponibles, PesoPenalizacion, FactorAleatoriedad=3):
    Poblacion = []
    for _ in range(TamanoPoblacion):
        Cromosoma = ConstruirGiantTourVecinoMasCercano(Instancia, FactorAleatoriedad)
        NuevoIndividuo = Individuo(Cromosoma, Instancia, NumVehiculosDisponibles, PesoPenalizacion)
        Poblacion.append(NuevoIndividuo)
    return Poblacion