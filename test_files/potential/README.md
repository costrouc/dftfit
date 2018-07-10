# Potentials

A list of potentials that are supported by dftfit. If you can write
your potential in one of the following forms. DFTFIT can optimize it.



# Tersoff Potentials

Parameters: m, gamma, lambda3, c, d, costheta0, n, beta, lambda2, B, R, D, lambda1, A


# Stillinger Weber Potentials

Parameters: epsilon, sigma, a, lambda, gamma, cosheta0, A, B, p, q, tol

## Mixing Rules

### Analysis of the mixing rules for the Stillinger–Weber potential: a case-study of Ge–Si interactions in the liquid phase

https://doi.org/10.1016/j.jnoncrysol.2006.07.017

```math
\frac{\beta}{\gamma}
```

> With such systems, however, there arises a problem of choosing
> suitable parameters for unlike-species interactions, i.e. devising
> $`\sigma_{ij}, \epsilon+{ij} from \sigma_i, sigma_j, \epsilon_i,
> \epsilon_j`$ (for the two-body term) and \epsilon_{ijk},
> \lambda_{ijk}`$ from $`\epsilon_i, \epsilon_j, \lambda_i, and
> \lambda_j`$, where i, j, and k label the species of atoms in bond
> pairs and triplets.  The two-body parameters were usually approximated
> using the geometric mean for the energy parameter and the arithmetic
> mean for the length parameter (the so-called Lorentz–Berthelot mixing
> rules). This had no rigoristic justification in first principles, but
> was analogous to what was usually done for other potentials

