#!/usr/bin/python
from __future__ import print_function

import re
import portage
import stat
import errno
from portage import os
from _emerge.actions import load_emerge_config
try:
	from subprocess import getstatusoutput as subprocess_getstatusoutput
except ImportError:
	from commands import getstatusoutput as subprocess_getstatusoutput

class PluginAdapter(object):

	def __init__(self,cfgroot):
		self.cfg_dir = os.path.join(cfgroot,"/etc/portage/extensions")

class PluginPhaseAdapter(PluginAdapter):

	def __init__(self, cfgroot, settings, trees, mtimedb):
		PluginAdapter.__init__(self, cfgroot)
		self.phase_dir = os.path.join(self.cfg_dir,"/phases/post")
		self.settings = settings
		self.trees = trees
		self.mtimedb = mtimedb

	def configure(self,a):
		a.settings = self.settings
		a.trees = self.trees
		a.mtimedb = self.mtimedb

class PluginHook(object):

	def __init__(self):
		pass

	def needsToRun(self):
		return True

	def run(self):
		print( "HI!")
		return True

import portage.util
from portage.util import shlex_split
from portage.output import colorize
from portage.output import blue, bold, colorize, create_color_func, darkgreen, red, yellow

class EtcConfigPlugin(PluginHook):

	def needsToRun(self):
		return True

	def run(self):
		config_protect = shlex_split(settings.get("CONFIG_PROTECT", ""))
		self.chk_updated_cfg_files(settings["EROOT"], config_protect)
	
	def chk_updated_cfg_files(self, eroot, config_protect):
		target_root = eroot
		result = list(portage.util.find_updated_config_files(target_root, config_protect))

		print("DEBUG: scanning /etc for config files....")

		for x in result:
			print("\n"+colorize("WARN", " * IMPORTANT:"), end=' ')
			if not x[1]: # it's a protected file
				print("config file '%s' needs updating." % x[0])
			else: # it's a protected dir
				print("%d config files in '%s' need updating." % (len(x[1]), x[0]))
	
		if result:
			print(" "+yellow("*")+" See the "+colorize("INFORM","CONFIGURATION FILES")\
					+ " section of the " + bold("emerge"))
			print(" "+yellow("*")+" man page to learn how to update config files.")

	def find_updated_config_files(target_root, config_protect):
		"""
		Return a tuple of configuration files that needs to be updated.
		The tuple contains lists organized like this:
		[ protected_dir, file_list ]
		If the protected config isn't a protected_dir but a procted_file, list is:
		[ protected_file, None ]
		If no configuration files needs to be updated, None is returned
		"""
	
		os = _os_merge
	
		if config_protect:
			# directories with some protect files in them
			for x in config_protect:
				files = []
	
				x = os.path.join(target_root, x.lstrip(os.path.sep))
				if not os.access(x, os.W_OK):
					continue
				try:
					mymode = os.lstat(x).st_mode
				except OSError:
					continue
	
				if stat.S_ISLNK(mymode):
					# We want to treat it like a directory if it
					# is a symlink to an existing directory.
					try:
						real_mode = os.stat(x).st_mode
						if stat.S_ISDIR(real_mode):
							mymode = real_mode
					except OSError:
						pass
	
				if stat.S_ISDIR(mymode):
					mycommand = \
						"find '%s' -name '.*' -type d -prune -o -name '._cfg????_*'" % x
				else:
					mycommand = "find '%s' -maxdepth 1 -name '._cfg????_%s'" % \
							os.path.split(x.rstrip(os.path.sep))
				mycommand += " ! -name '.*~' ! -iname '.*.bak' -print0"
				a = subprocess_getstatusoutput(mycommand)
	
				if a[0] == 0:
					files = a[1].split('\0')
					# split always produces an empty string as the last element
					if files and not files[-1]:
						del files[-1]
					if files:
						if stat.S_ISDIR(mymode):
							yield (x, files)
						else:
							yield (x, None)

class InfoPlugin(PluginHook):

	def needsToRun(self):
		return "noinfo" not in self.settings.features

	def run(self):
		infodirs = self.settings.get("INFOPATH","").split(":") + self.settings.get("INFODIR","").split(":")
		info_mtimes = self.mtimedb["info"]
		self.chk_updated_info_files(self.settings["ROOT"], infodirs, info_mtimes)

	def chk_updated_info_files(self, root, infodirs, prev_mtimes):
	
		if os.path.exists("/usr/bin/install-info"):
			out = portage.output.EOutput()
			regen_infodirs=[]
			for z in infodirs:
				if z=='':
					continue
				inforoot=os.path.normpath(root+z)
				if os.path.isdir(inforoot) and \
					not [x for x in os.listdir(inforoot) \
					if x.startswith('.keepinfodir')]:
						infomtime = os.stat(inforoot)[stat.ST_MTIME]
						if inforoot not in prev_mtimes or \
							prev_mtimes[inforoot] != infomtime:
								regen_infodirs.append(inforoot)
	
			if not regen_infodirs:
				portage.writemsg_stdout("\n")
				out.einfo("GNU info directory index is up-to-date.")
			else:
				portage.writemsg_stdout("\n")
				out.einfo("Regenerating GNU info directory index...")
	
				dir_extensions = ("", ".gz", ".bz2")
				icount=0
				badcount=0
				errmsg = ""
				for inforoot in regen_infodirs:
					if inforoot=='':
						continue
	
					if not os.path.isdir(inforoot) or \
						not os.access(inforoot, os.W_OK):
						continue
	
					file_list = os.listdir(inforoot)
					file_list.sort()
					dir_file = os.path.join(inforoot, "dir")
					moved_old_dir = False
					processed_count = 0
					for x in file_list:
						if x.startswith(".") or os.path.isdir(os.path.join(inforoot, x)):
							continue
						if x.startswith("dir"):
							skip = False
							for ext in dir_extensions:
								if x == "dir" + ext or x == "dir" + ext + ".old":
									skip = True
									break
							if skip:
								continue
						if processed_count == 0:
							for ext in dir_extensions:
								try:
									os.rename(dir_file + ext, dir_file + ext + ".old")
									moved_old_dir = True
								except EnvironmentError as e:
									if e.errno != errno.ENOENT:
										raise
									del e
						processed_count += 1
						myso=subprocess_getstatusoutput("LANG=C LANGUAGE=C /usr/bin/install-info --dir-file="+inforoot+"/dir "+inforoot+"/"+x)[1]
						existsstr="already exists, for file `"
						if myso!="":
							if re.search(existsstr,myso):
								# Already exists... Don't increment the count for this.
								pass
							elif myso[:44]=="install-info: warning: no info dir entry in ":
								# This info file doesn't contain a DIR-header: install-info produces this
								# (harmless) warning (the --quiet switch doesn't seem to work).
								# Don't increment the count for this.
								pass
							else:
								badcount=badcount+1
								errmsg += myso + "\n"
						icount=icount+1
	
					if moved_old_dir and not os.path.exists(dir_file):
						# We didn't generate a new dir file, so put the old file
						# back where it was originally found.
						for ext in dir_extensions:
							try:
								os.rename(dir_file + ext + ".old", dir_file + ext)
							except EnvironmentError as e:
								if e.errno != errno.ENOENT:
									raise
								del e
	
					# Clean dir.old cruft so that they don't prevent
					# unmerge of otherwise empty directories.
					for ext in dir_extensions:
						try:
							os.unlink(dir_file + ext + ".old")
						except EnvironmentError as e:
							if e.errno != errno.ENOENT:
								raise
							del e
	
					#update mtime so we can potentially avoid regenerating.
					prev_mtimes[inforoot] = os.stat(inforoot)[stat.ST_MTIME]
	
				if badcount:
					out.eerror("Processed %d info files; %d errors." % \
						(icount, badcount))
					writemsg_level(errmsg, level=logging.ERROR, noiselevel=-1)
				else:
					if icount > 0:
						out.einfo("Processed %d info files." % (icount,))

if __name__ == "__main__":
	settings, trees, mtimedb = load_emerge_config()
	x=PluginPhaseAdapter("/", settings, trees, mtimedb)
	a=InfoPlugin()
	b=EtcConfigPlugin()
	x.configure(a)
	x.configure(b)
	print(a.needsToRun())
	print(a.run())
	print(b.needsToRun())
	print(b.run())
