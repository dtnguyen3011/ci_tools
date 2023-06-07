<!---

	Copyright (c) 2009, 2016 Robert Bosch GmbH and its subsidiaries.
	This program and the accompanying materials are made available under
	the terms of the Bosch Internal Open Source License v4
	which accompanies this distribution, and is available at
	http://bios.intranet.bosch.com/bioslv4.txt

-->

# Find Cpps

* [About](#about)
* [Maintainers](#maintainers)
* [Contributors](#contributors)
* [License](#license)
* [Coding Style](#style)
* [How to use it](#use)
* [How to build](#build)
* [How to test](#test)
* [How to contribute](#contribute)
* [Used 3rd party Licenses](#licenses)
* [Used encryption](#encryption)
* [Feedback](#feedback)

## <a name="about">About</a>

The find_cpps.py script is able to determine changed header or inline files and feed the input
back to the prqa_helper.py

## <a name="maintainers">Maintainers</a>

* [Ingo Jauch](https://connect.bosch.com/profiles/html/profileView.do?key=fccee294-fb86-40cf-8c78-6917f4a69e13)
* [Andre Bem](https://connect.bosch.com/profiles/html/profileView.do?userid=E49CC0EA-C3A5-46DB-8BB2-8B7C89DA4D3E)

## <a name="contributors">Contributors</a>

Consider listing contributors in this section to give explicit credit. You 
could also ask contributors to add themselves in this file on their own.

## <a name="license">License</a>
 
>	Copyright (c) 2009, 2016 Robert Bosch GmbH and its subsidiaries.
>	This program and the accompanying materials are made available under
>	the terms of the Bosch Internal Open Source License v4
>	which accompanies this distribution, and is available at
>	http://bios.intranet.bosch.com/bioslv4.txt

## <a name="style">Coding Style</a>

This project uses [PEP8](https://www.python.org/dev/peps/pep-0008/) as it's basic coding style. To enforce it's usage both [pylint](https://www.pylint.org/) and [yapf](https://github.com/google/yapf) should be used to enforce all code changes and check for potential errors and warnings in the code.

## <a name="use">How to use it</a>

### find_cpps.py

This script is meant to find all cpp file changes according to a given list of files or to a git difference between the current branch and the origin/develop branch.

Options and usage vary according to project and use case. An example configuration to find the differences in the test_src directory exists in find_cpps/example_cfg. Run:

> $ python find_cpps.py -h

for usage details. 

## <a name="build">How to build</a>

No need to build.


## <a name="test">How to test</a>

To run the unit tests:

> $ python -m unittest

## <a name="contribute">How to contribute</a>

If you want to use this setup or contribute, please first contact the [Maintainers](#maintainers).

## <a name="licenses">Used 3rd party Licenses</a>

You must mention all 3rd party licenses (e.g. OSS) licenses used by your
project here. Example:

Software | License
------------------
 
## <a name="encryption">Used encryption</a>

Declaration of the usage of any encryption (see BIOS Repository Policy §4.a ).

## <a name="feedback">Feedback</a>

Get in contact with the [Maintainers](#maintainers), e.g. via email or via the [coding rules T&R project](https://rb-tracker.bosch.com/tracker/projects/CDF/summary).

<!---

	Copyright (c) 2009, 2016 Robert Bosch GmbH and its subsidiaries.
	This program and the accompanying materials are made available under
	the terms of the Bosch Internal Open Source License v4
	which accompanies this distribution, and is available at
	http://bios.intranet.bosch.com/bioslv4.txt

-->
