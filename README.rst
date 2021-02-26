=========
LayerView
=========

.. image:: https://img.shields.io/pypi/v/layerview?style=flat
    :alt: Latest package version on PyPi
    :target: https://pypi.org/project/layerview/

.. image:: https://img.shields.io/pypi/status/LayerView
    :alt: PyPI Status
    :target: https://pypi.org/project/layerview/

.. image:: https://img.shields.io/pypi/pyversions/layerview?style=flat
    :alt: Supported Python versions
    :target: https://pypi.org/project/layerview/

.. image:: https://img.shields.io/pypi/implementation/layerview?style=flat
    :alt: Supported Python implementation
    :target: https://pypi.org/project/layerview/

.. image:: https://img.shields.io/github/workflow/status/majabojarska/LayerView/build?label=build&style=flat
    :alt: LayerView build status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/build.yml

.. image:: https://img.shields.io/github/workflow/status/majabojarska/LayerView/docs?label=docs&style=flat
    :alt: Documentation build status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/docs.yml

.. image:: https://img.shields.io/github/workflow/status/majabojarska/LayerView/lint?label=lint&style=flat
    :alt: Code linting status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/lint.yml

.. image:: https://img.shields.io/readthedocs/layerview?label=Read%20the%20Docs&style=flat
    :target: https://layerview.readthedocs.io/en/latest/
    :alt: Read the Docs documentation Status

.. image:: https://github.com/majabojarska/LayerView/raw/main/docs/_static/app.png
    :alt: Main window of LayerView application.
    :target: https://pypi.org/project/layerview/

LayerView is a G-code file visualizer and inspector.

* Source code: `majabojarska/LayerView <https://github.com/majabojarska/LayerView>`_
* License: `GPLv3`_
* Documentation: https://layerview.readthedocs.io.

Features
--------

* 3D visualization and inspection of G-code files.

  * Parametrized layer coloring.
  * Adjustable visible layer range.
  * Parameter inspection for model and layers.

* Supports `RepRap`_ G-code flavour and its derivatives.
  `Marlin`_ also works fine with the current feature set.
* Hardware accelerated 3D rendering via `Panda3D`_.
* Runs on x86_64 variants of Linux, Windows, MacOS.

Quickstart
----------

Install the latest LayerView package via pip:

.. code-block:: console

    pip install -U layerview

Run LayerView:

.. code-block:: console

    layerview

See the `full documentation <https://layerview.readthedocs.io/en/latest/index.html>`_
for more details on `installation <https://layerview.readthedocs.io/en/latest/installation.html>`_
and `usage <https://layerview.readthedocs.io/en/latest/usage.html>`_.

Contributing
------------

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.
See the `Contributing <https://layerview.readthedocs.io/en/latest/contributing.html>`_
page for more details on how to contribute to this project.

Credits
-------

This package was created with Cookiecutter_ and the `briggySmalls/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`briggySmalls/cookiecutter-pypackage`: https://github.com/briggySmalls/cookiecutter-pypackage
.. _`GPLv3`: http://www.gnu.org/licenses/gpl-3.0.en.html
.. _`Panda3D`: https://www.panda3d.org/
.. _`RepRap`: https://reprap.org/wiki/G-code
.. _`Marlin`: https://marlinfw.org/meta/gcode/
.. _`CPython`: https://en.wikipedia.org/wiki/CPython
