# -*- coding: utf-8 -*-
"""
The script should take about several seconds to run.
usage: converts .scel format to .txt format(搜狗词库提词)
python ./scel2txt.py
"""
import struct
import os

# 搜狗的scel词库就是保存的文本的unicode编码，每两个字节一个字符（中文汉字或者英文字母）
# 找出其每部分的偏移位置即可
# 主要两部分
# 1.全局拼音表，貌似是所有的拼音组合，字典序
#       格式为(index,len,pinyin)的列表
#       index: 两个字节的整数 代表这个拼音的索引
#       len: 两个字节的整数 拼音的字节长度
#       pinyin: 当前的拼音，每个字符两个字节，总长len
#
# 2.汉语词组表
#       格式为(same,py_table_len,py_table,{word_len,word,ext_len,ext})的一个列表
#       same: 两个字节 整数 同音词数量
#       py_table_len:  两个字节 整数
#       py_table: 整数列表，每个整数两个字节,每个整数代表一个拼音的索引
#
#       word_len:两个字节 整数 代表中文词组字节数长度
#       word: 中文词组,每个中文汉字两个字节，总长度word_len
#       ext_len: 两个字节 整数 代表扩展信息的长度，好像都是10
#       ext: 扩展信息 前两个字节是一个整数(不知道是不是词频) 后八个字节全是0
#
#      {word_len,word,ext_len,ext} 一共重复same次 同音词 相同拼音表

# 拼音表偏移，
startPy = 0x1540

# 汉语词组表偏移
startChinese = 0x2628

# 全局拼音表
GPy_Table = {}

# 解析结果
# 元组(词频,拼音,中文词组)的列表
GTable = []


def byte2str(data):
    """
    原始字节码转为字符串
    :param data: 
    :return: 
    """
    pos = 0
    str = ''
    while pos < len(data):
        c = chr(struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0])
        if c != chr(0):
            str += c
        pos += 2
    return str


def getPyTable(data):
    """
    获取拼音表
    :param data: 
    :return: 
    """
    data = data[4:]
    pos = 0
    while pos < len(data):
        index = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        pos += 2
        lenPy = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        pos += 2
        py = byte2str(data[pos:pos + lenPy])

        GPy_Table[index] = py
        pos += lenPy


def getWordPy(data):
    """
    获取一个词组的拼音
    :param data: 
    :return: 
    """
    pos = 0
    ret = ''
    while pos < len(data):
        index = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        ret += GPy_Table[index]
        pos += 2
    return ret


def getChinese(data):
    """
    读取中文表,GTable是全局变量,汇总所有词库的数据。LTable是局部变量，并返回每个scel文件对应的词库数据
    :param data: 
    :return: 
    """
    pos = 0
    LTable = []
    while pos < len(data):
        # 同音词数量
        same = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]

        # 拼音索引表长度
        pos += 2
        py_table_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]

        # 拼音索引表
        pos += 2
        py = getWordPy(data[pos: pos + py_table_len])

        # 中文词组
        pos += py_table_len
        for i in range(same):
            # 中文词组长度
            c_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
            # 中文词组
            pos += 2
            word = byte2str(data[pos: pos + c_len])
            # 扩展数据长度
            pos += c_len
            ext_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
            # 词频
            pos += 2
            count = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]

            # 保存
            GTable.append((count, py, word))
            LTable.append((count, py, word))
            # 到下个词的偏移位置
            pos += ext_len
    return LTable


def scel2txt(file_name):
    """
    scel格式转化为一个整体的txt格式词典
    :param file_name: 
    :return: 
    """
    print('-' * 60)
    with open(file_name, 'rb') as f1:
        data = f1.read()

    print("词库名：", byte2str(data[0x130:0x338]))  # .encode('GB18030')
    print("词库类型：", byte2str(data[0x338:0x540]))
    print("描述信息：", byte2str(data[0x540:0xd40]))
    print("词库示例：", byte2str(data[0xd40:startPy]))

    getPyTable(data[startPy:startChinese])
    getChinese(data[startChinese:])


def scel2txt_sole(file_name):
    """
    每个scel格式文件转化为对应的txt格式词典
    :param file_name: 
    :return: 
    """
    print('-' * 60)
    with open(file_name, 'rb') as a:
        data = a.read()

    print("词库名：", byte2str(data[0x130:0x338]))  # .encode('GB18030')
    print("词库类型：", byte2str(data[0x338:0x540]))
    print("描述信息：", byte2str(data[0x540:0xd40]))
    print("词库示例：", byte2str(data[0xd40:startPy]))

    getPyTable(data[startPy:startChinese])
    LTable = getChinese(data[startChinese:])
    # 保存结果
    for a in fin_txt:
        c = len(a.split('\\'))
        if a.split('\\', c)[c-1].split('.', 1)[0] == file_name.split('\\', c)[c-1].split('.', 1)[0]:
            with open(a, 'w', encoding='utf8') as b:
                b.writelines([word + '\n' for count, py, word in LTable])

# len(a.split('\\'))
if __name__ == '__main__':
    curdir = os.getcwd()
    # 输入scel所在文件夹路径
    in_path = curdir + os.sep + "data"
    fin = [fname for fname in os.listdir(in_path) if fname[-5:] == ".scel"]
    # =============================================================================
    # 输出scel文件汇总的词典
    # =============================================================================
    # 输出txt词典所在文件夹路径
    out_path = os.path.join(curdir, 'dict.txt')
    for f in fin:
        fn = os.path.join(in_path, f)
        scel2txt(fn)
    # 保存结果
    with open(out_path, 'w', encoding='utf8') as f:
        f.writelines([word + '\n' for count, py, word in GTable])
    print('==================================================================')
    print('Med_dict_integral Finished!')
    print('==================================================================')
    # =============================================================================
    # 输出单个scel文件对应的词典
    # =============================================================================
    # 输出单个词典所在文件夹路径
    out_path = curdir + os.sep + "file" + os.sep
    fin = [fname for fname in os.listdir(in_path) if fname[-5:] == ".scel"]
    for f in fin:
        open(out_path + f.split('.', 1)[0] + '.txt', 'w')
    fin_txt = [os.path.join(out_path, fname) for fname in os.listdir(out_path)]
    print(fin_txt)
    for f in fin:
        fn = os.path.join(in_path, f)
        scel2txt_sole(fn)
    print('==================================================================')
    print('Med_dict_sole Finished!')
    print('==================================================================')
