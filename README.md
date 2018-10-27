# python library for interacting with gdbserver

# paths:

`bin` - host run scripts

`docker` - docker stuff

`scripts` - scripts run from inside a container

`tests` - test suite

# getting started

to run the local cli `bin/run-cli`

to start the dev server `bin/dev-up`

to run the tests `bin/run-tests`

## tests from host:

make sure nose is installed:

`pip install --user nose`

then:

`cd tests && nosetests`

