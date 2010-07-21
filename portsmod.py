#!/usr/bin/python2

# Copyright 2010 Daniel Robbins, Funtoo Technologies, LLC.
#
# FUNTOO TECHNOLOGIES INTERNAL SOURCE CODE
# ALPHA - DO NOT RELEASE - NOT FOR DISTRIBUTION
#
# The unauthorized reproduction or distribution of this copyrighted work is
# illegal, and may result in civil or criminal liability.

# NOTE: Keep the scope of this small so the import list can be minimized
# and easily managed:

import os

import portage.versions

import access


# This module implements a simplified mechanism to access the contents of a
# Portage tree. In addition, the PortageRepository class (see below) has
# an elegant design that should support alternate Portage repository layouts
# as well as alternate backend storage formats. An effort has been made to
# keep things simple and extendable.

class CatPkg(object):

	# CatPkg is an object that is used to specify a particular group of
	# ebuilds that is identified by a category and package name, such
	# as "sys-apps/portage".

	def __repr__(self):
		return "CatPkg(%s)" % self.catpkg

	def __init__(self,catpkg):
		# catpkg = something like "sys-apps/portage"
		self.catpkg = catpkg

	@property
	def cat(self):
		#i.e. "sys-apps"
		return self.catpkg.split("/")[0]
	
	@property
	def pkg(self):
		#i.e. "portage"
		return self.catpkg.split("/")[1]

	@property
	def p(self):
		#i.e. "portage"
		return self.pkg

	def __getitem__(self,key):
		
		# This method allows properties to be grabbed using atom["cat"]
		# as well as standard atom.cat. This comes in handy when expanding
		# strings: 
		#
		# path = "%(cat)s/%(p)s" % atom

		if hasattr(self,key):
			return getattr(self,key)

class PkgAtom(object):

	# Our PkgAtom is different from a dependency, and literally means "a
	# specific reference to an individual package". This package could be a
	# specific ebuild in a Portage tree, or a specific record in
	# /var/db/pkg indicating that the package is installed. An "PkgAtom"
	# uniquely references one package without ambiguity. 
	
	# LOGICAL TEST OF AN ATOM: Two identical atoms cannot co-exist in a
	# single repository. 

	# LOGICAL TEST OF WHAT IS CONSIDERED ATOM DATA: Any data that can be
	# used to specify a uniquely-existing package in a repository, that is
	# capable of co-existing with other similar atoms, should be considered
	# atom data. Otherwise, the data should not be considered atom data.
	# Example: slots *are* part of an PkgAtom for repositories of installed or
	# built packages, because foo/bar-1.0:slot=3 and foo/bar-1.0:slot=4 can
	# co-exist in these repositories.

	# So note that a package *slot* is considered part of the PkgAtom for
	# packages that have already been installed or built. However, slot is
	# *not* part of the PkgAtom for packages in a Portage tree, as the slot
	# can be undefined at this point. For installed packages, the slot can
	# be specified as follows:

	# sys-apps/portage-2.2_rc67:slot=3
	
	# However, USE variables are not considered PkgAtom data for any type of
	# repository because "foo/bar-1.0[gleep]" and "foo/bar-1.0[boing]"
	# cannot co-exist independently in a Portage tree *or* installed
	# package repository.

	# The PkgAtom object provides a standard class for describing a package
	# atom, in the abstract. Helper methods/properties are provided to
	# access the atom's various attributes, such as package name, category,
	# package version, revision, etc. The package atom is not tied to a
	# particular Portage repository, and does not have an on-disk path. If
	# you want an on-disk path for an PkgAtom, you'd create a new PkgAtom and
	# pass it to the PortageRepository object and it will tell you.

	# As touched on above, there is a text representation of an PkgAtom that
	# is standardized, which is:

	# <cat>/<p>{:key1=val1{:key2=val2...}}

	# <cat> = category name
	# <p> = full package name and version (including optional revision)
	# :key=val = optional additional data in key=value format. values can
	# consist of any printable character except a colon. Additional key
	# values can be specified by appending another colon to the line,
	# such as:

	# sys-foo/bar-1.0:slot=1:python=2.6:keywords=foo,bar,oni

	# (Although you wouldn't want to specify keywords in an PkgAtom as it
	# wouldn't pass the LOGICAL TESTS above.)
	
	def __repr__(self):
		return "PkgAtom(%s)" % self.atom

	def __init__(self,atom):
		self.atom = atom
		self._keysplit = None
		self._keys = None
		self._cpvs = None

	def __getitem__(self,key):
		
		# This method allows properties to be grabbed using atom["cat"]
		# as well as standard atom.cat. This comes in handy when expanding
		# strings: 
		#
		# path = "%(cat)s/%(p)s" % atom

		if hasattr(self,key):
			return getattr(self,key)

	@property
	def keys(self):
		
		# Additional atomdata key/value pairs in dictionary format. These
		# are created on initialization and you should not modify the
		# keys property directly.

		if self._keys == None:
			self._keys = {}
			for meta in self._keysplit[1:]:
				key, val = meta.split("=",1)
				self._keys[key] = val
		return self._keys

	@property
	def cpvs(self):
		# cpvs = "catpkgsplit string" and is used by other properties
		if self._cpvs == None:
			self._keysplit = self.atom.split(":")
			self._cpvs = portage.versions.catpkgsplit(self._keysplit[0])
		return self._cpvs
	
	@property
	def cat(self):
		#i.e. "sys-apps"
		return self.atom.split("/")[0]
	
	@property
	def pf(self):
		#i.e. "portage-2.2_rc67-r1"
		return self.atom.split("/")[1]
	
	@property
	def p(self):
		#i.e. "portage"
		return self.cpvs[1]

	@property
	def pv(self):
		#i.e. "2.2_rc67"
		return self.cpvs[2]
	
	@property
	def pr(self):
		#i.e. "r1"
		return self.cpvs[3]

	def __eq__(self,other):
		# We can only test for atom equality, but cannot otherwise compare them.
		# PkgAtoms are equal when they reference the same unique cat/pkg and have
		# the same key data.
		return self.cpvs == other.cpvs and self.keys == other.keys

class PkgAtomFilter(object):

	# When we read package.mask, we create a bunch of PkgAtomFilters for each mask entry 
	# we find. When the Portage tree is queried for "visible" packages, these PkgAtomFilters
	# are used to reduce the set of packages returned.

	# The workhorse method of the PkgAtomFilter is apply, which will return a set of visible
	# and masked packages:

	# >>> vis, masked = my.apply(asdlfkdsjf)

	def __init__(self,depstring):
		self.depstring = depstring

	def apply(self,pkgatomset):
		pass

	@property
	def cat(self):
		return "foo"

	@property
	def p(self):
		return "bar"

class EClassAtom(object):

	def __repr__(self):
		return "EClassAtom(%s)" % self.atom

	def __init__(self,atom):
		self.atom = atom

class Adapter(object):

	def __init__(self,**args):
		for arg in args.keys():
			setattr(self,arg,args[arg])

class PortageRepository(object):

	# PortageRepository provides an easy-to-use and elegant means of
	# accessing an on-disk Gentoo/Funtoo Portage repository. It is designed
	# to allow for some abstraction of the underlying repository structure.

	# PortageRepository should be suitable for creating subclasses accessed
	# a remote Portage repository, or accessed the contents of .git
	# metadata to view the repository, or even a Portage repository with a
	# non-standard filesystem layout.

	# This class has minimal external source code dependencies, utilizing
	# only "portage.versions" from the official Portage sources for version
	# splitting, etc. This allows this code to be easily used by utility
	# programs.

	# Subclasses can override PortageRepository's init_paths() method to
	# implement alternate repository layouts, or override accessor
	# functions (via self.access) to implement alternate storage
	# mechanisms.

	def __repr__(self):
		return "PortageRepository(%s)" % self.base_path.diskpath

	# The self._has_*() and self._*_list() methods below are used to query
	# the Portage repository. If you want to change the structure of the
	# Portage repository, you would override these methods in a subclass,
	# and possibly update self.init_paths() as needed to ensure that the
	# Adapters reference your methods (we don't call these methods
	# directly, instead we look at self.atom_map which will point to the
	# right methods to use for each object type in the repository.)

	# Note that the _has_*() methods will return a path to the object if
	# it exists, otherwise None. This behavior should be preserved as it
	# improves the utility of these methods. Better than True/False.

	# The _has_*() and _*_list() methods do not recurse through overlays.
	# They query the local repository only. That is why these methods
	# should not be called by other code.

	# Also note that I don't implement _eclass_list(), as eclasses are
	# not something that you need to query in this way. You just need
	# to find the right eclasses from your base tree and overlays, and
	# _has_eclass() is sufficient to get this done.

	def _has_eclass(self,arg,**args):
		path = self.path.adjpath("eclass/%s.eclass" % arg.atom)
		if path.exists():
			return path.path

	def _has_catpkg(self,catpkg):
		path = self.path.adjpath(catpkg.catpkg)
		if path.isdir():
			return path.path

	def _catpkg_list(self,categories=None):
		cp = []
		if categories == None:
			categories = self.categories
		for cat in categories:
			if not self.path.adjpath(cat).isdir():
				continue
			for pkg in self.path.adjpath(cat).listdir():
				cp.append(CatPkg("%s/%s" % ( cat, pkg )))
		return cp

	def _has_pkgatom(self,pkgatom):
		path = self.path.adjpath("%s/%s/%s.ebuild" % ( pkgatom.cat, pkgatom.p, pkgatom.pf ))
		if path.exists():
			return path.path

	def _pkgatom_list(self,catpkgs=None):
		pa = []
		if catpkgs == None:
			catpkgs = self._catpkg_list()
		for catpkg in catpkgs:
			if not self.access.isdir(catpkg.catpkg):
				continue
			for file in self.access.listdir(catpkg.catpkg):
				if file[-7:] == ".ebuild":
					pa.append(PkgAtom("%s/%s" % ( catpkg.cat, file[:-7])))
		return pa

	def init_paths(self):

		# The Portage repository structure is abstracted somewhat using
		# the settings defined in the init_paths() function. This
		# function is automatically called by __init__() so you can
		# simply override this method for any variant PortageRepository
		# layouts without having to mess with __init__()

		self.path = {
			"eclass_dir" : self.path.adjpath("eclass"),
			"categories" : self.path.adjpath("profiles/categories"),
			"info_pkgs" : self.path.adjpath("profiles/info_pkgs"),
			"info_vars" : self.path.adjpath("profiles/info_vars")
		}

		#self.config_map = {
		#	"categories" : {
		#		"read" : 
		
		# self.atom_map defines the different types of Atoms that are
		# in the PortageTree, and points to internal methods for 
		# determining if an Atom exists ("has") and getting a list of
		# Atoms ("list"), and points to a list of overlays to use
		# when we need to take overlays into account.

		# Eclasses and packages can have different inheritance
		# patterns, and the "overlays" setting below allows their
		# inheritance patterns to be different.
		
		# The Adapter objects are a convenience so I don't need to use
		# recursive dictionaries and type
		# self.atom_map[objtype]["overlays"].  Instead I can type
		# self.atom_map[objtype].overlays and avoid one hash lookup to
		# boot. It also makes the code easier to read. All the Adapter
		# does is create object attributes and methods based on the
		# keyword arguments you pass to __init__().

		self.atom_map = {
			CatPkg : Adapter( 
					has=self._has_catpkg,
					list=self._catpkg_list,
					overlays=self.overlays
			),
			PkgAtom: Adapter( 
					has=self._has_pkgatom, 
					list=self._pkgatom_list,
					overlays=self.overlays  
			),
			EClassAtom: Adapter(
					has=self._has_eclass, 
					overlays=self.eclass_overlays 
			)
		}

	def __init__(self,path, **args):

		# initialize variables. Also note that self.overlays contains a
		# list of child overlays, which in turn can have their own
		# child overlays (even though classic Portage doesn't allow
		# overlays to have their own overlays, this is supported by
		# this code. Typically just your "main" tree would have
		# overlays and overlays would not have their own overlays.)
		
		# Overlays at the beginning of the self.overlays list have
		# precedence.
		#
		# Here's how you would set up /usr/portage as the base tree
		# with /var/tmp/git/funtoo-overlay as its overlay:
		#
		# a = PortageRepository("/usr/portage")
		# b = PortageRepository("/var/tmp/git/funtoo-overlay",overlay=True)
		# a.overlays = [b]
		#
		# You would then call "a" and it would automatically access
		# its overlays as needed.
		#
		# Eclass Overlays are normally disabled, but can be enabled
		# using the eclass_overlays variable:
		#
		# a.eclass_overlays = [b]
		#
		# Now, not only will ebuilds in "b" complement and override
		# those ebuilds in "a", but eclasses in "b" will also complement
		# and override those in "a".

		self.overlays = []
		self.eclass_overlays = []

		# self.base_path is a variable pointing to the starting path
		# of the Portage tree, i.e. "/usr/portage".

		self.path = path.repository(self)

		# specifying "overlay=True" to __init__() will set self.overlay
		# to True. This is not really used for anything right now other
		# than making any code using this class easier to read.

		if "overlay" in args and args["overlay"] == True:
			self.overlay = True
		else:
			self.overlay = False

		# self.init_paths() sets up repository-specific configuration,
		# and can be overridden by PortageRepository subclasses without
		# having to mess around with hacking the standard __init__()
		# logic:

		self.init_paths()

	@property
	def info_pkgs(self,recurse=True):

		# Returns "info_pkgs" from repository, which is a set
		# of ebuild atoms that "emerge --info" should display
		# versions of (used for user bug reports)

		return self.__grabset__(self.path["info_pkgs"],recurse)

	@property
	def info_vars(self,recurse=True):
		
		# Returns "info_vars" from repository, which is a set
		# of variables that "emerge --info" should display.
		# (Used for user bug reports.)
		
		return self.__grabset__(self.path["info_vars"],recurse)

	@property
	def categories(self,recurse=True):
		
		# This property will return a set containing all valid
		# categories. By default, overlays are scanned as well.
		
		return self.__grabset__(self.path["categories"],recurse)

	def __grabset__(self,path,recurse=True):
		
		# This is a helper function for various methods above
		# that need to grab data from a file in the repo and
		# return the data. This helper function *will* recurse
		# through child overlays and append the child data
		# -- useful for categories, info_pkgs, and info_vars,
		# but probably not what you want for package.mask :)

		out = set(path.grabfile())
		if recurse:
			for overlay in self.overlays:
				out = out | overlay.__grabset__(path)
		return out

	def getList(self,otype,qlist,recurse=True):

		# getList() implements the generic recursive overlay lookup
		# logic for returning a list of objects that match certain
		# criteria.
		#
		# Typically, you'd use it like this:
		#
		# >>> repo.getList(CatPkg,["sys-apps","dev-lang"]) 
		#
		# (return list of CatPkgs in categories "sys-apps" and
		# "dev-lang")
		#
		# >>> repo.getList(PkgAtom,[CatPkg("sys-apps/portage"),CatPkg("dev-lang/python")])
		#
		# (return list of PkgAtoms in CatPkgs "sys-apps/portage" and
		# "dev-lang/python")
		#
		# getList accepts a query *list* rather than a single query so
		# it can efficiently handle bulk queries. If you just want to
		# query one thing, then pass it a single-item list.

		atoms = set()
		if recurse:
			for overlay in self.atom_map[otype].overlays:
				atoms = atoms | overlay.getList(otype,qlist,recurse)
		atoms = atoms | set(self.atom_map[otype].list(qlist))
		return atoms

	def getRef(self,atom,recurse=True,**args):

		# This is a handy method that, when given an Atom of some kind,
		# will return a reference to it if it exists. Overlays are
		# scanned recursively and the "right" match is found, meaning
		# that if an overlay has the Atom then it will return the atom
		# in the overlay.
		#	
		# A "reference" is actually a "RepositoryObjRef" object, which
		# gives you all the info you need about the atom that was
		# found. The ref contains a reference to the repository that
		# owns the object, a reference to the object itself (PkgAtom,
		# CatPkg, etc.), and path to the object relative to the object
		# root.
		#
		# If the atom is not found, None is returned.
		#
		# Use it like this:
		#
		# print repo.getRef(PkgAtom("sys-apps/portage-2.2_rc67-r2"))
		# print repo.getRef(EClassAtom("autotools")) print
		# repo.getRef(CatPkg("sys-libs/glibc"))

		if recurse:
			for overlay in self.atom_map[type(atom)].overlays:
				ref = overlay.getRef(atom,recurse,**args)
				if ref != None:
					return ref
			path = self.atom_map[type(atom)].has(atom, **args)
			if path != None:
				return RepositoryObjRef(self,atom,path)
			else:
				return None

	# In a classic Portage tree, the categories and ebuilds in the tree are
	# used to define the authoritative contents of the tree, but when you
	# want to access metadata inside an ebuild, a metadata cache is
	# examined first. If the metadata cache data is fresh, internal ebuild
	# data is pulled from the metadata cache. If the metdata cache is
	# stale, it is freshened by running "ebuild.sh depend" (which sources
	# the ebuild), and then new, fresh metadata is generated and stored in
	# the cache, and this new metadata is then used. All metadata required
	# for emerge to function properly exists in the metadata cache.

	# So in the classic Portage tree implementation, there are two
	# repositories that must be looked at - one, the Portage tree, to see
	# what ebuilds exist, (and also to get profile and masking
	# information), and another location, the metadata cache, to retrieve
	# the metadata contents of the ebuild. If you need to actually run the
	# ebuild, you look back at the Portage tree. While this is complicated,
	# it allows users to modify ebuilds in their Portage tree and have them
	# be used by Portage. It also adds complication to the distro side of
	# things - new metadata must be generated, and injected into the Portage
	# tree inside the metadata/ directory, so that after an emerge --sync,
	# the user's metadata can be quickly updated.

	# It may be useful to implement a new tree architecture, where a new
	# type of Portage repository can exist that consists solely of
	# metadata, plus profile and mask information. Then the metadata and
	# Portage tree are unified in the sense that the metadata is always
	# considered the authoritative source of what exists in the tree, and
	# is also the authoritative source for ebuild metadata. Then, emerge
	# can actually resolve dependencies without the need for ebuilds to be
	# present! If an ebuild is needed (for merging,) it can be fetched from
	# the Web just like a source file. Tarballs can be served from a Web
	# service using a RESTful API. This may seem unusual, but fetching is
	# already generally necessary for an ebuild to be compiled and merged
	# as source files are typically not local.

	# This model would dramatically reduce the size of the Portage tree,
	# and simplify the Portage code base due to the fact that it is a 
	# simpler and cleaner architecture. However, this new model of Portage
	# tree would not allow ebuilds to be modified. In effect, this new
	# Portage tree architecture would present an immutable tree, where
	# the contents of the tree are fetched from a remote server. This
	# differs from the classic behavior of allowing users to modify and
	# add their own ebuilds.

	# However, this does not mean that the new Portage tree architecture is
	# a bad idea. First, many users are not interested in modifying
	# ebuilds. For these users, the additional flexibility afforded by the
	# current architecture offers no advantage. In addition, the small
	# number of people who do need to locally modify or add ebuilds may be
	# better served by using an overlay to accomplish this. Currently,
	# overlays are not capable enough to allow all possible desired
	# modifications to be achieved via an overlay - for example, I think it
	# is currently impossible to say "look at my overlay for all sys-apps/
	# portage packages, and *ignore* all ebuilds in the immutable tree upon
	# which my overlay rests" - but as these functions are added to
	# Portage, then the immutable tree concept becomes a possibility.

	# The potential benefits of an immutable tree are significant:

	# 2 to 12MB tree size rather than 150-300MB tree size
	# 40-500 inodes rather than hundreds of thousands of inodes
	# No need to synchronize metadata on users systems
	# emerge sync traffic reduced by orders of magnitude.

	# This would allow portage snapshots to be 2 to 12MB in size.
	# emerge sync would be almost instantaneous.
	# as the cache would always be fresh, "stale" metadata would not
	# exist and this would result in significantly faster dependency
	# calculations.

	# This is a great benefit, but in order to implement, the overlay 
	# model must be augmented to allow for local modification of Portage
	# trees without difficulty.
				
if __name__ == "__main__":
	from access import *
	a=PortageRepository(FilePath("/var/git/portage-mini-2010"))
	b=PortageRepository(FilePath("/root/git/funtoo-overlay"),overlay=True)
	a.overlays=[b]
	print a.getRef(PkgAtom("sys-apps/portage-2.2_rc67-r2"))
	print a.getRef(EClassAtom("autotools"))
	print a.getRef(CatPkg("sys-libs/glibc"))
	print a.getList(CatPkg,["sys-apps","sys-libs"])
	print
	print a.getList(PkgAtom,[CatPkg("sys-apps/portage")])

