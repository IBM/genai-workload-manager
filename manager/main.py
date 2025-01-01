#!/usr/bin/env python3
import click
import manager

@click.group()
def main():
    pass

@main.command()
@click.option('-f', '--filename', help="Input spec file", required=True)
def deploy(filename):
    manager.deploy(filename)

@main.command()
@click.option("-n", "--name", help="Name of job to scale")
def scale(name):
    manager.scale(name)

@main.command()
@click.option("-n", "--name", help="Name of job to delete", required=True, multiple=True)
def delete(name):
    manager.delete(name)

if __name__ == "__main__":
    main()
