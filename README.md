# translationConverter (tx)

This tool provides a number of RESTful services for
processing and publishing translations on the [Door43 Content Service](https://git.door43.org).

# Development

All of the development commands have been place in a makefile for easy use.

* `make` or `make doc` generates the documentation.
* `make dependencies` install the dependencies.
* `make test` runs the tests.
* `make run` starts the development server.

## Contributing

When contributing please follow these practices:

* place new services under `./src/services/`.
* register your services in `./src/main.py` within the `register_services` function.
* add tests for your services in `./tests`.

# Documentation

All methods and modules **must** be documented with reStructured text.
These doc strings will be used to generate the documentation files.

Everything under `./doc` has been configured for you or is managed by the makefile.
**Stay out of there!**

## Subpackages

If your service is prepared as a subpackage (directory) as opposed to a submodule (single file)
you must add a doc string to the subpackage's `__init__.py` file otherwise it will not
be added to the table of contents.
