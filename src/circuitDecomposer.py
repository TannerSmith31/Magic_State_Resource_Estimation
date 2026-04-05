import math

from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit.quantum_info import Operator, Pauli
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from typing import Literal
from pygridsynth.gridsynth import gridsynth_gates, gridsynth_circuit
from utils import QuantumGate, dagger, operatorNorm
import mpmath
import numpy as np
from scipy.linalg import sqrtm
from scipy.stats import unitary_group
from scipy.spatial.transform import Rotation

class CircuitDecomposer:
	gateSet: list[QuantumGate]        #List of gates that we will decompose the arbitrary circuit into
	gateSet2x2: list[QuantumGate]
	decompositionError: float         #tolerable error for each gate when decomposing a circuit
	originalCircuit: QuantumCircuit   #the original non-decomposed circuit comprised of arbitrary gates
	decomposedCircuit: QuantumCircuit #the decomposed circuit comprised of only gates in our gateSet
	
	def __init__(self, gateSet:list[QuantumGate], decompositionError:float, originalCircuit:QuantumCircuit):
		self.gateSet = gateSet
		self.decompositionError = decompositionError
		self.originalCircuit = originalCircuit
		self.decomposedCircuit = QuantumCircuit(self.originalCircuit.num_qubits, self.originalCircuit.num_clbits)
		self.gateSet2x2 = []
		for gate in gateSet:
			if QuantumGate(gate).is_2x2:
				self.gateSet2x2.append(gate)

	def decomposeToGateset(self):
		self.options = self.basicApproximationHelper(3, [[]]) # TODO: Find a good numGates.
		# Use numpy matrices.
		#if 'T' in self.gateSet:
			#return self.decomposeToCliffordPlusT()
		#TODO: take the original circuit from this object and decompose it into the gateSet of this object

		for inst in self.originalCircuit.data:
			#Check if the instruction is already in self.gateSet first.

			U = inst.matrix
			decomposedGate = self.solovayKitaev(U, 5)

		#TODO: set the decomposedCircuit to the one we just created and then return the decomposed circuit
		return "TODO: IMPLEMENT decomposeToGateset function"
	
	def basicApproximationHelper(self, numGates, currCombinations):
		if numGates == 0:
			return currCombinations
		else:
			newCombinations = []
			for combination in currCombinations:
				newCombinations.append(combination)
				for gate in self.gateSet2x2:
					newCombination = combination
					newCombination.append(gate)
					newCombinations.append(newCombination)
			return self.basicApproximationHelper(numGates - 1, newCombinations)
	
	def basicApproximation(self, U):
		names = get_standard_gate_name_mapping()
		currentOption = None
		minOperatorNorm = math.inf
		for option in self.options:
			currMatrix = np.identity(2)
			for gate in option:
				gateMatrix = names[gate.name.lower()].to_matrix()
				currMatrix = np.matmul(currMatrix, gateMatrix)
			
			optionOperatorNorm = operatorNorm(U, currMatrix)
			if optionOperatorNorm < minOperatorNorm:
				minOperatorNorm = optionOperatorNorm
				currentOption = currMatrix
			
		return currentOption
	
	def gcDecompose(self, inputMatrix):
		done = False
		biggerMatrix = [
			[inputMatrix[0][0], inputMatrix[0][1], 0],
			[inputMatrix[1][0], inputMatrix[1][1], 0],
			[0, 0, 1]]
		theta = Rotation.from_matrix(biggerMatrix).as_euler('zyx')[0]
		cgc = 1/math.sqrt(2)
		bound = cgc * math.sqrt(self.decompositionError)
		identity = np.identity(2)
		v = None
		w = None
		while not done:
			v = unitary_group.rvs(2)
			w = unitary_group.rvs(2)
			if operatorNorm(identity, v) < bound:
				done = True
		return v, w

	# function Solovay-Kitaev(Gate U , depth n)
	def solovayKitaev(self, U , n):
		# if (n == 0)
		if n == 0:
			# Return Basic Approximation to U
			return self.basicApproximation(U)
		# else
		else:
			# Set Un−1 = Solovay-Kitaev(U, n − 1)
			UNMinusOne = self.solovayKitaev(U, n - 1)
			# Set V , W = GC-Decompose(U U^†_{n − 1})
			#print(np.matmul(U, dagger(UNMinusOne)))
			#print(np.matmul(dagger(UNMinusOne), U))
			V, W = self.gcDecompose(np.matmul(U, dagger(UNMinusOne)))
			# Set Vn−1 = Solovay-Kitaev(V ,n − 1)
			VNMinusOne = self.solovayKitaev(V, n - 1)
			# Set Wn−1 = Solovay-Kitaev(W ,n − 1)
			WNMinusOne = self.solovayKitaev(W, n - 1)
			# Return Un = Vn−1Wn−1V †  n−1W †  n−1Un−1;
			return np.dot(np.dot(np.dot(np.dot(VNMinusOne, WNMinusOne), dagger(VNMinusOne)), dagger(WNMinusOne)), UNMinusOne)
	
	def decomposeToCliffordPlusT(self):
		mpmath.mp.dps = 128
		epsilon = mpmath.mpf("1e-10")

		for inst in self.originalCircuit.data:
			if inst.name == 'rz':
				theta = float(inst.params[0])
				circuit = gridsynth_circuit(mpmath.mpf(theta), epsilon)
				#print(circuit)

				for gate in circuit:
					string = gate.to_simple_str()
					if string == 'S':
						self.decomposedCircuit.s(gate.target_qubit)
					if string == 'H':
						self.decomposedCircuit.h(gate.target_qubit)
					if string == 'T':
						self.decomposedCircuit.t(gate.target_qubit)
					if string == 'X':
						# Printing the circuit shows this as an SX gate, but its simple string is X.  Not sure which is correct.
						self.decomposedCircuit.sx(gate.target_qubit)
					# if string == 'W':
						# Qiskit does not appear to have W as an option.

					#print(self.decomposedCircuit.draw('text'))

				# Not Sure why this is causing an error.
				# print(trasyn.synthesize(target_unitary=theta, nonclifford_budget=100))

		# Might use SK instead for consistency of comparison.
		return self.decomposedCircuit
