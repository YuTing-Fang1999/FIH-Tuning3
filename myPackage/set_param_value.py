import os
import xml.etree.ElementTree as ET
import json
import numpy as np
# from myPackage.func import curve_converter

def set_c7_param_value(key, key_config, project_path, trigger_idx, param_value):
    xml_path = project_path + key_config["file_path"]

    # 從檔案載入並解析 XML 資料
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 子節點與屬性
    mod_aec_datas = root.findall(key_config["xml_node"])
    # expand param
    param_value = np.concatenate([[p]*n for p,n in zip(param_value, key_config["expand"])])
    # if key=="ASF":
    #     param_value = np.concatenate([param_value[:-1], curve_converter(np.arange(64), param_value[-1])])

    for i, ele in enumerate(mod_aec_datas):
        if i==trigger_idx:
            rgn_data = ele.find(key_config["data_node"])
            dim = 0
            for param_name in key_config['param_names']:
                parent = rgn_data.find(param_name+'_tab')
                if parent:

                    length = int(parent.attrib['length'])

                    param_value_new = param_value[dim: dim+length]
                    param_value_new = [str(x) for x in param_value_new]
                    param_value_new = ' '.join(param_value_new)

                    # print('old param', wnr24_rgn_data.find(param_name+'_tab/'+param_name).text)
                    rgn_data.find(param_name+'_tab/' + param_name).text = param_value_new
                    # print('new param',wnr24_rgn_data.find(param_name+'_tab/'+param_name).text)

                else:
                    parent = rgn_data.find(param_name)

                    length = int(parent.attrib['length'])

                    param_value_new = param_value[dim: dim+length]
                    param_value_new = [str(x) for x in param_value_new]
                    param_value_new = ' '.join(param_value_new)

                    # print('old param', wnr24_rgn_data.find(param_name+'_tab/'+param_name).text)
                    parent.text = param_value_new
                    # print('new param',wnr24_rgn_data.find(param_name+'_tab/'+param_name).text)

                dim += length
            break

    # write the xml file
    tree.write(xml_path, encoding='UTF-8', xml_declaration=True)