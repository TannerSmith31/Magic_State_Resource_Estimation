from __future__ import annotations  #This allows me to type-hint something as a MagicFactory in a param to a function in the class definition.
import math
from src.utils import calcLER, calcProbErr_X_Z, QuantumGate

class MagicFactory:
    inStateCnts: dict[QuantumGate,int]      #number of each type of state input into the factor to be distilled
    outStateCnts: dict[QuantumGate,int]     #number of each type of magic state output by the factory
    outErrorRates: dict[QuantumGate,float]   #error rate of the magic states produced by the factory
    distillationCycles: float               #number of cycles to run a full distillation
    distillationTime: float              #amount of 'time' to run a full distillation. Note, 'Time' is number of stabelizer measurements (cycles*d). This accounts for code distance slowing down the factory
    qubitFootprint:int                      #number of physical qubits required for the factory
    codeDistance:int                        #code distance used to implement this factory
    subFactories: list[MagicFactory]|None   #Subfactories used within this magic factory (e.g. CCZ factory uses multiple T factories to create magic state)

    def __init__(self, inStateCnts:dict[QuantumGate,int], outStateCnts:dict[QuantumGate,int], outErrorRates:dict[QuantumGate,float], 
                 distillationCycles:float, distillationTime:float, qubitFootprint:int, codeDistance:int, subFactories:list[MagicFactory]|None = None):
        
        if (len(outStateCnts) != len(outErrorRates)):
            raise ValueError(f"The length of outStateCnts ({len(outStateCnts)}) doesn't match the length of outErrorRates ({len(outErrorRates)}). Ensure you have provided error rates for all output states.")
        
        self.inStateCnts = inStateCnts
        self.outStateCnts = outStateCnts
        self.outErrorRates = outErrorRates
        self.distillationCycles = distillationCycles
        self.distillationTime = distillationTime
        self.qubitFootprint = qubitFootprint
        self.codeDistance = codeDistance
        self.subFactories = subFactories

    """Get a list of the magic states produced by this factory"""
    def getMagicStates(self):
        magicStates = []
        for state in self.outStateCnts: #iterate through the keys of the outState cnt dictionary.
            magicStates.append(state)
        return magicStates


    """
        T factory from paper "Magic State Distillation: Not as Costly as You Think" by Daniel Litinski
            d_x: x code distance
            d_z: z code distance
            d_m: number of code cycles used in lattice surgery
            p_phys: error rate of the physical qubits
        NOTE: this factory takes in |+> qubits and outputs |T> magic states   TODO: double check this is the case
    """
    @classmethod
    def T_factory_15_to_1(cls, d_x:int, d_z:int, d_m:int, p_phys:float) -> MagicFactory:

        #TODO: FIGURE OUT HOW THEY CALCULATE outErrorRate and p_fail SO I DONT HAVE TO HARD CODE THE EXAMPLES HERE
        p_fail = 0   #the probability the distilation protocol fails
        outErrorRate = 0    #error rate of the produced magic state causing a faulty rotation
        if (d_x==7 and d_z == 3 and d_m == 3 and math.isclose(p_phys, 1e-4)):
            p_fail = 0.005524
            outErrorRate = 4.4 * 10**(-8)
        elif (d_x==9 and d_z==3 and d_m ==3 and math.isclose(p_phys, 1e-4)):
            p_fail = 0.005524
            outErrorRate = 9.3 * 10**(-10)
        elif (d_x==11 and d_z==5 and d_m == 5 and math.isclose(p_phys, 1e-4)):
            p_fail = 0
            outErrorRate = 1.9 * 10**(-11)
        else:
            print("WARNING: unknown d_x, d_z, d_m, p_phys combo for 15 to 1 factory")
            print("setting p_fail to 10^-3 and outErrorRate = p_phys^((d_x+1)/4)")
            p_fail = 10**(-3)
            outErrorRate = p_phys**((d_x+1)/4) # This seems to approximate the error rates given in the 'Not as Costly' paper fairly well
        
        qubitFootprint =  2*(d_x + 4*d_z) * 3*d_x + 4*d_m #This equation appears in section 3 of the 'not as costly' paper
        distillationCycles = 6 * d_m / (1-p_fail)           #This equation appears in section 3 of the 'not as costly paper
        distillationTime = distillationCycles * max(d_x,d_z)  #This gets us the number of stabelizer measurements

        return cls(
            inStateCnts = {QuantumGate.H:5}, #TODO: figure out a way to change this. Its technically the |+> state that goes in
            outStateCnts = {QuantumGate.T:1},
            outErrorRates = {QuantumGate.T:outErrorRate},
            distillationCycles = distillationCycles,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint,
            codeDistance = d_x, #TODO: maybe adjust the class to take in more than just one code distance so we can also account for d_z
        )
    
    """
        15 to 1 T factory introduced in 'Low Overhead Quantum Computing with Lattice Surgery'. It is a little more space costly than the 15 to 1 factory
        from the 'Not as costly as you think' paper but provides better output fidelity (according to the equations).
            d: code distance used to encode logical qubits
            p_in: error rate of the states going into the distillation (this is the physical error rate if we are making a level 1 factory)
        NOTE: This factory takes in noisy |+> states and outputs clean |T> magic states
    """
    @classmethod
    def T_factory_15_to_1_Old(cls, d:int, p_in:float) -> MagicFactory:
        
        qubitFootprint = (4*d) * (8*d)
        numCycles = 6.5
        distillationTime = numCycles * d #I got this eq from the paper this factory is from under section X. Distillation
        outErrorRate = 35 * p_in**3 #assuming that the input of the factory is p_in TODO: this is probably distillation limited and doesnt relate to surface code size

        return cls(
            inStateCnts = {QuantumGate.H:15},
            outStateCnts = {QuantumGate.T:1},
            qubitFootprint = qubitFootprint,
            outErrorRates = {QuantumGate.T:outErrorRate},
            distillationCycles = numCycles,
            distillationTime = distillationTime,
            codeDistance = d,
        )
    
    """
        CCZ factory based on the paper 'Efficient magic state factories with a catalyzed |CCZ> -> 2|T> transformation'
            T_Factory: The factory/protocol that is generating the T states to be used in the generation of the CCZ state
                NOTE: this must be a T factory. Also, the paper uses T factories that have half the code distance as the CCZ part of the factory
            d_CZZ is the code distance used for the CCZ distillation that distills the |T1> states into a CCZ state
    """
    @classmethod
    def CCZ_factory(cls, T_Factory: MagicFactory, d_CCZ: int) -> MagicFactory:
        
        if T_Factory.getMagicStates() != [QuantumGate.T]:  #CCZ factory works by using T gates distilled from T factories  PTODO:could update this to accept factories that produce |T> and other gates and just do calculations based on the |T> states
            raise ValueError(f'CCZ_factory param T_Factory must be a T gate factory but was a {T_Factory.getMagicStates()} gate factory')
        CCZ_NaiveDistCycleCnt = 4 + (T_Factory.codeDistance/d_CCZ)*3 + 1 + 2 #based on paper [4 stabelizer meas + Tdist/CCZdist*3 T injection + 1 X or Y basis meas + 2 detect err]
        CCZ_distillationCycles = (4 + (T_Factory.codeDistance/d_CCZ)*3) #we pipeline the factory by starting the production of the next CCZ state after finishing the T injection of the prior CCZ state so when running for a long time it only takes the time to do the injection and measurements.
        CCZ_distillationTime = CCZ_distillationCycles * d_CCZ
        numT1Factories = math.ceil((8*T_Factory.distillationTime)/CCZ_distillationTime) #we need enough T1 factories to produce 8|T> states in the time it takes to make one CCZ state (5.5d_CCZ cycles)
        T1FactoryFootprint = T_Factory.qubitFootprint #The size of a level 1 T gate factory
        CCZFactoryFootprint = 3*6*d_CCZ**2 #The size of just the CCZ distillation part of the CCZ factory
        qubitFootprint = numT1Factories*T1FactoryFootprint + CCZFactoryFootprint #Total space of CCZ distillation (1 CCZdistillation fed by numT1Factories Tgate factories)
        outErrorRate = 28* (T_Factory.outErrorRates[QuantumGate.T])**2  #TODO: this is the out error rate if it is distillation limited (i.e. the code distance of the T and CCZ factories is high enough that it isn't the source of most error. However, it is possible that with low code distances, it does not get this good) Fix this to adjust error rate based on if the code distance is the bottleneck or if the distillation is the bottle neck.
        return cls(
            inStateCnts = {QuantumGate.H:15*numT1Factories}, #NOTE: just the CCZ portion takes in 8 |T> states but these take T factories to produce
            outStateCnts = {QuantumGate.CCZ:1},
            outErrorRates = {QuantumGate.CCZ:outErrorRate},
            distillationCycles = CCZ_distillationCycles,
            distillationTime = CCZ_distillationTime,
            qubitFootprint = qubitFootprint,
            codeDistance = d_CCZ,
            subFactories = [T_Factory], #TODO: technically there are numT1Factories, not just 1. I need a way to keep track of how many. Maybe make this a dictionary that is {Factory:cnt}?
        )
    
    """
        Catalyzed |CCZ> -> 2|T> factory based on paper 'Efficient magic state factories with a catalyzed |CCZ> -> 2|T> transformation'
        It takes in 15|T>, converts those to |CCZ>, then converts that to 2|T>
    """
    @classmethod
    def catalyzed2T_factory(cls, CCZ_factory: MagicFactory, d_2T:int) -> MagicFactory:
        distillationCycles = max(CCZ_factory.distillationCycles+1, 6.5)
        distillationTime = max(CCZ_factory.distillationTime+d_2T, 6.5 * d_2T) #The figure in the paper says its depth is 6.5d and I am guessing that is the distillation time since it is * d and also with No CCZ bottleneck so I am taking a max of the CCZ cycle time + d_2T cycle to get the math to work (CCZ factory with rate of 5.5d makes a 2T factory 6.5d 2T factory).
        qubitFootprint = CCZ_factory.qubitFootprint + (4*d_2T)**2
        outErrorRate = CCZ_factory.outErrorRates[QuantumGate.CCZ] #I think the T states produced have the same error rate as the CCZ states of the CCZ factory (TODO: figure out how this relates to code distance of the factory)
        
        return cls(
            inStateCnts = CCZ_factory.inStateCnts,
            outStateCnts = {QuantumGate.T:2},
            outErrorRates = {QuantumGate.T:outErrorRate},
            distillationCycles = distillationCycles,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint,
            codeDistance = d_2T,
            subFactories = [CCZ_factory],
        )
    
    """
        This is the square root T factory based on the paper 'Efficient magic state factories with a catalyzed |CCZ> -> 2|T> transformation'
        This uses T subfactories to produce 5 T states per round: 4 to implement logical AND, 1 to implement 2Theta gate (in this case 2Theta is a T gate),
    """
    @classmethod
    def sqrtT_factory(cls, T_Factory:MagicFactory, d:int) -> MagicFactory:
        numTFactories = math.ceil(5/T_Factory.outStateCnts[QuantumGate.T]) #Need enough T factories to produce 5 T states (1 for T gate and 4 for logical AND) per cycle
        qubitFootprint = 3*d**2 + numTFactories*T_Factory.qubitFootprint #the 3d^2 term comes from the fact that the circuit itself is 3 logical qubits.
        distillationTime = T_Factory.distillationTime #the bottleneck will likely be the CCZ factory outputs to be able to run the 3-qbit circuit
        distillationCycles = T_Factory.distillationCycles #same reasoning as distillationTime
        #Somehow account for the time to distill the first catalyst state (depends on if you just use synthelization (many T gates) or magically distill it (look at other paper for this. will need to add it as a factory)
        return cls(
            inStateCnts = {gate: count*numTFactories for gate,count in T_Factory.inStateCnts.items()}, #this is ignoring the 2 input |+> states that will turn into sqrt T states because we can directly feed in the qubits we want to apply the sqrt T gate to
            outStateCnts = {QuantumGate.sqrtT:2},
            outErrorRates = {QuantumGate.sqrtT:T_Factory.outErrorRates[QuantumGate.T]}, #TODO: this will be likely be worse than the input state. additionally the fidelity becomes worse as we run it (O(n)) until the catalyst is poisoned
            distillationCycles = distillationCycles,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint,
            codeDistance = d,
            subFactories = [T_Factory],
        )
    
    """
        Factory to produce a series of arbitrarily small rotations. Uses the generalized C2T factory from 'Efficient magic state factories with a catalyzed |CCZ>->2|T> transformation'
        Starts with a C2T factory which produces 2T states, one is output and one is fed into the sqrt(T) factory (M_3). This factory produces 2 sqrt(T) gates, one is ouput the next
        is fed into the next factory M_4 and so on until M_k. the M_k factory outputs both its states.
        an M_k factory produces phases of e^ipi(1/2^k). Thus a M_0=Z, M_1=S, M_2=T, M_3=sqrt(T),, M_4=4rt(T)...
        This factory outputs 1 of each state |M_n> for 2<=n<=k-1 and 2 |M_k> states
        
        Params:
            C2TFactory: the C2T factory used to produce the T states to run the M factories (and possibly also produce the initial catalyst)
            k: the finest grained rotation to produce (adding a phase of e^-ipi(1/2^k)
            d: the code distance used in the M part of the factories
            TODO: catalystFactories[] should be a list of factories that are used for the initial catalyst state so we can get fidelities and maybe determine better qubit footprint
    """
    @classmethod
    def catalyzed_Rz_factory(cls, T_Factory:MagicFactory, k:int, d:int) -> MagicFactory:
        if k < 2:
            raise ValueError(f"k value should be greater than 2 for catalyzed Rz Factory since k=1->S factory. Got k={k}")
        if k > 7:
            raise ValueError(f"currently the catalyzed RZ factory doesnt accept k values greater than 7. Got k={k}") #TODO: sometime fix this
        if QuantumGate.T not in T_Factory.getMagicStates():
            raise ValueError(f"T_Factory param must produce T gates")
        MfactoryFootprint = 3*d**2 #the M factories use 3 qubits each encoded at distance d^2
        numMfactories = k-2  #we dont include k=1 since that would be an S factory. Also dont include k=2 which is a T factory since we will use a normal T factory for that. the first M factory is a sqrt(T) factory (M_2) and so on for each k increase
        numTFactories = math.ceil((4*numMfactories+1)/T_Factory.outStateCnts[QuantumGate.T]) #each M factory needs 4 T states to apply the logical and gate within them. The additional 1 is for the T factory that applies the 2theta rotation for the sqrtT factory
        qubitFootprint = MfactoryFootprint * numMfactories + T_Factory.qubitFootprint * numTFactories
        distillationTime = T_Factory.distillationTime #I am assuming this will be the bottleneck, but there is also a startup period where we distill the catalysts we have to think about
        distillationCycles = T_Factory.distillationCycles #same assumption as w/ distillationTime
        
        #get the list of gates this factory produces and the dictionary of how many of each. NOTE: it produces 2 2^krtT states and 1 of each prior 2^xrtT states down to T gate
        rootGates = [QuantumGate.sqrtT, QuantumGate.rootT_4, QuantumGate.rootT_8, QuantumGate.rootT_16, QuantumGate.rootT_32]
        outStates = []
        outStateCnts = {}
        for i in range(0,k-3):
            outStateCnts[rootGates[i]] = 1
            outStates.append(rootGates[i])
        outStateCnts[rootGates[k-3]] = 2
        outStates.append(rootGates[k-3])

        #get the output error rate of each of the output rates
        #TODO: research what this would actually be (for the time being i am just setting it to the C2T output error rate). May have to do with catalyst fidelity so perhaps pass catalyst fidelity as param and we dont explain how catalyst is formed
        outErrorRates = {}
        for state in outStates:
            outErrorRates[state] = T_Factory.outErrorRates[QuantumGate.T]


        return cls(
            inStateCnts = {gate: count * numTFactories for gate,count in T_Factory.inStateCnts.items()},
            outStateCnts = outStateCnts,
            outErrorRates = outErrorRates,
            distillationCycles = distillationCycles,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint,
            codeDistance = d, #TODO: this is just for the M factories so not a good indicator
            subFactories = [T_Factory]
        )
    

    #TODO: implement factory based on the technique in the "Even more efficient magic state distillation by zero-level distillation"
    #TODO: other options include magic state cultivation: growing T states as cheap as CNOT gates paper (seems to be way better in space but a little worse in fidelity and time)
    






