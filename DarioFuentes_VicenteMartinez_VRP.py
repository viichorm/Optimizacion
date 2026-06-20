import random
import math
import time


# Bloque inicio, definir cantidad soluciones (la idea es que todos evaluemos las mismas soluciones)
LIMITE_EVALUACIONES = 35700
EVALUACIONES        = 0

# Si alcanza las soluciones
class PresupuestoAgotado(Exception):
    pass

#Reiniciar el contador al terminar una iteracion
def ReiniciarPresupuesto(Limite=35700):
    global EVALUACIONES, LIMITE_EVALUACIONES
    EVALUACIONES        = 0
    LIMITE_EVALUACIONES = Limite


# 
def EvaluarSolucion(Individuo, Instancia):
    global EVALUACIONES
    ListaRutas = Decodificar(Individuo, Instancia)
    Distancia  = CalcularDistanciaTotal(ListaRutas, Instancia)
    EVALUACIONES += 1
    if EVALUACIONES >= LIMITE_EVALUACIONES:
        raise PresupuestoAgotado()
    return Distancia


# Bloque de la definicion del vehiculoS
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


# Bloque para parsear el CVRP respectivamente
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
    
    # Calculo de las distancias y asignarlas en una matriz
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

    #funciones auxiliares
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


# Funcion generica para leer el archivo desde el directorio.
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


# Generacion de los individuos o soluciones de manera aleatoria.
def GenerarIndividuo(Instancia):
    IndiceDeposito = Instancia.NodoDeposito - 1
    Clientes = [i for i in range(Instancia.NumNodos) if i != IndiceDeposito]
    random.shuffle(Clientes)
    return Clientes

# Generar la poblacion de los individuos aleatoreamente 
def GenerarPoblacion(Instancia, TamanoPoblacion=35700):
    Poblacion = []
    for _ in range(TamanoPoblacion):
        Poblacion.append(GenerarIndividuo(Instancia))
    return Poblacion


# A cada solucion, (que son la lista de los nodoss), asignarle los vehiculos, respectando las restricciones del problema 
def Decodificar(Individuo, Instancia):
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


# Funcion para calcular la distancia total de todos los vehiculos de una solucion ya decodificada. 
def CalcularDistanciaTotal(ListaRutas, Instancia):
    DistanciaTotal = 0.0
    for Ruta in ListaRutas:
        for k in range(len(Ruta) - 1):
            DistanciaTotal += Instancia.MatrizDistancias[Ruta[k]][Ruta[k + 1]]
    return DistanciaTotal

# Funcion para calcular el fitness de cada solucion, siendo inversamente propocional a la distancia total
def CalcularFitness(Individuo, Instancia):
    Distancia = EvaluarSolucion(Individuo, Instancia)
    return 1.0 / Distancia

# Funcion auxiliar para imprimir
def DistanciaSinContar(Individuo, Instancia):
    return CalcularDistanciaTotal(Decodificar(Individuo, Instancia), Instancia)


# Operadores utilizados dentro del AG, siendo elitismo, el cruceOX y dos tipos de mutacion (swap e insercion)
def SeleccionElitista(Poblacion, ValoresFitness, Mu):
    Emparejados = sorted(
        zip(ValoresFitness, Poblacion),
        key=lambda x: x[0],
        reverse=True
    )
    return [Ind for _, Ind in Emparejados[:Mu]]


def CruceOX(Padre1, Padre2):
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
    Hijo = Individuo[:]
    if random.random() < TasaMutacion:
        N        = len(Hijo)
        NumSwaps = 3 if N > 100 else 1
        for _ in range(NumSwaps):
            i, j             = random.sample(range(N), 2)
            Hijo[i], Hijo[j] = Hijo[j], Hijo[i]
    return Hijo


def MutacionInsercion(Individuo, TasaMutacion):
    Hijo = Individuo[:]
    if random.random() < TasaMutacion:
        N       = len(Hijo)
        Origen  = random.randint(0, N - 1)
        Gen     = Hijo.pop(Origen)
        Destino = random.randint(0, N - 1)
        Hijo.insert(Destino, Gen)
    return Hijo


#Busqueda Local Estocastica, lo que hace es:
# - Tomar un individuo y generar un vecino aplicando un operador de mutacion (swap o insercion).
# - Evaluar el vecino utilizando EvaluarSolucion (lo que consume presupuesto).
# - Este caso es estocastico, porque se lselecciona al azar practicamente
def SLS(Individuo, Instancia, NumIteraciones=100):
    Actual          = Individuo[:]
    DistanciaActual = EvaluarSolucion(Actual, Instancia)   
    Operadores      = [MutacionSwap, MutacionInsercion]

    for _ in range(NumIteraciones):
        Operador        = random.choice(Operadores)
        Vecino          = Operador(Actual, 1.0)
        DistanciaVecino = EvaluarSolucion(Vecino, Instancia)  

        if DistanciaVecino < DistanciaActual:
            Actual          = Vecino
            DistanciaActual = DistanciaVecino

    return Actual

# Funcion que aplica el SLS anterior explicado, primero evaluando toda la poblacion incial y selecciona las TopN mejores soluciones
# La idea de esta implementacion, es que el AG no empiece con soluciones full aleatorias, sino que mas bien comience con algo mas interesante.
def AplicarSLSPoblacion(Poblacion, Instancia, TopN=500, NumIteraciones=100):
    print(f"\n  [SLS] Evaluando poblacion para seleccionar top {TopN}...", end=" ", flush=True)
    T = time.time()

    ValoresFitness = []
    PoblacionEval  = []
    PresupuestoOK  = True
    try:
        for Ind in Poblacion:
            ValoresFitness.append(CalcularFitness(Ind, Instancia))
            PoblacionEval.append(Ind)
    except PresupuestoAgotado:
        PresupuestoOK = False
        print(f"\n  [SLS] Presupuesto agotado durante evaluacion inicial "
              f"({EVALUACIONES}/{LIMITE_EVALUACIONES}).")
    Emparejados  = sorted(zip(ValoresFitness, PoblacionEval), key=lambda x: x[0], reverse=True)
    TopPoblacion = [Ind for _, Ind in Emparejados[:TopN]]

    if not PresupuestoOK:
        return TopPoblacion if TopPoblacion else Poblacion

    DistAntesMedia = (sum(1.0 / f for f, _ in Emparejados[:TopN]) / len(Emparejados[:TopN])
                      if Emparejados else 0.0)
    print(f"listo ({time.time()-T:.2f}s)  dist_media_antes={DistAntesMedia:.2f}")

    print(f"  [SLS] Mejorando hasta {len(TopPoblacion)} individuos ({NumIteraciones} iter c/u)...",
          end=" ", flush=True)
    T = time.time()

    PoblacionMejorada = []
    try:
        for Ind in TopPoblacion:
            PoblacionMejorada.append(SLS(Ind, Instancia, NumIteraciones))
    except PresupuestoAgotado:
        Restantes = TopPoblacion[len(PoblacionMejorada):]
        PoblacionMejorada.extend(Restantes)
        print(f"\n  [SLS] Presupuesto agotado durante SLS "
              f"({EVALUACIONES}/{LIMITE_EVALUACIONES}).")
        return PoblacionMejorada

    DistDespuesMedia = (sum(DistanciaSinContar(Ind, Instancia) for Ind in PoblacionMejorada)
                        / len(PoblacionMejorada)) if PoblacionMejorada else 0.0
    Mejora = DistAntesMedia - DistDespuesMedia
    print(f"listo ({time.time()-T:.2f}s)  dist_media_despues={DistDespuesMedia:.2f}")
    if DistAntesMedia:
        print(f"  [SLS] Mejora promedio: {Mejora:.2f}  ({Mejora/DistAntesMedia*100:.2f}%)")
    print(f"  [SLS] Evaluaciones consumidas hasta ahora: {EVALUACIONES}/{LIMITE_EVALUACIONES}\n")

    return PoblacionMejorada


# Ejecucion del algoritmo Genetico
# Usando la estrategia de mu + lambda (padres + hijos), haciendo evolucionar generacion tras generacion
# Ademas, se implementan dos tipos de reinyeccion: una periodica (cada cierta cantidad de generaciones) y otra de emergencia (si no hay mejora tras cierto numero de generaciones)
# Toda la poblacion incial y lo reduce a 25 mu (abajo en el codigo de ejecucion se ve mejor, y luego genera 70 lambdas)
# Por cada generacion: se generan los lambda hijos tomando dos padres al azar, combinandolos con el cruce OX y aplicando mutacion swap e insercion
# Luego se juntan padres e hijos en un solo pool (mu + lambda) y se seleccionan los mu mejores por seleccion elitista, de modo que una buena solucion nunca se pierde
# Si corresponde, se aplica la reinyeccion periodica (reemplaza una fraccion de los peores por individuos nuevos aleatorios para mantener diversidad)
# Se actualiza el mejor individuo global si la generacion mejoro la distancia; si no, se cuenta como generacion sin mejora
# Si se acumulan demasiadas generaciones sin mejora, se gatilla la reinyeccion de emergencia (reemplazo mas agresivo para escapar de un minimo local)
# Todo el ciclo corre bajo el control de presupuesto: al alcanzar las 35700 evaluaciones se corta limpiamente y se devuelve la mejor solucion encontrada
# Retorna el mejor individuo, el historial de la mejor distancia por generacion y la poblacion final

def EjecutarAG(Instancia, Poblacion, Mu, Lambda, NumGeneraciones, TasaMutacion,
               FrecuenciaReinyeccion=50, FraccionReinyeccion=0.2,
               GeneracionesSinMejora=100, FraccionReinyeccionEmergencia=0.4):
    OptStr = f"{Instancia.OptimoConocido:.2f}" if Instancia.OptimoConocido else "desconocido"

    print(f"\n  Parametros AG:")
    print(f"    Mu (padres)               : {Mu}")
    print(f"    Lambda (hijos)            : {Lambda}")
    print(f"    Generaciones (tope)       : {NumGeneraciones}")
    print(f"    Tasa mutacion             : {TasaMutacion}")
    print(f"    Reinyeccion periodica     : cada {FrecuenciaReinyeccion} gen ({FraccionReinyeccion*100:.0f}% de Mu)")
    print(f"    Reinyeccion emergencia    : tras {GeneracionesSinMejora} gen sin mejora ({FraccionReinyeccionEmergencia*100:.0f}% de Mu)")
    print(f"    Optimo conocido           : {OptStr}")
    print(f"    Presupuesto global        : {LIMITE_EVALUACIONES} evaluaciones")
    print(f"    Evaluaciones ya usadas    : {EVALUACIONES}")
    print(f"    Poblacion inicial         : {len(Poblacion)} individuos post-SLS\n")
    MejorIndividuo     = Poblacion[0]
    MejorDistancia     = DistanciaSinContar(MejorIndividuo, Instancia)
    HistorialMejorDist = [MejorDistancia]
    NumReinyecciones   = 0
    NumEmergencias     = 0
    GenSinMejora       = 0
    GenAlcanzada       = 0

    def _gap_str(Dist):
        if Instancia.OptimoConocido:
            Gap = (Dist - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
            return f"gap={Gap:+.1f}%"
        return ""

    try:
        print("  Evaluando poblacion post-SLS...", end=" ", flush=True)
        TInicio        = time.time()
        ValoresFitness = [CalcularFitness(Ind, Instancia) for Ind in Poblacion]
        Poblacion      = SeleccionElitista(Poblacion, ValoresFitness, Mu)
        print(f"listo ({time.time() - TInicio:.1f}s)")

        MejorIndividuo = Poblacion[0]
        MejorDistancia = DistanciaSinContar(MejorIndividuo, Instancia)
        HistorialMejorDist = [MejorDistancia]

        print(f"  Distancia inicial (mejor post-SLS): {MejorDistancia:.2f}  {_gap_str(MejorDistancia)}\n")
        print(f"  {'Gen':>5}  {'Mejor dist':>12}  {'Gap%':>7}  {'Mejora':>9}  {'Reinj':>6}  {'Evals':>7}  {'t':>6}")
        print(f"  {'─'*72}")

        for Gen in range(1, NumGeneraciones + 1):
            GenAlcanzada = Gen
            TGen = time.time()
            Hijos = []
            while len(Hijos) < Lambda:
                Padre1, Padre2 = random.sample(Poblacion, 2)
                Hijo1, Hijo2   = CruceOX(Padre1, Padre2)
                Hijo1 = MutacionSwap(Hijo1, TasaMutacion)
                Hijo2 = MutacionSwap(Hijo2, TasaMutacion)
                Hijo1 = MutacionInsercion(Hijo1, TasaMutacion)
                Hijo2 = MutacionInsercion(Hijo2, TasaMutacion)
                Hijos.extend([Hijo1, Hijo2])

            
            PoolCombinado = Poblacion + Hijos
            FitnessPool   = [CalcularFitness(Ind, Instancia) for Ind in PoolCombinado]
            Poblacion     = SeleccionElitista(PoolCombinado, FitnessPool, Mu)

            
            EtiquetaReinj = "  -"
            if Gen % FrecuenciaReinyeccion == 0:
                NumNuevos        = max(1, int(Mu * FraccionReinyeccion))
                Frescos          = [GenerarIndividuo(Instancia) for _ in range(NumNuevos)]
                Poblacion        = Poblacion[:Mu - NumNuevos] + Frescos
                NumReinyecciones += 1
                EtiquetaReinj    = " PER"

            
            DistanciaActual = DistanciaSinContar(Poblacion[0], Instancia)
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
                print(f"  {Gen:>5}  {MejorDistancia:>12.2f}  {GapStr:>7}  {Signo}{abs(Mejora):>8.2f}  "
                      f"{EtiquetaReinj:>6}  {EVALUACIONES:>7}  {time.time()-TGen:>5.2f}s")

    except PresupuestoAgotado:
        print(f"\n  [AG] Presupuesto agotado en gen {GenAlcanzada} "
              f"({EVALUACIONES}/{LIMITE_EVALUACIONES} evaluaciones). Corte limpio.")

    print(f"  {'─'*72}")
    print(f"\n  Distancia final optima    : {MejorDistancia:.2f}  {_gap_str(MejorDistancia)}")
    print(f"  Generaciones completadas  : {GenAlcanzada}")
    print(f"  Evaluaciones consumidas   : {EVALUACIONES}/{LIMITE_EVALUACIONES}")
    print(f"  Reinyecciones periodicas  : {NumReinyecciones}")
    print(f"  Reinyecciones emergencia  : {NumEmergencias}")

    return MejorIndividuo, HistorialMejorDist, Poblacion


# IMPRESION DE RESULTADOS
def ResumirPermutacion(Individuo, MaxMostrar=10):
    N = len(Individuo)
    if N <= MaxMostrar * 2:
        return str(Individuo)
    Inicio = ", ".join(str(x) for x in Individuo[:MaxMostrar])
    Final  = ", ".join(str(x) for x in Individuo[-MaxMostrar:])
    return f"[{Inicio}, ... ({N - MaxMostrar*2} nodos omitidos) ..., {Final}]"


def ResumirRutas(ListaRutas, Instancia, MaxRutas=5, MaxNodosPorRuta=6):
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
    print(f"  Evaluaciones totales usadas: {EVALUACIONES}/{LIMITE_EVALUACIONES}")

    if PobFinal is not None:
        print(f"\n  {'='*54}")
        print(f"  TOP {Top} SOLUCIONES UNICAS  (poblacion final)")
        print(f"  {'='*54}")

        VistosDist = set()
        UniqFinal  = []
        for Ind in PobFinal:
            Dist = round(DistanciaSinContar(Ind, Instancia), 2)
            if Dist not in VistosDist:
                VistosDist.add(Dist)
                UniqFinal.append((Dist, Ind))

        UniqFinal.sort(key=lambda x: x[0])

        if not UniqFinal:
            print("  (sin soluciones unicas en la poblacion final)")
        else:
            for Puesto, (Distancia, Ind) in enumerate(UniqFinal[:Top], start=1):
                ListaRutas = Decodificar(Ind, Instancia)
                GapStr     = ""
                if Instancia.OptimoConocido:
                    G      = (Distancia - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
                    GapStr = f"  gap={G:+.2f}%"
                print(f"\n  #{Puesto}")
                print(f"    Distancia  : {Distancia:.2f}{GapStr}")
                print(f"    Vehiculos  : {len(ListaRutas)}")
                print(f"    Permutacion: {ResumirPermutacion(Ind, MaxMostrar=8)}")
                print(f"    Rutas (primeras 5 de {len(ListaRutas)}):")
                ResumirRutas(ListaRutas, Instancia, MaxRutas=5, MaxNodosPorRuta=5)

        if len(UniqFinal) < Top:
            print(f"\n  Nota: solo {len(UniqFinal)} soluciones distintas en poblacion final.")

    print("\n" + "=" * 60 + "\n")


def ImprimirPoblacion(Instancia, Poblacion, NumImprimir=3):
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

        print(f"  {'─'*54}")
        print(f"  Individuo {i+1}:")
        print(f"    Permutacion : {ResumirPermutacion(Individuo, MaxMostrar=8)}")
        print(f"    Vehiculos   : {len(ListaRutas)}")
        print(f"    Distancia   : {Distancia:.2f}")
        print(f"    Rutas (primeras 3):")
        ResumirRutas(ListaRutas, Instancia, MaxRutas=3, MaxNodosPorRuta=5)

    print()
    print(f"  Total soluciones generadas: {len(Poblacion)}")
    print("=" * 60)


# Funcion del bloque de ejecucion, basicamente que haga todo en el main, siendo SLS + AG
def EjecutarUnaCorrida(RutaArchivo, Semilla, Parametros, Verboso=False):
    random.seed(Semilla)
    ReiniciarPresupuesto(Parametros["LIMITE_EVALS"])

    Instancia = LeerInstanciaCVRP(RutaArchivo)
    Poblacion = GenerarPoblacion(Instancia, Parametros["TAMANO_POBLACION_INICIAL"])

    if Verboso:
        ImprimirPoblacion(Instancia, Poblacion, NumImprimir=2)

    import io as _io, contextlib as _ctx
    Contexto = _ctx.redirect_stdout(_io.StringIO()) if not Verboso else _ctx.nullcontext()

    with Contexto:
        Poblacion = AplicarSLSPoblacion(
            Poblacion, Instancia,
            TopN           = Parametros["SLS_TOP_N"],
            NumIteraciones = Parametros["SLS_ITERACIONES"]
        )
        MejorIndividuo, Historial, PobFinal = EjecutarAG(
            Instancia, Poblacion,
            Mu                            = Parametros["MU"],
            Lambda                        = Parametros["LAMBDA"],
            NumGeneraciones               = Parametros["NUM_GENERACIONES"],
            TasaMutacion                  = Parametros["TASA_MUTACION"],
            FrecuenciaReinyeccion         = Parametros["FREQ_REINYECCION"],
            FraccionReinyeccion           = Parametros["FRAC_REINYECCION"],
            GeneracionesSinMejora         = Parametros["GEN_SIN_MEJORA"],
            FraccionReinyeccionEmergencia = Parametros["FRAC_REINY_EMERGENCIA"]
        )

    Distancia = DistanciaSinContar(MejorIndividuo, Instancia)
    Rutas     = Decodificar(MejorIndividuo, Instancia)
    Gap = ((Distancia - Instancia.OptimoConocido) / Instancia.OptimoConocido * 100
           if Instancia.OptimoConocido else None)

    return {
        "nombre":          Instancia.Nombre,
        "archivo":         RutaArchivo,
        "semilla":         Semilla,
        "mejor_distancia": Distancia,
        "optimo":          Instancia.OptimoConocido,
        "gap":             Gap,
        "evaluaciones":    EVALUACIONES,
        "vehiculos":       len(Rutas),
        "mejor_individuo": MejorIndividuo,
    }


# ESTADISTICA Y EXPERIMENTO MULTI-SEMILLA
def CalcularEstadisticas(Distancias, Optimo=None):
    """Media, desviacion estandar (poblacional), min, max y gaps."""
    import statistics
    N      = len(Distancias)
    Media  = sum(Distancias) / N
    Desv   = statistics.pstdev(Distancias) if N > 1 else 0.0
    Minimo = min(Distancias)
    Maximo = max(Distancias)
    Stats = {
        "n": N, "media": Media, "desv": Desv,
        "min": Minimo, "max": Maximo,
    }
    if Optimo:
        Stats["gap_media"] = (Media - Optimo) / Optimo * 100
        Stats["gap_min"]   = (Minimo - Optimo) / Optimo * 100
    return Stats


def EjecutarExperimento(Archivos, Semillas, Parametros, RutaCSV="resultados.csv"):
    print("\n" + "#" * 64)
    print(f"  EXPERIMENTO MULTI-SEMILLA  ({len(Semillas)} corridas por instancia)")
    print(f"  Presupuesto por corrida: {Parametros['LIMITE_EVALS']} evaluaciones")
    print(f"  Semillas: {Semillas}")
    print("#" * 64)
    Resultados = {arch: [] for arch in Archivos}

    for IndiceSemilla, Semilla in enumerate(Semillas, start=1):
        print(f"\n  ── Ejecucion {IndiceSemilla}/{len(Semillas)}  (semilla {Semilla}) "
              f"{'─'*22}")
        for Archivo in Archivos:
            T = time.time()
            R = EjecutarUnaCorrida(Archivo, Semilla, Parametros, Verboso=False)
            Resultados[Archivo].append(R)
            GapStr = f"gap={R['gap']:+6.1f}%" if R["gap"] is not None else ""
            print(f"     {R['nombre']:8}  dist={R['mejor_distancia']:11.2f}  {GapStr}"
                  f"  evals={R['evaluaciones']}  veh={R['vehiculos']}  ({time.time()-T:.1f}s)")

    GuardarCSV(Archivos, Resultados, Semillas, RutaCSV)
    print(f"\n  CSV guardado en: {RutaCSV}")

    
    print("\n" + "#" * 64)
    print("  MEJOR SOLUCION POR INSTANCIA")
    print("#" * 64)
    for Archivo in Archivos:
        
        MejorCorrida = min(Resultados[Archivo], key=lambda R: R["mejor_distancia"])
        ImprimirMejorSolucion(Archivo, MejorCorrida, Parametros)

    return Resultados



def ImprimirMejorSolucion(Archivo, Corrida, Parametros):
    Instancia  = LeerInstanciaCVRP(Archivo)
    ListaRutas = Decodificar(Corrida["mejor_individuo"], Instancia)

    print("\n" + "=" * 60)
    print(f"  MEJOR SOLUCION  -  {Corrida['nombre']}")
    print("=" * 60)
    print(f"  Semilla        : {Corrida['semilla']}")
    print(f"  Distancia (OF) : {Corrida['mejor_distancia']:.2f}")
    if Instancia.OptimoConocido:
        print(f"  Optimo conocido: {Instancia.OptimoConocido:.2f}")
        print(f"  Gap            : {Corrida['gap']:+.2f}%")
    print(f"  Vehiculos      : {len(ListaRutas)}")
    print(f"  Rutas:")
    ResumirRutas(ListaRutas, Instancia, MaxRutas=len(ListaRutas), MaxNodosPorRuta=6)
    print("=" * 60)


def GuardarCSV(Archivos, Resultados, Semillas, RutaCSV):
    
    Etiquetas = [Resultados[a][0]["nombre"].lower() for a in Archivos]
    Cabecera  = "ejecucion,semilla," + ",".join(f"distancia_{e}" for e in Etiquetas)

    Lineas = [Cabecera]
    for i, Semilla in enumerate(Semillas):
        Campos = [str(i + 1), str(Semilla)]
        for Archivo in Archivos:
            Campos.append(f"{Resultados[Archivo][i]['mejor_distancia']:.4f}")
        Lineas.append(",".join(Campos))

    with open(RutaCSV, "w") as F:
        F.write("\n".join(Lineas) + "\n")


# Ejecucion MAIN

if __name__ == "__main__":
    Archivos = [
        "01_facil.txt",
        "02_medio.txt",
        "03_dificil.txt"
    ]

    # ── 10 semillas para las 10 ejecuciones independientes por instancia ──
    SEMILLAS = [42, 7, 13, 99, 256, 1024, 333, 77, 500, 888]

    # ── Presupuesto por ejecucion ─────────────────────────────────
    LIMITE_EVALS              = 35700  

    # ── Parametros generales
    TAMANO_POBLACION_INICIAL  = 300    # individuos aleatorios al inicio (antes 5000)
    MU                        = 25     # padres que sobreviven por generacion (antes 50)
    LAMBDA                    = 70     # hijos generados por generacion (antes 100)
    NUM_GENERACIONES          = 100000 # tope alto: el presupuesto corta antes
    TASA_MUTACION             = 0.15
    FREQ_REINYECCION          = 40     # reinyeccion periodica cada N gen (antes 50)
    FRAC_REINYECCION          = 0.20
    GEN_SIN_MEJORA            = 50     # gen sin mejora -> emergencia (antes 60)
    FRAC_REINY_EMERGENCIA     = 0.40

    # ── Parametros SLS ────────────────────────────────────────────
    SLS_TOP_N                 = 40     # mejores individuos que pasan al SLS (antes 50)
    SLS_ITERACIONES           = 25     # iteraciones de exploracion por individuo (antes 30)

    # Empaquetar todos los parametros en un dict para pasarlos a las corridas
    PARAMETROS = {
        "LIMITE_EVALS":             LIMITE_EVALS,
        "TAMANO_POBLACION_INICIAL": TAMANO_POBLACION_INICIAL,
        "MU":                       MU,
        "LAMBDA":                   LAMBDA,
        "NUM_GENERACIONES":         NUM_GENERACIONES,
        "TASA_MUTACION":            TASA_MUTACION,
        "FREQ_REINYECCION":         FREQ_REINYECCION,
        "FRAC_REINYECCION":         FRAC_REINYECCION,
        "GEN_SIN_MEJORA":           GEN_SIN_MEJORA,
        "FRAC_REINY_EMERGENCIA":    FRAC_REINY_EMERGENCIA,
        "SLS_TOP_N":                SLS_TOP_N,
        "SLS_ITERACIONES":          SLS_ITERACIONES,
    }

    # ── Ejecutar las 10 mejores por instancia + estadistica + CSV ──
    Resultados = EjecutarExperimento(
        Archivos   = Archivos,
        Semillas   = SEMILLAS,
        Parametros = PARAMETROS,
        RutaCSV    = "resultados.csv"
    )