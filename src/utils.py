from enum import Enum

"""
    Enum of all the quantum gates we will be dealing with
"""
class QuantumGate(Enum):
    # CLIFFORD
    X = "X"
    Y = "Y"
    Z = "Z"
    H = "H"
    CX = "CX"
    S = "S"

    # NON CLIFFORD
    T = "T"
    CCZ = "CCZ"
    sqrtT = "sqrtT"
    R_z = "R_z"
    Tdiv2 = "T/2"

    @property
    def is_clifford(self) -> bool:
        return self in {QuantumGate.X, QuantumGate.Y, QuantumGate.Z, QuantumGate.H, QuantumGate.CX, QuantumGate.S}

"""
    Calculates the logical error rate of a surface code based on a physical error rate p_phys and a code distance d
    The equation used is based on the one presented in sec 2 of the paper 'Magic State Distillation: Not as Costly as you Think'
"""
def calcLER(p_phys:float, d:int):
    exp = (d+1)/2
    LER = 0.1*(100*p_phys)**exp
    return LER

"""
    Calculates the probability of an X error occuring and the probability of a Z error occuring when a logical qubit is encoded
    in a rectangular patch of d_x by d_z where d_x is the x code distance and d_z is the z code distance.
    Calculations based on sec 2 of paper 'Magic State Distillation: Not as Costly as you Think'
"""
def calcProbErr_X_Z(p_phys:float, d_x:int, d_z:int):
    probXerr = 0.5 * (d_z / d_x) * calcLER(p_phys, d_x)
    probZerr = 0.5 * (d_x / d_z) * calcLER(p_phys, d_z)
    return probXerr, probZerr