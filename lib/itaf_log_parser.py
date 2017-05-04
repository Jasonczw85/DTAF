import re
from collections import namedtuple

_search_line = re.compile('(\d{1,6})\/(\d{1,6})\s(\S+)\.\.\.\s(\S+)\s?', re.IGNORECASE)
_search_total_passed = re.compile('^PASSED:\s(\d+\/\d+)', re.IGNORECASE)
_search_total_unresolved = re.compile('^UNRESOLVED:\s(\d+\/\d+)', re.IGNORECASE)
_search_total_failed = re.compile('^FAILED:\s(\d+\/\d+)', re.IGNORECASE)

def parse_itaf_log(log):

	ITAF_RESULT = namedtuple('ITAF_RESULT', ('test_summary', 'detail_results'))
	TEST_SUMMARY = namedtuple('TEST_SUMMARY', ('total_passed', 'total_failed', \
		'total_unresolved'))

	_detail_results = dict()
	_total_passed = None
	_total_failed = None
	_total_unresolved = None


	with open(log, 'rb') as log_file:
		lines = log_file.readlines()

	for each_line in lines:
		each_line = each_line.strip()

		line_mo = _search_line.search(each_line)
		total_passed_mo = _search_total_passed.search(each_line)
		total_failed_mo = _search_total_failed.search(each_line)
		total_unresolved_mo = _search_total_unresolved.search(each_line)

		if line_mo:
			_detail_results[line_mo.group(3)] = line_mo.group(4).lower()
		elif total_passed_mo:
			_total_passed = total_passed_mo.group(1)
		elif total_failed_mo:
			_total_failed = total_failed_mo.group(1)
		elif total_unresolved_mo:
			_total_unresolved = total_unresolved_mo.group(1)

	summary = TEST_SUMMARY(_total_passed, _total_failed, _total_unresolved)
	itaf_result = ITAF_RESULT(summary, _detail_results)

	return itaf_result