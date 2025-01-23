#!/usr/bin/env python3
import click
import manager
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Job(BaseModel):
    name: str

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

@app.post('/scale')
def scaleAPI(job:Job):
    if not manager.scale(job.name):
        return "Did not scale", 401
    else:
        return "Scaled", 200

@main.command()
@click.option("-n", "--name", help="Name of job to delete", required=True, multiple=True)
def delete(name):
    manager.delete(name)

if __name__ == "__main__":
    main()
