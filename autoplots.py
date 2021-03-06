

import re
import os
import subprocess
import logging
import shutil
from sys import argv
import datetime
import threading

DEBUG = True

command = "./start.sh" # 运行时候的脚本
target_dir = "/mnt"  # P好的文件要转移的位置
filename_pattern = re.compile(r"Generating plot for k=(\d+) filename=(\S+) id=(\S+)")
path_pattern = re.compile(r"Renamed final file from \"(\S+)\" to \"(\S+)\"")
progress_pattern = re.compile(r"Progress: (\S+)")

# move 线程的ID
move_tid = None

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
    match = progress_pattern.match(line)
    if match:
        (_progress,) = match.groups()
        print(line)

# 打印本次消耗的时间
    
# 移动文件到目标文件夹
def move_file_to_target(finalpath, target_dir):
    if finalpath == None:
        return False 
    shutil.move(finalpath, target_dir)
    print("move file success!")
    return True

# 复制文件到目标文件夹
def copy_file_to_target(finalpath, target_dir):
    if finalpath == None:
        return False 
    try:
        shutil.move(finalpath, target_dir)
    except Exception as e:
        print(e)
        print("copy file failure! %s" % finalpath)
        return False 
    print("move file success!")
    print("try to remove file")
    try:
        shutil.rmtree(finalpath)
    except Exception as e:
        print(e)
        print("remove file failure!")
        return False
    print("remove file success!")
    return True


# 运行一次程序
def run_once():
    starttime = datetime.datetime.now()

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

    # 打印P文件消耗的时间
    plot_endtime = datetime.datetime.now()
    print("Plot file cost time: %s" % (plot_endtime - starttime))

    # 单独起一个线程进行文件的复制，不耽误P盘的时间
    if compare_filename_and_path(info_dict):
        # 创建线程
        move_tid = threading.Thread(target=copy_file_to_target, args=(info_dict.get('finalpath'), target_dir))
        move_tid.start()
        
    else:
        print("move file failure!")

    final_endtime = datetime.datetime.now()
    # 打印生成文件名，以及最终消耗时间
    print("finish %s ,cost time %s" % (info_dict.get('filename'), final_endtime-starttime))

if __name__=="__main__":
    logging.basicConfig(filename='debug.log',format='%(message)s', level=logging.DEBUG)
    if len(argv) != 2:
        print("help: ")
        print("python3 %s cycle_num" % argv[0])
    else:
        for i in range(int(argv[1])):
            print("[+] IN CYCLE %d" % i)
            run_once()
        move_tid.join()