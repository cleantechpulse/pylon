#------------------------------------------------------------------------------
# Copyright (C) 2009 Richard W. Lincoln
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANDABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#------------------------------------------------------------------------------

""" Graph editor.
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

from os.path import join, dirname

from enthought.pyface.image_resource import ImageResource
from envisage.resource.resource_editor import ResourceEditor

from pylon.ui.graph.graph import Graph

#------------------------------------------------------------------------------
#  Constants:
#------------------------------------------------------------------------------

IMAGE_LOCATION = join(dirname(__file__), "..", "ui", "images")

#------------------------------------------------------------------------------
#  "GraphEditor" class:
#------------------------------------------------------------------------------

class GraphEditor(ResourceEditor):
    """ A graph editor for the current network.
    """

    image = ImageResource("dot", search_path=[IMAGE_LOCATION])

    #--------------------------------------------------------------------------
    #  "TraitsUIEditor" interface.
    #--------------------------------------------------------------------------

    def create_ui(self, parent):
        """ Creates the traits UI that represents the editor.
        """

        self.document = document = self.editor_input.load()

        g = Graph(network=document)
        ui = g.edit_traits(parent=parent, kind="subpanel")

        # Dynamic notification of document object modification
        document.on_trait_change(self.on_document_modified)

        return ui

# EOF -------------------------------------------------------------------------