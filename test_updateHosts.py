#!/usr/bin/env python
#
# unit tests for updateHosts.py
#
# script by patrice houlet - 2023 - GPLv3
#

import unittest
import sys
import re

from updateHosts import get_bad_lines, clean_data, patterns, restore_org_le

__version__ = '1.0'


# detect Python 3.7 for version-dependent implementations
PY37 = sys.version_info >= (3, 7)

if not PY37:
   raise Exception('Python 3.7 or later required.')


class Tests(unittest.TestCase):

   @classmethod
   def setUpClass(cls):

      cls.data = [
                  ' This is # a bad line -0',
                  '111.222.333.444 scammers-1.com',
                  '\n0.0.222.0 scammers-2.com',
                  '# \n111.222.333.444 scammers-3.com',
                  '# comment \r\f0.444.0.0 scammers-4.com',
                  '# \n111.222.333.444 sub_domain.scammers-5.com',
                  '0.0.0.0 \n111.222.333.444 scammers-6.com',
                  '0.0.0.0 bad-7.007',
                  '0.0.0.0 bad-8',
                  '0.0.0.0 bad-9.i',
                  '0.0.0.0 sub_domain.bad-10.com',
                  '127.0.0.1 localhost',
                  '127.0.0.1 localhost.localdomain',
                  '127.0.0.1 local',
                  '::1 localhost',
                  '0.0.0.0 0.0.0.0.valid-try-11.net',
                  '0.0.0.0 good-12.012com'
                 ]

      nb = len(cls.data) - 4
      ng = len(cls.data) - nb

      print(">>>>>>>>>>>>>>>>>>>>>>  Tests Setup  >>>>>>>>>>>>>>>>>>>>>>")
      print(f">>> {nb} compromised or non-valid lines")
      print(f">>> {ng} good line")
      print("\n".join(cls.data))
      print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
      print(cls.data)
      print(">>>>>>>>>>>>>>>>>>>  End of Tests Setup  >>>>>>>>>>>>>>>>>>")
      
      cls.bad_data = [
                  (0, ' This is # a bad line -0'),
                  (1, '111.222.333.444 scammers-1.com'),
                  (2, '\n0.0.222.0 scammers-2.com'),
                  (3, '# \n111.222.333.444 scammers-3.com'),
                  (4, '# comment \r\x0c0.444.0.0 scammers-4.com'),
                  (5, '# \n111.222.333.444 sub_domain.scammers-5.com'),
                  (6, '0.0.0.0 \n111.222.333.444 scammers-6.com'),
                  (7, '0.0.0.0 bad-7.007'),
                  (8, '0.0.0.0 bad-8'),
                  (9, '0.0.0.0 bad-9.i'),
                  (10, '0.0.0.0 sub_domain.bad-10.com')
                 ]

      cls.cleaned_data = [
                  '0.0.0.0 sub_domain.bad-10.com',
                  '127.0.0.1 localhost',
                  '127.0.0.1 localhost.localdomain',
                  '127.0.0.1 local',
                  '::1 localhost',
                  '0.0.0.0 0.0.0.0.valid-try-11.net',
                  '0.0.0.0 good-12.012com'
                 ]
      
      cls.restored_data = [
                  '0.0.0.0 sub_domain.bad-10.com',
                  '127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4',
                  '127.0.0.1 local',
                  '::1 localhost localhost.localdomain localhost6 localhost6.localdomain6',
                  '0.0.0.0 0.0.0.0.valid-try-11.net',
                  '0.0.0.0 good-12.012com'
                 ]


   def test_1_get_bad_lines(self):

      print("\n---------- test_get_bad_lines():")

      bad_data = get_bad_lines(self.data)
      self.assertEqual(bad_data, self.bad_data)


   def test_2_clean_data(self):

      print("\n---------- test_clean_data():")

      clean_data(self.data, self.bad_data)   
      self.assertEqual(self.data, self.cleaned_data)


   def test_3_regexes(self):

      print("\n---------- test_regexes():")

      def is_match(prog, str):
         if prog.fullmatch(str) is None:
            return False
         return True

      print('--- Regex domain')
      prog = re.compile(rf"^{patterns('d')}$")

      tds = { 'a.io' : True,
              'abc.com' : True,
              '911.gov' : True,
              's002.my-company.com' : True,
              'xn--nnx388a.cn.com' : True,
              'abc' : False,
              'abc.' : False,
              '.abc.com' : False,
              '-abc.com' : False,
              'abc-.com' : False,
              'abc.-com' : False,
              'abc.com-' : False,
              'abc.c' : False,
              'abc.007' : False,
              'my_host.com' : False,
              'abc%$.com' : False,
              'abc\n.com' : False,
              'abc\r\f.com' : False,
              'abc..com' : False,
              'abc.-.com' : False,
              'news..abc.com' : False,
              'my_host.domain.com' : False,
            }

      for d in tds:
         print(f'{d}\t{tds[d]}')
         self.assertEqual(is_match(prog, d), tds[d])

      print('--- Regex domain2')

      prog = re.compile(rf"^{patterns('d2')}$")

      tds['my_host.domain.com'] = True

      for d in tds:
         print(f'{d}\t{tds[d]}')
         self.assertEqual(is_match(prog, d), tds[d])


   def test_4_restore_org_le(self):

      print("\n---------- test_restore_org_le():")
      
      restore_org_le(self.data)
      self.assertEqual(self.data, self.restored_data)

if __name__ == "__main__":
   unittest.main()