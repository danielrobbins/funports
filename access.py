class FileAccessInterface(object):

	def __init__(self,base_path):
		self.base_path = base_path
	
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

class GitAccessInterface(FileAccessInterface):

	def __init__(self,base_path):
		self.base_path = base_path
		self.tree = {}

	def populate(self):
		print commands.getoutput("cd %s; git ls-tree --name-only HEAD" % self.base_path)


