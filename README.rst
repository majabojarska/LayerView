=========
LayerView
=========

.. image:: https://img.shields.io/pypi/v/layerview.svg
    :alt: Latest package version on PyPi
    :target: https://pypi.python.org/pypi/layerview

.. image:: https://github.com/majabojarska/LayerView/actions/workflows/build.yml/badge.svg
    :alt: LayerView build status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/build.yml

.. image:: https://github.com/majabojarska/LayerView/actions/workflows/docs.yml/badge.svg
    :alt: Documentation build status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/docs.yml

.. image:: https://github.com/majabojarska/LayerView/actions/workflows/lint.yml/badge.svg
    :alt: Code linting status on GitHub Actions
    :target: https://github.com/majabojarska/LayerView/actions/workflows/lint.yml

.. image:: https://readthedocs.org/projects/layerview/badge/?version=latest
    :target: https://layerview.readthedocs.io/en/latest/?badge=latest
    :alt: Read the Docs documentation Status

.. image:: https://github.com/majabojarska/LayerView/raw/main/docs/_static/app.png
    :alt: Main window of LayerView application.

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

Installation
------------

LayerView can be installed via pip.

.. code-block:: console

    $ pip install layerview

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
