#!/usr/bin/python2

# Copyright 2010 Daniel Robbins, Funtoo Technologies, LLC.
#
# FUNTOO TECHNOLOGIES INTERNAL SOURCE CODE
# ALPHA - DO NOT RELEASE - NOT FOR DISTRIBUTION
#
# The unauthorized reproduction or distribution of this copyrighted work is
# illegal, and may result in civil or criminal liability.

import re

class ConfigFile(object):

	def __repr__(self):
		if self.parent:
			return "ConfigFile(%s,parent=%s)" % ( self.root, self.parent.root )
		else:
			return "ConfigFile(%s)" % self.root

	# This class implements a parser and class for a Portage-style configuration
	# file.
	#
	# You can use it like this:
	# a=ConfigFile("/etc/make.globals")
	# b=ConfigFile("/etc/make.conf",parent=a)
	#
	# Then ConfigFile "b" can reference/expand variables defined in ConfigFile "a".
	#
	# The syntax is very close to standard Bourne shell variable definition syntax,
	# with the following limitations:

	# 0) Only the variable expansion "${foo}" is recognized (not "$foo")
	#
	# 1) Variable data must be enclosed in double-quotes, not single quotes (foo="bar")
	#    and not no-quotes (foo=bar).
	#
	# 2) Like shell, multiple-line variables are allowed, as follows:
	#
	#    a="foo
	#    bar"
	#  
	#    However, the trailing '"' will only be recognized as a string termination
	#    character if it appears at the end of a line, optionally padded only by
	#    whitespace. This means that our minimal parser allows the following
	#    strings to be defined, which would be illegal in shell syntax:
	#
	#    a=" "foo bar" oni "
	#    (this would set "a" to ' "foo bar" oni ')
	#
	#    This dramatically simplifies the code and speeds things up too, since we
	#    can do some parsing of lines line-by-line rather than character-by-character.
	#    It eliminates a lot of complexity that we'd need to deal with if we supported
	#    a full shell syntax.
	#
	# 3) Backslash escaping only works for '\$', '\\', and '\"' for backwards
	#    compatibility.
	#
	# Hopefully, this will fully support all existing Portage configuration files without
	# requiring complex code.

	# The configuration file format should be kept as simple as possible
	# in order to keep the implementation as simple as possible. Shell format
	# sucks, so it doesn't make sense to go crazy here.

	def __init__(self, root, parent=None):
		self.root = root
		self.data = None
		self.parent = parent

	def __getitem__(self,key):
		# this is a recursive method that is slow and ready to optimize.
		if self.data == None:
			self._read()
		if self.data.has_key(key):
			return self.data[key]
		elif self.parent and self.parent.has_key(key):
			return self.parent[key]
		else:
			return ""
		
	_valid_varname = re.compile("\A[a-zA-Z_]\w+$")
		
	def keys(self,recurse=True):
		keys = []
		if self.data == None:
			self._read()
		keys.extend(self.data.keys())
		if recurse and self.parent:
			keys.extend(self.parent.keys(recurse))
		return keys

	def getExpansion(self,vardata):
		pos = 0
		while pos < len(vardata):
			
			# quickly scan for all normal text, and yield it
			# back to the caller when we reach the end of
			# string or the first special character:
			
			pos2 = pos 
			while pos2 < len(vardata):
				if vardata[pos2] in [ "$", "\\" ]:
					break
				else:	
					pos2 += 1
		
			# return "normal" string data to caller:
			if pos != pos2:
				yield vardata[pos:pos2]

			# update pos to reflect our current position:

			pos = pos2

			# At this point, we are either at end of string, or
			# we have found a "special" character that requires
			# further processing... if we're at end, stop:

			if pos >= len(vardata):
				break

			if vardata[pos:pos+2] == "${":
				# variable - scan for end...
				pos2 = pos + 2
				while vardata[pos2] != "}":
					pos2 += 1
					if pos2 >= len(vardata):
						# unterminated variable
						print "unterminated VAR"
						return
				varname = vardata[pos+2:pos2]
				yield [varname]
				pos = pos2 + 1
			elif vardata[pos:pos+2] == "\\\\":
				yield "\\\\"
				pos += 2
			elif vardata[pos:pos+2] == '\\"':
				yield '"'
				pos += 2
			elif vardata[pos:pos+2] == '\\$':
				yield '$'
				pos += 2
			else:
				yield vardata[pos]
				pos += 1

	def expand_var(self,vardata,stack=[],recurse=True):
		out = ""
		for part in self.getExpansion(vardata):
			if type(part) == type([]):
				varname = part[0]
				if varname in self.data:
					out += self.expand_var(self.data[varname],stack[:].append(varname))
				elif recurse and self.parent and self.parent.has_key(varname):
					out += self.expand_var(self.parent[varname],stack[:].append(varname))
				else:
					continue
			else:
				out += part
		return out
	
	def __contains__(self,key):
		if self.data == None:
			self._read()
		if self.data.has_key(key):
			return True
		elif self.parent and self.parent.has_key(key):
			return True
		return False

	def has_key(self,key,recurse=True):
		if self.data == None:
			self._read()
		if self.data.has_key(key):
			return True
		elif recurse and self.parent and self.parent.has_key(key):
			return True
		return False

	def _read(self):

		a = open(self.root,"r")
		lines = a.readlines()
		a.close()
		
		self.data = {}

		lpos = 0
		while lpos < len(lines):
			line = lines[lpos][:-1].lstrip()
			if line == "\n" or len(line) == 0 or line[0] == "#":
				lpos += 1
				continue
			equals = line.find('=')
			if equals == -1:
				print "ERROR no variable def"
				# TODO raise exception - no variable definition
				pass
			varname = line[0:equals]
			
			if line[equals:equals+2] != '="':
				# single line variable with no quotes
				self.data[varname] = self.expand_var(line[equals+1:])
				lpos += 1
				continue
			
			vardata = line[equals+2:]

			if self._valid_varname.match(varname) == None:
				# TODO raise exception - invalid variable name
				print "invalid var name"
				lpos += 1
				continue

			accum = ""
			while vardata.rstrip()[-1] != '"':
				# look at successive lines until trailing "'" is found:
				# trailing backslash support:
				if vardata[-1] == "\\":
					vardata = vardata[:-1]
				accum += vardata
				lpos += 1
				if lpos >= len(lines):
					# TODO: error, no end quote, got to end of file
					print "NO END QUOTE for",varname
					pass

				# for new vardata, remove trailing newline and any whitespace on the left, prepend a " "
				# this ensures that the 'foo bar oni' example above has one space between each word...

				vardata = " " + lines[lpos][:-1].lstrip()

				# keep looking...
			accum += vardata.rstrip()[:-1]

			self.data[varname] = self.expand_var(accum)
			lpos +=1
			continue

if __name__ == "__main__":
	z=ConfigFile("/usr/share/portage/config/make.globals")
	a=ConfigFile("/etc/make.conf", parent=z)
	for key in a.keys():
		print "%s: '%s'" % (key,a[key])
