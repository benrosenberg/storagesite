from matplotlib import pyplot as plt
import pandas as pd
import datetime

VISITOR_LOG_FILENAME = './static/files/visitors.txt'

PIE_FILENAME = './static/images/pie.png'
BAR_FILENAME = './static/images/bar.png'

def get_ip_series():
    with open(VISITOR_LOG_FILENAME, 'r') as f:
        ips = [l.strip().split('] ')[1] for l in f.readlines()]
    return pd.Series(ips)

def generate_pie_chart(N=20):
    ips = get_ip_series()
    vc = ips.value_counts().head(N)
    plt.pie(vc)
    plt.legend(vc.index)
    plt.title('IP accesses as of {} (top {})'.format(datetime.datetime.now(), N))
    plt.savefig(PIE_FILENAME)
    plt.clf()

def generate_bar_chart(N=20):
    ips = get_ip_series()
    vc = ips.value_counts().head(N)
    plt.bar(vc.index, vc)
    plt.title('IP accesses as of {} (top {})'.format(datetime.datetime.now(), N))
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(BAR_FILENAME)
    plt.clf()

def generate_all_graphics(N=20):
    generate_pie_chart(N=N)
    generate_bar_chart(N=N)

if __name__ == '__main__':
    generate_all_graphics()
