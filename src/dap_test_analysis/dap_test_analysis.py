import os
import re
import shutil
import xml.etree.ElementTree as ET
from analyzers import *

def update_log(log_file, spec_dir, case_output_dir):
	'''
	This is the interface to DI compatibility test framework, which takes the itaf log and update it,
	using info got from test spec and test output, if certain failed case could be considered acceptable.
	'''
	log_backup = log_file + '.bak'
	shutil.copy2(log_file, log_backup)
	
	with open(log_file, 'r') as f:
		log = f.readlines()
	
	out = []
	report_file = []
	count = 0
	specs = None
	for line in log:
		case = re.match('[0-9]+/[0-9]+\s(\S+)\s(PASSED|FAILED|UNRESOLVED)', line)
		if case is not None:
			if case.group(2) == 'FAILED':
				case_name = case.group(1)[:-3]
				print 'Checking failed test case: %s... ' %(case_name),
				report_file.append('----%s----\n' % case_name)
				
				if specs is None:
					specs = TestCase.get_all_specs(spec_dir)			
				try:
					failed_case = TestCase(case_name, specs, case_output_dir)
					acceptable, report = failed_case.analyze()
				except (TestCaseError, AnalyzerError), e:
					acceptable = False
					report = ['Error: %s\n' %e]
					print '\nError: %s' %e
				
				report_file.extend(report)
				if acceptable:
					line = re.sub('FAILED', 'PASSED', line)
					count += 1
					print 'Test marked as PASSED'
					print line.strip()
				else:
					print 'Test still marked as FAILED'
		else:
			m = re.match('(PASSED|FAILED):\s([-+]?\d+)/([-+]?\d+)$', line)
			if m is not None:
				key, value, tot_value = m.groups()
				value = int(value)
				tot_value = int(tot_value)
				if key == 'PASSED':
					new_value = value + count
				else:
					new_value = value - count
				new_line = line[:m.start(2)] + '%d' % new_value + line[m.end(2):]
				line = new_line
				print "Now %d/%d tests %s (was %d/%d)" %(new_value, tot_value, key, value, tot_value)
				print line.strip()
		out.append(line)
		
	with open('dap_test_analysis_result.txt', 'wb') as f:
		f.writelines(report_file)	

	with open(log_file, 'wb') as f:
		f.writelines(out)

class TestCaseError(Exception): pass

class TestCase(object):
	'''
	An instance of TestCase object is used to encapsulate info and operations
	for failed test cases, the method analyze() would return analysis results
	of the test case.
	'''
	name_to_analyzer = {
					   'FREQCMP' : FreqCmpAnalyzer
					   }
	
	def __init__(self, case_name, specs, case_output_dir):
		self._name = case_name
		self._specs = specs
		self._case_output_dir = os.path.join(case_output_dir, case_name)
		
		
	def analyze(self):	
		acceptable = False
		report = []
		analyzer = self._get_analyzer()
		acceptable, report = analyzer.analyze()

		return (acceptable, report)
		
	
	def _get_analyzer(self):
		eval_tool_name = self._get_eval_tool(self._name)

		if eval_tool_name in TestCase.name_to_analyzer:
			return TestCase.name_to_analyzer[eval_tool_name](self._case_output_dir)
		else:
			raise TestCaseError('Test case: %s uses an unsupported tool: %s' %(self._name, eval_tool_name))

	def _get_eval_tool(self, id):
		eval_tool = None

		for test in self._specs:
			if test.get('id') == id:
				for step in test.findall('step'):
					if step.get('type') == 'eval':
						if step.find('processor') is not None:
							eval_tool = step.find('processor').text
						break
				
				if eval_tool is None:
					eval_tool = self._get_eval_tool(test.get('parent'))
				break
	
		return eval_tool
		

	@staticmethod
	def get_all_specs(spec_dir):
		test_suite = ET.Element('testsuite')
		for file in os.listdir(spec_dir):
			base, ext = os.path.splitext(file)
			if ext == '.xml':
				tests = ET.parse(os.path.join(spec_dir, file)).getroot().findall('testspec')
				test_suite.extend(tests)							

		return test_suite
	
	