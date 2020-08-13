
import sys

import numpy as np
import pandas as pd
from datetime import datetime

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from influxdb import DataFrameClient

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread
from experimental.kalman import Kalman


def superPlot(df):
    keys = ['alt', 'altf', 'gs', 'gsf', 'vs', 'vsf']
    yLabels = ['ALT [m] AMSL', 'ALTf [m] AMSL', 'GS [km/h]', 'GSf [km/h]', 'VS [km/h]', 'VSf [km/h]']
    # yRanges = [[0, 5000], [0, 500], [60, 110], [0, 3500], [0, 2200], [0, 800], [0, 300], [0, 600], [-0.05, 1.05]]
    multipliers = [1, 1, 1, 1, 1, 1]
    legendLabels = keys

    plt.figure(figsize=[18, 10])

    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(left=0.05, right=0.74)  # 0.04-0.84 for 5 keys; 0.05-0.80 for 6 keys; 0.05-0.76 for 7 keys
    plt.legend(fontsize=20)

    host.set_xlabel("dateTime")

    for i in range(0, len(keys)):
        if i == 0:
            host.set_ylabel(yLabels[0])
            # host.set_ylim(yRanges[i])

            p0, = host.plot(df.index, df['alt'], label=legendLabels[0])

        else:
            par1 = host.twinx()

            offset = (i - 1) * 50
            new_fixed_axis1 = par1.get_grid_helper().new_fixed_axis
            par1.axis["right"] = new_fixed_axis1(loc="right", axes=par1, offset=(offset, 0))

            par1.set_ylabel(yLabels[i])
            # par1.set_ylim(yRanges[i])

            p1, = par1.plot(df.index, df[keys[i]] / multipliers[i], label=legendLabels[i])

    host.legend(loc='lower center')
    # plt.title(f"{originalFileName}")
    plt.draw()
    plt.show()

    # fn = composeFilename2(originalFileName, suffix, 'png')
    # fp = f"{outPath}/{fn}"
    # plt.savefig(fp, dpi=200)

    # plt.close()


if __name__ == '__main__':

    influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    # ADDR = '074812'     # IBI CUBE3
    # ADDR = 'DDDDFE'     # kabrda ventus
    ADDR = 'DDD530'  # hUSKy
    # ADDR = '034819'  # ROBIN
    # ADDR = '4AD706'  # 'SE-UXF', Kjell, 'Duo Discus xlt'
    # ADDR = 'DDA80A'  # 'DS' (TT)
    # ADDR = '151035'  # A1 2020-08-10
    # ADDR = '213707'  # OK-PLR

    # ADDR = 'DDDD40'  # 'ZQ' (gliding - mach02)

    # ADDR = 'DD8ED4'  # F-CVVZ (LFLE) where gliders never land
    # ADDR = 'DDA391'  # F-CIJL (LFLE) where gliders never land
    # ADDR = 'D006D0'  # F-PVVA (LFLE) where gliders never land

    # ADDR = 'DDA816'    # random address from the log

    startDate = '2020-08-13'

    dt: datetime = datetime.strptime(startDate, '%Y-%m-%d')
    ts = dt.timestamp()     # [s]
    startTs = f"{ts:.0f}000000000"

    query = f"select * from pos where addr='{ADDR}' and time > {startTs}"

    c = DataFrameClient(host=INFLUX_DB_HOST, port=8086, database=INFLUX_DB_NAME)
    res = c.query(query=query)

    if len(res) == 0:
        print('[INFO] No data.')
        sys.exit(0)

    df = res['pos']

    # filter/smoothen the data a bit:
    windowsSize = 5
    df['altf'] = df['alt'].rolling(window=windowsSize, center=False, closed='right').mean()
    kalman = Kalman()
    df['altk'] = df['alt'].apply(lambda val: kalman.predict(val))

    df['gsf'] = df['gs'].rolling(window=windowsSize, center=False).mean()
    kalman = Kalman()
    df['gsk'] = df['gs'].apply(lambda val: kalman.predict(val))

    # df['vsf'] = df['vs'].rolling(window=windowsSize, center=True).mean()
    # df['trf'] = df['tr'].rolling(window=windowsSize, center=True).mean()

    df['aglf'] = df['agl'].rolling(window=windowsSize, center=False).mean()
    kalman = Kalman()
    df['aglk'] = df['agl'].apply(lambda val: kalman.predict(val))

    # altitude delta:
    # df['dAlt'] = df['alt'].diff()

    # airborne flag / status detection:
    min = int(df['gsf'].min())
    max = int(df['gsf'].max())
    df['airborneGs'] = df['gsf'].apply(lambda val: max if val > 60 else min)
    min = int(df['agl'].min())
    max = int(df['agl'].max())
    df['airborneAgl'] = df['agl'].apply(lambda val: max if val > 20 else min)

    # superPlot(df)

    keys1 = ['alt', 'altf']
    keys2 = ['gs', 'gsf']
    # keys3 = ['vs', 'vsf']
    # keys4 = ['tr', 'trf']
    # df[keys].plot(figsize=(20, 15))

    fig = plt.figure()
    gs = fig.add_gridspec(3, hspace=0)
    axes = gs.subplots(sharex=True, sharey=False)
    # fig, axes = plt.subplots(nrows=3, ncols=1)
    for ax in axes:
        ax.minorticks_on()

        ax.xaxis.set_major_formatter(DateFormatter("%d. %m. %Y\n%H:%M"))
        ax.yaxis.set_ticks_position('both')

        ax.grid(b=True, which='major', color='#666666', linestyle='-')
        ax.grid(b=True, which='minor', color='#999999', linestyle='--', alpha=0.5)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95)

    df.plot(y=['alt'], figsize=(20, 15), ax=axes[0], rot=0, ls='', marker='.', markersize=2)
    df.plot(y=['altf'], ax=axes[0], rot=0)
    df.plot(y=['altk'], ax=axes[0], rot=0)

    df.plot(y=['agl'], ax=axes[1], rot=0, ls='', marker='.', markersize=2)
    df.plot(y=['aglf'], ax=axes[1], rot=0)
    df.plot(y=['aglk'], ax=axes[1], rot=0)
    df.plot(y=['airborneAgl'], ax=axes[1], rot=0)

    df.plot(y=['gs'], ax=axes[2], rot=0, ls='', marker='.', markersize=2)
    df.plot(y=['gsf'], ax=axes[2], rot=0)
    df.plot(y=['gsk'], ax=axes[2], rot=0)
    df.plot(y=['airborneGs'], ax=axes[2], rot=0)

    # df[keys3].plot(figsize=(20, 15), ax=axes[2], rot=0)
    # df[keys4].plot(figsize=(20, 15), ax=axes[3], rot=0)
    plt.show()



    # dfx = df[df['gs'] < 50]
    # dfx['gs'].plot(ls='', marker='+', markersize=4)
    # plt.show()

    print('KOHEU.')
