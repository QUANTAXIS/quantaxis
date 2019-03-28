# -*- coding: utf-8 -*-

from unittest import TestCase
import QUANTAXIS as QA
from QUANTAXIS.QAFetch import QATdx
from QUANTAXIS.QAFetch.QATdx import QA_fetch_get_stock_day, select_best_ip, ping, get_ip_list_by_multi_process_ping
from QUANTAXIS.QASU.save_tdx import gen_param, now_time
from QUANTAXIS.QAUtil.QASetting import QA_Setting
from QUANTAXIS.QAUtil.QADate_trade import QA_util_if_tradetime
from QUANTAXIS.QAUtil.Parallelism import Parallelism
import datetime, time
import os
from multiprocessing import cpu_count
from QUANTAXIS.QACmd import QA_SU_save_stock_day


class TestSelect_best_ip(TestCase):
    def test_select_best_ip(self):
        best_ip = select_best_ip()
        ip = best_ip['stock']['ip']
        port = best_ip['stock']['port']
        self.assertTrue(isinstance(ip, str), '未获取到ip')
        self.assertTrue(isinstance(port, int), '未获取到端口号')
        self.assertTrue(ping(ip, port, 'stock') < datetime.timedelta(0, 1, 0),
                        '地址ping不通： {} {} {}'.format(ip, port, ping(ip, port, 'stock')))
        type = 'future'
        ip = best_ip[type]['ip']
        port = best_ip[type]['port']
        self.assertTrue(ping(ip, port, type) < datetime.timedelta(0, 1, 0),
                        '地址ping不通： {} {} {}'.format(ip, port, ping(ip, port, 'stock')))

        code = '000001'
        days = 300
        start = datetime.datetime.now().date() - datetime.timedelta(days)
        end = datetime.datetime.now().date() - datetime.timedelta(10)
        data = QA_fetch_get_stock_day(code, start_date=start, end_date=end)
        # print(data)
        self.assertTrue(len(data) > (end - start).days / 2,
                        '返回数据个数不匹配，数据长度：{},天数（包含节假日）：{}'.format(len(data), (end - start).days / 2))

        # 恢复初始化ip，重新测试ip
        default_ip = {'stock': {'ip': None, 'port': None},
                      'future': {'ip': None, 'port': None}}
        qasetting = QA_Setting()
        qasetting.set_config(
            section='IPLIST', option='default', default_value=default_ip)
        filenames = ['stock_ip_list', 'stock_ip_list_MP']
        for filename in filenames:
            # 删除保存ip的pickle文件
            filename = '{}{}{}.pickle'.format(qasetting.get_config(
                section='LOG', option='path', default_value=""), os.sep, filename)
            if os.path.isfile(filename):
                os.remove(filename)
        best_ip = select_best_ip()
        ip = best_ip['stock']['ip']
        port = best_ip['stock']['port']
        self.assertTrue(isinstance(ip, str), '未获取到ip')
        self.assertTrue(isinstance(port, int), '未获取到端口号')
        ip = best_ip['future']['ip']
        port = best_ip['future']['port']
        self.assertTrue(isinstance(ip, str), '未获取到ip')
        self.assertTrue(isinstance(port, int), '未获取到端口号')
        data = QA_fetch_get_stock_day(code, start, end)
        self.assertTrue(len(data) > (end - start).days / 2,
                        '返回数据个数不匹配，数据长度：{},天数（包含节假日）：{}'.format(len(data), (end - start).days / 2))

    def test_gen_paramz(self):
        codelist = QA.QA_fetch_stock_list_adv().code.tolist()
        days = 300
        start = datetime.datetime.now().date() - datetime.timedelta(days)
        end = datetime.datetime.now().date() - datetime.timedelta(10)
        codeListCount = 200
        ips = get_ip_list_by_multi_process_ping(QA.QAUtil.stock_ip_list, filename='stock_ip_list_MP')
        param = gen_param(codelist[:codeListCount], start, end, IPList=ips[:cpu_count()])
        a = time.time()
        ps = Parallelism(cpu_count())
        ps.add(QA.QAFetch.QATdx.QA_fetch_get_stock_day, param)
        ps.run()
        data = ps.get_results()
        b = time.time()
        t1 = b - a
        data = list(data)
        print('返回数据{}条，用时：{}秒'.format(len(data), t1))
        # print(data)
        # print([x.code.unique() for x in data])
        self.assertTrue(len(data) == codeListCount, '返回结果和输入参数个数不匹配： {} {}'.format(len(data), codeListCount))
        i, j = 0, 0
        for x in data:
            try:
                # print(x)
                i += 1
                self.assertTrue((x is None) or (len(x) > 0), '返回数据太少：{}'.format(len(x)))
                if not ((x is None) or (len(x) > 0)):
                    print('data is None')
                if i % 10 == 0:
                    print(x)
            except Exception as e:
                j += 1
        print(i, j)

    def test_QA_SU_save_stock_day_lastdat(self):
        # 交易时间QA.QAFetch.QATdx.QA_fetch_get_stock_day返回的数据会实时更新
        codelist = QA.QA_fetch_stock_list_adv().code.tolist()
        days = 300
        start = datetime.datetime.now() - datetime.timedelta(days)
        end = datetime.datetime.now()
        if QA_util_if_tradetime(end):
            end2 = end - datetime.timedelta(1)
        else:
            end2 = end
        codeListCount = 200
        a = time.time()
        ps = Parallelism(cpu_count())
        data1 = QA.QAFetch.QATdx.QA_fetch_get_stock_day(codelist[0], start, end)
        data2 = QA.QAFetch.QATdx.QA_fetch_get_stock_day(codelist[0], start, end2)
        # 交易时间段，
        self.assertTrue(len(data1) == len(data2), '数据长度：{} {} 日期： {} {}'.format(len(data1), len(data2), end, end2))
        print('数据长度：{} {} 日期： {} {}'.format(len(data1), len(data2), end, end2))
        print('当前数据： {} {}'.format(data1.close[-1], data2.close[-1]))

        # 设定在交易时间内
        end = datetime.datetime(end.year, end.month, end.day, 10, 0)
        if QA_util_if_tradetime(end):
            end2 = end - datetime.timedelta(1)
        else:
            end2 = end
        codeListCount = 200
        a = time.time()
        ps = Parallelism(cpu_count())
        data1 = QA.QAFetch.QATdx.QA_fetch_get_stock_day(codelist[0], start, end)
        data2 = QA.QAFetch.QATdx.QA_fetch_get_stock_day(codelist[0], start, end2)
        # 交易时间段，
        self.assertFalse(len(data1) == len(data2), '数据长度：{} {} 日期： {} {}'.format(len(data1), len(data2), end, end2))
        print('数据长度：{} {} 日期： {} {}'.format(len(data1), len(data2), end, end2))
        print('当前数据： {} {}'.format(data1.close[-1], data2.close[-1]))

    def test_QA_SU_save_stock_day(self):
        print('start test_QA_SU_save_stock_day')
        codelist = QA.QA_fetch_stock_list_adv().code.tolist()
        days = 300
        start = datetime.datetime.now() - datetime.timedelta(days)
        end = datetime.datetime.now()
        data1 = QA.QA_fetch_stock_day_adv(codelist[0], start, end)
        QA_SU_save_stock_day('tdx', paralleled=True)
        print('end test_QA_SU_save_stock_day')
        data2 = QA.QA_fetch_stock_day_adv(codelist[0], start, end)
        self.assertTrue(
            len(data2) == len(data1) if data1.datetime[-1] == data2.datetime[-1] else len(data2) > len(data1),
            '保存后的数据应该比未保存前长： {} {}'.format(len(data2), len(data1)))

if __name__ == '__main__':
    TestCase.run()
