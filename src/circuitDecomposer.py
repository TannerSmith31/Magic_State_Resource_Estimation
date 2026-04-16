from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit.circuit.library import RXGate, RYGate
from qiskit.quantum_info import Operator, Pauli
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from typing import Literal
from pygridsynth.gridsynth import gridsynth_gates, gridsynth_circuit
import mpmath
import numpy as np
from scipy.linalg import sqrtm
from scipy.stats import unitary_group
from scipy.spatial.transform import Rotation
from qiskit.synthesis import OneQubitEulerDecomposer
#from tensorflow_graphics.geometry.transformation.axis_angle import from_euler
import quaternionic
from math import cos, sqrt, inf, sin
from sympy import MatrixSymbol, pprint, solveset, Symbol
import sympy
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum import UnitaryOperator

from src.utils import QuantumGate, dagger, operatorNorm

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
		self.cApprox = 4 * sqrt(2)
		self.epsilon = {}

	def decomposeToGateset(self):
		names = get_standard_gate_name_mapping()
		self.options = self.basicApproximationHelper(6, [[]]) # TODO: Find a good numGates.
		self.matrixOptions = []
		for option in self.options:
			currMatrix = np.identity(2)
			for gate in option:
				gateMatrix = names[gate.name.lower()].to_matrix()
				currMatrix = np.matmul(currMatrix, gateMatrix)
				self.matrixOptions.append([currMatrix, option])
		# Use numpy matrices.
		#if 'T' in self.gateSet:
			#return self.decomposeToCliffordPlusT()
		#TODO: take the original circuit from this object and decompose it into the gateSet of this object

		for inst in self.originalCircuit.data:
			#Check if the instruction is already in self.gateSet first.

			U = inst.matrix
			n = 5
			self.epsilon[0] = 0.14
			for i in range(1, n + 1):
				#self.epsilon[i] = self.cApprox * self.epsilon[i - 1] ** (3/2)
				self.epsilon[i] = (self.cApprox ** 2 * self.epsilon[0]) ** (3/2) ** n / self.cApprox ** 2
			decomposedGate = self.solovayKitaev(U, n)

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
					newCombination = list(combination)
					newCombination.append(gate)
					newCombinations.append(newCombination)
			return self.basicApproximationHelper(numGates - 1, newCombinations)
	
	def basicApproximation(self, U):
		names = get_standard_gate_name_mapping()
		currentOption = None
		minOperatorNorm = inf
		for option in self.matrixOptions:
			
			optionOperatorNorm = operatorNorm(U, option[0])
			if abs(optionOperatorNorm) < abs(minOperatorNorm):
				minOperatorNorm = optionOperatorNorm
				currentOption = option

		#self.decomposedCircuit.append(currentOption[1])
		return currentOption[0]
	
	def gcDecompose(self, inputMatrix, n):
		done = False
		cgc = 1/sqrt(2)
		
		bound = cgc * sqrt(self.decompositionError)
		identity = np.identity(2)
		v = None
		w = None
		euler = OneQubitEulerDecomposer().angles(unitary=inputMatrix)
		quat = quaternionic.array.from_euler_angles(euler)
		axis = quat.to_axis_angle
		theta = np.linalg.norm(axis)
		leftSide = sin(theta / 2)
		# 0 = (1 - cos(phi)) * sqrt(1 - (1/8) * (3 - 4 * cos(phi) + cos(2 * phi))) - leftSide
		x = Symbol('x')
		# A bug makes this sometimes an empty set.
		# This line confirmed to work.
		phis = solveset(((1 - sympy.cos(x)) * sympy.sqrt(1 - (1/8) * (3 - 4 * sympy.cos(x) + sympy.cos(2 * x))) - leftSide), x, sympy.Reals)
		if phis == sympy.EmptySet:
			phis = solveset(((1 - sympy.cos(x)) * sympy.sqrt(1 - (1/8) * (3 - 4 * sympy.cos(x) + sympy.cos(2 * x))) - leftSide) ** 2, x, sympy.Reals)
			if phis == sympy.EmptySet:
				phis = solveset(((1 - sympy.cos(x)) * sympy.sqrt(1 - (1/8) * (3 - 4 * sympy.cos(x) + sympy.cos(2 * x))) - leftSide) ** 3, x, sympy.Reals)


		vSymbol = MatrixSymbol('v', 2, 2)
		wSymbol = MatrixSymbol('w', 2, 2)

		negatedInput = sympy.Matrix(inputMatrix * -1)

		#vs, ws = solveset(sympy.MatAdd(negatedInput, sympy.MatMul(vSymbol, wSymbol, Dagger(vSymbol), Dagger(wSymbol))), sympy.FiniteSet(vSymbol, wSymbol), UnitaryOperator)

		pprint(phis)
		iterable = iter(phis)
		quat = quat.ndarray
		while not done:
			phi = next(iterable)
			#print(sin(theta / 2), (1 - cos(phi)) * sqrt(1 - (1/8) * (3 - 4 * cos(phi) + cos(2 * phi))), 2 * sin(phi / 2) ** 2 * sqrt(1 - sin(phi/2) ** 4))
			v = RXGate(float(phi)).to_matrix()
			w = RYGate(float(phi)).to_matrix()
			#print(operatorNorm(identity, v), sqrt(self.epsilon[n]/2))
			if abs(operatorNorm(identity, v)) < sqrt(self.epsilon[n]/2):
				done = True
		return v, w

	# function Solovay-Kitaev(Gate U , depth n)
	def solovayKitaev(self, U , n):
		#print("I: ", np.matmul(U, dagger(U)))
		# if (n == 0)
		if n == 0:
			# Return Basic Approximation to U
			print('SK: ', 0, operatorNorm(U, self.basicApproximation(U)))
			return self.basicApproximation(U)
		# else
		else:
			# Set Un−1 = Solovay-Kitaev(U, n − 1)
			UNMinusOne = self.solovayKitaev(U, n - 1)
			# Set V , W = GC-Decompose(U U^†_{n − 1})
			print(np.matmul(U, dagger(UNMinusOne)))
			V, W = self.gcDecompose(np.matmul(U, dagger(UNMinusOne)), n)
			# Set Vn−1 = Solovay-Kitaev(V ,n − 1)
			VNMinusOne = self.solovayKitaev(V, n - 1)
			# Set Wn−1 = Solovay-Kitaev(W ,n − 1)
			WNMinusOne = self.solovayKitaev(W, n - 1)
			# Return Un = Vn−1Wn−1V †  n−1W †  n−1Un−1;
			print('SK: ', n, operatorNorm(U, np.matmul(np.matmul(np.matmul(np.matmul(VNMinusOne, WNMinusOne), dagger(VNMinusOne)), dagger(WNMinusOne)), UNMinusOne)))
			return np.matmul(np.matmul(np.matmul(np.matmul(VNMinusOne, WNMinusOne), dagger(VNMinusOne)), dagger(WNMinusOne)), UNMinusOne)
	
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
