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
		
		self.parents = [ ]
		parent = "%s/parent" % self.profile_path
		if self.access.exists(parent):
			entries = self.access.grabfile(parent)
			for entry in entries:
				self.parents.append(PortageProfile(self.base_path,self.access.adjpath(self.profile_path,entry)))
	
	@property
	def defaults(self):
		conf = []
		for parent in self.parents:
			conf.extend(parent.defaults)
		myf = "%s/make.defaults" % self.profile_path
		if self.access.exists(myf):
			conf.append(self.access.diskpath(myf))
		return conf

if __name__ == "__main__":
	a=PortageProfile("/var/git/portage-mini-2010/profiles","default/linux/amd64/2008.0")
	print a.parents
	print a.defaults
