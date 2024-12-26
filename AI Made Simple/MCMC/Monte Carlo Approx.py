import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import cauchy

# 1. Set seed
np.random.seed()

# 2. Fix settings
m = 100000              # Number of Monte Carlo samples
th0 = 0.5               # True (unknown) location parameter

# 3. Generate observed data
#    Cauchy sample of size 200 with location th0 and scale = 1
n = 200
x = th0 + np.random.standard_cauchy(n)

# 4. Fix hyperpriors for the normal prior
mu = 0     # Prior mean
s2 = 1     # Prior variance (so std = 1)

# 5. Sample from the prior (Normal(mu, sqrt(s2)))
th = np.random.normal(loc=mu, scale=np.sqrt(s2), size=m)

# 6. Approximate the posterior:
#    We'll keep a running numerator and denominator:
#      num = Σ (θ_j * weight_j)
#      den = Σ (weight_j)
#    where weight_j = ∏ p(x_i | θ_j)
#                   = exp( sum( log p(x_i | θ_j) ) )
num = 0.0
den = 0.0
th_hat = np.zeros(m)  # to store the running posterior mean at each iteration

for j in range(m):
    # Compute log likelihood of the data given current θ_j
    log_lik = cauchy.logpdf(x, loc=th[j], scale=1.0)
    # Weight = exp of sum of log likelihoods
    omega = np.exp(np.sum(log_lik))
    
    # Update numerator and denominator
    num += th[j] * omega
    den += omega
    
    # Store running posterior mean
    th_hat[j] = num / den

# 8. Print the final estimate
posterior_mean = num / den
print("Final posterior mean estimate:", posterior_mean)

# 7. Plot the evolving estimate of the posterior mean
plt.figure(figsize=(8, 5))
plt.plot(np.arange(1, m+1), th_hat, 'b-', linewidth=1, label=f"Sample value = {round(posterior_mean, 3)}")
plt.axhline(y=th0, color='r', linestyle='--', linewidth=2, label=f"True value = {th0}")
plt.ylim(0, 1)
plt.xlabel("Iteration")
plt.ylabel("Posterior mean estimate")
plt.title("Monte Carlo Approximation of Posterior Mean")
plt.legend()
plt.tight_layout()
plt.show()

