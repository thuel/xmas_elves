"""
Module to solve the xmas-elves problem.

The xmas-elves problem means, that there are three or more people which
want to randomly draw for each person another person among themselves
to make a gift to. Every persons gets one of the other persons asigned
to make a gift to this person. In the end every person makes one gift
and every person receives one gift.

In the role of making a gift a person is called elf. In the role of
receiving a gift a person is called giftee. Allthough every person in the
problem has both roles the persons are represented as Elf objects.

The whole assignment is done using a network graph where the persons
represent the nodes (in form of Elf objects) and the edges between
the persons indicate which person could make a gift to whom of the
other persons. By default no edges are create between nodes which are
partners.

The algorithm chooses randomly among those nodes with the lowest degree
of ingoing edges to get the next node (giftee) to which an elf is
randomly assigned to. Once the elf is chosen and assigned, all of the other
ingoing nodes of the giftee are removed from the graph. The same procedure
applies to the outgoing edges of the node with elf role. At the end there
is a directed graph with one or more subgraphs where every node has excatly
one outgoing and one incomming edge.
"""

import networkx as nx
import openpyxl as xl
import csv
import random
import logging
import time
import datetime
import smtplib

from textwrap import dedent
from pprint import pprint
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
from collections import Counter, defaultdict
from email.message import EmailMessage

from .user_dialog_prompts import yes_or_no

logger = logging.getLogger(__name__)
logger_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
stream_formatter = logging.Formatter(logger_format)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)


class Elf:
    """
    Object to represent one person taking part in the "game".

    Initialised with a name, email-address and partner. The partner
    is an empty string if there is none. The partner can be used to
    determine if the partner could be a giftee or not. The create_edges
    method makes use of this variable.
    """

    def __init__(self, name, email, partner, giftee=None):
        self.name = name
        self.email = email
        self.partner = partner
        self.giftee = giftee

    def __str__(self):
        return "Elf(name={}, email={}, partner={})".format(
            self.name,
            self.email,
            self.partner
        )

    def __repr__(self):
        return str(self)

    def __iter__(self):
        yield from (self.name, self.email, self.partner, self.giftee)


def nodes_from_string(string):
    """
    Helper method to create elf nodes from a comma separate string
    with line breaks (see example under if __name__ == "__main__").
    """
    data_lines = [
        line
        for line in string.splitlines()
        if line != ''
    ]
    reader = csv.reader(data_lines)
    return create_nodes(reader)


def nodes_from_csv(filename):
    """
    Helper method to create elf nodes from a csv file.
    """
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        return create_nodes(reader)


def nodes_from_excel(filename):
    wb = xl.load_workbook(filename)
    ws = wb.active
    data = [
        [value for value in row]
        for row in ws.values
    ]
    return create_nodes(data)


def create_nodes(data_list):
    """
    Factory method to create Elf object nodes
    from the given data lines.
    """
    return [
        Elf(name, email, partner, None)
        for name, email, partner, *_ in data_list
    ]


def create_edges(nodes, allow_partner=False):
    """
    Given a list of Elf nodes, return a list of edges.

    allow_partner:  if True, partners are also taken into account
        for possible gift making relationships. On default, partners
        are not allowed to be drawn as either elf or giftee of one
        another.
    """
    edges = [
        (node, neighbour)
        for node in nodes
        for neighbour in nodes
        if node != neighbour
    ]
    if not allow_partner:
        for node in nodes:
            for neighbour in nodes:
                if node.partner == neighbour.name:
                    edges.remove((node, neighbour))
    return edges


def random_min_indegree(graph, remaining_giftees):
    """
    Return the node with lowest degree of ingoing edges.

    If there is more than one node with the minimum degree, one of
    these nodes is drawn randomly from the list of minimum degree nodes.

    graph: the graph to determine minimum degree of ingoing edges on.
    remaining_giftees: list of Elf objects without elf assigned to them.
    """
    min_degree = len(graph.nodes)
    min_set = []
    for node in remaining_giftees:
        min_degree = min([min_degree, graph.in_degree(node)])
    for node in remaining_giftees:
        if graph.in_degree(node) <= min_degree:
            min_set.append(node)
    chosen = random.choice(min_set)
    return chosen


def xmas_elves(original_graph):
    """
    Return a new graph object for which the xmas-elves problem is solved.

    A new instance of a directed graph object is created an the actual
    algorithem is run on this new graph object.
    """
    graph = nx.DiGraph(original_graph)
    try:
        queue = [node for node in graph.nodes]
        while len(queue) > 0:
            current_node = random_min_indegree(graph, queue)
            queue.remove(current_node)
            chosen_wichtel = random.choice(
                list(graph.predecessors(current_node))
            )
            chosen_wichtel.giftee = current_node
            obsolete_ingoing = [
                node
                for node in graph.predecessors(current_node)
                if node != chosen_wichtel
            ]
            for node in obsolete_ingoing:
                graph.remove_edge(node, current_node)
            obsolete_outgoing = [
                node
                for node in graph.successors(chosen_wichtel)
                if node != current_node
            ]
            for node in obsolete_outgoing:
                graph.remove_edge(chosen_wichtel, node)
        if None in [n.giftee for n in graph.nodes]:
            return xmas_elves(original_graph)
    except IndexError as e:
        logger.warning(e)
        return xmas_elves(original_graph)
    return graph


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        'personsource',
        type=str,
        help=dedent("""\
            Comma and newline separated string or path to file\
            containing info about the persons to be included\
            in the xmas-elves problem.
            Structure: name,email,partner,
            """)
    )
    parser.add_argument(
        '-m', '--mailconfig',
        type=str,
        help=dedent("""\
            Path to file containing configuration for sending\
            E-Mails. The config file is in .ini format and\
            contains a section named "email" with the following\
            key, value pairs:
            - smtp_mode, indicates wheter ssl or tls should be used
            - smtp_server, address of the smtp server to be used
            - smtp_port, port used to authenticate to
            - sender_address, e-mail address of the sender
            - sender_password, password to authenticate the sender\
            with the smtp server
            """)
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help=dedent("""\
            With dry-run there are no e-mails sent and the solution
            to the problem is printed to standard output.
            """)
    )
    parser.add_argument(
        '--allow-partners',
        action='store_true',
        help=dedent("""\
            Switch to control if partners should be allowed in elf
            giftee relationships.
            """)
    )
    parser.add_argument(
        '-s', '--stats',
        action='store_true',
        help=dedent("""\
            Solve the problem 20'000 times and print the counts for
            each elf giftee combination.
            """)
    )

    return parser.parse_args()


def create_nodes_from_type(string):
    if Path(string).exists():
        logger.debug(
            "Path.exists() in create_nodes_from_type: {}".format(
                Path(string).exists()
            )
        )
        ext = Path(string).suffix
        if ext in ['.xls', '.xlsx']:
            logger.debug("going to return nodes_from_excel")
            try:
                return nodes_from_excel(string)
            except Exception as e:
                raise e
                # ("Couldn't parse excel file successfully.")
        else:
            try:
                return nodes_from_csv(string)
            except Exception as e:
                raise e
                # ("Couldn't parse csv file successfully.")
    else:
        try:
            return nodes_from_string(string)
        except Exception as e:
            raise e
            # ("Couldn't parse the string successfully.")


def parse_mail_config(configfile):
    parser = ConfigParser()
    parser.read(configfile)
    return dict(parser['Email'])


def mail_html_text(text):
    text = text.replace('\n\n', '\n')
    return "".join([
        f'<p>{line}</p>' if line != '' else '</br>'
        for line in text.split('\n')
    ])


def mail_text(reciever, giftee):
    year = datetime.date.today().year
    return dedent("""\
        Hallo {},

        Weihnachten {} steht vor der Tür und ich wurde gebeten, die
        Wichtelauslosung zu starten.

        Du bist das Wichteli von {}. Vielen Dank, dass du mitmachst!

        Ich wünsche dir eine schöne Adventszeit.

        Liebe Grüsse
        Dein automatischer Wichtler
        """).format(reciever, year, giftee)


def mail_texts(graph):
    texts = [
        mail_text(elf.name, elf.giftee.name)
        for elf in graph.nodes
    ]
    return texts


def mail_messages(graph, sender):
    for node in graph.nodes:
        name, email, _, giftee = node
        msg = EmailMessage()
        msg['Subject'] = "Wichtelauslosung {}".format(
            datetime.date.today().year
        )
        msg['From'] = sender
        msg['To'] = email
        content = mail_text(name, giftee.name)
        msg.set_content(content)
        msg.add_alternative(mail_html_text(content), subtype='html')
        yield msg


def send_xmas_mails(config, graph):
    SMTP_SERVER = config['smtp_server']
    SMTP_PORT = int(config['smtp_port'])
    SENDER_ADDRESS = config['sender_address']
    SENDER_PASSWORD = config['sender_password']
    for msg in mail_messages(graph, SENDER_ADDRESS):
        with smtplib.SMTP("{}:{}".format(SMTP_SERVER, SMTP_PORT)) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_ADDRESS, SENDER_PASSWORD)
            smtp.send_message(msg)
        time.sleep(2)


def draw_graph(graph):
    import matplotlib.pyplot as plt
    labels = {node: node.name for node in graph.nodes}
    plt.subplot(111)
    nx.draw(graph, labels=labels)
    plt.show()


def resend_mail_for_node(filename, nodename, mailconfig):
    """
    Resend the mail for one Node from a solved graph stored as gpickle.

    To be used, by importing the module in an interpreter and providing
    the paramters necessairy.

    filename: path to stored gpickle graph
    nodename: name of the elf to send the mail again
    mailconfig: path to the mail configuration file
    """
    solved_graph = nx.read_gpickle(filename)
    for node in solved_graph:
        if node.name == nodename:
            wanted_node = node
    new_graph = nx.DiGraph()
    new_graph.add_node(wanted_node)
    mail_config = parse_mail_config(mailconfig)
    send_xmas_mails(mail_config, new_graph)


def main():
    args = parse_args()
    nodes = create_nodes_from_type(args.personsource)
    # prepare edges
    edges = create_edges(nodes, args.allow_partners)
    # Create a directed graph
    graph = nx.from_edgelist(edges, nx.DiGraph)
    solved_graph = xmas_elves(graph)
    message_texts = mail_texts(solved_graph)

    if args.dry_run:
        for line in message_texts:
            print(line.replace("\n", " "))
    else:
        date = datetime.date.today()
        persons_path = Path(args.personsource)
        persons_name = persons_path.name
        filename = "{}/{}-{}.gpickle".format(
            persons_path.parent,
            date,
            persons_name
        )
        nx.write_gpickle(solved_graph, filename)
        if yes_or_no("Really send e-mails?"):
            mail_config = parse_mail_config(args.mailconfig)
            send_xmas_mails(mail_config, solved_graph)
        else:
            print("Not sending e-mails for the solved graph")
            draw_graph(solved_graph)

    if args.stats:  # and graph not loaded from file
        # Do some statistics with the graph:
        all_dict = defaultdict(list)
        for i in range(20000):
            g = xmas_elves(graph)
            for node in g.nodes:
                all_dict[node.name].append(node.giftee.name)

        res = {
            key: Counter(value)
            for key, value in all_dict.items()
        }
        """#Could be used to create a tabled view of up to 8 runs of xmas_elves
        for key, value in all_dict.items():
            values = ["{: <9s}".format(v) for v in value]
            print("{: <9s}\t{}".format(key, values))
        """
        pprint(res)


if __name__ == "__main__":

    main()
    csv_text = dedent("""\
        Angelina,angelina@email.com,Walter,
        Walter,walter@email.com,Angelina,
        Irena,irena@email.com,Isaac,
        Isaac,isaac@email.com,Irena,
        Gavin,gavin@email.com, ,
        Vince,vince@email.com,Vincent,
        Vincent,vincent@email.com,Vince,
        Renetta,renetta@email.com,Demetrius,
        Demetrius,demetrius@email.com,Renetta,
        Belinda,belinda@email.com, ,
        """)

    # prepare nodes
    nodes = nodes_from_string(csv_text)
    # nodes = nodes_from_csv('xmaselves_persons.txt')
    # prepare edges
    edges = create_edges(nodes)
    # Create a directed graph
    graph = nx.from_edgelist(edges, nx.DiGraph)
