class PortageProfile(ConfigurationData):

	# While the Portage profile is traditinally stored within the Portage
	# repository, it makes sense to not impose this restriction on the 
	# PortageProfile object. This PortageProfile object can exist anywhere
	# on the filesystem.

	def __init__(self, root):
		self.root = root


