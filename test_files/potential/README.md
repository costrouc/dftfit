# Potentials

A list of potentials that are supported by dftfit. If you can write
your potential in one of the following forms. DFTFIT can optimize it.

Note that the yaml schema is not the only way to provide a
potential. `json` can be used to represent any DFTFIT yaml
specification. Additionally they can be represented with normal python
datastructures `dict` and `list`.

Two Body Potentials
 - [Python Function](#Python Function)
 - [ZBL](#ZBL Potential)
 - [Lennard Jones](#Lennard Jones Potential)
 - [Beck](#Beck Potential)
 - [Buckingham](#Buckingham Potential)

# Python Functions

DFTFIT allows for arbitrary python functions to be used for pair
potentials. The only requirement is that you define a function named
`potential` with the last arguments being the `r` that will be
supplied by dftfit. All the other parameters to the function will be
optimized. See this [stack-overflow
question](https://stackoverflow.com/questions/19139869/vectorizing-a-function-python)
if you need clarification on what numpy function vectorization
is. Under the covers DFTFIT evaluates the function at a set number of
points (`np.linspace(cutoff[0], cutoff[1], samples)`) to calculate the
energies and forces (via the finite centered difference).

An example of the buckingham potential is below. You are free to
import and call any functions within the block.

```python
import numpy as np

def potential(A, p, C, r):
    return A * np.exp(-r/p) - C / (r**6)
```

yaml schema

```yaml
pair:
 - type: python-function
   cutoff: [1.0, 10.0]
   samples: 1000
   function: |
     import numpy as np

     def potential(A, p, C, r):
         return A * np.exp(-r/p) - C / (r**6)
   parameters:
     - elements: ['Mg', 'Mg']
       coefficients: [1309362.2766468062, 0.104, 0.0]
     - elements: ['Mg', 'O']
       coefficients: [9892.357, 0.20199, 0.0]
     - elements: ['O', 'O']
       coefficients: [2145.7345, 0.3, 30.2222]
```

# ZBL Potential

 - [lammps documentation](https://lammps.sandia.gov/doc/pair_zbl.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/MgO-charge-buck-zbl.yaml)
 - 2 parameters: Z_1, Z_2

```math
E_{ij} = \frac{Z_i Z_j e^2}{4 \pi \epsilon_0 r_{ij}} \phi(r_{ij}/a)
```

```math
a = \frac{0.46850}{Z_i^{0.23} + Z_j^{0.23}}
```

```math
\phi{x} = 0.18175e^{-3.19980x} + 0.50986e^{-0.94229x} + 0.28022e^{-0.40290x} + 0.02817e^{-0.20162x}
```

yaml schema

```yaml
pair:
 - type: zbl
   cutoff: [3.0, 4.0]
   parameters:
     - elements: ['Mg', 'Mg']
       coefficients: [12, 12]
     - elements: ['Mg', 'O']
       coefficients: [12, 8]
     - elements: ['O', 'O']
       coefficients: [8, 8]
```

# Lennard Jones Potential

 - [lammps documentation](https://lammps.sandia.gov/doc/pair_lj.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/Ne-lennard-jones.yaml)
 - parameters 2: ε, σ

```math
E = 4 \epsilon \left[ \left(\frac{\sigma}{r} \right)^{12} - \left( \frac{\sigma}{r} \right)^6 \right]
```

yaml schema

```yaml
pair:
 - type: lennard-jones
   cutoff: [10.0]
   parameters:
     - elements: ['Ne', 'Ne']
       coefficients: [33.921, 2.801]
```

# Beck Potential

 - [lammps documentation](https://lammps.sandia.gov/doc/pair_beck.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/He-beck.yaml)
 - 5 parameters: A, B, a, α, β

```math
E(r) = A \exp \left[ -\alpha r - \beta r^6 \right] -\frac{B}{(r^2 + a^2)^3} \left( 1 + \frac{2.709 + 3a^2}{r^2 + a^2} \right)
```

yaml schema

```yaml
pair:
 - type: beck
   cutoff: [8.0]
   parameters:
     - elements: ['He', 'He']
       coefficients: [399.671876712, 0.0000867636112694, 0.675, 4.390, 0.0003746]
```

# Buckingham Potential

 - [lammps documentation](https://lammps.sandia.gov/doc/pair_buck.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/MgO-charge-buck.yaml)
 - 3 parameters: A, ρ, C

```math
\psi(r) = A \exp^{-\frac{r}{\rho}} - \frac{C}{r^6}
```

yaml schema

```yaml
pair:
 - type: buckingham
   cutoff: [10.0]
   parameters:
     - elements: ['Mg', 'Mg']
       coefficients: [1309362.2766468062, 0.104, 0.0]
     - elements: ['Mg', 'O']
       coefficients: [9892.357, 0.20199, 0.0]
     - elements: ['O', 'O']
       coefficients: [2145.7345, 0.3, 30.2222]
```

# Tersoff Potentials

 - [lammmps documentation](https://lammps.sandia.gov/doc/pair_tersoff.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/SiC-tersoff.yaml)
 - 14 parameters

```math
E = \frac{1}{2} \sum_i \sum_{j \ne i} V_{ij}
```

```math
V_{ij} = f_c\left(r_{ij}\right) \left[f_R(r_{ij}) + b_{ij} f_A(r_{ij})\right]
```

```math
f_c(r_{ij}) = \left\{
  \begin{array}{lr}
    1 & r_{ij} < R_{ij} - D_{ij} \\
    \frac{1}{2} - \frac{1}{2} \sin \left[\frac{\pi}{2}(r_{ij} - R_{ij})/D_{ij}\right] & R_{ij} - S_{ij} < r_{ij} < R_{ij} + D_{ij} \\
    0 & r_{ij} > R_{ij} + D_{ij}
  \end{array}
\right.
```

```math
f_R(r) = A_{ij} \exp ( -{\lambda_{1, ij}} r )
```

```math
f_A(r) = -B_{ij} \exp ( -\lambda_{2, ij} r )
```

```math
b_{ij} = (1 + \beta_i^{n_i} \zeta_{ij}^{n_i})^{-\frac{1}{2{n_i}}}
```

```math
\zeta_{ij} = \sum_{k \ne i, j} f_c(r_{ik}) g(\theta_{ijk}) \exp [\lambda_{3, ij}^m (r_{ij} - r_{ik}) ^ m ]
```

```math
g(\theta_{ijk}) = \gamma_{ik}\left( 1 + \frac{c_i^2}{d_i^2} - \frac{c_i^2}{[d_i^2 + (\cos \theta_{0, i} - \cos \theta_{ijk})^2]}\right)
```

Variables: $`R_{ij}, D_{ij}, A_{ij}, \lambda_{1, ij}, B_{ij}, \lambda_{2, ij}, \beta_i, n_i, \gamma_{ik}, c_i, d_i, m_i, \lambda_{3, ij}, \theta_{0, i}`$

Two body terms (6): $`n_i, \beta_i, \lambda_{2, ij}, B_{ij}, \lambda_{1, ij}, A_{ij}`$.

Three body terms (6): $`m_i, \gamma_{ik}, \lambda_{3, ij}, c_i, d_i, \theta_{0, i}`$

Terms that only depend on primary atom (6): $`n_i, \beta_i, m_i, c_i, d_i, \theta_{0, i}`$

Usually Fixed Terms $`m, \gamma, \beta`$

Mixing Terms $`\lambda, A, B, R, D`$

__m must be 3 or 1__

Original tersoff [1] form achieved when $`m = 3`$ and $`\gamma = 1`$

Tersoff [2] has the the following contstraints: 

$`\lambda_{3, i} = 0`$ thus m has not effect. In original paper $`\gamma_{ik} = 1`$.

Additional assumptions are the following: `lambda3 = 0`, `m = 3`, and
`gamma = 1` thus these parameters are not included.

The order of the parameters are `c, d, costheta0, n, beta, lambda2, B,
R, D, lambda1, A`. Additional models may be added if necissary.

```math
\lambda_{ij} = \frac{1}{2} (\lambda_{i} + \lambda_{j})
```

```math
A_{ij} = \sqrt{A_i A_j}
```

```math
B_{ij} = \chi_{ij} \sqrt{B_i B_j}
```

A mixing parameter is required for elements (N -1) see paper

```math
R_{ij} = \sqrt{R_i R_j}
```

```math
D_{ij} = \sqrt{D_i D_j}
```

Albe [3] when $`\beta = 1`$ and $`m = 1`$.

From [4] an R is 1.95, 2.85 for C-C-C and Si-Si-Si respectively and
0.15 for D (units Angstroms). R and D are chosen so as to include the
first neighbor shell only.

# Stillinger Weber Potentials

 - [lammps documentation](https://lammps.sandia.gov/doc/pair_sw.html)
 - [example potential](https://gitlab.com/costrouc/dftfit/blob/master/test_files/potential/CdTe-stillinger-weber.yaml)
 - 11 parameters

```math
E = \sum_i \sum_{j > i} \phi_2(r_{ij}) + \sum_i \sum_{j \ne i} \sum_{k > j} \phi_3(r_{ij}, r_{ik}, \theta_{ijk})
```

```math
\phi_2(r_{ij}) = A_{ij} \epsilon_{ij} \left[ B_{ij} \left( \frac{\sigma_{ij}}{r_{ij}} \right)^{p_{ij}} - \left( \frac{\sigma_{ij}}{r_{ij}} \right)^{q_{ij}} \right] \exp \left( \frac{\sigma_{ij}}{r_{ij} - a_{ij} \sigma_{ij}} \right) 
```

```math
\phi_3(r_{ij}, r_{ik}, \theta_{ijk}) = \lambda_{ijk} \epsilon_{ijk} \left[ cos \theta_{ijk} - cos \theta_{0ijk} \right]^2 exp \left( \frac{\gamma_{ij} \sigma_{ij}}{r_{ij} - a_{ij}\sigma_{ij}} \right) exp \left( \frac{\gamma_{ij} \sigma_{ik}}{r_{ik} - a_{ik}\sigma_{ik}} \right)
```

Parameters: $`\epsilon, \sigma, a, \lambda, \gamma, costheta0, A, B, p, q, tol`$

Mixing terms: $`\sigma, \epsilon`$

## Mixing Rules

### Analysis of the mixing rules for the Stillinger–Weber potential: a case-study of Ge–Si interactions in the liquid phase

https://doi.org/10.1016/j.jnoncrysol.2006.07.017

> With such systems, however, there arises a problem of choosing
> suitable parameters for unlike-species interactions, i.e. devising
> $`\sigma_{ij}, \epsilon_{ij} from \sigma_i, sigma_j, \epsilon_i,
> \epsilon_j`$ (for the two-body term) and $`\epsilon_{ijk},
> \lambda_{ijk}`$ from $`\epsilon_i, \epsilon_j, \lambda_i, and
> \lambda_j`$, where i, j, and k label the species of atoms in bond
> pairs and triplets.  The two-body parameters were usually approximated
> using the geometric mean for the energy parameter and the arithmetic
> mean for the length parameter (the so-called Lorentz–Berthelot mixing
> rules). This had no rigoristic justification in first principles, but
> was analogous to what was usually done for other potentials. - page 4233

> Choosing mixed-species paramters $`\epsilon_{ijk}, \lambda_{ijk}`$ for
> the three-body part is less obvious. Usually the choice of
> $`\epsilon_{ijk} = \sqrt{\epsilon_{ij}\epsilon_{ik}} =
> \epsilon^{\frac{1}{4}}_j \epsilon^{\frac{1}{2}}_j
> \epsilon^{\frac{1}{4}}_j`$ and $`\lambda_{ijk} = \sqrt{\lambda_{ij}\lambda_{ik}} =
> \lambda^{\frac{1}{4}}_j \lambda^{\frac{1}{2}}_j
> \lambda^{\frac{1}{4}}_j`$, first made by Grabow and Gilmer in [17]
> was iterated, even though the original authors had not justified it in
> any way.

> In our study we decided to further test this traditional choice
> against other ways of constructing the parameters, eg. $`\lambda_{Si
> Si Ge} = \sqrt[3]{\lambda_{Si} \lambda_{Si} \lambda_{Ge}}`$.

> Since the resultant parameters differed by only a few percent, we
> expected to obtain similar results, regardless of the type of the
> mixing rule employed, which would then confirm the validity of the
> Grabow–Gilmer mixing as one of several that work.  Surprisingly, this
> was not the case. It turned out that the simulations performed with
> only slightly different parameters resulted in radically different
> final atomic configurations.


# References

1. [Tersoff Original Paper J. Tersoff, Phys Rev B, 37, 6991 (1988).](https://doi.org/10.1103/PhysRevB.37.6991)
2. [Albe Form](http://iopscience.iop.org/article/10.1088/0953-8984/15/32/324/meta)
3. [Tersoff 2](https://doi.org/10.1103/PhysRevB.39.5566)
4. [Lammps Implementation](http://lammps.sandia.gov/doc/pair_tersoff.html)
17. M.H. Grabow, G.H. Gilmer, Surf. Sci. 194 (1987) 333
