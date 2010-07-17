import os
import commands

class FileAccessInterface(object):

	def __init__(self,base_path):
		self.base_path = os.path.realpath(base_path)
	
	def open(self,file, mode):
		return open("%s/%s" % ( self.base_path, file ), mode)

	def listdir(self,path):
		return os.listdir(os.path.normpath("%s/%s" % ( self.base_path, path ) ))

	def exists(self,path):
		return os.path.exists("%s/%s" % ( self.base_path, path ))

	def isdir(self,path):
		return os.path.isdir("%s/%s" % ( self.base_path, path ))

	def diskpath(self,path):
		return os.path.normpath("%s/%s" % ( self.base_path, path ))

	def adjpath(self,root,change):
		# if change is an absolute path, return change
		# if change is relative path, return new change path relative
		# to "root" (typically "current directory")
		if os.path.isabs(change):
			return change
		else:
			return os.path.normpath(os.path.join(root, change))

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

	def collapse_files(self,files):
		pass
		out = {}
		for file in files:
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
