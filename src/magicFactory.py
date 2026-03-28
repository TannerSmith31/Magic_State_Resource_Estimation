from __future__ import annotations  #This allows me to type-hint something as a MagicFactory in a param to a function in the class definition.
import math
from src.utils import calcLER, calcProbErr_X_Z, QuantumGate

class MagicFactory:
    gate:str            #gate being distilled (T, CCZ, ...)
    inputStateCnt:int   #number of states input into the factor to be distilled
    outputStateCnt:int  #number of magic states output by the factory
    outErrorRate:float   #error rate of the magic states produced by the factory
    distillationTime:float   #number of cycles to run a full distillation
    qubitFootprint:int       #number of physical qubits required for the factory

    def __init__(self, gate:QuantumGate, inputStateCnt:int, outputStateCnt:int, outErrorRate:float, distillationTime:float, qubitFootprint:int):
        self.gate = gate
        self.inputStateCnt = inputStateCnt
        self.outputStateCnt = outputStateCnt
        self.outErrorRate = outErrorRate
        self.distillationTime = distillationTime
        self.qubitFootprint = qubitFootprint


    """
        T factory from paper "Magic State Distillation: Not as Costly as You Think" by Daniel Litinski
            d_x: x code distance
            d_z: z code distance
            d_m: number of code cycles used in lattice surgery
            p_phys: error rate of the physical qubits
        NOTE: this factory takes in |+> qubits and outputs |T> magic states   TODO: double check this is the case
    """
    @classmethod
    def T_factory_15_to_1(cls, d_x:int, d_z:int, d_m:int, p_phys:float):

        #TODO: FIGURE OUT HOW THEY CALCULATE outErrorRate and p_fail SO I DONT HAVE TO HARD CODE THE EXAMPLES HERE
        p_fail = 0   #the probability the distilation protocol fails
        outErrorRate = 0    #error rate of the produced magic state causing a faulty rotation
        if (d_x==7 and d_z == 3 and d_m ==3 and p_phys == 10**(-4)):
            p_fail = 0.005524
            outErrorRate = 10**(-8)
        elif (d_x==9 and d_z==3 and d_z ==3 and p_phys == 10**(-4)):
            p_fail = 0.005524
            outErrorRate = 9.3*10**(-10)
        elif (d_x==11 and d_z==5 and d_z == 5 and p_phys == 10**(-4)):
            p_fail = 0
            outErrorRate = 1.9 * 10**(-11)
        else:
            print("WARNING: unknown d_x, d_z, d_m, p_phys combo for 15 to 1 factory")
            print("setting p_fail to 10^-3 and outErrorRate = p_phys^((d_x+1)/4)")
            p_fail = 10**(-3)
            outErrorRate = p_phys**((d_x+1)/4) # This seems to approximate the error rates given in the 'Not as Costly' paper fairly well
        
        qubitFootprint =  2*(d_x + 4*d_z) * 3*d_x + 4*d_m #This equation appears in section 3 of the 'not as costly' paper
        distillationTime = 6 * d_m / (1-p_fail)           #This equation appears in section 3 of the 'not as costly paper

        return cls(
            gate = QuantumGate.T,
            inputStateCnt = 15,
            outputStateCnt = 1,
            outErrorRate = outErrorRate,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint,
        )
    
    """
        15 to 1 T factory introduced in 'Low Overhead Quantum Computing with Lattice Surgery'. It is a little more space costly than the 15 to 1 factory
        from the 'Not as costly as you think' paper but provides better output fidelity (according to the equations).
            d: code distance used to encode logical qubits
            p_in: error rate of the states going into the distillation (this is the physical error rate if we are making a level 1 factory)
        NOTE: This factory takes in noisy |T> magic states and outputs cleaner |T> magic states
    """
    @classmethod
    def T_factory_15_to_1_Old(cls, d, p_in):
        
        qubitFootprint = (4*d) * (8*d)
        numCycles = 6.5*d  #I got this eq from the paper this factory is from under section X. Distillation
        outErrorRate = 35 * p_in**3 #assuming that the input of the factory is p_in TODO: this is probably distillation limited and doesnt relate to surface code size

        return cls(
            gate = QuantumGate.T,
            inputStateCnt = 15,
            outputStateCnt = 1,
            qubitFootprint = qubitFootprint,
            outErrorRate = outErrorRate,
            distillationTime = numCycles
        )
    
    """
        CCZ factory based on the paper 'Efficient magic state factories with a catalyzed |CCZ> -> 2|T> transformation'
            T_Factory: The factory/protocol that is generating the T states to be used in the generation of the CCZ state
                NOTE: this must be a T factory. Also, the paper uses T factories that have half the code distance as the CCZ part of the factory
            d_CZZ is the code distance used for the CCZ distillation that distills the |T1> states into a CCZ state
    """
    @classmethod
    def CCZ_factory(cls, T_Factory: MagicFactory, d_CCZ: int):
        
        if T_Factory.gate != QuantumGate.T:  #CCZ factory works by using T gates distilled from T factories
            raise ValueError(f'CCZ_factory param T_Factory must be a T gate factory but was a {T_Factory.gate} gate factory')
        
        CCZ_distillationTime = 5.5 * d_CCZ #it takes 10-11 cycles to produce 2 CCZ states when overlapped so roughly 5.5d cycles per state
        numT1Factories = math.ceil((8*T_Factory.distillationTime)/CCZ_distillationTime) #we need enough T1 factories to produce 8|T> states in the time it takes to make one CCZ state (5.5d_CCZ cycles)
        T1FactoryFootprint = T_Factory.qubitFootprint #The size of a level 1 T gate factory
        CCZFactoryFootprint = 3*6*d_CCZ #The size of just the CCZ distillation part of the CCZ factory
        qubitFootprint = numT1Factories*T1FactoryFootprint + CCZFactoryFootprint #Total space of CCZ distillation (1 CCZdistillation fed by numT1Factories Tgate factories)
        outErrorRate = 28* (T_Factory.outErrorRate)**2  #TODO: this is the out error rate if it is distillation limited (i.e. the code distance of the T and CCZ factories is high enough that it isn't the source of most error. However, it is possible that with low code distances, it does not get this good) Fix this to adjust error rate based on if the code distance is the bottleneck or if the distillation is the bottle neck.
        return cls(
            gate = QuantumGate.CCZ,
            inputStateCnt = 15,
            outputStateCnt = 1,
            outErrorRate = outErrorRate,
            distillationTime = CCZ_distillationTime,
            qubitFootprint = qubitFootprint,
        )
    
    """
        Catalyzed |CCZ> -> 2|T> factory based on paper 'Efficient magic state factories with a catalyzed |CCZ> -> 2|T> transformation'
        It takes in 15|T>, converts those to |CCZ>, then converts that to 2|T>
    """
    @classmethod
    def catalyzed_CCZ_to_2T_factory(cls, CCZ_Factory: MagicFactory, d_T:int):
        distillationTime = 6.5 * d_T   #I got this from the figure in the paper, but it may assume no bottleneck in the L1 T or CCZ factories
        qubitFootprint = CCZ_Factory.qubitFootprint + (4*d_T)**2
        outErrorRate = CCZ_Factory.outErrorRate #I think the T states produced have the same error rate as the CCZ states of the CCZ factory (TODO: figure out how this relates to code distance of the factory)
        
        return cls(
            gate = QuantumGate.T,
            inputStateCnt = 15,
            outputStateCnt = 2,
            outErrorRate = outErrorRate,
            distillationTime = distillationTime,
            qubitFootprint = qubitFootprint
        )
    
    """
        Factory to produce sqrt T gates.
    """
    @classmethod
    def sqrtT_factory(cls):
        #TODO: implement factory
        return
    

    """
        Factory based on the technique used in "Even more efficient magic state distillation by zero-level distillation" (2024)
    """
    @classmethod
    def zeroLevelDistillation_factory(cls):
        #TODO: implement factory


        #errorRate = 100 *(p)^2   #this was given in the paper
        return
    






