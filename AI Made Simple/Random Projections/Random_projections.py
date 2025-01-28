import numpy as np
from sklearn.random_projection import GaussianRandomProjection

# Create a dataset with 100 entries that belongs to a 1,000-dimensional space
np.random.seed(1)
high_dimensional_data = np.random.rand(100, 1000) # Each value is between 0 and 1

# Suppose that the lemma of Johnson-Lindenstrauss told us that the output space has 52-dimensions
n_components = 50

# Since the matrix R is random, I have to set the seed also here
random_projection = GaussianRandomProjection(n_components=n_components, random_state=1) 

# Apply the random projection
reduced_data = random_projection.fit_transform(high_dimensional_data)







