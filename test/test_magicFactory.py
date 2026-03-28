import pytest
from src.utils import QuantumGate
from src.magicFactory import MagicFactory

def test_default_constructor():
    mock_magicFactory = MagicFactory(QuantumGate.T, 15, 1, 0.001, 5.5, 25)

    assert mock_magicFactory.gate == QuantumGate.T
    assert mock_magicFactory.inputStateCnt == 15
    assert mock_magicFactory.outputStateCnt == 1
    assert mock_magicFactory.distillationTime == 5.5
    assert mock_magicFactory.qubitFootprint == 25

#TODO: test CZZ factory where I pass in a T factory based on the one int the CCZ->2T paper and it should calculate the number of factories needed to be 5 if the code distance of the T factories is half that of the CCZ factory