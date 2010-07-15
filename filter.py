
class PkgAtomFilter(object):

	# Generic object

class Level1PkgAtomFilter(object):

	# Level1 means the filter can be applied based on version alone (no SLOT or other metadata)
	# and does not require a repository reference. Faster and simpler.

class Level2PkgAtomFilter(object):

	# Level2 means the filter can be applied but requires accessing metadata and/or Distro root
	# to look at distro-specific configuration. Slower and more complex.

class FilterGroup(object):
	
	# a collection of filters, such as from a package.mask file. Can also be heirarchically linked
	# with other filters.

class MultiFilterGroup(object):

class MaskFilterGroup(object):

class UnmaskFilterGroup(object):

