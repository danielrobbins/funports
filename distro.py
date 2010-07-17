from ports import *
from profile import PortageProfile
from configfile import ConfigFile
import os


class DistroAdapter(object):

	# The DistroAdapter should be used to glean information about a particular
	# Gentoo operating system installation on a particular root filesystem
	# (root filesystem path is specified as an argument to __init__()).

	# The DistroAdapter should not provide "action" methods itself, but should
	# return configuration and objects that have their own "action" methods.
	# We should call DistroAdapter to get information and objects with which
	# to do stuff, not to do stuff directly. I don't want DistroAdapter to
	# turn into a bloated class that is required for doing anything. Instead,
	# it should be used to get your bearings, then you can ignore it and work
	# with the other classes (PortageTree, ConfigFile, etc.) to get things
	# done.

	# DistroAdapter will take care of caching where possible to reduce IO and
	# computation when querying the tree.

	def __init__(self,root):

		self.root = os.path.normpath(root)
		if self.root[-1] != "/":
			self.root = self.root + "/"

		self._global_config = None
		self._general_config = None
		self._complete_config = None
		self._config = None
		self._profile = None
		self._portdir = None

	@property 
	def portdir(self):
		
		# self.portdir references the Portage tree referenced by the
		# /etc/make.conf file stored on the DistroAdapter's root
		# filesystem.

		if self._portdir == None:
			self._portdir = PortageRepository(os.path.normpath("%s/%s" % (self.root, self.general_config["PORTDIR"])))
		return self._portdir

	@property
	def profile(self):

		# This is a property to reference the currently-configured
		# Portage profile on the DistroAdapter's root filesystem.

		if self._profile == None:

			if "PROFILE" in self.general_config:
				
				# This is a new way of setting the profile - define a PROFILE variable in /etc/make.conf
				# with PROFILE set to something like "default/linux/amd64/2008.0". The profile is assumed
				# to be relative to the profile root of "PORTDIR/profiles"

				profroot = os.path.normpath("%s/%s/profiles" % (self.root, self.general_config["PORTDIR"]))
				profname = self.general_config["PROFILE"]

			else:
				# This is the traditional way to set the Portage profile - an /etc/make.profile symlink.
				# Here, we look at the destination of the symlink (typically something like
				# ../usr/portage/profiles/default/linux/amd64/2008.0,) and we split this destination
				# right after the "profiles/" - the first part is the path to the profile root, the
				# second part is the path (relative to the profile root) to the profile.

				proftemp = os.path.normpath("%setc/%s" %  ( self.root, os.readlink("%s/etc/make.profile" % self.root )))
				splitter = proftemp.find("profiles/") + len("profiles/")
				profroot = os.path.realpath(proftemp[0:splitter])
				profname = proftemp[splitter:]

			self._profile = PortageProfile(profroot,profname)

		return self._profile

	
	@property
	def global_config(self):

		# When a ConfigFile is loaded, its variables are expanded. This
		# means that You can have two ConfigFile objects referencing
		# the same configuration file, but they will have different
		# data *if* their parents were set differently.  This is
		# because the parent is used for variable expansion if a var is
		# referenced that has not been defined locally.

		# However, if two ConfigFile objects have the same parent, and
		# reference the same file, they will have the same data, and
		# can be used as parents multiple *other* ConfigFiles with no
		# problem.

		# Such is the case with /etc/make.globals - it has no parent, so
		# we can safely re-use it multiple times as a parent. Therefore,
		# this property exists so we only load it once. Other code should
		# access /etc/make.globals by simply referencing self.global_config.


		if self._global_config == None:
			self._global_config = ConfigFile(os.path.normpath("%s/%s" % ( self.root, "/etc/make.globals" )))
		return self._global_config


	@property
	def general_config(self):

		# The "general" configuration is the combination of /etc/make.profile
		# and /etc/make.globals - enough to get general settings like PORTDIR
		# that are not profile-specific.
	
		if self._general_config == None:
			self._general_config = ConfigFile(os.path.normpath("%s/%s" % ( self.root, "/etc/make.conf" )), parent=self.global_config)
		return self._general_config

	@property
	def complete_config(self):

		# This is called the "complete" config because it consists of
		# /etc/make.conf, plus all the make.defaults files in the
		# profile, plus /etc/make.globals.  This configuration is
		# suitable as a basis for ebuild and other operations because
		# it contains a full set of configuration settings related to
		# building.

		if self._complete_config == None:
			
			# Create list of all configuration files to add as
			# children, including cascading profile make.defaults
			# files...

			cfglist = self.profile["make.defaults"] #returns list of files from cascaded profile
			cfglist.append(os.path.normpath("%s/%s" % (self.root, "/etc/make.conf")))

			# Create a stack of ConfigFile objects, each pointing
			# to the previous, with "/etc/make.conf" at top, and
			# the ConfigFile("/etc/make.globals") sitting at the
			# bottom:

			stack = self.global_config
			for cfname in cfglist:
				stack = ConfigFile(cfname, parent=stack)

			# Set self._complete_config to the top of stack (the
			# one referencing "/etc/make.conf") - the others are
			# referenced in .parent(.parent), etc.

			self._complete_config = stack

		return self._complete_config


if __name__ == "__main__":

	print "COMPLETE CONFIGURATION"
	print "======================"
	print

	a=DistroAdapter("/")
	for key in a.complete_config.keys():
		print "%s: '%s'" % (key, a.complete_config[key])
	print
	print "CONFIG FILE HEIRARCHY"
	print "====================="
	print
	foo = a.complete_config
	while foo != None:
		print foo
		foo = foo.parent


	print 
	print "PORTAGE TREE"
	print "============"
	print
	print a.portdir

"""
	@property
	def filterGroup(self):
		if self._filtergroup == None:
			b=UnmaskFilterGroup("/etc/portage/package.unmask")
			a=MaskFilterGroup("/etc/portage/package.mask")
			d=UnmaskFilterGroup("/usr/portage/profiles/package.unmask")
			c=MaskFilterGroup("/usr/portage/profiles/package.mask")
			# recurse into profile.....
		self._filtergroup=MultiFilterGroup((b,a,d,c))
		return self._filtergroup

"""
