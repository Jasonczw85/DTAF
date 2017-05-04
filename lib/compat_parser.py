#!/usr/bin/env python

import pandas as pd
import sys
from collections import namedtuple

sys.path.append('..')

from sqlops.mysqlops import *


class CompatDataFrame(object):

	def __init__(self, **kwargs):
		self.kwargs = kwargs
		self._project_name = kwargs['project_name']
		self._project_version = kwargs['project_version']
		self._project_release = kwargs['project_release']
		self._cl = kwargs['dut_cl']
		self._ref_cl = kwargs['ref_cl']
		self._latest_cl_db = kwargs['latest_cl_db']
		self._updated_by = kwargs['updated_by']
		self._itaf_result = kwargs['itaf_result']
		self._db_eng_signal = kwargs['db_eng_signal']

		self._compare_summary = "Tests pass"
		self._build_msg = "Build passed!"

	def remove_tag(self):

		sql_update = "update CompatTestSummary set updated_by=Null where intrinsic_version='%s' \
		and project_name='%s' and project_version='%s' and project_release='%s'" \
		%(self._latest_cl_db, self._project_name, self._project_version, self._project_release)

		update_mysql(sql_update, self._db_eng_signal)

	def get_ref_result(self):

		column_dict = {
						'intrinsic_version' : self._ref_cl,
						'project_name' : self._project_name,
						'project_version' : self._project_version,
						'project_release' : self._project_release
						}

		summary_dict = {
						'CompatTestSummary' : {'query_column' : 'compare_summary'},
						'CompatBuildSummary' : {'query_column' : 'build_msg'}
						}

		for key, value in summary_dict.items():
			value['column_dict'] = column_dict
			df = read_mysql_select(key, self._db_eng_signal, value['column_dict'], \
				value['query_column'])

			setattr(self, '_'+value['query_column'], str(df[value['query_column']].values[0]))

		# Using read_mysql_query instead since read_musql_monitor method would 
		# end up with "core dumped" error when query table 'Compatibility' with
		# huge mounts of records
		sql_ref_itaf = "select test_api,test_result from Compatibility where \
		intrinsic_version='%s' and project_name='%s' and project_version='%s' \
		and project_release='%s'" %(self._ref_cl, self._project_name, \
			self._project_version, self._project_release)
		self._ref_itaf_result = read_mysql_query(sql_ref_itaf, self._db_eng_signal)

	def get_summary(self):

		COMPARE_RESULT = namedtuple('COMPARE_RESULT', ('diff_cases', 'new_cases'))
		NEW_CASES = namedtuple('NEW_CASES', ('failed_cases', 'unresolved_cases'))

		_diff_cases, _new_cases = compare_dict(self._itaf_result.detail_results, \
			df_to_dict(self._ref_itaf_result, 'test_api', 'test_result'))

		new_cases_failed = [x for x in _new_cases.keys() if _new_cases[x]=='failed']
		new_cases_unresolved = [x for x in _new_cases.keys() if _new_cases[x]=='unresolved']

		ret = any(_diff_cases) or any(new_cases_failed) or any(new_cases_unresolved)

		new_cases = NEW_CASES(new_cases_failed, new_cases_unresolved)
		compare_result = COMPARE_RESULT(_diff_cases, new_cases)

		if ret:
			self._compare_summary = "Tests fail, investigation needed"

		return (int(ret), compare_result)

	def get_df(self):

		CompatBuildSummary_dict = {
									'intrinsic_version' :  [self._cl], 
									'project_name' : [self._project_name], 
									'project_version' : [self._project_version], 
									'project_release' : [self._project_release], 
									'build_result' : [1], 
									'build_msg' : [self._build_msg],
									'updated_by' : [self._updated_by]
									}

		self._CompatBuildSummary_df = pd.DataFrame.from_dict(CompatBuildSummary_dict)

		CompatTestSummary_dict = {
									'intrinsic_version' :  [self._cl], 
									'project_name' : [self._project_name], 
									'project_version' : [self._project_version], 
									'project_release' : [self._project_release], 
									'subtotal_on_passed' : [self._itaf_result.test_summary.total_passed], 
									'subtotal_on_failed' : [self._itaf_result.test_summary.total_failed], 
									'subtotal_on_unresolved' : [self._itaf_result.test_summary.total_unresolved], 
									'compare_summary' : [self._compare_summary], 
									'updated_by' : [self._updated_by]
								}
		self._CompatTestSummary_df = pd.DataFrame.from_dict(CompatTestSummary_dict)

		self._Compatibility_df = pd.DataFrame()
		for key, value in self._itaf_result.detail_results.items():
			Compatibility_dict = {
									'intrinsic_version' :  [self._cl], 
									'project_name' : [self._project_name], 
									'project_version' : [self._project_version], 
									'project_release' : [self._project_release], 
									'test_api' : [key], 
									'test_result' : [value]
								}
			self._Compatibility_df = self._Compatibility_df.append(pd.DataFrame.from_dict(Compatibility_dict))

		return (self._CompatBuildSummary_df, self._CompatTestSummary_df, self._Compatibility_df)


def df_to_dict(df, columnA, columnB):

	result = dict()
	data_len = len(df[columnA])

	for i in range(data_len):
		result[str(df[columnA][i])] = str(df[columnB][i])

	return result

def compare_dict(dut_dict, ref_dict):

	diff_cases = []
	new_cases = dict()

	for key, value in dut_dict.items():
		if ref_dict.has_key(key):
			if ref_dict[key] != value:
				diff_cases.append(key)
		else:
			new_cases[key] = value

	return (diff_cases, new_cases)

if __name__ == "__main__":

	args = {
			'project_name' : 'MS_Mixer',
			'project_version' : 'v2.5.0',
			'project_release' : 'generic_float32_release',
			'dut_cl' : '5000000',
			'ref_cl' : '4022557',
			'latest_cl_db' : '4090753',
			'updated_by' : 'zxchen',
			'itaf_result' : '/mnt/DI_TEST/KL_File/MS_Mixer_v2.0_generic_float32_release.log'
			}

	compat_parser_obj = CompatDataFrame(**args)

	print ("Query Database for Reference Results".center(78,'='))
	compat_parser_obj.get_ref_result()

	print ("Compare ITAF Results".center(78,'='))
	compat_parser_obj.get_summary()

	print ('Generate DataFrame'.center(78, '='))
	compat_parser_obj.get_df()

	print compat_parser_obj._Compatibility_df
	print compat_parser_obj._CompatTestSummary_df
	print compat_parser_obj._CompatBuildSummary_df
