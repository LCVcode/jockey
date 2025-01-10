# Contributing to _Jockey_
Welcome! Thank you for your interest in contributing to _Jockey_,
an open-source community project that aims to simplify operations on large [Juju](https://juju.is) deployments.

Jockey's core querying functionality uses a purely functional programming style keep the scope narrow and maintenance easy.  No OOP-style contributions to core Jockey components will be considered.

## Contributing at a Glance

1. [First-time contributors](#first-time-contributors)
2. [Prepare the development environment](#prepare-the-development-environment)
   1. [Continuous Integration testing](#continuous-integration-testing)
   2. [Local development environment](#local-development-environment)
      1. [Check formatting](#check-formatting)
      2. [Fix formatting](#fix-formatting)
      3. [Run tests](#run-tests)
3. [Submitting changes](#submitting-changes)
4. [Maintainer guidelines](#maintainer-guidelines)

## First-time contributors
We reiterate: welcome! If you need help, please check out the [issue tracker](https://github.com/LCVcode/jockey/issues).

In particular, the following tags are a great start:
- [good first issue][good first issue]
- [documentation][documentation]
- [help wanted][help wanted]

You do not need permission to start working on any issue. Just jump in, [make sure you add tests](#run-tests), and open a pull request.

To get advice and input on a problem:
Add a comment to the issue.
If you've encountered a new problem, open a [bug][bug].
If you have an idea for a new enhancement, open a [feature][feature].
You're more likely to get help with the more details you provide.

[good first issue]: https://github.com/LCVcode/jockey/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22
[documentation]: https://github.com/LCVcode/jockey/issues?q=is%3Aopen+is%3Aissue+label%3Adocumentation
[help wanted]: https://github.com/LCVcode/jockey/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22
[bug]: https://github.com/LCVcode/jockey/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=
[feature]: https://github.com/LCVcode/jockey/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=Feature%3A+
[new PR]: https://github.com/LCVcode/jockey/compare

## Prepare the development environment
### Continuous Integration testing
_Jockey_ uses [Continuous Integration (CI)](https://en.wikipedia.org/wiki/Continuous_integration) to evaluate all pull requests. When you open a pull request (PR), our automated CI workflows will run against your PR.

Our automated CI workflows currently include the following tools:
- [black](https://github.com/psf/black)
- [isort](https://github.com/PyCQA/isort)
- [flake8](https://github.com/PyCQA/flake8)
- [mypy](https://github.com/python/mypy)
- [pytest](https://docs.pytest.org/en/stable/)

In addition to catching problems, bots will automatically fix any formatting issues. This eliminates the need to configure a complicated local development environment so that you can focus on the code. CI takes the load off your back and points you to any problem areas requiring your attention.

### Local development environment
We configured our tools to support those who prefer to perform testing and formatting locally.
_Jockey_ uses Poetry to manage the Python development environment.

First, make sure you have Poetry installed. If not, please refer to the
[Poetry installation guide](https://python-poetry.org/docs/#installation).

Next, install the dependencies of _Jockey_ using Poetry:
```bash
poetry install
```

Once everything is ready, you can configure your editor to use the Poetry-generated virtual environment or drop into the shell using Poetry:
```bash
poetry shell
```

#### Check formatting
_Jockey_ uses the following linters to check formatting:
- [black](https://github.com/psf/black)
- [isort](https://github.com/PyCQA/isort)
- [flake8](https://github.com/PyCQA/flake8)
- [mypy](https://github.com/python/mypy)

It's possible to run these linters locally:

##### black
```bash
# Lint code format with black
poetry run black src tests --check
```

##### isort
```bash
# Lint import order with isort
poetry run isort src tests --check
```

##### flake8
```bash
# Lint with flake8
poetry run flake8 src tests
```

##### mypy
```bash
# Lint with mypy
poetry run mypy src
```

#### Fix formatting
Not only are you able to check your formatting, but a few linters can automatically fix it:

##### black
```bash
# Fix code format with black
poetry run black src
```

##### isort
```bash
# Fix import order with isort
poetry run isort src tests
```

#### Run tests
_Jockey_ uses several unit tests to validate software functionality. You can run these locally, too:

##### pytest
```bash
# Execute unit tests
poetry run pytest -s
```

## Submitting changes
Implementing a fix or a new feature is even more valuable than a great bug report or feature request. Your contributions are precious as the foundation of open-source development.

If your change requires a significant amount of work to write, we recommend starting by opening an issue laying out your plan. That lets a conversation happen early in case other contributors disagree with your plan or have ideas that will help you do it.

We lean on the GitHub pull-request workflow. If you're unfamiliar with this, please refer to [GitHub's documentation on the feature](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).

The best pull requests clearly describe their purpose and changes. New tests, especially in the presence of significant changes or feature implementations, go a long way toward ensuring enduring stability for Jockey.

Once you're ready to submit your changes, [open a pull request on the repository][new PR] against the `master` branch. The [maintainers](MAINTAINERS.md) will review your changes.

## Maintainer guidelines
[Maintainers](MAINTAINERS.md) should follow these rules when handling pull requests:

- Wait for tests to finish and pass before merging PRs.
- Use the "Squash and Merge" strategy to merge PRs.
- Delete any branches for merged PRs.
- Edit the final commit message to conform to this format, where `(<scope>)` is optional:
  ```
  <type>(<scope>): <message>
  ```
