from magicFactory import MagicFactory
from typing import List
from qiskit import QuantumCircuit


class ResourceEstimator:
    magicFactories: List[MagicFactory]   #list of magic factories on the chip to run the algo
    quantumCircuit: QuantumCircuit       #The circuit to be run
    codeDistance: int                    #The code distance of error correction on the circuit
    p_phys: float

    def __init__(self, magicFactories: List[MagicFactory], quantumCircuit: QuantumCircuit):
        self.magicFactories = magicFactories
        self.quantumCircuit = quantumCircuit

    #TODO: function to decompose circuit into clifford + whatever magic state is made by the factories
    def decomposeToCliffordPlusMagic(self):
        # Raise an error if magicFactories or quantumCircuit is null.
        if self.magicFactories == None:
            raise ValueError("ResourceEstimator.magicFactories should not be null.")
        if self.quantumCircuit == None:
            raise ValueError("ResourceEstimator.quantumCircuit should not be null.")
        
        #TODO: look at the magic factories in the list of magic factories and decompose the circuit into those gates
        return None

    """
        Do a resource analysis of the given circuit using the magic factories provided
        Determine cycles to run (runtime), space on chip (magic factory + errorcorrection + algo), 
    """
    def analyzeCircuit(self):
        #TODO: function to go through and analyze the total resource cost of running the circuit with the given factories (may be multiple functions)
        return
