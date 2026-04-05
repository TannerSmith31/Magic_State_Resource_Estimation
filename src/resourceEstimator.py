from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel, pauli_error
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGOpNode
from qiskit_aer import AerSimulator
import itertools

from src.circuitDecomposer import CircuitDecomposer
from src.utils import QuantumGate
from src.magicFactory import MagicFactory

#TODO: go through and change the decompPrecision variable to be a mp floating point rather than just a float.
class ResourceEstimator:
    magicFactories: list[MagicFactory]   # List of magic factories on the chip to run the algo
    basisGateset: list[QuantumGate]      # basis gateset for this estimator (clifford + the magic gates that can be produced by the factories)
    magicGateset: list[QuantumGate]      # set of magic gates being distilled
    codeDistance: int                    # The code distance of error correction on the circuit
    p_phys: float

    def __init__(self, magicFactories: list[MagicFactory], codeDistance:int, p_phys:float):
        self.magicFactories = magicFactories
        self.codeDistance = codeDistance
        self.p_phys = p_phys 

        # Look at the list of magic factories to get the magic basis
        if not magicFactories:
            raise ValueError("must pass a list of magic factories when creating a ResourceEstimator")
        magicGateset = {gate for factory in self.magicFactories for gate in factory.gates} #create a set of gates from the magic factory
        basisGateset = list(magicGateset) #convert the magic gateset to a list and assign those gates into the basis gateset, then iterate through the nonclifford gates and add them
        
        #add clifford gates to the basis gateset
        for gate in QuantumGate:
            if gate.isClifford:
                basisGateset.append(gate)
        
        #add the basis gateset and magic gateset to the resource estimator
        self.basisGateset = list(basisGateset)
        self.magicGateset = magicGateset

    """
        Function to decompose circuit into Clifford + whatever magic state is made by the factories
            decompPrecision: How close we want each gate to be to the target unitary (TODO: determine if this should be per gate, or full circuit decomp precision [i.e. we want the full circuit, when treated as a unitary, to be within the precision of the original])
    """
    def decomposeToCliffordPlusMagic(self, qc:QuantumCircuit, decompPrecision:float):
        # Raise an error if magicFactories or quantumCircuit is null.
        if self.magicFactories == None:
            raise ValueError("ResourceEstimator.magicFactories should not be null.")
        if qc == None:
            raise ValueError("ResourceEstimator.quantumCircuit should not be null.")
        
        #TODO: Look at the list of magic factories and decompose the circuit into the available gates.
        gates = []
        for factory in self.magicFactories:
            gates.append(factory.gate)
        for gate in QuantumGate:
            if gate.is_clifford:
                gates.append(gate)

        decomposer = CircuitDecomposer(gates, errorRate, self.quantumCircuit)
        decomposedCircuit = decomposer.decomposeToGateset()
        return decomposedCircuit
    
    """
        calculates the total number of physical qubits needed to run the algorithm (factories + algorithm)
    """
    def calcFootprint(self):
        # Calculate the total area of factories
        magicFactoryFootprint = 0 #initialize a counter for the qubits required for all factories
        for mFactory in self.magicFactories:
            magicFactoryFootprint += mFactory.qubitFootprint
        
        #Calculate the physical qubits required for the algorithm based on code distance
        logicalQubits = self.quantumCircuit.num_qubits()            #each qubit in the algorithm is a logical qubit
        logicalQubitFootprint = 2 * self.codeDistance**2 - 1    #surface codes are a [2d^2-1, 1, d] code so it takes 2d^2-1 physical qubits to implement 1 logical qubit
        circuitFootprint = logicalQubits * logicalQubitFootprint

        #TODO: account for routing / lattice surgery? or ignore routing? maybe give a flat 10% for routing or something?

        return magicFactoryFootprint + circuitFootprint
    
    """
        Function to calculate how long the algorithm will take to run. It considers the number of cycles needed to produces the required
        number of magic states and how many magic states can be produced per timestep
    """
    def calcRuntime(self, qc:QuantumCircuit) -> float:
        # create a dictionary to keep track of the totoal number of each type of magic gate in the circuit
        magicGateCounts = {gate.value: 0 for gate in self.magicGateset}
        
        for instruction in qc.data:
            gateName = instruction.operation.name
            if gateName in magicGateCounts:
                magicGateCounts[gateName] += 1

        #create a dictionary to keep track of the depth of each magic gate in the circuit
        magicGateDepths = self.getMagicDepths(qc)
        
        #calculate the production rate of each of the magic states
        magicStateProductionRates = {gate: 0 for gate in self.magicGateset} #this will be in AlgoCycles/Tgate  (NOTE: algoCycles are cycles based on the code distance of the algo)
        for magicFactory in self.magicFactories:
            for magicOutState in magicFactory.gates: #go through all the produced states
                #take the factories outStateCnt and divide it by how many operations occur
                #This will be the number of states output per operation (ill call a 'unit of time') and then multiply that by the number of units of time occur in one code cycle of the algorithm
                factoryOutputRate = (magicFactory.outStateCnts[magicOutState]/magicFactory.distillationTime)*self.codeDistance
                
                #sum up the output rates for each of the factories
                magicStateProductionRates[magicOutState] += factoryOutputRate
        
        #TODO: this has nothing to do with the depth of the circuit, not just total number of gates.
        #calculate the total number of cycles to generate enough of each magic state and take the largest
        mostCyclesOfStates= 0
        for magicState in self.magicGateset:
            cyclesForCurState = magicGateCounts[magicState]/magicStateProductionRates[magicState]
            if cyclesForCurState > mostCyclesOfStates:
                mostCyclesOfStates = cyclesForCurState
        
        return mostCyclesOfStates
    
    """
        Function to get the depth of the circuit in relation to each of the magic states. This is calculated by running through the DAG of the circuit and
        finding the longest path of a certain magic gate that must be executed sequentially.
        Params:
            qc: The quantum circuit to get the depth of magic gates of
        Returns:
            dictionary of {magicGate: depth} pairs
    """
    def getMagicDepths(self,qc:QuantumCircuit) -> dict[QuantumGate,int]:
        circuitDAG = circuit_to_dag(qc)
        nodeMagicDepths = {}
        maxMagicDepths = {gate:0 for gate in self.magicGateset}

        for node in circuitDAG.topological_nodes():  #Iterate through nodes in topological order
            predNodeList = list(circuitDAG.predecessors(node)) #create an iterator that goes over the predecessor nodes and convert it to a list
            nodeMagicDepths[node] = {} #initialize the subdictionary in this node for all the magic states

            for magicGate in self.magicGateset:
                #If there are no predecessors, add the node to the dictionary and set its value to 0
                if len(predNodeList) < 1:
                    nodeMagicDepths[node][magicGate] = 0
                #otherwise go through predecessors and calculate this nodes depth by taking the max (then later adding 1 if its a magic gate)
                else:
                    nodeMagicDepths[node][magicGate] = max(nodeMagicDepths[p][magicGate] for p in predNodeList)

                #if the current node is the magic gate we are counting, we add one to its depth
                if isinstance(node, DAGOpNode) and node.op.name == magicGate.value:
                    nodeMagicDepths[node][magicGate] += 1
                
                #check if the depth for the current node & gate is greater than the max seen for this magic gate
                if nodeMagicDepths[node][magicGate] > maxMagicDepths[magicGate]:
                    maxMagicDepths[magicGate] = nodeMagicDepths[node][magicGate]
        
        return maxMagicDepths

    """
        Function to run the circuit (decomposed or original depending on 'decomposeQC' variable) and determine runtime statistics of the algorithm (fidelity, etc.)
            shots: the number of shots to run
            decomposeQC: boolean to tell whether to run the decomposed circuit or the original circuit. Defaults to True (using the decomposed circuit)
            idealClifford: boolean to tell whether noise should be added to the circuit itself, or just to the magic gates
    """
    def runCircuit(self, qc:QuantumCircuit, shots:int=1000, idealCliffords:bool=True):        
        ###GENERATING NOISE MODEL###
        p_th = 0.01  #based on surface codes from 'Surface codes towards practical quantum computing'
        
        ## Compute logical error rate
        if self.codeDistance == 0:
            p_L = self.p_phys  #no error correction
        else:
            exponent = (self.codeDistance + 1) / 2
            p_L = 0.03 * (self.p_phys / p_th)**exponent #LER eq based on 'Surface codes towards practical quantum computing'

        ##Build noise model
        noiseModel = NoiseModel()

        ## Add noise to cliffords if chosen
        if not idealCliffords:
            magicGateNames = [gate.value for gate in self.magicGateset] #get the names of all the magic gates
            allCircuitGates = qc.count_ops().keys() #get the names of all the gates in the circuit
            
            nonMagicGates1q = []
            nonMagicGates2q = []

            for gateName in allCircuitGates:
                #skip if gateName is a magic gate (or a barrier)
                if gateName in magicGateNames or gateName == 'barrier':
                    continue

                inst = qc.find_instruction(gateName)[0].operation

                if inst.num_qubits == 1:
                    nonMagicGates1q.append(gateName)
                elif inst.num_qubits == 2:
                    nonMagicGates2q.append(gateName)
                else:
                    print(f"WARNING: found a gate in the circuit with more than 3 qubits: {gateName}. Noise not automatically applied")

            
            err_1q = pauli_error([('X', p_L/3), ('Y', p_L/3), ('Z', p_L/3), ('I', 1-p_L)])
            paulis = ["".join(p) for p in itertools.product("IXYZ", repeat=2) if "".join(p) != "II"]
            err_2q = pauli_error([(op, p_L/15) for op in paulis] + [("II", 1-p_L)])

            ## Apply to all logical single- and two-qubit gate errors
            noiseModel.add_all_qubit_quantum_error(err_1q, nonMagicGates1q)
            noiseModel.add_all_qubit_quantum_error(err_2q, nonMagicGates2q)
        
        ## Add noise to magic gates based on distillation fidelity
        magicGatesetFidelities = {g:0 for g in self.magicGateset}
        for gate in self.magicGateset:
            #Ideally, to get the average fidelity of the magic states being produced, lets say we have three factories A B and C that produce states
            #at rates Ra, Rb, and Rc (Tgates per unitTime where uniTime is cycles * codeDistance^2 since a cycle is the time to measure all the
            #stabelizers which is proportional to d^2), and produce magic states with fidelities Fa, Fb, Fc, then we can say the average fidelity 
            # will be (Ra/(Ra+Rb+Rc))*Fa + (Rb/(Ra+Rb+Rc))*Fb + (Rc/(Ra+Rb+Rc))*Fc = (Ra*Fa + Rb*Fb + Rc*Fc)/(Ra + Rb + Rc) so we wil have a variable 
            # storing the denominator sum (Ra+Rb+Rc) and one that is saving the numerator sum (Ra*Fa + Rb*Fb + Rc*Fc)
            fidelityRatioSum = 0 #numerator
            productionRateSum = 0 #denominator
            for magicFactory in self.magicFactories:
                for outMagicGate in magicFactory.gates:
                    if outMagicGate == gate:
                        #get the magic states produced per unit of time by taking the number of states output and dividing it by the distillation time
                        curFactoryProductionRate = magicFactory.outStateCnts[gate]/magicFactory.distillationTime
                        productionRateSum += curFactoryProductionRate
                        fidelityRatioSum += curFactoryProductionRate * (1-magicFactory.outErrorRates[outMagicGate]) #fidelity of the output state is 1-error
            
            magicGatesetFidelities[gate] = fidelityRatioSum/productionRateSum  #TODO: error check for division by zero here and the above parts of this loop that have a division

        #go through the error rates for each of the magic states and add them to their respective gates.
        for magicGate in self.magicGateset:
            magicGateErr = 1-magicGatesetFidelities[magicGate]
            magic_err = pauli_error([('Z', magicGateErr), ('I', 1 - magicGateErr)]) # T-gates usually suffer Z-errors
            noiseModel.add_all_qubit_quantum_error(magic_err, [magicGate.value])

        ### USING NOISE MODEL TO RUN CIRCUIT ###
        simulator = AerSimulator(noise_model = noiseModel) #set noise model into simulator backend
        job = simulator.run(qc, shots=shots)
        results = job.results()
        counts = results.get_counts()

        return counts

    """
        Do a resource analysis of the given circuit using the magic factories provided
        Determine cycles to run (runtime), space on chip (magic factory + errorcorrection + algo), 
    """
    def analyzeCircuit(self, qc:QuantumCircuit, decompPrecision:float):
        #Decompose circuit based on magic factories  (ALREADY DONE WHEN RESOURCE ESTIMATOR IS CREATED. MAYBE CHANGE THIS TO BE DONE AFTER AND DECOMPOSED CIRCUIT IS PASSED IN?)

        #Calculate footprint

        #run circuit to get COUNTS

        # use COUNTS into a function that takes in counts and the circuit/algo run and determines fidelity (so somehow gets the ideal counts and compares)
        return
