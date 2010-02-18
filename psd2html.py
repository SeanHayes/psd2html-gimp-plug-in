#!/usr/bin/env python

from gimpfu import *
import os

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def plugin_func(image, drawable, opaque_image_format, transparent_image_format, translucent_image_format):
	#get name of file
	filename = os.path.splitext(image.filename)[0]
	#create filename.html and filename_files/ folder
	html_file = os.open(filename+os.path.extsep+'html', os.O_RDWR+os.O_CREAT)
	directory = os.mkdir(filename+'_files')
	
	html = """
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="generator" content="psd2html GIMP Plug-in" />
</head>
<body>
	"""
	css = ""
	#iterate through layers, in order
	for layer in image.layers:
		print layer.name
		#TODO: Escape me!
		element_id=layer.name
		image_ext = 'png'
		image_file = os.path.join(directory, element_id+os.path.extsep+image_ext)
		html += "<div id=\""+element_id+"\"></div>"
		css += "#"+element_id+"{ background-image: src("+image_file+"); }\n"
		#if layer is an image extract it to filename_files/ and create <div> element with a background-image set
		#to do later: if layer is text, create a text node
	
	html += """
</body>
</html>
	"""
	
	os.write(html_file, html)
	os.close(html_file)
	#to do later: arrange nodes into a heirarchy based on size and position. Elements that fit within another element should be a child node.
	#to do later: detect if multiple layers have the same size and position and treat them like buttons
	#to do later: use an XML library to construct .html file. Use an XHTML 1.0 Strict doctype and validate the markup.

register(
	"psd2html",
	_("Converts a .psd file (or other layered image) to an .html template."),
	_("This is a Python plug-in for the GIMP that will extract images and text out of a .psd file (or other layered image) and create an .html template from it. I don't think this plugin will ever fully replace a human coder, but it should be able to do 50-90% of the work."),
	"Seán Hayes",
	"Seán Hayes",
	"2010",
	N_("_Convert to HTML..."),
	"",
	[
		(PF_IMAGE, "image", "Input image", None),
		(PF_DRAWABLE, "drawable", "Input drawable", None),
		(PF_RADIO, "opaque-image-format", _("Layers without transparency will be saved in this format."), "jpg", (("gif", "gif"), ("jpg", "jpg"), ("png", "png"))),
		(PF_RADIO, "transparent-image-format", _("Layers with transparency will be saved in this format."), "png", (("gif", "gif"), ("png", "png"))),
		(PF_RADIO, "translucent-image-format", _("Layers containing partial transparency will be saved in this format."), "png", (("png", "png"))),
		#to do later: add options for manually choosing CSS and JS to use, could be useful for compatibility with CSS and JS frameworks
	],
	[],
	plugin_func,
	menu="<Image>/Filters/Web",
	domain=("gimp20-python", gimp.locale_directory),
	)

main()

