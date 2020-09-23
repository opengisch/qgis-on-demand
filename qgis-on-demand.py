import requests
import json
import os
import subprocess

import docker
import click

from tabulate import tabulate


@click.group()
def cli():
    pass


@cli.command()
def list_tags():
    response = requests.get(
        'https://registry.hub.docker.com/v2/repositories/qgis/qgis/tags?page_size=1024')

    tags = response.json()['results']
    results = []
    for tag in tags:
        results.append([tag['name'], tag['last_updated'], tag['full_size']])

    print(tabulate(results, headers=['Name', 'Last updated', 'Full size']))


def _pull(tag):
    client = docker.APIClient(
        base_url='unix://var/run/docker.sock')

    for line in client.pull(
            'qgis/qgis:{}'.format(tag), stream=True, decode=True):
        print(json.dumps(line, indent=4))


@cli.command()
@click.argument('tag', default='latest')
def start_qgis(tag='latest'):
    subprocess.run(['xhost', '+'])

    client = docker.from_env()
    image = 'qgis/qgis:{}'.format(tag)

    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        _pull(tag)

    cwd = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(cwd, 'plugins')
    io_dir = os.path.join(cwd, 'io')

    client.containers.run(
        image=image,
        volumes={
            '/tmp/.X11-unix': {'bind': '/tmp/.X11-unix', 'mode': 'ro'},
            plugins_dir: {'bind': '/root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/', 'mode': 'rw'},
            io_dir: {'bind': '/io/', 'mode': 'rw'},
        },
        environment=['DISPLAY={}'.format(os.environ['DISPLAY'])],
        command='qgis',
        detach=False,
        auto_remove=True,
    )


if __name__ == '__main__':
    cli()
