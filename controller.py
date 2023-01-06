from PyQt5.QtWidgets import (
    QTabWidget, QStatusBar, QWidget, QLabel,
    QMainWindow, QMessageBox, QToolButton,
    QVBoxLayout, QScrollArea, QSplitter,
    QFileDialog
)
from myPackage.Capture import Capture
from myPackage.Tuning.Tuning import Tuning
from myPackage.read_param_value import read_c7_param_value, read_c6_param_value
from myPackage.read_trigger_data import read_c7_trigger_data, read_c6_trigger_data
from myPackage.set_param_value import set_c7_param_value
from myPackage.build_and_push import build_and_push_c7

import os
import xml.etree.ElementTree as ET
import json
import threading
import ctypes, inspect

from UI.MainWindow import MainWindow

class MainWindow_controller(QMainWindow):
    def __init__(self):
        super().__init__() 
        self.read_param_value = {}
        self.read_param_value["c6project"] = read_c6_param_value
        self.read_param_value["c7project"] = read_c7_param_value

        self.read_trigger_data = {}
        self.read_trigger_data["c6project"] = read_c6_trigger_data
        self.read_trigger_data["c7project"] = read_c7_trigger_data

        self.set_param_value = {}
        self.set_param_value["c7project"] = set_c7_param_value

        self.build_and_push = {}
        self.build_and_push["c7project"] = build_and_push_c7

        self.capture = Capture()
        self.setting = self.read_setting()
        self.config = self.read_config()
        
        self.ui = MainWindow()
        self.ui.setup_UI(self, self.capture)
        self.set_UI_data(self.setting)

        self.capture.logger = self.ui.logger
        self.tuning = Tuning( self.ui.run_page.lower_part, self.setting, self.config, self.capture, 
                                self.set_param_value, self.build_and_push)

        self.setup_controller()
        self.ui.param_page.push_and_save_block.capture_worker.capture = self.capture



    def set_UI_data(self, setting):
        key_data = self.setting[self.setting["root"]][self.setting["key"]]

        ##### project_page #####
        if "platform" in setting:
            self.ui.project_page.platform_selecter.set_platform(setting["platform"])

        if "project_path" in setting:
            self.ui.project_page.label_project_path.setText(setting["project_path"])

            if os.path.exists(setting["project_path"]):
                self.set_project(setting["project_path"])

        if "exe_path" in setting:
            self.ui.project_page.label_exe_path.setText(setting["exe_path"])
        if "bin_name" in setting:
            self.ui.project_page.lineEdits_bin_name.setText(setting["bin_name"])

        ##### ROI_page #####
        if os.path.exists('./capture.jpg'):
            self.ui.ROI_page.set_photo('./capture.jpg')
            if "roi" in setting:
                self.ui.ROI_page.rois = setting["roi"]
                self.ui.ROI_page.draw_ROI(self.ui.ROI_page.rois)

        if 'target_type' in setting and len(setting["target_type"])>0:
            assert len(setting["roi"]) == len(setting["target_type"])
            for i in range(len(setting["target_type"])):
                self.ui.ROI_page.add_to_table(setting["target_type"][i], setting["target_score"][i], setting["target_weight"][i])

        ##### param_page #####
        if "param_change_idx" in key_data: 
            self.ui.param_page.param_modify_block.update_param_change_idx(key_data["param_change_idx"])

        for i, name in enumerate(self.ui.param_page.hyper_setting_block.hyper_param_name):
            if name in self.setting:
                self.ui.param_page.hyper_setting_block.lineEdits_hyper_setting[i].setText(str(self.setting[name]))

        if 'saved_dir_name' in self.setting:
            self.ui.param_page.push_and_save_block.lineEdits_dir_name.setText(self.setting['saved_dir_name'])
        if 'saved_img_name' in self.setting:
            self.ui.param_page.push_and_save_block.lineEdits_img_name.setText(self.setting['saved_img_name'] )

        ##### run page #####
        if "TEST_MODE" in self.setting:
            self.ui.run_page.upper_part.TEST_MODE.setChecked(self.setting["TEST_MODE"])
            self.ui.run_page.upper_part.pretrain.setChecked(self.setting["PRETRAIN"])
            self.ui.run_page.upper_part.train.setChecked(self.setting["TRAIN"])
        
    
    def get_UI_data(self):
        key_data = self.setting[self.setting["root"]][self.setting["key"]]

        ##### project_page #####
        self.setting["project_path"] = self.ui.project_page.label_project_path.text()
        self.setting["exe_path"] = self.ui.project_page.label_exe_path.text()
        self.setting["bin_name"] = self.ui.project_page.lineEdits_bin_name.text()

        ##### ROI_page #####
        self.setting["roi"] = self.ui.ROI_page.rois

        assert len(self.setting["roi"]) == self.ui.ROI_page.table.rowCount()
        self.setting["target_type"] = []
        self.setting["target_score"] = []
        self.setting["target_weight"] = []
        for i in range(self.ui.ROI_page.table.rowCount()):
            self.setting["target_type"].append(self.ui.ROI_page.table.cellWidget(i, 0).text())
            self.setting["target_score"].append(float(self.ui.ROI_page.table.cellWidget(i, 1).text()))
            self.setting["target_weight"].append(float(self.ui.ROI_page.table.cellWidget(i, 2).text()))

        ##### param_page #####
        self.setting["trigger_idx"] = self.ui.param_page.trigger_selector.currentIndex()
        self.setting["trigger_name"] = self.ui.param_page.trigger_selector.currentText()

        key_data["param_value"] = self.ui.param_page.param_modify_block.get_param_value()
        key_data["param_change_idx"] = self.ui.param_page.param_modify_block.get_param_change_idx()

        key_data["coustom_range"] = []
        for item in self.ui.param_page.param_range_block.param_range_items:
            for lineEdit in item.lineEdits_coustom_range:
                if lineEdit.text() != "": 
                    key_data["coustom_range"].append(json.loads(lineEdit.text()))

        for i, name in enumerate(self.ui.param_page.hyper_setting_block.hyper_param_name):
            if self.ui.param_page.hyper_setting_block.lineEdits_hyper_setting[i].text()=="":
                self.setting[name] = ""
            else:
                self.setting[name] = int(self.ui.param_page.hyper_setting_block.lineEdits_hyper_setting[i].text())

        ##### run page #####
        self.setting["TEST_MODE"] = self.ui.run_page.upper_part.TEST_MODE.isChecked()
        self.setting["PRETRAIN"] = self.ui.run_page.upper_part.pretrain.isChecked()
        self.setting["TRAIN"] = self.ui.run_page.upper_part.train.isChecked()

    def setup_controller(self):
        ########## trigger ##########
        #############################

        ##### project_page #####
        self.ui.project_page.platform_selecter.buttongroup1.buttonClicked.connect(self.onPlatformSelecterClicked)
        self.ui.project_page.btn_select_project.clicked.connect(self.select_project)
        self.ui.project_page.btn_select_exe.clicked.connect(self.select_exe)

        ##### param page #####
        self.ui.param_page.trigger_selector.currentIndexChanged[int].connect(self.set_trigger_idx)
        self.ui.param_page.ISP_tree.tree.itemClicked.connect(self.ISP_tree_itemClicked)

        ##### run page #####
        self.ui.run_page.upper_part.btn_run.clicked.connect(self.run)
        self.ui.run_page.upper_part.btn_param_window.clicked.connect(self.show_param_window)

        ########## trigger ##########
        #############################

        ########## tuning ###########
        #############################

        # tuning to param window
        self.tuning.update_param_window_scores_signal.connect(self.ui.param_window.update_scores)
        self.tuning.update_param_window_signal.connect(self.ui.param_window.update)
        self.tuning.setup_param_window_signal.connect(self.ui.param_window.setup)

        # tuning to UI
        self.tuning.finish_signal.connect(self.finish)
        self.tuning.set_score_signal.connect(self.ui.run_page.upper_part.set_score)
        self.tuning.set_generation_signal.connect(self.ui.run_page.upper_part.set_generation)
        self.tuning.set_individual_signal.connect(self.ui.run_page.upper_part.set_individual)

        # tuning logger
        self.tuning.log_info_signal.connect(self.ui.logger.show_info)
        self.tuning.run_cmd_signal.connect(self.ui.logger.run_cmd)

        ########## tuning ###########
        #############################


        ##### capture signal #####
        self.capture.capture_fail_signal.connect(self.capture_fail)
        self.capture.log_info_signal.connect(self.ui.logger.show_info)
        self.capture.run_cmd_signal.connect(self.ui.logger.run_cmd)

        # alert_info_signal
        self.ui.project_page.alert_info_signal.connect(self.alert_info)
        self.ui.ROI_page.alert_info_signal.connect(self.alert_info)
        self.ui.param_page.push_and_save_block.alert_info_signal.connect(self.alert_info)
        self.ui.run_page.upper_part.alert_info_signal.connect(self.alert_info)
        self.tuning.alert_info_signal.connect(self.alert_info)

        self.ui.param_page.push_and_save_block.set_param_value_signal.connect(self.set_param_value_slot)
        self.ui.param_page.push_and_save_block.push_worker.push_to_camera_signal.connect(self.build_and_push_slot)
        self.ui.param_page.push_and_save_block.get_UI_date_signal.connect(self.get_UI_data)
        
        # # ML logger
        # self.tuning.ML.log_info_signal.connect(self.ui.logger.show_info)

    def set_param_value_slot(self):
        key_config = self.config[self.setting["platform"]][self.setting["root"]][self.setting["key"]]
        self.set_param_value[self.setting["platform"]](self.setting["key"], key_config, self.setting["project_path"], self.setting["trigger_idx"], self.setting["param_value"])

    def build_and_push_slot(self):
        self.ui.logger.show_info('push bin to camera...')
        self.ui.logger.run_cmd('adb shell input keyevent = KEYCODE_HOME')
        self.build_and_push[self.setting["platform"]](self.setting["exe_path"], self.setting["project_path"], self.setting["bin_name"])
        self.capture.clear_camera_folder()
        self.ui.logger.show_info('wait for reboot camera...')

    def onPlatformSelecterClicked(self):
        self.ui.project_page.label_project_path.setText("")
        self.ui.project_page.label_exe_path.setText("")
        if self.ui.project_page.platform_selecter.buttongroup1.checkedId() == 1:
            self.setting["platform"] = self.ui.project_page.platform_selecter.rb1.text()
            self.ui.project_page.setc6Form()

        if self.ui.project_page.platform_selecter.buttongroup1.checkedId() == 2:
            self.setting["platform"] = self.ui.project_page.platform_selecter.rb2.text()
            self.ui.project_page.setc7Form()
        
        

    def ISP_tree_itemClicked(self, item, col):
        if item.parent() is None: 
            if item.isExpanded():item.setExpanded(False)
            else: item.setExpanded(True)
            return

        root = item.parent().text(0)
        key = item.text(0)
        self.change_page_to(root, key)


    def change_page_to(self, root, key):
        self.setting["root"] = root
        self.setting["key"] = key
        self.ui.logger.signal.emit('Change param page to {}/{}'.format(root, key))

        ##### param_page UI #####
        key_config = self.config[self.setting["platform"]][self.setting["root"]][self.setting["key"]]
        key_data = self.setting[self.setting["root"]][self.setting["key"]]

        self.ui.param_page.param_modify_block.update_UI(key_config)
        self.ui.param_page.param_range_block.update_UI(key_config)
        self.ui.param_page.param_range_block.update_defult_range(key_config["defult_range"])
        if "coustom_range" in key_data and len(key_data["coustom_range"])>0:
            self.ui.param_page.param_range_block.update_coustom_range(key_data["coustom_range"])
        else:
            self.ui.param_page.param_range_block.update_coustom_range(key_config["defult_range"])

        self.ui.param_page.trigger_selector.setCurrentIndex(self.setting["trigger_idx"])
        self.set_trigger_idx(self.setting["trigger_idx"])

    def select_project(self):
        path = QFileDialog.getExistingDirectory(self,"選擇project", self.ui.project_page.defult_path) # start path
        if path == "": return
        self.ui.project_page.defult_path = path.split('/')[-2]
        self.ui.project_page.label_project_path.setText(path)

        self.ui.logger.show_info('\nset_project')
        self.setting['project_name'] = path.split('/')[-1]
        self.setting['project_path'] = path
        self.set_project(path)

    def select_exe(self):
        path, filetype = QFileDialog.getOpenFileName(self,"選擇ParameterParser", self.ui.project_page.defult_path) # start path
        if path == "": return
        self.ui.project_page.defult_path = path.split('/')[-2]
        self.ui.project_page.label_exe_path.setText(path)

    def set_project(self, project_path):
        self.ui.logger.show_info("set_project_XML")

        key_config = self.config[self.setting["platform"]][self.setting["root"]][self.setting["key"]]
        # xml_path = project_path + key_config["file_path"]

        # # 從檔案載入並解析 XML 資料
        # if not os.path.exists(xml_path):
        #     self.ui.logger.show_info('Return because no such file: '+xml_path)
        #     self.ui.logger.show_info("找不到參數檔案，請確認"+self.setting["project_name"]+"是否為"+self.setting["platform"])
        #     self.ui.project_page.label_project_path.setText("找不到參數檔案，請確認"+self.setting["project_name"]+"是否為"+self.setting["platform"])
        #     self.ui.param_page.reset_UI()
        #     return

        ##### ISP_Tree #####
        tree_data = {}
        for root in self.config[self.setting["platform"]]:
            if root not in self.setting: self.setting["root"] = {}
            tree_data[root] = []
            for key in self.config[self.setting["platform"]][root]:
                if key not in self.setting[root]: self.setting[root][key] = {}
                tree_data[root].append(key)
        self.ui.param_page.ISP_tree.update_UI(tree_data)

        aec_trigger_datas = self.read_trigger_data[self.setting["platform"]](key_config, self.setting["project_path"])

        self.ui.param_page.trigger_selector.update_UI(aec_trigger_datas)
        self.ui.logger.show_info("Load {} Successfully".format(self.setting["project_name"]))
        self.change_page_to(self.setting["root"], self.setting["key"])

    def set_trigger_idx(self, trigger_idx):
        if trigger_idx==-1:
            self.ui.logger.signal.emit("set_trigger_idx return because trigger_idx=-1")
            return
        self.ui.logger.signal.emit('trigger_idx: {}'.format(trigger_idx))

        key_config = self.config[self.setting["platform"]][self.setting["root"]][self.setting["key"]]
        
        param_value = self.read_param_value[self.setting["platform"]](key_config, self.setting["project_path"], trigger_idx)
        self.ui.param_page.param_modify_block.update_param_value(param_value)

    def run(self):
        print('click run btn')
        if self.tuning.is_run:
            self.finish()
        else:
            self.start()

    def start(self):
        self.get_UI_data()
        self.ui.logger.clear_info()
        self.ui.logger.signal.emit("START")

        self.tuning.is_run = True
        self.ui.run_page.upper_part.btn_run.setText('STOP')
        self.ui.run_page.upper_part.mytimer.startTimer()

        # 建立一個子執行緒
        self.tuning_task = threading.Thread(target=lambda: self.tuning.run())
        # 當主程序退出，該執行緒也會跟著結束
        self.tuning_task.daemon = True
        # 執行該子執行緒
        self.tuning_task.start()

    def finish(self):
        self.ui.logger.signal.emit("STOP")
        self.tuning.is_run = False
        self.ui.run_page.upper_part.btn_run.setText('Run')
        self.ui.run_page.upper_part.mytimer.stopTimer()
        self.tuning.ML.save_model()
        stop_thread(self.tuning_task)

    def show_param_window(self):
        self.ui.param_window.close()
        self.ui.param_window.resize(400, 400)
        self.ui.param_window.showNormal()

    def capture_fail(self):
        if self.tuning.is_run: self.ui.run_page.upper_part.mytimer.stopTimer()
        QMessageBox.about(self, "拍攝未成功", "拍攝未成功\n請多按幾次拍照鍵測試\n再按ok鍵重新拍攝")
        self.capture.state.acquire()
        self.capture.state.notify()  # Unblock self if waiting.
        self.capture.state.release()
        if self.tuning.is_run: self.ui.run_page.upper_part.mytimer.continueTimer()
    
    def alert_info(self, title, text):
        # print(title)
        self.ui.logger.signal.emit(text)
        QMessageBox.about(self, title, text)

    def read_setting(self):
        if os.path.exists('setting.json'):
            with open('setting.json', 'r') as f:
                return json.load(f)

        else:
            print("找不到設定檔，重新生成一個新的設定檔")
            return {
                "root": "OPE",
                "key": "WNR",
                "OPE":{
                    "WNR":{}
                },
                "trigger_idx": 0,
                "platform": "c7project"
            }

    def read_config(self):
        assert os.path.exists('config')
        config = {}
        for name in os.listdir('config'):
            with open('config/'+name, 'r') as f:
                config[name.split('.')[0]] = json.load(f)

        return config
             

    def write_setting(self):
        print('write_setting')
        with open("setting.json", "w") as outfile:
            outfile.write(json.dumps(self.setting, indent=4))

    def closeEvent(self, event):
        # if self.tuning.is_run: self.run_page.upper_part.finish()
        # if self.param_window: self.param_window.close()
        # if self.tuning.ML: self.tuning.ML.save_model()

        print('window close')
        self.get_UI_data()
        self.write_setting()


def _async_raise(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            return
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
    """
    @profile:強制停掉線程函數
    :param thread:
    :return:
    """
    if thread == None:
        print('thread id is None, return....')
        return
    _async_raise(thread.ident, SystemExit)