import random
import math


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
        if Linea.startswith(("TYPE", "COMMENT", "DIMENSION", "EDGE_WEIGHT_TYPE")):
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

    return InstanciaCVRP(Nombre, Capacidad, NodoDeposito, ListaCoordenadas, ListaDemandas)


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
       aparece exactamente una vez → no hay duplicados ni omisiones.
    2. Continuidad de ruta: la lectura secuencial i → i+1 traza la
       ruta sin interrupciones logicas.
    3. Limite de capacidad: acumulador por vehiculo. Si agregar el
       siguiente cliente excede Q → se cierra la ruta actual y se
       abre una nueva con el cliente que no cabia.
    4. Vinculacion al deposito: cada ruta empieza y termina con el
       indice del deposito, aunque este no aparece en la permutacion.

    Retorna:
        ListaRutas: lista de listas, cada sublista es la ruta completa
                    de un vehiculo incluyendo deposito al inicio y al final.
                    Ejemplo: [[0, 5, 12, 3, 0], [0, 7, 1, 0]]
    """
    IndiceDeposito = Instancia.NodoDeposito - 1
    Capacidad      = Instancia.Capacidad
    Demandas       = Instancia.ListaDemandas

    ListaRutas     = []   # resultado final
    RutaActual     = [IndiceDeposito]  # restriccion 4: salida desde deposito
    CargaActual    = 0

    for NodoCliente in Individuo:
        DemandaCliente = Demandas[NodoCliente]

        # Restriccion 3: ¿cabe este cliente en el vehiculo actual?
        if CargaActual + DemandaCliente <= Capacidad:
            # Restriccion 2: continuidad → simplemente se agrega al final
            RutaActual.append(NodoCliente)
            CargaActual += DemandaCliente
        else:
            # Capacidad excedida → cerrar ruta actual y abrir una nueva
            RutaActual.append(IndiceDeposito)  # restriccion 4: regreso al deposito
            ListaRutas.append(RutaActual)

            # Nueva ruta para este cliente que no cabia
            RutaActual  = [IndiceDeposito, NodoCliente]  # restriccion 4: sale del deposito
            CargaActual = DemandaCliente

    # Cerrar la ultima ruta activa
    RutaActual.append(IndiceDeposito)  # restriccion 4: regreso al deposito
    ListaRutas.append(RutaActual)

    return ListaRutas


# ============================================================
# Disntancia Total y Fitness
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
# BLOQUE 6: IMPRESION
# ============================================================
def ImprimirPoblacion(Instancia, Poblacion, NumImprimir=100):
    IndiceDeposito = Instancia.NodoDeposito - 1
    print("=" * 60)
    print(f"  INSTANCIA : {Instancia.Nombre}")
    print(f"  Nodos     : {Instancia.NumNodos}  (incluye deposito)")
    print(f"  Clientes  : {Instancia.NumNodos - 1}")
    print(f"  Capacidad : {Instancia.Capacidad}")
    print(f"  Deposito  : indice {IndiceDeposito} (nodo {Instancia.NodoDeposito})")
    print("=" * 60)

    # ── Primeras N soluciones ──────────────────────────────
    MostrarHasta = min(NumImprimir, len(Poblacion))
    print(f"\nPrimeras {MostrarHasta} soluciones (lista aleatoria → rutas decodificadas):\n")

    for i in range(MostrarHasta):
        Individuo  = Poblacion[i]
        ListaRutas = Decodificar(Individuo, Instancia)

        print(f"  {'─'*54}")
        print(f"  Individuo {i+1:>5}:")
        print(f"    Permutacion : {Individuo}")
        print(f"    Vehiculos   : {len(ListaRutas)}")
        for j, Ruta in enumerate(ListaRutas):
            CargaRuta = sum(Instancia.ListaDemandas[n] for n in Ruta if n != IndiceDeposito)
            print(f"    V{j+1:>3}: carga={CargaRuta:>6}  ruta={Ruta}")
        print(f"    Distancia total: {CalcularDistanciaTotal(ListaRutas, Instancia):.2f}")
        print(f"    Fitness        : {CalcularFitness(Individuo, Instancia):.6f}")

    # ── Top 5 mejores fitness de toda la población ─────────
    print(f"\n  {'═'*54}")
    print(f"  TOP 5 MEJORES FITNESS (de {len(Poblacion)} soluciones)")
    print(f"  {'═'*54}")

    FitnessTotal = [
        (i, CalcularFitness(Poblacion[i], Instancia))
        for i in range(len(Poblacion))
    ]
    FitnessTotal.sort(key=lambda x: x[1], reverse=True)  # mayor fitness primero

    for Puesto, (Indice, Fitness) in enumerate(FitnessTotal[:5], start=1):
        Individuo  = Poblacion[Indice]
        ListaRutas = Decodificar(Individuo, Instancia)
        Distancia  = CalcularDistanciaTotal(ListaRutas, Instancia)

        print(f"\n  #{Puesto}  Individuo {Indice+1:>6} │ Fitness: {Fitness:.6f} │ Distancia: {Distancia:.2f} │ Vehiculos: {len(ListaRutas)}")
        for j, Ruta in enumerate(ListaRutas):
            CargaRuta = sum(Instancia.ListaDemandas[n] for n in Ruta if n != IndiceDeposito)
            print(f"    V{j+1:>3}: carga={CargaRuta:>6}  ruta={Ruta}")

    print()
    print(f"  Total de soluciones generadas: {len(Poblacion)}")
    print("=" * 60)
    print()



# ============================================================
# BLOQUE 7: MAIN
# ============================================================
if __name__ == "__main__":
    random.seed(42)

    Archivos = [
        "01_facil.txt",
        "02_medio.txt",
        "03_dificil.txt"
    ]

    TAMANO_POBLACION = 35700

    for RutaArchivo in Archivos:
        print(f"\nCargando {RutaArchivo}...")
        Instancia  = LeerInstanciaCVRP(RutaArchivo)
        Poblacion  = GenerarPoblacion(Instancia, TAMANO_POBLACION)
        ImprimirPoblacion(Instancia, Poblacion, NumImprimir=3)