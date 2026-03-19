from resourceEstimator import ResourceEstimator
from qiskit import QuantumCircuit
from magicFactory import MagicFactory

# Test the null value errors for decomposeToCliffordPlusMagic().
def testNullCircuit():
	try:
		factory = MagicFactory("", 0, 0, 0, 0, 0)
		estimator = ResourceEstimator(factory, None)
		estimator.decomposeToCliffordPlusMagic()
	except ValueError:
		pass
	else:
		raise Exception("testNullCircuit() failed.")

def testNullFactory():
	try:
		circuit = QuantumCircuit(2, 0)
		estimator = ResourceEstimator(None, circuit)
		estimator.decomposeToCliffordPlusMagic()
	except ValueError:
		pass
	else:
		raise Exception("testNullFactory() failed.")

testNullCircuit()
testNullFactory()