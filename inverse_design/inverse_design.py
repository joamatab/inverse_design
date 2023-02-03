# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/07_inverse_design.ipynb.

# %% auto 0
__all__ = ['omega', 'dl', 'Nx', 'Ny', 'Npml', 'epsr_init', 'space', 'wg_width', 'space_slice', 'Nsteps', 'step_size', 'epsr',
           'bg_epsr', 'design_region', 'input_slice', 'output_slice', 'epsr_total', 'source', 'probe', 'grad_fn',
           'get_design_region', 'set_design_region', 'forward', 'loss_fn', 'step_fn']

# %% ../notebooks/07_inverse_design.ipynb 2
import autograd.numpy as npa
import matplotlib.pylab as plt
import numpy as np
from ceviche import jacobian
from ceviche.modes import insert_mode
from .brushes import notched_square_brush, show_mask
from inverse_design.conditional_generator import (
    generate_feasible_design,
    generate_feasible_design_mask,
    new_latent_design,
    transform,
)
from .direct_optimization import huber_loss
from inverse_design.naive_inverse_design import (
    init_domain,
    mask_combine_epsr,
    mode_overlap,
    viz_sim,
)
from jax.example_libraries.optimizers import adam
from tqdm.notebook import trange

# %% ../notebooks/07_inverse_design.ipynb 5
# Angular frequency of the source in Hz
omega = 2 * np.pi * 200e12
# Spatial resolution in meters
dl = 40e-9
# Number of pixels in x-direction
Nx = 100
# Number of pixels in y-direction
Ny = 100
# Number of pixels in the PMLs in each direction
Npml = 20
# Initial value of the structure's relative permittivity
epsr_init = 12.0
# Space between the PMLs and the design region (in pixels)
space = 10
# Width of the waveguide (in pixels)
wg_width = 12
# Length in pixels of the source/probe slices on each side of the center point
space_slice = 8
# Number of epochs in the optimization
Nsteps = 100
# Step size for the Adam optimizer
step_size = 1e-2

# %% ../notebooks/07_inverse_design.ipynb 9
# Initialize the parametrization rho and the design region
epsr, bg_epsr, design_region, input_slice, output_slice = init_domain(
    Nx, Ny, Npml, space=space, wg_width=wg_width, space_slice=space_slice
)

epsr_total = mask_combine_epsr(epsr, bg_epsr, design_region)

# Setup source
source = insert_mode(omega, dl, input_slice.x, input_slice.y, epsr_total, m=1)

# Setup probe
probe = insert_mode(omega, dl, output_slice.x, output_slice.y, epsr_total, m=2)

# %% ../notebooks/07_inverse_design.ipynb 11
def get_design_region(epsr, design_region=design_region):
    I = np.where(design_region.sum(0) > 1e-5)[0]
    J = np.where(design_region.sum(1) > 1e-5)[0]
    return epsr[I,:][:,J]

# %% ../notebooks/07_inverse_design.ipynb 12
def set_design_region(epsr, value, design_region=design_region):
    return np.where(design_region > 1e-5, value, epsr)

# %% ../notebooks/07_inverse_design.ipynb 20
def forward(latent_weights, brush):
    latent_t = transform(latent_weights, brush)
    design_mask = generate_feasible_design_mask(latent_t, brush)
    epsr = np.where(design_mask, 12.0, 1.0)

# %% ../notebooks/07_inverse_design.ipynb 21
def loss_fn(epsr):
    epsr = epsr.reshape((Nx, Ny))
    simulation.eps_r = mask_combine_epsr(epsr, bg_epsr, design_region)
    _, _, Ez = simulation.solve(source)
    return -mode_overlap(Ez, probe) / E0

# %% ../notebooks/07_inverse_design.ipynb 22
grad_fn = jacobian(loss_fn, mode='reverse')

# %% ../notebooks/07_inverse_design.ipynb 27
def step_fn(step, state):
    latent = np.asarray(params_fn(state), dtype=float) # we need autograd arrays here...
    loss = loss_fn(latent)
    grads = grad_fn(latent)
    optim_state = update_fn(step, grads, state)
    return loss, optim_state
