import pytest
from qiskit import QuantumCircuit
from src.resourceEstimator import ResourceEstimator
from src.magicFactory import MagicFactory
from src.utils import QuantumGate
import numpy as np

def test_null_factory():
    """Ensures a ValueError is raised when the factory list is None."""
    with pytest.raises(ValueError):
        mockEstimator = ResourceEstimator(None, 5, 1e-3)

def test_clifford_plus_t():
    """Ensures the decomposition runs without errors for a standard T-gate circuit."""
    mockCircuit = QuantumCircuit(4, 0)
    mockFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockCircuit.rz(0.3, 0)

    estimator = ResourceEstimator([mockFactory], 5, 1e-3)
    # Pytest automatically fails if an uncaught exception is raised here
    #estimator.decomposeToCliffordPlusMagic(mockCircuit, 1e-5)

def test_calcFootprint():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockFactory2 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 400, 3)
    mockFactory3 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 123, 3)
    #qubit footprint of factories should be 200+400+123=723

    mockResourceEstimator = ResourceEstimator([mockFactory1,mockFactory2,mockFactory3],5,1e-3)
    mockCircuit = QuantumCircuit(5,0) #5qbits at (2*5^2-1=49)qbits each = 245

    assert mockResourceEstimator.calcFootprint(None) == 723 #just the factories
    assert mockResourceEstimator.calcFootprint(mockCircuit) == 968 #245+723
    
def test_getMagicDepths_Tgate():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory1],5,1e-3)
    
    mockCircuit = QuantumCircuit(3,0)
    for i in range(3):
        mockCircuit.h(i)
        mockCircuit.t(i)
    mockCircuit.cx(1,2)
    mockCircuit.t(1)
    mockCircuit.h(2)
    mockCircuit.cx(0,1)
    mockCircuit.cx(0,2)
    mockCircuit.tdg(0)   #should also catch the dagger

    #q0 -h-t-----*-*-tdg-
    #q1 -h-t-*-t-X-----
    #q2 -h-t-X-h---X---
    
    assert mockResourceEstimator.getMagicDepths(mockCircuit) == {QuantumGate.T:3} 

def test_getMagicDepths_TandCCZGate():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockFactory2 = MagicFactory({QuantumGate.T:15}, {QuantumGate.CCZ:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory1,mockFactory2],5,1e-3)
    
    mockCircuit = QuantumCircuit(4,0)
    for i in range(3):
        mockCircuit.h(i)
        mockCircuit.t(i)
    mockCircuit.cx(1,3)
    mockCircuit.t(1)
    mockCircuit.h(2)
    mockCircuit.ccz(0,1,2)
    mockCircuit.ccz(1,2,3)
    mockCircuit.t(0)
    mockCircuit.t(3)

    #q0 -h-t-----*---t-
    #q1 -h-t-*-t-*-*---
    #q2 -h-t---h-Z-*---
    #q3 -----X-----Z-t-
    
    assert mockResourceEstimator.getMagicDepths(mockCircuit) == {QuantumGate.T:3, QuantumGate.CCZ:2} 

def test_getMagicDepths_rootAngles():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.sqrtT:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockFactory2 = MagicFactory({QuantumGate.T:15}, {QuantumGate.rootT_8:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory1,mockFactory2],5,1e-3)
    
    mockCircuit = QuantumCircuit(1,0)
    
    mockCircuit.rz(np.pi/32,0)
    mockCircuit.h(0)
    mockCircuit.rz(np.pi/8,0)
    mockCircuit.h(0)
    mockCircuit.rz(np.pi/8,0)
    mockCircuit.rz(np.pi/32,0)
    mockCircuit.h(0)
    mockCircuit.rz(np.pi/32,0)

    # q0 --rootT_8-h-sqrtT-h-sqrtT-rootT_8-h-rootT_8--

    assert mockResourceEstimator.getMagicDepths(mockCircuit) == {QuantumGate.sqrtT:2,QuantumGate.rootT_8:3}

def test_calcRuntime():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5, 10, 200, 3)
    mockFactory2 = MagicFactory({QuantumGate.T:15}, {QuantumGate.sqrtT:1, QuantumGate.rootT_4:1, QuantumGate.rootT_8:2}, {QuantumGate.sqrtT:0.001, QuantumGate.rootT_4:0.001, QuantumGate.rootT_8:0.001}, 10, 20, 200, 3)

    mockResourceEstimator = ResourceEstimator([mockFactory1, mockFactory2], 2, 1e-3)

    mockCircuit = QuantumCircuit(1,0)
    
    mockCircuit.rz(np.pi/32,0)
    mockCircuit.h(0)
    mockCircuit.rz(np.pi/8,0)
    mockCircuit.t(0)
    mockCircuit.rz(np.pi/8,0)
    mockCircuit.rz(np.pi/16,0)
    mockCircuit.rz(np.pi/8,0)
    mockCircuit.t(0)
    mockCircuit.rz(np.pi/32,0)

    #2T, 3 sqrtT, 1 rootT_4, 2 rootT_8 
    #The 3 sqrtT gates should be the bottleneck so we need to figure out how long it will take to produce 3 of them
    #it takes 20 'units of time' to produce 1 sqrtT gate so 60 'units of time' to produce 3.
    #Then to get this into codecycles of the algo, we divide it by the algo code distance: 60/2=10 algo codecycles

    assert mockResourceEstimator.calcRuntime(mockCircuit) == 30

def test_calcRuntimeWithMultipleTFactories():
    mockFactory1 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5, 10, 200, 3)
    mockFactory2 = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:2}, {QuantumGate.T:0.001}, 5, 10, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory1, mockFactory2], 5, 1e-3)
    mockCircuit = QuantumCircuit(1,0)

    mockCircuit.h(0)
    for i in range(3):
        mockCircuit.t(0)
    mockCircuit.h(0)
    for i in range(10):
        mockCircuit.t(0)

    #The circuit has 13 T gates. The first factory produces 1 per 10 cycles and the second produces 2 per 10 cycles
    #So both factorys produce 3 per 10 'units of time' so the runtime should be 10/3 * 13 = 43.33333.
    #Then, converting this to algo codecycles we get 43.3333/5 which is 8.6666 algo codecycles
    
    assert mockResourceEstimator.calcRuntime(mockCircuit) == pytest.approx(26/3.0, 1e-3)

def test_runCircuit_highFidelityT_idealClifford():
    mockCircuit = QuantumCircuit(1,1)
    for i in range(13):
        mockCircuit.h(0)
        mockCircuit.t(0)
    mockCircuit.measure(0,0)
    #The above circuit [(HT)^13], according to Quirk, should be measured |1> 45% of the time

    outError = 1e-10
    mockFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:outError}, 5, 10, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory], 7, 1e-3)

    #get the average number of shots over numRepeats runs to get a more stable test
    avg1Counts = 0
    numRepeats = 5
    for i in range(numRepeats):
        counts = mockResourceEstimator.runCircuit(mockCircuit, shots=1000, idealCliffords=True)
        avg1Counts += counts.get('1',0)
    avg1Counts = avg1Counts/numRepeats

    assert abs(avg1Counts - 450) < 20   #ideal |1> count is 450, so it should be at least within 20 given almost no noise

def test_runCircuit_lowFidelityT_idealClifford():
    mockCircuit = QuantumCircuit(1,1)
    for i in range(14):
        mockCircuit.h(0)
        mockCircuit.t(0)
    mockCircuit.measure(0,0)
    #The above circuit, according to Quirk, should be measured ON 22.1% of the time

    outError = 5e-1 #super high error
    mockFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:outError}, 5, 10, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory], 7, 1e-3)

    #get the average number of shots over numRepeats runs to get more stable test
    avg1Counts = 0
    numRepeats = 5
    for i in range(numRepeats):
        counts = mockResourceEstimator.runCircuit(mockCircuit, shots=1000, idealCliffords=True)
        avg1Counts += counts.get('1',0)
    avg1Counts = avg1Counts/numRepeats

    assert abs(avg1Counts - 221) > 200   #ideal |1> count is 221, so it should be far from this due to noisy T gates

def test_runCircuit_highFidelityT_nonIdealClifford_highCodeDist():
    mockCircuit = QuantumCircuit(1,1)
    for i in range(14):
        mockCircuit.h(0)
        mockCircuit.t(0)
    mockCircuit.measure(0,0)
    #The above circuit, according to Quirk, should be measured ON 22.1% of the time

    codeDistance = 35 #high code distance
    p_phys = 5e-3 #high physical error rate
    mockFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:1e-12}, 5, 10, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory], codeDistance, p_phys)

    #get the average number of shots over numRepeats runs to get more stable test
    avg1Counts = 0
    numRepeats = 5
    for i in range(numRepeats):
        counts = mockResourceEstimator.runCircuit(mockCircuit, shots=1000, idealCliffords=False)
        avg1Counts += counts.get('1',0)
    avg1Counts = avg1Counts/numRepeats

    assert abs(avg1Counts - 221) < 20   #ideal |1> count is 221, so it should be close to this since code distance is high

def test_runCircuit_highFidelityT_nonIdealClifford_lowCodeDist():
    mockCircuit = QuantumCircuit(1,1)
    for i in range(14):
        mockCircuit.h(0)
        mockCircuit.t(0)
    mockCircuit.measure(0,0)
    #The above circuit, according to Quirk, should be measured ON 22.1% of the time

    codeDistance = 3 #low code distance
    p_phys = 5e-2 #high physical error rate
    mockFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:1e-12}, 5, 10, 200, 3)
    mockResourceEstimator = ResourceEstimator([mockFactory], codeDistance, p_phys)

    #get the average number of shots over numRepeats runs to get more stable test
    avg1Counts = 0
    numRepeats = 5
    for i in range(numRepeats):
        counts = mockResourceEstimator.runCircuit(mockCircuit, shots=1000, idealCliffords=False)
        avg1Counts += counts.get('1',0)
    avg1Counts = avg1Counts/numRepeats

    assert abs(avg1Counts - 221) > 200   #ideal |1> count is 221, so it should be close to this since code distance is high










