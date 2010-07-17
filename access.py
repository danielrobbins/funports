import os
import commands

class FilePath(object):

	def __init__(self,path,base_path="/"):
		self._path = path
		self._base_path = base_path

	def __eq__(self,other):
		return self.diskpath == other.diskpath

	def __hash__(self):
		return hash(self.diskpath)

	def __repr__(self):
		return "FilePath(%s,%s)" % ( self.base_path, self.path )

	@property
	def path(self):
		return self._path

	@path.setter
	def path(self,value):
		return FilePath(value,base_path=self.base_path)

	@property
	def base_path(self):
		return self._base_path

	def __add__(self,other):
		return FilePath(os.path.join(self.path,other),base_path=self.base_path)

	@property
	def diskpath(self):
		return os.path.normpath(os.path.join(self.base_path,self.path))

	def adjpath(self,change):

		# This returns a new path -
		# foo.adjpath("..") would return the previous directory.
		# foo.adjpath("foo") would return a path to the current path plus "/foo"
		# foo.adjpath("/foo") would return an absolute path "/foo.
		# The path root for the new path is the same as this path.

		if os.path.isabs(change):
			return FilePath(change,base_path=self.base_path)
		else:
			return FilePath(os.path.normpath(os.path.join(self.path, change)),base_path=self.base_path)


class FileAccessInterface(object):

	def __init__(self,base_path):
		self.base_path = os.path.realpath(base_path)
	
	def open(self,path, mode):
		return open(path.diskpath, mode)

	def listdir(self,path):
		return os.listdir(path.diskpath)

	def exists(self,path):
		return os.path.exists(path.diskpath)

	def isdir(self,path):
		return os.path.isdir(path.diskpath)

	def diskpath(self,path):
		return os.path.normpath(path.diskpath)

	def grabfile(self,path):
		# grabfile() is a simple helper method that grabs the contents
		# of a typical portage configuration file, minus any lines
		# beginning with "#", and returns each line as an item in a
		# list. Newlines are stripped. This helper function looks at
		# the repository base_path, not any overlays.  If a directory
		# is specified, the contents of the directory are concatenated
		# and returned.
		out=[]	
		if not self.exists(path):
			return out
		if self.isdir(path):
			scan = self.listdir(path)
			scan = map(lambda(x): "%s/%s" % ( path, x ), scan )
		else:
			scan = [ path ]
		for path in scan:
			a=self.open(path,"r")
			for line in a.readlines():
				if len(line) and line[0] != "#":
					out.append(line[:-1])
			a.close()
		return out

	def collapse_files(self,paths):
		pass
		out = {}
		for file in paths:
			if self.exists(file):
				f=self.open(file,"r")	
				for line in f.readlines():
					items = line.split()
					if len(items) and item[0][0] != "#":
						out[item[0]] = items[1:]
				f.close()
		return out

class GitAccessInterface(FileAccessInterface):

	def __init__(self,base_path):
		self.base_path = base_path
		self.tree = {}

	def populate(self):
		print commands.getoutput("cd %s; git ls-tree --name-only HEAD" % self.base_path)

"""
import subprocess
from grp import getgrnam

	def do(self,action,atom,env={}):
		ref = self.getRef(atom)
		if ref == None:
			return None
		master_env = {
			"PORTAGE_TMPDIR" : "/var/tmp/portage",
			"EBUILD" : ref.repo.access.diskpath(ref.path),
			"EBUILD_PHASE" : action,
			"ECLASSDIR" : self.diskpath(self.path["eclass_dir"]),
			"PORTDIR" : self.base_path,
			"PORTDIR_OVERLAY" : " ".join(self.overlays),
			"PORTAGE_GID" : repr(getgrnam("portage")[2]),
			"CATEGORY" : atom.cat,
			"PF" : atom.pf,
			"P" : atom.p,
			"PV" : atom.pv
		} 
		master_env.update(env)	
		pr, pw = os.pipe()
		a = os.dup(pw)
		os.dup2(a,9)
		p = subprocess.call(["/usr/lib/portage/bin/ebuild.sh",action],env=master_env,close_fds=False)
		a = os.read(pr, 100000)
		print a.split("\n")
		os.close(pr)
		os.close(pw)
"""

if __name__ == "__main__":
	a=FilePath("/foo/bar")
	print a
	print a + "/oni"
	print a
	print a + "oni"
