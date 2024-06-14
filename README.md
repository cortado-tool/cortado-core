# Cortado-Core

**Cortado-core is a Python library that implements various algorithms and methods for interactive/incremental process discovery.**
Cortado-core is part of the software tool Cortado.
Please refer to the [website of Cortado](https://cortado.fit.fraunhofer.de) that contains a list of publications on algorithms implemented in cortado-core. 

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

We highly value code quality and reliability in our project. To ensure this, our GitLab pipeline includes unit testing using `pytest` and linting using `black`.

### GitLab Pipeline

Our GitLab pipeline automatically performs essential checks whenever code changes are pushed to the repository.

#### Unit Tests

The pipeline's `unit_tests` stage is responsible for running unit tests using `pytest`. It ensures that our codebase remains robust and free from logical errors. If any tests fail, the pipeline provides prompt feedback, enabling us to quickly identify and address any issues.

#### Code Linting

We're committed to maintaining consistent code formatting and style. The pipeline includes a linting stage that uses `black`, a powerful code formatter for Python. This ensures that our code adheres to a unified and clean style, enhancing readability and maintainability.

### Running Unit Tests Locally

You can also run the `pytest` unit tests locally on your development environment. Ensure you have `pytest` installed, and then navigate to the project's root directory and run: `pytest cortado_core/tests/`

This will execute the unit tests and provide you with immediate feedback on their status.

### Development and Code Formatting
During development, we encourage you to utilize black for code formatting. The black tool helps maintain a consistent style across our codebase and minimizes formatting-related discussions. It's recommended to run black on your code before committing changes. You can do so using the following command:
`black .`

By incorporating black into your workflow, you contribute to maintaining a clean and organized codebase.

## Citing Cortado

* If you are using or referencing Cortado in scientific work, please cite Cortado as follows.

  > Schuster, D., van Zelst, S.J., van der Aalst, W.M.P. (2021). Cortado—An Interactive Tool for Data-Driven Process Discovery and Modeling. In: Application and Theory of Petri Nets and Concurrency. PETRI NETS 2021. Lecture Notes in Computer Science, vol 12734. Springer, Cham. https://doi.org/10.1007/978-3-030-76983-3_23

  Download citation 
  [.BIB](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=bibtex&flavour=citation)&nbsp;
  [.RIS](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=refman&flavour=citation)&nbsp;
  [.ENW](https://citation-needed.springer.com/v2/references/10.1007/978-3-030-76983-3_23?format=endnote&flavour=citation)

  DOI [10.1007/978-3-030-76983-3_23](https://doi.org/10.1007/978-3-030-76983-3_23)


* If you are using or referencing a specific algorithm implemented in Cortado/Cortado-Core in your scientific work, please cite the corresponding publication, cf. [website of Cortado](https://cortado.fit.fraunhofer.de).


## Contact

If you are interested in Cortado, get in touch if you have any questions or custom request via [Mail - daniel.schuster@fit.fraunhofer.de](mailto:daniel.schuster@fit.fraunhofer.de)


