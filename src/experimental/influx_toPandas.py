
import sys

import pandas as pd
from dateutil import parser
from datetime import datetime

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from influxdb import DataFrameClient

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread


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

    # ADDR = 'DDDDFE'     # kabrda ventus
    # ADDR = '074812'     # IBI CUBE3
    # ADDR = '4AD706'  # 'SE-UXF', Kjell, 'Duo Discus xlt'
    # ADDR = 'DDA80A'    # 'DS' (TT)
    # ADDR = 'DDDD40'  # 'ZQ' (gliding - mach02)
    ADDR = 'DDD530'  # hUSKy

    startDate = '2020-08-08'

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

    windowsSize = 14
    df['altf'] = df['alt'].rolling(window=windowsSize, center=False, closed='right').mean()
    df['gsf'] = df['gs'].rolling(window=windowsSize, center=False).mean()
    # df['vsf'] = df['vs'].rolling(window=windowsSize, center=True).mean()
    # df['trf'] = df['tr'].rolling(window=windowsSize, center=True).mean()

    # altitude delta:
    # df['dAlt'] = df['alt'].diff()

    # TODO kalman filtering? https://stackoverflow.com/questions/48739169/how-to-apply-a-rolling-kalman-filter-to-a-column-in-a-dataframe
    # TODO https://pykalman.github.io/

    # superPlot(df)

    keys1 = ['alt', 'altf']
    keys2 = ['gs', 'gsf']
    # keys3 = ['vs', 'vsf']
    # keys4 = ['tr', 'trf']
    # df[keys].plot(figsize=(20, 15))

    fig, axes = plt.subplots(nrows=2, ncols=1)
    for ax in axes:
        ax.xaxis.set_major_formatter(DateFormatter("%d. %m. %Y\n%H:%M"))
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95)
    df.plot(y=['alt'], figsize=(20, 15), ax=axes[0], rot=0, ls='', marker='.', markersize=2)
    df.plot(y=['altf'], ax=axes[0], rot=0)
    df.plot(y=['gs'], ax=axes[1], rot=0, ls='', marker='.', markersize=2)
    df.plot(y=['gsf'], ax=axes[1], rot=0)
    # df[keys3].plot(figsize=(20, 15), ax=axes[2], rot=0)
    # df[keys4].plot(figsize=(20, 15), ax=axes[3], rot=0)
    plt.show()

    # dfx = df[df['gs'] < 50]
    # dfx['gs'].plot(ls='', marker='+', markersize=4)
    # plt.show()

    print('KOHEU.')
