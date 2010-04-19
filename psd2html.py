#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import re

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def plugin_func(image, drawable):
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
	
	When testing in the console, call this function with:
	plugin_func(gimp.image_list()[0], gimp.image_list()[0])
	"""
	global progress
	#step used for progress bar. 1 for html file, 1 for css file, 3 for each layer
	step_size = 1 / (2 + 3 * len(image.layers))
	progress = 0
	def add_progress(steps):
		global progress
		progress += steps * step_size
		gimp.progress_update(progress)
	gimp.progress_init('psd2html: Running')
	add_progress(0)
	#get name of file
	filename = os.path.splitext(image.filename)[0]
	directory = os.path.dirname(image.filename)
	#TODO: clean up existing files and folders in case this plugin has already been run (accept overwrite parameter from user, or fail)
	#create filename.html and filename_files/ folder
	html_file_path = os.path.join(directory, filename+os.path.extsep+'html')
	html_file = os.open(html_file_path, os.O_RDWR+os.O_CREAT)
	media_dir = filename+'_files'
	os.mkdir(media_dir)
	css_file_path = os.path.join(directory, media_dir, 'style'+os.path.extsep+'css')
	css_file = os.open(css_file_path, os.O_RDWR+os.O_CREAT)
	
	inner_html = ""
	css = ""
	
	disallowed_chars = re.compile(r'[^\w-]+')
	leading_nonletters = re.compile(r'^([^a-z]+)(.*)')
	#iterate through layers, bottom first (image.layers is ordered top first, bottom last)
	for layer in reversed(image.layers):
		name = layer.name
		gimp.progress_init('psd2html: Inspecting %s' % name)
		#replace disallowed characters with an underscore
		element_id = disallowed_chars.sub('_', name.lower())
		#remove leading non-letters
		element_id = leading_nonletters.sub(r'\2_\1', element_id)
		#remove leading and trailing underscores
		element_id = element_id.strip('_')
		#TODO: test for empty and duplicate ids
		x, y = layer.offsets
		width = layer.width
		height = layer.height
		#for debugging
		print element_id
		image_ext = 'png'
		image_path = os.path.join(directory, media_dir, element_id+os.path.extsep+image_ext)
		#the path relative from the css file
		image_rel_path = os.path.relpath(image_path, os.path.dirname(css_file_path))
		inner_html += "\t<div id=\"%s\"></div>\n" % element_id
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

""" % (element_id, image_rel_path, y, x, width, height)
		
		#if layer is an image extract it to filename_files/ and create <div> element with a background-image set
		
		add_progress(1)
		gimp.progress_init('psd2html: Saving %s' % image_path)
		pdb.gimp_file_save(image, layer, image_path, image_path, run_mode=1)
		add_progress(2)
		#to do later: if layer is text, create a text node
	
	#TODO: needs a clearing stylesheet
	html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="generator" content="psd2html GIMP Plug-in" />
	<link href="%s" rel="stylesheet" type="text/css" />
</head>
<body>
%s</body>
</html>
""" % (os.path.relpath(css_file_path, os.path.dirname(html_file_path)), inner_html)
	
	gimp.progress_init('psd2html: Saving %s' % html_file_path)
	os.write(html_file, html)
	os.close(html_file)
	add_progress(1)
	gimp.progress_init('psd2html: Saving %s' % css_file_path)
	os.write(css_file, css)
	os.close(css_file)
	add_progress(1)
	
	gimp.progress_init('psd2html: Finished')
	gimp.progress_update(1)
	#to do later: arrange nodes into a heirarchy based on size and position. Elements that fit within another element should be a child node.
	#to do later: detect if multiple layers have the same size and position and treat them like buttons. Option to extract as css sprites.
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
		#TODO: add option for interactive file saving, and another for css defined opacity
		#to do later: add options for manually choosing CSS and JS to use, could be useful for compatibility with CSS and JS frameworks
	],
	[],
	plugin_func,
	menu="<Image>/Filters/Web",
	domain=("gimp20-python", gimp.locale_directory),
	)

main()

