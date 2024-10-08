import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
import os # 경로 탐색

# 파일 업로드 함수
# 디렉토리 이름, 파일을 주면 해당 디렉토리에 파일을 저장해주는 함수
def save_uploaded_file(directory, file):
    # 1. 저장할 디렉토리(폴더) 있는지 확인
    #   없다면 디렉토리를 먼저 만든다.
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # 2. 디렉토리가 있으니, 파일 저장
    with open(os.path.join(directory, file.name), 'wb') as f:
        f.write(file.getbuffer())
    return st.success('파일 업로드 성공!')



# 기본 형식
def main():
    st.title('WELT RTIB Simulator')

    menu = ['csv 업로드']

    choice = st.sidebar.selectbox('메뉴', menu)
    
    if choice == menu[0]:
        st.subheader('csv 파일 업로드 ')

        csv_file = st.file_uploader('CSV 파일 업로드', type=['csv'])

        #print(csv_file.type)
        if csv_file is not None:
            current_time = datetime.now()
            filename = current_time.isoformat().replace(':', '_') + '.csv'

            csv_file.name = filename

            save_uploaded_file('csv', csv_file)

            # csv를 보여주기 위해 pandas 데이터 프레임으로 만들어야한다.
            df = pd.read_csv('csv/'+filename)

    return df

def preprocess_data(df):
    try:
        df['LOT'] = pd.to_datetime(df['LOT'], format='%Y/%m/%d %H:%M')
    except:
        df['LOT'] = pd.to_datetime(df['LOT'], format='%Y-%m-%d %H:%M')
    try:
        df['AET'] = pd.to_datetime(df['AET'], format='%Y/%m/%d %H:%M')
    except:
        df['AET'] = pd.to_datetime(df['AET'], format='%Y-%m-%d %H:%M')

    df['AST'] = df['LOT'] + pd.to_timedelta(df['SOL'], unit='m')
    df['AST'] = pd.to_datetime(df['AST'], format='%Y/%m/%d %H:%M')

    df['WASO'] = pd.to_timedelta(df['WASO'], unit='m')

    df['TST'] = (df['AET'] - df['AST'] - pd.to_timedelta(df['WASO'], unit='m'))

    df['TST'] = df['TST'].dt.total_seconds() / 60
    df['WASO'] = df['WASO'].dt.total_seconds() / 60

    df['DSE'] = (pd.to_datetime(df['AET']) - pd.to_datetime(df['LOT']))

    df['DSE'] = df['DSE'].dt.total_seconds() / 60

    df['SE'] = df['TST'] / df['DSE']

    df.loc[df['TST'] > 720, ['DNS', 'LOT', 'AET', 'SOL', 'WASO', 'AST', 'TST', 'DSE', 'SE']] = np.nan

    return df

def calculate_rTIB(accSE, accTST, accDSE, SW):
    # Calculate recommended time in bed (rTIB) based on sleep efficiency metrics
    accSE = round(accSE, 2)
    accTST = round(accTST, 2)
    accDSE = round(accDSE, 2)

    # When sleep efficiency is good (greater than or equal to 0.95)
    if accSE >= 0.95:
        # Maintain the current sleep duration
        rTIB = accDSE
    # When sleep efficiency is poor (less than or equal to 0.87)
    elif accSE <= 0.87:
        # Adjust the time in bed to be closer to the actual sleep duration to improve sleep efficiency
        rTIB = accTST
        # Exception case: within a week of the first rTIB calculation
        if SW == True:
            rTIB += 30  # Add 30 minutes
    # When sleep efficiency is moderate (between 0.87 and 0.95)
    else:
        # Adjust rTIB based on sleep efficiency, with lower SE closer to TST and higher SE closer to DSE
        rTIB = accTST + (accDSE - accTST) * (accSE - 0.87) * 10
        rTIB = round(rTIB)
    # Ensure rTIB is within a certain range (300 to 600 minutes)
    rTIB = max(300, min(rTIB, 600))

    # Round rTIB to the nearest multiple of 15
    rTIB = round(rTIB / 15) * 15
    return rTIB

def calculate_averages(data):

    se_list = data['SE'].tolist()
    tst_list = data['TST'].tolist()
    dse_list = data['DSE'].tolist()
    date_list = data['DATE'].tolist()
    
    se_averages = []
    tst_averages = []
    dse_averages = []
    assinged_dates = []
    rtib_pre = []
    index = 0
    rtib_count = 0   
    while index + 5 <= len(se_list):
        # Extract the three consecutive numbers
        print("start index",index)
        print("rtib count", rtib_count)
        if rtib_count == 0:
          SW = True
          FR = False
          print(se_list)
          if str(se_list[6]) == 'nan' and str(se_list[7]) == 'nan':
              print("passed")
              FR = False
              rtib_count += 1
              pass
          else:
              first_seven_se = se_list[index:index + 7]
              first_seven_tst = tst_list[index:index + 7]
              first_seven_dse = dse_list[index:index + 7]
              date_val = date_list[index:index + 7]
              print("before rtib has increased",date_val)
              date_value = date_val[-1]
              print(date_value)
              date_obj = pd.to_datetime(date_value)
              new_date_obj = date_obj + pd.Timedelta(days=2)
              new_date_value = new_date_obj.strftime('%Y/%m/%d')
              print(new_date_value)
              assinged_dates.append(new_date_value)
              print("first seven se", first_seven_se)
              print("first seven tst", first_seven_tst)
              print("first seven dse", first_seven_dse)
              print("first seven date", date_val)
              se_series = pd.Series(first_seven_se)
              first_seven_se = se_series.tolist()
              if se_series.nunique() < 2:
                  se_average = next(filter(lambda x: str(x) != 'nan', first_seven_se), None)
                  tst_average = next(filter(lambda x: str(x) != 'nan', first_seven_tst), None)
                  dse_average = next(filter(lambda x: str(x) != 'nan', first_seven_dse), None)
              else:  
                  se_average = np.nanmean(first_seven_se)
                  tst_average = np.nanmean(first_seven_tst)
                  dse_average = np.nanmean(first_seven_dse)
              rtib = calculate_rTIB(se_average, tst_average, dse_average, SW)
              print("se_average",se_average)
              print("tst_average",tst_average)
              print("dse_average",dse_average)
              print("rtib",rtib)
              se_averages.append(se_average)
              tst_averages.append(tst_average)
              dse_averages.append(dse_average)
              rtib_pre.append(rtib)
              index += 3
              rtib_count += 1
              FR = True
              print("new index",index)
        elif rtib_count >= 1:
          if index == 6:
            SW = False
          if FR == False:
              se_nan_check = se_list[0:index + 8]
              tst_nan_check = tst_list[0:index + 8]
              dse_nan_check = dse_list[0:index + 8]
              date_val = date_list[0:index + 9]
              print("FR is False date",date_val)
              index +=4
              FR = True
          elif FR == True:
              se_nan_check = se_list[0:index + 5]
              tst_nan_check = tst_list[0:index + 5]
              dse_nan_check = dse_list[0:index + 5]
              date_val = date_list[0:index + 5]
              print("FR is TRUE date",date_val)
          print("after rtib has increased",date_val)
          date_value = date_val[-1]
          print("before date add",date_value)
          date_obj = pd.to_datetime(date_value)
          new_date_obj = date_obj + pd.Timedelta(days=2)
          new_date_value = new_date_obj.strftime('%Y/%m/%d')
          print("after date add",new_date_value)
          assinged_dates.append(new_date_value)
          se_non_na = [x for x in se_nan_check if not np.isnan(x)]
          tst_non_na = [x for x in tst_nan_check if not np.isnan(x)]
          dse_non_na = [x for x in dse_nan_check if not np.isnan(x)]

          current_index_min = index - 1
          print("index max", current_index_min)
          print("first five se:", se_nan_check)
          print("first five tst:", tst_nan_check)
          print("first five dse:", dse_nan_check)
          # Replace NaN values with the next available number

          if len(se_non_na) <= 4:
            print("less or equal to 4")
            first_five_se = se_non_na
            first_five_tst = tst_non_na
            first_five_dse = dse_non_na
          else:
            print("more than 4")
            first_five_se = se_non_na[-5:]
            first_five_tst = tst_non_na[-5:]
            first_five_dse = dse_non_na[-5:]


          print("final five se:", first_five_se)
          print("final five tst:", first_five_tst)
          print("final five dse:", first_five_dse)
          print("first five date", date_val)
          # Calculate the average of the three numbers
          se_series = pd.Series(first_five_se)
          first_five_se = se_series.tolist()
          if se_series.nunique() < 2:
              se_average = next(filter(lambda x: str(x) != 'nan', first_five_se), None)
              tst_average = next(filter(lambda x: str(x) != 'nan', first_five_tst), None)
              dse_average = next(filter(lambda x: str(x) != 'nan', first_five_dse), None)
          else:  
              se_average = np.nanmean(first_five_se)
              tst_average = np.nanmean(first_five_tst)
              dse_average = np.nanmean(first_five_dse)
          rtib = calculate_rTIB(se_average, tst_average, dse_average, SW)
          print("se_average",se_average)
          print("tst_average",tst_average)
          print("dse_average",dse_average)
          print("rtib",rtib)
          se_averages.append(se_average)
          tst_averages.append(tst_average)
          dse_averages.append(dse_average)
          rtib_pre.append(rtib)
          # Move to the next set of three numbers
          index += 1
          rtib_count += 1
          print("new index",index)

    return rtib_pre, assinged_dates

def present_result(rtib_test, dates):
    results_df = pd.DataFrame({'RTIB_DATE': dates, 'RTIB': rtib_test})
    results_df['RTIB_AET'] = pd.to_datetime(results_df['RTIB_DATE'])
    results_df['RTIB_AET'] += pd.to_timedelta('7 hours')
    results_df['RTIB_LOT'] = (results_df['RTIB_AET'] - pd.to_timedelta(results_df['RTIB'], unit='m'))
    results_df = results_df[['RTIB_DATE','RTIB_LOT','RTIB_AET','RTIB']]
    results_df = results_df.drop(results_df.index[-1])
    st.dataframe(results_df)
    

if __name__ == '__main__':
    df = main()
    processed_df = preprocess_data(df)
    rtib_test, date = calculate_averages(processed_df)
    st.subheader('RTIB 결과')
    present_result(rtib_test, date)
    st.success("RTIB 시뮬레이션 완료")
