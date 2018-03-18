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
    from WF_selection import Selection, getSel
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
m_menu_text     = "Point(s) = divide(Line)"
m_accel         = ""
m_tool_tip      = """<b>Create Point(s)</b> at Center location of each selected Line(s).<br>
Cut each selected Line(s) in 2 (n) parts and<br>
create a (n-1) Point(s) along selected edge(s) except at extrema.<br>
The number (n) indicates how many parts to consider.<br>
<br>
- Select one or several Line/Edge(s) and/or<br>
- Select one Plane/Face to process all (4) Edges and/or<br>
- Select one Object to process all Edges at once<br>
- Then Click on the button<br>
<br> 
<i>Click in view window without selection will popup<br>
 - a Warning Window and<br> 
 - a Parameter(s) Window in Task Panel!</i>
"""
m_location       = "Single"
m_locations      = ["Single", "All"]
m_numberLinePart = 2
m_indexPart      = 1
###############

class CenterLinePointPanel:  
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(path_WF_ui + m_dialog)
        self.form.setWindowTitle(m_dialog_title)
        self.form.UI_CenterLinePoint_spin_numberLinePart.setValue(m_numberLinePart)
        self.form.UI_CenterLinePoint_spin_indexPart.setValue(m_indexPart)
        self.form.UI_CenterLinePoint_checkBox.setCheckState(QtCore.Qt.Unchecked)
        if m_location == "All":
            self.form.UI_CenterLinePoint_checkBox.setCheckState(QtCore.Qt.Checked)
                        
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
          
        if WF.verbose() != 0:
            print_msg("m_numberLinePart = " + str(m_numberLinePart))
            print_msg("m_indexPart = " + str(m_indexPart))
            
        Gui.Control.closeDialog()
        m_actDoc = App.activeDocument()
        if m_actDoc is not None:
            if len(Gui.Selection.getSelectionEx(m_actDoc.Name)) != 0:
                run()
        return True
    
    def reject(self):
        Gui.Control.closeDialog()
        return False
    
    def shouldShow(self):    
        return (len(Gui.Selection.getSelectionEx(App.activeDocument().Name)) == 0 )   


def makeCenterLinePointFeature(group):
    """ Makes a CenterLinePoint parametric feature object. 
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
        m_tooltip = """The number indicates in how many Parts 
        each selected parent Lines(s) will be cut in (Max 100).
        """   
        selfobj.addProperty("App::PropertyInteger","NumberLinePart",self.name,
                            m_tooltip).NumberLinePart=2
        m_tooltip = """The location of the point : 1/2 means middle of the segment !
The number indicates at which part's end the point will be located.
- If the Number of parts is 2 and Point at part's end 1,
this means that the point will be located in the middle of the Line.
- If the Number of parts is 2 and Point at part's end 2, 
this means that the point will be located in the end of the Line.

Negative value are allowed
Limits : [-1000:1000]
        """ 
        selfobj.addProperty("App::PropertyInteger","IndexPart",self.name,
                            m_tooltip).IndexPart=1        
        
        selfobj.setEditorMode("Edge", 1)
        selfobj.Proxy = self    
     
    # this method is mandatory   
    def execute(self,selfobj): 
        """ Print a short message when doing a recomputation. """
#         if WF.verbose() != 0:
#             App.Console.PrintMessage("Recompute Python CenterLinePoint feature\n")
        
        if 'Edge' not in selfobj.PropertiesList:
            return
        if 'IndexPart' not in selfobj.PropertiesList:
            return
        if 'NumberLinePart' not in selfobj.PropertiesList:
            return
        
        n = eval(selfobj.Edge[1][0].lstrip('Edge'))
#         if WF.verbose() != 0:
#             print_msg("n = " + str(n))
        
        try:   
            Vector_point = alongLinePoint(selfobj.Edge[0].Shape.Edges[n-1], 
                                          selfobj.IndexPart , selfobj.NumberLinePart)
                                 
            point = Part.Point( Vector_point )
            selfobj.Shape = point.toShape()
            propertiesPoint(selfobj.Label)
            selfobj.X = float(Vector_point.x)
            selfobj.Y = float(Vector_point.y)
            selfobj.Z = float(Vector_point.z)
        except:
            pass
                
    def onChanged(self, selfobj, prop):
        """ Print the name of the property that has changed """
        # Debug mode
        if WF.verbose() != 0:
            App.Console.PrintMessage("Change property : " + str(prop) + "\n")
        
        if 'parametric' in selfobj.PropertiesList:
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
    m_sel, m_actDoc = getSel(WF.verbose())
      
    try:        
        Number_of_Edges, Edge_List = m_sel.get_segmentsNames(
            getfrom=["Segments","Curves","Planes","Objects"])
        if WF.verbose() != 0:        
            print_msg("Number_of_Edges = " + str(Number_of_Edges))
            print_msg("Edge_List = " + str(Edge_List))
            
        Number_of_Vertexes, Vertex_List = m_sel.get_pointsNames(
            getfrom=["Points","Curves","Objects"])
        if WF.verbose() != 0:        
            print_msg("Number_of_Vertexes = " + str(Number_of_Vertexes))
            print_msg("Vertex_List = " + str(Vertex_List))
            
        if Number_of_Edges == 0 :
            #if Number_of_Vertexes < 2 :
            raise Exception(m_exception_msg)
        try:
            m_main_dir = "WorkPoints_P"   
            m_sub_dir  = "Set"
            m_group = createFolders(str(m_main_dir))
            
            #### From Edges
            # Create a sub group if needed
            if Number_of_Edges > 1 or m_location != "Single":
                try:
                    m_ob = App.ActiveDocument.getObject(str(m_main_dir)).newObject("App::DocumentObjectGroup", str(m_sub_dir))
                    m_group = m_actDoc.getObject( str(m_ob.Label) )
                except:
                    printError_msg("Could not Create '"+ str(m_sub_dir) +"' Objects Group!")           
            
            if WF.verbose() != 0:
                print_msg("Group = " + str(m_group.Label))                 
            
            for i in range( Number_of_Edges ):
                edge = Edge_List[i]
                
                if WF.verbose() != 0:
                    print_msg("Location = " + str(m_location))
                
                if m_location == "Single" :                  
                    App.ActiveDocument.openTransaction("Macro CenterLinePoint")
                    selfobj = makeCenterLinePointFeature(m_group)    
                    selfobj.Edge           = edge
                    selfobj.NumberLinePart = m_numberLinePart
                    selfobj.IndexPart      = m_indexPart 
                    selfobj.Proxy.execute(selfobj)
                else:
                    for m_iPart in range(m_numberLinePart+1):
                        App.ActiveDocument.openTransaction("Macro CenterLinePoint")
                        selfobj = makeCenterLinePointFeature(m_group)    
                        selfobj.Edge           = edge
                        selfobj.NumberLinePart = m_numberLinePart
                        selfobj.IndexPart      = m_iPart 
                        selfobj.Proxy.execute(selfobj)
            
            #### From Vertexes
            if Number_of_Vertexes > 2:
                try:
                    m_ob = App.ActiveDocument.getObject(str(m_main_dir)).newObject("App::DocumentObjectGroup", str(m_sub_dir))
                    m_group = m_actDoc.getObject( str(m_ob.Label) )
                except:
                    printError_msg("Could not Create '"+ str(m_sub_dir) +"' Objects Group!")           
             
            if (Number_of_Vertexes % 2 == 0): #even
                if WF.verbose() != 0:
                    print_msg("Even number of points")
                if Number_of_Vertexes == 2:
                    vertex1 = Vertex_List[0]
                    vertex2 = Vertex_List[1]
                    
                    if WF.verbose() != 0:
                        print_msg("vertex1 = " + str(vertex1))
                        print_msg("vertex2 = " + str(vertex2))
                else :
                    for i in range(0,Number_of_Vertexes-2,2):
                        vertex1 = Vertex_List[i]
                        vertex2 = Vertex_List[i+1]
                        
                        if WF.verbose() != 0:
                            print_msg("vertex1 = " + str(vertex1))
                            print_msg("vertex2 = " + str(vertex2))   
            else: #odd
                if WF.verbose() != 0:
                    print_msg("Odd number of points")               
                for i in range(Number_of_Vertexes-1):
                    vertex1 = Vertex_List[i]
                    vertex2 = Vertex_List[i+1]
           
                                   
        finally:
            App.ActiveDocument.commitTransaction()
            
    except Exception as err:
        printError_msg(err.message, title="Macro CenterLinePoint")

                           
if __name__ == '__main__':
    run()