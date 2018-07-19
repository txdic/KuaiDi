import pandas as pd
import math
import re

class checkworker(object):
    def run(self, file_name_1, file_name_2, out_file_1, out_file_final):
        # 读取基础表格
        kdzs = pd.read_excel(file_name_1, dtype = {'快递单号':str}).dropna(thresh=5)
        hdxx = pd.read_excel(file_name_2, dtype = {'运单编号':str}).dropna(thresh=3)
        cpxx = pd.read_excel('./app/static/data/产品信息表.xlsx') # 需要维护产品重量
        adrs = pd.read_csv('./app/static/data/addresslist.csv') # 需要维护地址信息


        # 把'发货信息'里的商品文字根据空格或者换行进行识别区分
        def product_to_list(cell):
            if type(cell)==float or len(cell)<5:
                x = None
            else:
                x = re.split('    |\n', cell)
            return x

        kdzs['bag'] = kdzs['发货信息'].apply(product_to_list)

        # 读取文字描述， 读取 商品名称 和商品数量
        def get_numbers(piece):
            num = int(re.findall('.*\[ ?(\d+\.?\d?)\]', piece)[0])

            return num

        def get_product(piece):
            piece = piece.replace(' ','') # 文字规范：一律取消空格
            product = re.findall('(.*)\[ ?\d+\.?\d?\]', piece)[0]

            return product


        def get_product_num(cell):

            product_num = list()
            illegal_product_num = dict()

            if cell is None:
                pass
            else:
                for location,piece in enumerate(cell):
                    try:
                        product = get_product(piece)
                        num = get_numbers(piece)
                        product_num.append([product,num])
                    except:
                        illegal_product_num[piece] = location+1

            return product_num, illegal_product_num

        kdzs['product & num'] = kdzs['bag'].apply(get_product_num)

        # 把描述不规范的信息记录下来，形成'错误信息汇报'。
        def wrong_information(cell):
            information = []
            if len(cell[1]) == 0:
                return None
            else:
                for x in cell[1]:
                    info = '订单中第 {} 个商品信息（名字或数量）是错误的'.format(cell[1][x])
                    information.append(info)

                return information

        kdzs['错误信息汇报'] = kdzs['product & num'].apply(wrong_information)



        # 文字规范：一律取消空格
        cpxx['原产品']=cpxx['原产品'].replace({' ':''},regex=True)

        # 将 kdzs 和 cpxx 的商品进行关联，找出对应的重量
        def get_weight(product):

            try:
                weight = round(cpxx.loc[cpxx['原产品']==product, '毛重'].iloc[0],2)
                #missing_product = None
            except:
                weight = 0
                #missing_product = product

            return weight


        def get_product_num_weight(cell):
            for piece in cell[0]:
                weight = get_weight(piece[0])
                piece.append(weight)

            return cell


        kdzs['product & num & weight'] = kdzs['product & num'].apply(get_product_num_weight)

        # 根据订单行的商品重量，计算订单重量
        def total_weight(cell):
            total_weight = 0
            for piece in cell[0]:
                total_weight = total_weight + piece[1]*piece[2]

            return round(total_weight/1000,2)

        kdzs['订单重量'] = kdzs['product & num & weight'].apply(total_weight)

        # 匹配kdzs和adrs的地址，得出“内圈外圈”

        provices = adrs.地址.values

        def get_location(cell):
            province = '0'
            if type(cell)==float or len(cell)<5:
                province = '0'
                return province
            for i in provices:
                place = re.findall(i, cell)
                if len(place) > 0:
                    province = place[0]

            return province

        kdzs['省份'] = kdzs['详细地址'].apply(get_location)

        def get_circle(cell):
            try:
                circle = adrs.loc[adrs['地址']==cell, '内圈外圈'].iloc[0]
            except:
                circle = 0
            return circle
        kdzs['内圈外圈'] = kdzs['省份'].apply(get_circle)

        # 对于无法得出商品重量的商品，形成“没有重量的产品清单”，这些商品需要在‘产品信息表’中维护重量。
        # 会生成'没有重量的产品清单.xlsx'
        def get_non_names(cell):
            names = []
            for piece in cell[0]:
                if piece[2] == 0:
                    names.append(piece[0])
            if len(names)>0:
                return names
            else: return ['忽略此行']

        kdzs['non_names'] = kdzs['product & num & weight'].apply(get_non_names)
        df_1 = pd.DataFrame(list(set(kdzs['non_names'].values.sum())), columns = ['没有重量的名字'])
        df_1.to_excel(out_file_1)

        # 利用 百世汇通的物流单价计算规则， 计算订单的物流费
        def get_fee(x):
            if x['状态'] == '已申请回收':
                return 0
            else:
                if x['内圈外圈'] == '内圈':
                    if x['订单重量'] == 0:
                        fee = 0
                    elif x['订单重量'] <= 3:
                        fee = 4
                    elif x['订单重量'] <= 4:
                        fee = 5
                    elif x['订单重量'] <= 5:
                        fee = 5
                    elif x['订单重量'] <= 6:
                        fee = 6
                    elif x['订单重量'] <= 7:
                        fee = 7
                    elif x['订单重量'] <= 8:
                        fee = 8
                    elif x['订单重量'] <= 9:
                        fee = 8
                    elif x['订单重量'] <= 10:
                        fee = 8
                    else: fee = 0.8*math.ceil(x['订单重量'])
                else:
                    if x['订单重量'] <= 3:
                        fee = 4.5
                    else: fee = 3 * math.ceil(x['订单重量'])
            return round(fee,2)

        kdzs['订单运费'] = kdzs.apply(get_fee, axis=1)


        # 字符化处理 快递单号'
        #kdzs['快递单号'] = kdzs['快递单号'].apply(str)

        # 表格合并，以及生产物流费与重量的差异
        check = pd.merge(kdzs, hdxx, left_on = '快递单号', right_on = '运单编号', how = 'outer')
        check['运费差异'] = check['订单运费'] - check['费用']
        check['重量差异'] = check['订单重量'] - check['计费重量']

        # 对于新生成的表格，把 '错误信息汇报' 放在最后一列
        wrong_info = check['错误信息汇报']
        check.drop(labels=['错误信息汇报'], axis=1,inplace = True)
        check.insert(len(check.columns), '错误信息汇报', wrong_info)

        # 导出 最终用于比较的表格。
        check.to_excel(out_file_final)

        print('it is all right!')
