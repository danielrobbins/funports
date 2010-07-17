import os
from access import FileAccessInterface

class PortageProfile(object):

	# While the Portage profile is traditinally stored within the Portage
	# repository, it makes sense to not impose this restriction on the 
	# PortageProfile object. This PortageProfile object can exist anywhere
	# on the filesystem.

	def __repr__(self):
		return "PortageProfile(%s)" % self.profile_path

	def __init__(self, base_path, profile_path):
		self.base_path = base_path
		self.profile_path = profile_path
		self.access = FileAccessInterface(self.base_path)
		self._cascaded_items = {}
		
		self.parents = [ ]
		parent = "%s/parent" % self.profile_path
		if self.access.exists(parent):
			entries = self.access.grabfile(parent)
			for entry in entries:
				self.parents.append(PortageProfile(self.base_path,self.access.adjpath(self.profile_path,entry)))


	def __getitem__(self,key):
		if key in self._cascaded_items:
			return self._cascaded_items[key]
		else:
			return self._cascade(key)

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
				parent_item = parent[filename]
				if parent_item != None:
					found.extend(parent_item)
			myf = "%s/%s" % ( self.profile_path, filename )
			if self.access.exists(myf):
				found.append(myf)
			self._cascaded_items[filename] = found
		return self._cascaded_items[filename]

	@property
	def virtuals(self):
		virts = self._cascade("virtuals")
		return self.access.collapse_files(virts)

if __name__ == "__main__":
	a=PortageProfile("/var/git/portage-mini-2010/profiles","default/linux/amd64/2008.0")
	print a.parents
	print a["make.defaults"]
