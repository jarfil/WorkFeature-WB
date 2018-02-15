# -*- coding: utf-8 -*-
"""
***************************************************************************
*   FreeCAD Work Feature workbench                                        *
*                                                                         *
*   Copyright (c) 2017 <rentlau_64>                                       *
*   Code rewrite by <rentlau_64> from Work Features macro:                *
*   https://github.com/Rentlau/WorkFeature                                *
*                                                                         *
*   This file is a supplement to the FreeCAD CAx development system.      *  
*   http://www.freecadweb.org                                             *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU Lesser General Public License (LGPL)    *
*   as published by the Free Software Foundation; either version 2 of     *
*   the License, or (at your option) any later version.                   *
*   for detail see the COPYING and COPYING.LESSER text files.             *
*   http://en.wikipedia.org/wiki/LGPL                                     *
*                                                                         *
*   This software is distributed in the hope that it will be useful,      *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU Library General Public License for more details.                  *
*                                                                         *
*   You should have received a copy of the GNU Library General Public     *
*   License along with this macro; if not, write to the Free Software     *
*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
*   USA or see <http://www.gnu.org/licenses/>                             *
***************************************************************************
"""
__title__="Macro CenterLinePoint"
__author__ = "Rentlau_64"
__brief__ = '''
Macro CenterLinePoint.
Creates a parametric CenterLinePoint from an Edge
'''
###############
m_debug = False
###############
import sys
import os.path
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part
from PySide import QtGui,QtCore
import WF
from WF_Objects_base import WF_Point
# from Utils.WF_selection import Selection
# from Utils.WF_geometry import *

# get the path of the current python script 
path_WF = os.path.dirname(__file__)
 
path_WF_icons     = os.path.join(path_WF, 'Resources', 'Icons')
path_WF_utils     = os.path.join(path_WF, 'Utils')
path_WF_resources = os.path.join(path_WF, 'Resources')
path_WF_ui        = os.path.join(path_WF, 'Resources', 'Ui')
 
if not sys.path.__contains__(str(path_WF_utils)):
    sys.path.append(str(path_WF_utils))
    sys.path.append(str(path_WF_ui))
     
try:
    from WF_selection import Selection
    from WF_print import printError_msg, print_msg
    from WF_directory import createFolders, addObjectToGrp
    from WF_geometry import *
    #from WF_utils import *
except:
    print "ERROR: cannot load WF modules !!"
    sys.exit(1)

###############
m_icon          = "/WF_centerLinePoint.svg"
m_dialog        = "/WF_UI_centerLinePoint.ui"
m_dialog_title  = "Define number of parts and location(s)."
m_exception_msg = """Unable to create Center Line Point(s) :
    Select one or several Line/Edge(s) and/or
    Select one Plane/Face to process all (4) Edges and/or
    Select one Object to process all Edges at once !
   
Go to Parameter(s) Window in Task Panel!"""
m_result_msg    = " : Mid Line Point(s) created !"
m_menu_text     = "Center of Line(s)"
m_accel         = ""
m_tool_tip      = """<b>Create Point(s)</b> at Center location of each selected Line(s).<br>
...<br>
<i>Click in view window without selection will popup<br>
 - a Warning Window and<br> 
 - a Parameter(s) Window in Task Panel!</i>
"""
m_location       = "Single"
m_locations      = ["Single", "All"]
m_numberLinePart = 2
m_indexPart      = 1

def addObjectToGrp(obj,grp,info=0):
    m_obj = obj
    m_grp = grp
    m_grp.addObject(m_obj) # adds object to the group
    if info != 0:
        print_msg("Object " + str(m_obj) + " added to Group : " + str(m_grp))    

###############
class CenterLinePointPanel:  
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(path_WF_ui + m_dialog)
        self.form.setWindowTitle(m_dialog_title)
        
    def accept(self):
        global m_location
        global m_numberLinePart
        global m_indexPart
        
        m_select = self.form.UI_CenterLinePoint_checkBox.isChecked()
        if m_select:
            m_location = "All"
        else :
            m_location = "Single" 
        m_numberLinePart = self.form.UI_CenterLinePoint_spin_numberLinePart.value()
        m_indexPart      = self.form.UI_CenterLinePoint_spin_indexPart.value()
        Gui.Control.closeDialog()
        return True
    
    def reject(self):
        Gui.Control.closeDialog()
        return True
    
    def shouldShow(self):    
        return (len(Gui.Selection.getSelectionEx(App.activeDocument().Name)) == 0 )   



def makeCenterLinePointFeature(group):
    """ Makes a CenterLinePoint" parametric feature object. 
    into the given Group
    Returns the new object.
    """ 
    m_name = "CenterLinePoint_P"
    m_part = "Part::FeaturePython"     
    
    try:     
        m_obj = App.ActiveDocument.addObject(str(m_part),str(m_name))
        if group != None :
            addObjectToGrp(m_obj,group,info=1)
        CenterLinePoint(m_obj)
        ViewProviderCenterLinePoint(m_obj.ViewObject)
    except:
        printError_msg( "Not able to add an object to Model!")
        return None
    
    return m_obj


class CenterLinePoint(WF_Point):
    """ The CenterLinePoint feature object. """
    # this method is mandatory
    def __init__(self,selfobj):
        self.name = "CenterLinePoint"
        WF_Point.__init__(self, selfobj, self.name)
        """ Add some custom properties to our CenterLinePoint feature object. """
        selfobj.addProperty("App::PropertyLinkSub","Edge",self.name,
                            "Input edge")   
        selfobj.addProperty("App::PropertyInteger","NumberLinePart",self.name,
                            "The number of parts of parent segment !").NumberLinePart=2
        selfobj.addProperty("App::PropertyInteger","IndexPart",self.name,
                            "The location of the point : 1/2 means middle of the segment !").IndexPart=1        
        selfobj.setEditorMode("Edge", 1)
        selfobj.Proxy = self    
     
    # this method is mandatory   
    def execute(self,selfobj): 
        """ Print a short message when doing a recomputation. """
        if WF.verbose() != 0:
            App.Console.PrintMessage("Recompute Python CenterLinePoint feature\n")
        
        n = eval(selfobj.Edge[1][0].lstrip('Edge'))
#         if selfobj.NumberLinePart == 2:       
#             Vector_point = centerLinePoint(selfobj.Edge[0].Shape.Edges[n-1])
#         else:
        Vector_point = alongLinePoint(selfobj.Edge[0].Shape.Edges[n-1], selfobj.IndexPart , selfobj.NumberLinePart)
                             
        point = Part.Point( Vector_point )
        selfobj.Shape = point.toShape()
        propertiesPoint(selfobj.Label)
        selfobj.X = float(Vector_point.x)
        selfobj.Y = float(Vector_point.y)
        selfobj.Z = float(Vector_point.z)
                 

       
    def onChanged(self, selfobj, prop):
        """ Print the name of the property that has changed """
        # Debug mode
        if WF.verbose() != 0:
            App.Console.PrintMessage("Change property : " + str(prop) + "\n")
        
        if selfobj.parametric == 'No' :
            selfobj.setEditorMode("NumberLinePart", 1)
            selfobj.setEditorMode("IndexPart", 1) 
        else :
            selfobj.setEditorMode("NumberLinePart", 0)
            selfobj.setEditorMode("IndexPart", 0)
            
        if prop == "IndexPart":
            selfobj.Proxy.execute(selfobj)
        if prop == 'NumberLinePart':
            if  selfobj.NumberLinePart  <= 1 :
                selfobj.NumberLinePart = 2
            elif selfobj.NumberLinePart  > 100 :
                selfobj.NumberLinePart = 100
            selfobj.Proxy.execute(selfobj)

        WF_Point.onChanged(self, selfobj, prop)   
            
class ViewProviderCenterLinePoint:
    global path_WF_icons
    icon = '/WF_centerLinePoint.svg'  
    def __init__(self,vobj):
        """ Set this object to the proxy object of the actual view provider """
        vobj.Proxy = self
    
    # this method is mandatory    
    def attach(self, vobj): 
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
    
    # subelements is a tuple of strings
    def onDelete(self, feature, subelements): 
        return True
    
    # This method is optional and if not defined a default icon is shown.
    def getIcon(self):        
        """ Return the icon which will appear in the tree view. """
        return (path_WF_icons + ViewProviderCenterLinePoint.icon)
           
    def setIcon(self, icon = '/WF_centerLinePoint.svg'):
        ViewProviderCenterLinePoint.icon = icon
            
class CommandCenterLinePoint:
    """ Command to create CenterLinePoint feature object. """
    def GetResources(self):
        return {'Pixmap'  : path_WF_icons + m_icon,
                'MenuText': m_menu_text,
                'Accel'   : m_accel,
                'ToolTip' : m_tool_tip}

    def Activated(self):
        m_actDoc = App.activeDocument()
        if m_actDoc is not None:
            if len(Gui.Selection.getSelectionEx(m_actDoc.Name)) == 0:
                Gui.Control.showDialog(CenterLinePointPanel())
        run()
        
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

if App.GuiUp:
    Gui.addCommand("CenterLinePoint", CommandCenterLinePoint())


def run():
    m_actDoc = App.activeDocument()
    if m_actDoc == None:
        message = "No Active document selected !"
        return (None, message)
    if not m_actDoc.Name:
        message = "No Active document.name selected !"
        return (None, message) 
       
    m_selEx  = Gui.Selection.getSelectionEx(m_actDoc.Name)                    
    m_sel    = Selection(m_selEx)
 
    if m_sel == None :
        print_msg("Unable to create a Selection Object !") 
        return None
    
    #m_debug = WF.verbose()
    if WF.verbose() != 0:
        print_msg("m_actDoc      = " + str(m_actDoc))
        print_msg("m_actDoc.Name = " + str(m_actDoc.Name))
        print_msg("m_selEx       = " + str(m_selEx))         
        print_msg("m_sel         = " + str(m_sel))
      
    try:        
        Number_of_Edges, Edge_List = m_sel.get_segmentsNames(getfrom=["Segments","Curves","Planes","Objects"])
        if WF.verbose() != 0:        
            print_msg("Number_of_Edges = " + str(Number_of_Edges))
            
        if Number_of_Edges == 0:
            raise Exception(m_exception_msg)
        try:
            m_main_dir  = "WorkPoints_P"   
            m_group = createFolders(str(m_main_dir))
            if WF.verbose() != 0:
                print_msg("Group = " + str(m_group.Label))
            m_sub_dir  = "Set"
            
            # Create a sub group if needed
            if Number_of_Edges > 1:
                try:
                    m_ob = App.ActiveDocument.getObject(str(m_main_dir)).newObject("App::DocumentObjectGroup", str(m_sub_dir))
                    m_group = m_actDoc.getObject( str(m_ob.Label) )
                except:
                    printError_msg("Could not Create '"+ str(m_sub_dir) +"' Objects Group!")           
                             
            for i in range( Number_of_Edges ):
                edge = Edge_List[i]
                
                if WF.verbose() != 0:
                    print_msg("Location = " + str(m_location))
                
                if m_location == "Single" :                  
                    App.ActiveDocument.openTransaction("Macro CenterLinePoint")
                    selfobj = makeCenterLinePointFeature(m_group)    
                    selfobj.Edge = edge
                    selfobj.NumberLinePart = m_numberLinePart
                    selfobj.IndexPart      = m_indexPart 
                    selfobj.Proxy.execute(selfobj)
                else:
                    for m_iPart in range(m_numberLinePart+1):
                        App.ActiveDocument.openTransaction("Macro CenterLinePoint")
                        selfobj = makeCenterLinePointFeature(m_group)    
                        selfobj.Edge = edge
                        selfobj.NumberLinePart = m_numberLinePart
                        selfobj.IndexPart      = m_iPart 
                        selfobj.Proxy.execute(selfobj)
                        
#                if WF.verbose() != 0:    
#                    print_point(Vector_Line_Center,str(Center_User_Name) + result_msg + " at :")
        finally:
            App.ActiveDocument.commitTransaction()
            
    except Exception as err:
        printError_msg(err.message, title="Macro CenterLinePoint")

                           
if __name__ == '__main__':
    run()