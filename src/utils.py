from enum import Enum
import numpy as np
from scipy.linalg import sqrtm

"""
    Enum of all the quantum gates we will be dealing with
"""
class QuantumGate(Enum):
    # CLIFFORD
    X = "x"
    Y = "y"
    Z = "z"
    H = "h"
    CX = "cx"
    S = "s"

    # NON CLIFFORD
    T = "t"
    CCZ = "ccz"
    sqrtT = "sqrtT"
    rootT_4 = "4rootT"
    rootT_8 = "8rootT"
    rootT_16 = "16rootT"
    rootT_32 = "32rootT"
    PHASE = "p"
    Tdiv2 = "T/2"
    Tdg = "Tdagger"

    @property
    def isClifford(self) -> bool:
        return self in {QuantumGate.X, QuantumGate.Y, QuantumGate.Z, QuantumGate.H, QuantumGate.CX, QuantumGate.S}

    @property
    def is_2x2(self) -> bool:
        return self in {QuantumGate.X, QuantumGate.Y, QuantumGate.Z, QuantumGate.H, QuantumGate.S, QuantumGate.T, QuantumGate.sqrtT, QuantumGate.R_z, QuantumGate.Tdiv2}

    @property
    def getAngle(self) -> float:
        if self in {QuantumGate.X, QuantumGate.Y, QuantumGate.Z}:
            return np.pi
        if self == QuantumGate.T:
            return np.pi/4
        elif self == QuantumGate.sqrtT:
            return np.pi/8
        elif self == QuantumGate.rootT_4:
            return np.pi/16
        elif self == QuantumGate.rootT_8:
            return np.pi/32
        elif self == QuantumGate.rootT_16:
            return np.pi/64
        elif self == QuantumGate.rootT_32:
            return np.pi/128
        else:
            raise ValueError(f"getAngle is not defined for {self.name} gate")
        
    @property
    def getDaggerAngle(self) -> float:
        try:
            return -self.getAngle
        except ValueError:
            raise ValueError(f"getDaggarAngle is not defined for {self.name} gate")
        
        
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

def dagger(matrix):
    newMatrix = np.matrix_transpose(matrix)
    newMatrix = np.conjugate(newMatrix)
    return newMatrix

def operatorNorm(matrix0, matrix1):
    subtractedMatrix = matrix0 - matrix1
	# This is how Wolfram Alpha says to do an operator norm, at least to my understanding.
    return sqrtm(max(np.linalg.eig(np.matmul(np.linalg.matrix_transpose(subtractedMatrix), subtractedMatrix)).eigenvalues))