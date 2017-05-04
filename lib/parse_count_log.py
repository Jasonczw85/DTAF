#!/usr/bin/ev python

import re
from collections import namedtuple
import pandas as pd
import os
import pdb
import json
import plotly
import plotly.offline as py
import plotly.tools as tls
from plotly.graph_objs import *
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.MIMEMultipart import MIMEMultipart
import argparse
import sys
import logging
from datapro import *


_search_node_name = re.compile('^(\s*)(\S+)\s(\S+)\s\(entered\s(\d+)\stimes\)')
_search_api_usage = re.compile('^\s+(\S+)\s+([0-9]+\.?[0-9]*)\s+([0-9]+\.?[0-9]*)')

_API_USAGE = namedtuple('API_USAGE', ('summary', 'details'))
_SUMMARY = namedtuple('SUMMARY', ('average', 'total'))


class CountNode(object):

	"""
	This class wraps all infos in count_report.log into one CountNode Object
	"""

	def __init__(self, **kwargs):
		self.name = kwargs['name']
		self.loop_times = kwargs['loop_times']
		self.node_id = kwargs['node_id']
		self.spaces = kwargs['spaces']
		self.changelist = kwargs['changelist']

		self.parent_node = None
		self.child_node = []
		self.pid = None
		self.low_usage = None
		self.high_usage = None


class ParseCountReport(object):

	"""
	This class is used to extrac data from dlb_count report and covert them to dataframe
	"""

	def __init__(self, file_path, changelist):
		self.file_path = file_path
		self.changelist = changelist
		self.node_list = []

	def parse(self):
		with open(self.file_path, 'r') as fp:
			lines = fp.readlines()

		node = None
		id = 0
		for l in lines:
			name_mo = _search_node_name.search(l)
			api_usage_mo = _search_api_usage.search(l)

			if name_mo:
				# Initialize CountNode
				args={
					'spaces' : len(name_mo.group(1)),
					'name' : name_mo.group(2),
					'node_id' : id,
					'loop_times' : name_mo.group(4),
					'changelist' : self.changelist
				}
				node = CountNode(**args)
				tag = name_mo.group(3)
				has_duplicate = False
				
				# specify parent_child node relationship
				if self.node_list:
					# find a sub-node
					if node.spaces > self.node_list[-1].spaces:
						node.parent_node = self.node_list[-1]
						self.node_list[-1].child_node.append(node)
					# find a samelevel-node
					elif node.spaces == self.node_list[-1].spaces:
						if self.node_list[-1].parent_node:
							node.parent_node = self.node_list[-1].parent_node
							self.node_list[-1].parent_node.child_node.append(node)
					# find upper-level node summary and exclude root node
					# elif node.spaces < node_list[-1].spaces and node.spaces != 0:
					elif node.spaces < self.node_list[-1].spaces:
						has_duplicate, duplicate_node = findDuplicate(node, self.node_list)
						node = duplicate_node
						self.node_list.remove(duplicate_node)

				self.node_list.append(node)
				low_details = dict()
				id += 1
			elif node and not has_duplicate:
				if api_usage_mo:
					s = api_usage_mo.group(1)
					if s == 'TOTAL':
						# low-level api usage search on one node complete
						low_summary = _SUMMARY(api_usage_mo.group(2), api_usage_mo.group(3))
						node.low_usage = _API_USAGE(low_summary, low_details)
					else:
						# keep searching low_level api usage
						low_details[s] = dict()
						low_details[s]['average'] = api_usage_mo.group(2)
						low_details[s]['total'] = api_usage_mo.group(3)

		self.getPid()

		self.getHighUsage()

		return self.node_list

	# Allocate node pid
	def getPid(self):
		values = sorted(set(map(lambda x : x.spaces, self.node_list)))
		group_node_list = [[y for y in self.node_list if y.spaces==x] for x in values]

		temp_pid = 0
		for ng in group_node_list:
			for n in ng:
				n.pid = temp_pid
			temp_pid += 1

	# Get high level operator usages
	def getHighUsage(self):
		for node in self.node_list:
			prefix = os.getenv('DLB_COUNT_HIGHLEVEL_PREFIX')
			high_details = dict()
			sum = 0
			for n in node.child_node:
				if n.name.startswith(prefix):
					name = n.name[len(prefix):]
					high_details[name] = dict()
					high_details[name]['average'] = None
					high_details[name]['total'] = n.loop_times
					sum += int(n.loop_times)
			
			high_summary = _SUMMARY(None, sum)

			if sum != 0:
				node.high_usage = _API_USAGE(high_summary, high_details)

	# Find duplicate node
	def findDuplicate(node):
		target_node = None
		duplicate = False
		for x in reversed(self.node_list):
			if node.name == x.name:
				target_node = x
				duplicate = True
				break
		
		return (duplicate, target_node)


# Convert CountNode to dataframe
def NodetoDF(node_list):
	ListofRows = []
	for node in node_list:
		node_dict = {
					'id'          :    node.node_id,
					'name'        :    node.name,
					'loop_times'  :    node.loop_times,
					'low_usage'   :    node.low_usage,
					'high_usage'  :    node.high_usage,
					'parent_node' :    node.parent_node,
					'child_node'  :    node.child_node,
					'pid'         :    node.pid,
					'changelist'  :    node.changelist
		}
		ListofRows.append(node_dict)

	df = pd.DataFrame.from_records(ListofRows, \
		columns=['id', 'name', 'loop_times', 'low_usage', 'high_usage', 'parent_node', 'child_node', 'pid', 'changelist'])

	return (df, mergeDF(node_list, 'low_usage'), mergeDF(node_list, 'high_usage'))

# Convert Node_List to json object
def NodetoJSON(root_node):
	d = dict()
	d['name'] = root_node.name
	d['id'] = root_node.node_id
	d['loop_times'] = root_node.loop_times
	d['low_usage'] = root_node.low_usage
	d['high_usage'] = root_node.high_usage
	d['pid'] = root_node.pid
	d['changelist'] = root_node.changelist

	if root_node.child_node:
		d['child_node'] = [NodetoJSON(x) for x in root_node.child_node]

	return d

# Obtain total usage of low/high level APIs in dataframe format
def mergeDF(node_list, api_type):
	mapping = {'low_usage' : 'low_level_api', 'high_usage' : 'high_level_api'}
	df_all = pd.DataFrame()

	for node in node_list:
		attr = getattr(node, api_type)
		if attr:
			for key,value in attr.details.items():
				df = pd.DataFrame([key], columns=[mapping[api_type]])
				df = df.join(pd.DataFrame([int(value['total'])], columns=['total']))
				# df = df.join(pd.DataFrame([cl], columns=['changelist']))
				df_all = df_all.append(df)

	if not df_all.empty:
		# Group record with same api names
		df_all = df_all.groupby(mapping[api_type], as_index=False).sum()
		# Sort in ascent
		df_all = df_all.sort_values(by=['total'], ascending=[False])

	return df_all

# Get total low/high level operator usages under itaf case folder in dataframe format
def getallDF(path, changelist):
	report_list = []
	for root, dir, file in os.walk(path):
		for f in file:
			if f == 'count_report.log':
				report_list.append(os.path.join(root, f))

	df_low_total = pd.DataFrame()
	df_high_total = pd.DataFrame()

	for log in report_list:
		print 'Parsing %s...' %log
		node_list = ParseCountReport(log, changelist).parse()
		df, df_low, df_high = NodetoDF(node_list)

		df_low_total = df_low_total.append(df_low)
		df_high_total = df_high_total.append(df_high)

	df_low_total = df_low_total.groupby('low_level_api', as_index=False).sum()
	df_low_total = df_low_total.sort_values(by=['total'], ascending=[False])

	df_high_total = df_high_total.groupby('high_level_api', as_index=False).sum()
	df_high_total = df_high_total.sort_values(by=['total'], ascending=[False])

	return (df_low_total, df_high_total)

# Send email notifications
def send_email(receivers, subject, content, img=[], att_file=[]):
	me = 'zxchen@dolby.com'
	you = receivers
	msg = MIMEMultipart()
	msg['Subject'] = subject

	for af in att_file:
		if af:
			att = MIMEText(open(af,'rb').read(),'base64','utf8')
			att["Content-Type"] = 'application/octet-stream'
			af = ''.join(af.split('/')[-1:])
			att["Content-Disposition"] = "attachment;filename=%s" %af
			msg.attach(att)
	for i in img:
		if i:
			msg_image = MIMEImage(open(i,'rb').read())
			msg_image.add_header('Content-ID',"<%s>" %i);
			msg.attach(msg_image)
			content += "<td><img src='cid:%s'></td>" %i

	body = MIMEText(content,_subtype='html',_charset='utf8')
	msg.attach(body)

	msg['From'] = 'zxchen@dolby.com'
	msg['to'] = you
	msg['cc'] = ''

	try:
		s = smtplib.SMTP()
		s.connect('mail.dolby.com')
		#       s.login(mail_user,mail_pass)
		s.sendmail(me, you, msg.as_string())
		s.close()
		return True
	except Exception, e:
		print str(e)
		return False

# Get DataFrame fot heatmap plotting
def updateDF(df, caselist, changelist):
	df_update = pd.DataFrame()

	length = 0
	for case in caselist:
		df_temp = pd.DataFrame([case], columns=['high_level_api'])

		usage = 0
		if case in df['high_level_api'].values.tolist():
			length += 1
			usage = df.loc[df['high_level_api']==case, 'total'].values[0]

		df_temp = df_temp.join(pd.DataFrame([int(usage)], columns=['total']))
		df_temp = df_temp.join(pd.DataFrame([changelist], columns=['changelist']))

		df_update = df_update.append(df_temp)

	return (df_update.sort_values(by=['high_level_api'], ascending=[False]), length)

# Get all high level operators in DI
def getAllHigh(path):
	highdict = dict()
	prefix = os.getenv('DLB_COUNT_HIGHLEVEL_PREFIX')
	for root, dir, file in os.walk(path):
		for f in file:
			if f.endswith('txt'):
				algor = os.path.splitext(f)[0]
				filename = os.path.join(root, f)
				caselist = []

				with open(filename, 'r') as fn:
					lines = fn.readlines()

				for l in lines:
					l = l.strip()

					node_mo = _search_node_name.search(l)
					if node_mo:
						name = node_mo.group(2)
						if name.startswith(prefix):
							caselist.append(name[len(prefix):])

				highdict[algor] = list(set(caselist))

	return highdict

# def main():

# 	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# 	parser.add_argument('-d', '--directory',
# 						dest='directory',
# 						action='store',
# 						default='',
# 						help='Directory storing all count reports you want to parse.'
# 						)

# 	parser.add_argument('-e', '--email',
# 						dest='email',
# 						action='append',
# 						default=[],
# 						help='Sending email notification. This could be passed multiple times')

# 	parser.add_argument('--json',
# 						dest='json',
# 						action='store_true',
# 						default=False,
# 						help='Transfer data to json object and store under current workspace as \
# 						data_json.txt.'
# 						)

# 	options = parser.parse_args()

# 	if not options.directory:
# 		parser.error("No parsing directory specified. The option '-d' is missing.\n \
# 			Try parse_count_log.py --help for more information")

# 	logger = logging.getLogger('Parse Count Report')
# 	logger.setLevel(logging.DEBUG)
# 	format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 	fh = logging.FileHandler('')





if __name__=='__main__':

	# sys.exit(main())

	# log = 'count_report.log'
	# node_list = ParseCountReport(log, 'v4.9_release').parse()
	# for node in node_list:
	# 	print (''.center(78, '#'))
	# 	print "Current node is %s, id is %d, pid is %d, loop %s times" \
	# 	%(node.name, node.node_id, node.pid, node.loop_times)
		
	# 	print "Low-Level API Usage is ", node.low_usage
		
	# 	print "High-Level API Usage is ", node.high_usage
		
	# 	if node.parent_node:
	# 		print "Parent node is ", node.parent_node.name
	# 	else:
	# 		print "Parent node is None"
		
	# 	print "Child node is ", [x.name for x in node.child_node]
	
	#################### CountNode to json object ####################
	# json_tree = NodetoJSON(node_list[-1])

	# print json.dumps(json_tree, indent=4)
	
	# #################### CountNode to datafram object ####################
	# df, df_low, df_high = NodetoDF(node_list)

	# # Plot Bar Type Usage
	# fig = tls.make_subplots(rows=2, cols=1, subplot_titles=('Low_Level_Usage', 'High_Level_Usage'))
	# fig.append_trace({'x' : df_low['low_level_api'], 'y' : df_low['total'], 'type' : 'bar', \
	# 	'name' : 'Low_Level', 'marker': {"color": "#0F8C79"}}, 1, 1)
	# fig.append_trace({'x' : df_high['high_level_api'], 'y' : df_high['total'], 'type' : 'bar', \
	# 	'name' : 'High_Level', 'marker': {"color": "#0066FF"}}, 2, 1)
	# fig['layout']['xaxis1'].update(title='Low_Level_APIs')
	# fig['layout']['xaxis2'].update(title='High_Level_APIs')
	# fig['layout']['yaxis1'].update(title='Total Usage')
	# fig['layout']['yaxis2'].update(title='Total Usage')
	# fig['layout'].update(title='Low/High Level APIs Usage in DDP v4.9 GA')
	# py.plot(fig, filename='usage.html')


	#################### CountNode to datafram object (Including Usage Diffs) ####################
	# log_ref = 'count_report_ref.log'
	# log_dut = 'count_report_dut.log'

	# node_list_ref = ParseCountReport(log_ref, 'ref_cl').parse()
	# node_list_dut = ParseCountReport(log_dut, 'dut_cl').parse()
	
	# # CountNode to DataFrame format
	# df_total_ref, df_low_ref, df_high_ref = NodetoDF(node_list_ref)
	# df_total_dut, df_low_dut, df_high_dut = NodetoDF(node_list_dut)

	# df_common_low = pd.merge(df_low_ref, df_low_dut, on=['low_level_api', 'total'], how='inner')
	# df_diff_low_ref = \
	# df_low_ref[~df_low_ref.low_level_api.isin(df_common_low.low_level_api.values)]
	# df_diff_low_dut = \
	# df_low_dut[~df_low_dut.low_level_api.isin(df_common_low.low_level_api.values)]

	# df_common_high = pd.merge(df_high_ref, df_high_dut, on=['high_level_api', 'total'], \
	# 	how='inner')
	# df_diff_high_ref = \
	# df_high_ref[~df_high_ref.high_level_api.isin(df_common_high.high_level_api.values)]
	# df_diff_high_dut = \
	# df_high_dut[~df_high_dut.high_level_api.isin(df_common_high.high_level_api.values)]
	
	# # Plot total low/high level usage and stored in .html format
	# fig = tls.make_subplots(rows=4, cols=1, subplot_titles=('Low_Level_Usage_Dut_Cl', \
	# 	'High_Level_Usage_Dut_CL', 'Low_Level_Usage_Diff', 'High_Level_Usage_Diff'))

	# fig.append_trace({'x' : df_low_dut['low_level_api'], 'y' : df_low_dut['total'], 'type' : \
	# 	'bar', "marker": {"color": "#0F8C79"}, 'showlegend' : False}, 1, 1)
	# fig.append_trace({'x' : df_high_dut['high_level_api'], 'y' : df_high_dut['total'], 'type' : \
	# 	'bar', "marker": {"color": "#0F8C79"}, 'showlegend' : False}, 2, 1)

	# if not df_diff_low_dut.empty:
	# 	fig.append_trace({'x' : df_diff_low_dut['low_level_api'], \
	# 		'y' : df_diff_low_dut['total'], 'type' : 'bar', "marker": {"color": "#0F8C79"}, \
	# 		'showlegend' : False}, 3, 1)
	# if not df_diff_low_ref.empty:
	# 	fig.append_trace({'x' : df_diff_low_ref['low_level_api'], \
	# 		'y' : df_diff_low_ref['total'], 'type' : 'bar', "marker": {"color": "#BD2D28"}, \
	# 		'showlegend' : False}, 3, 1)

	# if not df_diff_high_dut.empty:
	# 	fig.append_trace({'x' : df_diff_high_dut['high_level_api'], \
	# 		'y' : df_diff_high_dut['total'], 'name' : 'dut_cl', 'type' : 'bar', \
	# 		"marker": {"color": "#0F8C79"}, 'showlegend' : False}, 4, 1)
	# if not df_diff_high_ref.empty:
	# 	fig.append_trace({'x' : df_diff_high_ref['high_level_api'], \
	# 		'y' : df_diff_high_ref['total'], 'name' : 'ref_cl', 'type' : 'bar', \
	# 		"marker": {"color": "#BD2D28"}, 'showlegend' : False}, 4, 1)

	# fig['layout']['xaxis1'].update(title='Low_Level_APIs')
	# fig['layout']['xaxis3'].update(title='Low_Level_APIs')
	# fig['layout']['xaxis2'].update(title='High_Level_APIs')
	# fig['layout']['xaxis4'].update(title='High_Level_APIs')
	# fig['layout']['yaxis1'].update(title='Total Usage')
	# fig['layout']['yaxis2'].update(title='Total Usage')
	# fig['layout']['yaxis3'].update(title='Total Usage')
	# fig['layout']['yaxis4'].update(title='Total Usage')
	# fig['layout'].update(title='Low/High Level APIs Usage in DDP')

	# py.plot(fig, filename='usage.html')
	
	################## Generating Total Usage Results ####################
	white_path = '/home/zxchen/zxchen_temp_workspace/dlb_count'
	casedict = getAllHigh(white_path)

	filename = '/home/zxchen/zxchen_temp_workspace/dlb_count/out.log'

	casedict['fft'] = []
	casedict['dct'] = []
	casedict['qmf'] = []

	with open(filename, 'r') as fn:
		lines = fn.readlines()

		for l in lines:
			l = l.strip()

			mo = _search_node_name.search(l)
			casename = mo.group(2).split('yyao_')[1]

			if 'dct' in casename:
				casedict['dct'].append(casename)
			elif 'fft' in casename and not casename.startswith('fft'):
				casedict['fft'].append(casename)
			elif 'qmf' in casename:
				casedict['qmf'].append(casename)

	casedict['fft'] = list(set(casedict['fft']))
	for x in ['fft_open', 'ifft_open', 'fft_is_ok', 'fft_close', 'ifft_close']:
		casedict['fft'].append(x)
	casedict['dct'] = list(set(casedict['dct']))
	casedict['qmf'] = list(set(casedict['qmf']))

	length = 0
	for v in casedict.values():
		length += len(v)
	print "There are %s high level operators in total" %length

	# search_dict = {
	# 				# 'AC4' : '/home/zxchen/zxchen_temp_workspace/cidk/Dolby_AC-4_Decoder_Imp/Test_Tools/work_transcode',
	# 				'DAP' : '/home/zxchen/zxchen_temp_workspace/cidk/Dolby_Audio_Processing_Imp/Test_Tools/dap_cpdp_test/test/work',
	# 				'Bacchus' : '/home/zxchen/zxchen_temp_workspace/cidk/Dolby_Digital_Plus_Decoder_Imp/Test_Tools/work'
	# }

	# for key, value in search_dict.items():
	# 	df_low, df_high = getallDF(value, key)

	# 	print "%s use %s low level operators in total" % (key, \
	# 		len(df_low['low_level_api'].values.tolist()))
	# 	print "%s use %s high level operators in total" % (key, \
	# 		len(df_high['high_level_api'].values.tolist()))

	# 	csv_low = os.path.join(os.getcwd(), ('%s_low.csv') %key)
	# 	csv_high = os.path.join(os.getcwd(), ('%s_high.csv') %key)

	# 	df_low.to_csv(csv_low, columns=['low_level_api', 'total'], index=False)
	# 	df_high.to_csv(csv_high, columns=['high_level_api', 'total'], index=False)

	# 	fig = tls.make_subplots(rows=2, cols=1, subplot_titles=('Low_Level_Usage', 'High_Level_Usage'))
	# 	fig.append_trace({'x' : df_low['low_level_api'], 'y' : df_low['total'], \
	# 		'type' : 'bar', 'name' : 'Low_Level', 'marker': {"color": "#0F8C79"}}, 1, 1)
	# 	fig.append_trace({'x' : df_high['high_level_api'], 'y' : df_high['total'], \
	# 		'type' : 'bar', 'name' : 'High_Level', 'marker': {"color": "#0066FF"}}, 2, 1)
	# 	fig['layout']['xaxis1'].update(title='Low_Level_APIs')
	# 	fig['layout']['xaxis2'].update(title='High_Level_APIs')
	# 	fig['layout']['yaxis1'].update(title='Total Usage')
	# 	fig['layout']['yaxis2'].update(title='Total Usage')
	# 	fig['layout'].update(title='Low/High Level APIs Usage')
	# 	py.plot(fig, filename=('usage_%s.html') %key)


	df1_high = pd.read_csv('AC4_high.csv')
	df2_high = pd.read_csv('DAP_high.csv')
	df3_high = pd.read_csv('Bacchus_high.csv')

	caselist = []
	for df in [df1_high, df2_high, df3_high]:
		caselist.extend(df['high_level_api'].values.tolist())
	caselist = list(set(caselist))

	print "There are %s high level operators used in total" %len(caselist)

	# df1_heatmap = updateDF(df1_high, caselist, 'AC4')
	# df2_heatmap = updateDF(df2_high, caselist, 'DAP')
	# df3_heatmap = updateDF(df3_high, caselist, 'Bacchus')

	# pdb.set_trace()

	# trace = {
	# 			"y" : ['AC4', 'DAP', 'Bacchus'],
	# 			"x" : df1_heatmap['high_level_api'].values.tolist(),
	# 			"z" : [df1_heatmap['total'].values.tolist(), df2_heatmap['total'].values.tolist(), df3_heatmap['total'].values.tolist()],
	# 			"type": "heatmap",
	# 			"colorscale" : [[0, "rgb(255,0,0)"], [0.5, "rgb(255,100,0)"], \
	# 			[1, "rgb(255,210,0)]"]],
	# 			"reversescale": True
	# }

	# data = ([trace])

	# layout = {
	# 			"showlegend": False,
	# 			"title" : \
	# 			"High Level Operator Usages Comparison in AC4, DAP and Bacchus"
	# }

	# fig = Figure(data=data, layout=layout)
	# py.plot(fig, filename='comparison_heatmap.html')


	caselist_diff = []
	for key, value in casedict.items():
		case_inter = list(set(value).intersection(set(caselist)))
		caselist_diff.extend(case_inter)
	casedict['blkvec'].extend(list(set(caselist) - set(caselist_diff)))
	casedict['blkvec'].remove('LdivLL')
	casedict['blkvec'].remove('LrecipI')

	for key, value in casedict.items():
		case_inter = list(set(value).intersection(set(caselist)))
		print "There are %s high level operatos in %s in total" %(len(set(value)), key)
		print "There are %s high level operators used in %s in total" %(len(case_inter), key)
		
		df1_heatmap, length1 = updateDF(df1_high, case_inter, 'AC4')
		print "AC4 uses %s high level operators in %s" %(length1, key)
		df2_heatmap, length2 = updateDF(df2_high, case_inter, 'DAP')
		print "DAP uses %s high level operators in %s" %(length2, key)
		df3_heatmap, length3 = updateDF(df3_high, case_inter, 'Bacchus')
		print "Bacchus uses %s high level operators in %s" %(length3, key)
		
		# trace = {
		# 			"y" : ['AC4', 'DAP', 'Bacchus'],
		# 			"x" : df1_heatmap['high_level_api'].values.tolist(),
		# 			"z" : [df1_heatmap['total'].values.tolist(), df2_heatmap['total'].values.tolist(), df3_heatmap['total'].values.tolist()],
		# 			"type": "heatmap",
		# 			"colorscale" : [[0, "rgb(230,0,0)"], [0.5, "rgb(255,210,0)"], [1, "rgb(255,255,255)]"]],
		# 			"reversescale": True
		# }

		# data = ([trace])

		# layout = {
		# 			"showlegend": False,
		# 			"title" : \
		# 			"High Level Operator Usages of %s Comparison in AC4, DAP and Bacchus" %key
		# }

		# fig = Figure(data=data, layout=layout)
		# py.plot(fig, filename=('comparison_heatmap_%s.html') %key)


	# #################### Sending out Email Notifications ####################

	# print "Sending Email Notifications..."

	# subject = '[Daily Report]::Dolby Intrinsics High/Low APIs Usage Monitor'
	# content = 'See attached for details on DI low/high usage within DDP v4.9 GA, DAP v2.5.4 and AC4_Decoder v1.5.0'
	# send_email('zxchen@dolby.com', subject, content, [], ['usage_ac4_v1.5.0.html', 'usage_udc_4.9.html', 'usage_dap_2.5.4.html'])