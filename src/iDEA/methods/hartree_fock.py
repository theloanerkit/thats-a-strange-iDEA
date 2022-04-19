"""Contains all Hartree-fock functionality and solvers."""


import numpy as np
import scipy as sp
import iDEA.system
import iDEA.state
import iDEA.observables
import iDEA.methods.non_interacting
import iDEA.methods.hartree


# Method name.
name = "hartree_fock"


# Inherit functions.
kinetic_energy_operator = iDEA.methods.non_interacting.kinetic_energy_operator
external_potential_operator = iDEA.methods.non_interacting.external_potential_operator
hartree_potential_operator = iDEA.methods.hartree.hartree_potential_operator


def exchange_potential_operator(s: iDEA.system.System, p: np.ndarray) -> np.ndarray:
    """
    Compute the exchange potential operator.

    Args;
        s: iDEA.system.System, System object.
        p: np.ndarray, Charge density matrix.

    Returns:
        Vx: np.ndarray, Exchange potential energy operator.
    """
    v_x = iDEA.observables.exchange_potential(s, p)
    Vx = v_x * s.dx
    return Vx


def hamiltonian(s: iDEA.system.System, up_n: np.ndarray, down_n: np.ndarray, up_p: np.ndarray, down_p: np.ndarray, K: np.ndarray = None, V: np.ndarray = None) -> np.ndarray:
    """
    Compute the Hamiltonian from the kinetic and potential terms.

    Args:
        s: iDEA.system.System, System object.
        up_n: np.ndarray, Charge density of up electrons.
        down_n: np.ndarray, Charge density of down electrons.
        up_p: np.ndarray, Charge density matrix of up electrons.
        down_p: np.ndarray, Charge density matrix of down electrons.
        K: np.ndarray, Single-particle kinetic energy operator [If None this will be computed from s]. (default = None)
        V: np.ndarray, Potential energy operator [If None this will be computed from s]. (default = None)

    Returns:
        H: np.ndarray, Hamiltonian, up Hamiltonian, down Hamiltonian.
    """
    if K is None:
        K = kinetic_energy_operator(s)
    if V is None:
        V = external_potential_operator(s)
    Vh = hartree_potential_operator(s, up_n + down_n)
    Vx = exchange_potential_operator(s, up_p + down_p)
    up_Vx = exchange_potential_operator(s, up_p)
    down_Vx = exchange_potential_operator(s, down_p)
    H = K + V + Vh + Vx
    up_H = K + V + Vh + up_Vx
    down_H = K + V + Vh + down_Vx
    return H, up_H, down_H


def total_energy(s: iDEA.system.System, state: iDEA.state.SingleBodyState) -> float:
    """
    Compute the total energy.

    Args:
        s: iDEA.system.System, System object.
        state: iDEA.state.SingleBodyState, State. (default = None)

    Returns:
        E: float, Total energy.
    """
    E = iDEA.observables.single_particle_energy(s, state)
    n = iDEA.observables.density(s, state)
    v_h = iDEA.observables.hartree_potential(s, n)
    E -= iDEA.observables.hartree_energy(s, n, v_h)
    p, up_p, down_p = iDEA.observables.density_matrix(s, state, return_spins=True)
    up_v_x = iDEA.observables.exchange_potential(s, up_p)
    down_v_x = iDEA.observables.exchange_potential(s, down_p)
    E -= iDEA.observables.exchange_energy(s, up_p, up_v_x)
    E -= iDEA.observables.exchange_energy(s, down_p, down_v_x)
    return E


def solve(s: iDEA.system.System, k: int = 0, restricted: bool = False, tol: float = 1e-10) -> iDEA.state.SingleBodyState:
    """
    Solves the Schrodinger equation for the given system.

    Args:
        s: iDEA.system.System, System object.
        k: int, Energy state to solve for. (default = 0, the ground-state)
        restricted: bool, Is the calculation restricted (r) on unrestricted (u). (default=False)
        tol: float, Tollerance of convergence. (default = 1e-10)

    Returns:
        state: iDEA.state.SingleBodyState, Solved state.
    """
    return iDEA.methods.non_interacting.solve(s, hamiltonian, k, restricted, tol)

