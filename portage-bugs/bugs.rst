SLOT Cannot Be Calculated Dynamically
=====================================

Currently, SLOT (and potentially other critical variables, although this bug
deals directly with SLOT) are set statically and cannot be set dynamically by
the ebuild. This lack of ability to define SLOT dynamically creates problems
when the SLOT of an ebuild may be determined by another package's version
number. For example, the SLOT of a python module should ideally be determined
by the SLOT of the python framework it is being built against. However, having
the SLOT set dynamically -- which would be an ideal solution -- is not
possible.

Proposed Solution and Impact
----------------------------

Don't cache SLOT in an ebuild's metadata, and allow it to be set dynamically.
This will prevent SLOT dependencies from being satisfied automatically, as
Portage then cannot easily "scan" for a package that satisfies the SLOT
requirement. The impact of this reduced functionality would need to be
assessed -- ie. how useful are SLOT dependencies in contrast to the ability
to set SLOT dynamically.

No "if Package Installed" Dependency Conditional
================================================

Portage's dependencies currently only support conditionals based on whether
a particular USE variable is set or not. However, there are times where it
is helpful to require a specific version (or SLOT?) of a package only if that
package happens to be installed. This is particularly useful when a known
conflict exists between two packages. In this case, one package can have its
dependencies modified so that *if* a second package is installed, this second
package will be upgraded to a certain minimum version to avoid conflicts.
This problem would otherwise be resolved by end-users.

Documented Case
---------------

On March 19, 2010, Michael Frysinger addressed Gentoo Bug 309623 by adding a
blocker to sys-libs/zlib so that it would not install if libxml2 earlier than
2.7.7 was installed. This created a blocker during ``emerge -auDN world``
that Portage could not auto-resolve. The solution by Daniel Robbins for Funtoo
was to add a ``>dev-util/libxml2-2.7.7`` PDEPEND to the new zlib. This allowed
Portage to auto-resolve the blocker. This solution was workable because libxml2
is part of a standard stage3. However, if libxml2 were instead an optional
package, then a PDEPEND would not be an adequate solution, since a forced merge
of an optional package to resolve the problem would force the package to be
merged even for those who did not want the package. This gives weight to the
need for a "if package installed" dependency conditional that can be used to
conditionally merge based on whether a particular package atom is installed.

Proposed Solution and Impact
----------------------------

A new Portage design could introduce a new kind of dependency conditional that
is based on whether a package is installed on the current or ROOT filesystem.
There should be no negative impact on other Portage functionality by
implementing this feature. It should not negatively impact binary packages as
this feature should be fully compatible with them.

Lack of Multi-Sub-Package Support
=================================

A number of ebuilds are essentially two or more packages in one. Consider a
package that has a number of binary tools, plus a Python API. The Python API
will build against the currently-installed version of Python, and thus should
ideally have a 2.6 SLOT, while the main binary tools may have a SLOT of 0,
indicating that they cannot co-exist on the system. These are basically two
independent packages, bundled as single ebuild, each of which should have its
own core package metadata such as SLOT. Also consider "-dev" packages offered
by Debian and RPM-based distributions, which may have their own conflict rules.

Proposed Solution and Impact
----------------------------

Implement multi-sub-package support in a future redesign of Portage. This will
allow separate sub-components of a package to have their own conflict rules,
and allow complex packages to be handled more effectively within ebuilds.

Inability to Generate Low-Level Merge Lists
===========================================

Currently, emerge uses dependencies to determine what packages to merge. This
is an automation feature that enables users to get the packages merged that
they want, without resolving dependencies themselves. However, sometimes it is
necessary to emerge packages in a particular order that may not be easily
expressed using dependencies, for example - emerge system or a core toolchain
upgrade.  Often, scripts are required in order to "direct" emerge to merge
packages in a particular order, by calling emerge multiple times.

Proposed Solution and Impact
----------------------------

It would be convenient if Portage had support for "build scripts", or could
generate low-level, arbitrary merge lists using an API, without having to
just rely on dependencies to generate these merge lists behind the scenes
using hard-coded algorithms. Then, dependency resolution could be build on top
of this functionality, as a function that outputs a merge list.

This functionality would be more easily implemented in an entirely new Portage
code-base.
