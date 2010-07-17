import os
from access import *

class PortageProfile(object):

	# While the Portage profile is traditinally stored within the Portage
	# repository, it makes sense to not impose this restriction on the 
	# PortageProfile object. This PortageProfile object can exist anywhere
	# on the filesystem.

	def __repr__(self):
		return "PortageProfile(%s)" % self.path

	def __init__(self, path):
		# self.path is a FilePath object (defined in access.py).
		# self.path.base_path would point to e.g. "/usr/portage/profiles".
		# self.path.path would point to e.g. "default/linux/x86/2008.0".
		# self.path.diskpath would point to "/usr/portage/profiles/default/linux/x86/2008.0".
		
		self.path = path
		self.access = FileAccessInterface(self.path.base_path)
		self._cascaded_items = {}
		
		self.parents = [ ]
		parent = self.path.adjpath("parent")
		if self.access.exists(parent):
			entries = self.access.grabfile(parent)
			for entry in entries:
				self.parents.append(PortageProfile(self.path.adjpath(entry)))

	def __getitem__(self,path):
		if path in self._cascaded_items:
			return self._cascaded_items[path]
		else:
			return self._cascade(path)

	def _cascade(self,filename):

		# _cascade() will recursively look at the parent profiles and
		# the current profile and create a list of all files that have
		# a certain filename. This function is used to get a list of
		# all "virtuals" files, or all "make.defaults" files. The
		# absolute physical disk path to these files is returned in
		# list form. Already-computed lists are stored in
		# self._cascaded_items[filename], in case they are requested
		# multiple times.

		if filename not in self._cascaded_items:
			found = []
			for parent in self.parents:
				parent_items = parent[filename]
				if parent_items != None:
					found.extend(parent_items)
			myf = self.path.adjpath(filename)
			if self.access.exists(myf):
				found.append(myf)
			self._cascaded_items[filename] = found
		return self._cascaded_items[filename]

	@property
	def virtuals(self):
		virts = self._cascade("virtuals")
		return self.access.collapse_files(virts)

if __name__ == "__main__":
	a=PortageProfile(FilePath("default/linux/amd64/2008.0",base_path="/var/git/portage-mini-2010/profiles"))
	print "PROFILE PARENTS"
	print "==============="
	print
	print a.parents
	print
	print "make.defaults"
	print "============="
	print
	print a["make.defaults"]
	print
