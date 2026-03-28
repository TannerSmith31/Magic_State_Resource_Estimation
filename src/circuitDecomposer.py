from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from src.utils import QuantumGate

class circuitDecomposer:
    gateSet: list[QuantumGate]        #List of gates that we will decompose the arbitrary circuit into
    decompositionError: float         #tolerable error for each gate when decomposing a circuit
    originalCircuit: QuantumCircuit   #the original non-decomposed circuit comprised of arbitrary gates
    decomposedCircuit: QuantumCircuit #the decomposed circuit comprised of only gates in our gateSet

    def __init__(self, gateSet:list[QuantumGate], decompositionError:float, originalCircuit:QuantumCircuit):
        self.gateSet = gateSet
        self.decompositionError = decompositionError
        self.originalCircuit = originalCircuit
    
    def decomposeToGateset(self):
        #TODO: take the original circuit from this object and decompose it into the gateSet of this object
        #Possible organization: have this function take in the gateset to decompose to and then have seperate subfunctions
        #in this class that go from arbitrary gateset to a specific clifford + <Magic> gateset and then have this function
        #determine which of those functions to call

        #TODO: set the decomposedCircuit to the one we just created and then return the decomposed circuit
        return "TODO: IMPLEMENT decomposeToGateset function"
