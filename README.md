# Cortado-Core

![lint workflow](https://github.com/cortado-tool/cortado-core/actions/workflows/lint.yml/badge.svg)
![test workflow](https://github.com/cortado-tool/cortado-core/actions/workflows/test.yml/badge.svg)

**Cortado-core is a Python library that implements various algorithms and methods for interactive/incremental process discovery.**
Cortado-core is part of the software tool Cortado.

## Setup
* Install Python 3.10.x (https://www.python.org/downloads/). Make sure to install a 64-BIT version.
* Optional (recommended): Create a virtual environment (https://docs.python.org/3/library/venv.html) and activate it
* Install all packages required by cortado-core
  * Execute `pip install -r requirements.txt`

## Using Cortado-Core in Another Project
* Cortado-core can be used as a dependency in other Python-projects
* Install cortado-core via `pip install 'cortado-core @ git+https://github.com/cortado-tool/cortado-core.git@master'`

# Contributing

## Unit Testing and Code Quality

We highly value code quality and reliability in our project. To ensure this, our Github workflow includes unit testing using `pytest` and linting using `black`.

### Github Workflow

Our Github workflow automatically performs essential checks whenever code changes are pushed to the repository.

#### Unit Tests

The job `unit_tests` is responsible for running unit tests using `pytest`. It ensures that our codebase remains robust and free from logical errors. If any tests fail, the workflow provides prompt feedback, enabling us to quickly identify and address any issues.

#### Code Linting

We're committed to maintaining consistent code formatting and style. The workflow includes a linting job that uses `black`, a powerful code formatter for Python. This ensures that our code adheres to a unified and clean style, enhancing readability and maintainability.

### Running Unit Tests Locally

You can also run the `pytest` unit tests locally on your development environment. Ensure you have `pytest` installed, and then navigate to the project's root directory and run: `pytest cortado_core/tests/`

This will execute the unit tests and provide you with immediate feedback on their status.

### Development and Code Formatting
During development, we encourage you to utilize black for code formatting. The black tool helps maintain a consistent style across our codebase and minimizes formatting-related discussions. It's recommended to run black on your code before committing changes. You can do so using the following command:
`black .`

By incorporating black into your workflow, you contribute to maintaining a clean and organized codebase.

## Relevant Publications for Cortado

| Publication                                                                                                                        | Authors                                                             | Year | Relevant source code                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------- |
| [Defining and visualizing process execution variants from partially ordered event data](https://doi.org/10.1016/j.ins.2023.119958) | Schuster, D., Zerbato, F., van Zelst, S.J., van der Aalst, W.M.P.   | 2024 |                                                                                                    |
| [Incremental Discovery of Process Models Using Trace Fragments](https://doi.org/10.1007/978-3-031-41620-0_4)                       | Schuster, D., Föcking, N., van Zelst, S.J., van der Aalst, W.M.P.   | 2023 | [cortado_core/lca_approach.py](cortado_core/lca_approach.py)                                       |
| [Mining Frequent Infix Patterns from Concurrency-Aware Process Execution Variant](https://doi.org/10.14778/3603581.3603603)        | Martini, M., Schuster, D., Wil M. P. van der Aalst                  | 2023 | [cortado_core/eventually_follows_pattern_mining/](cortado_core/eventually_follows_pattern_mining/) |
| [Cortado: A dedicated process mining tool for interactive process discovery](https://doi.org/10.1016/j.softx.2023.101373)          | Schuster, D., van Zelst, S.J., van der Aalst, W.M.P.                | 2023 |                                                                                                    |
| [Control-Flow-Based Querying of Process Executions from Partially Ordered Event Data](https://doi.org/10.1007/978-3-031-20984-0_2) | Schuster, D., Martini, M., van Zelst, S.J., van der Aalst, W.M.P.   | 2022 | [cortado_core/variant_query_language/](cortado_core/variant_query_language/)                       |
| [Conformance Checking for Trace Fragments Using Infix and Postfix Alignments](https://doi.org/10.1007/978-3-031-17834-4_18)        | Schuster, D., Föcking, N., van Zelst, S.J., van der Aalst, W.M.P.   | 2022 | [cortado_core/alignments/](cortado_core/alignments/)                                               |
| [Temporal Performance Analysis for Block-Structured Process Models in Cortado](https://doi.org/10.1007/978-3-031-07481-3_13)       | Schuster, D., Schade, L., van Zelst, S.J., van der Aalst, W.M.P.    | 2022 | [cortado_core/performance/](cortado_core/performance/)                                             |
| [A Generic Trace Ordering Framework for Incremental Process Discovery](https://doi.org/10.1007/978-3-031-01333-1_21)               | Schuster, D., Domnitsch, E., van Zelst, S.J., van der Aalst, W.M.P. | 2022 | [cortado_core/trace_ordering/](cortado_core/trace_ordering/)                                       |
| [Freezing Sub-models During Incremental Process Discovery](https://doi.org/10.1007/978-3-030-89022-3_2)                            | Schuster, D., van Zelst, S.J., van der Aalst, W.M.P.                | 2021 | [cortado_core/freezing/](cortado_core/freezing/)                                                   |
| [Visualizing Trace Variants from Partially Ordered Event Data](https://doi.org/10.1007/978-3-030-98581-3_3)                        | Schuster, D., Schade, L., van Zelst, S.J., van der Aalst, W.M.P.    | 2021 | [cortado_core/utils/](cortado_core/utils/)                                                         |
| [Cortado—An Interactive Tool for Data-Driven Process Discovery and Modeling](https://doi.org/10.1007/978-3-030-76983-3_23)         | Schuster, D., van Zelst, S.J., van der Aalst, W.M.P.                | 2021 |                                                                                                    |
| [Incremental Discovery of Hierarchical Process Models](https://doi.org/10.1007/978-3-030-50316-1_25)                               | Schuster, D., van Zelst, S.J., van der Aalst, W.M.P.                | 2020 |                                                                                                    |

## Citing Cortado

* If you are using or referencing Cortado in scientific work, please cite Cortado as follows.

  > Schuster, D., van Zelst, S.J., van der Aalst, W.M.P. (2021). Cortado—An Interactive Tool for Data-Driven Process Discovery and Modeling. In: Application and Theory of Petri Nets and Concurrency. PETRI NETS 2021. Lecture Notes in Computer Science, vol 12734. Springer, Cham. https://doi.org/10.1007/978-3-030-76983-3_23

  Download citation 
  [.BIB](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=bibtex&flavour=citation)&nbsp;
  [.RIS](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=refman&flavour=citation)&nbsp;
  [.ENW](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=endnote&flavour=citation)

  DOI [10.1007/978-3-030-76983-3_23](https://doi.org/10.1007/978-3-030-76983-3_23)


* If you are using or referencing a specific algorithm implemented in Cortado/cortado-core in your scientific work, please cite the corresponding publication.


## Contact

If you are interested in Cortado, get in touch if you have any questions or custom request via Mail - [daniel.schuster@rwth-aachen.de](mailto:daniel.schuster@rwth-aachen.de)


