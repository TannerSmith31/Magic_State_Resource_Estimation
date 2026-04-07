import pytest
from src.utils import QuantumGate
from src.magicFactory import MagicFactory

def test_default_constructor():
    mockMagicFactory = MagicFactory({QuantumGate.T:15}, {QuantumGate.T:1}, {QuantumGate.T:0.001}, 5.5, 16.5, 200, 3)

    assert mockMagicFactory.getMagicStates() == [QuantumGate.T]
    assert mockMagicFactory.inStateCnts == {QuantumGate.T:15}
    assert mockMagicFactory.outStateCnts == {QuantumGate.T:1}
    assert mockMagicFactory.outErrorRates == {QuantumGate.T:0.001}
    assert mockMagicFactory.distillationCycles == 5.5
    assert mockMagicFactory.distillationTime == 16.5
    assert mockMagicFactory.qubitFootprint == 200
    assert mockMagicFactory.codeDistance == 3

def test_T_factory_15_to_1():
    mockMagicFactory = MagicFactory.T_factory_15_to_1(7,3,3,1e-4) #This is the first protocol listed in Table 1 of 'Not as Costly' paper 

    assert mockMagicFactory.getMagicStates() == [QuantumGate.T]
    assert mockMagicFactory.inStateCnts == {QuantumGate.H:5}
    assert mockMagicFactory.outStateCnts == {QuantumGate.T:1}
    assert mockMagicFactory.outErrorRates == pytest.approx({QuantumGate.T:4.4*(10**(-8))}, 1e-08)
    assert mockMagicFactory.distillationCycles == pytest.approx(18.1, 1e-3)
    assert mockMagicFactory.distillationTime == pytest.approx(126.7, 1e-3)
    assert mockMagicFactory.qubitFootprint == 810
    assert mockMagicFactory.codeDistance == 7

def test_T_factory_15_to_1_Old():
    mockMagicFactory = MagicFactory.T_factory_15_to_1_Old(7,1e-4)

    assert mockMagicFactory.getMagicStates() == [QuantumGate.T]
    assert mockMagicFactory.inStateCnts == {QuantumGate.H:15}
    assert mockMagicFactory.outStateCnts == {QuantumGate.T:1}
    assert mockMagicFactory.outErrorRates == pytest.approx({QuantumGate.T:35e-12}, 1e-13)
    assert mockMagicFactory.distillationCycles == 6.5
    assert mockMagicFactory.distillationTime == 45.5
    assert mockMagicFactory.qubitFootprint == 1568
    assert mockMagicFactory.codeDistance == 7

def test_CCZ_factory():
    d_T = 7
    d_CCZ = 2*d_T
    mockTFactory = MagicFactory.T_factory_15_to_1_Old(d_T,1e-3)
    mockCCZFactory = MagicFactory.CCZ_factory(mockTFactory, d_CCZ)
    assert mockCCZFactory.getMagicStates() == [QuantumGate.CCZ]
    assert mockCCZFactory.inStateCnts == {QuantumGate.H:15*5} #should have created 5 T factories and I set the TFactory as the old one that takes 15 in
    assert mockCCZFactory.outStateCnts == {QuantumGate.CCZ:1}
    assert mockCCZFactory.outErrorRates == pytest.approx({QuantumGate.CCZ:3.43e-14}, 1e-15)
    assert mockCCZFactory.distillationCycles == 5.5
    assert mockCCZFactory.distillationTime == 77
    assert mockCCZFactory.qubitFootprint == mockTFactory.qubitFootprint * 5 + 3528
    assert mockCCZFactory.codeDistance == 14
    assert mockCCZFactory.subFactories == [mockTFactory]

def test_catalyzed2T_factory():
    mockCCZFactory = MagicFactory({QuantumGate.H:8},{QuantumGate.CCZ:1},{QuantumGate.CCZ:1e-9},5.5,77,200,14,None)
    #NOTE: the above mock CCZ factory has no T subfactory
    mockC2TFactory = MagicFactory.catalyzed2T_factory(mockCCZFactory, 14)

    assert mockC2TFactory.getMagicStates() == [QuantumGate.T]
    assert mockC2TFactory.inStateCnts == {QuantumGate.H:8}
    assert mockC2TFactory.outStateCnts == {QuantumGate.T:2}
    assert mockC2TFactory.outErrorRates == pytest.approx({QuantumGate.T:1e-9}, 1e-10)
    assert mockC2TFactory.distillationCycles == 6.5
    assert mockC2TFactory.distillationTime == 91
    assert mockC2TFactory.qubitFootprint == 3336 #TODO: this seems like a lot. I think something is wrong with my formulas
    assert mockC2TFactory.codeDistance == 14
    assert mockC2TFactory.subFactories == [mockCCZFactory]

def test_sqrtT_factory():
    mockTFactory = MagicFactory({QuantumGate.H:8},{QuantumGate.T:2},{QuantumGate.T:1e-9}, 8.5,59.5, 200,7)
    mockSqrtTFactory = MagicFactory.sqrtT_factory(mockTFactory,7)

    assert mockSqrtTFactory.getMagicStates() == [QuantumGate.sqrtT]
    assert mockSqrtTFactory.inStateCnts == {QuantumGate.H:24}  #8x3 Since each mock TFactory produces 2 T states, it should take 3 factories each taking mockTFactor.inStateCnt inputs (8)
    assert mockSqrtTFactory.outStateCnts == {QuantumGate.sqrtT:2}
    assert mockSqrtTFactory.outErrorRates == pytest.approx({QuantumGate.sqrtT:1e-9}, 1e-10)
    assert mockSqrtTFactory.distillationCycles == 8.5
    assert mockSqrtTFactory.distillationTime == 59.5
    assert mockSqrtTFactory.qubitFootprint == 747 
    assert mockSqrtTFactory.codeDistance == 7
    assert mockSqrtTFactory.subFactories == [mockTFactory]

def test_catalyzedRz_fatory():
    mockTFactory = MagicFactory({QuantumGate.H:8},{QuantumGate.T:2},{QuantumGate.T:1e-9}, 8.5,59.5, 200,7)
    mockRZFactory = MagicFactory.catalyzed_Rz_factory(mockTFactory,5,7)

    assert mockRZFactory.getMagicStates() == [QuantumGate.sqrtT, QuantumGate.rootT_4, QuantumGate.rootT_8]
    assert mockRZFactory.inStateCnts == {QuantumGate.H:56}  #should have taken in 4*3+1 = 13 mockTFactories each with 8 input states
    assert mockRZFactory.outStateCnts == {QuantumGate.sqrtT:1, QuantumGate.rootT_4:1, QuantumGate.rootT_8:2}
    assert mockRZFactory.outErrorRates == pytest.approx({QuantumGate.sqrtT:1e-9,QuantumGate.rootT_4:1e-9,QuantumGate.rootT_8:1e-9}, 1e-10)
    assert mockRZFactory.distillationCycles == 8.5
    assert mockRZFactory.distillationTime == 59.5
    assert mockRZFactory.qubitFootprint == 1841
    assert mockRZFactory.codeDistance == 7
    assert mockRZFactory.subFactories == [mockTFactory]
