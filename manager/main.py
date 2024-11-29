#!/usr/bin/env python3
import click
import manager

@click.group()
def main():
    pass

@main.command()
@click.option('-f', '--filename', help="Input spec file", required=True)
@click.option('--standalone', is_flag=True, help="Standalone deployment vs pod", default=False)
def deploy(filename, standalone):
    manager.deploy(filename, standalone)

@main.command()
@click.option("--name")
def scale(name):
    manager.scale(name)

if __name__ == "__main__":
    main()
