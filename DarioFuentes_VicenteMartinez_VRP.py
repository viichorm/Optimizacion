import random
import math
import time


# ============================================================
# BLOQUE 1: CLASE VEHICULO
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
# ============================================================
class InstanciaCVRP:
    def __init__(self, Nombre, Capacidad, NodoDeposito, ListaCoordenadas, ListaDemandas, OptimoConocido=None):
        self.Nombre = Nombre
        self.Capacidad = Capacidad
        self.NodoDeposito = NodoDeposito
        self.ListaCoordenadas = ListaCoordenadas
        self.ListaDemandas = ListaDemandas
        self.NumNodos = len(ListaCoordenadas)
        self.MatrizDistancias = self.ConstruirMatrizDistancias()
        self.ArregloVehiculos = []
        self.OptimoConocido = OptimoConocido

    def ConstruirMatrizDistancias(self):
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
        DemandaTotal = self.ObtenerDemandaTotal()
        return math.ceil(DemandaTotal / self.Capacidad)

    def ObtenerDistanciaMaxima(self):
        return max(max(Fila) for Fila in self.MatrizDistancias)

    def CrearFlota(self, NumVehiculos):
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
# BLOQUE 3: LECTURA DEL ARCHIVO
# ============================================================
def LeerInstanciaCVRP(RutaArchivo):
    with open(RutaArchivo, "r") as Archivo:
        Lineas = [Linea.strip() for Linea in Archivo.readlines()]

    Nombre = ""
    Capacidad = 0
    ListaCoordenadas = []
    ListaDemandas = []
    NodoDeposito = 1
    OptimoConocido = None
    SeccionActual = None

    for Linea in Lineas:
        if Linea == "" or Linea == "EOF":
            continue
        if Linea.startswith("NAME"):
            Nombre = Linea.split(":")[1].strip()
            continue
        if Linea.startswith("CAPACITY"):
            Capacidad = int(Linea.split(":")[1].strip())
            continue
        if Linea.startswith("COMMENT"):
            try:
                OptimoConocido = float(Linea.split(":")[1].strip())
            except (ValueError, IndexError):
                OptimoConocido = None
            continue
        if Linea.startswith(("TYPE", "DIMENSION", "EDGE_WEIGHT_TYPE")):
            continue
        if Linea.startswith("NODE_COORD_SECTION"):
            SeccionActual = "COORDENADAS"
            continue
        if Linea.startswith("DEMAND_SECTION"):
            SeccionActual = "DEMANDAS"
            continue
        if Linea.startswith("DEPOT_SECTION"):
            SeccionActual = "DEPOSITO"
            continue

        Valores = Linea.split()
        if SeccionActual == "COORDENADAS":
            ListaCoordenadas.append((float(Valores[1]), float(Valores[2])))
        elif SeccionActual == "DEMANDAS":
            ListaDemandas.append(int(Valores[1]))
        elif SeccionActual == "DEPOSITO":
            ValorDeposito = int(Valores[0])
            if ValorDeposito != -1:
                NodoDeposito = ValorDeposito

    return InstanciaCVRP(Nombre, Capacidad, NodoDeposito, ListaCoordenadas, ListaDemandas, OptimoConocido)


# ============================================================
# BLOQUE 4: GENERACION DE POBLACION INICIAL
# ============================================================
def GenerarIndividuo(Instancia):
    """
    Genera un individuo: permutacion aleatoria de indices de clientes.
    El deposito NO se incluye en la lista (se agrega implicito en el decodificador).
    """
    IndiceDeposito = Instancia.NodoDeposito - 1
    Clientes = [i for i in range(Instancia.NumNodos) if i != IndiceDeposito]
    random.shuffle(Clientes)
    return Clientes


def GenerarPoblacion(Instancia, TamanoPoblacion=35700):
    """
    Genera TamanoPoblacion individuos aleatorios.
    """
    Poblacion = []
    for _ in range(TamanoPoblacion):
        Poblacion.append(GenerarIndividuo(Instancia))
    return Poblacion


# ============================================================
# BLOQUE 5: DECODIFICADOR
# Lee la permutacion de izquierda a derecha y construye rutas
# de vehiculos respetando las 4 restricciones del CVRP.
# ============================================================
def Decodificar(Individuo, Instancia):
    """
    Convierte un individuo (lista de clientes) en rutas de vehiculos.

    Restricciones implementadas:
    1. Visita unica: la permutacion plana garantiza que cada cliente
       aparece exactamente una vez.
    2. Continuidad de ruta: lectura secuencial i -> i+1.
    3. Limite de capacidad: si agregar el siguiente cliente excede Q,
       se cierra la ruta actual y se abre una nueva.
    4. Vinculacion al deposito: cada ruta empieza y termina en el deposito.

    Retorna:
        ListaRutas: lista de listas con rutas completas incluyendo deposito.
    """
    IndiceDeposito = Instancia.NodoDeposito - 1
    Capacidad      = Instancia.Capacidad
    Demandas       = Instancia.ListaDemandas

    ListaRutas  = []
    RutaActual  = [IndiceDeposito]
    CargaActual = 0

    for NodoCliente in Individuo:
        DemandaCliente = Demandas[NodoCliente]
        if CargaActual + DemandaCliente <= Capacidad:
            RutaActual.append(NodoCliente)
            CargaActual += DemandaCliente
        else:
            RutaActual.append(IndiceDeposito)
            ListaRutas.append(RutaActual)
            RutaActual  = [IndiceDeposito, NodoCliente]
            CargaActual = DemandaCliente

    RutaActual.append(IndiceDeposito)
    ListaRutas.append(RutaActual)
    return ListaRutas


# ============================================================
# BLOQUE 6: DISTANCIA TOTAL Y FITNESS
# ============================================================
def CalcularDistanciaTotal(ListaRutas, Instancia):
    """Suma todas las distancias recorridas en todas las rutas."""
    DistanciaTotal = 0.0
    for Ruta in ListaRutas:
        for k in range(len(Ruta) - 1):
            DistanciaTotal += Instancia.MatrizDistancias[Ruta[k]][Ruta[k + 1]]
    return DistanciaTotal


def CalcularFitness(Individuo, Instancia):
    """Fitness inversamente proporcional a la distancia total."""
    ListaRutas = Decodificar(Individuo, Instancia)
    Distancia  = CalcularDistanciaTotal(ListaRutas, Instancia)
    return 1.0 / Distancia


# ============================================================
# BLOQUE 7: OPERADORES GENETICOS
# ============================================================
def SeleccionElitista(Poblacion, ValoresFitness, Mu):
    """
    Seleccion elitista: retorna los Mu mejores individuos
    ordenados de mayor a menor fitness (menor distancia).
    """
    Emparejados = sorted(
        zip(ValoresFitness, Poblacion),
        key=lambda x: x[0],
        reverse=True
    )
    return [Ind for _, Ind in Emparejados[:Mu]]


def CruceOX(Padre1, Padre2):
    """
    Order Crossover (OX1). Preserva la sub-ruta central y el orden relativo
    de los nodos restantes.
    """
    N = len(Padre1)
    Corte1, Corte2 = sorted(random.sample(range(N), 2))

    def _generar_hijo(P1, P2):
        Hijo = [None] * N
        Hijo[Corte1:Corte2+1] = P1[Corte1:Corte2+1]
        EnSegmento = set(P1[Corte1:Corte2+1])

        IndiceP2 = (Corte2 + 1) % N
        Faltantes = []
        for _ in range(N):
            if P2[IndiceP2] not in EnSegmento:
                Faltantes.append(P2[IndiceP2])
            IndiceP2 = (IndiceP2 + 1) % N

        IndiceHijo = (Corte2 + 1) % N
        for Gen in Faltantes:
            Hijo[IndiceHijo] = Gen
            IndiceHijo = (IndiceHijo + 1) % N

        return Hijo

    return _generar_hijo(Padre1, Padre2), _generar_hijo(Padre2, Padre1)


def MutacionSwap(Individuo, TasaMutacion):
    """
    Mutacion por intercambio (swap): con probabilidad TasaMutacion,
    aplica NumSwaps intercambios aleatorios.
    NumSwaps escala con el tamanio del cromosoma: 3 swaps en instancias
    de mas de 100 clientes para dar pasos exploratorios mas amplios.
    """
    Hijo = Individuo[:]
    if random.random() < TasaMutacion:
        N        = len(Hijo)
        NumSwaps = 3 if N > 100 else 1
        for _ in range(NumSwaps):
            i, j             = random.sample(range(N), 2)
            Hijo[i], Hijo[j] = Hijo[j], Hijo[i]
    return Hijo


def MutacionInsercion(Individuo, TasaMutacion):
    """
    Mutacion por insercion: con probabilidad TasaMutacion, extrae un
    cliente de su posicion y lo reinserta en otra posicion aleatoria.
    Complementa al swap explorando vecindades distintas del espacio.
    """
    Hijo = Individuo[:]
    if random.random() < TasaMutacion:
        N       = len(Hijo)
        Origen  = random.randint(0, N - 1)
        Gen     = Hijo.pop(Origen)
        Destino = random.randint(0, N - 1)
        Hijo.insert(Destino, Gen)
    return Hijo


# ============================================================
# BLOQUE 8: BUSQUEDA LOCAL ESTOCASTICA (SLS)
# Preprocesador que mejora los TopN mejores individuos antes del AG.
#
# Flujo por individuo:
#   1. Seleccionar pseudoaleatoriamente un operador (Swap o Insercion).
#   2. Aplicarlo con tasa 1.0 (exploracion forzada).
#   3. Si el vecino mejora la distancia (first-improvement), aceptarlo.
#   4. Repetir NumIteraciones veces.
#
# Ventaja: mejora la calidad de la poblacion inicial sin el costo
# O(N^2) iterativo de un best-improvement clasico.
# ============================================================
def SLS(Individuo, Instancia, NumIteraciones=100):
    """
    Busqueda Local Estocastica sobre un individuo.

    En cada iteracion elige pseudoaleatoriamente entre MutacionSwap
    o MutacionInsercion, evalua el vecino y acepta si mejora (first-improvement).

    Parametros:
        Individuo      : permutacion de clientes (lista de indices).
        Instancia      : objeto InstanciaCVRP con matriz de distancias.
        NumIteraciones : presupuesto de exploracion por individuo.

    Retorna:
        Mejor individuo encontrado durante la busqueda.
    """
    Actual          = Individuo[:]
    DistanciaActual = CalcularDistanciaTotal(Decodificar(Actual, Instancia), Instancia)
    Operadores      = [MutacionSwap, MutacionInsercion]

    for _ in range(NumIteraciones):
        Operador        = random.choice(Operadores)
        Vecino          = Operador(Actual, 1.0)
        DistanciaVecino = CalcularDistanciaTotal(Decodificar(Vecino, Instancia), Instancia)

        if DistanciaVecino < DistanciaActual:
            Actual          = Vecino
            DistanciaActual = DistanciaVecino

    return Actual


def AplicarSLSPoblacion(Poblacion, Instancia, TopN=500, NumIteraciones=100):
    """
    Aplica SLS a los TopN mejores individuos de la poblacion.

    Flujo:
      1. Evaluar fitness de toda la poblacion y seleccionar los TopN mejores.
      2. Mejorar cada uno con SLS(NumIteraciones).
      3. Retornar los TopN mejorados como nueva poblacion inicial para el AG.

    Parametros:
        Poblacion      : lista de individuos aleatorios (ej: 35700).
        Instancia      : objeto InstanciaCVRP.
        TopN           : cuantos mejores pasan al SLS (default 500).
        NumIteraciones : presupuesto de iteraciones del SLS por individuo.

    Retorna:
        PoblacionMejorada: lista de TopN individuos post-SLS.
    """
    print(f"\n  [SLS] Evaluando {len(Poblacion)} individuos para seleccionar top {TopN}...", end=" ", flush=True)
    T = time.time()

    ValoresFitness = [CalcularFitness(Ind, Instancia) for Ind in Poblacion]
    Emparejados    = sorted(zip(ValoresFitness, Poblacion), key=lambda x: x[0], reverse=True)
    TopPoblacion   = [Ind for _, Ind in Emparejados[:TopN]]
    DistAntesMedia = sum(1.0 / f for f, _ in Emparejados[:TopN]) / TopN
    print(f"listo ({time.time()-T:.2f}s)  dist_media_antes={DistAntesMedia:.2f}")

    print(f"  [SLS] Mejorando {TopN} individuos ({NumIteraciones} iter c/u)...", end=" ", flush=True)
    T = time.time()

    PoblacionMejorada = [SLS(Ind, Instancia, NumIteraciones) for Ind in TopPoblacion]

    DistDespuesMedia = sum(
        CalcularDistanciaTotal(Decodificar(Ind, Instancia), Instancia)
        for Ind in PoblacionMejorada
    ) / TopN
    Mejora = DistAntesMedia - DistDespuesMedia
    print(f"listo ({time.time()-T:.2f}s)  dist_media_despues={DistDespuesMedia:.2f}")
    print(f"  [SLS] Mejora promedio: {Mejora:.2f}  ({Mejora/DistAntesMedia*100:.2f}%)\n")

    return PoblacionMejorada


# ============================================================
# BLOQUE 9: CICLO DEL ALGORITMO GENETICO (mu + lambda)
# ============================================================
def EjecutarAG(Instancia, Poblacion, Mu, Lambda, NumGeneraciones, TasaMutacion,
               FrecuenciaReinyeccion=50, FraccionReinyeccion=0.2,
               GeneracionesSinMejora=100, FraccionReinyeccionEmergencia=0.4):
    """
    Ciclo evolutivo con estrategia (mu + lambda), seleccion elitista,
    reinyeccion periodica de diversidad y reinyeccion de emergencia
    cuando se detecta estancamiento prolongado.

    Flujo por generacion:
        1. Generar Lambda hijos via cruce OX + MutacionSwap + MutacionInsercion.
        2. Pool combinado (mu + lambda) -> seleccionar los Mu mejores.
        3. Reinyeccion periodica cada FrecuenciaReinyeccion generaciones:
           reemplaza el FraccionReinyeccion peor con individuos aleatorios frescos.
        4. Reinyeccion de emergencia si no hay mejora en GeneracionesSinMejora
           generaciones consecutivas: reemplaza FraccionReinyeccionEmergencia de Mu.
        5. Registrar mejor individuo y gap vs optimo conocido.

    NOTA: BusquedaLocalSwap fue removida del ciclo AG porque su costo
    O(N^2) iterativo hace inviable la ejecucion (>20h estimadas en facil).
    La poblacion inicial ya llega mejorada gracias al SLS del bloque 8.

    Retorna:
        (MejorIndividuo, HistorialMejorDistancia, PoblacionFinal)
    """
    OptStr = f"{Instancia.OptimoConocido:.2f}" if Instancia.OptimoConocido else "desconocido"

    print(f"\n  Parametros AG:")
    print(f"    Mu (padres)               : {Mu}")
    print(f"    Lambda (hijos)            : {Lambda}")
    print(f"    Generaciones              : {NumGeneraciones}")
    print(f"    Tasa mutacion             : {TasaMutacion}")
    print(f"    Reinyeccion periodica     : cada {FrecuenciaReinyeccion} gen ({FraccionReinyeccion*100:.0f}% de Mu)")
    print(f"    Reinyeccion emergencia    : tras {GeneracionesSinMejora} gen sin mejora ({FraccionReinyeccionEmergencia*100:.0f}% de Mu)")
    print(f"    Optimo conocido           : {OptStr}")
    print(f"    Poblacion inicial         : {len(Poblacion)} individuos post-SLS\n")

    # Paso 0: evaluar poblacion inicial y reducir a Mu
    print("  Evaluando poblacion post-SLS...", end=" ", flush=True)
    TInicio        = time.time()
    ValoresFitness = [CalcularFitness(Ind, Instancia) for Ind in Poblacion]
    Poblacion      = SeleccionElitista(Poblacion, ValoresFitness, Mu)
    print(f"listo ({time.time() - TInicio:.1f}s)")

    MejorIndividuo     = Poblacion[0]
    MejorDistancia     = CalcularDistanciaTotal(Decodificar(MejorIndividuo, Instancia), Instancia)
    HistorialMejorDist = [MejorDistancia]
    NumReinyecciones   = 0
    NumEmergencias     = 0
    GenSinMejora       = 0

    def _gap_str(Dist):
        if Instancia.OptimoConocido:
            Gap = (Dist - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
            return f"gap={Gap:+.1f}%"
        return ""

    print(f"  Distancia inicial (mejor post-SLS): {MejorDistancia:.2f}  {_gap_str(MejorDistancia)}\n")
    print(f"  {'Gen':>5}  {'Mejor dist':>12}  {'Gap%':>7}  {'Mejora':>9}  {'Reinj':>6}  {'t':>6}")
    print(f"  {'─'*58}")

    # Ciclo generacional
    for Gen in range(1, NumGeneraciones + 1):
        TGen = time.time()

        # Paso 1: generar Lambda hijos con cruce OX + doble mutacion
        Hijos = []
        while len(Hijos) < Lambda:
            Padre1, Padre2 = random.sample(Poblacion, 2)
            Hijo1, Hijo2   = CruceOX(Padre1, Padre2)
            Hijo1 = MutacionSwap(Hijo1, TasaMutacion)
            Hijo2 = MutacionSwap(Hijo2, TasaMutacion)
            Hijo1 = MutacionInsercion(Hijo1, TasaMutacion)
            Hijo2 = MutacionInsercion(Hijo2, TasaMutacion)
            Hijos.extend([Hijo1, Hijo2])

        # Paso 2: pool combinado (mu + lambda) -> seleccion elitista
        PoolCombinado = Poblacion + Hijos
        FitnessPool   = [CalcularFitness(Ind, Instancia) for Ind in PoolCombinado]
        Poblacion     = SeleccionElitista(PoolCombinado, FitnessPool, Mu)

        # Paso 3: reinyeccion periodica de diversidad
        EtiquetaReinj = "  -"
        if Gen % FrecuenciaReinyeccion == 0:
            NumNuevos        = max(1, int(Mu * FraccionReinyeccion))
            Frescos          = [GenerarIndividuo(Instancia) for _ in range(NumNuevos)]
            Poblacion        = Poblacion[:Mu - NumNuevos] + Frescos
            NumReinyecciones += 1
            EtiquetaReinj    = " PER"

        # Paso 4: deteccion de estancamiento y reinyeccion de emergencia
        DistanciaActual = CalcularDistanciaTotal(Decodificar(Poblacion[0], Instancia), Instancia)
        if DistanciaActual < MejorDistancia:
            MejorDistancia = DistanciaActual
            MejorIndividuo = Poblacion[0]
            GenSinMejora   = 0
        else:
            GenSinMejora += 1

        if GenSinMejora >= GeneracionesSinMejora:
            NumNuevos      = max(1, int(Mu * FraccionReinyeccionEmergencia))
            Frescos        = [GenerarIndividuo(Instancia) for _ in range(NumNuevos)]
            Poblacion      = Poblacion[:Mu - NumNuevos] + Frescos
            GenSinMejora   = 0
            NumEmergencias += 1
            EtiquetaReinj  = " EMR"

        Mejora = HistorialMejorDist[-1] - MejorDistancia if HistorialMejorDist else 0
        HistorialMejorDist.append(MejorDistancia)

        if Gen % 10 == 0 or Gen == 1 or Gen == NumGeneraciones:
            GapStr = ""
            if Instancia.OptimoConocido:
                Gap    = (MejorDistancia - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
                GapStr = f"{Gap:+.1f}%"
            Signo = "▼" if Mejora > 0.001 else "="
            print(f"  {Gen:>5}  {MejorDistancia:>12.2f}  {GapStr:>7}  {Signo}{abs(Mejora):>8.2f}  {EtiquetaReinj:>6}  {time.time()-TGen:>5.2f}s")

    print(f"  {'─'*58}")
    print(f"\n  Distancia final optima    : {MejorDistancia:.2f}  {_gap_str(MejorDistancia)}")
    print(f"  Reinyecciones periodicas  : {NumReinyecciones}")
    print(f"  Reinyecciones emergencia  : {NumEmergencias}")

    return MejorIndividuo, HistorialMejorDist, Poblacion


# ============================================================
# BLOQUE 10: IMPRESION DE RESULTADOS
# ============================================================
def ResumirPermutacion(Individuo, MaxMostrar=10):
    """Muestra solo los primeros y ultimos elementos de una permutacion larga."""
    N = len(Individuo)
    if N <= MaxMostrar * 2:
        return str(Individuo)
    Inicio = ", ".join(str(x) for x in Individuo[:MaxMostrar])
    Final  = ", ".join(str(x) for x in Individuo[-MaxMostrar:])
    return f"[{Inicio}, ... ({N - MaxMostrar*2} nodos omitidos) ..., {Final}]"


def ResumirRutas(ListaRutas, Instancia, MaxRutas=5, MaxNodosPorRuta=6):
    """Muestra un subconjunto de rutas con nodos resumidos."""
    IndiceDeposito = Instancia.NodoDeposito - 1
    MostrarHasta   = min(MaxRutas, len(ListaRutas))

    for j in range(MostrarHasta):
        Ruta      = ListaRutas[j]
        CargaRuta = sum(Instancia.ListaDemandas[n] for n in Ruta if n != IndiceDeposito)
        N         = len(Ruta)
        if N <= MaxNodosPorRuta * 2:
            RutaStr = str(Ruta)
        else:
            Inicio  = ", ".join(str(x) for x in Ruta[:MaxNodosPorRuta])
            Final   = ", ".join(str(x) for x in Ruta[-MaxNodosPorRuta:])
            RutaStr = f"[{Inicio}, ...({N - MaxNodosPorRuta*2} nodos)..., {Final}]"
        print(f"      V{j+1:>3}: carga={CargaRuta:>6}  ruta={RutaStr}")

    Omitidas = len(ListaRutas) - MostrarHasta
    if Omitidas > 0:
        print(f"      ... ({Omitidas} rutas mas no mostradas)")


def ImprimirResultadosAG(Instancia, MejorIndividuo, HistorialDist, Top=5, PobFinal=None):
    """Muestra resumen final: gap, historial y top N soluciones unicas."""
    print("\n" + "=" * 60)
    print(f"  RESULTADOS FINALES  -  {Instancia.Nombre}")
    print("=" * 60)

    DistFinal = HistorialDist[-1]
    if Instancia.OptimoConocido:
        Gap = (DistFinal - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
        print(f"\n  Optimo conocido : {Instancia.OptimoConocido:.2f}")
        print(f"  Mejor obtenido  : {DistFinal:.2f}")
        print(f"  Gap             : {Gap:+.2f}%")

    print("\n  Historial de mejor distancia:")
    NumGen = len(HistorialDist) - 1
    Hitos  = sorted(set([0, NumGen // 4, NumGen // 2, 3 * NumGen // 4, NumGen]))
    for h in Hitos:
        GapStr = ""
        if Instancia.OptimoConocido:
            G      = (HistorialDist[h] - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
            GapStr = f"  (gap {G:+.1f}%)"
        print(f"    Gen {h:>4}: {HistorialDist[h]:.2f}{GapStr}")

    Mejora = HistorialDist[0] - HistorialDist[-1]
    print(f"\n  Mejora total: {HistorialDist[0]:.2f} -> {HistorialDist[-1]:.2f}  (reduccion {Mejora:.2f})")

    if PobFinal is not None:
        print(f"\n  {'='*54}")
        print(f"  TOP {Top} SOLUCIONES UNICAS  (poblacion final)")
        print(f"  {'='*54}")

        VistosDist = set()
        UniqFinal  = []
        for Ind in PobFinal:
            Fit  = CalcularFitness(Ind, Instancia)
            Dist = round(1.0 / Fit, 2)
            if Dist not in VistosDist:
                VistosDist.add(Dist)
                UniqFinal.append((Fit, Ind))

        UniqFinal.sort(key=lambda x: x[0], reverse=True)

        if not UniqFinal:
            print("  (sin soluciones unicas en la poblacion final)")
        else:
            for Puesto, (Fit, Ind) in enumerate(UniqFinal[:Top], start=1):
                ListaRutas = Decodificar(Ind, Instancia)
                Distancia  = CalcularDistanciaTotal(ListaRutas, Instancia)
                GapStr     = ""
                if Instancia.OptimoConocido:
                    G      = (Distancia - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
                    GapStr = f"  gap={G:+.2f}%"
                print(f"\n  #{Puesto}")
                print(f"    Fitness    : {Fit:.8f}")
                print(f"    Distancia  : {Distancia:.2f}{GapStr}")
                print(f"    Vehiculos  : {len(ListaRutas)}")
                print(f"    Permutacion: {ResumirPermutacion(Ind, MaxMostrar=8)}")
                print(f"    Rutas (primeras 5 de {len(ListaRutas)}):")
                ResumirRutas(ListaRutas, Instancia, MaxRutas=5, MaxNodosPorRuta=5)

        if len(UniqFinal) < Top:
            print(f"\n  Nota: solo {len(UniqFinal)} soluciones distintas en poblacion final.")

    print("\n" + "=" * 60 + "\n")


def ImprimirPoblacion(Instancia, Poblacion, NumImprimir=3):
    """Imprime una muestra de la poblacion inicial con sus metricas."""
    IndiceDeposito = Instancia.NodoDeposito - 1
    print("=" * 60)
    print(f"  INSTANCIA : {Instancia.Nombre}")
    print(f"  Nodos     : {Instancia.NumNodos}  (incluye deposito)")
    print(f"  Clientes  : {Instancia.NumNodos - 1}")
    print(f"  Capacidad : {Instancia.Capacidad}")
    print(f"  Deposito  : indice {IndiceDeposito} (nodo {Instancia.NodoDeposito})")
    if Instancia.OptimoConocido:
        print(f"  Optimo    : {Instancia.OptimoConocido:.2f}  (del COMMENT del archivo)")
    print("=" * 60)

    MostrarHasta = min(NumImprimir, len(Poblacion))
    print(f"\nMuestra de {MostrarHasta} soluciones iniciales (aleatorias):\n")

    for i in range(MostrarHasta):
        Individuo  = Poblacion[i]
        ListaRutas = Decodificar(Individuo, Instancia)
        Distancia  = CalcularDistanciaTotal(ListaRutas, Instancia)
        Fitness    = CalcularFitness(Individuo, Instancia)

        print(f"  {'─'*54}")
        print(f"  Individuo {i+1}:")
        print(f"    Permutacion : {ResumirPermutacion(Individuo, MaxMostrar=8)}")
        print(f"    Vehiculos   : {len(ListaRutas)}")
        print(f"    Distancia   : {Distancia:.2f}")
        print(f"    Fitness     : {Fitness:.6f}")
        print(f"    Rutas (primeras 3):")
        ResumirRutas(ListaRutas, Instancia, MaxRutas=3, MaxNodosPorRuta=5)

    print()
    print(f"  Total soluciones generadas: {len(Poblacion)}")
    print("=" * 60)


# ============================================================
# BLOQUE 11: MAIN
# ============================================================
if __name__ == "__main__":
    random.seed(42)

    Archivos = [
        "01_facil.txt",
        "02_medio.txt",
        "03_dificil.txt"
    ]

    # ── Parametros generales ──────────────────────────────────────
    TAMANO_POBLACION_INICIAL  = 35700  # individuos aleatorios generados al inicio
    MU                        = 600    # padres que sobreviven por generacion en el AG
    LAMBDA                    = 1000    # hijos generados por generacion en el AG
    NUM_GENERACIONES          = 2500   # iteraciones del ciclo evolutivo
    TASA_MUTACION             = 0.15   # probabilidad de mutar (swap + insercion)
    FREQ_REINYECCION          = 50     # reinyeccion periodica cada N generaciones
    FRAC_REINYECCION          = 0.20   # fraccion de Mu reemplazada periodicamente
    GEN_SIN_MEJORA            = 100    # generaciones sin mejora -> reinyeccion emergencia
    FRAC_REINY_EMERGENCIA     = 0.40   # fraccion de Mu reemplazada en emergencia

    # ── Parametros SLS ────────────────────────────────────────────
    SLS_TOP_N                 = 35700    # mejores individuos que pasan al SLS
    SLS_ITERACIONES           = 100    # iteraciones de exploracion por individuo

    for RutaArchivo in Archivos:
        print(f"\n{'#'*60}")
        print(f"  Cargando {RutaArchivo}...")
        print(f"{'#'*60}")

        Instancia = LeerInstanciaCVRP(RutaArchivo)

        # 1. Generar poblacion inicial grande (aleatoria)
        print(f"\n  Generando {TAMANO_POBLACION_INICIAL} individuos aleatorios...")
        Poblacion = GenerarPoblacion(Instancia, TAMANO_POBLACION_INICIAL)

        # 2. Mostrar muestra de la poblacion inicial
        ImprimirPoblacion(Instancia, Poblacion, NumImprimir=3)

        # 3. SLS: seleccionar los SLS_TOP_N mejores y mejorarlos
        #    antes de pasarlos al AG como poblacion inicial de calidad
        print(f"\n  Iniciando SLS (top {SLS_TOP_N}, {SLS_ITERACIONES} iter c/u)...")
        Poblacion = AplicarSLSPoblacion(
            Poblacion,
            Instancia,
            TopN           = SLS_TOP_N,
            NumIteraciones = SLS_ITERACIONES
        )

        # 4. Ejecutar AG con la poblacion mejorada por SLS
        print(f"  Iniciando Algoritmo Genetico ({len(Poblacion)} individuos post-SLS)...")
        MejorIndividuo, Historial, PobFinal = EjecutarAG(
            Instancia,
            Poblacion,
            Mu                            = MU,
            Lambda                        = LAMBDA,
            NumGeneraciones               = NUM_GENERACIONES,
            TasaMutacion                  = TASA_MUTACION,
            FrecuenciaReinyeccion         = FREQ_REINYECCION,
            FraccionReinyeccion           = FRAC_REINYECCION,
            GeneracionesSinMejora         = GEN_SIN_MEJORA,
            FraccionReinyeccionEmergencia = FRAC_REINY_EMERGENCIA
        )

        # 5. Mostrar resultados finales
        ImprimirResultadosAG(
            Instancia,
            MejorIndividuo,
            Historial,
            Top      = 5,
            PobFinal = PobFinal
        )