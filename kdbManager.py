# KDB GUI-manager
# Version 1.1
# by Juce.

import wx
import wx.lib.colourselect as csel
import string
import sys, os

VERSION, DATE = "1.1.0", "04/2005"

class RGBAColor:
	def __init__(self, color, alpha=-1):
		self.color = color
		self.alpha = alpha


"""
Utility method to construct wx.Color object 
from a RRGGBBAA string, as used in attrib.cfg files
"""
def MakeRGBAColor(str):
	r, g, b = int(str[0:2],16), int(str[2:4],16), int(str[4:6],16)
	try:
		a = int(str[6:8], 16)
		return RGBAColor(wx.Color(r,g,b), a)
	except:
		return RGBAColor(wx.Color(r,g,b), -1)


"""
Utility method for showing message box window
"""
def MessageBox(owner, title, text):
	dlg = wx.MessageDialog(owner, text, title, wx.OK | wx.ICON_INFORMATION)
	dlg.ShowModal()
	dlg.Destroy()

"""
A panel with colour select button, label, and edit control
"""
class KitColourSelect(wx.Panel):
	def __init__(self, parent, attribute, labelText, frame):
		wx.Panel.__init__(self, parent, -1)

		self.undef = wx.Color(0x99,0x99,0x99)
		self.att = attribute
		self.label = wx.StaticText(self, -1, labelText, size=(120, -1), style=wx.ALIGN_RIGHT)
		#font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		#self.label.SetFont(font)
		#self.label.SetSize(self.label.GetBestSize())

		self.cs = csel.ColourSelect(self, -1, "", self.undef, size=(40,-1))
		self.edit = wx.TextCtrl(self, -1, "undefined", style=wx.TE_PROCESS_ENTER, validator=MyValidator(), size=(60,-1))
		self.edit.SetMaxLength(8)
		self.button = wx.Button(self, -1, "undef", size=(60, -1)) 
		self.frame = frame

		csSizer = wx.BoxSizer(wx.HORIZONTAL)
		csSizer.Add(self.cs, 0, wx.EXPAND)
		csSizer.Add(self.edit, 0, wx.EXPAND)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
		sizer.Add(csSizer, 0, wx.EXPAND)
		sizer.Add(self.button, 0, wx.LEFT | wx.EXPAND, border=10)

		self.SetSizer(sizer)
		self.Layout()

		self.cs.Bind(csel.EVT_COLOURSELECT, self.OnSelectColour)
		self.edit.Bind(wx.EVT_TEXT_ENTER, self.OnEditColour)
		self.button.Bind(wx.EVT_BUTTON, self.OnUndef)


	def SetColour(self, color):
		self.cs.SetColour(color)
		self.edit.SetValue("%02X%02X%02X" % (color.Red(), color.Green(), color.Blue()))
		# update the kit panel
		try:
			self.frame.kitPanel.kit.attributes[self.att] = self.edit.GetValue()
			self.frame.kitPanel.Refresh()
		except AttributeError:
			pass
		except KeyError:
			pass

	def SetRGBAColour(self, rgba):
		color = rgba.color
		self.cs.SetColour(color)
		if rgba.alpha == -1:
			self.edit.SetValue("%02X%02X%02X" % (color.Red(), color.Green(), color.Blue()))
		else:
			self.edit.SetValue("%02X%02X%02X%02X" % (color.Red(), color.Green(), color.Blue(), rgba.alpha))
		# update the kit panel
		try:
			self.frame.kitPanel.kit.attributes[self.att] = self.edit.GetValue()
			self.frame.kitPanel.Refresh()
		except AttributeError:
			pass
		except KeyError:
			pass


	def ClearColour(self):
		self.cs.SetColour(self.undef)
		self.edit.SetValue("undefined")
		# update the kit panel
		try:
			del self.frame.kitPanel.kit.attributes[self.att]
			self.frame.kitPanel.Refresh()
		except AttributeError:
			pass
		except KeyError:
			pass


	"""
	Sets attribute to newly selected color
	"""
	def OnSelectColour(self, event):
		self.SetColour(event.GetValue())

		# add to modified list
		self.frame.addKitToModified()


	"""
	Verifies manually edited color and sets attribute
	"""
	def OnEditColour(self, event):
		text = self.edit.GetValue()
		# add padding zeroes, if needed
		if len(text) < 6:
			text = "%s%s" % ('0'*(6-len(text)), text)

		# attempt to set the color
		color = self.undef
		try:
			color = MakeRGBAColor(text)
			self.SetRGBAColour(color)
		except:
			self.ClearColour()

		# add to modified list
		self.frame.addKitToModified()


	"""
	Removes color definition from attributes
	"""
	def OnUndef(self, event):
		self.ClearColour()

		# add to modified list
		self.frame.addKitToModified()


class MyValidator(wx.PyValidator):
	def __init__(self):
		wx.PyValidator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return MyValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()

		for x in val:
			if x not in string.hexdigits:
				return False

		return True

	def OnChar(self, event):
		key = event.KeyCode()

		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return

		if chr(key) in string.hexdigits:
			event.Skip()
			return

		if not wx.Validator_IsSilent():
			wx.Bell()

		# Returning without calling even.Skip eats the event before it
		# gets to the text control
		return

"""
A drop-down list with label
"""
class MyList(wx.Panel):
	def __init__(self, parent, attribute, labelText, items, frame):
		wx.Panel.__init__(self, parent, -1)
		self.frame = frame
		self.att = attribute
		self.label = wx.StaticText(self, -1, labelText, size=(120,-1), style=wx.ALIGN_RIGHT)
		#font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		#self.label.SetFont(font)
		#self.label.SetSize(self.label.GetBestSize())

		self.choice = wx.Choice(self, -1, choices=[str(i) for i in items], size=(100,-1))
		self.choice.SetSelection(0)
		self.button = wx.Button(self, -1, "undef", size=(60,1))

		self.sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
		self.sizer.Add(self.choice, 0, wx.EXPAND)
		self.sizer.Add(self.button, 0, wx.LEFT | wx.EXPAND, border=10)

		# by default the kit panel is not refreshed on selection change
		self.refreshOnChange = False

		# bind events
		self.choice.Bind(wx.EVT_CHOICE, self.OnSelect)
		self.button.Bind(wx.EVT_BUTTON, self.OnUndef)

		self.SetSizer(self.sizer)
		self.Layout()


	def SetStringSelection(self, str):
		self.choice.SetStringSelection(str)
		self.frame.kitPanel.kit.attributes[self.att] = str
		if self.refreshOnChange:
			self.frame.kitPanel.Refresh()


	def SetUndef(self):
		self.choice.SetSelection(0)
		try:
			del self.frame.kitPanel.kit.attributes[self.att] 
		except AttributeError:
			pass
		except KeyError:
			pass
		if self.refreshOnChange:
			self.frame.kitPanel.Refresh()


	def OnSelect(self, event):
		selection = event.GetString()
		index = self.choice.GetSelection()
		if index == 0:
			# first item should always be "undefined"
			self.SetUndef()
		else:
			self.SetStringSelection(selection)

		# add kit to modified set
		self.frame.addKitToModified()


	def OnUndef(self, event):
		self.SetUndef()

		# add kit to modified set
		self.frame.addKitToModified()



"""
A panel with kit texture
"""
class KitPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, size=(512, 256))
		self.kit = None

		# bind events
		self.Bind(wx.EVT_PAINT, self.OnPaint)

	def OnPaint(self, event):
		dc = wx.PaintDC(self)

		# draw kit
		bmp = None	
		if self.kit == None:
			bmp = wx.Bitmap("default.png")
			dc.DrawBitmap(bmp, 0, 0, True)
			return event.Skip()
		else:
			bmp = wx.Bitmap(self.kit.filename)
			dc.DrawBitmap(bmp, 0, 0, True)

		# draw some overlay items
		nameText, numberText = "ABC", "9"
		if self.kit.isKeeper:
			numberText = "1"

		# shirt name
		try:
			colorName = MakeRGBAColor(self.kit.attributes["shirt.name"])
			if colorName.alpha != 0:
				dc.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD, False))
				dc.SetTextForeground(colorName.color)
				try:
					if self.kit.attributes["name.shape"] == "curved":
						dc.DrawRotatedText(nameText[0], 238, 15, 7)
						dc.DrawText(nameText[1], 253, 15)
						dc.DrawRotatedText(nameText[2], 268, 15, -7)
					else:
						dc.DrawText(nameText, 238, 15)
				except KeyError:
					dc.DrawText(nameText, 238, 15)
		except KeyError:
			pass

		# shirt number
		try:
			colorNumber = MakeRGBAColor(self.kit.attributes["shirt.number"])
			if colorNumber.alpha != 0:
				dc.SetFont(wx.Font(42, wx.SWISS, wx.NORMAL, wx.BOLD, False))
				dc.SetTextForeground(colorNumber.color)
				dc.DrawText(numberText, 244, 46)
		except KeyError:
			pass

		# shirt front number (for national teams)
		if self.kit.teamId < 64:
			try:
				colorNumber = MakeRGBAColor(self.kit.attributes["shirt.number"])
				if colorNumber.alpha != 0:
					dc.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
					dc.SetTextForeground(colorNumber.color)
					dc.DrawText(numberText, 109, 66)
			except KeyError:
				pass

		# shorts number(s)
		try:
			colorShorts = MakeRGBAColor(self.kit.attributes["shorts.number"])
			if colorShorts.alpha != 0:
				dc.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
				dc.SetTextForeground(colorShorts.color)
				try:
					shortsNumPos = self.kit.attributes["shorts.number.location"];
					if shortsNumPos == "off":
						positions = []
					elif shortsNumPos == "right":
						positions = [(40,205)]
					elif shortsNumPos == "both":
						positions = [(40,205), (120,205)]
					else:
						positions = [(120,205)]
				except KeyError:
					positions = [(120,205)]
				for pos in positions:
					dc.DrawText(numberText, pos[0], pos[1])
		except KeyError:
			pass


class Kit:
	def __init__(self, filename):
		# create a kit with undefined attributes 
		self.filename = filename
		self.attributes = dict()
		self.isKeeper = False # flag to indicate a GK kit
		self.attribRead = False # flag to indicate that attributes were already read


class KdbTree(wx.TreeCtrl):
	def __init__(self, parent, style, frame, kdbPath=""):
		wx.TreeCtrl.__init__(self, parent, -1, style=style)
		self.kdbPath = kdbPath
		self.frame = frame

		self.root = self.AddRoot("uni")
		self.SetPyData(self.root, None)

		# bind events
		self.Bind(wx.EVT_TREE_KEY_DOWN, self.OnKeyDown)
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)


	"""
	Shows a warning window, with a choice of saving changes,
	discarding them, or cancelling the operation.
	"""
	def cancelledOnSaveChanges(self):
		if len(self.frame.modified) > 0:
			# figure out what to do with changes: Save or Discard
			dlg = wx.MessageDialog(self, """You haven't saved your changes.
Do you want to save them?""",
					"Save or Discard changes",
					wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
			retValue = dlg.ShowModal()
			dlg.Destroy()

			if retValue == wx.ID_YES:
				# save the changes first
				self.frame.saveChanges(False)
				pass
			elif retValue == wx.ID_CANCEL:
				# cancel the operation
				return True

		self.frame.modified.clear()
		self.frame.SetStatusText("Modified kits: 0")
		return False

	
	def OnRefresh(self, event):
		if self.cancelledOnSaveChanges():
			return

		self.updateTree()
		self.frame.modified.clear()
		self.frame.SetStatusText("Modified kits: 0");
		self.frame.selectKit(None)
		print "KDB-tree updated."


	def OnKeyDown(self, event):
		key = event.GetKeyCode()
		item = self.GetSelection()
		if key == wx.WXK_RETURN:
			if self.IsExpanded(item):
				self.Collapse(item)
			else:
				self.Expand(item)


	def OnSelChanged(self, event):
		try:
			item = event.GetItem()
			#print "OnSelChanged: %s" % self.GetItemText(item)
			kit = self.GetPyData(item)
			self.frame.selectKit(kit)

		except wx._core.PyAssertionError:
			pass


	def updateTree(self):
		self.CollapseAndReset(self.root)

		kdbPath = self.kdbPath

		isz = (16,16)
		il = wx.ImageList(isz[0], isz[1])
		fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
		fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
		fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

		self.SetImageList(il)
		self.il = il

		self.SetItemImage(self.root, fldridx, wx.TreeItemIcon_Normal)
		self.SetItemImage(self.root, fldropenidx, wx.TreeItemIcon_Expanded)

		# Populate the tree control with content from KDB.
		# The idea here is to only add those files/folders to the tree, which
		# actually are recognized and processed by KitServer, and leave everything
		# else out of the tree control. (One exception to this rule is: attrib.cfg
		# file in each team folder. KitServer does process it, but we are not gonna
		# show that file in the tree.)

		try:
			# read team names from external text file
			teamNames = dict()
			try:
				f = open("teams.txt")
				for line in f:
					(num, name) = line.split(" ", 1)
					teamNames[num] = name.strip()
				f.close()
			except IOError:
				# file either not there, or some other error.
				# Not much we can do. Ignore.
				pass

			# remember team names for later usage
			self.frame.teamNames = teamNames

			all = os.listdir(kdbPath + "/uni")
			dirs = [item for item in all if os.path.isdir(kdbPath + "/uni/" + item)]

			# filter out extra dirs and only show ones that matter
			teamDirs = list()
			for dir in dirs:
				try:
					num = int(dir)
					if num >= 0 and num <= 204:
						teamDirs.append(dir)
				except:
					# ignore non-numbered folders
					pass

			# sort alphabetically
			teamDirs.sort()

			# add team dirs
			for team in teamDirs:
				child = self.AppendItem(self.root, "%s" % self.frame.GetTeamText(team))
				self.SetPyData(child, None)
				self.SetItemImage(child, fldridx, wx.TreeItemIcon_Normal)
				self.SetItemImage(child, fldropenidx, wx.TreeItemIcon_Expanded)

				defaultKits = ("texga.bmp", "texgb.bmp", "texpa.bmp", "texpb.bmp")
				extraDirs = ("gx", "px")

				all = os.listdir(kdbPath + "/uni/" + team)
				dirs = [item for item in all if os.path.isdir("%s/uni/%s/%s" % (kdbPath, team, item))]
				files = [item for item in all if item not in dirs]

				# dirs with extra kits
				for dir in dirs:
					if dir in extraDirs:
						item = self.AppendItem(child, dir)
						self.SetPyData(item, None)
						self.SetItemImage(item, fldridx, wx.TreeItemIcon_Normal)
						self.SetItemImage(item, fldropenidx, wx.TreeItemIcon_Expanded)

						all = os.listdir(kdbPath + "/uni/" + team + "/" + dir)
						extras = [extra for extra in all if not os.path.isdir("%s/uni/%s/%s/%s" %
							(kdbPath, team, dir, extra))]

						for kitfile in extras:
							if os.path.splitext(kitfile)[1].lower() == ".bmp":
								eitem = self.AppendItem(item, kitfile)
								# make new Kit object
								kit = Kit("%s/uni/%s/%s/%s" % (kdbPath, team, dir, kitfile))
								kit.teamId = int(team)
								self.SetPyData(eitem, kit)
								self.SetItemImage(eitem, fileidx, wx.TreeItemIcon_Normal)
								self.SetItemImage(eitem, fileidx, wx.TreeItemIcon_Expanded)

				# default kits
				for file in files:
					if file in defaultKits:
						item = self.AppendItem(child, file)
						# make new Kit object
						kit = Kit("%s/uni/%s/%s" % (kdbPath, team, file))
						kit.teamId = int(team)
						self.SetPyData(item, kit)
						self.SetItemImage(item, fileidx, wx.TreeItemIcon_Normal)
						self.SetItemImage(item, fileidx, wx.TreeItemIcon_Expanded)

		except Exception, ex:
			dlg = wx.MessageDialog(self, """PROBLEM: KDB Manager is unable to read the
contents of your KDB. You selected: 

%s

Perhaps, you accidently selected a wrong folder. 
Please try choosing a different one.""" % self.kdbPath,
					"KDB Manager ERROR",
					wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()

			# trigger folder selection
			self.frame.OnSetFolder(None)

		# show the contents of KDB
		self.Expand(self.root)
		self.SetFocus()
		self.SelectItem(self.root)


class MyFrame(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, size=(800, 570))
		self.kdbPath = "C:\\"

		# create a dictionary to keep track of modified kits
		self.modified = {}

		# status bar
		self.CreateStatusBar()
		self.SetStatusText("Modified kits: 0")

		# Create widgets
		##################

		splitter = wx.SplitterWindow(self, -1, style=wx.SP_3D)

		# right parent panel
		p2 = wx.Panel(splitter, -1)

		# current kit panel
		self.kitPanel = KitPanel(p2)

		# colored panels
		self.nameCS = KitColourSelect(p2, "shirt.name", "Shirt name colour:", self)
		self.numberCS = KitColourSelect(p2, "shirt.number", "Shirt number colour:", self)
		self.shortsCS = KitColourSelect(p2, "shorts.number", "Shorts number colour:", self)

		# collar choice
		self.collar = MyList(p2, "collar", "Collar:", ["undefined", "yes", "no"], self)

		# model choice
		modellist = ["undefined"]
		for id in range(59):
			modellist.append(id)
		self.model = MyList(p2, "model", "3D-model ID:", modellist, self)

		# cuff choice
		self.cuff = MyList(p2, "cuff", "Cuffs:", ["undefined", "yes", "no"], self)

		# number-type choice
		self.numberType = MyList(p2, "number.type", "Number type:", ["undefined",0,1,2,3], self)

		# name-type choice
		self.nameType = MyList(p2, "name.type", "Name type:", ["undefined",0,1], self)

		# name-type choice
		self.nameShape = MyList(p2, "name.shape", "Name shape:", ["undefined", "straight", "curved"], self)
		self.nameShape.refreshOnChange = True

		# shorts-num-location choice
		self.shortsNumLocation = MyList(p2, "shorts.number.location", "Shorts number location:", ["undefined", "off", "left", "right", "both"], self)
		self.shortsNumLocation.refreshOnChange = True

		# Kit database folder
		try:
			cfg = open("kdbm.cfg", "rt")
			self.kdbPath = cfg.read().strip()
			cfg.close()
		except IOError:
			self.OnSetFolder(None)

		# tree control
		self.tree = KdbTree(splitter, wx.TR_HAS_BUTTONS, self, self.kdbPath)
		self.tree.updateTree()

		# menu
		menubar = wx.MenuBar()

		menu1 = wx.Menu()
		menu1.Append(101, "&KDB folder", 
			"Set/change the location of KDB folder. Your current is: %s" % self.kdbPath)
		menu1.Append(102, "&Save changes", "Save the changes to attrib.cfg files")
		menu1.AppendSeparator()
		menu1.Append(103, "E&xit", "Exit the program")
		menubar.Append(menu1, "&File")

		menu2 = wx.Menu()
		menu2.Append(202, "&Restore this kit", "Undo changes for this kit")
		menu2.Append(201, "&Refresh KDB", "Reload the KDB from disk")
		menubar.Append(menu2, "&Edit")

		menu3 = wx.Menu()
		menu3.Append(301, "&About", "Author and version information")
		menubar.Append(menu3, "&Help")

		self.SetMenuBar(menubar)

		# Create sizers
		#################

		self.rightSizer = wx.BoxSizer(wx.VERTICAL)
		p2.SetSizer(self.rightSizer)

		# Build interface by adding widgets to sizers
		################################################

		self.rightSizer.Add(self.kitPanel, 0, wx.BOTTOM | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.nameCS, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.numberCS, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.shortsCS, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.collar, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.model, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.cuff, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.numberType, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.nameType, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.nameShape, 0, wx.LEFT | wx.ALIGN_CENTER, border=10)
		self.rightSizer.Add(self.shortsNumLocation, 0, wx.LEFT | wx.BOTTOM | wx.ALIGN_CENTER, border=10)

		splitter.SetMinimumPaneSize(80)
		splitter.SplitVertically(self.tree, p2, -520)

		#self.Layout()

		# Bind events
		self.Bind(wx.EVT_CLOSE, self.OnExit)

		self.Bind(wx.EVT_MENU, self.OnSetFolder, id=101)
		self.Bind(wx.EVT_MENU, self.OnMenuSave, id=102)
		self.Bind(wx.EVT_MENU, self.OnExit, id=103)
		self.Bind(wx.EVT_MENU, self.OnRestore, id=202)
		self.Bind(wx.EVT_MENU, self.tree.OnRefresh, id=201)
		self.Bind(wx.EVT_MENU, self.OnAbout, id=301)


	"""
	Shows dialog window to select the KDB folder.
	"""
	def OnSetFolder(self, event):
		try:
			if self.tree.cancelledOnSaveChanges():
				return
		except AttributeError:
			# no tree yet. ignore then
			pass

		print "Set/change KDB folder location"
		dlg = wx.DirDialog(self, """Select your KDB folder:
(Folder named "KDB", which is typically located
inside your kitserver folder)""",
				style=wx.DD_DEFAULT_STYLE)

		if dlg.ShowModal() == wx.ID_OK:
			self.kdbPath = dlg.GetPath()
			print "You selected %s" % self.kdbPath

			# clear out kit panel, and disable controls
			self.enableControls(None)
			self.kitPanel.kit = None
			self.kitPanel.Refresh()

			# try to update the tree
			try:
				self.tree.kdbPath = self.kdbPath
				self.tree.updateTree()
			except AttributeError:
				# looks like we don't have a tree yet. 
				# so just rememeber this value for now.
				pass

			# save the value in configuration file
			try:
				cfg = open("kdbm.cfg", "wt")
				print >>cfg, self.kdbPath
				cfg.close()
			except IOError:
				# unable to save configuration file
				pass

		else:
			print "Selection cancelled."

		# destroy the dialog after we're done
		dlg.Destroy()


	def selectKit(self, kit):
		self.enableControls(kit)

		if kit != None and not kit.attribRead:
			#print "Showing %s" % kit.filename
			# read kit attributes from attrib.cfg
			self.readAttributes(kit)
			kit.attribRead = True

		# assign this kit to kitPanel
		self.kitPanel.kit = kit
		self.kitPanel.Refresh()

		# update colour selects
		undef = wx.Color(0x99,0x99,0x99)
		try:
			self.nameCS.SetRGBAColour(MakeRGBAColor(kit.attributes["shirt.name"]))
		except:
			self.nameCS.ClearColour()
		self.nameCS.Refresh()

		try:
			self.numberCS.SetRGBAColour(MakeRGBAColor(kit.attributes["shirt.number"]))
		except:
			self.numberCS.ClearColour()
		self.numberCS.Refresh()

		try:
			self.shortsCS.SetRGBAColour(MakeRGBAColor(kit.attributes["shorts.number"]))
		except:
			self.shortsCS.ClearColour()
		self.shortsCS.Refresh()

		# update collar
		try:
			self.collar.SetStringSelection(kit.attributes["collar"])
		except:
			self.collar.SetUndef()

		# update model
		try:
			self.model.SetStringSelection(kit.attributes["model"])
		except:
			self.model.SetUndef()

		# update cuff
		try:
			self.cuff.SetStringSelection(kit.attributes["cuff"])
		except:
			self.cuff.SetUndef()

		# update numberType
		try:
			self.numberType.SetStringSelection(kit.attributes["number.type"])
		except:
			self.numberType.SetUndef()

		# update nameType
		try:
			self.nameType.SetStringSelection(kit.attributes["name.type"])
		except:
			self.nameType.SetUndef()

		# update nameShape
		try:
			self.nameShape.SetStringSelection(kit.attributes["name.shape"])
		except:
			self.nameShape.SetUndef()

		# update shortsNumLocation
		try:
			self.shortsNumLocation.SetStringSelection(kit.attributes["shorts.number.location"])
		except:
			self.shortsNumLocation.SetUndef()


	def enableControls(self, kit):
		if kit == None:
			self.nameCS.Enable(False)
			self.numberCS.Enable(False)
			self.shortsCS.Enable(False)
			self.collar.Enable(False)
			self.model.Enable(False)
			self.cuff.Enable(False)
			self.numberType.Enable(False)
			self.nameType.Enable(False)
			self.nameShape.Enable(False)
			self.shortsNumLocation.Enable(False)
		else:
			self.nameCS.Enable(True)
			self.numberCS.Enable(True)
			self.shortsCS.Enable(True)
			self.collar.Enable(True)
			self.model.Enable(True)
			self.cuff.Enable(True)
			self.numberType.Enable(True)
			self.nameType.Enable(True)
			self.nameShape.Enable(True)
			self.shortsNumLocation.Enable(True)


	def OnRestore(self, event):
		if self.kitPanel.kit == None:
			return

		self.kitPanel.kit.attribRead = False
		self.selectKit(self.kitPanel.kit)

		# remove kit from list of modified kits
		self.removeKitFromModified()


	"""
	Read kit attributes from attrib.cfg file
	"""
	def readAttributes(self, kit):
		# clear out the attributes dictionary
		kit.attributes.clear()

		print "Reading attributes for %s" % kit.filename
		dir, file = os.path.split(kit.filename)
		# check if this is an "extra" kit. If so
		# adjust the dir and file
		if dir[-2:]=="gx" or dir[-2:]=="px":
			file = "%s/%s" % (dir[-2:], file)
			dir = dir[:-2]

		# set goalkeeper flag
		if file[0:3]=="gx/" or file[0:4]=="texg":
			kit.isKeeper = True

		att, section = None, ""
		try:
			att = open("%s/%s" % (dir, "attrib.cfg"))
			found = False
			for line in att:
				line = line.strip()
				print "line: {%s}" % line

				# strip out the comment
				commentStarts = line.find("#")
				if commentStarts != -1:
					line = line[:commentStarts]

				if len(line)==0:
					continue

				if line[0]=='[' and line[-1]==']':
					# new section. If we have already
					# saw our section, this means the end
					# of it, and we're done.
					if found:
						break;
					section = line[1:-1].replace("\\","/")
					#print "section: {%s}" % section
					continue

				# check if this is a section that we're looking for
				if section == file:
					found = True
					tok = line.split()
					if len(tok)==3:
						kit.attributes[tok[0].strip()] = tok[2].strip()

			att.close()

		except IOError:
			# unable to read attributes. Ignore.
			if att != None:
				att.close()


	def addKitToModified(self):
		self.modified[self.kitPanel.kit] = True
		# update status bar text
		self.SetStatusText("Modified kits: %d" % len(self.modified.keys()))


	def removeKitFromModified(self):
		try:
			del self.modified[self.kitPanel.kit]
			# update status bar text
			self.SetStatusText("Modified kits: %d" % len(self.modified.keys()))
		except KeyError:
			pass
			

	def OnMenuSave(self, event):
		self.saveChanges()
		self.modified.clear()
		self.SetStatusText("Modified kits: 0");
		print "Changes saved."


	def OnAbout(self, event):
		dlg = wx.MessageDialog(self, """KDB Manager by Juce.
Version %s from %s

This is a helper program for working with KDB (Kit Database)
for KitServer 4. Provides simple visual interface to
define different attributes for kits: colors for name and
numbers, 3D-model, collar, and some others.""" % (VERSION, DATE),
			"About KDB Manager", wx.OK | wx.ICON_INFORMATION)

		dlg.ShowModal()
		dlg.Destroy()


	def OnExit(self, evt):
		print "MyFrame.OnExit"

		# do necessary clean-up and saves
		if self.tree.cancelledOnSaveChanges():
			return

		# Exit the program
		self.Destroy()
		sys.exit(0)


	"""
	Saves the changes for altered kits to corresponding attrib.cfg files
	"""
	def saveChanges(self, showConfirmation=True):
		print "Saving changes..."

		# TEMP:test
		print "Modified kits [%d]:" % len(self.modified.keys())
		for kit in self.modified.keys():
			# for now: just print out the kit filename
			print kit.filename

		# group kits by their containing folders, so that we
		# can easily write one attrib.cfg file for all kits in the same dir
		kits = dict()
		for kit in self.modified.keys():
			# determine containing dir and kit id
			dir, file = os.path.split(kit.filename.replace("\\", "/"))
			if dir[-3:]=="/gx" or dir[-3:]=="/px":
				dir, file = dir[:-3], "%s/%s" % (dir[-2:], file)

			# find the dictionary for corresponding dir
			dirDict = None
			try:
				dirDict = kits[dir] # dictionary already exists
			except KeyError:
				dirDict = {} # create new dictionary
				kits[dir] = dirDict

			# add file to the dictionary
			kit.id = file
			dirDict[kit.id] = kit

		# TEMP:test
		for key in kits.keys():
			print "Kit group: %s" % key
			for kit in kits[key].values():
				print "File: %s" % kit.id

		# write attrib.cfg for each group
		for dir in kits.keys():
			att = None

			# read current attrib.cfg, if one exists
			cfg = list()
			try:
				att = open("%s/%s" % (dir, "attrib.cfg"), "rt")
				for line in att:
					cfg.append(line.strip())
			except IOError:
				pass # no attrib.cfg. That's fine. We'll make a new one

			# write attrib.cfg, preserving the unmodified content
			try:
				att = open("%s/%s" % (dir, "attrib.cfg"), "wt")
			except IOError:
				MessageBox(self, "Unable to save changes", "ERROR: cannot open file %s for writing." % att)
				return

			try:
				teamId = os.path.split(dir)[1]

				# write a comment line, if not already there
				cmt = "# Kit attributes for team %s" % self.GetTeamText(teamId)
				if len(cfg)==0 or cfg[0] != cmt:
					print >>att, cmt
					print >>att

				section, skip = "", False

				# go through old content line by line
				for line in cfg:
					if len(line)==0 or line[0] == "#": # empty line or comment.
						print >>att, line
						continue

					# strip off comment at the end of line
					comm = line.find("#")
					if comm > -1:
						line = line[:comm]

					# strip off any remaining white space
					line = line.strip()

					# check if this is a new section
					if line[0]=="[" and line[-1]=="]":
						section = line[1:-1].replace("\\", "/")
						print >>att, "[%s]" % section
						skip = False

						# If we have a modified kit for this section, then
						# write attributes and skip to next section
						try:
							group = kits[dir]
							kit = group[section]
							self.writeSortedAttributes(att, kit)
							# remove this kit from the group, so 
							# that we don't write it twice
							del group[section]
							skip = True
						except KeyError:
							pass

						continue

					if not skip:
						print >>att, line

				# now, write the remaning kits in this group:
				# only ones not referenced in old config file 
				# should be left
				for kit in kits[dir].values():
					print >>att
					print >>att, "[%s]" % kit.id
					self.writeSortedAttributes(att, kit)

			except Exception, e:
				MessageBox(self, "Unable to save changes", "ERROR during save: %s" % str(e))

			att.close()

			# show save confirmation message, if asked so.
			if showConfirmation:
				MessageBox(self, "Changes saved", "Your changes were successfully saved.")


	def writeSortedAttributes(self, file, kit):
		keys = kit.attributes.keys()
		keys.sort()
		for name in keys:
			print >>file, "%s = %s" % (name, kit.attributes[name])


	""" 
	Returns team name: an ID with helper text, if available.
	"""
	def GetTeamText(self, id):
		try:
			return "%s (%s)" % (id, self.teamNames[id])
		except KeyError:
			return "%s" % id


class MyApp(wx.App):
	def OnInit(self):
		frame = MyFrame(None, -1, "KDB Manager")
		frame.Show(1)
		self.SetTopWindow(frame)
		return True


if __name__ == "__main__":
	#app = MyApp(redirect=True, filename="output.log")
	#app = MyApp(redirect=True)
	app = MyApp(0)
	app.MainLoop()

