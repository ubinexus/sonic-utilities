#! /usr/bin/python -u

import click
import swsssdk
from tabulate import tabulate

STATS_DESCRIPTION = [
    ('Storm Detected Cnt',   'PFC_WD_QUEUE_STATS_DEADLOCK_DETECTED'),
    ('Storm Restored Cnt',   'PFC_WD_QUEUE_STATS_DEADLOCK_RESTORED'),
    ('Tx Packets',           'PFC_WD_QUEUE_STATS_TX_PACKETS'),
    ('Rx Packets',           'PFC_WD_QUEUE_STATS_TX_DROPPED_PACKETS'),
    ('Tx Packets Drop',      'PFC_WD_QUEUE_STATS_RX_PACKETS'),
    ('Rx Packets Drop',      'PFC_WD_QUEUE_STATS_RX_DROPPED_PACKETS_LAST'),
    ('Tx Packets Last',      'PFC_WD_QUEUE_STATS_TX_PACKETS_LAST'),
    ('Rx Packets Last',      'PFC_WD_QUEUE_STATS_TX_DROPPED_PACKETS_LAST'),
    ('Tx Packets Last Drop', 'PFC_WD_QUEUE_STATS_RX_PACKETS_LAST'),
    ('Rx Packets Last Drop', 'PFC_WD_QUEUE_STATS_RX_DROPPED_PACKETS_LAST')
]

STATS_HEADER = ('Queue',) + zip(*STATS_DESCRIPTION)[0]

# Main entrypoint
@click.group()
def cli():
    """ SONiC PFC Watchdog """

def get_all_queues(db):
    queue_names = db.get_all(db.COUNTERS_DB, 'COUNTERS_QUEUE_NAME_MAP')
    return queue_names.keys()

# Show stats
@cli.command()
@click.argument('queues', nargs = -1)
def stats(queues):
    """ Show PFC WD stats per queue """
    db = swsssdk.SonicV2Connector(host='127.0.0.1')
    db.connect(db.COUNTERS_DB)
    table = []

    if len(queues) == 0:
        queues = get_all_queues(db)

    for queue in queues:
        stats_list = []
        queue_oid = db.get(db.COUNTERS_DB, 'COUNTERS_QUEUE_NAME_MAP', queue)
        stats = db.get_all(db.COUNTERS_DB, 'COUNTERS:' + queue_oid)
        if stats is None:
            continue
        for stat in STATS_DESCRIPTION:
            line = stats.get(stat[1], '0')
            stats_list.append(line)
        #click.echo("Queue ID " + queue)
        table.append([queue] + stats_list)

    print(tabulate(table, STATS_HEADER, stralign='center', numalign='center', tablefmt='simple'))

if __name__ == '__main__':
    cli()
