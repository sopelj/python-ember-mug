# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/sopelj/python-ember-mug/issues>.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Python Ember Mug could always use more documentation, whether as part of the
official Python Ember Mug docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at <https://github.com/sopelj/python-ember-mug/issues>.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started

Ready to contribute? Here's how to set up `python-ember-mug` for local development.

1. Fork the `python-ember-mug` repo on GitHub.
2. Clone your fork locally

    ```
    git clone git@github.com:your_name_here/python-ember-mug.git
    ```

3. Ensure [hatch](https://hatch.pypa.io/) is installed.
4. You can directly run the CLI from hatch with:

    ```
    hatch run ember-mug --help
    ```

5. Create a branch for local development:

    ```
    git checkout -b name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

6. When you're done making changes, check that your changes pass the
   tests, including testing other Python versions, with Hatch:

    ```
    hatch run test:cov
    ```

7. Commit your changes and push your branch to GitHub:

    ```
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

8. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.md.
3. The pull request should work for Python 3.9, 3.10 and 3.11. Check
   <https://github.com/sopelj/python-ember-mug/actions>
   and make sure that the tests pass for all supported Python versions.

## Tips

```
hatch run test:cov tests/test_python_ember_mug.py
```

To run a subset of tests.

## Deploying

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in CHANGELOG.md).
Then run:

```
hatch version patch # possible: major / minor / patch
git add .
git commit -m "Bump version: v$(hatch version)"
git tag "v$(hatch version)"
git push
git push --tags
```

GitHub Actions will then deploy to PyPI if tests pass.
