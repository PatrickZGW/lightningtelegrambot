import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns
import pandas as pd

import config

config = config.Config()

def create_chart():
    conn = sqlite3.connect(config.SQLITEDB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM statistics')
    stats = c.fetchall()
    c.close()
    
    df = pd.DataFrame(stats, columns=['id', 'num_nodes', 'capacity_ltc', 'capacity_usd', 'price', 'num_channels', 'time'])
    df['time_new'] = pd.to_datetime(df['time'])
    
    sns.set_style('darkgrid')
    plt.style.use('dark_background')
    f, (ax1, ax2, ax3, ax4) = plt.subplots(4,1, sharex=True, gridspec_kw = {'height_ratios':[2, 1, 1, 1]})
    f.set_figwidth(12)
    f.set_figheight(8)
    
    ax1.plot(df['time_new'], df['capacity_ltc'])
    ax2.plot(df['time_new'], df['num_nodes'])
    ax3.plot(df['time_new'], df['num_channels'])
    ax4.plot(df['time_new'], df['capacity_usd'])
    
    ax1.set_title('LTC Lightning Network growth')
    ax1.grid(lw=0.3, color='white')
    ax1.lines[0].set_color('#00C040')
    ax1.lines[0].set_linewidth(2.5)
    ax1.set_ylabel('Capacity (LTC)')
    
    ax2.set_ylabel('#nodes')
    ax2.lines[0].set_color('#80C0FF')
    ax2.lines[0].set_linewidth(2.5)
    ax2.grid(lw=0.3, color='white')
    
    ax3.set_ylabel('#channels')
    ax3.lines[0].set_color('#FFFF00')
    ax3.lines[0].set_linewidth(2.5)
    ax3.grid(lw=0.3, color='white')
    
    ax4.set_ylabel('Capacity (USD)')
    ax4.grid(lw=0.3, color='white')
    
    
    yearsFmt = mdates.DateFormatter('%m-%d')
    ax1.xaxis.set_major_formatter(yearsFmt)
    
    fmt = '{x:,.0f}'
    tick = mtick.StrMethodFormatter(fmt)
    ax1.yaxis.set_major_formatter(tick)
    ax4.yaxis.set_major_formatter(tick)
    
    return f