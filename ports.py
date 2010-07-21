



repo = {
	r"profiles/[\w-]+" : Profile,
	r"[^/]+" : Category,
	r"[^/]+/[^/]+" : CatPkg,
	r"[^/]+/[^/]+/[^_]+" : PkgAtom,
}

disk = {
	r"[^/]+" : Category,
	r"[^/]+/[^/]+" : CatPkg,
	r"[^/]+/[^/]+/[^_]+" : PkgAtom,




class Root(object):

	def __init__(self,path):
		self.path = path

	def __hash__(self):
		return hash(path)
	
	def __eq__(self,other):
		return self.path == other.path

class Path(object):

	def __init__(self,root,path):
		self.root = root
		self.path = path
	
	def __hash__(self):
		return hash(self.fullpath)

	def adjpath(self,change):

		# This returns a new path -
		# foo.adjpath("..") would return the previous directory.
		# foo.adjpath("foo") would return a path to the current path plus "/foo"
		# foo.adjpath("/foo") would return an absolute path "/foo.
		# The path root for the new path is the same as this path.

		if os.path.isabs(change):
			return Path(root=self.root,path=change)
		else:
			return Path(root=self.root,path=os.path.normpath(os.path.join(self.path, change)))

	def contents(self):
		objs = set()
		for file in os.path.listdir(self.fullpath):
			objs.add(self.adjpath(file))
		return objs

	@property
	def fullpath(self):
		return os.path.join(self.root.path,self.path)
	
	def exists(self):
		return os.path.exists(self.fullpath)

	def open(self,mode):
		return open(self.fullpath,mode)

class PortageRepository(Path):

	def contents(self):
		cats = set(os.path.listdir(self.fullpath) & valid
		objs = set()
		for cat in cats:
			objs.add(Category(root=self.root,path=cat))
		return objs

	@property
	def valid(self):	
		return set(self.path.adjpath("profiles/categories").grabfile())	

class Category(Path):

	def contents(self):
		objs = set()
		for catpkg in os.path.listdir(self.fullpath):
			objs.add(CatPkg(root=self.root,path="%s/%s" % (self.path, catpkg)))
		return objs

class CatPkg(Path):

	def contents(self):
		objs = set()
		for pkgatom in os.path.listdir(self.fullpath):
			if pkgatom[-7:] != ".ebuild":
				continue
			vers = pkgatom[len(self.path):-7]
			objs.add(PkgAtom(root=self.root,path="%s/%s" % (self.path, vers)))
		return objs

class PkgAtom(Path):

	def exists(self):

class GitPortageRoot(Root):

class ProfileRoot(Root):


