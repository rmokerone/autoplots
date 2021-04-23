

import re
import os
import subprocess
import logging
import shutil
from sys import argv

DEBUG = True

command = "./start.sh" # 运行时候的脚本
target_dir = "/mnt"  # P好的文件要转移的位置
filename_pattern = re.compile(r"Generating plot for k=(\d+) filename=(\S+) id=(\S+)")
path_pattern = re.compile(r"Renamed final file from \"(\S+)\" to \"(\S+)\"")
progress_pattern = re.compile(r"Progress: (\S+)")

# 获取这次运行过程中产生的k,filename,id
# Generating plot for k=32 filename=plot-k32-2021-04-12-22-58-e4f43122a8739f2377d043369ce018e09ef7e3b817340a246c1fa8e585a4d435.plot id=0xe4f43122a8739f2377d043369ce018e09ef7e3b817340a246c1fa8e585a4d435
def update_k_filename_id(line, d):
    match = filename_pattern.match(line)
    if match:
        _k, _filename, _id = match.groups()
        _k = int(_k)
        d['k'] = _k
        d['filename'] = _filename
        d['id'] = _id
        print(d)
        return True
    return False

# 获取程序运行过程中转移路径的信息
# Renamed final file from \"/home/vroot/Plots/plot-k32-2021-04-12-22-58-e4f43122a8739f2377d043369ce018e09ef7e3b817340a246c1fa8e585a4d435.plot.2.tmp\" to \"/home/vroot/Plots/plot-k32-2021-04-12-22-58-e4f43122a8739f2377d043369ce018e09ef7e3b817340a246c1fa8e585a4d435.plot\"
# r"Renamed final file from \"(\S+)\" to \"(\S+)\""
def update_tmppath_finalpath(line, d):
    match = path_pattern.match(line)
    if match:
        _tmppath, _finalpath = match.groups()
        d['tmppath'] = _tmppath
        d['finalpath'] = _finalpath
        print(d)
        return True
    return False

def compare_filename_and_path(d):
    filename = d.get('filename')
    finalpath = d.get('finalpath')
    if filename == None or finalpath == None:
        return False

    if os.path.basename(finalpath) == filename:
        print("same name: %s" % filename)
        return True

# Progress: 4.167
# 打印P盘进度
def print_progress(line):
    match = path_pattern.match(line)
    if match:
        (_progress,) = match.groups()
        print(line)
    
# 移动文件到目标文件夹
def move_file_to_target(d, target_dir):
    finalpath = d.get('finalpath')
    if finalpath == None:
        return False 
    shutil.move(finalpath, target_dir)
    return True


# 运行一次程序
def run_once():
    logging.basicConfig(filename='debug.log',format='%(message)s', level=logging.DEBUG)

    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    returncode = cmd.poll()

    info_dict = {}
    while returncode is None:
        line = cmd.stdout.readline().strip().decode('utf-8')
        returncode = cmd.poll()
        # 将日志写入到debug文件中
        logging.debug(line)

        if update_k_filename_id(line, info_dict):
            print("result=%s" % info_dict)

        if update_tmppath_finalpath(line, info_dict):
            print("path result=%s" % info_dict)
        # 打印进度
        print_progress(line)

    if compare_filename_and_path(info_dict) and move_file_to_target(info_dict, target_dir):
        print("move file success!")
    else:
        print("move file failure!")

    print("finish %s" % info_dict.get('filename'))

if __name__=="__main__":
    if len(argv) != 2:
        print("help: ")
        print("python3 %s cycle_num" % argv[0])
    else:
        for i in range(int(argv[1])):
            print("[+] IN CYCLE %d" % i)
            run_once()