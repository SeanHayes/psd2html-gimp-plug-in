#!/usr/bin/env python

#	psd2html - Converts a .psd file (or other layered image) to an .html template.
#	Copyright © 2010 Seán Hayes

#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.

#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.

#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gimpfu import *
import os

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def plugin_func(image, drawable, opaque_image_format, transparent_image_format, translucent_image_format):
	"""
	This is the function that does most of the work. See register() below for more info.
	
	For a given image with the folloing path:
	/home/user/dev/template.psd
	
	the following file structure will result:
	/home/user/dev/template.psd
	/home/user/dev/template.html
	/home/user/dev/template_files/
	/home/user/dev/template_files/style.css
	/home/user/dev/template_files/<layer_name_0>.(gif|jpg|png)
	/home/user/dev/template_files/<layer_name_1>.(gif|jpg|png)
	/home/user/dev/template_files/<layer_name_n...>.(gif|jpg|png)
	
	When testing in the console, call this function with: plugin_func(gimp.image_list()[0], gimp.image_list()[0], 'png', 'png', 'png')
	"""
	#get name of file
	filename = os.path.splitext(image.filename)[0]
	directory = os.path.dirname(image.filename)
	#TODO: clean up existing files and folders in case this plugin has already been run (accept overwrite parameter from user, or fail)
	#create filename.html and filename_files/ folder
	html_file = os.open(os.path.join(directory, filename+os.path.extsep+'html'), os.O_RDWR+os.O_CREAT)
	media_dir = filename+'_files'
	os.mkdir(media_dir)
	css_file = os.open(os.path.join(directory, media_dir, 'style'+os.path.extsep+'css'), os.O_RDWR+os.O_CREAT)
	
	#TODO: needs a clearing stylesheet
	html = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="generator" content="psd2html GIMP Plug-in" />
</head>
<body>
	"""
	css = ""
	#iterate through layers, in order
	for layer in image.layers:
		#TODO: Escape me!
		element_id = layer.name
		#for debugging
		print element_id
		x, y = layer.offsets
		width = layer.width
		height = layer.height
		image_ext = 'png'
		image_file = os.path.join(directory, media_dir, element_id+os.path.extsep+image_ext)
		html += "<div id=\"%s\"></div>\n" % element_id
		#only absolute positioning supported, at least for now
		css += """#%s
{
	background-image: url("%s");
	position: absolute;
	top: %dpx;
	left: %dpx;
	width: %dpx;
	height: %dpx;
}

""" % (element_id, image_file, x, y, width, height)
		#if layer is an image extract it to filename_files/ and create <div> element with a background-image set
		#to do later: if layer is text, create a text node
	
	html += """
</body>
</html>
	"""
	
	os.write(html_file, html)
	os.close(html_file)
	os.write(css_file, css)
	os.close(css_file)
	#to do later: arrange nodes into a heirarchy based on size and position. Elements that fit within another element should be a child node.
	#to do later: detect if multiple layers have the same size and position and treat them like buttons
	#to do later: use an XML library to construct .html file. Use an XHTML 1.0 Strict doctype and validate the markup.
	#to do later: add the following optional tests: 
	#				Validate XHTML, CSS, JS
	#				Selenium tests
	#				Convert generated XHTML to image, compare it to flattened PSD

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

