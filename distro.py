class DistributionRoot(object):

	def __init__(self, root):
		self.root = root
		self._filtergroup = None

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


