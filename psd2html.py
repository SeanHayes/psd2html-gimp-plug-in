#!/usr/bin/env python

from gimpfu import *
import os

psd2html():
	#get name of file
	#create filename.html and filename_files/ folder
	
	
	#iterate through layers, in order
	#if layer is an image extract it to filename_files/ and create <div> element with a background-image set
	#if layer is text, create a text node
	
	#to do later: arrange nodes into a heirarchy based on size and position. Elements that fit within another element should be a child node.
	#to do later: detect if multiple layers have the same size and position and treat them like buttons

register(
	"py_extract_layers",
	_("Converts a .psd file (or other layered image) to an .html template."),
	_("This is a Python plug-in for the GIMP that will extract images and text out of a .psd file (or other layered image) and create an .html template from it. I don't think this plugin will ever fully replace a human coder, but it should be able to do 50-90% of the work."),
	"Seán Hayes",
	"Seán Hayes",
	"2010",
	_("_Convert to HTML..."),
	"",
	[
		(PF_RADIO, "opaque-image-format", _("Layers without transparency will be saved in this format."), "jpg", (("gif", "gif"), ("jpg", "jpg"), ("png", "png"))),
		(PF_RADIO, "transparent-image-format", _("Layers with transparency will be saved in this format."), "png", (("gif", "gif"), ("png", "png"))),
		(PF_RADIO, "translucent-image-format", _("Layers containing partial transparency will be saved in this format."), "png", (("png", "png"))),
		#to do later: add options for manually choosing CSS and JS to use, could be useful for compatibility with CSS and JS frameworks
	],
	[],
	psd2html,
    menu="<Image>/Filters/Web",
    )

main()

