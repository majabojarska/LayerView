.. highlight:: shell

============
Contributing
============

I'm not actively working on this project. However, contributions are welcome and credit will always be given!
    
You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/majabojarska/LayerView/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

LayerView could always use more documentation, whether as part of the
official LayerView docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/majabojarska/LayerView/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `LayerView` for local development.

#. Fork the `LayerView` repo on GitHub.
#. Clone your fork locally::

    $ git clone git@github.com:your_name_here/LayerView.git

#. Ensure `poetry is installed`_.
#. Install dependencies and start your virtualenv::

    $ poetry install

#. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

#. When you're done making changes, check that your changes pass the
   tests, including testing other Python versions, with tox::

    $ tox

#. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

#. Submit a pull request through the GitHub website.

.. _poetry is installed: https://python-poetry.org/docs/

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring. Describe the changes
   `CHANGELOG.rst`.
3. The pull request should work for Python 3.8 and 3.9. Check
   https://github.com/majabojarska/LayerView/pulls
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests in currently active environment::

$ pytest tests.test_layerview

To run all tests in isolated `tox` environments::

$ tox

Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in `CHANGELOG.rst`).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

If all CI tests pass, publish to PyPI::

$ poetry publish --build
