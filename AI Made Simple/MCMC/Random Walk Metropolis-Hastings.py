import numpy as np
import matplotlib.pyplot as plt

# Set seed for reproducibility
np.random.seed(12345)

# Initialize parameters
initial_theta = np.array([-1.0, 1.0])
num_iterations = 20000
theta_current = initial_theta.copy()
epsilon = 1e-8

# Define repulsive points (4x4 grid from -3 to +3)
grid_points = np.linspace(-3, 3, 4)
repulsive_mu = np.array(np.meshgrid(grid_points, grid_points)).T.reshape(-1, 2)

# Storage for the chain and running mean
chain = np.zeros((num_iterations, 2))
chain[0] = theta_current
running_mean = np.zeros((num_iterations, 2))
running_mean[0] = theta_current

# Log-posterior function
def log_posterior(theta):
    log_lik = -0.5 * np.sum(theta**2)
    distances_sq = np.sum((theta - repulsive_mu)**2, axis=1) + epsilon
    repulsive_prior = -np.sum(1.0 / distances_sq)
    return log_lik + repulsive_prior

current_log_posterior = log_posterior(theta_current)

# MCMC Sampling with running mean calculation
for i in range(1, num_iterations):
    proposal = np.random.normal(theta_current, np.sqrt(0.2), size=2)
    proposal_log_posterior = log_posterior(proposal)
    if np.log(np.random.uniform()) < (proposal_log_posterior - current_log_posterior):
        theta_current = proposal
        current_log_posterior = proposal_log_posterior
    chain[i] = theta_current
    # Update running mean
    running_mean[i] = running_mean[i-1] + (theta_current - running_mean[i-1]) / (i + 1)

# Summary statistics
theta_mean = chain.mean(axis=0)
theta_std = chain.std(axis=0)
print(f"Posterior Mean: {theta_mean}")
print(f"Posterior Std Dev: {theta_std}")

# Plotting the chain and repulsive points
plt.figure(figsize=(12, 5))

# 1. Plot the MCMC Chain
plt.subplot(1, 2, 1)
plt.plot(chain[:, 0], chain[:, 1], alpha=0.3, label='MCMC Chain')
plt.scatter(repulsive_mu[:, 0], repulsive_mu[:, 1], color='red', label='Repulsive Points')
plt.xlabel(r'$\theta_1$')
plt.ylabel(r'$\theta_2$')
plt.title('RWMH with Repulsive Normal Example')
plt.legend()
plt.grid(True)

# 2. Plot the Running Posterior Mean
plt.subplot(1, 2, 2)
plt.plot(running_mean[:, 0], label=r'$\theta_1$ Mean')
plt.plot(running_mean[:, 1], label=r'$\theta_2$ Mean')
plt.axhline(y=theta_mean[0], color='blue', linestyle='--', alpha=0.7)
plt.axhline(y=theta_mean[1], color='orange', linestyle='--', alpha=0.7)
plt.xlabel('Iteration')
plt.ylabel('Running Mean')
plt.title('Convergence of Posterior Mean')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
