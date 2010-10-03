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

def sort(d, layers, layers_meta):
	#print 'dict: %s' % str(d)
	for key in d.keys():
		#verify this key still exists since the dict can be chaged within this loop
		if not d.has_key(key):
			continue
		val = d[key]
		#print 'key: %s, val: %s' % (key, str(val))
		for key2 in d.keys():
			if not d.has_key(key):
				continue
			val2 = d[key2]
			#if they're the same size, they can't be parents or siblings
			#print key+', '+key2
			#print layers[key]
			if layers[key].width == layers[key2].width and layers[key].height == layers[key2].height:
				continue
			#if key2 is smaller, it might be a child
			elif (layers[key].width >= layers[key2].width) and (layers[key].height >= layers[key2].height):
				#if key2 is within the bounds of key
				if (layers_meta[key]['x'] <= layers_meta[key2]['x'] or layers_meta[key]['x2'] >= layers_meta[key2]['x2']) and (layers_meta[key]['y'] <= layers_meta[key2]['y'] or layers_meta[key]['y2'] >= layers_meta[key2]['y2']):
					#print 'layer: %s, x: %d, y: %d, x2: %d, y2: %d' % (key, layers_meta[key]['x'], layers_meta[key]['y'], layers_meta[key]['x2'], layers_meta[key]['y2'])
					#print 'layer2: %s, x: %d, y: %d, x2: %d, y2: %d' % (key2, layers_meta[key2]['x'], layers_meta[key2]['y'], layers_meta[key2]['x2'], layers_meta[key2]['y2'])
					d[key][key2] = d.pop(key2)
			#otherwise, key2 is a parent of key, in which case it'll be sorted in another iteration
	
	for key in d:
		d[key] = sort(d[key], layers, layers_meta)
	return d

def layers_to_dict(layers, layers_meta):
	print 'layers_to_dict()'
	d = {}
	l = {}
	for layer in layers:
		print layer.name
		d[layer.name] = {}
		l[layer.name] = layer
	d = sort(d, l, layers_meta)
	return (d, l)

def get_html(parent_key, d, layers, layers_meta, css_opacity, depth=0):
	px = 0
	py = 0
	if parent_key is not None:
		px = layers_meta[parent_key]['x']
		py = layers_meta[parent_key]['y']
	else:
		print 'parent: %s, (x, y): %s' % (str(parent_key), str((px, py)))
	style = []
	html = []
	for key in d:
		val = d[key]
		gimp.progress_init('psd2html: Inspecting %s' % layers[key].name)
		if css_opacity:
			opacity_string = """
	opacity: %.1f;
	filter: alpha(opacity=%i);""" % (layers[key].opacity/100.0, layers[key].opacity)
		else:
			opacity_string = ''
		
		if parent_key is None:
			print 'child: %s, (x, y): %s' % (key, str((layers_meta[key]['x'], layers_meta[key]['y'])))
		sub_s, sub_html = get_html(key, val, layers, layers_meta, css_opacity, depth=depth+1)
		#print 'sub_s: %s' % sub_s
		#CSS for this layer
		s = """#%s
{
	background-image: url("%s");
	position: absolute;
	top: %dpx;
	left: %dpx;
	width: %dpx;
	height: %dpx;%s
}

%s""" % (layers_meta[key]['id'], layers_meta[key]['image_rel_path'], layers_meta[key]['y']-py, layers_meta[key]['x']-px, layers[key].width, layers[key].height, opacity_string, sub_s)
		#html for this layer
		indent = '\t'*depth
		h = """%s<div id=\"%s\">
%s
%s</div>
""" % (indent, layers_meta[key]['id'], sub_html, indent)
		style.append(s)
		html.append(h)
		
	style = ''.join(style)
	html = ''.join(html)
	return (style, html)

def plugin_func(image, drawable, css_opacity):
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
	plugin_func(gimp.image_list()[0], gimp.image_list()[0], True)
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
	html_file = os.open(html_file_path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
	media_dir = filename+'_files'
	if not os.path.exists(media_dir):
		os.mkdir(media_dir)
	css_file_path = os.path.join(directory, media_dir, 'style'+os.path.extsep+'css')
	css_file = os.open(css_file_path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
	
	disallowed_chars = re.compile(r'[^\w-]+')
	leading_nonletters = re.compile(r'^([^a-z]+)(.*)')
	layers_meta = {}
	for layer in reversed(image.layers):
		layers_meta[layer.name] = {}
		layers_meta[layer.name]['x'], layers_meta[layer.name]['y'] = layer.offsets
		layers_meta[layer.name]['x2'] = layers_meta[layer.name]['x'] + layer.width
		layers_meta[layer.name]['y2'] = layers_meta[layer.name]['y'] + layer.height
		#TODO: only export visible layers
		#TODO: test for empty and duplicate ids
		#replace disallowed characters with an underscore
		layers_meta[layer.name]['id'] = disallowed_chars.sub('_', layer.name.lower())
		#remove leading non-letters
		layers_meta[layer.name]['id'] = leading_nonletters.sub(r'\2_\1', layers_meta[layer.name]['id'])
		#remove leading and trailing underscores
		layers_meta[layer.name]['id'] = layers_meta[layer.name]['id'].strip('_')
		
		#for debugging
		print layers_meta[layer.name]['id']
		image_ext = 'png'
		image_path = os.path.join(directory, media_dir, layers_meta[layer.name]['id']+os.path.extsep+image_ext)
		#the path relative from the css file
		layers_meta[layer.name]['image_rel_path'] = os.path.relpath(image_path, os.path.dirname(css_file_path))
		#if layer is an image extract it to filename_files/
		add_progress(1)
		gimp.progress_init('psd2html: Saving %s' % image_path)
		pdb.gimp_file_save(image, layer, image_path, image_path, run_mode=1)
		add_progress(2)
		#to do later: if layer is text, create a text node
	
	d, layers = layers_to_dict(reversed(image.layers), layers_meta)
	css, inner_html = get_html(None, d, layers, layers_meta, css_opacity)
	
	html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="generator" content="psd2html GIMP Plug-in" />
	<link href="%s" rel="stylesheet" type="text/css" />
</head>
<body>
%s
</body>
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
	#to do later: detect if multiple layers have the same size and position and treat them like buttons. Option to extract as css sprites.
	#to do later: use an XML library to construct .html file. Use an XHTML 1.0 Strict doctype and validate the markup.
	#to do later: add the following optional tests: 
	#				Validate XHTML, CSS, JS
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
		(PF_TOGGLE, "css-opacity", "Whether to use CSS to specify opacity (1, True) or save it in the image file (0, False).", None),
		#TODO: add option for interactive file saving, and another for css defined opacity
		#to do later: add options for manually choosing CSS and JS to use, could be useful for compatibility with CSS and JS frameworks
	],
	[],
	plugin_func,
	menu="<Image>/Filters/Web",
	domain=("gimp20-python", gimp.locale_directory),
	)

main()

