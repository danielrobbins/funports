import ports
import profile
from configfile import ConfigFile

class DistributionRoot(object):

	def __init__(self, root):
		self.root = root
		self._config = None
		self._portrepo = None

	@property
	def config(self):
		if self._config == None:
			
			# First, use make.globals and make.conf to get a ref to our
			# Portage repository:
			
			a=ConfigFile("/usr/share/portage/config/make.globals")
			c=ConfigFile("/etc/make.conf",parent=a)
			print c["PORTDIR"]
			self._portrepo=ports.PortageRepository(c["PORTDIR"])



a=DistributionRoot("/")
print a.config
print a._portrepo
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
